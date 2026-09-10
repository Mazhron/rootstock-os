"""PreToolUse guard on EVERY tool: THE FAN-OUT LAW + the spend meter (Tier 2b).

KIT COPY (Rootstock v1.9). Born in Everwood on 2026-09-10 after a public
report of a Claude that spun up 821 sub-agents and burned 50M+ tokens in
30 seconds on "check my markdown files for consistency". The CEO's ask:
"prevent this type of catastrophe at the harness level." The harness
hands us every tool call BEFORE it runs, so this hook is the circuit
breaker:

  1. THE SPEND METER (every call): reads the session transcript + its
     employee transcripts INCREMENTALLY (byte offsets in the state file,
     so a call costs a few KB of IO) and keeps raw + WEIGHTED tokens
     (weighted ~ cost: input 1, cache write 1.25, cache read 0.1, output 5).
     A systemMessage to the CEO at every `tokens_warn_every` weighted
     tokens; a velocity warning when `velocity_warn` weighted tokens land
     inside `velocity_window` seconds.
  2. THE HALT: `velocity_halt` weighted tokens inside the window = a
     runaway. EVERY tool call is refused until the CEO runs --resume in
     their own terminal. The manager can still talk, so it reports.
  3. THE AGENT CAPS (Agent / Task tools): a warning at `agents_warn`
     spawns per session, a refusal past `agents_cap`; a refusal when more
     than `burst_cap` spawns land inside `burst_window` seconds MACHINE-
     WIDE (that is the 821-agents shape); a refusal once the session's
     weighted spend passes `tokens_agents_cap`.
  4. THE WORKFLOW LOCK: the Workflow tool (dozens of agents from one
     call) is refused unless the CEO unlocked it.
  5. THE SELF-EDIT LOCK: Edit/Write on this file, its state or its unlock
     file is refused - the guard rail is not the manager's to move.

ONLY THE CEO LIFTS A CAP, in a terminal the manager does not drive:
  python tools/hooks/fanout_guard.py --allow-agents N     # N more spawns this window
  python tools/hooks/fanout_guard.py --allow-workflow     # the Workflow tool, once
  python tools/hooks/fanout_guard.py --allow-tokens M     # +M weighted tokens for spawns
  python tools/hooks/fanout_guard.py --allow-edit         # editing this guard, 2 h
  python tools/hooks/fanout_guard.py --resume             # clear a HALT
  python tools/hooks/fanout_guard.py --status             # what the meter sees
  python tools/hooks/fanout_guard.py --selftest           # the pipe tests, in-process
The bash guard refuses the manager running anything but --status and
--selftest here. Unlocks expire after `unlock_hours`.

INSTALL ORDER MATTERS: copy this file UNWIRED, set LIMITS with the CEO,
run --selftest, add the unlock refusal to the bash guard, gitignore the
two state files, THEN wire the every-tool PreToolUse entry - it locks
its own files the moment the settings watcher sees it.

All numbers live in LIMITS (edit them, then --selftest). Weighted, not
raw, because cache reads dominate raw counts at a tenth of the price; a
normal turn re-reads ~100-200k of cache and must never trip anything.

Search keys: fan-out, sub-agent cap, agent limit, token budget, spend
meter, runaway agents, circuit breaker, halt, workflow lock, unlock.
See also: _hooklib.py; bash_guard.py (refuses the manager unlocking
itself); SUBAGENT_METHOD.md law 6 (THE FAN-OUT LAW, the manager-side
rule); HOOKS_METHOD.md Tier 2b (the contract + bootstrap).
"""
import json
import os
import sys
import time

from _hooklib import ROOT, deny, emit, read_input

LIMITS = dict(
    agents_warn=6,                  # spawns per session -> a warning line
    agents_cap=12,                  # spawns per session -> refused past this
    burst_cap=6,                    # spawns machine-wide inside burst_window -> refused
    burst_window=60,                # seconds
    tokens_warn_every=10_000_000,   # weighted tokens per session -> warn at each multiple
    tokens_agents_cap=30_000_000,   # weighted per session -> no more spawns past this
    velocity_window=120,            # seconds the velocity meter looks back
    velocity_warn=2_000_000,        # weighted inside the window -> warning (once per window)
    velocity_halt=6_000_000,        # weighted inside the window -> HALT every tool call
    unlock_hours=2,                 # every --allow expires after this
)
WEIGHTS = {"input_tokens": 1.0, "cache_creation_input_tokens": 1.25,
           "cache_read_input_tokens": 0.1, "output_tokens": 5.0}
STATE = os.path.join(ROOT, ".claude", "fanout_state.json")    # gitignored
UNLOCK = os.path.join(ROOT, ".claude", "fanout_unlock.json")  # gitignored, CEO-written
SPAWN_TOOLS = ("Agent", "Task")
WORKFLOW_TOOLS = ("Workflow",)
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
GUARDED_FILES = ("fanout_guard.py", "fanout_state.json", "fanout_unlock.json")
KEEP_SESSIONS = 20


# ---------------------------------------------------------------- state --
def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        os.replace(tmp, path)
    except Exception:
        pass


def _session(state, sid):
    sessions = state.setdefault("sessions", {})
    s = sessions.get(sid)
    if s is None:
        s = sessions[sid] = {"files": {}, "raw": 0, "weighted": 0.0,
                             "samples": [], "agents": [], "warned_level": 0,
                             "warned_velocity": 0, "warned_agents": False,
                             "halted": None, "seen": 0}
    s["seen"] = time.time()
    if len(sessions) > KEEP_SESSIONS:
        for old in sorted(sessions, key=lambda k: sessions[k].get("seen", 0))[:-KEEP_SESSIONS]:
            del sessions[old]
    return s


def _unlock(path=None):
    u = _load(path or UNLOCK)
    if u and u.get("expires", 0) < time.time():
        return {}
    return u


# ---------------------------------------------------------------- meter --
def _transcripts(transcript_path, sid):
    """The session transcript + every employee transcript under it."""
    out = []
    if transcript_path and os.path.isfile(transcript_path):
        out.append(transcript_path)
    base = os.path.join(os.path.dirname(transcript_path or ""), sid or "", "subagents")
    try:
        for name in os.listdir(base):
            if name.endswith(".jsonl"):
                out.append(os.path.join(base, name))
    except OSError:
        pass
    return out


def _meter(s, transcript_path, sid, now):
    """Fold every NEW usage record into the session totals; returns the
    weighted tokens added by this call."""
    added = 0.0
    for path in _transcripts(transcript_path, sid):
        backfill = path not in s["files"]  # first sight of a file: totals only,
        rec = s["files"].setdefault(path, {"off": 0, "last_id": ""})  # never velocity
        try:
            size = os.path.getsize(path)
            if size < rec["off"]:
                rec["off"] = 0  # truncated/rewritten: start over
            if size == rec["off"]:
                continue
            with open(path, "rb") as fh:
                fh.seek(rec["off"])
                chunk = fh.read()
        except OSError:
            continue
        if not chunk.endswith(b"\n"):
            cut = chunk.rfind(b"\n")
            if cut < 0:
                continue
            chunk = chunk[:cut + 1]
        rec["off"] += len(chunk)
        for ln in chunk.decode("utf-8", "replace").splitlines():
            try:
                msg = json.loads(ln).get("message") or {}
            except Exception:
                continue
            u = msg.get("usage")
            if not u:
                continue
            mid = msg.get("id") or ""
            if mid and mid == rec["last_id"]:
                continue  # a streamed message re-emitted its usage
            rec["last_id"] = mid
            raw = 0
            w = 0.0
            for k, mult in WEIGHTS.items():
                n = int(u.get(k) or 0)
                raw += n
                w += n * mult
            s["raw"] += raw
            s["weighted"] += w
            if not backfill:
                added += w
    if added:
        s["samples"].append([now, added])
    horizon = now - LIMITS["velocity_window"]
    s["samples"] = [x for x in s["samples"] if x[0] >= horizon]
    return added


def _velocity(s):
    return sum(x[1] for x in s["samples"])


def _fmt(n):
    return "%.1fM" % (n / 1e6) if n >= 1e6 else "%dk" % (n // 1000)


# ------------------------------------------------------------- evaluate --
def evaluate(data, state, unlock, now=None):
    """The decision for one tool call. Returns (verdict, message, state):
    verdict 'deny' | 'warn' | 'ok'. Pure apart from the clock."""
    now = now or time.time()
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    sid = data.get("session_id") or "unknown"
    s = _session(state, sid)
    warnings = []

    # 1. The spend meter.
    _meter(s, data.get("transcript_path"), sid, now)
    level = int(s["weighted"] // LIMITS["tokens_warn_every"])
    if level > s["warned_level"]:
        s["warned_level"] = level
        warnings.append("SPEND: this session has metered ~%s weighted tokens "
                        "(%s raw) - %d x the %s warning step"
                        % (_fmt(s["weighted"]), _fmt(s["raw"]), level,
                           _fmt(LIMITS["tokens_warn_every"])))
    vel = _velocity(s)
    if s["halted"]:
        return ("deny", s["halted"], state)
    if vel >= LIMITS["velocity_halt"]:
        s["halted"] = ("HALT (fanout_guard): ~%s weighted tokens in the last %d s "
                       "- that is a runaway, not work. Every tool call is refused "
                       "until the CEO runs `python tools/hooks/fanout_guard.py "
                       "--resume` in their own terminal. Report what was running "
                       "and stop." % (_fmt(vel), LIMITS["velocity_window"]))
        return ("deny", s["halted"], state)
    if vel >= LIMITS["velocity_warn"] and now - s["warned_velocity"] > LIMITS["velocity_window"]:
        s["warned_velocity"] = now
        warnings.append("VELOCITY: ~%s weighted tokens in the last %d s (halt at %s)"
                        % (_fmt(vel), LIMITS["velocity_window"], _fmt(LIMITS["velocity_halt"])))

    # 2. Spawns.
    if tool in SPAWN_TOOLS:
        spawns = state.setdefault("spawns", [])
        spawns[:] = [t for t in spawns if t >= now - LIMITS["burst_window"]]
        extra = int(unlock.get("agents_extra") or 0)
        n = len(s["agents"])
        if len(spawns) >= LIMITS["burst_cap"] + extra:
            return ("deny", "THE FAN-OUT LAW (fanout_guard): %d sub-agents were spawned "
                    "on this machine in the last %d s - that is the 821-agents shape. "
                    "Refused. Do not retry or work around it: stop, tell the CEO what "
                    "you were fanning out and why. Only they can lift it "
                    "(`python tools/hooks/fanout_guard.py --allow-agents N`)."
                    % (len(spawns), LIMITS["burst_window"]), state)
        if n >= LIMITS["agents_cap"] + extra:
            return ("deny", "THE FAN-OUT LAW (fanout_guard): %d sub-agents already this "
                    "session (cap %d). Refused. A task that needs more employees than "
                    "that is a design question for the CEO, not a fan-out - stop and "
                    "ask. They lift it with `python tools/hooks/fanout_guard.py "
                    "--allow-agents N`." % (n, LIMITS["agents_cap"] + extra), state)
        tok_cap = LIMITS["tokens_agents_cap"] + float(unlock.get("tokens_extra") or 0)
        if s["weighted"] >= tok_cap:
            return ("deny", "THE FAN-OUT LAW (fanout_guard): this session has metered "
                    "~%s weighted tokens (cap for new spawns %s). No more sub-agents "
                    "until the CEO says so (`python tools/hooks/fanout_guard.py "
                    "--allow-tokens M`). Stop and report." % (_fmt(s["weighted"]), _fmt(tok_cap)), state)
        s["agents"].append(now)
        spawns.append(now)
        if n + 1 >= LIMITS["agents_warn"] and not s["warned_agents"]:
            s["warned_agents"] = True
            warnings.append("AGENTS: %d sub-agents spawned this session (refusal at %d)"
                            % (n + 1, LIMITS["agents_cap"] + extra))

    # 3. Workflows.
    if tool in WORKFLOW_TOOLS and not unlock.get("workflow"):
        return ("deny", "THE FAN-OUT LAW (fanout_guard): the Workflow tool can spawn "
                "dozens of agents from one call and is locked. The CEO unlocks it per "
                "use with `python tools/hooks/fanout_guard.py --allow-workflow` in "
                "their own terminal. Ask them; do not use the Agent tool to imitate "
                "the workflow.", state)

    # 4. The guard's own files.
    if tool in EDIT_TOOLS and not unlock.get("edit"):
        target = str(tin.get("file_path") or tin.get("notebook_path") or "").replace("\\", "/")
        if any(target.endswith(g) for g in GUARDED_FILES):
            return ("deny", "THE FAN-OUT LAW (fanout_guard): the guard rail, its state "
                    "and its unlock file are not the manager's to edit. If the CEO "
                    "asked for a change, they run `python tools/hooks/fanout_guard.py "
                    "--allow-edit` first (2 h window); then edit and --selftest.", state)

    if warnings:
        return ("warn", "[HOOK fanout_guard] " + " | ".join(warnings)
                + " (relay to the CEO verbatim)", state)
    return ("ok", "", state)


# ------------------------------------------------------------------ CLI --
def _cli(argv):
    u = _unlock() or {}
    exp = time.time() + LIMITS["unlock_hours"] * 3600
    if "--status" in argv:
        st = _load(STATE)
        for sid, s in sorted((st.get("sessions") or {}).items(), key=lambda kv: -kv[1].get("seen", 0))[:5]:
            print("%s  weighted ~%s  raw ~%s  agents %d  velocity ~%s  %s"
                  % (sid[:8], _fmt(s["weighted"]), _fmt(s["raw"]), len(s["agents"]),
                     _fmt(_velocity(s)), "HALTED" if s.get("halted") else "ok"))
        print("machine-wide spawns in last %ds: %d" % (
            LIMITS["burst_window"],
            len([t for t in st.get("spawns", []) if t >= time.time() - LIMITS["burst_window"]])))
        print("unlock: %s" % (json.dumps(u) if u else "none"))
        return 0
    if "--selftest" in argv:
        return _selftest()
    changed = False
    if "--allow-agents" in argv:
        u["agents_extra"] = int(argv[argv.index("--allow-agents") + 1]); changed = True
    if "--allow-tokens" in argv:
        u["tokens_extra"] = float(argv[argv.index("--allow-tokens") + 1]); changed = True
    if "--allow-workflow" in argv:
        u["workflow"] = True; changed = True
    if "--allow-edit" in argv:
        u["edit"] = True; changed = True
    if "--resume" in argv:
        st = _load(STATE)
        for s in (st.get("sessions") or {}).values():
            s["halted"] = None
            s["samples"] = []
        st["spawns"] = []
        _save(STATE, st)
        print("resumed: halts cleared, velocity meters reset")
    if changed:
        u["expires"] = exp
        _save(UNLOCK, u)
        print("unlock written (expires in %dh): %s" % (LIMITS["unlock_hours"], json.dumps(u)))
    if not changed and "--resume" not in argv:
        print(__doc__.split("ONLY THE CEO LIFTS A CAP")[1].split("The bash guard")[0])
    return 0


def _selftest():
    """The pipe tests, in-process against a scratch transcript. PASS/FAIL."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="fanout_")
    sid = "selftest-session"
    tp = os.path.join(tmp, sid + ".jsonl")
    sub = os.path.join(tmp, sid, "subagents")
    os.makedirs(sub)

    def usage(path, mid, out, cr=0, cw=0, inp=0):
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"message": {"id": mid, "usage": {
                "input_tokens": inp, "output_tokens": out,
                "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw}}}) + "\n")

    def call(tool, state, unlock=None, now=None, **tin):
        d = {"tool_name": tool, "tool_input": tin, "session_id": sid, "transcript_path": tp}
        return evaluate(d, state, unlock or {}, now)

    fails = []

    def check(name, cond):
        print("  %s %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            fails.append(name)

    t0 = 1_000_000.0
    st = {}
    # a normal turn: ~150k cache read = 15k weighted, nothing fires
    usage(tp, "m1", 400, cr=150_000)
    v, m, st = call("Read", st, now=t0, file_path="x.gd")
    check("normal turn is silent", v == "ok")
    check("meter counts raw", st["sessions"][sid]["raw"] == 150_400)
    # the same message id re-emitted is not double counted
    usage(tp, "m1", 400, cr=150_000)
    v, m, st = call("Read", st, now=t0 + 1, file_path="x.gd")
    check("streamed duplicate ignored", st["sessions"][sid]["raw"] == 150_400)
    # employee transcripts are metered too
    usage(os.path.join(sub, "agent-1.jsonl"), "a1", 1000, inp=50_000)
    v, m, st = call("Read", st, now=t0 + 2, file_path="x.gd")
    check("employee transcript metered", st["sessions"][sid]["raw"] == 201_400)
    # spawns: warn at agents_warn, deny at agents_cap
    verdicts = []
    for i in range(LIMITS["agents_cap"] + 1):
        v, m, st = call("Agent", st, now=t0 + 100 + i * 30, prompt="x")
        verdicts.append(v)
    check("spawn warning at agents_warn", verdicts[LIMITS["agents_warn"] - 1] == "warn")
    check("spawn refused past agents_cap", verdicts[-1] == "deny" and verdicts[-2] != "deny")
    # --allow-agents lifts the cap
    v, m, st = call("Agent", st, unlock={"agents_extra": 5, "expires": 9e12}, now=t0 + 2000, prompt="x")
    check("unlock lifts the session cap", v != "deny")
    # burst: a fresh session, many spawns inside the window
    st2 = {}
    sid2 = sid
    burst = []
    for i in range(LIMITS["burst_cap"] + 1):
        d = {"tool_name": "Agent", "tool_input": {"prompt": "x"}, "session_id": sid2,
             "transcript_path": tp}
        v, m, st2 = evaluate(d, st2, {}, t0 + 5000 + i)
        burst.append(v)
    check("burst refused inside burst_window", burst[-1] == "deny" and "821" in m)
    # workflow locked / unlocked
    v, m, st = call("Workflow", st, now=t0 + 6000, script="x")
    check("workflow locked", v == "deny")
    v, m, st = call("Workflow", st, unlock={"workflow": True, "expires": 9e12}, now=t0 + 6001, script="x")
    check("workflow unlocked by the CEO", v != "deny")
    # self-edit lock
    v, m, st = call("Edit", st, now=t0 + 6002, file_path=os.path.join(ROOT, "tools", "hooks", "fanout_guard.py"))
    check("self-edit refused", v == "deny")
    v, m, st = call("Edit", st, now=t0 + 6003, file_path=os.path.join(ROOT, "tools", "hooks", "bash_guard.py"))
    check("other hooks editable", v != "deny")
    # velocity halt: a burst of output tokens inside the window
    st3 = {}
    tp3 = os.path.join(tmp, "runaway.jsonl")
    usage(tp3, "r1", int(LIMITS["velocity_halt"] / WEIGHTS["output_tokens"]) + 1)
    d = {"tool_name": "Read", "tool_input": {}, "session_id": "runaway", "transcript_path": tp3}
    v, m, st3 = evaluate(d, st3, {}, t0 + 6999)  # first sight = backfill, no velocity
    check("first sight of a big transcript never halts", v == "ok")
    usage(tp3, "r2", int(LIMITS["velocity_halt"] / WEIGHTS["output_tokens"]) + 1)
    v, m, st3 = evaluate(d, st3, {}, t0 + 7000)
    check("runaway velocity halts", v == "deny" and "HALT" in m)
    v, m, st3 = evaluate(d, st3, {}, t0 + 7001)
    check("halt is sticky", v == "deny")
    st3["sessions"]["runaway"]["halted"] = None
    st3["sessions"]["runaway"]["samples"] = []
    v, m, st3 = evaluate(d, st3, {}, t0 + 7002)
    check("resume clears the halt", v == "ok")
    # spend warning at the first multiple (a long session creeping over
    # the step; one message that big would be a velocity halt instead)
    st4 = {}
    tp4 = os.path.join(tmp, "spend.jsonl")
    d = {"tool_name": "Read", "tool_input": {}, "session_id": "spend", "transcript_path": tp4}
    v, m, st4 = evaluate(d, st4, {}, t0 + 7900)
    st4["sessions"]["spend"]["weighted"] = LIMITS["tokens_warn_every"] - 1000
    usage(tp4, "s1", 0, cr=20_000)
    v, m, st4 = evaluate(d, st4, {}, t0 + 8000)
    check("spend warning at the first step", v == "warn" and "SPEND" in m)
    v, m, st4 = evaluate(d, st4, {}, t0 + 8001)
    check("spend warning fires once per step", v == "ok")
    print("fanout_guard selftest: %s" % ("PASS" if not fails else "FAIL " + ", ".join(fails)))
    return 0 if not fails else 1


def main():
    if len(sys.argv) > 1:
        sys.exit(_cli(sys.argv[1:]))
    data = read_input()
    if not data.get("tool_name"):
        return
    state = _load(STATE)
    try:
        verdict, msg, state = evaluate(data, state, _unlock())
    except Exception as e:  # a guard must never crash the turn
        verdict, msg = "ok", ""
        state.setdefault("errors", []).append(str(e)[:200])
        state["errors"] = state["errors"][-5:]
    _save(STATE, state)
    if verdict == "deny":
        deny(msg)
    elif verdict == "warn":
        emit({"systemMessage": msg,
              "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "additionalContext": msg}})


if __name__ == "__main__":
    main()

"""PreToolUse guard on EVERY tool: THE FAN-OUT LAW's circuit breaker (Tier 2b).

Mazhron's ask 2026-09-10, after a public report of a Claude that spun up
821 sub-agents and burned 50M+ tokens in 30 seconds on "check my markdown
files for consistency": "I want Rootstock to prevent this type of
catastrophe at the harness level." Loosened the same day at Mazhron's
word ("this might be too restrictive... I just wanted to prevent complete
runaway agents and gigantic token spend"): CATASTROPHE-ONLY. Nothing here
fires on real work, nothing needs a command to lift, and the manager is
never locked out of its own tools for more than a cooldown.

  REFUSES (the runaway shapes only):
  1. A BURST of spawns: more than `burst_cap` Agent/Task calls inside
     `burst_window` seconds, MACHINE-WIDE (821 agents in 30 s).
  2. A FLOOD of spawns: more than `flood_cap` inside `flood_window`
     seconds, per session (a slower runaway; 25 in ten minutes is not a
     delegation batch, it is a loop).
  3. RUNAWAY VELOCITY: `velocity_halt` WEIGHTED tokens inside
     `velocity_window` seconds -> every tool call is refused UNTIL THE
     WINDOW DRAINS (a cooldown, self-clearing; `--resume` clears it now).
     Weighted ~ cost: input 1, cache write 1.25, cache read 0.1, output 5;
     a normal turn re-reads ~100-200k of cache = ~20k weighted, nothing.

  WARNS (a systemMessage to the CEO + a context line to the manager,
  once per step, never a refusal):
  - spawn count every `agents_warn_every` per session;
  - session spend every `tokens_warn_every` weighted tokens;
  - velocity past `velocity_warn` inside the window;
  - the Workflow tool (bulk orchestration) - a reminder that it fans out.

  THE SPEND METER behind it reads the session transcript + its employee
  transcripts INCREMENTALLY (byte offsets in the state file; a warm call
  costs ~0.06 s). It sums the API's OWN usage fields per message - never
  transcript bytes - so a screenshot's base64 payload prices at 0 and
  pictures cost what the API charged (pixels). Checked 2026-09-11 after
  the usage sheet's picture-sizing fix raised the suspicion; selftested.
  The first sight of a file backfills totals without feeding velocity,
  so a mid-session install never halts on catch-up.

  python tools/hooks/fanout_guard.py --status     # what the meter sees
  python tools/hooks/fanout_guard.py --resume     # clear a halt/burst now
  python tools/hooks/fanout_guard.py --selftest   # the pipe tests, in-process
  python tools/hooks/fanout_guard.py --limits     # every number, current vs default
  python tools/hooks/fanout_guard.py --set burst_cap=12 flood_cap=40   # tune
  python tools/hooks/fanout_guard.py --defaults   # forget the tuning

THE NUMBERS (Mazhron's ask 2026-09-10, the /runaway skill): DEFAULTS
below are the script's; the owner's TUNED numbers live in
.claude/fanout_limits.json (COMMITTED - they travel with the repo and
survive a kit graft), written by `--set`, read fresh on every call. The
/runaway skill is the conversational front: it shows `--limits`, takes
the changes, runs `--set`, then `--selftest`. Only the owner tunes; the
manager never raises a limit on its own. The manager-side rule (never
fan out past a handful; a refusal = stop and report) is SUBAGENTS.md
rule 12; this hook is what makes it true on a bad day.

Search keys: fan-out, sub-agent cap, agent limit, token budget, spend
meter, runaway agents, runaway numbers, tune limits, circuit breaker,
halt, cooldown.
See also: tools/hooks/_hooklib.py; SUBAGENTS.md rule 12 (THE FAN-OUT
LAW); HOOKS_METHOD.md Tier 2b (portable); docs/systems/tooling.md (The
hooks).
"""
import json
import os
import sys
import time

from _hooklib import ROOT, deny, emit, read_input

DEFAULTS = dict(
    burst_cap=8,                    # spawns machine-wide inside burst_window -> refused
    burst_window=60,                # seconds
    flood_cap=25,                   # spawns per session inside flood_window -> refused
    flood_window=600,               # seconds
    agents_warn_every=10,           # spawns per session -> a warning at each multiple
    tokens_warn_every=10_000_000,   # weighted tokens per session -> a warning at each multiple
    velocity_window=120,            # seconds the velocity meter looks back
    velocity_warn=3_000_000,        # weighted inside the window -> warning (once per window)
    velocity_halt=10_000_000,       # weighted inside the window -> refuse until it drains
)
MEANING = {  # one line each, in the owner's words (the /runaway skill prints these)
    "burst_cap": "spawns on this MACHINE inside burst_window -> REFUSED (the 821-agents shape)",
    "burst_window": "seconds the burst counter looks back",
    "flood_cap": "spawns in one SESSION inside flood_window -> REFUSED (a loop, not a plan)",
    "flood_window": "seconds the flood counter looks back",
    "agents_warn_every": "spawns per session between AGENTS warnings (warn only)",
    "tokens_warn_every": "weighted tokens per session between SPEND warnings (warn only)",
    "velocity_window": "seconds the velocity meter looks back",
    "velocity_warn": "weighted tokens inside velocity_window -> VELOCITY warning (warn only)",
    "velocity_halt": "weighted tokens inside velocity_window -> EVERY tool call REFUSED until it drains",
}
CONFIG = os.path.join(ROOT, ".claude", "fanout_limits.json")  # COMMITTED: the owner's tuned numbers


def load_limits(path=CONFIG):
    """DEFAULTS overlaid with the owner's tuned numbers. A missing or broken
    file, an unknown key or a non-positive value falls back silently - the
    guard must never crash the turn over its own config."""
    limits = dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        for k, v in (raw or {}).items():
            if k in DEFAULTS and isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                limits[k] = int(v)
    except Exception:
        pass
    return limits


def set_limits(pairs, path=CONFIG):
    """Apply `key=value` strings to the config file. Returns (limits, errors);
    on any error nothing is written. Warn thresholds must stay below halt
    thresholds; everything else is the owner's call."""
    current = load_limits(path)
    errors = []
    for pair in pairs:
        if "=" not in pair:
            errors.append("expected key=value, got %r" % pair)
            continue
        k, v = pair.split("=", 1)
        k = k.strip()
        v = v.strip().replace("_", "").replace(",", "")
        if k not in DEFAULTS:
            errors.append("unknown key %r (see --limits)" % k)
            continue
        try:
            n = int(float(v))
        except ValueError:
            errors.append("%s: %r is not a number" % (k, v))
            continue
        if n <= 0:
            errors.append("%s: must be a positive integer" % k)
            continue
        current[k] = n
    if current["velocity_warn"] >= current["velocity_halt"]:
        errors.append("velocity_warn (%d) must stay below velocity_halt (%d)"
                      % (current["velocity_warn"], current["velocity_halt"]))
    if errors:
        return load_limits(path), errors
    tuned = {k: v for k, v in current.items() if v != DEFAULTS[k]}
    if tuned:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(tuned, fh, indent=2, sort_keys=True)
            fh.write("\n")
    elif os.path.exists(path):
        # THE PRESERVATION LAW (2026-09-10): the owner's file stays; an
        # all-defaults tuning is written as {} instead of removed.
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
    return current, []


def limits_table(limits=None):
    """The --limits printout: key, current, default, meaning."""
    limits = limits or load_limits()
    tuned = [k for k in DEFAULTS if limits[k] != DEFAULTS[k]]
    lines = ["fanout_guard limits (%s)" % (
        "TUNED in .claude/fanout_limits.json: " + ", ".join(tuned) if tuned
        else "all defaults; no .claude/fanout_limits.json")]
    lines.append("  %-18s %12s %12s  %s" % ("key", "current", "default", "meaning"))
    for k in DEFAULTS:
        mark = "*" if limits[k] != DEFAULTS[k] else " "
        lines.append("%s %-18s %12s %12s  %s" % (mark, k, "{:,}".format(limits[k]), "{:,}".format(DEFAULTS[k]), MEANING[k]))
    lines.append("  (* = tuned) weighted tokens ~ cost: input 1, cache write 1.25, cache read 0.1 (0.025 on Fable), output 5")
    return "\n".join(lines)


LIMITS = load_limits()
WEIGHTS = {"input_tokens": 1.0, "cache_creation_input_tokens": 1.25,
           "cache_read_input_tokens": 0.1, "output_tokens": 5.0}
# THE WEIGHTED COLUMN (the CEO's insight 2026-09-10, TOKEN_IDEAS 13): cache
# reads cost 0.025x on Claude Fable 5.1, 0.1x elsewhere - the same weights
# the usage sheet prices with, so the guard's meter and the sheet agree.
READ_MULT = {"fable": 0.025}


def read_weight(model):
    for key, mult in READ_MULT.items():
        if key in (model or ""):
            return mult
    return WEIGHTS["cache_read_input_tokens"]
STATE = os.path.join(ROOT, ".claude", "fanout_state.json")  # gitignored
SPAWN_TOOLS = ("Agent", "Task")
WORKFLOW_TOOLS = ("Workflow",)
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
                             "warned_velocity": 0, "warned_agents": 0,
                             "warned_workflow": False, "seen": 0}
    s["seen"] = time.time()
    if len(sessions) > KEEP_SESSIONS:
        for old in sorted(sessions, key=lambda k: sessions[k].get("seen", 0))[:-KEEP_SESSIONS]:
            del sessions[old]
    return s


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
            rmult = read_weight(msg.get("model"))
            for k, mult in WEIGHTS.items():
                n = int(u.get(k) or 0)
                raw += n
                w += n * (rmult if k == "cache_read_input_tokens" else mult)
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
def evaluate(data, state, now=None):
    """The decision for one tool call. Returns (verdict, message, state):
    verdict 'deny' | 'warn' | 'ok'. Pure apart from the clock."""
    now = now or time.time()
    tool = data.get("tool_name") or ""
    sid = data.get("session_id") or "unknown"
    s = _session(state, sid)
    warnings = []

    # 1. The spend meter + velocity.
    _meter(s, data.get("transcript_path"), sid, now)
    level = int(s["weighted"] // LIMITS["tokens_warn_every"])
    if level > s["warned_level"]:
        s["warned_level"] = level
        warnings.append("SPEND: this session has metered ~%s weighted tokens "
                        "(%s raw) - %d x the %s step"
                        % (_fmt(s["weighted"]), _fmt(s["raw"]), level,
                           _fmt(LIMITS["tokens_warn_every"])))
    vel = _velocity(s)
    if vel >= LIMITS["velocity_halt"]:
        return ("deny", "RUNAWAY (fanout_guard): ~%s weighted tokens in the last %d s "
                "- no real work spends like that. Tool calls are refused until the "
                "window drains (about %d s of quiet). Stop, tell Mazhron what was "
                "running, and do not resume the same loop."
                % (_fmt(vel), LIMITS["velocity_window"], LIMITS["velocity_window"]), state)
    if vel >= LIMITS["velocity_warn"] and now - s["warned_velocity"] > LIMITS["velocity_window"]:
        s["warned_velocity"] = now
        warnings.append("VELOCITY: ~%s weighted tokens in the last %d s (refusal at %s)"
                        % (_fmt(vel), LIMITS["velocity_window"], _fmt(LIMITS["velocity_halt"])))

    # 2. Spawns: refuse the runaway shapes, warn on the count.
    if tool in SPAWN_TOOLS:
        spawns = state.setdefault("spawns", [])
        spawns[:] = [t for t in spawns if t >= now - LIMITS["burst_window"]]
        if len(spawns) >= LIMITS["burst_cap"]:
            return ("deny", "THE FAN-OUT LAW (fanout_guard): %d sub-agents were spawned "
                    "on this machine in the last %d s - that is the 821-agents shape, "
                    "not a delegation batch. Refused. Stop, tell Mazhron what you were "
                    "fanning out and why; the window clears itself in a minute, but do "
                    "not resume the same fan-out." % (len(spawns), LIMITS["burst_window"]), state)
        recent = [t for t in s["agents"] if t >= now - LIMITS["flood_window"]]
        if len(recent) >= LIMITS["flood_cap"]:
            return ("deny", "THE FAN-OUT LAW (fanout_guard): %d sub-agents in the last %d "
                    "minutes - a loop, not a plan. Refused. A task that needs that many "
                    "employees is a design problem: split it, script it, or ask Mazhron."
                    % (len(recent), LIMITS["flood_window"] // 60), state)
        s["agents"].append(now)
        spawns.append(now)
        n = len(s["agents"])
        lvl = n // LIMITS["agents_warn_every"]
        if lvl > s["warned_agents"]:
            s["warned_agents"] = lvl
            warnings.append("AGENTS: %d sub-agents spawned this session" % n)

    # 3. Workflows: a reminder, never a refusal.
    if tool in WORKFLOW_TOOLS and not s["warned_workflow"]:
        s["warned_workflow"] = True
        warnings.append("WORKFLOW: a workflow fans out many agents from one call - "
                        "the burst/flood/velocity breakers still apply")

    if warnings:
        return ("warn", "[HOOK fanout_guard] " + " | ".join(warnings)
                + " (relay to Mazhron verbatim)", state)
    return ("ok", "", state)


# ------------------------------------------------------------------ CLI --
def _cli(argv):
    if "--status" in argv:
        st = _load(STATE)
        for sid, s in sorted((st.get("sessions") or {}).items(), key=lambda kv: -kv[1].get("seen", 0))[:5]:
            print("%s  weighted ~%s  raw ~%s  agents %d  velocity ~%s"
                  % (sid[:8], _fmt(s["weighted"]), _fmt(s["raw"]), len(s["agents"]),
                     _fmt(_velocity(s))))
        print("machine-wide spawns in last %ds: %d" % (
            LIMITS["burst_window"],
            len([t for t in st.get("spawns", []) if t >= time.time() - LIMITS["burst_window"]])))
        return 0
    if "--selftest" in argv:
        return _selftest()
    if "--limits" in argv:
        print(limits_table())
        return 0
    if "--set" in argv:
        pairs = [a for a in argv if a != "--set"]
        limits, errors = set_limits(pairs)
        if errors:
            print("not changed:\n  " + "\n  ".join(errors))
            return 1
        print(limits_table(limits))
        print("written; run --selftest to prove the guard still stands")
        return 0
    if "--defaults" in argv:
        if os.path.exists(CONFIG):
            with open(CONFIG, "w", encoding="utf-8") as fh:
                fh.write("{}\n")  # the preservation law: emptied, never removed
            print("tuning forgotten (%s now {})" % os.path.relpath(CONFIG, ROOT))
        else:
            print("already at defaults")
        print(limits_table(load_limits()))
        return 0
    if "--resume" in argv:
        st = _load(STATE)
        for s in (st.get("sessions") or {}).values():
            s["samples"] = []
            s["agents"] = []
        st["spawns"] = []
        _save(STATE, st)
        print("resumed: velocity meters and spawn windows cleared")
        return 0
    print(__doc__.split("  python tools/hooks")[0].split("THE SPEND METER")[0])
    return 0


def _selftest():
    """The pipe tests, in-process against a scratch transcript, ALWAYS at
    DEFAULTS (the owner's tuned numbers must never make them fail). PASS/FAIL."""
    global LIMITS
    tuned = LIMITS
    LIMITS = dict(DEFAULTS)
    try:
        return _selftest_body()
    finally:
        LIMITS = tuned


def _selftest_body():
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

    def call(tool, state, now=None, sess=sid, path=None, **tin):
        d = {"tool_name": tool, "tool_input": tin, "session_id": sess,
             "transcript_path": path or tp}
        return evaluate(d, state, now)

    fails = []

    def check(name, cond):
        print("  %s %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            fails.append(name)

    t0 = 1_000_000.0
    st = {}
    usage(tp, "m1", 400, cr=150_000)
    v, m, st = call("Read", st, now=t0, file_path="x.gd")
    check("normal turn is silent", v == "ok")
    check("meter counts raw", st["sessions"][sid]["raw"] == 150_400)
    usage(tp, "m1", 400, cr=150_000)
    v, m, st = call("Read", st, now=t0 + 1, file_path="x.gd")
    check("streamed duplicate ignored", st["sessions"][sid]["raw"] == 150_400)
    usage(os.path.join(sub, "agent-1.jsonl"), "a1", 1000, inp=50_000)
    v, m, st = call("Read", st, now=t0 + 2, file_path="x.gd")
    check("employee transcript metered", st["sessions"][sid]["raw"] == 201_400)
    # pictures: a screenshot read lands ~200 KB of base64 in the transcript;
    # the meter reads the API's usage fields only, so those bytes price at 0
    # (the 2026-09-10 "picture-sizing flaw" suspicion, disproved 2026-09-11)
    with open(tp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"role": "user", "content": [{"type": "tool_result",
                 "content": [{"type": "image", "source": {"data": "A" * 200_000}}]}]}}) + "\n")
    usage(tp, "m2", 10, cr=1_000)
    v, m, st = call("Read", st, now=t0 + 3, file_path="shot.png")
    check("a 200 KB screenshot in the transcript prices at 0 (usage fields only)",
          st["sessions"][sid]["raw"] == 202_410)
    # a real delegation batch: 4 parallel spawns, then 4 more a few minutes later
    vs = []
    for i in range(4):
        v, m, st = call("Agent", st, now=t0 + 100 + i, prompt="x")
        vs.append(v)
    check("a batch of 4 is silent", all(v == "ok" for v in vs))
    vs = []
    for i in range(4):
        v, m, st = call("Agent", st, now=t0 + 400 + i, prompt="x")
        vs.append(v)
    check("a second batch of 4 is silent", all(v == "ok" for v in vs))
    # spawn-count warning at the first multiple (10th spawn)
    v, m, st = call("Agent", st, now=t0 + 700, prompt="x")
    v, m, st = call("Agent", st, now=t0 + 701, prompt="x")
    check("warning at 10 spawns", v == "warn" and "AGENTS: 10" in m)
    # burst: a fresh session firing spawns back to back
    st2 = {}
    burst = []
    for i in range(LIMITS["burst_cap"] + 1):
        v, m, st2 = call("Agent", st2, now=t0 + 5000 + i, sess="burst", prompt="x")
        burst.append(v)
    check("burst refused inside burst_window", burst[-1] == "deny" and "821" in m
          and all(x != "deny" for x in burst[:-1]))
    v, m, st2 = call("Agent", st2, now=t0 + 5000 + LIMITS["burst_window"] + 5, sess="burst", prompt="x")
    check("burst window drains on its own", v != "deny")
    # flood: spaced past the burst window but many inside flood_window
    st3 = {}
    flood = []
    for i in range(LIMITS["flood_cap"] + 1):
        v, m, st3 = call("Agent", st3, now=t0 + 9000 + i * 15, sess="flood", prompt="x")
        flood.append(v)
    check("flood refused inside flood_window", flood[-1] == "deny" and "loop" in m
          and all(x != "deny" for x in flood[:-1]))
    # workflow: a reminder, not a refusal
    st4 = {}
    v, m, st4 = call("Workflow", st4, now=t0 + 12000, sess="wf", script="x")
    check("workflow warns, never refuses", v == "warn" and "WORKFLOW" in m)
    v, m, st4 = call("Workflow", st4, now=t0 + 12001, sess="wf", script="x")
    check("workflow reminder fires once", v == "ok")
    # velocity: first sight backfills; a runaway then refuses; the window drains
    st5 = {}
    tp5 = os.path.join(tmp, "runaway.jsonl")
    big = int(LIMITS["velocity_halt"] / WEIGHTS["output_tokens"]) + 1
    usage(tp5, "r1", big)
    v, m, st5 = call("Read", st5, now=t0 + 15000, sess="run", path=tp5)
    check("first sight of a big transcript never halts", v != "deny")
    usage(tp5, "r2", big)
    v, m, st5 = call("Read", st5, now=t0 + 15001, sess="run", path=tp5)
    check("runaway velocity refuses", v == "deny" and "RUNAWAY" in m)
    v, m, st5 = call("Read", st5, now=t0 + 15002, sess="run", path=tp5)
    check("still refused inside the window", v == "deny")
    v, m, st5 = call("Read", st5, now=t0 + 15001 + LIMITS["velocity_window"] + 1, sess="run", path=tp5)
    check("halt clears itself after the cooldown", v == "ok")
    # spend warning at the first multiple (a long session creeping over)
    st6 = {}
    tp6 = os.path.join(tmp, "spend.jsonl")
    v, m, st6 = call("Read", st6, now=t0 + 17900, sess="spend", path=tp6)
    st6["sessions"]["spend"]["weighted"] = LIMITS["tokens_warn_every"] - 1000
    usage(tp6, "s1", 0, cr=20_000)
    v, m, st6 = call("Read", st6, now=t0 + 18000, sess="spend", path=tp6)
    check("spend warning at the first step", v == "warn" and "SPEND" in m)
    v, m, st6 = call("Read", st6, now=t0 + 18001, sess="spend", path=tp6)
    check("spend warning fires once per step", v == "ok")
    # the owner's tuning: a config file overlays DEFAULTS; junk is ignored;
    # --set refuses a warn threshold above its halt and writes nothing
    cfg = os.path.join(tmp, "limits.json")
    lim, errs = set_limits(["burst_cap=12", "flood_cap=40"], path=cfg)
    check("--set writes the tuned keys", not errs and load_limits(cfg)["burst_cap"] == 12
          and load_limits(cfg)["flood_cap"] == 40 and load_limits(cfg)["burst_window"] == 60)
    lim, errs = set_limits(["velocity_warn=20000000"], path=cfg)
    check("--set refuses warn above halt", bool(errs)
          and load_limits(cfg)["velocity_warn"] == DEFAULTS["velocity_warn"])
    lim, errs = set_limits(["nonsense=5"], path=cfg)
    check("--set refuses an unknown key", bool(errs))
    with open(cfg, "w", encoding="utf-8") as fh:
        fh.write('{"burst_cap": -3, "flood_cap": "ten", "burst_window": 90, "made_up": 1}')
    lim = load_limits(cfg)
    check("junk config falls back per key", lim["burst_cap"] == 8 and lim["flood_cap"] == 25
          and lim["burst_window"] == 90 and "made_up" not in lim)
    lim, errs = set_limits(["burst_window=60"], path=cfg)
    # THE PRESERVATION LAW (2026-09-10): the file stays, emptied to {}.
    check("--set back to defaults empties the file, never removes it",
          not errs and os.path.exists(cfg)
          and open(cfg, encoding="utf-8").read().strip() == "{}")
    check("selftest ran at DEFAULTS", LIMITS == DEFAULTS)
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
        verdict, msg, state = evaluate(data, state)
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

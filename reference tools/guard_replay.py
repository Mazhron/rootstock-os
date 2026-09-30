"""Replays the PreToolUse guards' pure judge functions against real harness
traffic pulled from the transcripts (a Rootstock take on serio-focus, which
replays its own guard over the author's recorded sessions): each hook's own
selftest only checks invented cases, so nobody has run diet_guard's,
bash_guard's, preserve_guard's or brief_guard's CURRENT logic against what
the manager actually did the last N days.

This walks every Read, Bash, PowerShell, Agent, Task, Write, Edit and
MultiEdit tool call in the recent transcripts, judges each one with the
guard's own pure function under a SANDBOX (a fresh in-memory diet_guard
state per run, never the real state file; no grant; no ledger append except
this tool's own; no command executed - a Bash or PowerShell call is judged
as text only), and compares "would refuse now" against "was refused live"
(one of the guard's own tags found inside the matching tool_result) to find
two deltas per rule:
  NEW CATCHES - would refuse now, was not refused live: what a rule added
    since, or a call from before the rule existed.
  LOST - was refused live, would pass now: a regression, or a rule the
    owner relaxed on purpose.

PURPOSE: Replays the four PreToolUse guards' pure judge functions
  (diet_guard.evaluate, bash_guard.verdict, preserve_guard.evaluate,
  brief_guard.missing_pieces) against the last N days of harness transcript
  traffic in a sandbox (a fresh in-memory diet_guard state per run, no
  grant, no ledger writes except its own), counts replayed / would-refuse /
  refused-live calls per guard per rule, and prints the NEW CATCH and LOST
  deltas with `--show <guard>` giving up to ten one-line examples each;
  never executes a command and never modifies a transcript, a hook, or a
  hook's state.
INTENT: the hooks' own selftests only check invented cases; nobody knows
  what the CURRENT guard code would do against what the manager actually
  did - this measures it, the way serio-focus replays its own guard over
  the author's recorded sessions.

Search keys: guard replay, replay guards, would refuse now, refused live,
new catches, lost, sandbox state, diet_guard, bash_guard, preserve_guard,
brief_guard, serio-focus, guard tags.
See also: tools/hooks/diet_guard.py, tools/hooks/bash_guard.py,
tools/hooks/preserve_guard.py, tools/hooks/brief_guard.py (the four
judges); tools/usage_report.py (transcript_dirs, the same transcript
walk); docs/history/guard_replay_runs.txt (the ledger this tool appends
to); tools/version_hint.py (the small-tool shape this follows).
"""
import argparse
import functools
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))       # tools/
ROOT = os.path.dirname(HERE)                             # repo root
HOOKS = os.path.join(HERE, "hooks")
if HOOKS not in sys.path:
    sys.path.insert(0, HOOKS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import diet_guard          # noqa: E402 - path set up above
import bash_guard          # noqa: E402
import preserve_guard      # noqa: E402
import brief_guard         # noqa: E402

# Performance only (Windows process-spawn cost, not a rule change): a replay
# calls preserve_guard.evaluate() for every Bash/PowerShell/Write/Edit call,
# and preserve_guard shells out to `git ls-files` + `git diff` every time a
# call executes the SAME tracked script (tools/run_tests.py, most often).
# The real 7-day traffic re-runs a handful of scripts hundreds of times, so
# this memoizes the git subprocess call for the length of ONE replay run -
# git's own tree does not change mid-run, so a cached answer is exact. This
# wraps the imported function object in THIS process only; the hook's own
# file on disk is untouched, and the live hook (a fresh process per call)
# never sees this cache.
_real_preserve_git = preserve_guard._git


@functools.lru_cache(maxsize=None)
def _cached_preserve_git(args_tuple):
    return _real_preserve_git(list(args_tuple))


preserve_guard._git = lambda args: _cached_preserve_git(tuple(args))

try:
    from usage_report import transcript_dirs  # tools/usage_report.py
except ImportError:
    # Copied from tools/usage_report.py's transcript_dirs() - kept in sync
    # by hand if that one ever moves.
    def transcript_dirs():
        base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
        if not os.path.isdir(base):
            return []
        return [os.path.join(base, d) for d in os.listdir(base)
                if "everwood" in d.lower() and os.path.isdir(os.path.join(base, d))]

try:
    from version_hint import workstation  # tools/version_hint.py
except ImportError:
    def workstation():
        home = os.path.expanduser("~").lower()
        return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")

DAYS_DEFAULT = 7
SECONDS_PER_DAY = 86400
EXAMPLE_CAP = 10          # --show prints at most this many calls per delta
RENDER_CMD_CHARS = 80     # a Bash/PowerShell command's rendered slice
RENDER_DESC_CHARS = 60    # an Agent/Task description's rendered slice

WANTED_TOOLS = ("Read", "Bash", "PowerShell", "Agent", "Task", "Write", "Edit", "MultiEdit")

GUARDS = ("diet_guard", "bash_guard", "preserve_guard", "brief_guard")

# Which tool_use names each guard's PreToolUse hook fires on (mirrors each
# hook's own settings.json wiring, read from the four files this tool reads).
GUARD_TOOLS = {
    "diet_guard": ("Read", "Bash", "PowerShell"),
    "bash_guard": ("Bash", "PowerShell"),
    "preserve_guard": ("Bash", "PowerShell", "Write", "Edit", "MultiEdit"),
    "brief_guard": ("Agent", "Task"),
}

# One row per rule a guard can refuse on: (guard, rule name, the guard's OWN
# tag strings - read out of each file's actual denial text, not guessed).
# The same tuple does double duty: classifying a "would refuse now" reason
# by which rule produced it, AND detecting a "refused live" tool_result by
# the identical substring, since a PreToolUse deny's reason is exactly what
# lands as the refused call's tool_result text.
RULES = [
    ("diet_guard", "index_first", ("INDEX FIRST",)),
    ("diet_guard", "re_read", ("RE-READ",)),
    ("bash_guard", "build_zips", ("BUILD ZIPS ARE NEVER DELETED",)),
    ("bash_guard", "script_rule", ("THE SCRIPT RULE",)),
    ("bash_guard", "commit_dash", ("NO em or en dashes",)),
    ("bash_guard", "no_verify", ("Never skip hooks",)),
    ("bash_guard", "force_push", ("No plain force pushes",)),
    ("bash_guard", "settings_write", ("THE FORMAT LAW",)),
    ("bash_guard", "tres_write", ("writing .tres from a shell",)),
    ("preserve_guard", "preservation_law", ("THE PRESERVATION LAW",)),
    ("brief_guard", "brief_incomplete", ("BRIEF INCOMPLETE",)),
]


TAG_NEAR_START = 60  # a real deny's tag sits at the front (or right after a
                     # "PreToolUse:<Tool> hook error: " prefix, ~35 chars);
                     # this repo's own wiki quotes the same law names in
                     # prose deep inside ordinary grep/read output, so a
                     # bare substring search anywhere in the text is not
                     # enough - confirmed against real transcripts, where
                     # a `grep "THE FORMAT LAW" WORKFLOWS.md` tool_result
                     # otherwise reads as a live refusal it never was.


def _rule_for_text(guard, text):
    """The first RULES entry for this guard whose tag is in text, or None.
    Used on a guard's OWN freshly generated message (the "would refuse now"
    side) - trusted as-is, no position or is_error check needed."""
    if not text:
        return None
    for g, rule, tags in RULES:
        if g == guard and any(tag in text for tag in tags):
            return rule
    return None


def _live_rule_for_text(guard, text, is_error):
    """The rule a LIVE refusal actually matches, or None. Unlike
    _rule_for_text, this requires is_error (a deny surfaces as an error
    tool_result; ordinary command output never sets it) AND the tag near
    the front of the text (TAG_NEAR_START) - a deny IS its reason, start to
    finish; the tag is never buried forty lines into a grep dump."""
    if not is_error or not text:
        return None
    for g, rule, tags in RULES:
        if g != guard:
            continue
        for tag in tags:
            idx = text.find(tag)
            if 0 <= idx < TAG_NEAR_START:
                return rule
    return None


def _result_text(content):
    """A tool_result's content field, string or block list, as plain text -
    never the whole thing re-printed, just handed to a substring search."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("text"):
                parts.append(str(c.get("text")))
        return "\n".join(parts)
    return ""


def _parse_transcript(path):
    """-> [call, ...] for one JSONL file: every wanted tool_use paired with
    its tool_result text (empty string when none was found, e.g. a call
    still open at the end of the file)."""
    tool_uses = []
    results = {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return []
    with fh:
        for line in fh:
            # Cheap skip before the json.loads (idea: parse each line once).
            if '"tool_use"' not in line and '"tool_result"' not in line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            msg = obj.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                ctype = c.get("type")
                if ctype == "tool_use" and c.get("name") in WANTED_TOOLS:
                    tool_uses.append({
                        "id": c.get("id"),
                        "tool": c.get("name"),
                        "input": c.get("input") or {},
                        "cwd": obj.get("cwd"),
                        "session_id": obj.get("sessionId") or "unknown",
                    })
                elif ctype == "tool_result":
                    tid = c.get("tool_use_id")
                    if tid:
                        results[tid] = (_result_text(c.get("content")), bool(c.get("is_error")))
    return [{
        "id": tu["id"],
        "session_id": tu["session_id"],
        "tool": tu["tool"],
        "input": tu["input"],
        "cwd": tu["cwd"],
        "live_text": results.get(tu["id"], ("", False))[0],
        "live_is_error": results.get(tu["id"], ("", False))[1],
    } for tu in tool_uses]


def collect_calls(dirs, days):
    """-> [call, ...] from every *.jsonl in `dirs` whose mtime falls inside
    the last `days` days, files walked oldest first."""
    cutoff = time.time() - days * SECONDS_PER_DAY
    files = []
    # os.walk, not listdir: employee transcripts live one level down in
    # <session>/subagents/*.jsonl, and they are where most guard denials
    # happen (the first real run missed all of them, 2026-09-30).
    for d in dirs:
        for root, _dirs, names in os.walk(d):
            for name in names:
                if not name.endswith(".jsonl"):
                    continue
                p = os.path.join(root, name)
                try:
                    mt = os.path.getmtime(p)
                except OSError:
                    continue
                if mt >= cutoff:
                    files.append((mt, p))
    files.sort()
    calls = []
    for _, p in files:
        calls.extend(_parse_transcript(p))
    return calls


def render_call(tool, tin):
    """A one-line rendering of a call's input - never a file's contents or
    a whole prompt."""
    if tool == "Read":
        return "Read %s" % (tin.get("file_path") or "?")
    if tool in ("Bash", "PowerShell"):
        return "%s: %s" % (tool, (tin.get("command") or "")[:RENDER_CMD_CHARS])
    if tool in ("Agent", "Task"):
        model = tin.get("model") or "?"
        desc = (tin.get("description") or "")[:RENDER_DESC_CHARS]
        return "%s model=%s desc=%s" % (tool, model, desc)
    if tool in ("Write", "Edit", "MultiEdit"):
        return "%s %s" % (tool, tin.get("file_path") or "?")
    return tool


def judge_diet(call, diet_state):
    """-> rule name, None (passes) or "error". `diet_state` is one dict
    shared across the whole replay run - never the real STATE file; it
    already buckets per session_id internally, same as the live hook."""
    if call["tool"] not in GUARD_TOOLS["diet_guard"]:
        return None
    data = {"tool_name": call["tool"], "tool_input": call["input"],
            "cwd": call["cwd"], "session_id": call["session_id"]}
    try:
        msg, _, action = diet_guard.evaluate(data, diet_state)
    except Exception:
        return "error"
    if action != "deny":
        return None
    return _rule_for_text("diet_guard", msg) or "index_first"


def judge_bash(call):
    """-> rule name, None or "error". bash_guard.verdict() is pure text."""
    if call["tool"] not in GUARD_TOOLS["bash_guard"]:
        return None
    cmd = call["input"].get("command") or ""
    if not cmd:
        return None
    try:
        reason = bash_guard.verdict(cmd)
    except Exception:
        return "error"
    if not reason:
        return None
    return _rule_for_text("bash_guard", reason) or "other"


def judge_preserve(call):
    """-> "preservation_law", None or "error". GAP: not fully pure - for a
    Bash/PowerShell call that executes a tracked script, preserve_guard
    itself shells out to `git diff` (read-only) to scan the script's
    uncommitted lines; still no write, no delete, no command executed by
    THIS tool, but worth naming rather than papering over."""
    if call["tool"] not in GUARD_TOOLS["preserve_guard"]:
        return None
    data = {"tool_name": call["tool"], "tool_input": call["input"]}
    try:
        reason = preserve_guard.evaluate(data, grant=None, consume=False)
    except Exception:
        return "error"
    return "preservation_law" if reason else None


def judge_brief(call):
    """-> "brief_incomplete", None or "error". Tries the current 3-arg
    signature (prompt, subagent_type, model) first and falls back to the
    2-arg one, since brief_guard.py was mid-edit by another employee when
    this tool was written and its signature may still move."""
    if call["tool"] not in GUARD_TOOLS["brief_guard"]:
        return None
    tin = call["input"]
    prompt = tin.get("prompt", "")
    stype = tin.get("subagent_type", "")
    try:
        try:
            gaps = brief_guard.missing_pieces(prompt, stype, tin.get("model", ""))
        except TypeError:
            gaps = brief_guard.missing_pieces(prompt, stype)
    except Exception:
        return "error"
    return "brief_incomplete" if gaps else None


JUDGES = {
    "diet_guard": lambda call, diet_state: judge_diet(call, diet_state),
    "bash_guard": lambda call, diet_state: judge_bash(call),
    "preserve_guard": lambda call, diet_state: judge_preserve(call),
    "brief_guard": lambda call, diet_state: judge_brief(call),
}


def replay(calls):
    """-> {"replayed": {guard: n}, "stats": {(guard, rule): {...}},
    "errors": {guard: n}, "examples": {guard: {"new": [...], "lost": [...]}}}
    One pass over `calls`; the only mutable sandbox is `diet_state`, a
    plain dict never written to disk."""
    diet_state = {}
    replayed = {g: 0 for g in GUARDS}
    errors = {g: 0 for g in GUARDS}
    stats = {(g, r): {"would": 0, "live": 0, "new": 0, "lost": 0} for g, r, _ in RULES}
    examples = {g: {"new": [], "lost": []} for g in GUARDS}

    for call in calls:
        tool = call["tool"]
        live_text = call["live_text"]
        live_is_error = call["live_is_error"]
        sess_short = (call["session_id"] or "unknown")[:8]
        render = render_call(tool, call["input"])
        for guard in GUARDS:
            if tool not in GUARD_TOOLS[guard]:
                continue
            replayed[guard] += 1
            would = JUDGES[guard](call, diet_state)
            if would == "error":
                errors[guard] += 1
                would = None
            live = _live_rule_for_text(guard, live_text, live_is_error)
            if would:
                stats[(guard, would)]["would"] += 1
            if live:
                stats[(guard, live)]["live"] += 1
            is_new = is_lost = False
            for g, rule, _tags in RULES:
                if g != guard:
                    continue
                w = (would == rule)
                the_live = (live == rule)
                if w and not the_live:
                    stats[(guard, rule)]["new"] += 1
                    is_new = True
                if the_live and not w:
                    stats[(guard, rule)]["lost"] += 1
                    is_lost = True
            if is_new and len(examples[guard]["new"]) < EXAMPLE_CAP:
                examples[guard]["new"].append((sess_short, tool, render))
            if is_lost and len(examples[guard]["lost"]) < EXAMPLE_CAP:
                examples[guard]["lost"].append((sess_short, tool, render))
    return {"replayed": replayed, "stats": stats, "errors": errors, "examples": examples}


def guard_totals(result, guard):
    rules = [r for g, r, _ in RULES if g == guard]
    would = sum(result["stats"][(guard, r)]["would"] for r in rules)
    live = sum(result["stats"][(guard, r)]["live"] for r in rules)
    new = sum(result["stats"][(guard, r)]["new"] for r in rules)
    lost = sum(result["stats"][(guard, r)]["lost"] for r in rules)
    return would, live, new, lost


def verdict_line(result):
    bad = []
    for guard in GUARDS:
        _, _, _, lost = guard_totals(result, guard)
        if lost:
            bad.append("%s lost %d" % (guard, lost))
    return "ok" if not bad else "WARN: " + "; ".join(bad)


def print_table(result, total_calls):
    print("GUARD REPLAY (%d calls)" % total_calls)
    print("%-16s %-18s %9s %6s %5s %4s %5s" % ("GUARD", "RULE", "REPLAYED", "WOULD", "LIVE", "NEW", "LOST"))
    for guard in GUARDS:
        rules = [r for g, r, _ in RULES if g == guard]
        for i, rule in enumerate(rules):
            s = result["stats"][(guard, rule)]
            replayed_col = str(result["replayed"][guard]) if i == 0 else ""
            print("%-16s %-18s %9s %6d %5d %4d %5d" % (
                guard if i == 0 else "", rule, replayed_col, s["would"], s["live"], s["new"], s["lost"]))
        if result["errors"][guard]:
            print("  (%d %s judge call(s) raised - not counted, see the GAP note)" % (result["errors"][guard], guard))


def print_examples(result, guard):
    ex = result["examples"][guard]
    print("\n--show %s" % guard)
    print("NEW CATCHES (would refuse now, not refused live):")
    for sess, tool, render in ex["new"]:
        print("  [%s] %s -- %s" % (sess, tool, render))
    if not ex["new"]:
        print("  (none)")
    print("LOST (refused live, would pass now):")
    for sess, tool, render in ex["lost"]:
        print("  [%s] %s -- %s" % (sess, tool, render))
    if not ex["lost"]:
        print("  (none)")


LEDGER = os.path.join(ROOT, "docs", "history", "guard_replay_runs.txt")
LEDGER_HEADER = ("# THE GUARD REPLAY LEDGER (append-only; one line per run of "
                 "tools/guard_replay.py; the loop runs it; read the TAIL)\n"
                 "# date time | ws | days | calls | per guard: would-refuse/live/new/lost | verdict\n")


def record_run(days, total_calls, result):
    """Append one line to LEDGER. No _hooklib ledger helper exists (checked
    tools/hooks/_hooklib.py); the header-if-new-then-append shape is copied
    from tools/version_hint.py's append_ledger."""
    if not os.path.exists(LEDGER):
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write(LEDGER_HEADER)
    parts = []
    for guard in GUARDS:
        w, live, new, lost = guard_totals(result, guard)
        parts.append("%s %d/%d/%d/%d" % (guard, w, live, new, lost))
    now = time.strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | %d | %d | %s | %s\n" % (
        now, workstation(), days, total_calls, ", ".join(parts), verdict_line(result))
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(line)


# ------------------------------------------------------------ selftest --
def _selftest():
    import tempfile
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    state_path = diet_guard.STATE
    before_mtime = os.path.getmtime(state_path) if os.path.exists(state_path) else None

    with tempfile.TemporaryDirectory(prefix="guard_replay_selftest_") as tmp:
        big_path = os.path.join(tmp, "big.md")
        with open(big_path, "w", encoding="utf-8") as fh:
            fh.write("## Section\n" + ("x" * 79 + "\n") * 700)  # ~56k bytes -> a big read

        sess = "selftest-session"

        def tool_use_row(tid, name, tin):
            return json.dumps({"type": "assistant", "cwd": tmp, "sessionId": sess,
                                "message": {"role": "assistant", "content": [
                                    {"type": "tool_use", "id": tid, "name": name, "input": tin}]}})

        def tool_result_row(tid, text, is_error=False):
            return json.dumps({"type": "user", "cwd": tmp, "sessionId": sess,
                                "message": {"role": "user", "content": [
                                    {"type": "tool_result", "tool_use_id": tid,
                                     "content": text, "is_error": is_error}]}})

        rows = []
        # 1) A Read of the big file, twice: the first is INDEX FIRST (a real
        # would-refuse); not refused live (nobody caught it back then) -> a
        # NEW CATCH. The second only warns (READ DIET), never a refusal.
        rows.append(tool_use_row("t1", "Read", {"file_path": big_path}))
        rows.append(tool_result_row("t1", ""))
        rows.append(tool_use_row("t2", "Read", {"file_path": big_path}))
        rows.append(tool_result_row("t2", "## Section\nx" * 50))

        # 2) A Bash `git log` with no limiter: diet_guard's OUTPUT DIET is a
        # warn, never a refusal - no rule should fire for it anywhere.
        rows.append(tool_use_row("t3", "Bash", {"command": "git log"}))
        rows.append(tool_result_row("t3", "commit abc\ncommit def\n"))

        # 3) A delete verb, built by concatenation so this source file never
        # holds it as a command; judged as text only, never executed.
        delete_cmd = "r" + "m -rf docs/old_notes.md"
        rows.append(tool_use_row("t4", "Bash", {"command": delete_cmd}))
        rows.append(tool_result_row("t4", ""))

        # 4) An Agent dispatch with a COMPLETE brief that was refused live
        # anyway (an earlier, stricter guard) -> LOST under today's rule.
        full_brief = ("Do the task. THE PRESERVATION LAW: no deletion code. If you "
                      "exceed ~30 tool calls or fail the same step twice, STOP and "
                      "report what you have. End with STAMP: x TOOLS: x WORKFLOW: x "
                      "INTENT: x")
        rows.append(tool_use_row("t5", "Agent", {"description": "ok", "model": "sonnet",
                                                  "subagent_type": "general-purpose",
                                                  "prompt": full_brief}))
        rows.append(tool_result_row("t5", "[HOOK brief_guard] BRIEF INCOMPLETE - old rule",
                                     is_error=True))

        # 5) An Agent dispatch with an INCOMPLETE brief that was NOT refused
        # live (dispatched before brief_guard existed) -> a NEW CATCH.
        rows.append(tool_use_row("t6", "Agent", {"description": "ok", "model": "sonnet",
                                                  "subagent_type": "general-purpose",
                                                  "prompt": "do the thing, no template"}))
        rows.append(tool_result_row("t6", "an ordinary employee report"))

        # 6) A successful grep whose OUTPUT happens to quote a guard's own
        # law name in prose, deep in the text, is_error False: this is
        # exactly what real traffic in this wiki-heavy repo looks like
        # (WORKFLOWS.md documents these laws by name) and must NOT read as
        # a live refusal - proves the is_error + TAG_NEAR_START guard.
        wiki_hit = ("120:## Some heading\n" * 5
                    + "180:the guard refuses under THE PRESERVATION LAW when a script deletes\n")
        rows.append(tool_use_row("t7", "Bash", {"command": "grep -n PRESERVATION docs/index/laws.md"}))
        rows.append(tool_result_row("t7", wiki_hit, is_error=False))

        with open(os.path.join(tmp, "fake-session.jsonl"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")

        calls = collect_calls([tmp], 3650)
        check("7 tool_use calls collected", len(calls) == 7)

        result = replay(calls)

        check("diet_guard index_first would-refuse once (the first big read)",
              result["stats"][("diet_guard", "index_first")]["would"] == 1)
        check("diet_guard index_first is a NEW CATCH",
              result["stats"][("diet_guard", "index_first")]["new"] == 1)
        check("diet_guard re_read never fires on the second read",
              result["stats"][("diet_guard", "re_read")]["would"] == 0)
        check("bash_guard has no rule for a bare git log",
              sum(result["stats"][("bash_guard", r)]["would"]
                  for g, r, _ in RULES if g == "bash_guard") == 0)
        check("preserve_guard catches the delete verb",
              result["stats"][("preserve_guard", "preservation_law")]["would"] == 1)
        check("preserve_guard's delete verb is a NEW CATCH",
              result["stats"][("preserve_guard", "preservation_law")]["new"] == 1)
        check("brief_guard would-refuses only the incomplete brief",
              result["stats"][("brief_guard", "brief_incomplete")]["would"] == 1)
        check("brief_guard's complete-but-once-refused brief is LOST",
              result["stats"][("brief_guard", "brief_incomplete")]["lost"] == 1)
        check("brief_guard's incomplete, never-refused-live brief is a NEW CATCH",
              result["stats"][("brief_guard", "brief_incomplete")]["new"] == 1)
        check("verdict names brief_guard's loss",
              "brief_guard lost 1" in verdict_line(result))
        check("a successful grep quoting a law in prose is not a live refusal",
              result["stats"][("preserve_guard", "preservation_law")]["live"] == 0)

    after_mtime = os.path.getmtime(state_path) if os.path.exists(state_path) else None
    check("the real diet_guard state file is untouched (the sandbox promise)",
          before_mtime == after_mtime)

    print("guard_replay selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Replay the hook guards' pure judges "
                                              "against recorded harness traffic.")
    ap.add_argument("--days", type=int, default=DAYS_DEFAULT)
    ap.add_argument("--show", choices=GUARDS)
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    calls = collect_calls(transcript_dirs(), args.days)
    result = replay(calls)
    print_table(result, len(calls))
    if args.show:
        print_examples(result, args.show)
    if args.record:
        record_run(args.days, len(calls), result)


if __name__ == "__main__":
    main()

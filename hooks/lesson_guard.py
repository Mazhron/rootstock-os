"""PreToolUse hook: THE LESSON AT THE CHOICE - the lesson is surfaced when the
action is about to happen, not only when the prompt is typed (the CEO
2026-10-30).

THE OLD WAY STAYS WIRED (kept on purpose, the CEO: "keep a reference to the
old hook somewhere so we don't lose it. There may be a way to mix them in
the future"): tools/hooks/prompt_gauge.py THE LESSON LINE (the CEO
2026-09-20) matches the PROMPT's words against every LESSONS.md Keys line
and prints the matching headlines before the first tool call. This hook is
its action-time twin: it matches the TOOL CALL (the shell command, the file
path and the edit text, the employee brief) against the same Keys lines,
with the same matcher (tools/lesson_log.py match), and injects the DO
INSTEAD lines of each hit, once per entry per tool per session, as
additionalContext on the call. Both run; a future mix could let the
prompt-time line hand its hits to this one so a lesson the prompt already
named is not repeated at the action, or let this one fall silent on the
tools the prompt-time line covered.

WHY IT EXISTS (the CEO's question 2026-10-30: "you will look at a problem,
perform a task, then look at a lesson after it fails... Why does that keep
happening?"): the prompt names an outcome and the trap lives in a sub-step
the prompt never mentions, so the prompt-time match misses it; when it hits,
it prints a headline and the DO INSTEAD is in a 1000-line body; and the
Stop-side advisor (lesson_advisor.py) closes the loop AFTER the failure.
Nothing fired at the moment of the choice, phrased as the choice. This does.

THE TRIAL (the CEO 2026-10-30, "lets try the new work flow... keep track of
the hits and misses"): every SURFACED ledger line carries session=<id> so
tools/lesson_ladder.py can pair it with the Stop hook's ADVISED line of the
same session (a MISS) or not (a HIT). THE PLAN STEP NOTE: when a session
reaches PLAN_AFTER_WRITES write or edit calls and no `plan_check.py` run
was seen, one note asks for the plan step (tools/plan_check.py); once per
session, warn-only.

PURPOSE: PreToolUse hook on shell, write, edit and sub-agent calls that
  matches the call's text against LESSONS.md Keys lines and injects each
  hit's DO INSTEAD (or THE ONE RIGHT WAY) as additionalContext, once per
  entry per tool per session, ledgering one SURFACED line per hit with the
  session id; and notes once per session when writes begin with no plan
  step run.
INTENT: the CEO 2026-10-30: "Lets try the fix for the hook, please keep a
  reference to the old hook somewhere so we don't lose it. There may be a
  way to mix them in the future." - the lesson in front of the manager at
  the moment of the choice, in the words of the choice.

Search keys: lesson guard, lesson at the choice, pretooluse lesson, DO
INSTEAD, action-time match, prompt-time lesson line, mix the two hooks,
SURFACED, plan step note, unplanned writes.
See also: tools/hooks/prompt_gauge.py (THE LESSON LINE, the old way);
tools/hooks/lesson_advisor.py (the Stop end); tools/lesson_log.py (the
matcher and the ledger); tools/plan_check.py (the plan step);
tools/lesson_ladder.py (the hits and misses); LESSONS.md "The lesson was
there and I still tried the thing it says not to"; HOOKS_METHOD.md "Tier
4b - THE LESSON GUARD"; WORKFLOWS.md "Act on a prompt: the trial workflow
and the old way kept".
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _hooklib import ROOT, context, read_input  # noqa: E402

STATE = os.path.join(ROOT, ".claude", "lesson_guard_state.json")  # gitignored, per machine
TEXT_CAP = 2500      # characters of the call read for matching (a heredoc is long)
LINE_CAP = 260       # characters of DO INSTEAD injected per hit
PLAN_AFTER_WRITES = 3  # write or edit calls in a session before the plan step is asked for, once
SELF_FILES = ("LESSONS.md", "lesson_log.py", "lesson_guard.py", "lesson_advisor.py")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
PLAN_NOTE = ("[HOOK lesson_guard] PLAN STEP: %d write calls this session and no plan checked - "
             "`python tools/plan_check.py \"step\" \"step\" ...` scores the arc's steps against "
             "LESSONS and WORKFLOWS before the rest (the trial workflow, WORKFLOWS.md \"Act on a "
             "prompt\"); once per session.")


def gather_text(tool_name, tool_input):
    """The call's words: command, file path + edit text, or the brief."""
    ti = tool_input or {}
    if tool_name in ("Bash", "PowerShell"):
        txt = ti.get("command") or ""
    elif tool_name in WRITE_TOOLS:
        parts = [ti.get("file_path") or ti.get("notebook_path") or ""]
        for k in ("old_string", "new_string", "content", "new_source"):
            if ti.get(k):
                parts.append(str(ti[k])[:600])
        for e in ti.get("edits") or []:
            parts.append(str(e.get("new_string", ""))[:300])
        txt = " ".join(parts)
    elif tool_name in ("Agent", "Task"):
        txt = " ".join(str(ti.get(k) or "") for k in ("description", "prompt"))
    else:
        txt = ""
    return txt[:TEXT_CAP]


def is_self(text):
    """A call that edits or runs the lesson machinery itself stays silent."""
    low = (text or "").lower()
    return any(f.lower() in low for f in SELF_FILES)


def do_instead(entry):
    """The entry's DO INSTEAD clauses joined, else THE ONE RIGHT WAY, capped."""
    body = "\n".join(entry.get("body") or [])
    flat = re.sub(r"[ \t]+", " ", body)
    clauses = []
    for m in re.finditer(r"DO INSTEAD:\s*(.+?)(?=\n- |\n\n|\nNUANCE|\nSee also:|\Z)", flat, re.S):
        clauses.append(" ".join(m.group(1).split()))
    if not clauses:
        m = re.search(r"THE ONE RIGHT WAY:\s*(.+?)(?=\n\n|\n- |\Z)", flat, re.S)
        if m:
            clauses.append(" ".join(m.group(1).split()))
    out = " / ".join(clauses)
    return (out[:LINE_CAP - 3] + "...") if len(out) > LINE_CAP else out


def fresh_state(session_id):
    return {"session": session_id, "shown": [], "writes": 0, "planned": False, "plan_noted": False}


def track_plan(state, session_id, tool_name, text):
    """(state, note or ""): counts writes, marks a plan_check run, notes once."""
    state = dict(state or {})
    if state.get("session") != session_id:
        state = fresh_state(session_id)
    if tool_name in ("Bash", "PowerShell") and "plan_check.py" in (text or ""):
        state["planned"] = True
    note = ""
    if tool_name in WRITE_TOOLS:
        state["writes"] = int(state.get("writes") or 0) + 1
        if (state["writes"] >= PLAN_AFTER_WRITES and not state.get("planned")
                and not state.get("plan_noted")):
            state["plan_noted"] = True
            note = PLAN_NOTE % state["writes"]
    return state, note


def decide(hits, state, session_id, tool_name):
    """(lines to inject, new state). Once per entry per tool per session."""
    state = dict(state or {})
    if state.get("session") != session_id:
        state = fresh_state(session_id)
    shown = set(state.get("shown") or [])
    lines = []
    for _, e in hits:
        key = "%s:%s" % (tool_name, e["line"])
        if key in shown:
            continue
        shown.add(key)
        lines.append("  LESSONS.md line %d \"%s\" - DO INSTEAD: %s"
                     % (e["line"], e["heading"], do_instead(e) or "(read the entry)"))
    state["shown"] = sorted(shown)
    return lines, state


def _load_state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
    except OSError:
        pass


def main():
    data = read_input()
    tool = data.get("tool_name") or ""
    sid = data.get("session_id") or "?"
    text = gather_text(tool, data.get("tool_input") or {})
    state, note = track_plan(_load_state(), sid, tool, text)
    lines = []
    if text.strip() and not is_self(text):
        try:
            import lesson_log as ll
            hits = ll.match(text)
        except Exception:  # noqa: BLE001 - a hook never crashes the turn
            hits = []
        if hits:
            lines, state = decide(hits, state, sid, tool)
    _save_state(state)
    out = []
    if lines:
        out.append("[HOOK lesson_guard] LESSON AT THE CHOICE: this %s call hits %d LESSONS.md entr%s "
                   "- check the call against the DO INSTEAD before it runs (THE LESSON LAW):"
                   % (tool, len(lines), "y" if len(lines) == 1 else "ies"))
        out.extend(lines)
        try:
            ll.record("SURFACED", "session=%s | %s | %s"
                      % (sid, tool, " / ".join(x.strip().split(" - DO INSTEAD")[0] for x in lines)))
        except Exception:  # noqa: BLE001
            pass
    if note:
        out.append(note)
    if out:
        context("PreToolUse", "\n".join(out))
    sys.exit(0)


def _selftest():
    """Pure checks on gather_text / do_instead / decide / track_plan; never touches the state file."""
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    ok("a shell call's text is its command",
       gather_text("Bash", {"command": "git status --short"}) == "git status --short")
    ok("an edit's text is the path plus the edit",
       "WORKFLOWS.md" in gather_text("Edit", {"file_path": "WORKFLOWS.md", "new_string": "## X"}) and
       "## X" in gather_text("Edit", {"file_path": "WORKFLOWS.md", "new_string": "## X"}))
    ok("a brief's text is its prompt", "read the ledger" in gather_text("Agent", {"prompt": "read the ledger"}))
    ok("a read is not gathered", gather_text("Read", {"file_path": "x"}) == "")
    ok("a call on the lesson machinery is self", is_self("python tools/lesson_log.py --check"))
    ok("a plain call is not self", not is_self("python tools/run_all.py check"))
    e = {"heading": "H", "line": 7, "body": [
        "Tags: lessons, x | brief", "Keys: a b, c", "",
        "THE ONE RIGHT WAY: do the thing first.", "",
        "- TRIED (d): x. FAILED BECAUSE: y. DO INSTEAD: the first fix,",
        "  continued on the next line.",
        "- TRIED (d): z. DO INSTEAD: the second fix.",
        "- NUANCE: n.", "", "See also: s."]}
    di = do_instead(e)
    ok("DO INSTEAD clauses are joined and unwrapped",
       di == "the first fix, continued on the next line. / the second fix.")
    e2 = {"heading": "H2", "line": 9, "body": ["THE ONE RIGHT WAY: only this.", "", "See also: s."]}
    ok("no DO INSTEAD falls back to THE ONE RIGHT WAY", do_instead(e2) == "only this.")
    long_e = {"heading": "L", "line": 1, "body": ["- TRIED: a. DO INSTEAD: " + "w " * 400]}
    ok("the injected line is capped", len(do_instead(long_e)) <= LINE_CAP)
    hits = [(2, e), (2, e2)]
    lines, st = decide(hits, {}, "S1", "Bash")
    ok("a first hit injects one line per entry with its line number",
       len(lines) == 2 and "line 7" in lines[0] and "DO INSTEAD: the first fix" in lines[0])
    lines2, st = decide(hits, st, "S1", "Bash")
    ok("the same entry is silent on the same tool in the same session", lines2 == [])
    lines3, st = decide(hits, st, "S1", "Edit")
    ok("the same entry speaks again on another tool", len(lines3) == 2)
    lines4, st = decide(hits, st, "S2", "Bash")
    ok("a new session resets the shown set", len(lines4) == 2 and st["session"] == "S2")
    st, n1 = track_plan({}, "P1", "Edit", "WORKFLOWS.md")
    st, n2 = track_plan(st, "P1", "Write", "x.py")
    st, n3 = track_plan(st, "P1", "Edit", "y.md")
    ok("the plan note comes at the third unplanned write, not before",
       n1 == "" and n2 == "" and "PLAN STEP" in n3 and st["writes"] == 3)
    st, n4 = track_plan(st, "P1", "Edit", "z.md")
    ok("the plan note is once per session", n4 == "" and st["plan_noted"])
    st2, _ = track_plan({}, "P2", "Bash", "python tools/plan_check.py \"a\" \"b\"")
    for _ in range(4):
        st2, n = track_plan(st2, "P2", "Edit", "f.md")
    ok("a plan_check run silences the note for the session", st2["planned"] and n == "")
    st3, _ = track_plan(st2, "P3", "Edit", "f.md")
    ok("a new session resets the plan tracking", st3["writes"] == 1 and not st3["planned"])
    print("lesson_guard selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    main()

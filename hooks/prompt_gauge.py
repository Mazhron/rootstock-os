"""UserPromptSubmit hook: the context gauge + task counter, every prompt
(Tier 1, #3). SILENT unless a threshold is crossed - zero tokens on a
normal turn. When it speaks, the manager relays the line verbatim
(the CEO's 80% rule 2026-09-04; the 8/15 task thresholds 2026-09-02).

Since 2026-09-20 it also carries THE LESSON LINE (the CEO: "nothing surfaces
a lesson before I start"): the prompt's words are matched against the Keys
line of every LESSONS.md entry (tools/lesson_log.py match_lines) and the
matching headlines, at most three, are printed with their line numbers so the
manager reads the entry before the first tool call; a MATCHED line goes to
docs/history/lesson_runs.txt. Silent on a prompt that hits nothing.

Since 2026-09-13 it also carries THE KIT LINE: "KIT UNSYNCED" while a
portable original is newer than its kit copy or the kit folder is ahead
of the public mirror (tools/refresh_kit.py --check), silent otherwise.

Answers `--selftest` (house pattern: PASS/FAIL lines on the pure line
builder, never stdin or a real prompt).

PURPOSE: UserPromptSubmit hook that stays silent on a normal turn and, when
  a threshold is crossed, prints the checkpoint counter warning (8 tasks
  advised, 15 dire) and the context-remaining warning, plus since 2026-09-13
  a KIT UNSYNCED line when a portable original is newer than its kit copy,
  and since 2026-09-20 the LESSONS line naming the LESSONS.md entries whose
  Keys match the prompt, so the one right way is read before the first tool call.
INTENT: relays the checkpoint and context thresholds and the kit-sync check
  at zero cost on a normal turn, so the manager checkpoints or refreshes the
  kit only when the harness itself has detected the need.

Search keys: prompt hook, context gauge, 80 percent rule, task counter,
kit unsynced, lessons line, lesson loop.
See also: tools/checkpoint.py (thresholds + the transcript probe);
tools/hooks/stop_tick.py (the tick that feeds the counter); tools/lesson_log.py
(match_lines); LESSONS.md.
"""
import sys

from _hooklib import read_input  # noqa: F401  (sets sys.path)
import checkpoint as cp


def gauge_lines(n, load_):
    """The checkpoint + context lines the live hook prints, as a list."""
    lines = []
    if n >= 15:
        lines.append("!!!!! CHECKPOINT URGENT (%d tasks since last checkpoint) - "
                     "checkpoint before taking new work !!!!!" % n)
    elif n >= 8:
        lines.append("~~ CHECKPOINT ADVISED (%d tasks since last checkpoint) - "
                     "ADVISED MEANS DO IT: checkpoint at the end of this reply if "
                     "the arc is closed ~~" % n)
    if load_ is not None:
        remaining = max(0.0, 1.0 - load_ / float(cp.COMPACT_BUDGET))
        pct = round(remaining * 100)
        if remaining < 0.30:
            lines.append("!!!!! CHECKPOINT URGENT (CONTEXT: %d%% remaining, ~%dk "
                         "used) - checkpoint + /clear NOW; auto-compact is lossy "
                         "!!!!!" % (pct, load_ // 1000))
        elif remaining < 0.80:
            lines.append("~~ CHECKPOINT ADVISED (CONTEXT: %d%% remaining, ~%dk "
                         "used; the CEO's 80%% rule) - ADVISED MEANS DO IT: checkpoint "
                         "at the end of this reply if the arc is closed, so the CEO "
                         "can simply /clear ~~" % (pct, load_ // 1000))
    return lines


def main():
    data = read_input()
    ws = cp.which_ws()
    n = cp.load().get(ws, (0, ""))[0]
    load_ = cp.context_load()
    lines = gauge_lines(n, load_)
    if lines:
        print("[HOOK prompt_gauge] " + " | ".join(lines)
              + " (relay to the CEO verbatim)")
    # THE KIT LINE (the CEO 2026-09-13: whenever Rootstock is discussed, the
    # kit folder and the public repo are updated in the same batch): one
    # line while an original is newer than its kit copy or the kit is ahead
    # of the mirror.
    try:
        import refresh_kit as _rk
        _kit = _rk.check_line()
    except Exception:  # noqa: BLE001 - a hook never crashes the turn
        _kit = None
    if _kit:
        print("[HOOK prompt_gauge] " + _kit)
    # THE LESSON LINE (the CEO 2026-09-20): the entries whose Keys hit this
    # prompt, read before the first tool call. Silent when nothing matches.
    try:
        import lesson_log as _ll
        _lines = _ll.match_lines(data.get("prompt") or "")
    except Exception:  # noqa: BLE001 - a hook never crashes the turn
        _lines = []
    if _lines:
        print("[HOOK prompt_gauge] " + "\n".join(_lines))
        try:
            _ll.record("MATCHED", " / ".join(x.strip() for x in _lines[1:]))
        except Exception:  # noqa: BLE001
            pass


def _selftest():
    """Exercises gauge_lines() directly - never touches stdin or a prompt."""
    fails = 0
    ok = gauge_lines(0, None) == []
    print(("PASS  " if ok else "FAIL  ") + "n=0, no context load gives no lines")
    fails += not ok
    ok = any("ADVISED" in x for x in gauge_lines(8, None))
    print(("PASS  " if ok else "FAIL  ") + "n=8 gives an ADVISED line")
    fails += not ok
    ok = any("URGENT" in x for x in gauge_lines(15, None))
    print(("PASS  " if ok else "FAIL  ") + "n=15 gives an URGENT line")
    fails += not ok
    urgent_load = int(cp.COMPACT_BUDGET * 0.75)  # 25% remaining < 30%
    ok = any("CONTEXT" in x and "URGENT" in x for x in gauge_lines(0, urgent_load))
    print(("PASS  " if ok else "FAIL  ") + "under 30% remaining gives CONTEXT URGENT")
    fails += not ok
    advised_load = int(cp.COMPACT_BUDGET * 0.50)  # 50% remaining, 30-80%
    ok = any("CONTEXT" in x and "ADVISED" in x for x in gauge_lines(0, advised_load))
    print(("PASS  " if ok else "FAIL  ") + "30-80% remaining gives CONTEXT ADVISED")
    fails += not ok
    try:
        import lesson_log as _ll
        ok = any("LESSONS.md line" in x for x in _ll.match_lines(
            "brief an employee on the wetland species numbers and the lanes envelope"))
        print(("PASS  " if ok else "FAIL  ") + "a prompt hitting a LESSONS.md Keys line gets the lessons line")
        fails += not ok
        ok = _ll.match_lines("standup") == []
        print(("PASS  " if ok else "FAIL  ") + "a short prompt gets no lessons line")
        fails += not ok
    except ImportError:
        print("FAIL  lesson_log.py missing next to checkpoint.py")
        fails += 1
    print("prompt_gauge selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

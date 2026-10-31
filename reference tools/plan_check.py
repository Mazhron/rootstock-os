"""THE PLAN STEP (the trial workflow, Mazhron 2026-10-30): score an arc's steps
against the lesson book and the route index BEFORE the first write.

The prompt names an outcome; the trap lives in a sub-step the prompt never
mentions, so the prompt-time lesson line (prompt_gauge.py) cannot see it.
This script takes the plan itself, one line per step, each naming its tool,
file or script, and runs every step through the same matchers the hooks
use: tools/lesson_log.py match (the LESSONS.md Keys lines, printed with the
entry's DO INSTEAD) and tools/route_index.py match (the WORKFLOWS.md entry
and the loop script that already do the step). It prints one block per step
and ledgers one PLAN line in docs/history/lesson_runs.txt, so
tools/lesson_ladder.py can count how many arcs were planned.

PURPOSE: print, for each plan step given on the command line, a file or
  stdin, the LESSONS.md entries (with their DO INSTEAD), WORKFLOWS.md
  entries and loop scripts whose Keys hit the step's words, and ledger one
  PLAN line per run.
INTENT: Mazhron 2026-10-30: "Lets think about pre selection, selection and
  post selection of tools, context, lessons, workflows. How can we
  streamline this so we get the best and most efficient results without
  errors." - the manager's own diagnosis: nothing matched the plan, only
  the prompt. "Keep our current work flow on record, lets try the new
  work flow you just suggested."

Usage:
  python tools/plan_check.py "1. Edit WORKFLOWS.md: a new entry" "2. run law_gaps" ...
  python tools/plan_check.py --file plan.txt        (one step per line)
  echo "step" | python tools/plan_check.py -        (stdin)
  python tools/plan_check.py --selftest

Search keys: plan step, plan check, pre selection, score the plan, lesson
at the plan, route the step, trial workflow, PLAN line.
See also: tools/hooks/lesson_guard.py (the same matcher at the call, and
the PLAN STEP note after three unplanned writes); tools/lesson_ladder.py
(counts the PLAN lines); WORKFLOWS.md "Act on a prompt: the trial workflow
and the old way kept"; LESSONS.md "The lesson was there and I still tried
the thing it says not to".
"""
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "hooks"))   # a project: tools/hooks/
sys.path.insert(0, os.path.join(ROOT, "hooks"))    # the kit: hooks/ beside "reference tools/"

STEP_CAP = 30          # steps read at most
HIT_CAP = 3            # entries printed per matcher per step


def read_steps(argv):
    """The step lines from args, --file <path> or '-' (stdin); blanks dropped."""
    if "--file" in argv:
        path = argv[argv.index("--file") + 1]
        with open(path, encoding="utf-8") as fh:
            raw = fh.read().splitlines()
    elif "-" in argv:
        raw = sys.stdin.read().splitlines()
    else:
        raw = [a for a in argv if not a.startswith("--")]
    return [s.strip() for s in raw if s.strip()][:STEP_CAP]


def score_step(step):
    """(lesson hits, workflow hits, tool hits) for one step; each a list of entries."""
    import lesson_log as lessons_book
    import route_index as routes
    lessons = [e for _, e in lessons_book.match(step)][:HIT_CAP]
    wf, tl = routes.match(step)
    return lessons, [e for _, e in wf][:HIT_CAP], [e for _, e in tl][:HIT_CAP]


def _do_instead(entry):
    try:
        from lesson_guard import do_instead
        return do_instead(entry)
    except Exception:  # noqa: BLE001 - the hook module is optional here
        return entry.get("brief") or ""


def report(steps, scored):
    """The printed block: a summary line, then one numbered block per step."""
    nl = sum(len(s[0]) for s in scored)
    nw = sum(len(s[1]) for s in scored)
    nt = sum(len(s[2]) for s in scored)
    out = ["PLAN CHECK: %d step%s | lesson hits %d | workflow hits %d | tool hits %d"
           % (len(steps), "" if len(steps) == 1 else "s", nl, nw, nt)]
    for i, (step, (lessons, wfs, tools)) in enumerate(zip(steps, scored), 1):
        out.append("  %d. %s" % (i, step))
        for e in lessons:
            di = _do_instead(e)
            out.append("     LESSON line %d \"%s\"%s" % (e["line"], e["heading"],
                                                       (" - DO INSTEAD: " + di) if di else ""))
        for e in wfs:
            out.append("     WORKFLOW line %d \"%s\"" % (e["line"], e["heading"]))
        for e in tools:
            out.append("     TOOL %s - %s" % (e.get("path", "?"), "; ".join(e.get("keys", [])[:3])))
        if not (lessons or wfs or tools):
            out.append("     (no lesson, workflow or script names this step)")
    return out, (nl, nw, nt)


def main(argv):
    steps = read_steps(argv)
    if not steps:
        print("plan_check: give the steps as arguments, --file <path> or - for stdin")
        return 2
    scored = [score_step(s) for s in steps]
    lines, (nl, nw, nt) = report(steps, scored)
    print("\n".join(lines))
    try:
        import lesson_log as lessons_book
        lessons_book.record("PLAN", "steps %d | lessons %d | workflows %d | tools %d | %s"
                            % (len(steps), nl, nw, nt, steps[0][:80]))
    except Exception:  # noqa: BLE001
        pass
    return 0


def _selftest():
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    ok("args become steps, flags dropped, blanks dropped",
       read_steps(["--x", "a step", "", "  b  "]) == ["a step", "b"])
    les = {"heading": "H", "line": 5, "brief": "b", "body": ["- TRIED: t. DO INSTEAD: do x."]}
    wf = {"heading": "W", "line": 9, "keys": ["k"]}
    tl = {"path": "tools/t.py", "keys": ["k1", "k2", "k3", "k4"]}
    lines, counts = report(["one", "two"], [([les], [wf], [tl]), ([], [], [])])
    ok("the summary counts every matcher", counts == (1, 1, 1) and lines[0].startswith("PLAN CHECK: 2 steps"))
    ok("a lesson hit carries its DO INSTEAD", any("LESSON line 5" in x and "DO INSTEAD: do x." in x for x in lines))
    ok("a workflow hit names its line", any("WORKFLOW line 9" in x for x in lines))
    ok("a tool hit lists at most three keys", any(x.strip().startswith("TOOL tools/t.py") and "k4" not in x for x in lines))
    ok("an unmatched step says so", any("no lesson, workflow or script" in x for x in lines))
    try:
        import lesson_log  # noqa: F401
        import route_index  # noqa: F401
        real = score_step("write the WORKFLOWS.md entry for the new hook and run the check loop")
        ok("the real matchers answer a real step", isinstance(real, tuple) and len(real) == 3)
    except Exception as exc:  # noqa: BLE001
        ok("the real matchers import (%s)" % exc, False)
    print("plan_check selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main(sys.argv[1:]))

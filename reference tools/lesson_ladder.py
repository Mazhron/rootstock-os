"""THE LADDER (the trial workflow's scorer, the CEO 2026-10-30): the lesson
loop's two faces scored over the one ledger, and the lesson that keeps
failing as a lesson proposed one rung down.

ONE DATA SET, TWO FACES (LESSONS.md "Give a system a second face the player
can switch back to"): docs/history/lesson_runs.txt holds every event of the
loop. The OLD FACE is the prompt-time line (prompt_gauge.py writes MATCHED
when a prompt's words hit a Keys line). The NEW FACE is the lesson guard
(lesson_guard.py writes SURFACED when a tool call's words hit one) and the
plan step (plan_check.py writes PLAN). Both faces end at the same Stop hook
(lesson_advisor.py writes ADVISED after a fail-then-pass or an error). This
script pairs them: a MATCHED or SURFACED followed by an ADVISED within
PAIR_MINUTES (same workstation; same session when both carry one) is a
MISS - the lesson was in front of the manager and the failure came anyway;
one with no ADVISED after it is a HIT. An ADVISED with nothing before it is
UNCOVERED: neither face saw it coming. The ladder rule: a lesson missed
twice is proven insufficient as a lesson and is proposed one rung down -
lesson (judgment) -> WORKFLOWS step -> loop script -> refusing hook.

PURPOSE: read docs/history/lesson_runs.txt, pair MATCHED (old face) and
  SURFACED (new face) events with a following ADVISED to count hits and
  misses per face, count UNCOVERED advisories and PLAN lines, print a
  PROPOSE [DO] for any lesson missed twice, and append one line to
  docs/history/workflow_trial_runs.txt (run_all check group).
INTENT: the CEO 2026-10-30: "We should keep track of the hits and misses
  (ledger them) so we can keep track of success or failure of the new
  workflow concept." and "keep a record of the old way."

Usage: python tools/lesson_ladder.py [--days N] [--no-record] [--selftest]

Search keys: lesson ladder, trial ledger, hits and misses, old face, new
face, SURFACED, MATCHED, ADVISED, uncovered, move down a rung, workflow
trial, PROPOSE DO lesson missed twice.
See also: tools/hooks/lesson_guard.py; tools/hooks/prompt_gauge.py (THE
LESSON LINE); tools/hooks/lesson_advisor.py; tools/plan_check.py;
WORKFLOWS.md "Act on a prompt: the trial workflow and the old way kept";
LESSONS.md "The lesson was there and I still tried the thing it says not
to"; docs/systems/tooling.md "The loop".
"""
import datetime
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
SOURCE = os.path.join(ROOT, "docs", "history", "lesson_runs.txt")
LEDGER = os.path.join(ROOT, "docs", "history", "workflow_trial_runs.txt")
HEADER = (
    "# THE WORKFLOW TRIAL LEDGER (append-only; one line per run of tools/lesson_ladder.py: the "
    "lesson loop's two faces scored over docs/history/lesson_runs.txt; MISS = the lesson was "
    "shown and an ADVISED followed within %d min). Read the TAIL.\n"
    "# date time | ws | window | old face: matched N hit N miss N | new face: surfaced N hit N "
    "miss N | uncovered advised N | plans N | verdict\n"
)
PAIR_MINUTES = 20
MISS_RUNG = 2            # misses on one lesson that propose the move down a rung
_SESSION = re.compile(r"session=(\S+)")
_LESSON = re.compile(r"LESSONS\.md line (\d+)")


def parse(text):
    """[{t, ws, kind, detail, session, lessons[]}] from the ledger text, time order."""
    out = []
    for raw in (text or "").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = [p.strip() for p in raw.split(" | ")]
        if len(parts) < 4:
            continue
        try:
            t = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        detail = " | ".join(parts[3:])
        m = _SESSION.search(detail)
        out.append({"t": t, "ws": parts[1], "kind": parts[2], "detail": detail,
                    "session": m.group(1) if m else None,
                    "lessons": [int(x) for x in _LESSON.findall(detail)]})
    out.sort(key=lambda e: e["t"])
    return out


def _same_thread(a, b):
    if a["ws"] != b["ws"]:
        return False
    if a["session"] and b["session"]:
        return a["session"] == b["session"]
    return True


def score(events, since=None):
    """The counts dict for the events at or after `since` (a datetime or None)."""
    evs = [e for e in events if since is None or e["t"] >= since]
    advised = [e for e in evs if e["kind"] == "ADVISED"]
    window = datetime.timedelta(minutes=PAIR_MINUTES)
    res = {"old": {"n": 0, "hit": 0, "miss": 0}, "new": {"n": 0, "hit": 0, "miss": 0},
           "uncovered": 0, "plans": sum(1 for e in evs if e["kind"] == "PLAN"),
           "misses_by_lesson": {}}
    covered = set()
    for e in evs:
        face = "old" if e["kind"] == "MATCHED" else ("new" if e["kind"] == "SURFACED" else None)
        if not face:
            continue
        res[face]["n"] += 1
        pair = None
        for a in advised:
            if e["t"] <= a["t"] <= e["t"] + window and _same_thread(e, a):
                pair = a
                break
        if pair is None:
            res[face]["hit"] += 1
        else:
            res[face]["miss"] += 1
            covered.add(id(pair))
            for ln in e["lessons"]:
                res["misses_by_lesson"][ln] = res["misses_by_lesson"].get(ln, 0) + 1
    res["uncovered"] = sum(1 for a in advised if id(a) not in covered)
    return res


def verdict(res):
    due = sorted(ln for ln, n in res["misses_by_lesson"].items() if n >= MISS_RUNG)
    if due:
        return ("PROPOSE [DO] LESSONS.md line%s %s missed %d+ times: move the DO INSTEAD down a rung "
                "(a WORKFLOWS step, a loop script or a refusing hook)"
                % ("s" if len(due) > 1 else "", ", ".join(str(x) for x in due), MISS_RUNG))
    return "ok"


def line(res, ws, label, now=None):
    now = now or datetime.datetime.now()
    return ("%s | %s | %s | old face: matched %d hit %d miss %d | new face: surfaced %d hit %d miss %d "
            "| uncovered advised %d | plans %d | %s"
            % (now.strftime("%Y-%m-%d %H:%M"), ws, label,
               res["old"]["n"], res["old"]["hit"], res["old"]["miss"],
               res["new"]["n"], res["new"]["hit"], res["new"]["miss"],
               res["uncovered"], res["plans"], verdict(res)))


def _workstation():
    try:
        import lesson_log as ll
        return ll.workstation()
    except Exception:  # noqa: BLE001
        return "WS?"


def main(argv):
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 0
    try:
        with open(SOURCE, encoding="utf-8") as fh:
            events = parse(fh.read())
    except OSError:
        events = []
    since = (datetime.datetime.now() - datetime.timedelta(days=days)) if days else None
    res = score(events, since)
    out = line(res, _workstation(), ("last %dd" % days) if days else "all")
    print("LADDER: " + out)
    if "--no-record" not in argv:
        try:
            fresh = not os.path.isfile(LEDGER)
            if fresh:
                os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
                with open(LEDGER, "w", encoding="utf-8") as fh:
                    fh.write(HEADER % PAIR_MINUTES)
            from _ledger import append_unless_identical
            append_unless_identical(LEDGER, out, payload_from_col=2, note_prefix="[lesson_ladder] ")
        except Exception:  # noqa: BLE001 - a ledger write never fails the loop
            with open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(out + "\n")
    return 0


def _selftest():
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    txt = (
        "# header\n"
        "2026-10-30 10:00 | WS2 | MATCHED | LESSONS.md line 100 \"A\"\n"
        "2026-10-30 10:05 | WS2 | ADVISED | an error was followed by a fix\n"
        "2026-10-30 11:00 | WS2 | SURFACED | session=A | Bash | LESSONS.md line 200 \"B\"\n"
        "2026-10-30 11:03 | WS2 | ADVISED | session=A | a FAIL was followed by a PASS\n"
        "2026-10-30 12:00 | WS2 | SURFACED | session=B | Edit | LESSONS.md line 200 \"B\"\n"
        "2026-10-30 12:02 | WS2 | ADVISED | session=C | a FAIL was followed by a PASS\n"
        "2026-10-30 12:30 | WS2 | SURFACED | session=B | Edit | LESSONS.md line 200 \"B\"\n"
        "2026-10-30 12:31 | WS2 | ADVISED | session=B | an error\n"
        "2026-10-30 13:00 | WS2 | SURFACED | session=D | Bash | LESSONS.md line 300 \"C\"\n"
        "2026-10-30 13:10 | WS2 | PLAN | steps 3 | lessons 1 | workflows 1 | tools 0 | x\n"
        "2026-10-30 14:00 | WS2 | CHECK | entries 45 | PASS\n"
    )
    ev = parse(txt)
    ok("the header is skipped and every data line parses (a CHECK line is an event the pairing ignores)",
       len(ev) == 11 and not any(e["kind"].startswith("#") for e in ev))
    ok("a session id is read from the detail", ev[2]["session"] == "A" and ev[0]["session"] is None)
    r = score(ev)
    ok("the old face: one matched, one miss", r["old"] == {"n": 1, "hit": 0, "miss": 1})
    ok("the new face: four surfaced, two hits, two misses", r["new"] == {"n": 4, "hit": 2, "miss": 2})
    ok("an ADVISED in another session is uncovered", r["uncovered"] == 1)
    ok("plans are counted", r["plans"] == 1)
    ok("a lesson missed twice is proposed down a rung",
       r["misses_by_lesson"].get(200) == 2 and "PROPOSE [DO]" in verdict(r) and "line 200" in verdict(r))
    r2 = score(ev, since=datetime.datetime(2026, 10, 30, 12, 45))
    ok("a window cuts the old events", r2["old"]["n"] == 0 and r2["new"]["n"] == 1 and verdict(r2) == "ok")
    ln = line(r, "WS2", "all", datetime.datetime(2026, 10, 30, 15, 0))
    ok("the ledger line has every column", ln.count(" | ") == 7 and "miss 2" in ln and ln.startswith("2026-10-30 15:00 | WS2 | all |"))
    ok("an empty ledger scores to zeros", score(parse("")) ["new"]["n"] == 0 and verdict(score([])) == "ok")
    print("lesson_ladder selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main(sys.argv[1:]))

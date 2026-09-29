"""LAW GAPS: two cheap checks for laws no other script measures (the CEO's
ruling 2026-09-29, asked whether three unmeasured laws should get ledgers):
"Generally the rule is that everything that can be measured should be, or
else we can't learn from it. It's just dust in the wind. Make the call, if
we can learn from it, and it doesn't increase our token costs by any
significant amount, yes."

    python tools/law_gaps.py              # runs both checks, prints both lines
    python tools/law_gaps.py --selftest    # exercises the pure parsers, no git, no ledgers

CHECK A, THE ARCHIVE SWEEP: parses docs/index/notes.md for actioned notes
that have not yet moved to docs/systems/history.md.
CHECK B, THE WORKFLOW RULE (a proxy): parses 30 days of git log for changed
tool files named nowhere in WORKFLOWS.md, tools/run_all.py (a loop script's
workflow is its group), .claude/settings.json (a hook's wiring) or a skill.

The manager's call left a third candidate, the contradiction rule, out on
purpose: it cannot be measured cheaply by script.

PURPOSE: Ledger two proxies for laws no other script measures: notes.md
  entries actioned but not swept to history.md, and tools changed in 30
  days that no WORKFLOWS.md entry, run_all group, hook setting or skill
  names.
INTENT: the CEO's ruling 2026-09-29 (quoted above): measure what can be
  measured cheaply, so it teaches instead of being dust in the wind; the
  contradiction rule is left out on purpose because it cannot be measured
  by script.

Search keys: archive sweep, workflow gap, law ledgers, unmeasured laws,
notes.md sweep.
See also: docs/index/laws.md "The archive sweep" and "The workflow rule";
docs/index/notes.md; WORKFLOWS.md; tools/run_all.py check group, which the
manager wires.
"""
import datetime
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_PATH = os.path.join(ROOT, "docs", "index", "notes.md")
WORKFLOWS_PATH = os.path.join(ROOT, "WORKFLOWS.md")
SWEEP_LEDGER = os.path.join(ROOT, "docs", "history", "sweep_audit_runs.txt")
GAP_LEDGER = os.path.join(ROOT, "docs", "history", "workflow_gap_runs.txt")

SWEEP_HEADER = (
    "# THE ARCHIVE SWEEP LEDGER (append-only; one line per run of tools/law_gaps.py's "
    "notes.md sweep check). Read the TAIL.\n"
    "# date time | ws | notes N | actioned unmoved N | open N | open older than 21d N | verdict\n"
)
GAP_HEADER = (
    "# THE WORKFLOW GAP LEDGER (append-only; one line per run of tools/law_gaps.py's "
    "30 day tool-change proxy for the workflow rule). Read the TAIL.\n"
    "# date time | ws | commits N | tools changed N | unnamed N | verdict | unnamed basenames\n"
)

NOTE_RE = re.compile(r"^-\s*\*\*→\s*(?P<target>.+?)\s*\((?P<status>.+?)\):\*\*", re.MULTILINE)
ACTIONED_WORDS = ("actioned", "done", "closed", "resolved")
# whole words only, so "undone" or "reclosed" never reads as actioned
ACTIONED_RE = re.compile(r"\b(?:%s)\b" % "|".join(ACTIONED_WORDS))
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}-\d{2}")

TOOL_PATH_RE = re.compile(
    r"^tools/[^/]+\.py$|^tools/hooks/[^/]+\.py$|^\.claude/skills/([^/]+)/SKILL\.md$"
)


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def parse_notes(text):
    """Pure parser: docs/index/notes.md body text -> list of note dicts.

    Each dict: target, status_text (the whole parenthesis), date (first
    YYYY-MM-DD or MM-DD found in it, else ""), actioned (True when the
    parenthesis contains ACTIONED, DONE, CLOSED or RESOLVED, case-insensitive).
    """
    notes = []
    for m in NOTE_RE.finditer(text):
        target = m.group("target").strip()
        status_text = m.group("status").strip()
        low = status_text.lower()
        actioned = ACTIONED_RE.search(low) is not None
        date_m = DATE_RE.search(status_text)
        date = date_m.group(0) if date_m else ""
        notes.append({
            "target": target,
            "status_text": status_text,
            "date": date,
            "actioned": actioned,
        })
    return notes


def _note_date_to_dt(date_str, today):
    """A note's date string (YYYY-MM-DD or MM-DD) -> a datetime.date, or None."""
    if not date_str:
        return None
    if len(date_str) == 10:
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    try:
        month, day = date_str.split("-")
        return datetime.date(today.year, int(month), int(day))
    except ValueError:
        return None


def sweep_counts(notes, today):
    """notes (parse_notes output) + today's date -> the sweep's four counts."""
    total = len(notes)
    actioned_unmoved = sum(1 for n in notes if n["actioned"])
    open_notes = [n for n in notes if n["status_text"].lower().startswith("open")]
    open_count = len(open_notes)
    cutoff = today - datetime.timedelta(days=21)
    open_older = 0
    for n in open_notes:
        d = _note_date_to_dt(n["date"], today)
        if d is not None and d < cutoff:
            open_older += 1
    return total, actioned_unmoved, open_count, open_older


def sweep_verdict(actioned_unmoved):
    if actioned_unmoved > 0:
        return "WARN: sweep due, %d actioned note(s) still in notes.md" % actioned_unmoved
    return "ok"


def parse_log(text):
    """Pure parser: `git log --format=%H%x09%s --name-only` output -> list of
    (hash, subject, [paths]).
    """
    commits = []
    current = None
    for line in text.splitlines():
        if "\t" in line:
            h, subject = line.split("\t", 1)
            if current is not None:
                commits.append(current)
            current = (h, subject, [])
        elif line.strip() == "":
            continue
        else:
            if current is not None:
                current[2].append(line.strip())
    if current is not None:
        commits.append(current)
    return commits


def _tool_basename(path):
    """A tool path (tools/*.py, tools/hooks/*.py or .claude/skills/*/SKILL.md)
    -> the name to search WORKFLOWS.md for, or None if not a tool path.
    """
    m = TOOL_PATH_RE.match(path)
    if not m:
        return None
    if path.startswith(".claude/skills/"):
        return m.group(1)
    return os.path.basename(path)


def find_candidates(commits, workflows_text):
    """commits (parse_log output) + WORKFLOWS.md text -> (tools_changed, unnamed)
    where tools_changed is a sorted list of distinct basenames touched in the
    window and unnamed is the subset not found anywhere in workflows_text.
    """
    basenames = set()
    for _h, _subject, paths in commits:
        for p in paths:
            b = _tool_basename(p)
            if b:
                basenames.add(b)
    tools_changed = sorted(basenames)
    unnamed = [b for b in tools_changed if b not in workflows_text]
    return tools_changed, unnamed


def gap_verdict(unnamed):
    n = len(unnamed)
    if n > 0:
        return "WARN: %d tool(s) changed in 30d and named in no WORKFLOWS.md entry, run_all group, hook setting or skill" % n
    return "ok"


def _append_ledger(path, header, line):
    is_new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if is_new:
            fh.write(header)
        fh.write(line + "\n")


def run_sweep(ws, now):
    with open(NOTES_PATH, "r", encoding="utf-8") as fh:
        text = fh.read()
    notes = parse_notes(text)
    total, actioned_unmoved, open_count, open_older = sweep_counts(notes, now.date())
    verdict = sweep_verdict(actioned_unmoved)
    stamp = now.strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | notes %d | actioned unmoved %d | open %d | open older than 21d %d | %s" % (
        stamp, ws, total, actioned_unmoved, open_count, open_older, verdict,
    )
    _append_ledger(SWEEP_LEDGER, SWEEP_HEADER, line)
    return line


def run_gap(ws, stamp):
    proc = subprocess.run(
        ["git", "log", "--since=30.days", "--format=%H%x09%s", "--name-only"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    text = proc.stdout
    commits = parse_log(text)
    # THE NAMED CORPUS (manager, 2026-09-29, after the first run flagged hooks and loop
    # scripts): a tool is 'named' when WORKFLOWS.md, tools/run_all.py (the loop is the
    # workflow of a loop script), .claude/settings.json (a hook's wiring) or any
    # .claude/skills/*/SKILL.md mentions its basename.
    workflows_text = ""
    for _p in [WORKFLOWS_PATH, os.path.join(ROOT, "tools", "run_all.py"),
               os.path.join(ROOT, ".claude", "settings.json")] + sorted(
            glob.glob(os.path.join(ROOT, ".claude", "skills", "*", "SKILL.md"))):
        try:
            with open(_p, encoding="utf-8") as fh:
                workflows_text += fh.read() + "\n"
        except OSError:
            pass
    tools_changed, unnamed = find_candidates(commits, workflows_text)
    verdict = gap_verdict(unnamed)
    shown = unnamed[:12]
    line = "%s | %s | commits %d | tools changed %d | unnamed %d | %s | %s" % (
        stamp, ws, len(commits), len(tools_changed), len(unnamed), verdict, ", ".join(shown),
    )
    _append_ledger(GAP_LEDGER, GAP_HEADER, line)
    return line


# --------------------------------------------------------------------------
# selftest


def _check(name, cond, results):
    if cond:
        print("PASS  %s" % name)
        results.append(True)
    else:
        print("FAIL  %s" % name)
        results.append(False)


def selftest():
    results = []

    # parse_notes: at least 3 cases (ACTIONED, standing, open with full date)
    notes_text = (
        "## Cross-workstation notes\n\n"
        "- **→ BOTH WS (standing - THE PIN BOARD, 2026-08-24):** pinned ideas live\n"
        "  elsewhere.\n\n"
        "- **→ WS1, from WS2 (open - 2026-09-22, the memory trim):** a task for WS1.\n\n"
        "- **→ BOTH WS, from WS1 (open - 09-11 PULL NOTE ACTIONED by WS2, 2026-09-12):**\n"
        "  WS2 pulled it; still open on paper.\n"
    )
    notes = parse_notes(notes_text)
    _check("parse_notes: three bullets found", len(notes) == 3, results)
    _check("parse_notes: targets in order",
           [n["target"] for n in notes] == ["BOTH WS", "WS1, from WS2", "BOTH WS, from WS1"],
           results)
    _check("parse_notes: standing note not actioned", notes[0]["actioned"] is False, results)
    _check("parse_notes: standing note full date", notes[0]["date"] == "2026-08-24", results)
    _check("parse_notes: open note not actioned", notes[1]["actioned"] is False, results)
    _check("parse_notes: open note full date", notes[1]["date"] == "2026-09-22", results)
    _check("parse_notes: ACTIONED note flagged", notes[2]["actioned"] is True, results)
    _check("parse_notes: ACTIONED note year-less date", notes[2]["date"] == "09-11", results)

    today = datetime.date(2026, 9, 29)
    total, actioned_unmoved, open_count, open_older = sweep_counts(notes, today)
    _check("sweep_counts: total 3", total == 3, results)
    _check("sweep_counts: actioned unmoved 1", actioned_unmoved == 1, results)
    _check("sweep_counts: open count 2", open_count == 2, results)
    _check("sweep_counts: open older than 21d 0", open_older == 0, results)
    _check("sweep_verdict: warns on actioned unmoved",
           sweep_verdict(1) == "WARN: sweep due, 1 actioned note(s) still in notes.md", results)
    _check("sweep_verdict: ok when none", sweep_verdict(0) == "ok", results)

    # a fourth case: an old open note, to prove the 21-day math
    old_notes = parse_notes(
        "- **→ WS1, from WS2 (open - 2026-08-01, an old ask):** still waiting.\n"
    )
    _, _, _, old_open_older = sweep_counts(old_notes, today)
    _check("sweep_counts: old open note counted older than 21d", old_open_older == 1, results)
    _check("parse_notes: a word that only contains 'done' is not actioned",
           parse_notes("- **→ WS2, from WS1 (open - 2026-09-29, the undone list):** x.\n")[0]["actioned"] is False,
           results)

    # parse_log: at least 3 cases, including two commits, one touching
    # tools/x.py and WORKFLOWS.md together
    log_text = (
        "aaa1111\tfirst commit touches a tool and WORKFLOWS.md\n"
        "tools/x.py\n"
        "WORKFLOWS.md\n"
        "\n"
        "bbb2222\tsecond commit touches an unrelated file\n"
        "docs/history/lesson_runs.txt\n"
        "\n"
        "ccc3333\tthird commit touches a hook and a skill\n"
        "tools/hooks/y.py\n"
        ".claude/skills/some_skill/SKILL.md\n"
    )
    commits = parse_log(log_text)
    _check("parse_log: three commits", len(commits) == 3, results)
    _check("parse_log: first commit hash/subject",
           commits[0][0] == "aaa1111" and commits[0][1] == "first commit touches a tool and WORKFLOWS.md",
           results)
    _check("parse_log: first commit two paths",
           commits[0][2] == ["tools/x.py", "WORKFLOWS.md"], results)
    _check("parse_log: second commit one path",
           commits[1][2] == ["docs/history/lesson_runs.txt"], results)
    _check("parse_log: third commit hook and skill paths",
           commits[2][2] == ["tools/hooks/y.py", ".claude/skills/some_skill/SKILL.md"], results)

    # candidate filter with a fake WORKFLOWS text
    workflows_text = "## Do a thing\nRun tools/x.py before you do anything else.\n"
    tools_changed, unnamed = find_candidates(commits, workflows_text)
    _check("find_candidates: three tool paths reduced to three basenames",
           tools_changed == ["some_skill", "x.py", "y.py"], results)
    _check("find_candidates: x.py named, others unnamed",
           unnamed == ["some_skill", "y.py"], results)
    _check("gap_verdict: warns with unnamed",
           gap_verdict(unnamed) == "WARN: 2 tool(s) changed in 30d and named in no WORKFLOWS.md entry, run_all group, hook setting or skill",
           results)
    _check("gap_verdict: ok when empty", gap_verdict([]) == "ok", results)

    failed = results.count(False)
    print("law_gaps selftest: %d failed" % failed)
    return failed


def main():
    if "--selftest" in sys.argv:
        failed = selftest()
        sys.exit(1 if failed else 0)

    ws = workstation()
    now = datetime.datetime.now()
    sweep_line = run_sweep(ws, now)
    gap_line = run_gap(ws, now.strftime("%Y-%m-%d %H:%M"))
    print("SWEEP: %s" % sweep_line)
    print("WORKFLOW GAPS: %s" % gap_line)
    sys.exit(0)


if __name__ == "__main__":
    main()

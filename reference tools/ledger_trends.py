"""Ledger trends -> PROPOSALS: the learning loop's closing step, read-only.

Mazhron's ask 2026-09-10 ("Is Rootstock implementing learning loops?"):
the ledgers already MEASURE (usage, tests, links, heat, employees,
compactions); this script reads their tails, compares them with the
THRESHOLDS below and prints proposed rule changes for the owner. It never
applies anything - a proposal is a sentence at standup, and the owner
decides. Standup calls it after THE BUDGET; run it alone any time.

Proposals (each names its ledger and the number that crossed):
  usage_daily.txt   >= N CHECK verdicts in the last 7 lines -> the read
                    diet is slipping; a rising whole-file-read average
  test_runs.txt     >= N FAIL lines in the last 10 -> a flaky group
  wiki_link_runs.txt  dead links > 0 -> fix them (the list is in
                    wiki_links.txt)
  wiki_heat_runs.txt  cold sections >= N -> propose a cold-shelf sweep
                    (candidates in wiki_heat.txt; nothing moves without
                    the owner's word)
  SUBAGENTS.md ledger  a model's CORRECTED+FAILED share > 25% of its last
                    10 lines -> the escalation rule (SUBAGENTS rule 6)
  compact_runs.txt  >= N compactions in the last 7 days -> checkpoint
                    earlier
  delete_grants.txt / retired_files.txt  informational counts
When the set of proposals differs from the last run's, one line goes to
docs/history/proposal_runs.txt so the loop has its own history.

Search keys: learning loop, proposals, ledger trends, thresholds, rule
change proposal, standup proposals, escalation, cold shelf sweep.
See also: tools/standup.py (prints this block); docs/systems/tooling.md
(the learning loop); SUBAGENTS.md rule 6 (escalation); tools/wiki_heat.py;
tools/check_wiki_links.py; tools/usage_report.py.
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "docs", "history")
RUNS = os.path.join(HIST, "proposal_runs.txt")
THRESHOLDS = {
    "usage_check_days": 3,      # CHECK verdicts among the last 7 daily lines
    "usage_big_reads": 8,       # avg "big" whole-file reads over the last 7 lines
    "test_fails": 2,            # FAIL lines among the last 10 test runs
    "cold_sections": 10,        # cold sections reported by wiki_heat
    "employee_correction_pct": 25,  # SUBAGENTS rule 6
    "compactions_7d": 2,        # compactions inside the last 7 days
}


def data_lines(name):
    path = os.path.join(HIST, name)
    try:
        with open(path, encoding="utf-8") as fh:
            return [ln.rstrip() for ln in fh if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def proposals(th=THRESHOLDS):
    out = []
    # 1. usage_daily.txt
    lines = data_lines("usage_daily.txt")[-7:]
    checks = [ln for ln in lines if "| CHECK" in ln]
    if len(checks) >= th["usage_check_days"]:
        out.append("PROPOSE (usage_daily.txt): %d of the last %d days carry a CHECK "
                   "verdict - the read diet is slipping. Options: lower the diet "
                   "guard's BIG_READ_TOK, add a distill step for the files being "
                   "read whole, or batch CLAUDE.md/MEMORY edits at checkpoint "
                   "(cache misses)." % (len(checks), len(lines)))
    bigs = []
    for ln in lines:
        m = re.search(r"\|\s*\d+ \((\d+)\) / \d+,", ln)
        if m:
            bigs.append(int(m.group(1)))
    if bigs and sum(bigs) / len(bigs) >= th["usage_big_reads"]:
        out.append("PROPOSE (usage_daily.txt): big whole-file reads average %.1f/day "
                   "over the last %d days - which files? `python tools/wiki_heat.py` "
                   "shows the whole-read column; section them or split them."
                   % (sum(bigs) / len(bigs), len(bigs)))
    # 2. test_runs.txt
    tests = data_lines("test_runs.txt")[-10:]
    fails = [ln for ln in tests if "FAIL" in ln]
    if len(fails) >= th["test_fails"]:
        groups = sorted({ln.split("|")[3].strip() for ln in fails if ln.count("|") >= 3})
        out.append("PROPOSE (test_runs.txt): %d FAIL lines in the last %d runs (%s) - "
                   "a flaky or broken group; fix or quarantine before the next ship."
                   % (len(fails), len(tests), ", ".join(groups) or "?"))
    # 3. wiki_link_runs.txt
    links = data_lines("wiki_link_runs.txt")
    if links:
        m = re.search(r"dead (\d+)", links[-1])
        if m and int(m.group(1)) > 0:
            out.append("PROPOSE (wiki_link_runs.txt): %s dead wiki link(s) - fix them "
                       "(the list: docs/history/wiki_links.txt)." % m.group(1))
    # 4. wiki_heat_runs.txt
    heat = data_lines("wiki_heat_runs.txt")
    if heat:
        m = re.search(r"cold (\d+) \((\d+) lines\)", heat[-1])
        if m and int(m.group(1)) >= th["cold_sections"]:
            out.append("PROPOSE (wiki_heat_runs.txt): %s cold sections (%s lines never "
                       "or long-unread) - a cold-shelf sweep would thin the hot wiki. "
                       "Candidates: docs/history/wiki_heat.txt; the owner picks, "
                       "`python tools/cold_shelf.py --move` moves (never deletes)."
                       % (m.group(1), m.group(2)))
    # 5. SUBAGENTS.md ledger (rule 6)
    try:
        with open(os.path.join(ROOT, "SUBAGENTS.md"), encoding="utf-8") as fh:
            body = fh.read()
        led = body.split("## THE LEDGER", 1)[1] if "## THE LEDGER" in body else ""
        per = {}
        for ln in led.splitlines():
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) < 5 or not re.match(r"\d{4}-\d\d-\d\d", parts[0]):
                continue
            model = parts[2].split("/")[0].strip().lower()
            outcome = parts[4].split("-")[0].strip().upper()
            per.setdefault(model, []).append(outcome)
        for model, outs in sorted(per.items()):
            last = outs[-10:]
            bad = sum(1 for o in last if o.startswith(("CORRECTED", "FAILED")))
            pct = 100.0 * bad / len(last) if last else 0
            if len(last) >= 4 and pct > th["employee_correction_pct"]:
                out.append("PROPOSE (SUBAGENTS.md ledger): %s corrected/failed on %d of its "
                           "last %d tasks (%.0f%%) - rule 6 says bump the model a tier or "
                           "raise the effort in THE ASSIGNMENTS (dated, attributed)."
                           % (model, bad, len(last), pct))
    except OSError:
        pass
    # 6. compact_runs.txt
    week = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    comps = [ln for ln in data_lines("compact_runs.txt") if ln[:10] >= week
             and "pipe-test" not in ln]
    if len(comps) >= th["compactions_7d"]:
        out.append("PROPOSE (compact_runs.txt): %d compactions in the last 7 days - "
                   "sessions run past the gauge; checkpoint at the first ADVISED line."
                   % len(comps))
    return out


def info_lines():
    out = []
    n = len(data_lines("delete_grants.txt"))
    if n:
        out.append("grants: %d double-acknowledged deletion(s) on record (delete_grants.txt)" % n)
    n = len(data_lines("retired_files.txt"))
    if n:
        out.append("retired: %d file(s) on the shelf (_retired/, retired_files.txt)" % n)
    return out


def record(props):
    """One ledger line when the proposal set changed since the last line."""
    key = " || ".join(p.split(":", 1)[0] + ":" + p.split(":", 1)[1][:60] for p in props)
    last = data_lines("proposal_runs.txt")
    if last and last[-1].split(" | ", 3)[-1] == (key or "none"):
        return
    new = not os.path.isfile(RUNS)
    with open(RUNS, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# PROPOSAL HISTORY (append-only; one line whenever the ledger trends "
                     "change what is proposed). Read the TAIL.\n"
                     "# date time | ws | count | proposals (truncated)\n")
        fh.write("%s | %s | %d | %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                          workstation(), len(props), key or "none"))


def main(argv):
    if "--limits" in argv:
        for k, v in THRESHOLDS.items():
            print("  %-26s %s" % (k, v))
        return 0
    props = proposals()
    print("== PROPOSALS (ledger trends vs thresholds; `python tools/ledger_trends.py "
          "--limits`; NOTHING is applied - the owner decides)")
    if props:
        for p in props:
            print("  " + p)
    else:
        print("  none - every ledger trend is inside its threshold")
    for ln in info_lines():
        print("  " + ln)
    if "--no-record" not in argv:
        record(props)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""THE SYSTEMS AUDIT LEDGER (the CEO's ask 2026-09-13: "Do we have anything
in our loops that audits our ledgers, new features, etc. and considers new
options to increase efficiency (without losing context), decrease token
usage (without losing efficiency or context), add txt data structures for
increased knowledge, etc?" - we did not; the loop measured, it never
thought).

    python tools/systems_audit.py                    # status: last audit, what moved since
    python tools/systems_audit.py --record "<summary>"   # ledger a finished audit

The audit itself is a handful of READ-ONLY employees (four lanes: TOKENS -
the usage sheet, big reads, the diet; PROCESS - the workflows, skills,
hooks and what was done by hand in the day files; KNOWLEDGE - the wiki,
the ledgers, what a new txt structure would capture; FEATURES - what
shipped since the last audit and whether any of it should have been a
script, a hook, a data file or a cheaper model). Each returns PROPOSALS
only - the owner decides, nothing is applied (WORKFLOWS.md "Audit the
operating system"). When one finishes, `--record` appends one line to
docs/history/systems_audit_runs.txt (date, ws, day files and commits since
the previous audit, summary). tools/ledger_trends.py proposes the next
audit when the day-file count or the age since the last line crosses the
owner's thresholds (systems_audit_day_files / systems_audit_days).

PURPOSE: Keeps the systems audit ledger: prints status (last audit, days
  since, day files and commits since) and on --record appends one line to
  docs/history/systems_audit_runs.txt recording a finished four lane audit
  (tokens, process, knowledge, features) of the operating system.
INTENT: the CEO's ask 2026-09-13: 'Do we have anything in our loops that
  audits our ledgers, new features, etc. and considers new options to
  increase efficiency (without losing context), decrease token usage
  (without losing efficiency or context), add txt data structures for
  increased knowledge, etc?'

Search keys: systems audit, efficiency audit, token audit, process audit,
knowledge audit, feature audit, audit cadence, auditor.
See also: tools/readme_audit.py (the same shape for the public README);
tools/ledger_trends.py (rule 10); TOKEN_IDEAS.md (where a token proposal
lands); WORKFLOWS.md "Audit the operating system"; docs/systems/tooling.md
"The intent loop".
"""
import datetime
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "history", "systems_audit_runs.txt")
DAYS = os.path.join(ROOT, "docs", "history", "days")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def last_line():
    try:
        lines = [ln.rstrip() for ln in open(LEDGER, encoding="utf-8")
                 if ln.strip() and not ln.startswith("#")]
    except OSError:
        return None
    return lines[-1] if lines else None


def commits_since(date_str):
    try:
        r = subprocess.run(["git", "rev-list", "--count", "--since=" + date_str, "HEAD"],
                           cwd=ROOT, capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip() or 0)
    except Exception:  # noqa: BLE001
        return -1


def day_files_since(date_str):
    day = date_str[:10]
    return len([p for p in glob.glob(os.path.join(DAYS, "*.md"))
                if os.path.basename(p)[:10] > day])


def status():
    """(last_stamp or None, days_since, day_files_since, commits_since)"""
    ln = last_line()
    if not ln:
        return None, None, day_files_since("2000-01-01"), commits_since("2000-01-01")
    stamp = ln.split(" | ", 1)[0]
    try:
        then = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M")
        days = (datetime.datetime.now() - then).days
    except ValueError:
        days = None
    return stamp, days, day_files_since(stamp), commits_since(stamp)


def record(summary):
    stamp, days, dfs, commits = status()
    new = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# SYSTEMS AUDIT HISTORY (append-only; one line per finished four-lane "
                     "audit of the operating system: tokens, process, knowledge, features). "
                     "Read the TAIL.\n"
                     "# date time | ws | day files since previous | commits since previous | "
                     "summary\n")
        fh.write("%s | %s | %d | %s | %s\n" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), workstation(), dfs,
            commits if commits >= 0 else "?", summary.strip().replace("\n", " ")))
    print("recorded: systems audit, %d day file(s) and %s commit(s) since the previous one"
          % (dfs, commits))


def main(argv):
    if "--record" in argv:
        i = argv.index("--record")
        summary = argv[i + 1] if i + 1 < len(argv) else ""
        if not summary:
            sys.exit("--record needs a summary in quotes")
        record(summary)
        return 0
    stamp, days, dfs, commits = status()
    if not stamp:
        print("SYSTEMS AUDIT: none on record - %d day files and %d commits ever; run the "
              "four-lane audit and `--record` it" % (dfs, commits))
    else:
        print("SYSTEMS AUDIT: last %s (%s days ago); %d day file(s) and %d commit(s) since"
              % (stamp, days, dfs, commits))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

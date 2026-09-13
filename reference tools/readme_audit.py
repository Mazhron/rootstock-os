"""THE README AUDIT LEDGER (Mazhron 2026-09-13, the third layer of "prevent
the README falling behind": the lint catches drift in facts a script can
derive; only an AUDIT catches an answer we know that the README never
says).

    python tools/readme_audit.py                 # status: last audit, what moved since
    python tools/readme_audit.py --record "<summary>"   # ledger a finished audit

An audit is the manager's four-employee cross-reference (read-only
employees compare the public README against every method file, the
skills, the hooks and the front door; the manager applies the findings).
When one finishes, `--record` appends one line to
docs/history/readme_audit_runs.txt with the date, workstation, kit
version, and how many kit-folder commits landed since the previous
audit. tools/ledger_trends.py reads the tail and PROPOSES a fresh audit
at standup when the kit has moved past a threshold of commits or days
since the last line (readme_audit_kit_commits / readme_audit_days in its
THRESHOLDS - the owner's numbers). Nothing runs an audit by itself.

Search keys: readme audit, audit cadence, readme review, kit audit,
cross-reference audit, unwritten answers.
See also: tools/readme_lint.py (the mechanical layer); tools/ledger_trends.py
(the proposal); WORKFLOWS.md "Audit the public README (Rootstock)";
docs/systems/tooling.md "The README parity lint and audit cadence".
"""
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT_DIR = "Future Project MDs"
UPGRADES = os.path.join(ROOT, KIT_DIR, "UPGRADES.md")
LEDGER = os.path.join(ROOT, "docs", "history", "readme_audit_runs.txt")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def kit_version():
    try:
        m = re.search(r"CURRENT KIT VERSION:\s*\**v(\d+\.\d+)",
                      open(UPGRADES, encoding="utf-8").read())
        return m.group(1) if m else "?"
    except OSError:
        return "?"


def last_line():
    try:
        lines = [ln.rstrip() for ln in open(LEDGER, encoding="utf-8")
                 if ln.strip() and not ln.startswith("#")]
    except OSError:
        return None
    return lines[-1] if lines else None


def kit_commits_since(date_str):
    """Commits touching the kit folder since a 'YYYY-MM-DD HH:MM' stamp."""
    try:
        r = subprocess.run(["git", "rev-list", "--count", "--since=" + date_str, "HEAD",
                            "--", KIT_DIR], cwd=ROOT, capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip() or 0)
    except Exception:  # noqa: BLE001 - a status helper never crashes standup
        return -1


def status():
    """Return (last_date, days_since, commits_since) - None date if no audit yet."""
    ln = last_line()
    if not ln:
        return None, None, kit_commits_since("2000-01-01")
    stamp = ln.split(" | ", 1)[0]
    try:
        then = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M")
        days = (datetime.datetime.now() - then).days
    except ValueError:
        days = None
    return stamp, days, kit_commits_since(stamp)


def record(summary):
    stamp, days, commits = status()
    new = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# README AUDIT HISTORY (append-only; one line per finished four-employee "
                     "cross-reference of the public README). Read the TAIL.\n"
                     "# date time | ws | kit version | kit commits since previous audit | summary\n")
        fh.write("%s | %s | v%s | %s | %s\n" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), workstation(), kit_version(),
            commits if commits >= 0 else "?", summary.strip().replace("\n", " ")))
    print("recorded: audit at kit v%s, %s kit commits since the previous one"
          % (kit_version(), commits))


def main(argv):
    if "--record" in argv:
        i = argv.index("--record")
        summary = argv[i + 1] if i + 1 < len(argv) else ""
        if not summary:
            sys.exit("--record needs a summary in quotes")
        record(summary)
        return 0
    stamp, days, commits = status()
    if not stamp:
        print("README AUDIT: none on record - %d kit commits ever; run the four-employee "
              "audit and `--record` it" % commits)
    else:
        print("README AUDIT: last %s (%s days ago) at kit v%s; %d kit-folder commit(s) since"
              % (stamp, days, (last_line().split(" | ")[2]).lstrip("v"), commits))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

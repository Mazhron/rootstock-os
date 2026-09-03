"""THE STANDUP DIGEST (TOKEN_IDEAS idea 7, APPROVED by Mazhron 2026-09-02:
"this goes along with my rules of creating a script for everything").

Replaces the manager reading every handoff note and changelog wholesale after
a pull: prints a ~20-line digest - recent commits, the newest WS-note
headlines, the tail of every history ledger, and the open roadmap index. The
manager reads THIS, then opens full notes only where the digest points.

Usage:  python tools/standup.py [--commits N]   (default 12)

Search keys: standup, pull digest, session start, catch-up. See also:
TOKEN_IDEAS.md idea 7; docs/history/ ledgers; NEXT_STEPS.md.
"""
import argparse
import glob
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          timeout=60).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description="Post-pull standup digest")
    ap.add_argument("--commits", type=int, default=12)
    args = ap.parse_args()

    # WHERE WE LEFT OFF comes FIRST (Mazhron's ask 2026-09-02: after /clear
    # THEY have nothing - the manager must hand back the last prompt AND the
    # manager's last response, BOTH sides and VERBATIM (Mazhron 2026-09-03,
    # tightened same day: exact words, never condensed/paraphrased - the
    # checkpoint writes them into the day file word for word) plus the
    # state summary before anything else. Pulled from the newest day file's
    # "## WHERE WE LEFT OFF" section, refreshed at every checkpoint.
    days = sorted(glob.glob(os.path.join(ROOT, "docs", "history", "days", "*.md")))
    if days:
        import datetime
        newest = os.path.basename(days[-1])
        file_date = newest[:10]
        today = datetime.date.today().isoformat()
        if file_date == today:
            print("== SAME DAY - continuing %s" % newest)
        else:
            try:
                gap = (datetime.date.fromisoformat(today)
                       - datetime.date.fromisoformat(file_date)).days
                ago = "%d day(s) ago" % gap
            except ValueError:
                ago = "?"
            print("== NEW DAY (last log %s, %s) - PREVIOUS day's close below;"
                  % (file_date, ago))
            print("   manager: create today's day file at the first checkpoint.")
        body = open(days[-1], encoding="utf-8").read()
        wm = re.search(r"## WHERE WE LEFT OFF.*?(?=\n## |\Z)", body, flags=re.S)
        print("== WHERE WE LEFT OFF (%s)" % newest)
        if wm:
            for ln in wm.group(0).splitlines()[1:]:
                print("  " + ln)
        else:
            print("  (no WHERE WE LEFT OFF section yet - see the file's "
                  "COMPLETED list)")

    print("== VERSION + RECENT COMMITS")
    with open(os.path.join(ROOT, "project.godot"), encoding="utf-8") as fh:
        m = re.search(r'config/version="([^"]+)"', fh.read())
    print("  version: %s" % (m.group(1) if m else "?"))
    for ln in sh(["git", "log", "--oneline", "-%d" % args.commits]).splitlines():
        print("  " + ln)

    print("== NEWEST WS NOTES (headlines only - open CLAUDE.md for a body)")
    with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as fh:
        heads = re.findall(r"^- \*\*(→ WS[^:]{0,110})", fh.read(), flags=re.M)
    for h in heads[:6]:
        print("  " + h.strip())

    print("== LEDGER TAILS (docs/history/)")
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "history", "*.txt"))):
        with open(path, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        if lines:
            print("  %s:" % os.path.basename(path))
            for ln in lines[-2:]:
                print("    " + ln)

    print("== OPEN ROADMAP (NEXT_STEPS index)")
    with open(os.path.join(ROOT, "NEXT_STEPS.md"), encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("- [NS-"):
                print("  " + ln.strip())

    days_index = os.path.join(ROOT, "docs", "history", "days_index.txt")
    if os.path.isfile(days_index):
        print("== RECENT DAYS (docs/history/days/)")
        with open(days_index, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        for ln in lines[-3:]:
            print("  " + ln)


if __name__ == "__main__":
    main()

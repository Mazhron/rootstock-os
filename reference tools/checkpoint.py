"""THE CHECKPOINT COUNTER (Mazhron approved 2026-09-02: warn at 8 tasks,
DIRE at 15 with the offer to compress or clear).

HONESTY NOTE on the "looping script": no background process can watch the
conversation - the loop is the MANAGER'S law, enforced by this script: the
manager runs `--tick` after every completed task; the script keeps the count
in a state file and prints the escalating warnings, identically on both
workstations. `--reset` is run ONLY as part of a full checkpoint (work
pushed, day file's WHERE-WE-LEFT-OFF refreshed, tree clean).

Usage:
  python tools/checkpoint.py --tick     # +1 task; prints status/warnings
  python tools/checkpoint.py --status   # just look
  python tools/checkpoint.py --reset    # checkpoint done - count to zero

Thresholds: >=8 CHECKPOINT ADVISED; >=15 CHECKPOINT URGENT (dire).

Search keys: checkpoint counter, task count, clear warning, context budget.
See also: TOKEN_IDEAS.md 9b (the protocol); tools/standup.py (resumption);
docs/history/days/ (the day files that make /clear lossless).
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "docs", "history", "checkpoint_state.txt")


def which_ws():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def load():
    counts = {}
    if os.path.isfile(STATE):
        for ln in open(STATE, encoding="utf-8"):
            m = re.match(r"(WS\S*) \| (\d+) \| (.+)", ln.strip())
            if m:
                counts[m.group(1)] = (int(m.group(2)), m.group(3))
    return counts


def save(counts):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as fh:
        fh.write("# CHECKPOINT STATE (per WS: tasks since last checkpoint).\n")
        for ws, (n, when) in sorted(counts.items()):
            fh.write("%s | %d | %s\n" % (ws, n, when))


def report(n):
    if n >= 15:
        print("!!!!! CHECKPOINT URGENT (%d tasks since last checkpoint) !!!!!" % n)
        print("The session is heavy. Mazhron: I recommend /compact or /clear NOW.")
        print("Manager: push, refresh the day file's WHERE WE LEFT OFF, run --reset,")
        print("and emit the checkpoint marker BEFORE taking new work.")
    elif n >= 8:
        print("~~ CHECKPOINT ADVISED (%d tasks since last checkpoint) ~~" % n)
        print("Finish the current arc, then checkpoint (push + day file + marker).")
    else:
        print("checkpoint counter: %d task(s) since last checkpoint (warns at 8, dire at 15)" % n)


def main():
    ap = argparse.ArgumentParser(description="Checkpoint task counter")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tick", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    ws = which_ws()
    counts = load()
    n = counts.get(ws, (0, ""))[0]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if args.tick:
        n += 1
        counts[ws] = (n, now)
        save(counts)
    elif args.reset:
        n = 0
        counts[ws] = (0, now + " (checkpoint)")
        save(counts)
        print("checkpoint counter reset - marker may be emitted.")
        return
    report(n)
    sys.exit(0)


if __name__ == "__main__":
    main()

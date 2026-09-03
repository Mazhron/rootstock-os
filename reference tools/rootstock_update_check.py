"""ROOTSTOCK UPDATE CHECK (kit v1.3): is a newer kit available, and what
would it graft onto this project?

Reads the project's install stamp from CLAUDE.md
("Rootstock vX.Y installed <date> | updates: <policy>"), gets the kit's
current UPGRADES.md (a local clone if configured, else the public repo
over HTTPS), compares versions, and prints any graft entries newer than
the install - plus what the CEO's update POLICY says to do about them.
The script only REPORTS; the manager Claude performs grafts per the kit's
UPGRADES.md protocol (concepts onto the project's own files, never file
copies).

POLICIES (the CEO sets the word in the stamp line, changeable any time):
  ask       - default: present newer grafts, CEO picks all/some/none
  auto      - manager grafts everything newer in the next batch, reports
  relevant  - manager presents ONLY grafts that benefit THIS project,
              and records the skipped ones so they are never re-offered
  never     - no standup checks; only when the CEO explicitly asks

Checks are rate-limited to once a week (--force bypasses) and every check
appends one line to its ledger, so standup can carry the result for free.

Usage:  python tools/rootstock_update_check.py [--force] [--stamp vX.Y]
        (--stamp overrides the CLAUDE.md stamp, for testing)

ADAPT ON INSTALL: set KIT_CLONE if the CEO keeps a local clone, point
STAMP_FILE at your core file if it is not ./CLAUDE.md, and wire this into
your standup script or runner so the check rides an existing habit.

Search keys: rootstock update, kit version check, graft check, upgrade.
See also: UPGRADES.md (the graft log + protocol, in the kit repo).
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP_FILE = os.path.join(ROOT, "CLAUDE.md")
LEDGER = os.path.join(ROOT, "docs", "history", "rootstock_updates.txt")
KIT_CLONE = ""  # optional local clone of rootstock-os; "" = fetch over HTTPS
KIT_RAW = ("https://raw.githubusercontent.com/Mazhron/rootstock-os/"
           "main/UPGRADES.md")
CHECK_EVERY_DAYS = 7


def read_stamp():
    """-> (version tuple, policy) from the CLAUDE.md install stamp."""
    try:
        text = open(STAMP_FILE, encoding="utf-8").read()
    except OSError:
        return None, "ask"
    m = re.search(r"Rootstock v(\d+)\.(\d+) installed[^\n|]*"
                  r"(?:\|\s*updates:\s*(\w+))?", text)
    if not m:
        return None, "ask"
    return (int(m.group(1)), int(m.group(2))), (m.group(3) or "ask").lower()


def fetch_upgrades():
    """-> UPGRADES.md text from the local clone (pulled) or the public repo."""
    if KIT_CLONE and os.path.isdir(KIT_CLONE):
        subprocess.run(["git", "-C", KIT_CLONE, "pull", "--quiet"],
                       capture_output=True, timeout=60)
        return open(os.path.join(KIT_CLONE, "UPGRADES.md"),
                    encoding="utf-8").read()
    with urllib.request.urlopen(KIT_RAW, timeout=10) as r:
        return r.read().decode("utf-8", "replace")


def parse_entries(text):
    """-> (kit version tuple, [(version, title, what-lines)])."""
    vm = re.search(r"CURRENT KIT VERSION:\s*\**v(\d+)\.(\d+)", text)
    kit_v = (int(vm.group(1)), int(vm.group(2))) if vm else None
    entries = []
    for m in re.finditer(
            r"^### v(\d+)\.(\d+) - \S+ - (.+?)$\n(.*?)(?=^###? |\Z)",
            text, re.M | re.S):
        what = m.group(4).split("CARRIES:")[0].strip()
        entries.append(((int(m.group(1)), int(m.group(2))),
                        m.group(3).strip(), what))
    return kit_v, entries


def days_since_last_check():
    try:
        last = open(LEDGER, encoding="utf-8").read().strip().splitlines()[-1]
        then = datetime.date.fromisoformat(last[:10])
        return (datetime.date.today() - then).days
    except (OSError, ValueError, IndexError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="check even if rate-limited or policy is never")
    ap.add_argument("--stamp", help="override installed version, e.g. v1.1")
    args = ap.parse_args()

    local_v, policy = read_stamp()
    if args.stamp:
        m = re.match(r"v?(\d+)\.(\d+)$", args.stamp)
        local_v = (int(m.group(1)), int(m.group(2))) if m else local_v
    if local_v is None:
        print("ROOTSTOCK CHECK: no install stamp in %s - add "
              "'Rootstock vX.Y installed <date> | updates: ask' first."
              % os.path.relpath(STAMP_FILE, ROOT))
        return
    if policy == "never" and not args.force:
        print("ROOTSTOCK CHECK: policy is 'never' - checking only on the "
              "CEO's explicit ask (--force).")
        return
    ago = days_since_last_check()
    if ago is not None and ago < CHECK_EVERY_DAYS and not args.force:
        print("ROOTSTOCK CHECK: last checked %dd ago (limit %dd) - --force "
              "to re-check." % (ago, CHECK_EVERY_DAYS))
        return

    try:
        text = fetch_upgrades()
    except Exception as e:  # offline is normal; never fail a standup for it
        print("ROOTSTOCK CHECK: skipped (kit unreachable: %s)" % e)
        return
    kit_v, entries = parse_entries(text)
    if not kit_v:
        print("ROOTSTOCK CHECK: could not parse kit version - kit format "
              "changed? Read UPGRADES.md by hand.")
        return
    newer = [e for e in entries if e[0] > local_v]

    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    fresh = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write("# ROOTSTOCK UPDATE CHECKS (append-only; one line per "
                     "check).\n# date | installed | kit | verdict\n")
        fh.write("%s | v%d.%d | v%d.%d | %s\n" % (
            datetime.date.today().isoformat(), local_v[0], local_v[1],
            kit_v[0], kit_v[1],
            "current" if not newer else "%d graft(s) newer" % len(newer)))

    if not newer:
        print("ROOTSTOCK CHECK: v%d.%d installed = kit current. Nothing to "
              "graft." % local_v)
        return
    print("ROOTSTOCK CHECK: kit v%d.%d > installed v%d.%d - %d graft(s) "
          "available:" % (kit_v + local_v + (len(newer),)))
    for v, title, what in newer:
        print("\n  v%d.%d - %s" % (v[0], v[1], title))
        for line in what.splitlines():
            print("    " + line)
    print("\nPOLICY=%s -> %s" % (policy, {
        "ask": "present these to the CEO; graft the chosen ones per the "
               "kit's UPGRADES.md protocol, then bump the stamp.",
        "auto": "graft ALL of the above in the next batch per the kit's "
                "UPGRADES.md protocol, bump the stamp, report what changed.",
        "relevant": "present ONLY the grafts that benefit this project; "
                    "note the skipped versions in the ledger line so they "
                    "are never re-offered; bump the stamp either way.",
    }.get(policy, "unknown policy '%s' - treat as ask." % policy)))


if __name__ == "__main__":
    main()

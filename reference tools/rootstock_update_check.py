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

Checks are rate-limited to once every two days (--force bypasses; weekly until kit v1.48) and every check
appends one line to its ledger, so standup can carry the result for free.

Usage:  python tools/rootstock_update_check.py [--force] [--stamp vX.Y]
        (--stamp overrides the CLAUDE.md stamp, for testing)

ADAPT ON INSTALL: set KIT_CLONE if the CEO keeps a local clone, point
STAMP_FILE at your core file if it is not ./CLAUDE.md, and wire this into
your standup script or runner so the check rides an existing habit.

PURPOSE: Reads the project's install stamp from CLAUDE.md, fetches the kit's
  current UPGRADES.md (a local clone if configured, else the public repo
  over HTTPS), and prints any graft entries newer than the install plus what
  the CEO's update policy says to do about them; it only reports, a manager
  Claude performs the actual grafts by hand. It pins to the kit's release tag
  (vX.Y) and verifies UPGRADES.md against the tag's SHA256SUMS before it
  reports; a mismatch stops the report, a missing tag is flagged unverified
  and still lists main's grafts. The checksum proves the files match the
  release, not who signed it: the tag's signature is checked by hand (git tag
  -v, or the Verified badge in the repo's tags view). With KIT_CLONE set it
  runs git pull on that clone first (a second network reach) and verifies
  against the clone's own SHA256SUMS, unpinned.
INTENT: so a project can learn when the kit has grown new concepts worth
  grafting; checks are rate limited to once every two days (the CEO 2026-10-13:
  once per day or two, not weekly) so the check is cheap enough to ride the
  standup habit. The CEO 2026-10-13: "Anything pushed would need to come with
  whatever is needed to authenticate that the code is not malicious, we must
  ensure that no user could pull code and be forced to run it."

Search keys: rootstock update, kit version check, graft check, upgrade,
  signed tag, checksum, SHA256SUMS, verified release, pin to tag.
See also: UPGRADES.md (the graft log + protocol, in the kit repo).
"""
import argparse
import datetime
import hashlib
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP_FILE = os.path.join(ROOT, "CLAUDE.md")
LEDGER = os.path.join(ROOT, "docs", "history", "rootstock_updates.txt")
KIT_CLONE = ""  # optional local clone of rootstock-os; "" = fetch over HTTPS
KIT_RAW = "https://raw.githubusercontent.com/Mazhron/rootstock-os/{ref}/{path}"
CHECK_EVERY_DAYS = 2   # kit v1.48 (the CEO 2026-10-13: once per day or two, not weekly)
FIRST_TAGGED = "v1.51"  # the kit's first signed-tag release


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


def raw_url(ref, path):
    """-> the raw file URL at a branch or tag ref."""
    return KIT_RAW.format(ref=ref, path=path)


def fetch_text(ref, path):
    """-> file text at ref. The ONLY function that touches the network."""
    with urllib.request.urlopen(raw_url(ref, path), timeout=10) as r:
        return r.read().decode("utf-8", "replace")


def use_clone():
    return bool(KIT_CLONE) and os.path.isdir(KIT_CLONE)


def fetch_upgrades():
    """-> UPGRADES.md text from the local clone (pulled) or the public repo."""
    if use_clone():
        subprocess.run(["git", "-C", KIT_CLONE, "pull", "--quiet"],
                       capture_output=True, timeout=60)
        return open(os.path.join(KIT_CLONE, "UPGRADES.md"),
                    encoding="utf-8").read()
    return fetch_text("main", "UPGRADES.md")


def parse_sums(text):
    """-> {path: hex} from sha256sum-shaped lines ('<hex>  <path>')."""
    sums = {}
    for line in text.splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m:
            sums[m.group(2)] = m.group(1).lower()
    return sums


def verify_text(text_bytes, sums, name):
    """-> True when sha256(text_bytes) equals the sums entry for name."""
    want = sums.get(name)
    return bool(want) and hashlib.sha256(text_bytes).hexdigest() == want


def selftest():
    sample = ("%s  UPGRADES.md\n%s  README.md\n%s  skills/ship/SKILL.md\n"
              % ("a" * 64, "b" * 64, "c" * 64))
    sums = parse_sums(sample)
    body = b"CURRENT KIT VERSION: **v1.2**\n"
    good = {"UPGRADES.md": hashlib.sha256(body).hexdigest()}
    upg = ("CURRENT KIT VERSION: **v1.2**\n\n### v1.2 - 2026-01-02 - Two\nwhat two\n"
           "CARRIES: x\n\n### v1.1 - 2026-01-01 - One\nwhat one\n")
    kv, ents = parse_entries(upg)
    checks = [
        ("parse_sums count", len(sums) == 3),
        ("parse_sums path", sums.get("skills/ship/SKILL.md") == "c" * 64),
        ("verify match", verify_text(body, good, "UPGRADES.md")),
        ("verify changed byte", not verify_text(body + b"x", good, "UPGRADES.md")),
        ("verify missing name", not verify_text(body, {}, "UPGRADES.md")),
        ("raw_url", raw_url("v1.51", "SHA256SUMS") ==
         "https://raw.githubusercontent.com/Mazhron/rootstock-os/v1.51/SHA256SUMS"),
        ("parse_entries version", kv == (1, 2)),
        ("parse_entries count", len(ents) == 2 and ents[0][0] == (1, 2)),
    ]
    bad = [n for n, ok in checks if not ok]
    print("FAIL: " + ", ".join(bad) if bad else "PASS")
    sys.exit(1 if bad else 0)


def verify_release(kit_v, text):
    """-> (state, text to read, header note). state: verified | mismatch | unverified."""
    if use_clone():
        try:
            sums = parse_sums(open(os.path.join(KIT_CLONE, "SHA256SUMS"),
                                   encoding="utf-8").read())
            raw = open(os.path.join(KIT_CLONE, "UPGRADES.md"), "rb").read()
        except OSError:
            return "unverified", text, "UNVERIFIED local clone (no SHA256SUMS)"
        if verify_text(raw, sums, "UPGRADES.md"):
            return "verified", text, "VERIFIED local clone"
        return "mismatch", text, "UNVERIFIED local clone: checksum mismatch"
    tag = "v%d.%d" % kit_v
    try:
        sums_text = fetch_text(tag, "SHA256SUMS")
        pinned = fetch_text(tag, "UPGRADES.md")
    except Exception:
        return ("unverified", text, "UNVERIFIED (no tag or checksums at %s; "
                "the kit's first tagged release is %s)" % (tag, FIRST_TAGGED))
    if verify_text(pinned.encode("utf-8"), parse_sums(sums_text), "UPGRADES.md"):
        return "verified", pinned, "VERIFIED %s (checksum matches)" % tag
    return ("mismatch", text, "UNVERIFIED %s: checksum mismatch; do not graft "
            "from this release, tell the kit's owner" % tag)


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
    ap.add_argument("--selftest", action="store_true",
                    help="offline checks of the pure helpers")
    args = ap.parse_args()
    if args.selftest:
        selftest()

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
    # PIN + VERIFY (kit v1.51): read the tag's UPGRADES.md only if its hash
    # matches the tag's SHA256SUMS; a mismatch stops before any graft list.
    state, text, note = verify_release(kit_v, text)
    if state == "verified":
        kit_v, entries = parse_entries(text)
        kit_v = kit_v or (0, 0)
    newer = [e for e in entries if e[0] > local_v] if state != "mismatch" else []
    verdict = ("current" if not newer else "%d graft(s) newer" % len(newer))
    if state == "mismatch":
        verdict = "unverified"
    elif state == "unverified":
        verdict += " (unverified)"

    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    fresh = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write("# ROOTSTOCK UPDATE CHECKS (append-only; one line per "
                     "check).\n# date | installed | kit | verdict\n")
        fh.write("%s | v%d.%d | v%d.%d | %s\n" % (
            datetime.date.today().isoformat(), local_v[0], local_v[1],
            kit_v[0], kit_v[1], verdict))

    if state == "mismatch":
        print("ROOTSTOCK CHECK: " + note)
        return
    if not newer:
        print("ROOTSTOCK CHECK: v%d.%d installed = kit current. Nothing to "
              "graft. [%s]" % (local_v + (note,)))
        return
    print("ROOTSTOCK CHECK: kit v%d.%d > installed v%d.%d - %d graft(s) "
          "available: [%s]" % (kit_v + local_v + (len(newer), note)))
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

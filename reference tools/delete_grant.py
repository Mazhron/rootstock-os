"""Record the owner's double-acknowledged permission for ONE deletion.

THE PRESERVATION LAW (Mazhron's ruling 2026-09-10): nothing is deleted
without the owner's express permission, given twice. The ritual:
  1. The manager asks, naming the exact target: "This will delete X
     (n files, y KB). Do you approve?"
  2. The owner says yes (ack1).
  3. The manager restates the target and asks again: "To confirm: delete
     X, and nothing else?"
  4. The owner says yes again (ack2).
  5. The manager runs THIS script with all four texts VERBATIM. It writes
     .claude/delete_grant.json (gitignored, expires in --minutes, default
     15, single use) and appends the committed ledger
     docs/history/delete_grants.txt. Then the one deleting command runs;
     tools/hooks/preserve_guard.py lets exactly one command that names
     the target through and marks the grant used.
Nothing here deletes anything; `--status` shows the live grant. A target
in the never-list (a drive root, the home folder, the repo root or its
.git) is refused here too - no grant covers those.

Search keys: delete grant, permission, double acknowledgment, preservation
law, approved deletion, delete ledger.
See also: tools/hooks/preserve_guard.py (the guard that honors it);
tools/retire.py (the move that usually replaces a delete); WORKFLOWS.md
"Delete something (the grant ritual)"; docs/history/delete_grants.txt.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRANT = os.path.join(ROOT, ".claude", "delete_grant.json")
LEDGER = os.path.join(ROOT, "docs", "history", "delete_grants.txt")
HEADER = ("# DELETE GRANTS (append-only; one line per double-acknowledged deletion).\n"
          "# THE PRESERVATION LAW: nothing is deleted without the owner's permission given twice.\n"
          "# date time | ws | target | minutes | manager's ask | ack1 | ack2\n")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def main():
    ap = argparse.ArgumentParser(description="Record a double-acknowledged deletion grant")
    ap.add_argument("--target", help="the exact path (or unmistakable substring) to be deleted")
    ap.add_argument("--ask", help="the manager's question, verbatim")
    ap.add_argument("--ack1", help="the owner's first acknowledgment, verbatim")
    ap.add_argument("--ack2", help="the owner's second acknowledgment, verbatim")
    ap.add_argument("--minutes", type=int, default=15)
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    if a.status:
        try:
            g = json.load(open(GRANT, encoding="utf-8"))
        except (OSError, ValueError):
            print("no grant on file")
            return 0
        left = float(g.get("expires_at", 0)) - time.time()
        state = "USED %s" % g.get("used_at") if g.get("used") else (
            "live, %d s left" % left if left > 0 else "expired")
        print("target: %s\nstate: %s\nasked: %s\nack1: %s\nack2: %s"
              % (g.get("target"), state, g.get("ask"), g.get("ack1"), g.get("ack2")))
        return 0

    missing = [k for k in ("target", "ask", "ack1", "ack2") if not (getattr(a, k) or "").strip()]
    if missing:
        sys.exit("refused: every part of the ritual is required (missing: %s). "
                 "Ask, get a yes, restate, get a second yes - then record all four."
                 % ", ".join(missing))
    sys.path.insert(0, os.path.join(ROOT, "tools", "hooks"))
    from preserve_guard import _norm, never_reason  # noqa: E402
    nv = never_reason([_norm(a.target)])
    if nv:
        sys.exit("refused: the target is %s - no grant covers that shape." % nv)
    if len(a.ack1.strip()) < 2 or len(a.ack2.strip()) < 2:
        sys.exit("refused: an acknowledgment must be the owner's words, not a letter.")

    g = {"target": a.target, "ask": a.ask, "ack1": a.ack1, "ack2": a.ack2,
         "granted_at": time.strftime("%Y-%m-%d %H:%M"),
         "expires_at": time.time() + 60 * a.minutes, "used": False}
    os.makedirs(os.path.dirname(GRANT), exist_ok=True)
    with open(GRANT, "w", encoding="utf-8") as fh:
        json.dump(g, fh, indent=2)
    new = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER)
        fh.write("%s | %s | %s | %d | %s | %s | %s\n" % (
            g["granted_at"], workstation(), a.target, a.minutes,
            a.ask.replace("\n", " "), a.ack1.replace("\n", " "), a.ack2.replace("\n", " ")))
    print("grant recorded for %r (%d minutes, single use); ledgered in %s"
          % (a.target, a.minutes, os.path.relpath(LEDGER, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

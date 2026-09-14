"""Record the owner's double-acknowledged permission for ONE deletion.

THE PRESERVATION LAW (the CEO's ruling 2026-09-10): nothing is deleted
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

PURPOSE: Record the owner's double-acknowledged permission for one deletion:
  write the single-use, time-limited grant file and append the committed
  delete grants ledger, refusing targets in the never-delete list; performs
  no deletion itself.
INTENT: carries out the preservation law's double-acknowledgment ritual so a
  real deletion is provably the owner's decision, given twice, before the
  one deleting command runs.

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


def check_target(target):
    """None if `target` may be granted, else the never-list reason it can't be."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "hooks"))
    from preserve_guard import _norm, never_reason  # noqa: E402
    return never_reason([_norm(target)])


def write_grant(target, ask, ack1, ack2, minutes=15, now_fn=time.time,
                 grant_path=None, ledger_path=None):
    """Do the real write: the grant file + one ledger line. Raises ValueError
    on a refused target or a too-short acknowledgment; writes nothing then.
    `grant_path`/`ledger_path`/`now_fn` are injectable so a selftest can point
    this at a temp dir and a fake clock without touching the live files."""
    grant_path = grant_path or GRANT
    ledger_path = ledger_path or LEDGER
    nv = check_target(target)
    if nv:
        raise ValueError("the target is %s - no grant covers that shape." % nv)
    if len(ack1.strip()) < 2 or len(ack2.strip()) < 2:
        raise ValueError("an acknowledgment must be the owner's words, not a letter.")

    now = now_fn()
    g = {"target": target, "ask": ask, "ack1": ack1, "ack2": ack2,
         "granted_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(now)),
         "expires_at": now + 60 * minutes, "used": False}
    os.makedirs(os.path.dirname(grant_path), exist_ok=True)
    with open(grant_path, "w", encoding="utf-8") as fh:
        json.dump(g, fh, indent=2)
    new = not os.path.isfile(ledger_path)
    with open(ledger_path, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER)
        fh.write("%s | %s | %s | %d | %s | %s | %s\n" % (
            g["granted_at"], workstation(), target, minutes,
            ask.replace("\n", " "), ack1.replace("\n", " "), ack2.replace("\n", " ")))
    return g


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
    try:
        write_grant(a.target, a.ask, a.ack1, a.ack2, a.minutes)
    except ValueError as exc:
        sys.exit("refused: %s" % exc)
    print("grant recorded for %r (%d minutes, single use); ledgered in %s"
          % (a.target, a.minutes, os.path.relpath(LEDGER, ROOT)))
    return 0


def _selftest():
    """Exercise the real write_grant() path against a temp grant file and
    ledger (never the live .claude/delete_grant.json or
    docs/history/delete_grants.txt); the clock is injected so expiry can be
    proven without sleeping. tempfile.mkdtemp() is left in place afterward -
    a selftest never deletes anything (THE PRESERVATION LAW)."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="everwood_delete_grant_selftest_")
    grant_path = os.path.join(tmp, "grant.json")
    ledger_path = os.path.join(tmp, "delete_grants.txt")
    fails = 0
    fixed_now = 1_700_000_000.0
    clock = lambda: fixed_now  # noqa: E731

    write_grant(os.path.join(tmp, "scratch_target_one.txt"), "ask one", "yes", "yes indeed",
                minutes=15, now_fn=clock, grant_path=grant_path, ledger_path=ledger_path)
    ok = os.path.isfile(ledger_path) and open(ledger_path, encoding="utf-8").read().startswith(HEADER)
    print(("PASS  " if ok else "FAIL  ") + "ledger created with its header when absent")
    fails += not ok

    write_grant(os.path.join(tmp, "scratch_target_two.txt"), "ask two", "yep", "yes again",
                minutes=5, now_fn=clock, grant_path=grant_path, ledger_path=ledger_path)
    text = open(ledger_path, encoding="utf-8").read()
    ok = sum(1 for ln in text.splitlines() if ln.startswith("#")) == 3
    print(("PASS  " if ok else "FAIL  ") + "second write appends without repeating the header")
    fails += not ok

    data_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    ok = len(data_lines) == 2 and all(len(ln.split(" | ")) == 7 for ln in data_lines)
    print(("PASS  " if ok else "FAIL  ") + "line format matches the header's 7 columns")
    fails += not ok

    for bad_target, label in ((r"C:\\", "a drive root"),
                               (os.path.expanduser("~"), "the home folder"),
                               (ROOT, "the repo root")):
        try:
            write_grant(bad_target, "ask", "yes", "yes", minutes=15, now_fn=clock,
                        grant_path=grant_path, ledger_path=ledger_path)
            ok = False
        except ValueError:
            ok = True
        print(("PASS  " if ok else "FAIL  ") + "refuses %s as a target" % label)
        fails += not ok

    g_exp = write_grant(os.path.join(tmp, "scratch_target_three.txt"), "ask", "yes", "yes",
                         minutes=15, now_fn=clock, grant_path=grant_path, ledger_path=ledger_path)
    later = fixed_now + 60 * 20  # 20 simulated minutes after a 15-minute grant
    ok = (g_exp["expires_at"] - later) <= 0
    print(("PASS  " if ok else "FAIL  ") + "grant expires after its window (simulated clock)")
    fails += not ok

    # a pre-existing header-only ledger must not get a second header
    ledger2 = os.path.join(tmp, "preexisting_ledger.txt")
    with open(ledger2, "w", encoding="utf-8") as fh:
        fh.write(HEADER)
    write_grant(os.path.join(tmp, "scratch_target_four.txt"), "ask", "yes", "yes",
                minutes=15, now_fn=clock, grant_path=grant_path, ledger_path=ledger2)
    text2 = open(ledger2, encoding="utf-8").read()
    ok = sum(1 for ln in text2.splitlines() if ln.startswith("#")) == 3
    print(("PASS  " if ok else "FAIL  ") + "pre-existing header-only ledger takes its first real append cleanly")
    fails += not ok

    print("delete_grant selftest: %d failed (scratch dir left at %s, never cleaned up - THE PRESERVATION LAW)"
          % (fails, tmp))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    sys.exit(main())

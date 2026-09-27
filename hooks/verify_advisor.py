"""Stop hook: LEDGER ADVISED - no turn ends with an unverified delegation
(the CEO 2026-09-26: "make these processes more fool proof... through
hooks"). lesson_advisor's twin.

delegation_auditor appends one PENDING line per work delegation the
moment its report lands (docs/history/delegation_pending.txt, the
harness-metered figures inside). This hook reads that ledger at the
tail, append-only style: a PENDING id with no later `RESOLVED | <id>`
line is an unverified delegation, and the turn is refused ONCE (per
unresolved-set signature, same loop guard as lesson_advisor) with
LEDGER ADVISED: verify cheap, write the SUBAGENTS.md ledger line,
resolve the intent claim, append the RESOLVED line - or say in one line
why not, and the next stop passes. This closes the exact public failure
the CEO relayed: a manager saying employees did their job and moving
on; moving on is what gets blocked.

PURPOSE: Stop hook that reads delegation_pending.txt for PENDING ids
  without a later RESOLVED line and refuses to end the turn once per
  unresolved set with LEDGER ADVISED, so every delegation is verified
  and ledgered (or its deferral stated) before the manager moves on.
INTENT: the CEO 2026-09-26: "Can we make these processes more fool proof
  in any way through hooks" - verification was the one delegation step
  with no mechanical backstop.

Search keys: verify advisor, ledger advised, stop hook, delegation
pending, RESOLVED line, unverified delegation, rule 5.
See also: tools/hooks/delegation_auditor.py (writes the PENDING lines);
tools/hooks/lesson_advisor.py (the pattern); SUBAGENTS.md (rules 4, 5);
LESSONS.md "An append-only tracker is read at its tail".
"""
import hashlib
import json
import os
import sys

from _hooklib import ROOT, emit, read_input

PENDING = os.path.join(ROOT, "docs", "history", "delegation_pending.txt")
STATE = os.path.join(ROOT, ".claude", "verify_state.json")  # gitignored, per machine


def unresolved(text):
    """PENDING ids with no LATER RESOLVED line, in file order (the tail is
    the state: a RESOLVED line only clears a PENDING that came before it)."""
    pend = []
    for line in (text or "").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4 and parts[3] == "PENDING" and parts[2] not in pend:
            pend.append(parts[2])
        elif len(parts) >= 2 and parts[0].startswith("RESOLVED") and parts[1] in pend:
            pend.remove(parts[1])
    return pend


def decide(ids, mine):
    """('pass'|'block', reason); blocks once per unresolved-set signature."""
    if not ids:
        mine["last_sig"] = ""
        return "pass", ""
    sig = hashlib.sha1(",".join(sorted(ids)).encode("utf-8")).hexdigest()[:12]
    if mine.get("last_sig") == sig:
        return "pass", ""
    mine["last_sig"] = sig
    return "block", (
        "[HOOK verify_advisor] LEDGER ADVISED (%d unverified delegation%s: %s) - before this "
        "turn ends: verify cheap (test -> diff -> smell, SUBAGENTS.md rule 4), append the "
        "SUBAGENTS.md ledger line with the metered figures (rule 5), resolve the intent claim "
        "(rule 14), then append `RESOLVED | <id> | OK/CORRECTED - <words>` to "
        "docs/history/delegation_pending.txt - or say in one line why verification waits. "
        "This hook does not refuse the same set twice."
        % (len(ids), "s" if len(ids) != 1 else "", ", ".join(ids)))


def main():
    data = read_input()
    if data.get("stop_hook_active"):
        sys.exit(0)
    try:
        with open(PENDING, encoding="utf-8") as fh:
            ids = unresolved(fh.read())
    except OSError:
        sys.exit(0)  # no ledger yet = nothing pending
    try:
        with open(STATE, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        state = {}
    mine = dict(state.get("pending") or {})
    action, reason = decide(ids, mine)
    state["pending"] = mine
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
    except OSError:
        pass
    if action == "block":
        emit({"decision": "block", "reason": reason})
    sys.exit(0)


def _selftest():
    """Pure checks on unresolved()/decide(); never reads the real ledger."""
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    txt = ("2026-09-26 15:40 | WS2 | Dabc123 | PENDING | metered tools=6 tokens=74000 | wire X\n"
           "2026-09-26 15:41 | WS2 | Ddef456 | PENDING | metered tools=9 tokens=81000 | wire Y\n"
           "RESOLVED | Dabc123 | OK - diff matched, WOODTEST green\n")
    ok("a RESOLVED line clears its id, the other stays", unresolved(txt) == ["Ddef456"])
    ok("an empty ledger is clean", unresolved("") == [])
    ok("RESOLVED before its PENDING never clears (the tail is the state)",
       unresolved("RESOLVED | Dx | OK\n2026-09-26 | WS2 | Dx | PENDING | m | t\n") == ["Dx"])
    mine = {}
    a, r = decide(["Ddef456"], mine)
    ok("an unresolved id blocks once with LEDGER ADVISED",
       a == "block" and "LEDGER ADVISED" in r and "Ddef456" in r)
    ok("the same set never blocks twice", decide(["Ddef456"], mine)[0] == "pass")
    ok("a new id blocks again", decide(["Ddef456", "Dnew111"], mine)[0] == "block")
    a, _ = decide([], mine)
    ok("a cleared ledger passes and resets the signature",
       a == "pass" and mine["last_sig"] == "")
    print("verify_advisor selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

"""Stop hook: THE LESSON LOOP's stop end - LESSON ADVISED (the CEO 2026-09-20).

The checkpoint counter's twin. When the manager finishes a reply, this
hook reads the turn's slice of the harness transcript (everything since
the last Stop, by a per-transcript line pointer in .claude/lesson_state.json)
and asks tools/lesson_log.py for trial-and-error signals: the same command
run again after an error, repeated edit misses, a FAIL followed by a PASS,
an intent claim resolved DIFFERENT, an employee briefed twice, a prompt that
reads as a correction. When it sees one it REFUSES to end the turn once
with the reason "LESSON ADVISED" so the instruction lands in the manager's
context (a systemMessage only reaches the user), and ADVISED MEANS DO IT:
the manager writes or amends the LESSONS.md entry for the task shape, or
puts the fact in its topic file under a Tags line, or says in one line why
there is no lesson, then ends the turn. `stop_hook_active` and a per-slice
signature guard against loops: it never refuses the same slice twice, and
a turn that already edited LESSONS.md is ledgered WRITTEN and passes.

Silent on a clean turn, zero tokens. Every advised turn appends one
ADVISED line to docs/history/lesson_runs.txt; the check loop counts them
against entries written (tools/ledger_trends.py rule 14).

PURPOSE: Stop hook that scans the turn's transcript slice for trial-and-
  error signals and refuses to end the turn once with LESSON ADVISED when it
  finds one, so the manager captures the lesson in LESSONS.md or the wiki
  before the turn ends; silent otherwise, never the same slice twice.
INTENT: the CEO 2026-09-20: "something to push you to write what you
  learned, as well as push you to add to the knowledge base" - the
  checkpoint hook fires on work, nothing fired on trial and error until this.

Search keys: lesson advised, stop hook, lesson loop, trial and error,
knowledge capture, lesson state.
See also: tools/lesson_log.py (the signals + the ledger); LESSONS.md (the
book + the law); tools/hooks/stop_tick.py (the checkpoint twin);
tools/hooks/prompt_gauge.py (the prompt end).
"""
import hashlib
import json
import os
import sys

from _hooklib import ROOT, emit, read_input
import lesson_log as ll

STATE = os.path.join(ROOT, ".claude", "lesson_state.json")  # gitignored, per machine


def load_state(path=STATE):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(state, path=STATE):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
    except OSError:
        pass


def decide(sigs, mine):
    """(action, reason) for a slice's signals against this transcript's state:
    'pass' (nothing, or already advised for this signature), 'written' (the
    book was edited this turn), 'block' (refuse once with the reason).
    `mine` is updated in place with the signature that was acted on."""
    real = [s for s in sigs if not s.startswith("WRITTEN")]
    written = any(s.startswith("WRITTEN") for s in sigs)
    if written:
        mine["last_sig"] = ""
        return "written", "; ".join(real)
    if not real:
        return "pass", ""
    sig = hashlib.sha1("\n".join(real).encode("utf-8")).hexdigest()[:12]
    if mine.get("last_sig") == sig:
        return "pass", ""
    mine["last_sig"] = sig
    reason = ("[HOOK lesson_advisor] LESSON ADVISED (%s) - ADVISED MEANS DO IT (THE LESSON LAW, "
              "the CEO 2026-09-20): before this turn ends, write or amend the LESSONS.md entry "
              "for this task shape (heading in a prompt's words; Tags + Keys lines; THE ONE RIGHT "
              "WAY; TRIED / FAILED BECAUSE / DO INSTEAD), or put the fact in its topic file under "
              "a Tags line, or say in one line why there is no lesson here. Then end the turn; "
              "this hook does not refuse the same turn twice." % "; ".join(real))
    return "block", reason


def main():
    data = read_input()
    if data.get("stop_hook_active"):
        sys.exit(0)
    path = data.get("transcript_path")
    if not path or not os.path.isfile(path):
        try:
            import checkpoint as cp
            files = cp._transcript_files()
            path = files[0] if files else None
        except Exception:  # noqa: BLE001 - a hook never crashes the turn
            path = None
    if not path:
        sys.exit(0)
    state = load_state()
    key = os.path.basename(path)
    mine = dict(state.get(key) or {})
    try:
        sigs, n = ll.scan(path, int(mine.get("line") or 0))
    except Exception:  # noqa: BLE001
        sys.exit(0)
    mine["line"] = n
    action, reason = decide(sigs, mine)
    state[key] = mine
    save_state(state)
    if action == "written":
        ll.record("WRITTEN", reason or "LESSONS.md edited this turn")
    elif action == "block":
        ll.record("ADVISED", "; ".join(s for s in sigs if not s.startswith("WRITTEN")))
        emit({"decision": "block", "reason": reason})
    sys.exit(0)


def _selftest():
    """Pure checks on decide(): never reads a real transcript or writes the
    real state file or ledger."""
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    mine = {}
    ok("a clean slice passes", decide([], mine) == ("pass", ""))
    a, r = decide(["a FAIL was followed by a PASS"], mine)
    ok("a signal blocks once with LESSON ADVISED", a == "block" and "LESSON ADVISED" in r
       and "FAIL was followed" in r)
    ok("the same signature never blocks twice", decide(["a FAIL was followed by a PASS"], mine)[0] == "pass")
    ok("a new signature blocks again", decide(["2 edit calls missed their target"], mine)[0] == "block")
    a, r = decide(["2 edit calls missed their target", "WRITTEN: LESSONS.md was edited this turn"], mine)
    ok("a turn that edited the book is WRITTEN, not blocked", a == "written")
    ok("state round-trips through a temp file", (lambda p: (save_state({"t": {"line": 3}}, p),
                                                          load_state(p) == {"t": {"line": 3}})[1])(
        os.path.join(os.environ.get("TEMP", "."), "everwood_lesson_state_selftest.json")))
    print("lesson_advisor selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

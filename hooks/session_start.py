"""SessionStart hook: run the standup digest and inject it (Tier 1, #1).

Fires on startup, resume, /clear and after a compaction. This is the end
of "after /clear the CEO has nothing": the digest (THE LAST EXCHANGE mined
from the harness transcript + state + roadmap + ledger tails) arrives in
the manager's context without anyone typing "standup".

Answers `--selftest` (house pattern: PASS/FAIL lines on the pure header
builder and the pure loop/size helpers, never a live standup.py run, a real
run_all.py session run, or a write to the real digest_size.txt ledger).

THE LOOP LAW (the CEO's ruling 2026-09-14, "any script that should be run
multiple times must be called by the main looping script"): before running
standup.py, this hook checks docs/history/loop_runs.txt (via
tools/run_all.py's `last_run("session")`) and runs `run_all.py session`
itself when the session group has not run yet today on this workstation -
so the regen/check/metrics habit no longer depends on anyone remembering to
run it by hand. A one-line "[loop] ..." note is prepended to the digest
either way; a loop failure never blocks the digest itself.

THE DIGEST SIZE (the CEO's ruling 2026-09-14, "measure the standup digest"):
every injected digest appends one line to docs/history/digest_size.txt
(bytes + a bytes/4 token estimate + the trigger) so digest bloat shows up
in a ledger instead of only being felt.

PURPOSE: SessionStart hook that runs tools/standup.py and injects its digest
  into the manager's context on startup, resume, /clear and after a
  compaction, with a header telling the manager not to re-run standup and
  how to relay the last exchange; also runs the session group itself when
  it has not run today (THE LOOP LAW) and ledgers the digest's byte size.
INTENT: closes the gap where after a /clear the manager has no memory of the
  session, by re-injecting the last exchange, state and roadmap tails
  automatically instead of relying on anyone remembering to run standup;
  and makes the session group's habitual run, and the digest's size,
  measured rather than assumed.

Search keys: session start hook, auto standup, resume after clear, compact,
loop law, session group, digest size.
See also: tools/standup.py (the digest); tools/run_all.py (THE LOOP LEDGER,
last_run); docs/history/loop_runs.txt; docs/history/digest_size.txt;
.claude/skills/standup (the ritual this automates); tools/hooks/_hooklib.py.
"""
import datetime
import os
import subprocess
import sys
import time

from _hooklib import ROOT, TOOLS, context, read_input
import checkpoint as cp

DIGEST_SIZE_LEDGER = os.path.join(ROOT, "docs", "history", "digest_size.txt")


def header_for(source):
    return ("[HOOK session_start | trigger: %s] The standup digest below was "
             "injected automatically by .claude/settings.json - the /standup "
             "ritual already ran; do NOT run standup.py again. Manager: on a "
             "fresh session or after /clear, relay THE LAST EXCHANGE block "
             "FIRST and VERBATIM (both sides, in quote blocks), then state + "
             "next-likely, then a brief digest summary, then ask what to work "
             "on. After a compaction, use it to re-anchor silently unless "
             "something in it contradicts the summary." % source)


def run_standup():
    """Runs tools/standup.py and returns its digest text (or an error note)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "standup.py")],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=100)
        out = r.stdout.strip()
        if r.returncode != 0 or not out:
            out = "(standup.py failed rc=%s)\n%s" % (r.returncode, r.stderr[-800:])
    except Exception as exc:  # never break a session over the digest
        out = "(standup.py could not run: %s)" % exc
    return out


def session_ran_today(last, now=None):
    """Pure: has the session group's last_run() datetime already happened
    today? `last` is None when the group has never run."""
    now = now or datetime.datetime.now()
    return last is not None and last.date() == now.date()


def _run_note(returncode, tail_line, seconds):
    """Pure: the one-line note for an actual run_all.py session attempt."""
    if returncode == 0:
        return "[loop] session group ran in %d s" % seconds
    return "[loop] session group FAILED: %s" % tail_line


def loop_note():
    """THE LOOP LAW (the CEO 2026-09-14): runs the session group itself when
    it has not run today on this workstation, instead of relying on anyone
    remembering. Never raises - a loop failure never blocks the digest."""
    try:
        import run_all as ra
        last = ra.last_run("session")
    except Exception as exc:
        return "[loop] could not check run_all: %s" % exc
    if session_ran_today(last):
        return "[loop] session group last ran %s today" % last.strftime("%H:%M")
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "run_all.py"), "session"],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        seconds = time.time() - t0
        tail = (r.stdout + r.stderr).strip().splitlines()
        return _run_note(r.returncode, tail[-1] if tail else "(no output)", int(seconds))
    except Exception as exc:
        return "[loop] session group FAILED: %s" % exc


def _digest_line(text, ws, trigger, now=None):
    """Pure: the digest_size.txt line for `text` as injected."""
    now = now or datetime.datetime.now()
    b = len(text.encode("utf-8"))
    return "%s | %s | %d | %d | %s\n" % (
        now.strftime("%Y-%m-%d %H:%M"), ws, b, b // 4, trigger)


def log_digest_size(text, trigger):
    """Appends one digest_size.txt line. Never raises - a ledger failure
    never blocks the digest."""
    try:
        os.makedirs(os.path.dirname(DIGEST_SIZE_LEDGER), exist_ok=True)
        fresh = not os.path.isfile(DIGEST_SIZE_LEDGER)
        with open(DIGEST_SIZE_LEDGER, "a", encoding="utf-8") as fh:
            if fresh:
                fh.write("# standup digest size per session: date time | ws | "
                          "bytes | ~tokens (bytes/4) | trigger\n")
            fh.write(_digest_line(text, cp.which_ws(), trigger))
    except Exception:
        pass


def main():
    data = read_input()
    source = data.get("source", "?")
    note = loop_note()
    out = run_standup()
    digest = (note + "\n\n" + out) if note else out
    full_text = header_for(source) + "\n\n" + digest
    log_digest_size(full_text, source)
    context("SessionStart", full_text)


def _selftest():
    """Checks the pure header builder and the pure loop/size helpers - never
    runs standup.py, run_all.py session, or writes the real digest_size.txt
    ledger (slow, and it appends to real ledgers)."""
    fails = 0
    h = header_for("clear")
    ok = "trigger: clear" in h and "do NOT run standup.py again" in h
    print(("PASS  " if ok else "FAIL  ") + "header_for carries trigger + the no-rerun line")
    fails += not ok
    ok = os.path.isfile(os.path.join(TOOLS, "standup.py"))
    print(("PASS  " if ok else "FAIL  ") + "tools/standup.py exists")
    fails += not ok
    ok = os.path.isfile(os.path.join(TOOLS, "run_all.py"))
    print(("PASS  " if ok else "FAIL  ") + "tools/run_all.py exists")
    fails += not ok

    now = datetime.datetime(2026, 9, 14, 12, 0)
    today = datetime.datetime(2026, 9, 14, 8, 30)
    yesterday = datetime.datetime(2026, 9, 13, 8, 30)
    ok = session_ran_today(today, now) is True
    print(("PASS  " if ok else "FAIL  ") + "session_ran_today: run earlier today -> True")
    fails += not ok
    ok = session_ran_today(yesterday, now) is False
    print(("PASS  " if ok else "FAIL  ") + "session_ran_today: run yesterday -> False")
    fails += not ok
    ok = session_ran_today(None, now) is False
    print(("PASS  " if ok else "FAIL  ") + "session_ran_today: never run -> False")
    fails += not ok

    note_ok = _run_note(0, "tail", 12)
    ok = note_ok == "[loop] session group ran in 12 s"
    print(("PASS  " if ok else "FAIL  ") + "_run_note: success note")
    fails += not ok
    note_bad = _run_note(1, "boom", 5)
    ok = "FAILED: boom" in note_bad
    print(("PASS  " if ok else "FAIL  ") + "_run_note: failure note carries the tail line")
    fails += not ok

    line = _digest_line("x" * 400, "WS1", "startup", now)
    ok = ("| WS1 | 400 | 100 | startup" in line)
    print(("PASS  " if ok else "FAIL  ") + "_digest_line: bytes + bytes//4 + trigger")
    fails += not ok

    print("session_start selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

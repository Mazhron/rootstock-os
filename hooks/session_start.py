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

THE RESUME POINTER (kit v1.57, the CEO's yes 2026-10-31): the ledger showed
3.6 fires per session on the origin, resume fires at ~4.1k tokens each,
three of them inside one minute. A resume reopens the same conversation,
so the digest injected at its start is still in context; this hook now
injects one pointer line on resume (trigger "resume-pointer" in the ledger)
and the whole digest only when the day changed since this workstation's
last digest, or when the modes file says resume_digest = "full" (the old
way, kept). startup, clear and compact always get the whole digest.

PURPOSE: SessionStart hook that runs tools/standup.py and injects its digest
  into the manager's context on startup, resume, /clear and after a
  compaction, with a header telling the manager not to re-run standup and
  how to relay the last exchange; also runs the session group itself when
  it has not run today (THE LOOP LAW) and ledgers the digest's byte size;
  on a same-day resume it injects one pointer line instead of the digest
  (resume_digest = full in the modes file restores the old way); past the
  harness's 10,000-char injection cap it parks whole sections in
  .claude/standup_tail.txt in a fixed order and ends the head with a DIGEST
  TAIL line naming them (THE CAP SPLIT, kit v1.61; digest_cap_split = false
  injects the whole text, the old way).
INTENT: closes the gap where after a /clear the manager has no memory of the
  session, by re-injecting the last exchange, state and roadmap tails
  automatically instead of relying on anyone remembering to run standup;
  and makes the session group's habitual run, and the digest's size,
  measured rather than assumed.

Search keys: session start hook, auto standup, resume after clear, compact,
loop law, session group, digest size, resume pointer, modes file, cap split,
digest tail, 10,000 characters, injection cap.
See also: tools/standup.py (the digest); tools/run_all.py (THE LOOP LEDGER,
last_run); docs/history/loop_runs.txt; docs/history/digest_size.txt;
.claude/skills/standup (the ritual this automates); tools/hooks/_hooklib.py.
"""
import datetime
import os
import subprocess
import sys
import time

from _hooklib import ROOT, TOOLS, context, mode, read_input
import checkpoint as cp

DIGEST_SIZE_LEDGER = os.path.join(ROOT, "docs", "history", "digest_size.txt")


def pointer_for(loop_line):
    """THE RESUME POINTER (v1.57): the one-line injection on a same-day resume."""
    return ("[HOOK session_start | trigger: resume] The conversation resumed intact; the "
            "standup digest injected at its start still stands and standup.py was NOT re-run "
            "(THE RESUME POINTER, kit v1.57; resume_digest = \"full\" in "
            ".claude/rootstock_modes.json restores the whole digest). If the digest is no "
            "longer in context, run `python tools/standup.py` once. %s" % (loop_line or ""))


def last_digest_date(ws, path=DIGEST_SIZE_LEDGER):
    """The date (YYYY-MM-DD) of this workstation's newest digest_size.txt
    line, or "" when there is none. Reads the tail only."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 8192))
            tail = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return ""
    for ln in reversed(tail):
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 5 and parts[1] == ws and not ln.startswith("#"):
            return parts[0][:10]
    return ""


def resume_wants_full(source, resume_mode, last_date, today):
    """Pure: does this SessionStart get the whole digest? Everything but a
    resume does; a resume does when the old way is selected or the day
    changed since this workstation's last digest."""
    if source != "resume":
        return True
    if resume_mode == "full":
        return True
    return last_date != today


def header_for(source):
    """THE EIGHTH TRIM (2026-11-06): the header is part of the injection and
    counts against the cap; the dated rulings it used to quote live in
    HOOKS_METHOD.md Tier 1 #1 and .claude/skills/standup (~1,460 -> ~800)."""
    return ("[HOOK session_start | trigger: %s] The standup digest below was "
            "injected by .claude/settings.json - the /standup ritual already ran; "
            "do NOT run standup.py again. Manager, on a fresh session or after "
            "/clear: relay THE LAST EXCHANGE FIRST and VERBATIM - the user's last "
            "prompt in a quote block, then your own last response in a quote "
            "block, exactly as the digest prints them (THE VERBATIM OPENER, "
            "2026-11-03; the block is already the final message, nested relay "
            "stripped, 2000 chars a side, so quoting it cannot nest); then state "
            "+ next-likely, a brief digest summary, then ask what to work on. THE "
            "PROPOSAL LAW: every PROPOSE [DO] line is done in this first reply by "
            "a script, a hook or an employee; only [ASK] lines are questions. "
            "After a compaction, re-anchor silently unless the digest contradicts "
            "the summary. A DIGEST TAIL line at the end names sections parked in "
            "a file; Read it only where a section is needed." % source)


# THE CAP SPLIT (kit v1.61, 2026-11-06). Measured on the origin's transcripts
# (entry point claude-vscode, harness 2.1.289): a hook's additionalContext
# past 10,000 characters is persisted to a file and the model gets a 2KB
# preview plus the path; one 9,919-char digest arrived whole, 26 of 27
# since October were cut and read back by a Read. So the hook delivers a
# head it chose, under the cap, and parks whole sections in one local file
# the head names - nothing dropped, the tail one Read away by section.
# LESSONS.md "A hook injection past 10,000 characters arrives as a 2KB
# preview and a file path".
INJECT_CAP = 9500
TAIL_FILE = os.path.join(ROOT, ".claude", "standup_tail.txt")   # gitignored, per machine
TAIL_FILE_REL = ".claude/standup_tail.txt"
# Moved to the tail in this order until the head fits; a key is matched by
# prefix against the section's header line. THE LAST EXCHANGE, WHERE WE
# LEFT OFF, NEW DAY / SAME DAY and the header are never moved.
TAIL_ORDER = ("== OPEN ROADMAP", "== NEWEST WS NOTES", "== RECENT DAYS",
              "== LEDGER TAILS (quiet lines)", "== VERSION + RECENT COMMITS",
              "== THE CORE", "== THE LOOP", "== LEDGER TAILS", "== OPEN QUESTIONS",
              "== PROPOSALS")
QUIET_NAME = "== LEDGER TAILS (quiet lines)"


def sections(text):
    """Pure: [(header line or '' for the preamble, [lines])]. LEDGER TAILS'
    quiet block (the `  quiet (` line to the section's end) is its own
    section so the verdict lines can stay while the names move."""
    out = [["", []]]
    for ln in text.split("\n"):
        if ln.startswith("== "):
            out.append([ln, [ln]])
        elif (out[-1][0].startswith("== LEDGER TAILS") and out[-1][0] != QUIET_NAME
              and ln.startswith("  quiet (")):
            out.append([QUIET_NAME, [ln]])
        else:
            out[-1][1].append(ln)
    return [(n, ls) for n, ls in out if ls]


def short_name(header):
    """'== OPEN ROADMAP (NEXT_STEPS.md; ...)' -> 'OPEN ROADMAP'."""
    name = header[3:] if header.startswith("== ") else header
    if name == QUIET_NAME[3:]:
        return "LEDGER TAILS quiet lines"
    return name.split(" (", 1)[0].split(" - ", 1)[0].strip()


def tail_line(moved, tail_chars, path=TAIL_FILE_REL):
    return ("== DIGEST TAIL (THE CAP SPLIT): %d chars past the harness's 10,000-char "
            "injection cap moved to %s, nothing dropped - %s. Read that file before "
            "planning an arc (the roadmap), a cross-workstation step (the notes) or a "
            "ledger trend (the quiet lines)."
            % (tail_chars, path, "; ".join("%s (%d)" % m for m in moved)))


def split_for_cap(text, cap=INJECT_CAP, order=TAIL_ORDER, path=TAIL_FILE_REL):
    """Pure: (head, tail, moved [(name, chars)]). Under the cap: (text, '', []).
    Over it: sections leave in `order` until the head (with its DIGEST TAIL
    line) fits; if every movable section is gone and it still does not fit,
    the head is what remains (the harness will cut it; the ledger says so)."""
    if len(text) <= cap:
        return text, "", []
    secs = sections(text)
    moved_idx = []

    def head_of():
        kept = [ln for i, (n, ls) in enumerate(secs) if i not in moved_idx for ln in ls]
        moved = [(short_name(secs[i][0]), len("\n".join(secs[i][1]))) for i in sorted(moved_idx)]
        tail = "\n".join(ln for i in sorted(moved_idx) for ln in secs[i][1])
        head = "\n".join(kept)
        if moved:
            head += "\n" + tail_line(moved, len(tail), path)
        return head, tail, moved

    for key in order:
        for i, (n, ls) in enumerate(secs):
            if i in moved_idx or not n.startswith(key):
                continue
            if key == "== LEDGER TAILS" and n == QUIET_NAME:
                continue
            moved_idx.append(i)
        head, tail, moved = head_of()
        if len(head) <= cap:
            return head, tail, moved
    return head_of()


def write_tail(tail, trigger, path=TAIL_FILE):
    """The parked sections, regenerated whole each time; never raises."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# standup digest tail, written %s by tools/hooks/session_start.py "
                     "(trigger: %s) - THE CAP SPLIT: these sections were moved out of the "
                     "injection to keep it under the harness's 10,000-char cap; the head "
                     "in context names them. Regenerated at every session start.\n\n"
                     % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), trigger))
            fh.write(tail + "\n")
        return True
    except Exception:
        return False


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
    if not resume_wants_full(source, mode("resume_digest", "pointer"),
                             last_digest_date(cp.which_ws()),
                             datetime.date.today().isoformat()):
        text = pointer_for(note)
        log_digest_size(text, "resume-pointer")
        context("SessionStart", text)
        return
    out = run_standup()
    digest = (note + "\n\n" + out) if note else out
    full_text = header_for(source) + "\n\n" + digest
    # THE CAP SPLIT (v1.61): the ledger keeps the WHOLE digest's bytes (the
    # diet ritual measures the digest, not the delivery); the trigger field
    # says what was injected and what was parked.
    head, tail, moved = (split_for_cap(full_text) if mode("digest_cap_split", True)
                         else (full_text, "", []))
    if moved and not write_tail(tail, source):
        head, moved = full_text, []   # the file could not be written: inject whole
    log_digest_size(full_text, source if not moved else
                    "%s (head %d, tail %d)" % (source, len(head), len(tail)))
    context("SessionStart", head)


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

    # THE RESUME POINTER (v1.57)
    ok = (resume_wants_full("startup", "pointer", "2026-10-31", "2026-10-31") is True
          and resume_wants_full("clear", "pointer", "2026-10-31", "2026-10-31") is True
          and resume_wants_full("compact", "pointer", "2026-10-31", "2026-10-31") is True)
    print(("PASS  " if ok else "FAIL  ") + "resume_wants_full: startup, clear and compact always get the digest")
    fails += not ok
    ok = resume_wants_full("resume", "pointer", "2026-10-31", "2026-10-31") is False
    print(("PASS  " if ok else "FAIL  ") + "resume_wants_full: a same-day resume gets the pointer")
    fails += not ok
    ok = (resume_wants_full("resume", "pointer", "2026-10-30", "2026-10-31") is True
          and resume_wants_full("resume", "pointer", "", "2026-10-31") is True)
    print(("PASS  " if ok else "FAIL  ") + "resume_wants_full: a day change or no ledger gets the digest")
    fails += not ok
    ok = resume_wants_full("resume", "full", "2026-10-31", "2026-10-31") is True
    print(("PASS  " if ok else "FAIL  ") + "resume_wants_full: resume_digest=full is the old way")
    fails += not ok
    import tempfile
    tmpd = tempfile.mkdtemp(prefix="digest_size_")
    p = os.path.join(tmpd, "digest_size.txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("# header\n2026-10-29 16:03 | WS2 | 21920 | 5480 | startup\n"
                 "2026-10-30 14:54 | WS1 | 15651 | 3912 | resume\n"
                 "2026-10-30 15:10 | WS2 | 15393 | 3848 | clear\n")
    ok = last_digest_date("WS2", p) == "2026-10-30" and last_digest_date("WS1", p) == "2026-10-30" \
        and last_digest_date("WS9", p) == "" and last_digest_date("WS2", p + ".missing") == ""
    print(("PASS  " if ok else "FAIL  ") + "last_digest_date: newest line per workstation, empty when none")
    fails += not ok
    ptr = pointer_for("[loop] session group last ran 09:00 today")
    ok = "trigger: resume" in ptr and "NOT re-run" in ptr and "[loop]" in ptr and len(ptr) < 700
    print(("PASS  " if ok else "FAIL  ") + "pointer_for: one short line carrying the trigger and the loop note")
    fails += not ok

    # THE CAP SPLIT (v1.61)
    hdr = header_for("clear")
    ok = len(hdr) < 1000
    print(("PASS  " if ok else "FAIL  ") + "header_for: under 1,000 chars (the eighth trim; was ~1,460)")
    fails += not ok
    sample = (hdr + "\n\n[loop] note\n\n"
              "== THE LAST EXCHANGE (x)\n" + "  > e\n" * 40
              + "== WHERE WE LEFT OFF (d.md)\n" + "  - s\n" * 30
              + "== THE LOOP (g)\n  check | 1 d\n"
              + "== PROPOSALS (p)\n" + "  PROPOSE [DO] x\n" * 10
              + "== VERSION + RECENT COMMITS (c)\n  version: 1\n  abc one\n"
              + "== LEDGER TAILS (h)\n" + "  a_runs.txt: FAIL x\n" * 10
              + "  quiet (no verdict):\n" + "    b 11-01, c 11-02\n" * 10
              + "== OPEN ROADMAP (n)\n" + "  - [NS-1] r\n" * 40
              + "== RECENT DAYS (d)\n  2026-11-01 | WS1 | x\n")
    secs = sections(sample)
    names = [short_name(n) for n, _ in secs if n]
    ok = names == ["THE LAST EXCHANGE", "WHERE WE LEFT OFF", "THE LOOP", "PROPOSALS",
                   "VERSION + RECENT COMMITS", "LEDGER TAILS", "LEDGER TAILS quiet lines",
                   "OPEN ROADMAP", "RECENT DAYS"]
    print(("PASS  " if ok else "FAIL  ") + "sections: every == block, the quiet lines their own (%s)" % names)
    fails += not ok
    h, t, m = split_for_cap(sample, cap=len(sample) + 1)
    ok = h == sample and t == "" and m == []
    print(("PASS  " if ok else "FAIL  ") + "split_for_cap: under the cap nothing moves")
    fails += not ok
    cap = len(sample) - 200
    h, t, m = split_for_cap(sample, cap=cap)
    ok = (len(h) <= cap and [x[0] for x in m] == ["OPEN ROADMAP"]
          and "== OPEN ROADMAP" in t and "== OPEN ROADMAP" not in h
          and "== DIGEST TAIL (THE CAP SPLIT)" in h and "OPEN ROADMAP (" in h)
    print(("PASS  " if ok else "FAIL  ") + "split_for_cap: the roadmap leaves first, the head names it and fits")
    fails += not ok
    cap = len(hdr) + 1200
    h, t, m = split_for_cap(sample, cap=cap)
    moved = [x[0] for x in m]
    # `moved` reads in document order (the tail file's order); the moving
    # itself follows TAIL_ORDER, so the roadmap, recent days and the quiet
    # lines are gone before any verdict line is.
    ok = (len(h) <= cap and "THE LAST EXCHANGE" not in moved and "WHERE WE LEFT OFF" not in moved
          and "== THE LAST EXCHANGE" in h and "== WHERE WE LEFT OFF" in h
          and {"OPEN ROADMAP", "RECENT DAYS", "LEDGER TAILS quiet lines"} <= set(moved))
    print(("PASS  " if ok else "FAIL  ") + "split_for_cap: a tight cap moves in TAIL_ORDER, never the exchange or the day file (%s)" % moved)
    fails += not ok
    h, t, m = split_for_cap(sample, cap=cap)
    kept_lines = set(h.split("\n")) | set(t.split("\n"))
    ok = all(ln in kept_lines for ln in sample.split("\n"))
    print(("PASS  " if ok else "FAIL  ") + "split_for_cap: head + tail hold every line of the digest (nothing dropped)")
    fails += not ok
    h, t, m = split_for_cap(sample, cap=200)
    ok = "== THE LAST EXCHANGE" in h and "== WHERE WE LEFT OFF" in h and "PROPOSALS" in [x[0] for x in m]
    print(("PASS  " if ok else "FAIL  ") + "split_for_cap: an impossible cap still keeps the two never-cut blocks")
    fails += not ok
    tp = os.path.join(tmpd, "standup_tail.txt")
    ok = write_tail("== X\n  y", "clear", tp) and "== X" in open(tp, encoding="utf-8").read()
    print(("PASS  " if ok else "FAIL  ") + "write_tail: the parked sections land in the file with a dated header")
    fails += not ok

    print("session_start selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

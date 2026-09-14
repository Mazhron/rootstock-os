"""THE CORRECTION LEDGER (the CEO's ruling 2026-09-13: "Lets pretend I ask
you to do something. You build it, and it's wrong. I send you a correction
skill. You then inquire: What about the last thing I did needs correcting?
The user explains. You mark that down and prepare to fix the thing that
needs correcting, then you would ask 'What was the intent?'")

    python tools/correction_log.py --record --actor fable \\
        --shipped "<what was built, 3-10 words>" \\
        --wrong "<the CEO's words, verbatim>" \\
        [--intent-id I0007] [--intent-ref "<INTENT.md heading>"]
    python tools/correction_log.py --fixed C0003 --fix "<commit subject or note>"
    python tools/correction_log.py --last      # newest record
    python tools/correction_log.py --open      # corrections without a FIXED line

THE RECORD: docs/history/corrections.txt, append-only. A RECORD line is
written the moment the correction is understood (the CEO's words, not a
paraphrase); a FIXED line is appended when the fix ships. When the
correction names an intent claim (--intent-id), that claim is resolved
DIFFERENT with source=correction in the intent log by this script - a
correction IS the comparison's hardest evidence, so it never has to be
remembered separately. tools/intent_report.py counts corrections per
day/week/month next to the agreement rates; tools/ledger_trends.py
proposes a law or an INTENT.md entry when corrections cluster.

The /correct skill walks the ritual: ask what needs correcting -> record
-> ask "what was the intent?" -> the /intent skill files the why and
resolves the claim -> fix -> --fixed.

PURPOSE: Record the correction ledger: a RECORD line the moment a correction
  is understood in the CEO's own words, a FIXED line when the fix ships, and
  resolve the named intent claim as DIFFERENT in the intent log when one is
  given.
INTENT: the CEO's ruling 2026-09-13: Lets pretend I ask you to do something.
  You build it, and it's wrong. I send you a correction skill. You then
  inquire: What about the last thing I did needs correcting? The user
  explains. You mark that down and prepare to fix the thing that needs
  correcting, then you would ask What was the intent?

Search keys: correction, corrections ledger, mistake, wrong, fix record,
manager corrections, employee corrections, feedback loop.
See also: tools/intent_log.py; tools/intent_report.py; INTENT.md;
INTENT_METHOD.md (portable); SUBAGENTS.md (employee corrections are
tallied in its ledger; this file is the manager's and the cross-actor
record); WORKFLOWS.md "Correct a mistake".
"""
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "history", "corrections.txt")
HEADER = ("# THE CORRECTION LEDGER (append-only; a RECORD line when a correction is understood, "
          "a FIXED line when the fix ships). the CEO's words verbatim. Read the TAIL.\n"
          "# kind | id | date time | ws | actor | what shipped | what was wrong (verbatim) | "
          "intent id | INTENT.md ref | fix\n")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def lines():
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            return [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []


def parse(ln):
    p = [x.strip() for x in ln.split(" | ")]
    while len(p) < 10:
        p.append("")
    return dict(kind=p[0], id=p[1], when=p[2], ws=p[3], actor=p[4], shipped=p[5], wrong=p[6],
                intent_id=p[7], ref=p[8], fix=p[9])


def append(fields):
    new = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER)
        fh.write(" | ".join(fields) + "\n")


def records():
    return [parse(ln) for ln in lines()]


def next_id():
    ids = [int(r["id"][1:]) for r in records() if re.match(r"C\d+$", r["id"])]
    return "C%04d" % (max(ids or [0]) + 1)


def record(actor, shipped, wrong, intent_id="", ref=""):
    i = next_id()
    append(["RECORD", i, now(), workstation(), clean(actor), clean(shipped), clean(wrong),
            clean(intent_id), clean(ref), ""])
    print("%s recorded (%s): %s" % (i, actor, clean(shipped)))
    if intent_id:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "intent_log.py"),
                            "--resolve", intent_id, "--theirs", wrong, "--verdict", "different",
                            "--source", "correction"] + (["--intent-ref", ref] if ref else []),
                           cwd=ROOT, capture_output=True, text=True)
        print((r.stdout or r.stderr).strip())
    return i


def fixed(i, fix):
    known = {r["id"] for r in records()}
    if i not in known:
        sys.exit("no correction %s in %s" % (i, LEDGER))
    append(["FIXED", i, now(), workstation(), "", "", "", "", "", clean(fix)])
    print("%s fixed: %s" % (i, clean(fix)))


def open_ones():
    done = {r["id"] for r in records() if r["kind"] == "FIXED"}
    rows = [r for r in records() if r["kind"] == "RECORD" and r["id"] not in done]
    if not rows:
        print("no open corrections")
    for r in rows:
        print("  %s | %s | %s | %s | wrong: %s" % (r["id"], r["when"], r["actor"], r["shipped"],
                                                   r["wrong"][:80]))
    return rows


def _selftest():
    """Exercise the real record()/fixed() write path against a temp ledger
    (never the live docs/history/corrections.txt), with subprocess.run
    stubbed so no real intent claim is ever resolved. tempfile.mkdtemp() is
    left in place afterward - a selftest never deletes anything (THE
    PRESERVATION LAW)."""
    import tempfile
    global LEDGER
    tmp = tempfile.mkdtemp(prefix="everwood_correction_log_selftest_")
    orig_ledger = LEDGER
    orig_run = subprocess.run
    calls = []

    class _FakeResult:
        stdout = "stubbed: no real intent claim touched (selftest)"
        stderr = ""
        returncode = 0

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return _FakeResult()

    fails = 0
    try:
        LEDGER = os.path.join(tmp, "corrections.txt")
        subprocess.run = fake_run

        i1 = record("selftest-actor", "built a selftest widget",
                    "this is not what I meant", intent_id="I9999", ref="Some Heading")
        ok = os.path.isfile(LEDGER) and open(LEDGER, encoding="utf-8").read().startswith(HEADER)
        print(("PASS  " if ok else "FAIL  ") + "ledger created with its header when absent")
        fails += not ok

        ok = (len(calls) == 1 and calls[0][0] == sys.executable
              and "intent_log.py" in calls[0][1] and "--resolve" in calls[0])
        print(("PASS  " if ok else "FAIL  ") + "intent-log call stubbed - no real claim resolved")
        fails += not ok

        record("selftest-actor", "built another widget", "still not it")
        text = open(LEDGER, encoding="utf-8").read()
        ok = sum(1 for ln in text.splitlines() if ln.startswith("#")) == 2
        print(("PASS  " if ok else "FAIL  ") + "second write appends without repeating the header")
        fails += not ok

        data_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        ok = len(data_lines) == 2 and all(len(ln.split(" | ")) == 10 for ln in data_lines)
        print(("PASS  " if ok else "FAIL  ") + "line format matches the header's 10 columns")
        fails += not ok

        fixed(i1, "shipped the correct widget")
        ok = ("FIXED | %s" % i1) in open(LEDGER, encoding="utf-8").read()
        print(("PASS  " if ok else "FAIL  ") + "fixed() appends a FIXED line for a known id")
        fails += not ok

        # a pre-existing header-only ledger must not get a second header
        LEDGER = os.path.join(tmp, "preexisting_ledger.txt")
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write(HEADER)
        record("selftest-actor", "third widget", "still wrong")
        text3 = open(LEDGER, encoding="utf-8").read()
        ok = sum(1 for ln in text3.splitlines() if ln.startswith("#")) == 2
        print(("PASS  " if ok else "FAIL  ") + "pre-existing header-only ledger takes its first real append cleanly")
        fails += not ok
    finally:
        LEDGER = orig_ledger
        subprocess.run = orig_run

    print("correction_log selftest: %d failed (scratch dir left at %s, never cleaned up - THE PRESERVATION LAW)"
          % (fails, tmp))
    return 1 if fails else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    def opt(name, default=None):
        if name in argv:
            j = argv.index(name)
            return argv[j + 1] if j + 1 < len(argv) else default
        return default
    if "--record" in argv:
        shipped, wrong = opt("--shipped"), opt("--wrong")
        if not (shipped and wrong):
            sys.exit("--record needs --shipped and --wrong (the CEO's words verbatim)")
        record(opt("--actor", "fable"), shipped, wrong, opt("--intent-id", ""),
               opt("--intent-ref", ""))
        return 0
    if "--fixed" in argv:
        i, fix = opt("--fixed"), opt("--fix")
        if not (i and fix):
            sys.exit("--fixed <id> needs --fix")
        fixed(i, fix)
        return 0
    if "--open" in argv:
        open_ones()
        return 0
    if "--last" in argv:
        rs = [r for r in records() if r["kind"] == "RECORD"]
        print(("%s | %s | %s | %s" % (rs[-1]["id"], rs[-1]["actor"], rs[-1]["shipped"],
                                     rs[-1]["wrong"][:80])) if rs else "no corrections yet")
        return 0
    print(__doc__.split("\n\n")[1])
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

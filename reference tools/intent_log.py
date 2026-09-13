"""THE INTENT LOG (the CEO's ruling 2026-09-13: "When you or an agent has a
concept, your own intent, there should be a record of that to compare vs my
intent. Then, there needs to be a comparison of how many times your
intention or that of a subagent was the same, similar, or different than
mine.")

    python tools/intent_log.py --claim --actor fable --task "<3-8 words>" \\
        --mine "<what I understood the ask to be, before building>"
    python tools/intent_log.py --resolve I0007 --theirs "<the CEO's intent>" \\
        --verdict same|similar|different --source stated|correction|inferred \\
        [--intent-ref "<INTENT.md heading>"]
    python tools/intent_log.py --pending        # open claims
    python tools/intent_log.py --last           # newest id + line

THE RECORD: one line per claim in docs/history/intent_log.txt (append-only;
a resolve appends a RESOLVED line that supersedes the claim's PENDING
state - nothing is edited in place). A CLAIM is written BEFORE building:
the manager's (or an employee's, relayed by the manager) own reading of
what was asked. The RESOLVE lands when the truth is known: the CEO stated
or confirmed it (stated), a /correct revealed it (correction), or the
manager judged from the outcome with no explicit words (inferred - kept
honest by naming it). The verdict is the comparison:
  SAME       the reading matched; nothing was rebuilt or adjusted
  SIMILAR    matched in substance; a detail differed and was adjusted
             without a rebuild
  DIFFERENT  a correction or rebuild was needed
tools/intent_report.py turns the log into day/week/month agreement rates
(txt for us, csv + xlsx for a human) and says improving / steady /
declining; tools/ledger_trends.py proposes when the trend declines or
claims sit pending. tools/correction_log.py resolves a claim as DIFFERENT
by itself when a correction names it.

GOTCHA (2026-09-13, first day): under Git Bash / MSYS an argument that STARTS
with a slash ("/intent") is rewritten into a Windows path before Python
sees it. Run these commands from PowerShell, or start the text with a
word ("the /intent skill"), or set MSYS_NO_PATHCONV=1.

Why a log and not memory: real data, past vs present, and a trend that
says whether the feedback loop works (INTENT.md "Intent tracking").

PURPOSE: Log an intent claim before building and resolve it against
  the CEO's actual intent as same, similar or different, append-only, one
  line per claim and one per resolution.
INTENT: the CEO's ruling 2026-09-13: When you or an agent has a concept,
  your own intent, there should be a record of that to compare vs my intent.
  Then, there needs to be a comparison of how many times your intention or
  that of a subagent was the same, similar, or different than mine.

Search keys: intent log, intent claim, same similar different, agreement,
mazhron intent, manager intent, employee intent, feedback loop.
See also: INTENT.md (the why of every ruling); tools/intent_report.py;
tools/correction_log.py; INTENT_METHOD.md (portable); WORKFLOWS.md
"Record an intent" and "Correct a mistake"; docs/systems/tooling.md
"The intent loop".
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "docs", "history", "intent_log.txt")
VERDICTS = ("SAME", "SIMILAR", "DIFFERENT")
SOURCES = ("stated", "correction", "inferred")
HEADER = ("# THE INTENT LOG (append-only; a CLAIM line before building, a RESOLVED line when "
          "the CEO's intent is known - the newest line for an id wins). Read the TAIL.\n"
          "# kind | id | date time | ws | actor | task | claude intent | mazhron intent | "
          "verdict | source | INTENT.md ref\n")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def lines():
    try:
        with open(LOG, encoding="utf-8") as fh:
            return [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []


def parse(ln):
    p = [x.strip() for x in ln.split(" | ")]
    while len(p) < 11:
        p.append("")
    return dict(kind=p[0], id=p[1], when=p[2], ws=p[3], actor=p[4], task=p[5], mine=p[6],
                theirs=p[7], verdict=p[8], source=p[9], ref=p[10])


def state():
    """id -> the newest record for that id (a RESOLVED line supersedes its CLAIM)."""
    st = {}
    order = []
    for ln in lines():
        r = parse(ln)
        if r["id"] not in st:
            order.append(r["id"])
        base = st.get(r["id"], {})
        merged = dict(base)
        for k, v in r.items():
            if v or k not in merged:
                merged[k] = v
        st[r["id"]] = merged
    return st, order


def append(fields):
    new = not os.path.isfile(LOG)
    with open(LOG, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER)
        fh.write(" | ".join(fields) + "\n")


def next_id():
    st, order = state()
    n = max([int(i[1:]) for i in order if re.match(r"I\d+$", i)] or [0]) + 1
    return "I%04d" % n


def claim(actor, task, mine):
    i = next_id()
    append(["CLAIM", i, now(), workstation(), clean(actor), clean(task), clean(mine), "",
            "PENDING", "", ""])
    print("%s claimed (%s): %s" % (i, actor, clean(task)))
    return i


def resolve(i, theirs, verdict, source, ref=""):
    st, _ = state()
    if i not in st:
        sys.exit("no claim %s in %s" % (i, LOG))
    verdict = verdict.upper()
    if verdict not in VERDICTS:
        sys.exit("verdict must be one of %s" % (VERDICTS,))
    if source not in SOURCES:
        sys.exit("source must be one of %s" % (SOURCES,))
    r = st[i]
    if r["verdict"] != "PENDING":
        print("note: %s was already %s (%s) - appending a newer resolution, the newest wins"
              % (i, r["verdict"], r["source"]))
    append(["RESOLVED", i, now(), workstation(), r["actor"], r["task"], r["mine"],
            clean(theirs), verdict, source, clean(ref)])
    print("%s resolved %s (%s): mine=%r theirs=%r" % (i, verdict, source, r["mine"][:60],
                                                     clean(theirs)[:60]))


def pending():
    st, order = state()
    rows = [st[i] for i in order if st[i]["verdict"] == "PENDING"]
    if not rows:
        print("no pending intent claims")
    for r in rows:
        print("  %s | %s | %s | %s | mine: %s" % (r["id"], r["when"], r["actor"], r["task"],
                                                  r["mine"][:80]))
    return rows


def main(argv):
    def opt(name, default=None):
        if name in argv:
            j = argv.index(name)
            return argv[j + 1] if j + 1 < len(argv) else default
        return default
    if "--claim" in argv:
        task, mine = opt("--task"), opt("--mine")
        if not (task and mine):
            sys.exit("--claim needs --task and --mine")
        claim(opt("--actor", "fable"), task, mine)
        return 0
    if "--resolve" in argv:
        i = opt("--resolve")
        theirs, verdict, source = opt("--theirs"), opt("--verdict"), opt("--source")
        if not (i and theirs and verdict and source):
            sys.exit("--resolve <id> needs --theirs, --verdict and --source")
        resolve(i, theirs, verdict, source, opt("--intent-ref", ""))
        return 0
    if "--pending" in argv:
        pending()
        return 0
    if "--last" in argv:
        st, order = state()
        if order:
            r = st[order[-1]]
            print("%s | %s | %s | %s | %s" % (r["id"], r["verdict"], r["actor"], r["task"],
                                             r["mine"][:80]))
        else:
            print("no claims yet")
        return 0
    print(__doc__.split("\n\n")[1])
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

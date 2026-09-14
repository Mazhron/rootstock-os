"""THE OPEN QUESTIONS LOG (the CEO's ruling 2026-09-14: "Do it, open_questions
ledger with a nudge past N days").

Some questions only the owner can answer - a design ruling, a playtest
judgment call, a pillar-level tradeoff. Rather than let one sit inside a
CLAUDE.md cross-workstation note until someone remembers it, it goes here:
one line per question, append-only, visible in every standup, and nudged
by tools/ledger_trends.py (rule 11) once it has waited past
open_question_days (default 7, tunable in .claude/trend_limits.json).

Usage:
  python tools/open_questions.py --add "<question text>" [--raised YYYY-MM-DD]
  python tools/open_questions.py --resolve Q0001 --answer "<owner's words>"
  python tools/open_questions.py --open      # oldest first, with age in days
  python tools/open_questions.py --last

THE RECORD: one line per event in docs/history/open_questions.txt
(append-only; a resolution is a new RESOLVED line for the same id, never
an edit to the RAISED line - the newest line per id wins, same shape as
tools/intent_log.py).

PURPOSE: Log a question only the owner can answer, list the open ones with
  their age, and record the resolution in the owner's own words when it
  lands, append-only.
INTENT: the CEO's ruling 2026-09-14: open questions to the owner get a
  ledger, and standup nudges once one has waited past N days.

Search keys: open questions, ask mazhron, owner decision, design ruling,
pillar question, nudge, waiting on the owner.
See also: tools/ledger_trends.py rule 11 (the nudge); tools/standup.py
(the OPEN QUESTIONS TO MAZHRON block); WORKFLOWS.md "Track an open
question to the CEO"; tools/intent_log.py (the sibling ledger this one
copies its shape from); CLAUDE.md "Cross-workstation notes".
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "docs", "history", "open_questions.txt")
STATUSES = ("OPEN", "RESOLVED")
HEADER = ("# OPEN QUESTIONS TO THE OWNER (append-only; a resolution is a new line, never "
          "an edit): id | date raised | ws | status | date resolved | question | answer\n")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()


def today():
    return datetime.date.today().isoformat()


def lines():
    try:
        with open(LOG, encoding="utf-8") as fh:
            return [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []


def parse(ln):
    p = [x.strip() for x in ln.split(" | ")]
    while len(p) < 7:
        p.append("")
    return dict(id=p[0], raised=p[1], ws=p[2], status=p[3], resolved=p[4], question=p[5],
                answer=p[6])


def state():
    """id -> the newest record for that id (a RESOLVED line supersedes RAISED)."""
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
        merged["status"] = r["status"] or merged.get("status", "OPEN")
        st[r["id"]] = merged
    return st, order


def append(fields):
    new = not os.path.isfile(LOG)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER)
        fh.write(" | ".join(fields) + "\n")


def next_id():
    st, order = state()
    n = max([int(i[1:]) for i in order if re.match(r"Q\d+$", i)] or [0]) + 1
    return "Q%04d" % n


def add(question, raised=None):
    i = next_id()
    append([i, raised or today(), workstation(), "OPEN", "", clean(question), ""])
    print("%s raised: %s" % (i, clean(question)))
    return i


def resolve(i, answer):
    st, _ = state()
    if i not in st:
        sys.exit("no question %s in %s" % (i, LOG))
    r = st[i]
    if r["status"] == "RESOLVED":
        print("note: %s was already resolved - appending a newer resolution, the newest wins" % i)
    append([i, r["raised"], r["ws"], "RESOLVED", today(), r["question"], clean(answer)])
    print("%s resolved: %s" % (i, clean(answer)[:80]))


def open_rows():
    st, order = state()
    rows = [st[i] for i in order if st[i]["status"] == "OPEN"]
    ages = []
    for r in rows:
        try:
            d = datetime.date.fromisoformat(r["raised"])
            age = (datetime.date.today() - d).days
        except ValueError:
            age = -1
        ages.append((age, r))
    ages.sort(key=lambda t: -t[0])
    return ages


def print_open():
    ages = open_rows()
    if not ages:
        print("no open questions")
        return ages
    for age, r in ages:
        print("  %s | %sd | %s" % (r["id"], age if age >= 0 else "?", r["question"]))
    return ages


def main(argv):
    def opt(name, default=None):
        if name in argv:
            j = argv.index(name)
            return argv[j + 1] if j + 1 < len(argv) else default
        return default
    if "--add" in argv:
        q = opt("--add")
        if not q:
            sys.exit("--add needs a question string")
        add(q, opt("--raised"))
        return 0
    if "--resolve" in argv:
        i = opt("--resolve")
        answer = opt("--answer")
        if not (i and answer):
            sys.exit("--resolve <id> needs --answer")
        resolve(i, answer)
        return 0
    if "--open" in argv:
        print_open()
        return 0
    if "--last" in argv:
        st, order = state()
        if order:
            r = st[order[-1]]
            print("%s | %s | %s | %s" % (r["id"], r["status"], r["question"], r["answer"]))
        else:
            print("no questions yet")
        return 0
    print(__doc__.split("\n\n")[1])
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

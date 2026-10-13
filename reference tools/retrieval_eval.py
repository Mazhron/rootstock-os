"""THE RETRIEVAL EVALUATION (the CEO 2026-10-13: "Build the retrieval
evaluation as a loop", after an AI-engineering post asked whether a system
can "build a representative query dataset for that domain and measure if
that system actually works").

The lesson loop's prompt end (tools/lesson_log.py match) is a retrieval
system: a prompt's words against every LESSONS.md entry's Keys line, scored,
filtered, capped. Until now the ledger said only WHICH entries fired
(MATCHED), never whether the RIGHT one did. This script measures that from
two sides:

  THE QUERY SET (tools/retrieval_queries.txt): hand-written prompts in the
  owner's voice, each naming the entry it should surface (a heading
  fragment). hit = the entry is among the matcher's picks. A miss is a weak
  Keys line; the fix is the Keys line, never the matcher.

  THE REPLAY (the project's own transcripts, newest N typed prompts): every
  prompt is re-matched, and the turn after it is scanned with
  lesson_log.signals() for trial and error. Four cells:
    named, clean        a lesson fired and the turn went straight
    named, trial        a lesson fired and the turn still fumbled (the
                        wrong entry, or it was not read)
    silent, trial       nothing fired and the turn fumbled - the recall
                        gap: a lesson that does not exist, or whose Keys
                        never hit this prompt's words
    silent, clean       nothing to retrieve, nothing went wrong
  plus the fire rate per entry: an entry that fires on more than NOISY_PCT
  of eligible prompts is noise (its Keys are too generic) - the precision
  side.

Usage:
    python tools/retrieval_eval.py                 # report + ledger line (run_all metrics)
    python tools/retrieval_eval.py -n 300          # a wider replay window (default 200)
    python tools/retrieval_eval.py --queries-only  # the query set alone, no transcripts
    python tools/retrieval_eval.py --selftest

THE LEDGER: docs/history/retrieval_eval_runs.txt, one line per run through
tools/_ledger.py (trust the ledger): prompts | eligible | named | silent-trial
| named-trial | noisy | queries | hit | miss | PASS or WARN. The detail (which
query missed, what fired instead, the silent-trial prompts, the noisy
entries) is rewritten to docs/history/retrieval_eval.txt. tools/ledger_trends.py
rule 16 proposes a [DO] on a miss or a noisy entry.

PURPOSE: Measure the lesson matcher's recall and precision against a
  hand-written query set and against the project's own replayed prompts;
  print the report, rewrite docs/history/retrieval_eval.txt and append one
  ledger line (the append goes through tools/_ledger.py, which also updates
  its sidecar docs/history/ledger_heads.txt). Reads LESSONS.md, the query
  file and this project's transcripts (every ~/.claude/projects folder whose
  name carries the repo name, top level only); writes nothing else.
INTENT: the CEO 2026-10-13: the one gap the industry's RAG checklist named
  that Rootstock actually had was an evaluation set - we logged what fired,
  never whether the right thing fired; a weak Keys line should be found by a
  script, not by a session that repeats the trial and error.

Search keys: retrieval evaluation, retrieval eval, query set, query dataset,
hit miss, recall, precision, noisy keys, silent trial, lesson matcher
measured, RAG evaluation, does the right lesson fire, retrieval_queries.
See also: tools/lesson_log.py (the matcher and the signals); LESSONS.md
(the Keys lines being measured); tools/ledger_trends.py (rule 16);
tools/run_all.py (metrics group); docs/systems/self-audit.md ("Rootstock in
the industry's words"); WORKFLOWS.md "Evaluate the lesson retrieval".
"""
import datetime
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import lesson_log as _ll  # noqa: E402
from _ledger import append_unless_identical  # noqa: E402

QUERIES = os.path.join(ROOT, "tools", "retrieval_queries.txt")
LEDGER = os.path.join(ROOT, "docs", "history", "retrieval_eval_runs.txt")
REPORT = os.path.join(ROOT, "docs", "history", "retrieval_eval.txt")
WINDOW = 200          # typed prompts replayed, newest first
NOISY_PCT = 25        # an entry firing on more than this share of eligible prompts is noise
WRAPPERS = ("<command-", "<local-command", "<system-reminder", "<task-notification",
            "[Image:", "[Request interrupted", "Base directory for this skill",
            "Another Claude session sent a message", "Stop hook feedback", "Caveat: the messages")


# ------------------------------------------------------------ queries --
def queries(path=QUERIES):
    """[(expected heading fragment, prompt)] from the query file; `#` comments,
    one `fragment || prompt` per line."""
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                ln = raw.strip()
                if not ln or ln.startswith("#") or "||" not in ln:
                    continue
                frag, prompt = ln.split("||", 1)
                out.append((frag.strip(), prompt.strip()))
    except OSError:
        pass
    return out


def run_queries(qs, ents):
    """(hits, misses) - misses as (fragment, prompt, [headings that fired])."""
    hits, misses = 0, []
    for frag, prompt in qs:
        fired = [e["heading"] for _, e in _ll.match(prompt, ents)]
        if any(frag.lower() in h.lower() for h in fired):
            hits += 1
        else:
            misses.append((frag, prompt, fired))
    return hits, misses


# ------------------------------------------------------------- replay --
def _slug(path):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path)).lower()


def sessions():
    """This project's top-level transcripts, newest first (employee sessions
    live under <session>/subagents/ and are not walked: their prompts are
    briefs, not the owner's)."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(base):
        return []
    wanted = {_slug(ROOT), _slug(os.path.dirname(ROOT))}
    repo = re.sub(r"[^A-Za-z0-9]", "-", os.path.basename(ROOT)).lower()
    files = []
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and (d.lower() in wanted or repo in d.lower()):
            files += glob.glob(os.path.join(full, "*.jsonl"))
    return sorted(files, key=os.path.getmtime, reverse=True)


def _text(rec):
    return "\n".join(b.get("text", "") for b in _ll._blocks(rec)).strip()


def is_wrapper(text):
    return text.lstrip().startswith(WRAPPERS)


def turns(files, n=WINDOW):
    """[(prompt text, the records of its turn)] for the newest n typed
    prompts, oldest first; harness wrappers (a /clear, a task notification)
    are not prompts."""
    out = []
    for path in files:
        recs, _ = _ll._records(path)
        idx = _ll.user_text_indexes(recs)
        got = []
        for k, i in enumerate(idx):
            text = _text(recs[i])
            if not text or is_wrapper(text):
                continue
            end = idx[k + 1] if k + 1 < len(idx) else len(recs)
            got.append((text, recs[i:end]))
        out = got + out
        if len(out) >= n:
            break
    return out[-n:]


def evaluate(items, ents, sig_fn=None):
    """The four cells, the fire counts and the lists the report prints."""
    sig_fn = sig_fn or _ll.signals
    cells = {"named_clean": 0, "named_trial": 0, "silent_trial": 0, "silent_clean": 0}
    fires = {}
    eligible = 0
    silent_trial, named_trial = [], []
    for text, slice_ in items:
        if len(_ll.words(text)) < _ll.MIN_PROMPT_WORDS:
            continue  # a prompt the matcher never reads ("standup", "yes") is outside the cells
        eligible += 1
        hits = [e["heading"] for _, e in _ll.match(text, ents)]
        for h in hits:
            fires[h] = fires.get(h, 0) + 1
        sig = sig_fn(slice_)
        key = ("named" if hits else "silent") + ("_trial" if sig else "_clean")
        cells[key] += 1
        if key == "silent_trial":
            silent_trial.append((text, sig))
        elif key == "named_trial":
            named_trial.append((text, hits, sig))
    noisy = []
    if eligible:
        for h, c in sorted(fires.items(), key=lambda t: -t[1]):
            pct = 100.0 * c / eligible
            if pct > NOISY_PCT:
                noisy.append((h, c, pct))
    return {"cells": cells, "fires": fires, "eligible": eligible, "noisy": noisy,
            "silent_trial": silent_trial, "named_trial": named_trial, "n": len(items)}


# ------------------------------------------------------------- report --
def _short(text, n=90):
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= n else t[:n - 3] + "..."


def report_lines(ev, qs, hits, misses):
    c = ev["cells"]
    out = ["THE RETRIEVAL EVALUATION - %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "",
           "THE QUERY SET: %d quer%s, %d hit, %d miss" % (len(qs), "y" if len(qs) == 1 else "ies",
                                                         hits, len(misses))]
    for frag, prompt, fired in misses:
        out.append("  MISS \"%s\" <- %s" % (frag, _short(prompt)))
        out.append("       fired: %s" % ("; ".join(_short(h, 60) for h in fired) or "nothing"))
    out += ["",
            "THE REPLAY: %d prompt(s), %d eligible (%d+ content words)" % (ev["n"], ev["eligible"],
                                                                           _ll.MIN_PROMPT_WORDS),
            "  named, clean   %d" % c["named_clean"],
            "  named, trial   %d   (a lesson fired, the turn still fumbled)" % c["named_trial"],
            "  silent, trial  %d   (THE RECALL GAP: nothing fired, the turn fumbled)" % c["silent_trial"],
            "  silent, clean  %d" % c["silent_clean"]]
    if ev["silent_trial"]:
        out.append("  silent-trial prompts (a lesson missing, or Keys that never hit these words):")
        for text, sig in ev["silent_trial"][-12:]:
            out.append("    - %s  [%s]" % (_short(text), "; ".join(sig)[:80]))
    if ev["named_trial"]:
        out.append("  named-trial prompts (the wrong entry, or not read):")
        for text, hits_, sig in ev["named_trial"][-8:]:
            out.append("    - %s  -> %s" % (_short(text, 70), "; ".join(_short(h, 50) for h in hits_)))
    out.append("")
    out.append("FIRE RATES (over eligible prompts; noise above %d%%):" % NOISY_PCT)
    for h, cnt in sorted(ev["fires"].items(), key=lambda t: -t[1])[:12]:
        pct = 100.0 * cnt / ev["eligible"] if ev["eligible"] else 0
        out.append("  %3d  %5.1f%%  %s%s" % (cnt, pct, _short(h, 80), "  NOISY" if pct > NOISY_PCT else ""))
    if not ev["fires"]:
        out.append("  (nothing fired in the window)")
    return out


def ledger_line(ev, qs, hits, misses):
    c = ev["cells"]
    verdict = "PASS" if not misses and not ev["noisy"] else "WARN"
    return ("%s | %s | prompts %d | eligible %d | named %d | silent-trial %d | named-trial %d | "
            "noisy %d | queries %d | hit %d | miss %d | %s"
            % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), _ll.workstation(),
               ev["n"], ev["eligible"], c["named_clean"] + c["named_trial"], c["silent_trial"],
               c["named_trial"], len(ev["noisy"]), len(qs), hits, len(misses), verdict))


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    n = WINDOW
    if "-n" in argv:
        n = int(argv[argv.index("-n") + 1])
    ents = _ll.entries()
    qs = queries()
    hits, misses = run_queries(qs, ents)
    items = [] if "--queries-only" in argv else turns(sessions(), n)
    ev = evaluate(items, ents)
    lines = report_lines(ev, qs, hits, misses)
    print("\n".join(lines))
    if "--queries-only" in argv:
        return 1 if misses else 0
    line = ledger_line(ev, qs, hits, misses)
    try:
        os.makedirs(os.path.dirname(REPORT), exist_ok=True)
        with open(REPORT, "w", encoding="utf-8") as fh:
            fh.write("# THE RETRIEVAL EVALUATION detail (rewritten each run by tools/retrieval_eval.py; "
                     "the ledger is retrieval_eval_runs.txt)\n")
            fh.write("\n".join(lines) + "\n")
        fresh = not os.path.isfile(LEDGER)
        if fresh:
            with open(LEDGER, "w", encoding="utf-8") as fh:
                fh.write("# THE RETRIEVAL EVALUATION (append-only): date time | ws | prompts | eligible | "
                         "named | silent-trial | named-trial | noisy | queries | hit | miss | verdict. "
                         "Detail in retrieval_eval.txt; rule 16 of ledger_trends proposes on a miss or a "
                         "noisy entry.\n")
        append_unless_identical(LEDGER, line)
    except OSError as exc:
        print("ledger write failed: %s" % exc)
    print("\n" + line)
    return 0


# ----------------------------------------------------------- selftest --
_BOOK = """## Write a long file through the shell (heredocs)
Tags: lessons | brief
Keys: heredoc, long file, write tool, bash script
THE ONE RIGHT WAY: use the Write tool.
See also: x

## Brief a numbers task (an envelope)
Tags: lessons | brief
Keys: brief, retune, prices, numbers task
THE ONE RIGHT WAY: an envelope.
See also: x
"""


def _selftest():
    ok_all = True

    def check(ok, msg):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(("PASS  " if ok else "FAIL  ") + msg)

    ents = _ll.entries(_BOOK)
    qs = [("heredocs", "write the whole patch script as a bash heredoc please"),
          ("envelope", "brief haiku to retune the wetland rite prices for me"),
          ("envelope", "what is the weather today in the forest")]
    hits, misses = run_queries(qs, ents)
    check(hits == 2 and len(misses) == 1 and misses[0][0] == "envelope",
          "query set: two hits, the off-topic prompt is the one miss")
    items = [("write the whole patch script as a bash heredoc please", ["t1"]),
             ("brief haiku to retune the wetland rite prices for me", ["t2"]),
             ("the weather over the dark forest looks cloudy and cold tonight", ["t3"]),
             ("ok", ["t4"]),
             ("a long file through a heredoc again, the same script", ["t5"])]
    sig = lambda s: ["same command again after an error"] if s in (["t1"], ["t3"]) else []  # noqa: E731
    ev = evaluate(items, ents, sig_fn=sig)
    c = ev["cells"]
    check(c == {"named_clean": 2, "named_trial": 1, "silent_trial": 1, "silent_clean": 0},
          "replay: the four cells filled as planned (%s)" % c)
    check(ev["eligible"] == 4 and sum(c.values()) == 4,
          "replay: the two-letter prompt is outside the cells (%d eligible)" % ev["eligible"])
    check(len(ev["noisy"]) == 1 and ev["noisy"][0][0].startswith("Write a long file"),
          "fire rate: the entry on 2 of 4 eligible prompts (50%%) is the one flagged noisy above %d%%; "
          "the one on 1 of 4 (25%%) is not" % NOISY_PCT)
    check(is_wrapper("<command-name>/clear</command-name>") and is_wrapper("[Image: source: x.png]")
          and is_wrapper("Base directory for this skill: c:/x") and not is_wrapper("pasted <x> text"),
          "wrappers: a /clear, an image drop and a skill body are skipped, a prompt containing < is kept")
    line = ledger_line(ev, qs, hits, misses)
    check("| miss 1 | WARN" in line and "| noisy 1 |" in line, "ledger line carries miss, noisy and WARN")
    lines = report_lines(ev, qs, hits, misses)
    check(any(ln.startswith("  MISS \"envelope\"") for ln in lines) and any("NOISY" in ln for ln in lines),
          "report names the miss and the noisy entry")
    print("retrieval_eval selftest: %s" % ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

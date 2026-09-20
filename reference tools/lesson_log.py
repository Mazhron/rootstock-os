"""THE LESSON LOOP (the CEO's ask 2026-09-20, "something to push you to
write what you learned ... so you don't waste time and tokens repeating
trial and error before getting it right").

Both ends of the loop live here. The prompt end: match a prompt's words
against LESSONS.md's per-entry Keys lines and name the entries to read
before the first tool call. The stop end: scan the turn's transcript slice
for trial-and-error signals (the same command run again after an error,
repeated edit misses, a FAIL followed by a PASS, an intent claim resolved
DIFFERENT, an employee briefed twice, a prompt that reads as a correction)
so the Stop hook can say LESSON ADVISED. The check end: lint every entry's
shape and ledger the counts so the loop is measured.

Usage:
    python tools/lesson_log.py --match "<prompt text>"   # what the prompt hook would say
    python tools/lesson_log.py --scan [transcript.jsonl] # signals in the newest turn slice
    python tools/lesson_log.py --check                   # lint LESSONS.md + ledger line (run_all check)
    python tools/lesson_log.py --selftest

THE LEDGER: docs/history/lesson_runs.txt, append-only, one line per event:
date time | ws | kind | detail. Kinds: MATCHED (the prompt hook named
entries), ADVISED (the Stop hook asked for a lesson), WRITTEN (LESSONS.md
was edited inside an advised turn), CHECK (the lint's counts). The CHECK
line goes through tools/_ledger.py so an unchanged rerun does not grow it.

PURPOSE: Serve the lesson loop's three ends: match a prompt against the
  Keys lines of LESSONS.md entries and name the ones to read first; scan a
  transcript slice for trial-and-error signals so the Stop hook can advise
  a lesson; lint the entries' shape and ledger the counts for the check loop.
INTENT: the CEO 2026-09-20: a lesson is written the moment it is learned
  and met again before the next attempt at the same task shape, so the one
  right way runs first and trial and error is not paid for twice.

Search keys: lesson loop, lesson log, lesson advised, one right way, prompt
match, trial and error signals, lessons ledger, knowledge capture.
See also: LESSONS.md (the book + the law); tools/hooks/lesson_advisor.py
(the Stop twin); tools/hooks/prompt_gauge.py (the match line);
tools/_ledger.py (trust the ledger for the CHECK line); tools/run_all.py
(check group); tools/ledger_trends.py (rule 14).
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "LESSONS.md")
LEDGER = os.path.join(ROOT, "docs", "history", "lesson_runs.txt")
MATCH_CAP = 3            # entries named per prompt, at most
MIN_SCORE = 2            # one multi-word key, or two single-word keys
MIN_PROMPT_WORDS = 4     # shorter prompts (a slash command, "yes") are not matched

STOP = set("""a an the and or of to in on for with is are was were be been it its this
that these those you your i my me we our they them their he she his her do does did
done not no yes can could should would will just also then than so if as at by from
into over under up down out about after before again please let now new old one two
all any some more most very what which who how when where why there here have has had
make made get got go went use used using want need like same other onto each
""".split())


# ------------------------------------------------------------ words --
def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def words(text):
    """Lowercase alnum tokens, stopwords dropped, crude stem (plural/-ing/-ed)."""
    out = []
    for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if w in STOP or len(w) < 2:
            continue
        out.append(stem(w))
    return out


# ---------------------------------------------------------- entries --
def entries(text=None):
    """[{heading, line, keys[], brief, body}] for every `## ` entry of the book."""
    if text is None:
        try:
            with open(BOOK, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return []
    out = []
    cur = None
    for i, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("## "):
            cur = {"heading": raw[3:].strip(), "line": i, "keys": [], "brief": "", "body": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        cur["body"].append(raw)
        m = re.match(r"Keys:\s*(.+)", raw)
        if m:
            cur["keys"] = [k.strip() for k in m.group(1).split(",") if k.strip()]
        m = re.match(r"Tags:\s*[^|]*\|\s*(.+)", raw)
        if m:
            cur["brief"] = m.group(1).strip()
    return out


def match(prompt, ents=None):
    """[(score, entry)] for entries whose Keys hit the prompt, best first."""
    ws = words(prompt)
    if len(ws) < MIN_PROMPT_WORDS:
        return []
    have = set(ws)
    hits = []
    for e in (entries() if ents is None else ents):
        score = 0
        for key in e["keys"]:
            kw = words(key)
            if kw and all(w in have for w in kw):
                score += 2 if len(kw) > 1 else 1
        if score >= MIN_SCORE:
            hits.append((score, e))
    hits.sort(key=lambda t: (-t[0], t[1]["line"]))
    return hits[:MATCH_CAP]


def match_lines(prompt, ents=None):
    """The lines the prompt hook prints (empty on a normal prompt)."""
    hits = match(prompt, ents)
    if not hits:
        return []
    out = ["LESSONS: %d matching entr%s - read before the first tool call (THE LESSON LAW):"
           % (len(hits), "y" if len(hits) == 1 else "ies")]
    for _, e in hits:
        out.append("  LESSONS.md line %d \"%s\"%s" % (e["line"], e["heading"],
                                                     (" - " + e["brief"]) if e["brief"] else ""))
    return out


# ------------------------------------------------------------- lint --
REQUIRED = ("Tags:", "Keys:", "THE ONE RIGHT WAY", "See also:")


def lint(text=None):
    """['heading: what is missing', ...]; empty when every entry has its shape."""
    probs = []
    for e in entries(text):
        body = "\n".join(e["body"])
        missing = [r for r in REQUIRED if r not in body]
        if not e["keys"] and "Keys:" not in missing:
            missing.append("Keys: (empty)")
        if missing:
            probs.append("%s: missing %s" % (e["heading"], ", ".join(missing)))
    return probs


# -------------------------------------------------------- transcript --
def _records(path, start=0):
    """Parsed JSON records of a transcript from line `start`, with the total
    line count, so a caller can store a pointer for the next slice."""
    recs = []
    n = 0
    try:
        with open(path, encoding="utf-8") as fh:
            for n, raw in enumerate(fh, 1):
                if n <= start:
                    continue
                try:
                    recs.append(json.loads(raw))
                except ValueError:
                    continue
    except OSError:
        return [], 0
    return recs, n


def _blocks(rec):
    m = rec.get("message") or {}
    c = m.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return [b for b in (c or []) if isinstance(b, dict)]


def _result_text(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in (c or []) if isinstance(b, dict))


def user_text_indexes(recs):
    """Indexes of records that are a person's typed message (not a tool result)."""
    out = []
    for i, r in enumerate(recs):
        if r.get("type") != "user" or r.get("isSidechain"):
            continue
        bl = _blocks(r)
        if bl and all(b.get("type") == "text" for b in bl):
            out.append(i)
    return out


CORRECTION_RE = re.compile(
    r"(that'?s wrong|that is wrong|not what i (meant|asked|wanted)|you misread|you misunderstood|"
    r"^\s*correction\b|/correct\b|wrong (file|number|value|species|thing))", re.I)
ERROR_RE = re.compile(r"(traceback|error:|\bFAIL\b|not found|no such file|command not found|"
                      r"is not recognized|refused|denied|exit code [1-9])", re.I)
BOOK_NAME = os.path.basename(BOOK).lower()
# intent_log.py --resolve prints "I0048 resolved different (stated): ..."; only that
# line counts (a digest or day file QUOTING a past DIFFERENT is not this turn's).
DIFFERENT_RE = re.compile(r"\bI\d{4} resolved different \(", re.I)


def signals(recs):
    """[signal line, ...] found in a slice of transcript records."""
    cmds = {}          # normalized command -> [was_error, ...] in order
    edit_misses = 0
    fail_at = None
    pass_after_fail = False
    different = False
    agent_descs = []
    corrections = 0
    book_written = False
    result_of = {}     # tool_use id -> (name, command)
    order = 0
    for r in recs:
        for b in _blocks(r):
            t = b.get("type")
            if t == "tool_use":
                name = b.get("name") or ""
                inp = b.get("input") or {}
                if name in ("Bash", "PowerShell"):
                    cmd = re.sub(r"\s+", " ", (inp.get("command") or "").strip())
                    result_of[b.get("id")] = (name, cmd)
                    cmds.setdefault(cmd, [])
                elif name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                    result_of[b.get("id")] = (name, "")
                    if BOOK_NAME in (inp.get("file_path") or "").lower():
                        book_written = True
                elif name in ("Agent", "Task"):
                    d = (inp.get("description") or inp.get("prompt") or "")[:60].strip().lower()
                    if d:
                        agent_descs.append(d)
            elif t == "tool_result":
                order += 1
                txt = _result_text(b)
                err = bool(b.get("is_error")) or bool(ERROR_RE.search(txt[:4000]))
                name, cmd = result_of.get(b.get("tool_use_id"), ("", ""))
                if name in ("Bash", "PowerShell"):
                    cmds.setdefault(cmd, []).append(err)
                elif name in ("Edit", "Write", "MultiEdit", "NotebookEdit") and b.get("is_error"):
                    edit_misses += 1
                if re.search(r"\bFAIL\b", txt) and fail_at is None:
                    fail_at = order
                elif fail_at is not None and order > fail_at and re.search(r"\bPASS\b", txt) \
                        and not re.search(r"\bFAIL\b", txt):
                    pass_after_fail = True
                if DIFFERENT_RE.search(txt):
                    different = True
            elif t == "text" and r.get("type") == "user" and not r.get("isSidechain"):
                if CORRECTION_RE.search(b.get("text") or ""):
                    corrections += 1
    out = []
    for cmd, errs in cmds.items():
        if len(errs) >= 2 and errs[0] and cmd:
            out.append("the same command ran %d times after an error: %s"
                       % (len(errs), cmd[:70] + ("..." if len(cmd) > 70 else "")))
    if edit_misses >= 2:
        out.append("%d edit calls missed their target" % edit_misses)
    if pass_after_fail:
        out.append("a FAIL was followed by a PASS (something was fixed by trying)")
    if different:
        out.append("an intent claim resolved DIFFERENT")
    seen = set()
    for d in agent_descs:
        if d in seen:
            out.append("an employee was briefed twice on the same task: %s" % d[:50])
            break
        seen.add(d)
    if corrections:
        out.append("%d prompt(s) this turn read as a correction" % corrections)
    if book_written:
        out.append("WRITTEN: LESSONS.md was edited this turn")
    return out


def scan(path, start=0):
    """(signals, new line pointer) for the slice of `path` after line `start`;
    with start=0 the slice is everything after the last typed prompt."""
    recs, n = _records(path, start)
    if start == 0 and recs:
        idx = user_text_indexes(recs)
        if idx:
            recs = recs[idx[-1]:]
    return signals(recs), n


# ----------------------------------------------------------- ledger --
def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def record(kind, detail):
    """Append one event line (MATCHED / ADVISED / WRITTEN); never raises."""
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        fresh = not os.path.isfile(LEDGER)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            if fresh:
                fh.write("# THE LESSON LOOP (append-only): date time | ws | kind | detail. "
                         "MATCHED = prompt hook named entries; ADVISED = Stop hook asked for a "
                         "lesson; WRITTEN = LESSONS.md edited in that turn; CHECK = lint counts.\n")
            fh.write("%s | %s | %s | %s\n" % (_now(), workstation(), kind,
                                            re.sub(r"\s+", " ", detail).strip()))
    except OSError:
        pass


def _recent(kind, days=7):
    cut = datetime.datetime.now() - datetime.timedelta(days=days)
    n = 0
    if not os.path.isfile(LEDGER):
        return 0
    with open(LEDGER, encoding="utf-8") as fh:
        for raw in fh:
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3 or parts[2] != kind:
                continue
            try:
                if datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M") >= cut:
                    n += 1
            except ValueError:
                continue
    return n


def check():
    """Lint the book, print the counts, ledger one CHECK line (trust the ledger)."""
    ents = entries()
    probs = lint()
    adv, wr, mt = _recent("ADVISED"), _recent("WRITTEN"), _recent("MATCHED")
    verdict = "PASS" if not probs else "FAIL"
    print("LESSONS.md: %d entries | 7 d: advised %d, written %d, matched %d | %s"
          % (len(ents), adv, wr, mt, verdict))
    for p in probs:
        print("  FAIL " + p)
    line = "%s | %s | CHECK | entries %d | advised7d %d | written7d %d | matched7d %d | %s%s" % (
        _now(), workstation(), len(ents), adv, wr, mt, verdict,
        (" (" + "; ".join(probs)[:160] + ")") if probs else "")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from _ledger import append_unless_identical
        append_unless_identical(LEDGER, line, payload_from_col=2, note_prefix="[lesson_log] ")
    except ImportError:
        record("CHECK", line.split(" | ", 3)[3])
    return 0 if not probs else 1


# --------------------------------------------------------- selftest --
def _selftest():
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    book = ("# T\n\n## Brief a numbers task\nTags: lessons, x | brief one\nKeys: brief, employee, "
            "numbers, species numbers\nTHE ONE RIGHT WAY: read the spread.\nSee also: a.md\n\n"
            "## Broken entry\nTags: lessons | no keys\nTHE ONE RIGHT WAY: x\n")
    ents = entries(book)
    ok("entries parse headings, keys and briefs", len(ents) == 2 and ents[0]["keys"][0] == "brief"
       and ents[0]["brief"] == "brief one" and ents[0]["line"] == 3)
    ok("a multi-word key needs every word", match("please retune the species numbers for the ferns", ents)
       and not match("please retune the numbers for the ferns today", ents))
    ok("two single-word keys match", bool(match("brief an employee on the ferns tomorrow morning", ents)))
    ok("a short prompt never matches", match("brief employee numbers", ents) == [])
    ok("the printed line names the file, line and heading",
       any('LESSONS.md line 3 "Brief a numbers task"' in x
           for x in match_lines("brief an employee about the fern numbers today", ents)))
    probs = lint(book)
    ok("lint names the entry missing Keys and See also",
       len(probs) == 1 and "Broken entry" in probs[0] and "Keys:" in probs[0] and "See also:" in probs[0])
    ok("the live book lints clean", lint() == [])

    def tu(i, name, **inp):
        return {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": i, "name": name, "input": inp}]}}

    def tr(i, text, err=False):
        return {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": i, "content": text, "is_error": err}]}}

    recs = [{"type": "user", "message": {"content": "run the flora tests"}},
            tu("1", "Bash", command="python x.py"), tr("1", "Traceback: boom", True),
            tu("2", "Bash", command="python  x.py"), tr("2", "ok"),
            tu("3", "Edit", file_path="a.gd"), tr("3", "String to replace not found", True),
            tu("4", "Edit", file_path="a.gd"), tr("4", "not found", True),
            tu("5", "Bash", command="t"), tr("5", "FAIL  thing"),
            tu("6", "Bash", command="t2"), tr("6", "PASS  thing"),
            tu("7", "Bash", command="i"), tr("7", "I0048 resolved different (correction): mine='a' theirs='b'"),
            tu("8", "Agent", description="fix the lanes"), tu("9", "Agent", description="fix the lanes"),
            {"type": "user", "message": {"content": [{"type": "text", "text": "that's wrong, not what I meant"}]}},
            tu("10", "Edit", file_path="C:/x/LESSONS.md"), tr("10", "ok")]
    sig = signals(recs)
    ok("repeat after error is a signal", any("ran 2 times after an error" in s for s in sig))
    ok("two edit misses are a signal", any("2 edit calls missed" in s for s in sig))
    ok("FAIL then PASS is a signal", any("FAIL was followed by a PASS" in s for s in sig))
    ok("DIFFERENT is a signal", any("DIFFERENT" in s for s in sig))
    ok("a repeated brief is a signal", any("briefed twice" in s for s in sig))
    ok("a correction prompt is a signal", any("correction" in s for s in sig))
    ok("an edit to the book is reported as WRITTEN", any(s.startswith("WRITTEN") for s in sig))
    quiet = [{"type": "user", "message": {"content": "hello"}},
             tu("1", "Bash", command="ls"), tr("1", "a b c"),
             tu("2", "Bash", command="ls"), tr("2", "a b c")]
    ok("a clean turn has no signal (a repeated command without an error is fine)", signals(quiet) == [])
    ok("the slice starts at the last typed prompt", user_text_indexes(recs) == [0, 17])
    print("lesson_log selftest: %d failed" % fails)
    return 1 if fails else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if "--check" in argv:
        return check()
    if "--match" in argv:
        prompt = " ".join(argv[argv.index("--match") + 1:])
        lines = match_lines(prompt)
        print("\n".join(lines) if lines else "no matching lesson (score < %d)" % MIN_SCORE)
        return 0
    if "--scan" in argv:
        rest = argv[argv.index("--scan") + 1:]
        path = rest[0] if rest else None
        if not path:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import checkpoint as cp
            files = cp._transcript_files()
            path = files[0] if files else None
        if not path:
            print("no transcript found")
            return 1
        sig, n = scan(path)
        print("%s (%d lines)" % (path, n))
        print("\n".join("  " + s for s in sig) if sig else "  no trial-and-error signal in the last turn")
        return 0
    print(__doc__.split("Usage:")[1].split("THE LEDGER")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

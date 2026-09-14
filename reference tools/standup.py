"""THE STANDUP DIGEST (TOKEN_IDEAS idea 7, APPROVED by the CEO 2026-09-02:
"this goes along with my rules of creating a script for everything").

Replaces the manager reading every handoff note and changelog wholesale after
a pull: prints a ~20-line digest - recent commits, the newest WS-note
headlines, the tail of every history ledger, and the open roadmap index. The
manager reads THIS, then opens full notes only where the digest points.

Usage:  python tools/standup.py [--commits N] [--no-usage] [--selftest]   (default 5)

THE DIGEST DIET (the CEO 2026-09-14, "the most important pieces are context
and efficiency. As long as there is no loss there, I'm happy"): the digest
is the largest fixed load at session start, so it prints only what the
manager acts on. THE LOSS TEST: a line leaves the digest only when it is a
duplicate of another block, or carries no verdict and is one `tail -1`
away by a path the digest already prints. THE LAST EXCHANGE and WHERE WE
LEFT OFF are never cut. LEDGER TAILS prints a ledger's newest line in full
only when it carries a verdict (CHECK, FAIL, RED, STALE, WARN, UNSYNCED,
a cliff) or is newer than the previous standup (digest_size.txt's last
line); the rest collapse to name + date on shared lines; ledgers another
block already shows are skipped. Commits default to 5; RECENT DAYS prints
each day's first clause.

THE BUDGET (the CEO 2026-09-10, TOKEN_IDEAS 20): the digest refreshes the
usage sheet silently (tools/usage_report.py --quiet, incremental, ~2 s)
and prints the tail of docs/history/usage_daily.txt - yesterday's and
today's weighted spend judged against the previous 7 active days, with
the verdict. --no-usage skips the refresh (no transcripts, no time).

PURPOSE: Prints the post pull standup digest: the last exchange mined from
  harness transcripts, the day file's WHERE WE LEFT OFF, the usage budget
  line, THE LOOP (each run_all group's age), ledger trend proposals, version
  and recent commits, THE CORE (check_claude_md.py's OK/WARN line, run as a
  subprocess so the owner sees the core's size every session), WS notes
  from docs/index/notes.md, ledger tails, the open roadmap index, and OPEN
  QUESTIONS TO MAZHRON.
INTENT: the CEO 2026-09-02: 'this goes along with my rules of creating a
  script for everything.'

Search keys: standup, pull digest, session start, catch-up, the budget,
weighted spend, digest diet, loss test, quiet ledgers. See also: TOKEN_IDEAS.md ideas 7 + 20; docs/history/
ledgers; NEXT_STEPS.md; tools/usage_report.py (the daily line).
See also: TOKEN_IDEAS.md ideas 7 and 20; docs/history ledgers;
  NEXT_STEPS.md; tools/usage_report.py (the daily line);
  tools/ledger_trends.py (the proposals block).
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(args):
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except OSError:
        return ""  # tool missing (e.g. no git) - sections degrade, not crash


def _slug(path):
    """Claude Code names its per-project transcript folder by slugging the
    launch directory (every non-alphanumeric char -> '-')."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path)).lower()


def _transcript_files():
    """Top-level session transcripts for THIS project, newest first.
    Matches the slug of the repo root, its parent (Claude Code may be
    launched from either), or any folder containing the repo name."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(base):
        return []
    wanted = {_slug(ROOT), _slug(os.path.dirname(ROOT))}
    repo_slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.basename(ROOT)).lower()
    dirs = []
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if not os.path.isdir(full):
            continue
        dl = d.lower()
        if dl in wanted or repo_slug in dl:
            dirs.append(full)
    files = []
    for d in dirs:
        files += glob.glob(os.path.join(d, "*.jsonl"))
    return sorted(files, key=os.path.getmtime, reverse=True)


def _local_stamp(ts):
    import datetime
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return ts or "?"


_CAP = 8000  # chars replayed per side; the full text stays in the transcript


def _mine_exchange(path):
    """One transcript -> (asst_ts, user_ts, user_txt, imgs, asst_txt) for the
    final user-prompt -> assistant-text-reply pair, or None."""
    events = []
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return None
    with fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            typ = rec.get("type")
            if typ not in ("user", "assistant") or rec.get("isSidechain") \
                    or rec.get("isMeta"):
                continue
            content = (rec.get("message") or {}).get("content")
            if typ == "user":
                if isinstance(content, str):
                    txt, imgs = content, 0
                else:
                    blocks = [b for b in (content or []) if isinstance(b, dict)]
                    if any(b.get("type") == "tool_result" for b in blocks):
                        continue  # tool output, not the human typing
                    txt = "\n".join(b.get("text", "") for b in blocks
                                    if b.get("type") == "text")
                    imgs = sum(1 for b in blocks if b.get("type") == "image")
                s = txt.strip()
                if s.startswith("<") or s.startswith("Caveat:"):
                    continue  # harness command wrappers, not the human
                if not s and not imgs:
                    continue
                events.append((rec.get("timestamp", ""), "user", txt, imgs))
            else:
                txt = "\n".join(b.get("text", "") for b in (content or [])
                                if isinstance(b, dict)
                                and b.get("type") == "text")
                if txt.strip():
                    events.append((rec.get("timestamp", ""), "asst", txt, 0))
    ai = next((i for i in range(len(events) - 1, -1, -1)
               if events[i][1] == "asst"), None)
    if ai is None:
        return None
    ui = next((i for i in range(ai - 1, -1, -1)
               if events[i][1] == "user"), None)
    if ui is None:
        return None
    u, a = events[ui], events[ai]
    if u[2].strip().lower().lstrip("/") == "standup":
        return None  # that's THIS session invoking standup - not an exchange
    return (a[0], u[0], u[2], u[3], a[2])


def print_last_exchange():
    # THE LAST EXCHANGE comes from the HARNESS TRANSCRIPT, not the day file
    # (the CEO's third ruling on this, 2026-09-03 PM3): the day-file copy is
    # only as fresh as the last checkpoint, and twice now the exchange
    # replayed stale or condensed. The transcript on disk is ground truth -
    # every prompt and reply, word for word, written by the harness itself.
    # Standup replays the final pair verbatim; nothing depends on manager
    # discipline anymore.
    best = None
    best_file = None
    for path in _transcript_files()[:8]:
        got = _mine_exchange(path)
        if got and (best is None or got[0] > best[0]):
            best, best_file = got, path
    if not best:
        print("== THE LAST EXCHANGE: no harness transcripts found - falling "
              "back to the day file's WHERE WE LEFT OFF below.")
        return False
    asst_ts, user_ts, user_txt, imgs, asst_txt = best
    sess = os.path.basename(best_file).split(".")[0][:8]
    print("== THE LAST EXCHANGE (harness transcript = ground truth; "
          "session %s)" % sess)
    print("  USER'S LAST PROMPT (verbatim, %s):" % _local_stamp(user_ts))
    body = user_txt.strip() or "(no text)"
    if len(body) > _CAP:
        body = body[:_CAP] + "\n[truncated - full text in the transcript]"
    for ln in body.splitlines():
        print("  > " + ln)
    if imgs:
        print("  > [+ %d image attachment(s)]" % imgs)
    print("  MANAGER'S LAST RESPONSE (verbatim, %s):" % _local_stamp(asst_ts))
    body = asst_txt.strip()
    if len(body) > _CAP:
        body = body[:_CAP] + "\n[truncated - full text in the transcript]"
    for ln in body.splitlines():
        print("  > " + ln)
    return True


def print_budget():
    """THE BUDGET: refresh the usage sheet quietly, then the daily line's
    tail - each day's weighted spend vs the previous 7 active days. A
    missing script or transcript set degrades to one line, never a crash."""
    script = os.path.join(ROOT, "tools", "usage_report.py")
    daily = os.path.join(ROOT, "docs", "history", "usage_daily.txt")
    if not os.path.isfile(script):
        return

    try:
        subprocess.run([sys.executable, script, "--quiet"], cwd=ROOT,
                       capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        pass
    print("== THE BUDGET (weighted tokens = what counts against the plan; "
          "each day vs the previous 7 active days - usage_daily.txt tail)")
    try:
        with open(daily, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()]
    except OSError:
        print("  (no usage_daily.txt yet - run tools/usage_report.py)")
        return
    header = [ln for ln in lines if ln.startswith("#")]
    body = [ln for ln in lines if not ln.startswith("#")]
    if header:
        print("  " + header[-1].lstrip("# "))
    for ln in body[-2:]:
        print("  " + ln)
    if any("CHECK:" in ln for ln in body[-2:]):
        print("  manager: a CHECK verdict names what went wrong - relay it verbatim.")


def print_open_questions():
    """THE OPEN QUESTIONS block (the CEO's ruling 2026-09-14): open ones,
    oldest first, so a question waiting on the owner never scrolls off a
    ledger nobody rereads. Silent on any failure - never blocks standup."""
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import open_questions
        ages = open_questions.open_rows()
    except Exception:
        print("== OPEN QUESTIONS TO MAZHRON (unavailable)")
        return
    oldest = ages[0][0] if ages else 0
    print("== OPEN QUESTIONS TO MAZHRON (%d open, oldest %s d)" % (len(ages), oldest))
    for age, r in ages:
        print("  %s | %sd | %s" % (r["id"], age if age >= 0 else "?", r["question"]))


# THE LOOP LAW (the CEO's ruling: "Any script that should be run multiple
# times must be called by the main looping script; every action, every
# standup"). Fixed list matching tools/run_all.py's GROUPS keys (check,
# regen, tests, metrics, probes, builds, session) - a plain list rather
# than importing run_all.py, which would run its module-level code.
LOOP_GROUPS = ["check", "regen", "tests", "metrics", "probes", "builds", "session"]


def print_loop():
    """THE LOOP block: last run per run_all group, from loop_runs.txt
    (`date time | ws | group | seconds | result`, written by run_all.py)."""
    import datetime
    print("== THE LOOP (run_all groups, from loop_runs.txt)")
    latest = {}
    path = os.path.join(ROOT, "docs", "history", "loop_runs.txt")
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) < 3:
                    continue
                latest[parts[2]] = parts[0]
    except OSError:
        pass
    for g in LOOP_GROUPS:
        when = latest.get(g)
        if not when:
            print("  %-8s | never" % g)
            continue
        try:
            dt = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
            age = (datetime.datetime.now() - dt).days
            print("  %-8s | last run %s | %d d" % (g, when, age))
        except ValueError:
            print("  %-8s | last run %s" % (g, when))


# ---- THE DIGEST DIET helpers (pure; covered by --selftest) -----------------

# Ledgers another digest block already prints in full (THE BUDGET, THE LOOP,
# PROPOSALS, OPEN QUESTIONS, RECENT DAYS) or that only summarize a *_runs
# sibling printed on the same list. One `tail -1` away, never lost.
SHOWN_ELSEWHERE = {
    "usage_daily.txt", "loop_runs.txt", "proposal_runs.txt", "open_questions.txt",
    "days_index.txt", "wiki_heat.txt", "wiki_links.txt", "big_reads.txt",
    "intent_metrics.txt", "usage_metrics.txt", "cache_misses.txt", "core_diet.txt",
    "ledger_heads.txt",
}
_VERDICT = re.compile(r"\b(CHECK|FAIL|RED [1-9]|STALE|WARN|UNSYNCED|ERROR|STALL|MISSING|missing required: (?!none))")
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?")  # first date in the line


def has_verdict(line):
    """True when a ledger line carries something the manager must see."""
    return bool(_VERDICT.search(line))


def line_stamp(line):
    """'YYYY-MM-DD HH:MM' (or 'YYYY-MM-DD'): the first date in the line's head, else ''."""
    m = _DATE.search(line[:80])
    if not m:
        return ""
    return m.group(1) + (" " + m.group(2) if m.group(2) else "")


def last_standup_stamp(ledger_text):
    """The previous standup's 'YYYY-MM-DD HH:MM' from digest_size.txt, else ''."""
    for ln in reversed(ledger_text.splitlines()):
        st = line_stamp(ln)
        if st:
            return st
    return ""


def tails_plan(ledgers, since):
    """ledgers: [(name, newest_line)] -> (full: [(name, line)], quiet: [name date]).
    Full when the line has a verdict or is newer than `since`; quiet otherwise."""
    full, quiet = [], []
    for name, line in ledgers:
        if name in SHOWN_ELSEWHERE:
            continue
        st = line_stamp(line)
        if has_verdict(line) or (st and since and st > since):
            full.append((name, line))
        else:
            quiet.append("%s %s" % (name[:-4] if name.endswith(".txt") else name,
                                    st[5:10] if st else "-"))
    return full, quiet


def wrap_names(names, width=96, indent="    "):
    out, cur = [], ""
    for n in names:
        piece = (", " if cur else "") + n
        if len(cur) + len(piece) > width and cur:
            out.append(indent + cur)
            cur = n
        else:
            cur += piece
    if cur:
        out.append(indent + cur)
    return out


def first_clause(summary, cap=150):
    """A days_index summary's first clause: up to the first ';' or ' then ',
    capped; the full line stays in days_index.txt."""
    cut = re.split(r";| then |\. ", summary, maxsplit=1)[0].strip().rstrip(",:")
    return cut if len(cut) <= cap else cut[:cap].rstrip() + "..."


def selftest():
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)
    check("CHECK is a verdict", has_verdict("2026-09-14 | WS1 | CHECK: spend +229%"))
    check("PASS clean is not", not has_verdict("2026-09-11 16:53 | WS2 | raingoal | 1/1 PASS"))
    check("RED 0 is not, RED 2 is", not has_verdict("| RED 0 |") and has_verdict("| RED 2 |"))
    check("PROPOSE: none is not", not has_verdict("== PROPOSE: none"))
    check("a cliff is", has_verdict("cliffs: r8 LIFT STALL (<+5%)"))
    check("missing required: none is not", not has_verdict("20/20 present | missing required: none"))
    check("line_stamp reads date+time", line_stamp("2026-09-14 16:35 | WS1 | x") == "2026-09-14 16:35")
    check("line_stamp reads a bare date", line_stamp("2026-09-14 | WS1 | x") == "2026-09-14")
    check("line_stamp empty without a date", line_stamp("files 47 | sections 687") == "")
    check("line_stamp finds a date later in the head", line_stamp("RESOLVED | I0040 | 2026-09-14 16:55 | WS1") == "2026-09-14 16:55")
    check("first_clause drops a trailing comma", first_clause("I0002 explained, then x") == "I0002 explained")
    check("last_standup_stamp takes the newest dated line",
          last_standup_stamp("# hdr\n2026-09-14 10:00 | a\n2026-09-14 16:39 | b\n") == "2026-09-14 16:39")
    full, quiet = tails_plan([("a_runs.txt", "2026-09-14 17:00 | new"),
                              ("b_runs.txt", "2026-09-10 | old | PASS"),
                              ("c_runs.txt", "2026-09-01 | FAIL"),
                              ("usage_daily.txt", "2026-09-14 | CHECK")], "2026-09-14 16:39")
    check("newer than the last standup prints in full", ("a_runs.txt", "2026-09-14 17:00 | new") in full)
    check("old and clean collapses to name + date", quiet == ["b_runs 09-10"])
    check("old with a verdict prints in full", any(n == "c_runs.txt" for n, _ in full))
    check("shown-elsewhere ledgers are skipped", not any(n == "usage_daily.txt" for n, _ in full))
    check("first_clause cuts at ';'", first_clause("Pulled WS2; then more") == "Pulled WS2")
    check("first_clause cuts at ' then '", first_clause("I0002 explained then THE AUDIT") == "I0002 explained")
    check("first_clause caps long text", first_clause("x" * 200).endswith("..."))
    check("wrap_names wraps", len(wrap_names(["n%02d 09-14" % i for i in range(30)])) > 1)
    print("standup selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(description="Post-pull standup digest")
    ap.add_argument("--commits", type=int, default=5)  # THE DIGEST DIET: was 12
    ap.add_argument("--no-usage", action="store_true",
                    help="skip the usage-sheet refresh + THE BUDGET block")
    args = ap.parse_args()

    # THE LAST EXCHANGE prints FIRST and comes from the harness transcript
    # (see print_last_exchange). The day file's WHERE WE LEFT OFF follows as
    # the STATE summary (version, shipped, queue, next-likely) - it still
    # stores the checkpoint-time exchange for the searchable record, but
    # verbatim replay no longer depends on it.
    replayed = print_last_exchange()

    days = sorted(glob.glob(os.path.join(ROOT, "docs", "history", "days", "*.md")))
    if days:
        import datetime
        newest = os.path.basename(days[-1])
        file_date = newest[:10]
        today = datetime.date.today().isoformat()
        if file_date == today:
            print("== SAME DAY - continuing %s" % newest)
        else:
            try:
                gap = (datetime.date.fromisoformat(today)
                       - datetime.date.fromisoformat(file_date)).days
                ago = "%d day(s) ago" % gap
            except ValueError:
                ago = "?"
            print("== NEW DAY (last log %s, %s) - PREVIOUS day's close below;"
                  % (file_date, ago))
            print("   manager: create today's day file at the first checkpoint.")
        body = open(days[-1], encoding="utf-8").read()
        wm = re.search(r"## WHERE WE LEFT OFF.*?(?=\n## |\Z)", body, flags=re.S)
        print("== WHERE WE LEFT OFF (%s)" % newest)
        if wm:
            # THE DIGEST DIET (2026-09-14, after ledger_trends proposed a trim
            # at 33k bytes): when the transcript block above already replayed
            # the exchange verbatim, the day file's copy of the same quote
            # blocks is not printed twice - only its STATE / NEXT lines.
            quoting = False
            for ln in wm.group(0).splitlines()[1:]:
                s = ln.strip()
                if replayed:
                    if s.startswith(("MAZHRON'S LAST PROMPT", "MANAGER'S LAST RESPONSE",
                                     "USER'S LAST PROMPT")):
                        quoting = True
                        continue
                    if quoting and (s.startswith(">") or s == ""):
                        continue
                    quoting = False
                print("  " + ln)
            if replayed:
                print("  (prompt + response omitted here: the transcript block above is the verbatim record)")
        else:
            print("  (no WHERE WE LEFT OFF section yet - see the file's "
                  "COMPLETED list)")

    if not args.no_usage:
        print_budget()

    print_loop()

    # THE LEARNING LOOP's closing step (the CEO 2026-09-10): ledger trends
    # become proposals the owner rules on; nothing is applied by a script.
    out = sh([sys.executable, os.path.join(ROOT, "tools", "ledger_trends.py")])
    if out:
        print(out.rstrip())

    print("== VERSION + RECENT COMMITS")
    # Version source is per-project: Everwood reads project.godot. In a
    # non-Godot install, adapt this block (package.json, pyproject.toml,
    # a VERSION file...) - a missing source degrades to "?", never crashes.
    try:
        with open(os.path.join(ROOT, "project.godot"), encoding="utf-8") as fh:
            m = re.search(r'config/version="([^"]+)"', fh.read())
        print("  version: %s" % (m.group(1) if m else "?"))
    except OSError:
        print("  version: ? (no project.godot - adapt the version block)")
    log = sh(["git", "log", "--oneline", "-%d" % args.commits])
    if log:
        for ln in log.splitlines():
            print("  " + ln)
    else:
        print("  (no git history - not a git repo, or git unavailable)")

    # THE POINTER CORE (2026-09-14): the notes live in docs/index/notes.md now;
    # the core's size is said out loud here so the owner sees it every session.
    print("== THE CORE (CLAUDE.md; tools/check_claude_md.py; Anthropic: under 200 lines)")
    try:
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_claude_md.py")],
                             cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
        print("  " + (out.splitlines()[0] if out else "(no output)"))
        for ln in out.splitlines()[1:6]:
            print("  " + ln)
    except Exception as e:  # noqa: BLE001 - the digest never crashes on a lint
        print("  (lint did not run: %s)" % e)

    print("== NEWEST WS NOTES (headlines only - open docs/index/notes.md for a body)")
    try:
        with open(os.path.join(ROOT, "docs", "index", "notes.md"), encoding="utf-8") as fh:
            heads = re.findall(r"^- \*\*(→ (?:BOTH )?WS[^:]{0,110})", fh.read(),
                               flags=re.M)
        for h in heads[:6]:
            print("  " + h.strip())
    except OSError:
        print("  (no docs/index/notes.md)")

    # THE DIGEST DIET (2026-09-14): one tail line per ledger, not two - the
    # previous line is one `tail -2` away when a comparison is wanted, and
    # thirty ledgers at two lines each were a third of the digest.
    # THE DIGEST DIET (the CEO 2026-09-14, "no loss" as the test): a
    # ledger's newest line prints in full only when it carries a verdict or
    # is newer than the previous standup; the rest collapse to name + date.
    hist = os.path.join(ROOT, "docs", "history")
    try:
        with open(os.path.join(hist, "digest_size.txt"), encoding="utf-8") as fh:
            since = last_standup_stamp(fh.read())
    except OSError:
        since = ""
    ledgers = []
    for path in sorted(glob.glob(os.path.join(hist, "*.txt"))):
        with open(path, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        if lines:
            ledgers.append((os.path.basename(path), lines[-1]))
    full, quiet = tails_plan(ledgers, since)
    print("== LEDGER TAILS (docs/history/; full line = a verdict or new since the last standup%s; `tail -3 <ledger>` for a trend)"
          % (" " + since if since else ""))
    for name, line in full:
        print("  %s: %s" % (name, line))
    if quiet:
        print("  quiet (no verdict, unchanged; name + last date):")
        for ln in wrap_names(quiet):
            print(ln)

    print("== OPEN ROADMAP (NEXT_STEPS index)")
    try:
        with open(os.path.join(ROOT, "NEXT_STEPS.md"), encoding="utf-8") as fh:
            for ln in fh:
                if ln.startswith("- [NS-"):
                    print("  " + ln.strip())
    except OSError:
        print("  (no NEXT_STEPS.md)")

    print_open_questions()

    days_index = os.path.join(ROOT, "docs", "history", "days_index.txt")
    if os.path.isfile(days_index):
        print("== RECENT DAYS (docs/history/days/)")
        with open(days_index, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        for ln in lines[-3:]:
            parts = [x.strip() for x in ln.split(" | ", 3)]
            if len(parts) == 4:  # THE DIGEST DIET: the first clause; the file has the rest
                print("  %s | %s | %s | %s" % (parts[0], parts[1], parts[2], first_clause(parts[3])))
            else:
                print("  " + ln)


if __name__ == "__main__":
    main()

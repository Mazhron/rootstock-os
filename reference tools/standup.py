"""THE STANDUP DIGEST (TOKEN_IDEAS idea 7, APPROVED by the CEO 2026-09-02:
"this goes along with my rules of creating a script for everything").

Replaces the manager reading every handoff note and changelog wholesale after
a pull: prints a ~20-line digest - recent commits, the newest WS-note
headlines, the tail of every history ledger, and the open roadmap index. The
manager reads THIS, then opens full notes only where the digest points.

Usage:  python tools/standup.py [--commits N] [--no-usage]   (default 12)

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
weighted spend. See also: TOKEN_IDEAS.md ideas 7 + 20; docs/history/
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


def main():
    ap = argparse.ArgumentParser(description="Post-pull standup digest")
    ap.add_argument("--commits", type=int, default=12)
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
    print("== LEDGER TAILS (docs/history/, newest line each; `tail -3 <ledger>` for a trend)")
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "history", "*.txt"))):
        with open(path, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        if lines:
            print("  %s: %s" % (os.path.basename(path), lines[-1]))

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
            print("  " + ln)


if __name__ == "__main__":
    main()

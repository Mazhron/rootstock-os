"""THE STANDUP DIGEST (TOKEN_IDEAS idea 7, APPROVED by Mazhron 2026-09-02:
"this goes along with my rules of creating a script for everything").

Replaces the manager reading every handoff note and changelog wholesale after
a pull: prints a ~20-line digest - recent commits, the newest WS-note
headlines, the tail of every history ledger, and the open roadmap index. The
manager reads THIS, then opens full notes only where the digest points.

Usage:  python tools/standup.py [--commits N]   (default 12)

Search keys: standup, pull digest, session start, catch-up. See also:
TOKEN_IDEAS.md idea 7; docs/history/ ledgers; NEXT_STEPS.md.
"""
import argparse
import glob
import json
import os
import re
import subprocess

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
    # (Mazhron's third ruling on this, 2026-09-03 PM3): the day-file copy is
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
        return
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


def main():
    ap = argparse.ArgumentParser(description="Post-pull standup digest")
    ap.add_argument("--commits", type=int, default=12)
    args = ap.parse_args()

    # THE LAST EXCHANGE prints FIRST and comes from the harness transcript
    # (see print_last_exchange). The day file's WHERE WE LEFT OFF follows as
    # the STATE summary (version, shipped, queue, next-likely) - it still
    # stores the checkpoint-time exchange for the searchable record, but
    # verbatim replay no longer depends on it.
    print_last_exchange()

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
            for ln in wm.group(0).splitlines()[1:]:
                print("  " + ln)
        else:
            print("  (no WHERE WE LEFT OFF section yet - see the file's "
                  "COMPLETED list)")

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

    print("== NEWEST WS NOTES (headlines only - open CLAUDE.md for a body)")
    try:
        with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as fh:
            heads = re.findall(r"^- \*\*(→ WS[^:]{0,110})", fh.read(),
                               flags=re.M)
        for h in heads[:6]:
            print("  " + h.strip())
    except OSError:
        print("  (no CLAUDE.md)")

    print("== LEDGER TAILS (docs/history/)")
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "history", "*.txt"))):
        with open(path, encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh if ln.strip()
                     and not ln.startswith("#")]
        if lines:
            print("  %s:" % os.path.basename(path))
            for ln in lines[-2:]:
                print("    " + ln)

    print("== OPEN ROADMAP (NEXT_STEPS index)")
    try:
        with open(os.path.join(ROOT, "NEXT_STEPS.md"), encoding="utf-8") as fh:
            for ln in fh:
                if ln.startswith("- [NS-"):
                    print("  " + ln.strip())
    except OSError:
        print("  (no NEXT_STEPS.md)")

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

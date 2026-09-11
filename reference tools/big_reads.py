"""THE BIG-READS LEDGER (Mazhron's ruling 2026-09-10: "Section or split as
necessary. This should not require my approval, especially if we can script
it. It should be part of the looping scripts that run automatically.").

usage_daily.txt counts big whole-file reads per day but never says WHICH
files. This script mines the harness transcripts for every whole-file read
(a bare Read with no offset/limit, or a bare cat/type/Get-Content in a shell
command) whose tool result came back at BIG_READ_TOK tokens or more, and
tallies them PER FILE, with the fix each file needs:

  sectioned   - a .md with headings: Grep "^## " first, read one section
  NO HEADINGS - a big .md without "## " headings: it needs sectioning (the
                manager adds headings on the spot, no approval needed)
  code        - .gd/.py/.js/.gdshader: read by function index (the diet
                guard now serves that index instead of the whole file)
  data/dump   - generated or data files: never read whole, grep them
  gone        - the path no longer exists (moved, retired or scratch)

READ-ONLY: it counts and reports; it never moves or deletes anything (the
preservation law). Incremental via a byte-offset cache like wiki_heat.py.

Outputs: docs/history/big_reads.txt (regenerated) + one ledger line in
docs/history/big_reads_runs.txt. Wired into run_all's metrics group; the
ledger_trends proposal on big reads points here.

Usage:  python tools/big_reads.py [--days 30] [--top 30] [--no-cache]

Search keys: big reads, whole-file reads, read diet, which files, section
or split. See also: the read diet -> WIKI_METHOD.md | the diet guard ->
tools/hooks/diet_guard.py | wiki heat -> tools/wiki_heat.py | proposals ->
tools/ledger_trends.py | TOKEN_IDEAS.md idea 15.
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wiki_heat import find_transcripts, local_day, workstation  # noqa: E402
from usage_report import IMAGE_EXT, image_tokens  # noqa: E402  (pixels, not base64)

ROOT = os.path.dirname(HERE)
HIST = os.path.join(ROOT, "docs", "history")
OUT_TXT = os.path.join(HIST, "big_reads.txt")
RUNS_TXT = os.path.join(HIST, "big_reads_runs.txt")
CACHE_PATH = os.path.join(HIST, "big_reads_cache.json")
CACHE_VERSION = 1
BIG_READ_TOK = 10_000   # the 10k rule (TOKEN_IDEAS 15) - same as the guard
CODE_EXT = (".gd", ".py", ".js", ".gdshader", ".ts", ".ps1", ".sh")
DATA_EXT = (".tres", ".tscn", ".csv", ".json", ".txt", ".html", ".xlsx", ".log")

_CLAUSE_SPLIT = re.compile(r"&&|\|\||\||;")
_WHOLE_HEAD = re.compile(r"^\s*(cat|type|get-content|gc)\s+((?:-\S+\s+)*)([^\s|;&]+)", re.I)
_LIMITER = re.compile(r"-totalcount|-tail\b|\bhead\b|\btail\b|select-object\s+-(first|last)"
                      r"|select\s+-(first|last)|sed\s+-n|\b(wc|grep|findstr|sort|uniq|cut)\b", re.I)

RUNS_HEADER = ("# GENERATED ledger (append-only) by tools/big_reads.py: "
               "date | WS | big whole reads (all time) | last-7-active-day avg | "
               "top file (count)\n")


def norm_path(raw):
    p = raw.strip("\"'").replace("\\", "/")
    root = ROOT.replace("\\", "/")
    if p.lower().startswith(root.lower() + "/"):
        p = p[len(root) + 1:]
    return p


def pending_from_assistant(rec):
    """-> {tool_use_id: (path)} for the whole-read tool_use blocks of one record."""
    out = {}
    msg = rec.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, list):
        return out
    for blk in content:
        if not (isinstance(blk, dict) and blk.get("type") == "tool_use"):
            continue
        tin = blk.get("input") or {}
        if not isinstance(tin, dict):
            continue
        name = blk.get("name")
        tid = blk.get("id") or ""
        if name == "Read":
            if tin.get("file_path") and not (tin.get("offset") or tin.get("limit")):
                out[tid] = norm_path(tin["file_path"])
        elif name in ("Bash", "PowerShell"):
            cmd = tin.get("command") or ""
            if _LIMITER.search(cmd):
                continue
            for clause in _CLAUSE_SPLIT.split(cmd):
                m = _WHOLE_HEAD.match(clause)
                if m:
                    out[tid] = norm_path(m.group(3))
                    break
    return out


def parse_transcript(path, offset):
    """-> (events [[day, path, est_tok], ...], new_offset). Pairs each
    whole-read tool_use with its tool_result to size what came back."""
    events = []
    pending = {}
    with open(path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except (ValueError, UnicodeDecodeError):
                continue
            kind = rec.get("type")
            if kind == "assistant":
                pending.update(pending_from_assistant(rec))
                continue
            if kind != "user":
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            day = local_day(rec.get("timestamp") or "")
            for blk in content:
                if not (isinstance(blk, dict) and blk.get("type") == "tool_result"):
                    continue
                fpath = pending.pop(blk.get("tool_use_id") or "", None)
                if not fpath or not day:
                    continue
                if fpath.lower().endswith(IMAGE_EXT):
                    # A picture is priced by pixels (~1-2k tokens), never by
                    # its base64 payload; it is counted, not called "big".
                    ap = fpath if os.path.isabs(fpath) else os.path.join(ROOT, fpath)
                    events.append([day, fpath, image_tokens(ap), "image"])
                    continue
                payload = rec.get("toolUseResult")
                if payload is None:
                    payload = blk.get("content")
                try:
                    est = len(json.dumps(payload, default=str)) // 4
                except (TypeError, ValueError):
                    est = len(str(payload)) // 4
                if est >= BIG_READ_TOK:
                    events.append([day, fpath, est, "text"])
        new_offset = fh.tell()
    return events, new_offset


def load_cache(no_cache):
    if no_cache or not os.path.isfile(CACHE_PATH):
        return {"version": CACHE_VERSION, "files": {}}
    try:
        cache = json.load(open(CACHE_PATH, encoding="utf-8"))
    except (ValueError, OSError):
        return {"version": CACHE_VERSION, "files": {}}
    if cache.get("version") != CACHE_VERSION:
        return {"version": CACHE_VERSION, "files": {}}
    cache.setdefault("files", {})
    return cache


def gather(no_cache):
    cache = load_cache(no_cache)
    events = []
    paths = find_transcripts()
    for p in paths:
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        ent = cache["files"].get(p)
        if ent and ent.get("size", -1) <= size and ent.get("offset", 0) <= size:
            old = ent.get("events", [])
            new, off = parse_transcript(p, ent.get("offset", 0))
            ent.update({"size": size, "offset": off, "events": old + new})
        else:
            new, off = parse_transcript(p, 0)
            ent = {"size": size, "offset": off, "events": new}
            cache["files"][p] = ent
        events.extend(ent["events"])
    return events, len(paths), cache


def advice(path):
    ap = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    low = path.lower()
    if not os.path.isfile(ap):
        return "gone"
    if low.endswith(".md"):
        try:
            with open(ap, "rb") as fh:
                heads = sum(1 for ln in fh if ln.startswith(b"## "))
        except OSError:
            heads = 0
        return ("sectioned (%d headings)" % heads) if heads >= 2 else "NO HEADINGS - section it"
    if low.endswith(CODE_EXT):
        return "code - func index"
    if low.endswith(DATA_EXT):
        return "data/dump - grep it"
    return "other"


def ktok(n):
    return "~%dk" % round(n / 1000.0)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args(argv)

    events, n_tr, cache = gather(args.no_cache)
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=args.days)).strftime("%Y-%m-%d")

    by_file = {}
    by_day = {}
    images = {"n": 0, "tok": 0, "recent": 0}
    for ev in events:
        day, path, est = ev[0], ev[1], ev[2]
        kind = ev[3] if len(ev) > 3 else "text"
        if kind == "image":
            images["n"] += 1
            images["tok"] += est
            if day >= cutoff:
                images["recent"] += 1
            continue
        f = by_file.setdefault(path, {"n": 0, "tok": 0, "last": "", "recent": 0})
        f["n"] += 1
        f["tok"] += est
        f["last"] = max(f["last"], day)
        if day >= cutoff:
            f["recent"] += 1
        d = by_day.setdefault(day, {"n": 0, "tok": 0})
        d["n"] += 1
        d["tok"] += est

    files = sorted(by_file.items(), key=lambda kv: (-kv[1]["n"], -kv[1]["recent"], kv[1]["last"]))
    days = sorted(by_day.items())
    last7 = days[-7:]
    avg7 = (sum(d["n"] for _, d in last7) / float(len(last7))) if last7 else 0.0

    L = ["# GENERATED by tools/big_reads.py - every whole-file read of TEXT >= %s tokens, "
         "mined from the harness transcripts, tallied per file; never hand-edit" % ktok(BIG_READ_TOK),
         "# READ-ONLY report. The fix column is the manager's standing order (Mazhron "
         "2026-09-10): section or split on this report's word, no approval needed.",
         "# Images are priced by pixels (~1-2k tokens each) and listed on their own line, "
         "never as big reads.",
         "",
         "== BY FILE (n = big whole reads all time | in the last %d days | avg tokens | last | fix)" % args.days]
    if not files:
        L.append("(no big whole reads of text found)")
    for path, f in files[:args.top]:
        L.append("%-3d recent %-3d | %-5s | %s | %-28s | %s" % (
            f["n"], f["recent"], ktok(f["tok"] // f["n"]), f["last"], advice(path), path))
    if len(files) > args.top:
        L.append("(+%d more files)" % (len(files) - args.top))
    L += ["", "== BY DAY (big whole reads of text | tokens)"]
    for day, d in days[-14:]:
        L.append("%s | %-3d | %s" % (day, d["n"], ktok(d["tok"])))
    total = sum(f["n"] for _, f in files)
    recent_total = sum(f["recent"] for _, f in files)
    top = files[0] if files else None
    summary = ("big whole reads of text %d all time | %d in the last %d days | last-7-active-day "
               "avg %.1f | images read %d (%s, %d recent) | transcripts %d" % (
                   total, recent_total, args.days, avg7, images["n"], ktok(images["tok"]),
                   images["recent"], n_tr))
    L += ["", "== SUMMARY", summary, ""]
    with open(OUT_TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | %d | %.1f | %s" % (
        stamp, workstation(), total, avg7,
        ("%s (%d)" % (top[0], top[1]["n"])) if top else "none")
    new = not os.path.isfile(RUNS_TXT)
    with open(RUNS_TXT, "a", encoding="utf-8") as fh:
        if new:
            fh.write(RUNS_HEADER)
        fh.write(line + "\n")
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)
    print("== BIG READS (docs/history/big_reads.txt)")
    for ln in L[3:3 + min(12, len(files) + 1)]:
        print("  " + ln)
    print("  " + summary)


if __name__ == "__main__":
    main()

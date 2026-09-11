"""WIKI HEAT (task WIKI-HEAT-1, 2026-09-10): how often each wiki FILE and each
wiki SECTION actually gets read, mined from the Claude Code harness
transcripts - the same JSONL records tools/usage_report.py meters tokens
from, read here instead for READ EVENTS (Read/Bash/PowerShell/Grep calls
that touch a .md wiki file).

THE WIKI = every *.md at the repo root (non-recursive) + docs/systems/*.md +
docs/cold/*.md (that folder may not exist yet). A SECTION is a "## " heading
line through the line before the next "## " (or EOF); lines before the
first heading are the pseudo-section "(preamble)".

APPROXIMATION NOTE: headings move over time (sections get added, reworded,
reordered), but a transcript only records the LINE RANGE that was read, not
which heading it fell under at the time. This script maps every historical
read event against the file's CURRENT headings - a read from months ago
lands wherever those old line numbers fall today. That is inherent to line-
range mining; treat the section-level counts as approximate, the file-level
counts (which don't depend on heading position) as exact.

NOTHING MOVES. This script only counts and reports; the COLD SECTIONS list
is candidates for a human to consider for docs/cold/ - never an automatic
mover. (THE PRESERVATION LAW, 2026-09-10: this script contains no deletion
code and never touches wiki content.)

Outputs:
  docs/history/wiki_heat.txt       - REGENERATED whole each run: file totals,
                                      hottest sections, cold candidates,
                                      one summary line
  docs/history/wiki_heat_runs.txt  - append-only ledger, one line per run
  docs/history/wiki_heat_cache.json - incremental parse cache (transcripts
                                      are append-only; reruns only read new
                                      bytes). --no-cache forces a full
                                      rebuild.

Usage:  python tools/wiki_heat.py [--days 30] [--top 20] [--no-cache]
        # in run_all's metrics group

Search keys: wiki heat, read counts, cold sections, cold shelf candidates,
transcript mining.
See also: docs/systems/tooling.md (the wiki tooling); WIKI_METHOD.md (the
cold shelf); tools/usage_report.py (the same transcript format, sheet
side); tools/cold_shelf.py (the mover).
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "docs", "history")
OUT_TXT = os.path.join(HIST, "wiki_heat.txt")
RUNS_TXT = os.path.join(HIST, "wiki_heat_runs.txt")
CACHE_PATH = os.path.join(HIST, "wiki_heat_cache.json")
CACHE_VERSION = 1

SENTINEL_EOF = 10**9  # "to EOF" upper bound for an open-ended section read

# WHY COLD (Mazhron's ruling 2026-09-10: "be certain that you are learning
# why we're not referencing parts of the wiki ... in a game situation, we
# only touch certain files at certain times ... we built the wiki not only
# for your reference, but for a human reference"). Every wiki file maps to
# the code/data areas it documents; git activity in those areas over the
# window classifies its cold sections:
#   dormant        system doc, its code untouched in the window -> expected
#   current        system doc opened (any read) since its code last moved
#   active-unread  system doc whose code MOVED after the doc was last
#                  opened -> the one class worth a look (mis-titled
#                  heading? stale? unneeded?)
#   process        the operating-system files (laws, registry, roadmap) -
#                  read when the ritual calls, never on a schedule
#   reference      human/portable docs (lore, store copy, kit method files)
#   archive        history + the cold shelf: cold by design
# Cold by read count alone is NEVER a shelf reason. NOTHING MOVES.
AREA_MAP = {
    "docs/systems/soil.md": ["scripts/world/soil_grid.gd", "data/soil", "shaders/soil",
                             "assets/soil", "scripts/world/water_tile_overlay.gd",
                             "scripts/world/bank_overlay.gd", "scripts/world/inflow_overlay.gd"],
    "docs/systems/weather.md": ["scripts/core/climate.gd", "scripts/world/cloud_system.gd",
                                "scripts/entities/cloud.gd", "scripts/entities/raindrop.gd",
                                "scripts/world/catastrophe.gd", "scripts/ui/catastrophe_",
                                "scripts/world/sky_view.gd"],
    "docs/systems/flora.md": ["scripts/world/plant_system.gd", "scripts/world/seed_system.gd",
                              "scripts/entities/plant.gd", "scripts/entities/seed.gd",
                              "data/species", "scripts/core/evolutions.gd", "scripts/data/species"],
    "docs/systems/fauna.md": ["scripts/world/animal_system.gd", "scripts/world/bird_system.gd",
                              "scripts/world/pollinator_system.gd", "scripts/entities/animal.gd",
                              "scripts/entities/bird.gd", "data/animals", "scripts/data/animal"],
    "docs/systems/world-map.md": ["scripts/core/session.gd", "scripts/ui/rebirth_",
                                  "scripts/world/run_controller.gd", "scripts/data/biomes",
                                  "scripts/core/wills.gd", "scripts/ui/will_menu.gd"],
    "docs/systems/meta.md": ["scripts/core/meta.gd", "scripts/core/save_", "scripts/core/upgrade_manager.gd",
                             "scripts/core/modifiers.gd", "data/upgrades", "scripts/core/goals.gd",
                             "scripts/ui/ash_shop.gd", "scripts/core/balance_log.gd"],
    "docs/systems/ui.md": ["scripts/ui/", "scripts/core/settings.gd", "scripts/core/music_player.gd",
                           "scripts/core/analytics.gd", "scripts/core/tool_manager.gd"],
    "docs/systems/perf.md": ["scripts/core/object_pool.gd", "scripts/util/sim_probe.gd",
                             "scripts/core/spike_tracer.gd", "scripts/world/plant_system.gd"],
    "docs/systems/lag-and-latency.md": ["scripts/core/object_pool.gd", "scripts/util/sim_probe.gd",
                                        "scripts/core/spike_tracer.gd", "scripts/world/plant_system.gd"],
    "docs/systems/art-pipeline.md": ["tools/slice", "tools/extract_", "assets/", "shaders/",
                                     "scripts/util/asset_slicer.gd", "tools/montage"],
    "ART_METHOD.md": ["tools/slice", "tools/extract_", "assets/", "scripts/util/asset_slicer.gd"],
    "docs/systems/tooling.md": ["tools/"],
    "docs/systems/web-standards.md": ["tools/export_upgrade_web.py", "tools/export_species_web.py",
                                      "tools/export_cloud_web.py"],
    "docs/systems/testing.md": ["tools/run_tests.py", "scripts/util/", "tools/soak_report.py",
                                "tools/progression_report.py"],
    "GODOT_FIELD_NOTES.md": ["scripts/"],
    "CLICKER_DESIGN_NOTES.md": ["data/upgrades", "scripts/core/upgrade_manager.gd", "scripts/core/meta.gd"],
}
PROCESS_FILES = {"CLAUDE.md", "WORKFLOWS.md", "SUBAGENTS.md", "NEXT_STEPS.md", "TOKEN_IDEAS.md",
                 "FUTURE_FEATURES.md", "WORKSTATION.md", "SKILLS.md", "HOOKS_METHOD.md",
                 "WIKI_METHOD.md", "SUBAGENT_METHOD.md", "REPORTING_METHOD.md",
                 "WORKFLOW_METHOD.md", "WORKSTATION_METHOD.md"}
REFERENCE_FILES = {"LORE.md", "DESCRIPTION.md", "CHANGELOG.md", "COMPLETED_STEPS.md",
                   "KNOWLEDGE_INDEX.md", "README.md"}
ARCHIVE_PREFIXES = ("docs/systems/history.md", "docs/cold/")
WHY_ORDER = ("active-unread", "current", "dormant", "process", "reference", "archive")

RUNS_HEADER = (
    "# WIKI HEAT HISTORY (append-only; one line per run).\n"
    "# Read the TAIL for recent runs - never the whole file.\n"
    "# date time | ws | files | sections | touched | cold (lines) | why: active-unread/current/dormant/process/reference/archive | hottest section\n"
)


# ---------------------------------------------------------------- the wiki

def discover_wiki_files():
    """-> {file_id: abspath}. file_id is the display/report key: bare
    basename for root files, "docs/systems/<name>" and "docs/cold/<name>"
    for the others."""
    files = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "*.md"))):
        files[os.path.basename(p)] = p
    for p in sorted(glob.glob(os.path.join(ROOT, "docs", "systems", "*.md"))):
        files["docs/systems/" + os.path.basename(p)] = p
    for p in sorted(glob.glob(os.path.join(ROOT, "docs", "cold", "*.md"))):
        files["docs/cold/" + os.path.basename(p)] = p
    return files


def build_wiki_index(wiki_files):
    """basename.lower() -> [(category, file_id), ...] for match_wiki_file."""
    index = {}
    for fid in wiki_files:
        base = os.path.basename(fid).lower()
        if fid.startswith("docs/systems/"):
            cat = "systems"
        elif fid.startswith("docs/cold/"):
            cat = "cold"
        else:
            cat = "root"
        index.setdefault(base, []).append((cat, fid))
    return index


def match_wiki_file(raw_path, wiki_index):
    """Normalize a path from a transcript event and resolve it to a current
    wiki file_id, or None. Matches by basename + subfolder, never by full
    absolute path (an older transcripts folder spells the repo path
    differently)."""
    if not raw_path:
        return None
    norm = raw_path.replace("\\", "/")
    if norm.startswith("~"):
        norm = os.path.expanduser(norm).replace("\\", "/")
    norm = norm.lower()
    if not norm.endswith(".md"):
        return None
    base = norm.rsplit("/", 1)[-1]
    candidates = wiki_index.get(base)
    if not candidates:
        return None
    has_systems = "docs/systems/" in norm
    has_cold = "docs/cold/" in norm
    for cat, fid in candidates:
        if cat == "systems" and has_systems:
            return fid
        if cat == "cold" and has_cold:
            return fid
        if cat == "root" and not has_systems and not has_cold:
            return fid
    return None


def parse_sections(abspath):
    """-> [{"heading","start","end","lines"}, ...] for the file's CURRENT
    headings, 1-based inclusive line ranges. First entry is always the
    "(preamble)" pseudo-section (0 lines if the file opens on a heading)."""
    try:
        with open(abspath, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    total = len(lines)
    headings = [(line[3:].strip(), i) for i, line in enumerate(lines, start=1)
                if line.startswith("## ")]
    first_start = headings[0][1] if headings else total + 1
    pre_end = first_start - 1
    sections = [{"heading": "(preamble)", "start": 1, "end": pre_end,
                 "lines": max(0, pre_end)}]
    for idx, (htext, start) in enumerate(headings):
        end = headings[idx + 1][1] - 1 if idx + 1 < len(headings) else total
        sections.append({"heading": htext, "start": start, "end": end,
                          "lines": max(0, end - start + 1)})
    return sections


# ------------------------------------------------------------ transcripts

def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else "WS1"


def git_activity(days):
    """-> {repo-relative path: [(date, hash), ...]} over the last `days`
    days (one read-only `git log --name-only`)."""
    try:
        out = subprocess.run(["git", "log", "--since=%d.days" % days, "--name-only",
                              "--date=short", "--format=@@ %ad %h"], cwd=ROOT,
                             capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    touches = {}
    cur = None
    for ln in out.splitlines():
        ln = ln.strip()
        if ln.startswith("@@ "):
            parts = ln.split()
            cur = (parts[1], parts[2]) if len(parts) >= 3 else None
        elif ln and cur:
            touches.setdefault(ln.replace("\\", "/"), []).append(cur)
    return touches


def classify_file(fid, activity, last_read):
    """-> (why, distinct_commits, last_commit_date). The reason a file's
    cold sections are cold. active-unread = the file's code moved AFTER the
    doc was last opened (or the doc was never opened); current = the doc was
    opened since its code last moved; dormant = the code did not move."""
    if fid.startswith(ARCHIVE_PREFIXES):
        return ("archive", 0, "")
    if fid in PROCESS_FILES:
        return ("process", 0, "")
    if fid in REFERENCE_FILES:
        return ("reference", 0, "")
    areas = AREA_MAP.get(fid)
    if not areas:
        return ("reference", 0, "")
    commits = set()
    last_commit = ""
    for path, hits in activity.items():
        low = path.lower()
        if any(low.startswith(a.lower()) for a in areas):
            for date, h in hits:
                commits.add(h)
                last_commit = max(last_commit, date)
    if not commits:
        return ("dormant", 0, "")
    if last_read and last_read >= last_commit:
        return ("current", len(commits), last_commit)
    return ("active-unread", len(commits), last_commit)


def transcript_dirs():
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(base):
        return []
    return [os.path.join(base, d) for d in os.listdir(base)
            if "everwood" in d.lower()
            and os.path.isdir(os.path.join(base, d))]


def find_transcripts():
    paths = []
    for d in transcript_dirs():
        paths.extend(glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True))
    return sorted(set(paths))


def local_day(ts):
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d")
    except (ValueError, AttributeError, TypeError):
        return None


# The read-event extractors. Each returns (kind, raw_path, a, b) or a list
# of those (Bash/PowerShell can carry more than one .md hit per command).
_SED_RE = re.compile(
    r"sed\s+-n\s+['\"]?(\d+)\s*,\s*(\d+)p['\"]?\s+([^\s'\"|;&]+\.md)",
    re.IGNORECASE)
_CLAUSE_SPLIT = re.compile(r"&&|\|\||\||;")
_WHOLE_HEAD = re.compile(r"^\s*(cat|type|get-content|gc)\b", re.IGNORECASE)
_LIMITER = re.compile(
    r"-totalcount|-tail\b|\bhead\b|\btail\b|select-object\s+-(first|last)"
    r"|select\s+-(first|last)|sed\s+-n",
    re.IGNORECASE)
_MD_TOKEN = re.compile(r"([^\s'\"]+\.md)\b", re.IGNORECASE)


def extract_read_event(tin):
    path = tin.get("file_path")
    if not path:
        return None
    offset = tin.get("offset")
    limit = tin.get("limit")
    if not offset and not limit:
        return ("whole", path, 0, 0)
    a = offset or 1
    b = (a + limit - 1) if limit else SENTINEL_EOF
    return ("section", path, a, b)


def extract_shell_events(cmd):
    if not cmd:
        return []
    events = []
    for m in _SED_RE.finditer(cmd):
        a, b, path = m.group(1), m.group(2), m.group(3).strip("'\"")
        events.append(("section", path, int(a), int(b)))
    for clause in _CLAUSE_SPLIT.split(cmd):
        clause = clause.strip()
        if not clause or not _WHOLE_HEAD.match(clause):
            continue
        if _LIMITER.search(clause):
            continue
        mt = _MD_TOKEN.search(clause)
        if not mt:
            continue
        events.append(("whole", mt.group(1).strip("'\""), 0, 0))
    return events


def extract_grep_event(tin):
    path = tin.get("path")
    if not path:
        return None
    norm = path.replace("\\", "/").lower()
    if not norm.endswith(".md"):
        return None  # a directory path (or none) - skip per spec
    return ("grep", path, 0, 0)


def parse_transcript(path, offset, wiki_index):
    """Stream one transcript from a byte offset, returning
    (new_events, new_offset). new_events = [[day, kind, file_id, a, b], ...]"""
    events = []
    with open(path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except (ValueError, UnicodeDecodeError):
                continue
            if rec.get("type") != "assistant":
                continue
            day = local_day(rec.get("timestamp") or "")
            if not day:
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for blk in content:
                if not (isinstance(blk, dict) and blk.get("type") == "tool_use"):
                    continue
                name = blk.get("name")
                tin = blk.get("input") or {}
                if not isinstance(tin, dict):
                    continue
                hits = []
                if name == "Read":
                    ev = extract_read_event(tin)
                    if ev:
                        hits = [ev]
                elif name in ("Bash", "PowerShell"):
                    hits = extract_shell_events(tin.get("command") or "")
                elif name == "Grep":
                    ev = extract_grep_event(tin)
                    if ev:
                        hits = [ev]
                for kind, raw_path, a, b in hits:
                    fid = match_wiki_file(raw_path, wiki_index)
                    if fid:
                        events.append([day, kind, fid, a, b])
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


def gather_events(wiki_index, no_cache):
    """-> (all_events, transcript_count, cache_to_write)."""
    cache = load_cache(no_cache)
    old_files = cache["files"]
    new_files = {}
    all_events = []
    paths = find_transcripts()
    for path in paths:
        key = path.replace("\\", "/")
        size = os.path.getsize(path)
        prev = None if no_cache else old_files.get(key)
        if prev and prev.get("size") == size:
            events = prev.get("events", [])  # unchanged since last run
        elif prev and size > prev.get("size", 0):
            new_events, _ = parse_transcript(path, prev.get("offset", 0), wiki_index)
            events = prev.get("events", []) + new_events
        else:
            new_events, _ = parse_transcript(path, 0, wiki_index)  # new or shrunk
            events = new_events
        # Every branch above reads through to EOF, so the resume offset for
        # next time is simply the current size.
        new_files[key] = {"size": size, "offset": size, "events": events}
        all_events.extend(events)
    cache_out = {"version": CACHE_VERSION, "files": new_files}
    return all_events, len(paths), cache_out


# ------------------------------------------------------------- reporting

def newer(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def pad_rows(rows, pad_cols):
    """rows: list of list-of-str. pad_cols: how many leading columns to
    ljust to the widest in that column; remaining columns pass through."""
    if not rows:
        return []
    widths = [max(len(r[i]) for r in rows) for i in range(pad_cols)]
    out = []
    for r in rows:
        head = [r[i].ljust(widths[i]) for i in range(pad_cols)]
        out.append(" | ".join(head + r[pad_cols:]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30,
                     help="a section with no read in this many days counts cold")
    ap.add_argument("--top", type=int, default=20, help="hot-section row count")
    ap.add_argument("--no-cache", action="store_true", help="rebuild the parse cache")
    args = ap.parse_args()

    wiki_files = discover_wiki_files()
    wiki_index = build_wiki_index(wiki_files)
    section_map = {fid: parse_sections(abspath) for fid, abspath in wiki_files.items()}
    for sects in section_map.values():
        for s in sects:
            s["sectioned"] = 0
            s["last_touch"] = None

    all_events, transcript_n, cache_out = gather_events(wiki_index, args.no_cache)

    file_stats = {fid: {"whole": 0, "sectioned": 0, "grep": 0, "last": None}
                  for fid in wiki_files}
    for day, kind, fid, a, b in all_events:
        fs = file_stats.get(fid)
        sects = section_map.get(fid)
        if fs is None or sects is None:
            continue  # file no longer in the wiki
        fs["last"] = newer(fs["last"], day)
        if kind == "whole":
            fs["whole"] += 1
            for s in sects:
                s["last_touch"] = newer(s["last_touch"], day)
        elif kind == "section":
            fs["sectioned"] += 1
            for s in sects:
                if a <= s["end"] and b >= s["start"]:
                    s["sectioned"] += 1
                    s["last_touch"] = newer(s["last_touch"], day)
        elif kind == "grep":
            fs["grep"] += 1

    # -- FILES table
    file_rows = []
    never_read = []
    for fid, fs in file_stats.items():
        total = fs["whole"] + fs["sectioned"] + fs["grep"]
        if total == 0:
            never_read.append(fid)
        else:
            file_rows.append((total, fid, fs))
    file_rows.sort(key=lambda r: -r[0])
    files_lines = pad_rows(
        [[fid, "whole %d" % fs["whole"], "sectioned %d" % fs["sectioned"],
          "grep %d" % fs["grep"], "last %s" % (fs["last"] or "never")]
         for _, fid, fs in file_rows], 4)

    # -- HOT sections
    all_sections = []
    for fid, sects in section_map.items():
        fw = file_stats[fid]["whole"]
        for s in sects:
            all_sections.append((fid, s, fw))
    hot = [(fid, s, fw) for fid, s, fw in all_sections if s["sectioned"] > 0]
    hot.sort(key=lambda r: -r[1]["sectioned"])
    hot = hot[:args.top]
    hot_lines = pad_rows(
        [[str(s["sectioned"]), str(fw), s["last_touch"] or "never",
          "%s#%s" % (fid, s["heading"])] for fid, s, fw in hot], 3)

    # -- COLD sections
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=args.days)).strftime("%Y-%m-%d")
    cold = []
    for fid, s, fw in all_sections:
        if s["heading"] == "(preamble)" or s["lines"] < 6:
            continue
        # A whole-file read within the window counts: the section was seen.
        # (Before 2026-09-10 "never sectioned-read" alone made a section cold,
        # which called fauna.md cold after five whole reads.)
        is_cold = (not s["last_touch"]) or (s["last_touch"] < cutoff)
        if is_cold:
            cold.append((fid, s))
    cold.sort(key=lambda r: -r[1]["lines"])
    cold_lines = pad_rows(
        [["%d lines" % s["lines"], "last %s" % (s["last_touch"] or "never"),
          "%s#%s" % (fid, s["heading"])] for fid, s in cold], 2)

    # -- WHY COLD (the learning: which cold is expected, which deserves a look)
    activity = git_activity(args.days)
    why_of = {fid: classify_file(fid, activity, file_stats[fid]["last"]) for fid in wiki_files}
    why_counts = {w: 0 for w in WHY_ORDER}
    why_files = {}
    for fid, s in cold:
        why, hits, last_commit = why_of[fid]
        why_counts[why] += 1
        wf = why_files.setdefault(fid, {"why": why, "hits": hits, "n": 0, "lines": 0,
                                        "last_commit": last_commit})
        wf["n"] += 1
        wf["lines"] += s["lines"]
    why_rows = sorted(why_files.items(),
                      key=lambda kv: (WHY_ORDER.index(kv[1]["why"]), -kv[1]["n"]))
    why_lines = pad_rows(
        [[wf["why"], "%d cold" % wf["n"], "%d lines" % wf["lines"],
          "code: %d commits, last %s" % (wf["hits"], wf["last_commit"] or "-"),
          "doc last read %s" % (file_stats[fid]["last"] or "never"), fid]
         for fid, wf in why_rows], 5)
    why_summary = ", ".join("%s %d" % (w, why_counts[w]) for w in WHY_ORDER)

    sections_total = sum(len(s) for s in section_map.values())
    touched = sum(1 for _, s, _ in all_sections if s["last_touch"])
    cold_total_lines = sum(s["lines"] for _, s in cold)
    summary = ("files %d | sections %d | touched %d | cold %d (%d lines) "
               "| why: %s | events %d | transcripts %d") % (
        len(wiki_files), sections_total, touched, len(cold), cold_total_lines,
        why_summary, len(all_events), transcript_n)

    # -- write the report
    lines = [
        "# GENERATED by tools/wiki_heat.py - read counts per wiki file and "
        "section, mined from the harness transcripts; never hand-edit",
        "# Section mapping uses the CURRENT headings (approximate for old "
        "reads). Cold = candidates only; NOTHING MOVES WITHOUT THE OWNER'S "
        "WORD (the preservation law).",
        "",
        "== FILES (whole | sectioned | grep hits | last read)",
    ]
    lines.extend(files_lines)
    if never_read:
        lines.append("never read: " + ", ".join(sorted(never_read)))
    else:
        lines.append("never read: (none)")
    lines.append("")
    lines.append("== HOT SECTIONS (top %d by sectioned reads)" % args.top)
    lines.extend(hot_lines if hot_lines else ["(none read sectioned yet)"])
    lines.append("")
    lines.append("== COLD SECTIONS (0 sectioned reads ever, or last touch "
                  "older than %d days)" % args.days)
    lines.extend(cold_lines if cold_lines else ["(none)"])
    lines.append("")
    lines.append("== WHY COLD (per file: class | cold sections | lines | commits in its "
                 "code area over %d days + the last one | when the doc was last opened) - "
                 "active-unread (code moved AFTER the doc was last opened) is the only "
                 "class worth a look; current, dormant, process, reference and archive "
                 "cold is expected in a game project (Mazhron 2026-09-10)" % args.days)
    lines.extend(why_lines if why_lines else ["(none)"])
    lines.append("")
    lines.append("== SUMMARY")
    lines.append(summary)
    lines.append("")

    with open(OUT_TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    # -- ledger line
    if all_sections:
        hot_fid, hot_s, _ = max(all_sections, key=lambda r: r[1]["sectioned"])
        hottest = "%s#%s (%d)" % (hot_fid, hot_s["heading"], hot_s["sectioned"])
    else:
        hottest = "n/a"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ledger_line = ("%s | %s | files %d | sections %d | touched %d | "
                   "cold %d (%d lines) | why: %s | hottest %s") % (
        now, workstation(), len(wiki_files), sections_total, touched,
        len(cold), cold_total_lines, why_summary, hottest)
    if not os.path.isfile(RUNS_TXT):
        with open(RUNS_TXT, "w", encoding="utf-8") as fh:
            fh.write(RUNS_HEADER)
    with open(RUNS_TXT, "a", encoding="utf-8") as fh:
        fh.write(ledger_line + "\n")

    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache_out, fh)

    print(summary)
    for row in cold_lines[:10]:
        print(row)


if __name__ == "__main__":
    sys.exit(main())

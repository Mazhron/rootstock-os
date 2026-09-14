"""THE CORE DIET (the CEO's ruling 2026-09-14, after a Reddit reader measured
the kit's front door at ~5k tokens: "CLAUDE.md is the main index that keeps
the most used information (similar to your heatmap concept) and once they
fall out of the high-use heatmap, they get moved (by script) to the
appropriate index out of CLAUDE.md ... These indexes can grow much more
than the CLAUDE.md file").

CLAUDE.md is loaded IN FULL every session - it is the one standing cost.
This script keeps it the HOT CORE and nothing else:

  * every "## " / "### " section of CLAUDE.md is a UNIT;
  * a unit's HEAT over the window (default 30 days, .claude/trend_limits.json
    "core_cold_days") = explicit reads of its lines (wiki_heat's transcript
    cache) + reads of the wiki files it points at (its "follows") + whether
    git touched it inside the window;
  * a unit that carries an `Index: <name>` line is ROUTED to the sub-index
    docs/index/<name>.md (`Index: core` pins it - never moved by the loop);
  * `--move` (the loop's mode, metrics group) moves every COLD routed unit
    VERBATIM to its sub-index and, while CLAUDE.md is still over its token
    budget (check_claude_md.TOKEN_BUDGET), the coldest routed units next,
    lowest heat first; each move leaves ONE line in CLAUDE.md's
    "## The sub-indexes" block: `- <heading> -> docs/index/<name>.md | brief`
    (the brief is the unit's Tags line brief, so the core still states the
    law in a sentence), so every moved section stays findable by grep;
  * a COLD unit with no Index: line is only PROPOSED - a human names its
    home (the wiki convention: headings are search keys, a human files);
  * `--move-section "<heading>"` moves one unit now regardless of heat (the
    manager's explicit call, like cold_shelf's --move); `--restore
    "<heading>"` brings it back after the unit it originally followed.

NOTHING IS DELETED (THE PRESERVATION LAW): a move is verbatim, stubbed,
ledgered and reversible; the sub-index files grow without limit and are
themselves wiki files (headings are search keys, See-also lines inside each
section connect it to its knowledge files). The wiki scanners (wiki_heat,
check_wiki_links, export_tag_index, export_wiki_view, cold_shelf) discover
docs/index/*.md as wiki files.

Outputs:
  docs/history/core_diet.txt       regenerated report: every unit, its
                                    tokens, reads, follows, last edit, route,
                                    verdict; the PROPOSE lines
  docs/history/core_diet_runs.txt  append-only ledger, one line per run

Usage:
    python tools/core_diet.py                       # report + ledger (nothing moves)
    python tools/core_diet.py --move                # the loop's mode: move cold routed units, then to budget
    python tools/core_diet.py --move --dry-run      # say what would move
    python tools/core_diet.py --move-section "The checkpoint protocol" --reason "..."
    python tools/core_diet.py --restore "The checkpoint protocol"
    python tools/core_diet.py --selftest            # temp-dir round trip: move, stub, restore

PURPOSE: Measure the heat of every CLAUDE.md section from the transcript
  read cache, git recency and pointer follows, report it, and move cold or
  over-budget routed sections verbatim into named sub-index files under
  docs/index/ leaving a one-line stub, with an explicit move and a restore,
  so the always-loaded core stays inside its token budget by script.
INTENT: the CEO 2026-09-14: "make something so that this doesn't happen
  again ... CLAUDE.md is the main index that keeps the most used information
  ... once they fall out of the high-use heatmap, they get moved (by script)
  to the appropriate index out of CLAUDE.md to keep CLAUDE.md even more
  [lean]. These indexes can grow much more than the CLAUDE.md file."

Search keys: core diet, CLAUDE.md budget, sub-index, docs/index, hot core,
  section heat, move section, restore section, token budget, lean core
See also: tools/check_claude_md.py (the token budget it serves);
  tools/wiki_heat.py (the read cache it reuses); tools/cold_shelf.py (the
  sibling mover for rarely-read topic sections); WIKI_METHOD.md "The hot
  core and the sub-indexes"; WORKFLOWS.md "Diet the core (move a CLAUDE.md
  section to a sub-index)"; docs/systems/self-audit.md.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CORE_NAME = "CLAUDE.md"
INDEX_DIRNAME = os.path.join("docs", "index")
BLOCK_HEADING = "## The sub-indexes"
BLOCK_INTRO = ("(moved out by tools/core_diet.py, verbatim: heading -> sub-index | brief; "
               "`--restore \"<heading>\"` brings one back)")
DEFAULT_COLD_DAYS = 30
PROVENANCE = "<!-- core diet: moved from {core} on {day}, level {level}, after \"{after}\", reason: {reason}, {n} lines -->"
RESTORED = "<!-- core diet: \"{heading}\" restored to {core} on {day} -->"

INDEX_FILE_HEADER = (
    "# {title} index - sections moved out of CLAUDE.md by the core diet\n"
    "\n"
    "PURPOSE: hold the {name} sections that no longer earn a place in the\n"
    "  always-loaded core, verbatim, each heading a search key, each\n"
    "  section's See-also lines pointing at its knowledge files.\n"
    "INTENT: CLAUDE.md is the hot core (the CEO 2026-09-14); a sub-index\n"
    "  grows without limit and is read by section, on demand, never whole.\n"
    "\n"
    "Search keys: {name} index, sub-index, core diet, moved from CLAUDE.md.\n"
    "See also: CLAUDE.md (the hot core, \"The sub-indexes\" block);\n"
    "  WIKI_METHOD.md \"The hot core and the sub-indexes\"; tools/core_diet.py.\n"
)


# ----------------------------------------------------------------- helpers

def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else "WS1"


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def est_tokens(text):
    return len(text.encode("utf-8")) // 4


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def cold_days(root):
    """The window, from .claude/trend_limits.json when present."""
    path = os.path.join(root, ".claude", "trend_limits.json")
    try:
        data = json.load(open(path, encoding="utf-8"))
        return int(data.get("core_cold_days", DEFAULT_COLD_DAYS))
    except (OSError, ValueError, TypeError):
        return DEFAULT_COLD_DAYS


def token_budget():
    try:
        import check_claude_md  # noqa: F401  (the budget lives with the lint)
        return int(getattr(check_claude_md, "TOKEN_BUDGET", 3500))
    except Exception:
        return 3500


# ------------------------------------------------------------------- units

def parse_units(lines):
    """Every '## ' or '### ' heading through the line before the next
    heading of level 2 or 3. lines = splitlines(keepends=True).
    -> [{start, end, level, heading, normalized, route, brief}]"""
    idxs = [i for i, ln in enumerate(lines)
            if ln.startswith("## ") or ln.startswith("### ")]
    units = []
    for n, start in enumerate(idxs):
        end = idxs[n + 1] if n + 1 < len(idxs) else len(lines)
        ln = lines[start].rstrip("\r\n")
        level = 3 if ln.startswith("### ") else 2
        heading = ln[level + 1:].strip()
        body = "".join(lines[start + 1:end])
        route = None
        m = re.search(r"^Index:\s*([\w.-]+)\s*$", body, re.M)
        if m:
            route = m.group(1).lower()
        brief = ""
        mt = re.search(r"^Tags:[^|\n]*\|\s*(.+)$", body, re.M)
        if mt:
            brief = mt.group(1).strip()
        units.append({"start": start, "end": end, "level": level,
                      "heading": heading, "normalized": normalize(heading),
                      "route": route, "brief": brief,
                      "tokens": est_tokens("".join(lines[start:end]))})
    return units


def find_unit(units, query):
    q = normalize(query)
    for u in units:
        if u["normalized"] == q:
            return u
    hits = [u for u in units if q in u["normalized"]]
    return hits[0] if len(hits) == 1 else None


# -------------------------------------------------------------------- heat

def wiki_events(root, days):
    """{file_id: [(kind, a, b), ...]} inside the window, from wiki_heat's
    cache (rebuilt through wiki_heat's own gather when importable)."""
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    events = []
    try:
        import wiki_heat
        files = wiki_heat.discover_wiki_files()
        index = wiki_heat.build_wiki_index(files)
        all_events, _, cache = wiki_heat.gather_events(index, False)
        try:
            with open(wiki_heat.CACHE_PATH, "w", encoding="utf-8") as fh:
                json.dump(cache, fh)
        except OSError:
            pass
        events = all_events
    except Exception:
        cache_path = os.path.join(root, "docs", "history", "wiki_heat_cache.json")
        try:
            cache = json.load(open(cache_path, encoding="utf-8"))
            for rec in cache.get("files", {}).values():
                events.extend(rec.get("events", []))
        except (OSError, ValueError):
            events = []
    out = {}
    for day, kind, fid, a, b in events:
        if day >= since:
            out.setdefault(fid, []).append((kind, a, b))
    return out


def unit_reads(unit, core_events):
    """Explicit reads whose line range overlaps the unit (1-based)."""
    lo, hi = unit["start"] + 1, unit["end"]
    n = 0
    for kind, a, b in core_events:
        if kind == "whole":
            n += 1
        elif kind == "section":
            if b == 0:
                b = 10 ** 9
            if a <= hi and b >= lo:
                n += 1
    return n


def unit_follows(text, events, self_id):
    """Reads of every wiki file the unit names (basename match)."""
    n = 0
    for fid, evs in events.items():
        if fid == self_id:
            continue
        base = os.path.basename(fid)
        if fid.startswith("docs/") and fid in text:
            n += len(evs)
        elif not fid.startswith("docs/") and re.search(r"(?<![\w/])" + re.escape(base), text):
            n += len(evs)
    return n


def unit_edit_age(root, core_path, unit):
    """Days since git last touched any line of the unit, or None."""
    lo, hi = unit["start"] + 1, unit["end"]
    try:
        out = subprocess.run(
            ["git", "blame", "--line-porcelain", "-L", "%d,%d" % (lo, hi),
             "--", os.path.relpath(core_path, root)],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    newest = 0
    for ln in out.stdout.splitlines():
        if ln.startswith("committer-time "):
            try:
                newest = max(newest, int(ln.split()[1]))
            except ValueError:
                pass
    if not newest:
        return None
    then = datetime.date.fromtimestamp(newest)
    return (datetime.date.today() - then).days


def measure(root, core_path, days):
    text = read_text(core_path)
    lines = text.splitlines(keepends=True)
    units = parse_units(lines)
    events = wiki_events(root, days)
    core_events = events.get(CORE_NAME, [])
    for u in units:
        body = "".join(lines[u["start"]:u["end"]])
        u["reads"] = unit_reads(u, core_events)
        u["follows"] = unit_follows(body, events, CORE_NAME)
        age = unit_edit_age(root, core_path, u)
        u["edit_age"] = age
        u["edited"] = age is not None and age <= days
        u["heat"] = u["reads"] * 3 + u["follows"] + (1 if u["edited"] else 0)
        u["hot"] = u["reads"] > 0 or u["follows"] > 0 or u["edited"]
        if u["normalized"] == normalize(BLOCK_HEADING[3:]):
            u["route"] = "core"
    return text, lines, units


# ------------------------------------------------------------------- moves

def index_path(root, name):
    return os.path.join(root, INDEX_DIRNAME, name + ".md")


def block_span(lines):
    """(start, end) of the sub-indexes block, or None."""
    for i, ln in enumerate(lines):
        if ln.rstrip("\r\n") == BLOCK_HEADING:
            j = i + 1
            while j < len(lines) and not (lines[j].startswith("## ") or lines[j].startswith("### ")):
                j += 1
            return i, j
    return None


def ensure_block(lines, nl):
    span = block_span(lines)
    if span:
        return lines
    add = [nl, BLOCK_HEADING + nl, BLOCK_INTRO + nl, nl]
    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] = lines[-1] + nl
    return lines + add


def stub_line(unit, name):
    line = "- %s -> %s/%s.md" % (unit["heading"], INDEX_DIRNAME.replace("\\", "/"), name)
    if unit["brief"]:
        line += " | " + unit["brief"]
    return line


def move_unit(root, core_path, lines, unit, name, reason, dry_run, nl="\n"):
    """Move one unit verbatim to docs/index/<name>.md; stub it in the
    block. Returns the new core lines (or the old ones on dry run)."""
    units = parse_units(lines)
    prev = None
    for u in units:
        if u["start"] < unit["start"]:
            prev = u
    after = prev["heading"] if prev else "(top)"
    target = index_path(root, name)
    rel_target = "%s/%s.md" % (INDEX_DIRNAME.replace("\\", "/"), name)
    n = unit["end"] - unit["start"]
    if dry_run:
        print("[dry-run] would move %d lines (~%d tokens): %s -> %s" % (
            n, unit["tokens"], unit["heading"], rel_target))
        return lines
    if os.path.isfile(target):
        existing = read_text(target)
        if any(normalize(h) == unit["normalized"]
               for h in re.findall(r"^## (.+)$", existing, re.M)):
            print("SKIP %s: %s already holds that heading" % (unit["heading"], rel_target))
            return lines
    else:
        existing = INDEX_FILE_HEADER.format(title=name.capitalize(), name=name)
    today = datetime.date.today().isoformat()
    prov = PROVENANCE.format(core=CORE_NAME, day=today, level=unit["level"],
                             after=after, reason=reason, n=n)
    body = "".join(lines[unit["start"] + 1:unit["end"]])
    addition = nl + "## " + unit["heading"] + nl + prov + nl + body
    if not addition.endswith(nl):
        addition += nl
    write_text(target, existing + addition)
    new_lines = lines[:unit["start"]] + lines[unit["end"]:]
    new_lines = ensure_block(new_lines, nl)
    bstart, bend = block_span(new_lines)
    insert_at = bend
    while insert_at > bstart + 1 and new_lines[insert_at - 1].strip() == "":
        insert_at -= 1
    new_lines = new_lines[:insert_at] + [stub_line(unit, name) + nl] + new_lines[insert_at:]
    print("MOVED %d lines (~%d tokens): %s -> %s" % (n, unit["tokens"], unit["heading"], rel_target))
    return new_lines


def restore_unit(root, core_path, heading, dry_run):
    core_text = read_text(core_path)
    nl = "\r\n" if "\r\n" in core_text else "\n"
    lines = core_text.splitlines(keepends=True)
    idx_dir = os.path.join(root, INDEX_DIRNAME)
    q = normalize(heading)
    found = None
    for fn in sorted(os.listdir(idx_dir)) if os.path.isdir(idx_dir) else []:
        if not fn.endswith(".md"):
            continue
        path = os.path.join(idx_dir, fn)
        text = read_text(path)
        ilines = text.splitlines(keepends=True)
        hidx = [i for i, ln in enumerate(ilines) if ln.startswith("## ")]
        for k, i in enumerate(hidx):
            if normalize(ilines[i][3:]) == q:
                end = hidx[k + 1] if k + 1 < len(hidx) else len(ilines)
                found = (path, ilines, i, end)
                break
        if found:
            break
    if not found:
        sys.exit("restore: no docs/index section titled %r" % heading)
    path, ilines, i, end = found
    prov = ilines[i + 1].rstrip("\r\n") if i + 1 < end else ""
    m = re.search(r'level (\d), after "(.*?)", reason', prov)
    level = int(m.group(1)) if m else 2
    after = m.group(2) if m else "(top)"
    body = ilines[i + 2:end] if m else ilines[i + 1:end]
    unit_lines = ["#" * level + " " + ilines[i][3:]] + body
    if unit_lines and not unit_lines[-1].endswith(("\n", "\r")):
        unit_lines[-1] += nl
    if dry_run:
        print("[dry-run] would restore %d lines: %s -> %s after %r" % (
            len(unit_lines), heading, CORE_NAME, after))
        return
    today = datetime.date.today().isoformat()
    note = RESTORED.format(heading=ilines[i][3:].rstrip("\r\n"), core=CORE_NAME, day=today) + nl
    new_index = ilines[:i] + ["## " + ilines[i][3:], note, nl] + ilines[end:]
    write_text(path, "".join(new_index))
    # drop the stub line, put the unit back after the unit it followed
    stub = "- %s ->" % ilines[i][3:].rstrip("\r\n")
    lines = [ln for ln in lines if not ln.startswith(stub)]
    units = parse_units(lines)
    at = len(lines)
    if after != "(top)":
        for u in units:
            if u["normalized"] == normalize(after):
                at = u["end"]
                break
    else:
        at = units[0]["start"] if units else 0
    if at > 0 and lines[at - 1].strip() != "":
        unit_lines = [nl] + unit_lines
    if at < len(lines) and unit_lines[-1].strip() != "" and lines[at].strip() != "":
        unit_lines.append(nl)
    new_core = lines[:at] + unit_lines + lines[at:]
    write_text(core_path, "".join(new_core))
    print("RESTORED %s -> %s (after %r); note left in %s" % (
        heading, CORE_NAME, after, os.path.relpath(path, root)))


# ------------------------------------------------------------------ report

def write_report(root, units, days, budget, core_tokens, proposals, moved):
    hist = os.path.join(root, "docs", "history")
    os.makedirs(hist, exist_ok=True)
    out = []
    out.append("# THE CORE DIET - CLAUDE.md section heat (tools/core_diet.py; regenerated whole each run)")
    out.append("# window %d days | core ~%d tokens | budget %d | %s" % (
        days, core_tokens, budget, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    out.append("# heading | level | ~tokens | reads | follows | last edit (days) | route | verdict")
    for u in units:
        age = "-" if u["edit_age"] is None else str(u["edit_age"])
        route = u["route"] or "(unrouted)"
        verdict = "pinned" if u["route"] == "core" else ("HOT" if u["hot"] else "COLD")
        out.append("%s | %d | %d | %d | %d | %s | %s | %s" % (
            u["heading"], u["level"], u["tokens"], u["reads"], u["follows"], age, route, verdict))
    out.append("")
    if moved:
        out.append("== MOVED THIS RUN")
        out.extend("  " + m for m in moved)
    if proposals:
        out.append("== PROPOSE (the owner rules; nothing here is applied)")
        out.extend("  " + p for p in proposals)
    else:
        out.append("== PROPOSE: none")
    write_text(os.path.join(hist, "core_diet.txt"), "\n".join(out) + "\n")


def ledger_line(root, core_tokens, core_lines, units, moved, budget):
    hist = os.path.join(root, "docs", "history")
    path = os.path.join(hist, "core_diet_runs.txt")
    if not os.path.isfile(path):
        write_text(path, "# THE CORE DIET (append-only): one line per run. date time | ws | "
                         "core ~tokens (lines) | units | hot | cold | cold-unrouted | moved | budget\n")
    hot = sum(1 for u in units if u["hot"] and u["route"] != "core")
    cold = sum(1 for u in units if not u["hot"] and u["route"] != "core")
    unrouted = sum(1 for u in units if not u["hot"] and not u["route"])
    line = "%s | %s | ~%d (%d) | %d | %d | %d | %d | %d | %d\n" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), workstation(),
        core_tokens, core_lines, len(units), hot, cold, unrouted, len(moved), budget)
    try:
        import _ledger
        _ledger.append_unless_identical(path, line)
    except Exception:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    return line.rstrip()


# -------------------------------------------------------------------- main

def run(root, do_move, dry_run, reason):
    core_path = os.path.join(root, CORE_NAME)
    days = cold_days(root)
    budget = token_budget()
    text, lines, units = measure(root, core_path, days)
    nl = "\r\n" if "\r\n" in text else "\n"
    moved = []
    proposals = []
    if do_move:
        cold_routed = [u for u in units if not u["hot"] and u["route"] and u["route"] != "core"]
        for u in cold_routed:
            cur = find_unit(parse_units(lines), u["heading"])  # indexes shift after each move
            if not cur:
                continue
            before = len(lines)
            lines = move_unit(root, core_path, lines, cur, cur["route"],
                              reason or "cold for %d days" % days, dry_run, nl)
            if len(lines) != before or dry_run:
                moved.append("%s -> %s (cold)" % (cur["heading"], cur["route"]))
        # over budget: coldest routed units next
        core_tokens = est_tokens("".join(lines))
        if core_tokens > budget:
            routed = [u for u in measure_lines(root, core_path, lines, days)
                      if u["route"] and u["route"] != "core"]
            routed.sort(key=lambda u: (u["heat"], -(u["edit_age"] or 0)))
            for u in routed:
                if core_tokens <= budget:
                    break
                cur = find_unit(parse_units(lines), u["heading"])
                if not cur:
                    continue
                lines = move_unit(root, core_path, lines, cur, cur["route"],
                                  reason or "over budget (%d > %d tokens)" % (core_tokens, budget),
                                  dry_run, nl)
                moved.append("%s -> %s (budget)" % (cur["heading"], cur["route"]))
                core_tokens = est_tokens("".join(lines)) if not dry_run else core_tokens - cur["tokens"]
        if moved and not dry_run:
            write_text(core_path, "".join(lines))
            text, lines, units = measure(root, core_path, days)
    core_tokens = est_tokens(text)
    for u in units:
        if not u["hot"] and not u["route"]:
            proposals.append("PROPOSE (core_diet): \"%s\" (~%d tokens) is COLD for %d days and has no "
                             "Index: line - add `Index: <name>` (its sub-index) or `Index: core` (pin it)"
                             % (u["heading"], u["tokens"], days))
    if core_tokens > budget:
        proposals.append("PROPOSE (core_diet): CLAUDE.md is ~%d tokens (budget %d) and nothing routed "
                         "is left to move - route more sections or shorten what stays"
                         % (core_tokens, budget))
    if dry_run:
        print("[dry-run] CLAUDE.md ~%d tokens now (budget %d); %d move(s) planned; nothing written, "
              "no ledger line" % (core_tokens, budget, len(moved)))
        return 0
    write_report(root, units, days, budget, core_tokens, proposals, moved)
    line = ledger_line(root, core_tokens, len(lines), units, moved, budget)
    print("CORE DIET: CLAUDE.md ~%d tokens (%d lines, budget %d) | units %d | hot %d | cold %d | moved %d"
          % (core_tokens, len(lines), budget, len(units),
             sum(1 for u in units if u["hot"]), sum(1 for u in units if not u["hot"]), len(moved)))
    for p in proposals:
        print("  " + p)
    print("  ledger: " + line)
    return 0


def measure_lines(root, core_path, lines, days):
    """Heat for an in-memory version of the core (after moves)."""
    units = parse_units(lines)
    events = wiki_events(root, days)
    core_events = events.get(CORE_NAME, [])
    for u in units:
        body = "".join(lines[u["start"]:u["end"]])
        u["reads"] = unit_reads(u, core_events)
        u["follows"] = unit_follows(body, events, CORE_NAME)
        u["edit_age"] = None
        u["edited"] = False
        u["heat"] = u["reads"] * 3 + u["follows"]
        u["hot"] = u["reads"] > 0 or u["follows"] > 0
        if u["normalized"] == normalize(BLOCK_HEADING[3:]):
            u["route"] = "core"
    return units


def move_section(root, heading, reason, dry_run):
    core_path = os.path.join(root, CORE_NAME)
    text = read_text(core_path)
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    units = parse_units(lines)
    u = find_unit(units, heading)
    if not u:
        sys.exit("move-section: no CLAUDE.md section matches %r (headings: %s)" % (
            heading, "; ".join(x["heading"] for x in units)))
    if not u["route"]:
        sys.exit("move-section: %r has no `Index: <name>` line - add one so the script knows its home" % u["heading"])
    if u["route"] == "core":
        sys.exit("move-section: %r is pinned (Index: core)" % u["heading"])
    new_lines = move_unit(root, core_path, lines, u, u["route"], reason or "manager's call", dry_run, nl)
    if not dry_run and new_lines is not lines:
        write_text(core_path, "".join(new_lines))
    return 0


def selftest():
    tmp = tempfile.mkdtemp(prefix="core_diet_")
    core = os.path.join(tmp, CORE_NAME)
    write_text(core, "# T\n\nintro\n\n## Keep\nIndex: core\nstays\n\n## Laws\n\n### Rule A\nTags: x | brief A\nIndex: laws\nbody A\n\n### Rule B\nIndex: laws\nbody B\n\n## Tail\nend\n")
    lines = read_text(core).splitlines(keepends=True)
    units = parse_units(lines)
    ok = True
    def check(cond, label):
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + label)
        ok = ok and cond
    check([u["heading"] for u in units] == ["Keep", "Laws", "Rule A", "Rule B", "Tail"], "units parsed")
    check(units[2]["route"] == "laws" and units[2]["brief"] == "brief A", "route + brief read")
    new = move_unit(tmp, core, lines, units[2], "laws", "test", False)
    write_text(core, "".join(new))
    idx = read_text(index_path(tmp, "laws"))
    check("## Rule A" in idx and "body A" in idx and "core diet: moved" in idx, "moved verbatim with provenance")
    core_text = read_text(core)
    check("body A" not in core_text and "- Rule A -> docs/index/laws.md | brief A" in core_text, "stub line in the block")
    check(BLOCK_HEADING in core_text, "block created")
    restore_unit(tmp, core, "Rule A", False)
    core_text = read_text(core)
    check("### Rule A" in core_text and "body A" in core_text and "- Rule A ->" not in core_text, "restored, stub gone")
    check(core_text.index("### Rule A") > core_text.index("## Laws") and core_text.index("### Rule A") < core_text.index("### Rule B"), "restored after the unit it followed")
    check("restored to CLAUDE.md" in read_text(index_path(tmp, "laws")), "index keeps a restored note")
    print("core_diet selftest: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="THE CORE DIET: CLAUDE.md section heat + moves to docs/index/")
    ap.add_argument("--move", action="store_true", help="move cold routed units, then the coldest until under budget")
    ap.add_argument("--move-section", metavar="HEADING", help="move one routed unit now, regardless of heat")
    ap.add_argument("--restore", metavar="HEADING", help="bring a moved unit back into CLAUDE.md")
    ap.add_argument("--reason", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.restore:
        restore_unit(args.root, os.path.join(args.root, CORE_NAME), args.restore, args.dry_run)
        return 0
    if args.move_section:
        return move_section(args.root, args.move_section, args.reason, args.dry_run)
    return run(args.root, args.move, args.dry_run, args.reason)


if __name__ == "__main__":
    sys.exit(main())

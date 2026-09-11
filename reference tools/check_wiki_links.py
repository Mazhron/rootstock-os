"""Warn-only link checker for the knowledge wiki.

    python tools/check_wiki_links.py             # scan + report + regen ledger
    python tools/check_wiki_links.py --strict     # exit 1 when dead > 0
    python tools/check_wiki_links.py --quiet      # print only the summary line

THE WIKI: repo-root *.md (non-recursive) + docs/systems/*.md + docs/cold/*.md
(skipped if absent). Cross-references come in four forms:

  (a) "See also:" paragraphs - a line starting "See also:" plus continuation
      lines until a blank line, a "## " heading, or end of file. File tokens
      inside (ending .md/.py/.gd/.gdshader/.tscn/.json) are the links; bare
      topic words ("this file", "above") carry no file and are ignored.
  (b) [[name]] wiki links - resolve against any wiki file's basename.
  (c) markdown [text](relative/path) links - schemeless paths only.
  (d) in CLAUDE.md only, every "docs/systems/<name>.md" mention.

RESOLUTION: repo-root-relative, then relative to the referencing file's own
directory, then by BASENAME anywhere under the wiki's search roots (repo
root *.md, docs/**, tools/**, scripts/**, shaders/**, data/**, scenes/**,
.claude/**). A token resolved only by basename (its written path does not
exist) is reported OK but counted separately, never as dead.

Also tallies HYGIENE: per docs/systems/*.md file, how many "## " sections
have no "See also:" line before the next heading (informational only).

This script is warn-only by law: it never deletes anything, only regenerates
its own two output files (docs/history/wiki_links.txt overwritten each run,
docs/history/wiki_link_runs.txt appended to).

Search keys: wiki links, dead links, see also, link checker, hygiene.
See also: docs/systems/tooling.md (the wiki tooling); WIKI_METHOD.md (the
conventions); tools/run_all.py (check group).
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "history", "wiki_links.txt")
RUNS = os.path.join(ROOT, "docs", "history", "wiki_link_runs.txt")
RUNS_HEADER = (
    "# WIKI LINK CHECK HISTORY (append-only; one line per run).\n"
    "# Read the TAIL for recent runs - never the whole file.\n"
    "# date time | ws | files | links | dead | by-basename | sections without See-also | first dead targets\n"
)

TOKEN_EXT_RE = re.compile(
    r"[\w][\w./-]*\.(?:md|py|gd|gdshader|tscn|json)\b", re.UNICODE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKIP_ROOT_WALK = {".git", ".godot", "__pycache__"}
SEARCH_ROOTS = ["docs", "tools", "scripts", "shaders", "data", "scenes", "Future Project MDs",
                 os.path.join(".claude")]


def strip_punct(tok):
    return tok.strip().strip(")];,.|:")


def wiki_files():
    files = []
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if name.endswith(".md") and os.path.isfile(p):
            files.append(p)
    sysdir = os.path.join(ROOT, "docs", "systems")
    if os.path.isdir(sysdir):
        for name in sorted(os.listdir(sysdir)):
            if name.endswith(".md"):
                files.append(os.path.join(sysdir, name))
    colddir = os.path.join(ROOT, "docs", "cold")
    if os.path.isdir(colddir):
        for name in sorted(os.listdir(colddir)):
            if name.endswith(".md"):
                files.append(os.path.join(colddir, name))
    return files


def build_basename_map():
    """basename (lower) -> list of repo-relative paths, across search roots."""
    bmap = {}

    def add(path):
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        bmap.setdefault(os.path.basename(path).lower(), []).append(rel)

    for name in os.listdir(ROOT):
        p = os.path.join(ROOT, name)
        if name.endswith(".md") and os.path.isfile(p):
            add(p)

    for root_name in SEARCH_ROOTS:
        base = os.path.join(ROOT, root_name)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_ROOT_WALK]
            for fn in filenames:
                add(os.path.join(dirpath, fn))
    return bmap


def resolve(token, ref_dir, bmap):
    """Return (status, resolved_path_or_None). status in OK/BASENAME/DEAD."""
    tok = token.replace("\\", "/").lstrip("./")
    # (1) repo-root relative
    cand = os.path.normpath(os.path.join(ROOT, tok))
    if os.path.isfile(cand):
        return "OK", tok
    # (2) relative to referencing file's directory
    cand = os.path.normpath(os.path.join(ref_dir, tok))
    if os.path.isfile(cand):
        return "OK", tok
    # (3) by basename anywhere in the search roots
    base = os.path.basename(tok).lower()
    if base in bmap:
        return "BASENAME", bmap[base][0]
    return "DEAD", None


def extract_seealso_blocks(lines):
    """Yield (start_line_1based, text) for each See also: paragraph."""
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith("See also:"):
            start = i
            buf = [lines[i]]
            j = i + 1
            while j < n:
                ln = lines[j]
                if ln.strip() == "" or ln.startswith("## "):
                    break
                buf.append(ln)
                j += 1
            blocks.append((start + 1, "\n".join(buf)))
            i = j
        else:
            i += 1
    return blocks


def scan_file(path, bmap, wiki_basenames, is_claude_md):
    """Return (links_checked, dead_list, by_basename_count, sections_total,
    sections_without_seealso) for one wiki file."""
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    ref_dir = os.path.dirname(path)
    rel = os.path.relpath(path, ROOT).replace("\\", "/")

    links_checked = 0
    dead = []
    by_basename = 0
    seen_on_line = {}  # dedupe identical (line, token) pairs

    def record(lineno, token):
        nonlocal links_checked, by_basename
        token = strip_punct(token)
        if not token:
            return
        key = (lineno, token)
        if key in seen_on_line:
            return
        seen_on_line[key] = True
        links_checked += 1
        status, _ = resolve(token, ref_dir, bmap)
        if status == "DEAD":
            dead.append((rel, lineno, token))
        elif status == "BASENAME":
            by_basename += 1

    # (a) See also: blocks
    for start_line, block in extract_seealso_blocks(lines):
        for m in TOKEN_EXT_RE.finditer(block):
            # locate which physical line this match falls on
            offset = m.start()
            lineno = start_line + block.count("\n", 0, offset)
            record(lineno, m.group(0))

    # (b) [[name]] wiki links - resolve against wiki basenames only
    for idx, ln in enumerate(lines, start=1):
        for m in WIKILINK_RE.finditer(ln):
            name = strip_punct(m.group(1))
            if not name:
                continue
            key = (idx, "[[%s]]" % name)
            if key in seen_on_line:
                continue
            seen_on_line[key] = True
            links_checked += 1
            target = (name if name.lower().endswith(".md") else name + ".md").lower()
            if target not in wiki_basenames:
                dead.append((rel, idx, "[[%s]]" % name))

    # (c) markdown [text](path) links
    for idx, ln in enumerate(lines, start=1):
        for m in MDLINK_RE.finditer(ln):
            target = m.group(1)
            if target.startswith("#"):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):  # scheme (http:, mailto:, ...)
                continue
            token = target.split("#", 1)[0]
            if not token:
                continue
            record(idx, token)

    # (d) CLAUDE.md: every docs/systems/<name>.md mention
    if is_claude_md:
        for idx, ln in enumerate(lines, start=1):
            for m in re.finditer(r"docs/systems/[\w-]+\.md", ln):
                record(idx, m.group(0))

    # HYGIENE: sections without a See also: line (docs/systems/*.md only)
    sections_total = 0
    sections_without = 0
    if os.path.basename(os.path.dirname(path)) == "systems":
        heading_idxs = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
        for k, hi in enumerate(heading_idxs):
            sections_total += 1
            end = heading_idxs[k + 1] if k + 1 < len(heading_idxs) else len(lines)
            body = lines[hi:end]
            if not any(l.lstrip().startswith("See also:") for l in body):
                sections_without += 1

    return links_checked, dead, by_basename, sections_total, sections_without


def main():
    ap = argparse.ArgumentParser(description="Warn-only wiki link checker")
    ap.add_argument("--strict", action="store_true",
                     help="exit 1 when dead links are found")
    ap.add_argument("--quiet", action="store_true",
                     help="print only the summary line")
    args = ap.parse_args()

    files = wiki_files()
    bmap = build_basename_map()
    wiki_basenames = {os.path.basename(p).lower() for p in files}

    total_links = 0
    total_dead = []
    total_basename = 0
    hygiene = []  # (rel, without, total)

    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        is_claude_md = (os.path.basename(path) == "CLAUDE.md")
        links, dead, by_base, sec_total, sec_without = scan_file(
            path, bmap, wiki_basenames, is_claude_md)
        total_links += links
        total_dead.extend(dead)
        total_basename += by_base
        if sec_total:
            hygiene.append((rel, sec_without, sec_total))

    out_lines = []
    out_lines.append("WIKI LINK CHECK")
    out_lines.append("files scanned: %d" % len(files))
    out_lines.append("links checked: %d" % total_links)
    out_lines.append("dead: %d (resolved by basename: %d)" % (len(total_dead), total_basename))
    out_lines.append("")
    for rel, lineno, token in total_dead:
        out_lines.append("DEAD  %s:%d  -> %s" % (rel, lineno, token))
    if total_dead:
        out_lines.append("")
    out_lines.append("SECTIONS WITHOUT SEE-ALSO:")
    any_hygiene = False
    for rel, without, total in hygiene:
        if without > 0:
            any_hygiene = True
            out_lines.append("SECTIONS WITHOUT SEE-ALSO: %s %d/%d" % (rel, without, total))
    if not any_hygiene:
        out_lines.append("(none)")
    out_lines.append("")
    summary = "SUMMARY: %d files, %d links, %d dead, %d by-basename" % (
        len(files), total_links, len(total_dead), total_basename)
    out_lines.append(summary)

    report = "\n".join(out_lines) + "\n"

    if args.quiet:
        print(summary)
    else:
        print(report, end="")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# GENERATED by tools/check_wiki_links.py - the full dead-link "
                  "and hygiene report; never hand-edit\n")
        fh.write(report)

    if not os.path.exists(RUNS):
        with open(RUNS, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(RUNS_HEADER)

    ws = "WS2" if "travis" in os.path.expanduser("~").lower() else "WS1"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    no_seealso_total = sum(w for _, w, _ in hygiene)
    first_dead = ", ".join(t for _, _, t in total_dead[:3]) or "none"
    run_line = ("%s | %s | %d files | %d links | dead %d | by-basename %d | "
                "no-see-also %d | %s\n") % (
        now, ws, len(files), total_links, len(total_dead), total_basename,
        no_seealso_total, first_dead)
    with open(RUNS, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(run_line)

    if args.strict and total_dead:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

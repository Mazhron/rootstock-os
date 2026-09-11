"""cold_shelf.py - move rarely-used wiki sections to a cold shelf, verbatim.

THE PRESERVATION LAW: knowledge is never deleted, only MOVED to a cold shelf
that stays indexed, with a record left at the old location. Every operation
here is copy + rewrite-in-place; text is preserved byte for byte. This file
contains NO deletion code on purpose (no os.remove, unlink, rmtree, rmdir,
git rm) - a harness hook refuses writes containing those calls.

Commands:
  --move <source_file> <heading> --reason "<why>" [--dry-run] [--root DIR]
      Cut a "## " section out of a hot wiki file, append it verbatim (plus a
      one-line provenance comment) to docs/cold/<basename of source_file>,
      leave a two-line stub + blank line in its place, and log the move to
      docs/cold/INDEX.md.
  --restore <source_file> <heading> [--dry-run] [--root DIR]
      Reverse a move: put the verbatim body back in the hot file, replace
      the cold file's copy with a one-line "Restored to ..." note, and log
      the restore to docs/cold/INDEX.md.
  --list
      Print docs/cold/INDEX.md's data lines (or "cold shelf empty").
  --check
      Scan every hot wiki file for stubs and verify each one points at an
      existing cold file that still contains the heading.

Heading matching: exact text after "## " (case-insensitive, whitespace-
collapsed). A query that is an unambiguous PREFIX of exactly one heading is
also accepted; anything else lists the candidates and exits 1.

Search keys: cold shelf, move section, prune, rarely used, restore section,
preservation law.
See also: WIKI_METHOD.md (the cold shelf); docs/cold/INDEX.md (the index);
tools/wiki_heat.py (the candidates); tools/check_wiki_links.py (link checker).
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

HEADING_PREFIX = "## "

COLD_FILE_HEADER = (
    "# Cold shelf: {basename} (sections moved out of the hot wiki, verbatim; "
    "never delete - the preservation law)\n"
    "Search keys: cold shelf, {stem}, archived sections.\n"
    "See also: docs/cold/INDEX.md (the shelf index); {orig_path} (the hot file).\n"
    "\n"
)

INDEX_HEADER = (
    "# THE COLD SHELF INDEX (append-only; one line per move or restore)\n"
    "Rarely-used wiki sections live in docs/cold/, verbatim, and are read ONLY "
    "when a hot file's stub says the topic moved here. Nothing is ever deleted "
    "(the preservation law). Mover: tools/cold_shelf.py.\n"
    "Search keys: cold shelf, pruned, rarely used, archived knowledge, moved sections.\n"
    "See also: WIKI_METHOD.md (the cold shelf section); "
    "docs/history/wiki_heat.txt (the candidates list).\n"
    "\n"
    "date | action | hot file | ## heading | lines | reason | shelf file\n"
)

STUB_RE = re.compile(
    r"Moved to the cold shelf \d{4}-\d{2}-\d{2} \((?P<reason>[^)]*)\): "
    r"(?P<coldpath>docs/cold/\S+) - read only when this topic comes up\."
)


# ---------------------------------------------------------------------------
# low-level file helpers (no deletion anywhere in this file)
# ---------------------------------------------------------------------------

def detect_newline(text):
    return "\r\n" if "\r\n" in text else "\n"


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def to_posix(path_str):
    return str(path_str).replace("\\", "/")


def rel_to_root(path, root):
    try:
        return to_posix(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return to_posix(path)


# ---------------------------------------------------------------------------
# section parsing
# ---------------------------------------------------------------------------

def normalize_heading(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def find_sections(lines):
    """Return a list of section dicts for every '## ' line in lines.

    lines is the list from str.splitlines(keepends=True). Each section spans
    from its heading line up to (not including) the next heading line or EOF.
    """
    sections = []
    heading_idxs = [i for i, ln in enumerate(lines) if ln.startswith(HEADING_PREFIX)]
    for n, start in enumerate(heading_idxs):
        end = heading_idxs[n + 1] if n + 1 < len(heading_idxs) else len(lines)
        raw_heading_line = lines[start]
        heading_text = raw_heading_line.rstrip("\r\n")[len(HEADING_PREFIX):]
        sections.append({
            "start": start,
            "end": end,
            "heading_text": heading_text,
            "normalized": normalize_heading(heading_text),
        })
    return sections


def match_heading(lines, query):
    """Return (section, candidates). Exactly one of the two is non-empty/None.

    On a clean unambiguous match, section is the dict and candidates is None.
    On no match or an ambiguous match, section is None and candidates is the
    (possibly empty) list of section dicts that partially matched.
    """
    sections = find_sections(lines)
    nq = normalize_heading(query)

    exact = [s for s in sections if s["normalized"] == nq]
    if len(exact) == 1:
        return exact[0], None
    if len(exact) > 1:
        return None, exact

    prefix = [s for s in sections if s["normalized"].startswith(nq)]
    if len(prefix) == 1:
        return prefix[0], None
    return None, prefix


def fail(msg):
    print(msg)
    sys.exit(1)


def report_no_match(query, candidates, where):
    if not candidates:
        fail("No heading matching '{}' found in {}".format(query, where))
    print("Ambiguous heading '{}' in {} - matches:".format(query, where))
    for c in candidates:
        print("  ## {}".format(c["heading_text"]))
    sys.exit(1)


# ---------------------------------------------------------------------------
# --move
# ---------------------------------------------------------------------------

def cmd_move(root, source_file, heading, reason, dry_run):
    if not reason:
        fail("--move requires --reason \"<why>\"")

    source_path = Path(source_file)
    if not source_path.is_absolute():
        source_path = root / source_file
    if not source_path.exists():
        fail("Source file not found: {}".format(source_path))

    source_text = read_text(source_path)
    source_nl = detect_newline(source_text)
    source_lines = source_text.splitlines(keepends=True)

    section, candidates = match_heading(source_lines, heading)
    if section is None:
        report_no_match(heading, candidates, to_posix(source_path))

    start, end = section["start"], section["end"]
    body_text = "".join(source_lines[start + 1:end])
    if "Moved to the cold shelf" in body_text:
        fail("Section '## {}' in {} is already a cold stub - nothing to move".format(
            section["heading_text"], to_posix(source_path)))

    n_lines = end - start
    heading_text = section["heading_text"]
    today = date.today().isoformat()

    basename = source_path.name
    stem = source_path.stem
    orig_path_display = rel_to_root(source_path, root)
    cold_path = root / "docs" / "cold" / basename
    index_path = root / "docs" / "cold" / "INDEX.md"
    cold_rel_display = "docs/cold/{}".format(basename)

    # Load (or plan) the cold file's existing content.
    if cold_path.exists():
        cold_text = read_text(cold_path)
        cold_nl = detect_newline(cold_text)
    else:
        cold_text = COLD_FILE_HEADER.format(
            basename=basename, stem=stem, orig_path=orig_path_display,
        )
        cold_nl = "\n"

    cold_lines = cold_text.splitlines(keepends=True)
    existing_cold_sections = find_sections(cold_lines)
    if any(s["normalized"] == section["normalized"] for s in existing_cold_sections):
        fail("{} already has a '## {}' heading - refusing to move a duplicate".format(
            cold_rel_display, heading_text))

    if dry_run:
        print("[dry-run] would move {} lines: {}#{} -> {}".format(
            n_lines, orig_path_display, heading_text, cold_rel_display))
        return

    # --- build the cold-file addition: blank line, heading, provenance, body (verbatim) ---
    provenance = "<!-- cold shelf: moved from {} on {}, reason: {}, {} lines -->{}".format(
        orig_path_display, today, reason, n_lines, source_nl)
    addition = (
        source_nl
        + source_lines[start]              # heading line, verbatim
        + provenance
        + "".join(source_lines[start + 1:end])  # body, verbatim
    )
    new_cold_text = cold_text + addition
    write_text(cold_path, new_cold_text)

    # --- rewrite the source: keep the heading, replace the body with a stub ---
    stub = [
        "Moved to the cold shelf {} ({}): {} - read only when this topic comes up.{}".format(
            today, reason, cold_rel_display, source_nl),
        "See also: docs/cold/INDEX.md (the shelf index).{}".format(source_nl),
        source_nl,
    ]
    new_source_lines = source_lines[:start + 1] + stub + source_lines[end:]
    write_text(source_path, "".join(new_source_lines))

    # --- log to the index ---
    append_index_line(
        index_path, today, "moved", orig_path_display, heading_text,
        n_lines, reason, cold_rel_display,
    )

    print("MOVED {} lines: {}#{} -> {}".format(
        n_lines, orig_path_display, heading_text, cold_rel_display))


# ---------------------------------------------------------------------------
# --restore
# ---------------------------------------------------------------------------

def cmd_restore(root, source_file, heading, dry_run):
    source_path = Path(source_file)
    if not source_path.is_absolute():
        source_path = root / source_file
    if not source_path.exists():
        fail("Source file not found: {}".format(source_path))

    source_text = read_text(source_path)
    source_nl = detect_newline(source_text)
    source_lines = source_text.splitlines(keepends=True)

    section, candidates = match_heading(source_lines, heading)
    if section is None:
        report_no_match(heading, candidates, to_posix(source_path))

    start, end = section["start"], section["end"]
    heading_text = section["heading_text"]
    body_text = "".join(source_lines[start + 1:end])
    if "Moved to the cold shelf" not in body_text:
        fail("Section '## {}' in {} is not a cold-shelf stub - nothing to restore".format(
            heading_text, to_posix(source_path)))

    basename = source_path.name
    orig_path_display = rel_to_root(source_path, root)
    cold_path = root / "docs" / "cold" / basename
    index_path = root / "docs" / "cold" / "INDEX.md"
    cold_rel_display = "docs/cold/{}".format(basename)

    if not cold_path.exists():
        fail("Cold file not found: {}".format(cold_path))

    cold_text = read_text(cold_path)
    cold_nl = detect_newline(cold_text)
    cold_lines = cold_text.splitlines(keepends=True)

    cold_section, cold_candidates = match_heading(cold_lines, heading_text)
    if cold_section is None:
        report_no_match(heading_text, cold_candidates, cold_rel_display)

    c_start, c_end = cold_section["start"], cold_section["end"]
    if c_end - c_start < 2 or not cold_lines[c_start + 1].lstrip().startswith("<!-- cold shelf:"):
        fail("Cold section '## {}' in {} has no provenance line - refusing to restore".format(
            heading_text, cold_rel_display))

    restored_body = cold_lines[c_start + 2:c_end]  # verbatim original body
    today = date.today().isoformat()

    if dry_run:
        n_lines = (c_end - c_start) - 1  # minus the provenance line
        print("[dry-run] would restore {} lines: {} -> {}#{}".format(
            n_lines, cold_rel_display, orig_path_display, heading_text))
        return

    # --- rewrite the source: keep the heading, put the verbatim body back ---
    new_source_lines = source_lines[:start + 1] + restored_body + source_lines[end:]
    write_text(source_path, "".join(new_source_lines))

    # --- rewrite the cold file: keep the heading, collapse the body to one note ---
    restored_note = "Restored to {} on {}.{}".format(orig_path_display, today, cold_nl)
    new_cold_lines = cold_lines[:c_start + 1] + [restored_note] + cold_lines[c_end:]
    write_text(cold_path, "".join(new_cold_lines))

    n_lines = len(restored_body) + 1  # + heading line
    append_index_line(
        index_path, today, "restored", orig_path_display, heading_text,
        n_lines, "-", cold_rel_display,
    )

    print("RESTORED {} lines: {} -> {}#{}".format(
        n_lines, cold_rel_display, orig_path_display, heading_text))


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------

def append_index_line(index_path, today, action, hot_path, heading_text, n_lines, reason, shelf_file):
    if index_path.exists():
        index_text = read_text(index_path)
        nl = detect_newline(index_text)
        if not index_text.endswith(nl) and index_text:
            index_text += nl
    else:
        index_text = INDEX_HEADER
        nl = "\n"

    line = "{} | {} | {} | ## {} | {} lines | {} | {}{}".format(
        today, action, hot_path, heading_text, n_lines, reason, shelf_file, nl)
    write_text(index_path, index_text + line)


# ---------------------------------------------------------------------------
# --list
# ---------------------------------------------------------------------------

DATA_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \| ")


def cmd_list(root):
    index_path = root / "docs" / "cold" / "INDEX.md"
    if not index_path.exists():
        print("cold shelf empty")
        return
    lines = read_text(index_path).splitlines()
    data_lines = [ln for ln in lines if DATA_LINE_RE.match(ln)]
    if not data_lines:
        print("cold shelf empty")
        return
    for ln in data_lines:
        print(ln)


# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------

def hot_files(root):
    files = list(root.glob("*.md"))
    systems_dir = root / "docs" / "systems"
    if systems_dir.exists():
        files.extend(sorted(systems_dir.glob("*.md")))
    return sorted(files)


def cmd_check(root):
    broken = []
    stub_count = 0

    for hot_path in hot_files(root):
        text = read_text(hot_path)
        lines = text.splitlines(keepends=True)
        for section in find_sections(lines):
            body_text = "".join(lines[section["start"] + 1:section["end"]])
            if "Moved to the cold shelf" not in body_text:
                continue
            stub_count += 1
            hot_display = rel_to_root(hot_path, root)
            heading_text = section["heading_text"]

            m = STUB_RE.search(body_text)
            if not m:
                broken.append("{}#{} -> (malformed stub, could not parse cold path)".format(
                    hot_display, heading_text))
                continue

            cold_rel = m.group("coldpath")
            cold_path = root / cold_rel
            if not cold_path.exists():
                broken.append("{}#{} -> {} (cold file missing)".format(
                    hot_display, heading_text, cold_rel))
                continue

            cold_text = read_text(cold_path)
            cold_lines = cold_text.splitlines(keepends=True)
            cold_sections = find_sections(cold_lines)
            nq = normalize_heading(heading_text)
            if not any(s["normalized"] == nq for s in cold_sections):
                broken.append("{}#{} -> {} (heading not found in cold file)".format(
                    hot_display, heading_text, cold_rel))

    if broken:
        print("COLD SHELF CHECK: BROKEN ({} of {} stubs)".format(len(broken), stub_count))
        for b in broken:
            print("  BROKEN: {}".format(b))
        sys.exit(1)

    print("COLD SHELF CHECK: OK ({} stubs)".format(stub_count))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def default_root():
    return Path(__file__).resolve().parent.parent


def build_parser():
    p = argparse.ArgumentParser(
        description="Move or restore wiki sections to/from the cold shelf, verbatim.")
    p.add_argument("--move", nargs=2, metavar=("SOURCE", "HEADING"),
                    help="move a '## ' section from SOURCE to the cold shelf")
    p.add_argument("--restore", nargs=2, metavar=("SOURCE", "HEADING"),
                    help="restore a '## ' section from the cold shelf back to SOURCE")
    p.add_argument("--list", action="store_true", help="print the cold shelf index")
    p.add_argument("--check", action="store_true",
                    help="verify every hot-file stub points at a real cold section")
    p.add_argument("--reason", type=str, default=None, help="required with --move")
    p.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    p.add_argument("--root", type=str, default=None,
                    help="repo root override (default: parent of this script's tools/ dir)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else default_root()

    actions = [bool(args.move), bool(args.restore), args.list, args.check]
    if sum(actions) != 1:
        fail("Pass exactly one of --move, --restore, --list, --check")

    if args.move:
        cmd_move(root, args.move[0], args.move[1], args.reason, args.dry_run)
    elif args.restore:
        cmd_restore(root, args.restore[0], args.restore[1], args.dry_run)
    elif args.list:
        cmd_list(root)
    elif args.check:
        cmd_check(root)


if __name__ == "__main__":
    main()

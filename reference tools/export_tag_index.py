"""Compile the KNOWLEDGE INDEX from Tags: lines across the wiki.

    python tools/export_tag_index.py            # write KNOWLEDGE_INDEX.md
    python tools/export_tag_index.py --dry-run  # print summary only

THE TAG CONVENTION (Mazhron approved 2026-09-03): any section whose content
is hard-won knowledge (a lesson, a trap, a doctrine) carries, directly under
its `## ` heading, a line:

    Tags: tag1, tag2 | one-line brief of the takeaway

This script sweeps repo-root *.md + docs/systems/*.md and generates
KNOWLEDGE_INDEX.md (repo root, GENERATED - never hand-edit): one section per
tag, one clickable line per entry linking to the section's TRUE home. No
knowledge is duplicated - the index is links + briefs only. New files and
new tags appear automatically on the next run. Prefer the starter tags
(lessons, gotchas, architecture, performance, process, design, economy);
invent a new one only when none fits - the summary prints the tag inventory
so drift is visible.

Search keys: knowledge index, tags, lessons compiled, browsable pitfalls.
See also: WIKI_METHOD.md (the convention), tools/export_wiki_view.py.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "KNOWLEDGE_INDEX.md")
SKIP_ROOT = {"KNOWLEDGE_INDEX.md", "CHANGELOG.md", "context_dump.txt"}


def slug(heading):
    """GitHub-style anchor: lowercase, drop punctuation, spaces to hyphens."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")


def scan(path, rel):
    entries = []
    heading = None
    for ln in open(path, encoding="utf-8"):
        m = re.match(r"##+ (.+)", ln)
        if m:
            heading = m.group(1).strip()
            continue
        t = re.match(r"Tags:\s*([^|]+)\|\s*(.+)", ln)
        if t and heading:
            tags = [w.strip().lower() for w in t.group(1).split(",") if w.strip()]
            entries.append((tags, heading, t.group(2).strip(), rel))
        elif re.match(r"Tags:", ln):
            print("WARN %s: malformed Tags line (need 'Tags: a, b | brief'): %s"
                  % (rel, ln.strip()))
    return entries


def main():
    ap = argparse.ArgumentParser(description="Compile KNOWLEDGE_INDEX.md from Tags: lines")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = []
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".md") and name not in SKIP_ROOT:
            files.append((os.path.join(ROOT, name), name))
    sysdir = os.path.join(ROOT, "docs", "systems")
    for name in sorted(os.listdir(sysdir)):
        if name.endswith(".md"):
            files.append((os.path.join(sysdir, name), "docs/systems/" + name))

    by_tag = {}
    total = 0
    for path, rel in files:
        for tags, heading, brief, rel2 in scan(path, rel):
            total += 1
            for tag in tags:
                by_tag.setdefault(tag, []).append((heading, brief, rel2))

    print("tag inventory: " + (", ".join("%s(%d)" % (t, len(v))
          for t, v in sorted(by_tag.items())) or "(no Tags lines found)"))
    print("%d tagged sections across %d files scanned" % (total, len(files)))
    if args.dry_run:
        return

    lines = [
        "# KNOWLEDGE INDEX (GENERATED - do not hand-edit)",
        "",
        "Every hard-won fact in this project's wiki, grouped by tag and linked",
        "to its one true home. Regenerate: `python tools/export_tag_index.py`.",
        "Tag a section by putting `Tags: tag1, tag2 | one-line brief` directly",
        "under its heading (convention: WIKI_METHOD.md).",
        "",
    ]
    for tag in sorted(by_tag):
        lines.append("## %s" % tag.capitalize())
        lines.append("")
        for heading, brief, rel in by_tag[tag]:
            lines.append("- [%s](%s#%s) - %s" % (heading, rel, slug(heading), brief))
        lines.append("")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("wrote KNOWLEDGE_INDEX.md (%d tags, %d entries)" % (len(by_tag), total))


if __name__ == "__main__":
    main()

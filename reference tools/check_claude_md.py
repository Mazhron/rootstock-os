"""Guards the CLAUDE.md token diet (2026-08-24 restructure).

    python tools/check_claude_md.py

Warns (exit 1) when the lean core bloats past its budget or the library
index drifts from the files on disk. Run it whenever CLAUDE.md grows; the
answer to a warning is moving knowledge into docs/systems/, never raising
the budget casually.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "CLAUDE.md")
LIB = os.path.join(ROOT, "docs", "systems")
LINE_BUDGET = 700   # the 2026-08-24 restructure landed at ~250; alarm well before old habits return

problems = []
lines = open(CORE, encoding="utf-8").read().splitlines()
if len(lines) > LINE_BUDGET:
    problems.append("CLAUDE.md is %d lines (budget %d): move knowledge into "
                    "docs/systems/ topic files." % (len(lines), LINE_BUDGET))

indexed = set(re.findall(r"docs/systems/([\w-]+\.md)", "\n".join(lines)))
on_disk = {f for f in os.listdir(LIB) if f.endswith(".md")}
for f in sorted(indexed - on_disk):
    problems.append("index lists docs/systems/%s but the file is missing" % f)
for f in sorted(on_disk - indexed):
    problems.append("docs/systems/%s exists but the CLAUDE.md index does not "
                    "mention it" % f)

if problems:
    print("CLAUDE.md CHECK: FAIL")
    for p in problems:
        print(" - " + p)
    sys.exit(1)

# The expansion-doctrine count (Mazhron 2026-09-03): knowledge files are
# cheap and MEANT to multiply - this is informational, never a failure.
# At a round-1000 milestone, the manager mentions it to the user once.
kcount = len([n for n in os.listdir(ROOT) if n.endswith(".md")]) + len(on_disk)
note = "  <- crossed a 1000-file milestone: mention it to the user (informational; growth is good)" \
    if kcount >= 1000 else ""
print("CLAUDE.md CHECK: OK (%d lines, %d library files indexed, %d knowledge files%s)"
      % (len(lines), len(on_disk), kcount, note))

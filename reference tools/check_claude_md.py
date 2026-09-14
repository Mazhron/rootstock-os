"""Guards the CLAUDE.md token diet (2026-08-24 restructure).

    python tools/check_claude_md.py

Warns (exit 1) when the lean core bloats past its budget or the library
index drifts from the files on disk. Run it whenever CLAUDE.md grows; the
answer to a warning is moving knowledge into docs/systems/, never raising
the budget casually.

PURPOSE: Read CLAUDE.md and fail with exit 1 when the lean core exceeds its
  token or line budget or when the docs/systems library index or the
  docs/index sub-index list in CLAUDE.md drifts from the files on disk.
INTENT: keeps CLAUDE.md lean from the 2026-08-24 token diet restructure by
  catching bloat and index drift the moment they happen, instead of letting
  the file grow back into old habits. THE TOKEN BUDGET (the CEO 2026-09-14,
  after a Reddit reader measured the kit's front door at ~5k tokens): the
  core is the one file loaded whole every session, so its size is judged in
  tokens (bytes/4, the digest_size rule) and the answer to a FAIL is
  tools/core_diet.py (route a section, let the loop move it), never a
  raised budget.

Search keys: claude.md check, token diet, token budget, line budget, library
  index, sub-index list, index drift, knowledge file count
See also: CLAUDE.md (the file guarded), docs/systems/ (the library index
  checked), docs/index/ (the sub-indexes checked), tools/core_diet.py (the
  mover that answers a budget FAIL), tools/run_all.py (check group).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "CLAUDE.md")
LIB = os.path.join(ROOT, "docs", "systems")
SUBINDEX = os.path.join(ROOT, "docs", "index")
LINE_BUDGET = 300    # the 2026-08-24 restructure landed at ~250; 2026-09-14 the core diet re-pinned it there
TOKEN_BUDGET = 3500  # bytes/4; a fresh Rootstock install lands at ~1.5-3k, a 50-day project with live notes just under this


def core_tokens(text):
    return len(text.encode("utf-8")) // 4


if __name__ == "__main__":
  problems = []
  text = open(CORE, encoding="utf-8").read()
  lines = text.splitlines()
  tokens = core_tokens(text)
  if tokens > TOKEN_BUDGET:
    problems.append("CLAUDE.md is ~%d tokens (budget %d): route a section with an "
                    "`Index: <name>` line and run `python tools/core_diet.py --move`; "
                    "never raise the budget." % (tokens, TOKEN_BUDGET))
  if len(lines) > LINE_BUDGET:
    problems.append("CLAUDE.md is %d lines (budget %d): move knowledge into "
                    "docs/systems/ topic files or a docs/index/ sub-index." % (len(lines), LINE_BUDGET))

  indexed = set(re.findall(r"docs/systems/([\w-]+\.md)", "\n".join(lines)))
  on_disk = {f for f in os.listdir(LIB) if f.endswith(".md")}
  for f in sorted(indexed - on_disk):
    problems.append("index lists docs/systems/%s but the file is missing" % f)
  for f in sorted(on_disk - indexed):
    problems.append("docs/systems/%s exists but the CLAUDE.md index does not "
                    "mention it" % f)
  sub_indexed = set(re.findall(r"docs/index/([\w-]+\.md)", "\n".join(lines)))
  sub_disk = {f for f in os.listdir(SUBINDEX) if f.endswith(".md")} if os.path.isdir(SUBINDEX) else set()
  for f in sorted(sub_indexed - sub_disk):
    problems.append("CLAUDE.md names docs/index/%s but the file is missing" % f)
  for f in sorted(sub_disk - sub_indexed):
    problems.append("docs/index/%s exists but CLAUDE.md does not name it (one line in "
                    "the sub-indexes block)" % f)

  if problems:
    print("CLAUDE.md CHECK: FAIL (~%d tokens, %d lines)" % (tokens, len(lines)))
    for p in problems:
        print(" - " + p)
    sys.exit(1)

  # The expansion-doctrine count (the CEO 2026-09-03): knowledge files are
  # cheap and MEANT to multiply - this is informational, never a failure.
  # At a round-1000 milestone, the manager mentions it to the user once.
  kcount = len([n for n in os.listdir(ROOT) if n.endswith(".md")]) + len(on_disk) + len(sub_disk)
  note = "  <- crossed a 1000-file milestone: mention it to the user (informational; growth is good)" \
      if kcount >= 1000 else ""
  print("CLAUDE.md CHECK: OK (~%d tokens of %d, %d lines, %d library files + %d sub-indexes indexed, "
        "%d knowledge files%s)" % (tokens, TOKEN_BUDGET, len(lines), len(on_disk), len(sub_disk), kcount, note))

"""Guards the CLAUDE.md token diet (2026-08-24 restructure).

    python tools/check_claude_md.py

Warns (exit 1) when the lean core bloats past its budget or the library
index drifts from the files on disk. Run it whenever CLAUDE.md grows; the
answer to a warning is moving knowledge into docs/systems/, never raising
the budget casually.

PURPOSE: Read CLAUDE.md and fail with exit 1 when the pointer core exceeds its
  token or line budget, when CLAUDE.md does not name the master index, when
  the master index (docs/index/MASTER_INDEX.md) drifts from the docs/systems
  and docs/index files on disk, or when a .claude/rules file has no paths
  field (it would load every session; its tokens count against the core);
  warn past WARN_TOKENS.
INTENT: keeps CLAUDE.md lean from the 2026-08-24 token diet restructure by
  catching bloat and index drift the moment they happen, instead of letting
  the file grow back into old habits. THE TOKEN BUDGET (the CEO 2026-09-14,
  after a Reddit reader measured the kit's front door at ~5k tokens): the
  core is the one file loaded whole every session, so its size is judged in
  tokens (bytes/4, the digest_size rule) and the answer to a FAIL is
  tools/core_diet.py (route a section, let the loop move it), never a
  raised budget. THE POINTER CORE (the CEO 2026-09-14, after reading
  Anthropic's memory doc: "Claude.md should simply point to everything
  else"): the line budget is Anthropic's 200, the token budget 2,000 is
  the CEO's action line, the warn line 1,000 is the community figure;
  rules only load by path, the master index is the one door.

Search keys: claude.md check, token diet, token budget, line budget, warn
  tokens, master index, rules paths, index drift, knowledge file count
See also: CLAUDE.md (the file guarded), docs/index/MASTER_INDEX.md (the one
  door checked), docs/systems/ + docs/index/ (the files it must list),
  .claude/rules/ (paths checked), tools/core_diet.py (the mover that
  answers a budget FAIL), tools/standup.py (prints the OK/WARN line),
  tools/run_all.py (check group), https://code.claude.com/docs/en/memory.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "CLAUDE.md")
LIB = os.path.join(ROOT, "docs", "systems")
SUBINDEX = os.path.join(ROOT, "docs", "index")
LINE_BUDGET = 200    # Anthropic: "target under 200 lines per CLAUDE.md file" (code.claude.com/docs/en/memory)
TOKEN_BUDGET = 2000  # bytes/4; the CEO 2026-09-14: past 2,000 "there should be some type of action"; FAIL
WARN_TOKENS = 1000   # the community figure (~1k tokens); the pointer core lands ~900; WARN only
MASTER = os.path.join(SUBINDEX, "MASTER_INDEX.md")
MASTER_REL = "docs/index/MASTER_INDEX.md"
RULES = os.path.join(ROOT, ".claude", "rules")


def core_tokens(text):
    return len(text.encode("utf-8")) // 4


if __name__ == "__main__":
  problems = []
  text = open(CORE, encoding="utf-8").read()
  lines = text.splitlines()
  tokens = core_tokens(text)
  # rules without a paths: field load every session - they ARE core load
  unscoped = []
  scoped = []
  if os.path.isdir(RULES):
    for f in sorted(os.listdir(RULES)):
      if not f.endswith(".md"):
        continue
      rt = open(os.path.join(RULES, f), encoding="utf-8").read()
      fm = re.match(r"^---\r?\n(.*?)\r?\n---", rt, re.S)
      if fm and re.search(r"^paths:\s*$", fm.group(1), re.M) and re.search(r"^\s*-\s*\S", fm.group(1), re.M):
        scoped.append(f)
      else:
        unscoped.append(f)
        tokens += core_tokens(rt)
  for f in unscoped:
    problems.append(".claude/rules/%s has no `paths:` front matter, so it loads every "
                    "session; give it paths (Anthropic's path-scoped rules) or move it into "
                    "a sub-index" % f)
  if tokens > TOKEN_BUDGET:
    problems.append("CLAUDE.md is ~%d tokens (budget %d): route a section with an "
                    "`Index: <name>` line and run `python tools/core_diet.py --move`, or move a "
                    "rule set to .claude/rules/ with a paths: field; never raise the budget."
                    % (tokens, TOKEN_BUDGET))
  if len(lines) > LINE_BUDGET:
    problems.append("CLAUDE.md is %d lines (budget %d, Anthropic's target): move knowledge into "
                    "a docs/index/ sub-index or a path-scoped rule." % (len(lines), LINE_BUDGET))

  # the one door: CLAUDE.md names the master index, the master index lists everything
  core_text = "\n".join(lines)
  if MASTER_REL not in core_text:
    problems.append("CLAUDE.md does not name %s (the one door)" % MASTER_REL)
  master = open(MASTER, encoding="utf-8").read() if os.path.isfile(MASTER) else ""
  if not master:
    problems.append("%s is missing" % MASTER_REL)
  indexed = set(re.findall(r"docs/systems/([\w-]+\.md)", master))
  on_disk = {f for f in os.listdir(LIB) if f.endswith(".md")}
  for f in sorted(indexed - on_disk):
    problems.append("%s lists docs/systems/%s but the file is missing" % (MASTER_REL, f))
  for f in sorted(on_disk - indexed):
    problems.append("docs/systems/%s exists but %s does not mention it" % (f, MASTER_REL))
  sub_indexed = set(re.findall(r"docs/index/([\w-]+\.md)", master))
  sub_disk = {f for f in os.listdir(SUBINDEX) if f.endswith(".md")} if os.path.isdir(SUBINDEX) else set()
  sub_disk.discard("MASTER_INDEX.md")
  for f in sorted(sub_indexed - sub_disk - {"MASTER_INDEX.md"}):
    problems.append("%s names docs/index/%s but the file is missing" % (MASTER_REL, f))
  for f in sorted(sub_disk - sub_indexed):
    problems.append("docs/index/%s exists but %s does not name it (one line in "
                    "the sub-indexes block)" % (f, MASTER_REL))
  for f in scoped:
    if ".claude/rules/" + f not in master:
      problems.append(".claude/rules/%s exists but %s does not list it" % (f, MASTER_REL))

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
  warn = tokens > WARN_TOKENS
  print("CLAUDE.md CHECK: %s (~%d tokens of %d%s, %d lines of %d, %d rules by path, "
        "%d library files + %d sub-indexes in the master index, %d knowledge files%s)"
        % ("WARN" if warn else "OK", tokens, TOKEN_BUDGET,
           " - past the %d warn line, consider a move" % WARN_TOKENS if warn else "",
           len(lines), LINE_BUDGET, len(scoped), len(on_disk), len(sub_disk), kcount, note))

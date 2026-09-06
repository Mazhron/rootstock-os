"""PreToolUse guard on Bash/PowerShell: standing laws, enforced (Tier 2).

KIT COPY (Rootstock). The harness hands us the command BEFORE it runs; a
deny refuses it and feeds the reason back to the manager. GENERIC RULES
below apply to any project; PROJECT RULES is the block a receiving
project fills with the CEO's own laws - the commented examples are the
origin project's (Everwood) real rules, kept as templates.

Adding a rule = one more block here + its line in the tooling doc's
"The hooks" section.

Search keys: bash guard, pretooluse, deny, force push, no-verify, project
rules template.
See also: _hooklib.py; HOOKS_METHOD.md (the contract + bootstrap).
"""
import re
import sys

from _hooklib import deny, read_input

data = read_input()
cmd = (data.get("tool_input") or {}).get("command") or ""
if not cmd:
    sys.exit(0)
low = cmd.lower()

# ---- GENERIC RULES -------------------------------------------------------
if re.search(r"\bgit\s+commit\b", low) and "--no-verify" in low:
    deny("Never skip hooks (--no-verify); fix the failing hook instead.")
# Scoped to the push invocation (up to the next |, & or ;) and case-
# sensitive: a `git commit -F -` earlier in the same command must not read
# as a force push (misfire 2026-09-06).
for _m in re.finditer(r"\bgit\s+push\b([^|&;\n]*)", cmd):
    _seg = _m.group(1)
    if not (re.search(r"\s(--force|-f)\b", _seg) and "--force-with-lease" not in _seg):
        continue
    deny("No plain force pushes on a shared branch. Use --force-with-lease, "
         "and only with the CEO's explicit go-ahead.")

# ---- PROJECT RULES (fill from the CEO's laws; examples from Everwood) ----
# 1. Release artifacts are never deleted (Everwood: "BUILD ZIPS ARE NEVER
#    DELETED" - old zips are the 'before' side of dev-log comparisons).
# DELETE = r"(^|[\s;|&(])(rm|del|erase|rmdir|remove-item|ri|move-item|mv|rename-item)\b"
# if re.search(DELETE, low) and "<builds folder name, lowercased>" in low:
#     deny("BUILD ARTIFACTS ARE NEVER DELETED: ... leave them.")
#
# 2. Tests run through the runner script only (the Script Rule): setting
#    the project's test env var by hand is refused.
# if re.search(r"(\$env:<prefix>_\w*test\s*=|(^|[\s;&])<prefix>_\w*test\s*=\s*\S|export\s+<prefix>_\w*test)", low) \
#         and "run_tests.py" not in low:
#     deny("THE SCRIPT RULE: tests run through tools/run_tests.py ONLY.")
#
# 3. Text doctrine in commit messages (Everwood: no em/en dashes - commit
#    subjects become the public changelog).
# if re.search(r"\bgit\s+commit\b", low) and ("—" in cmd or "–" in cmd):
#     deny("NO em or en dashes in commit messages - use a hyphen, colon or comma.")
#
# 4. Engine/config files that a shell write corrupts (Everwood: PowerShell's
#    BOM breaks Godot's .tres parser).
# if re.search(r"(set-content|out-file|add-content)[^|;\n]*\.tres\b", low) or \
#         re.search(r">{1,2}\s*\"?[^\s\"|;]*\.tres\b", low):
#     deny("Write resource files with the Write/Edit tool, never a shell redirect.")

sys.exit(0)

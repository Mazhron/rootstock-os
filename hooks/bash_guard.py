"""PreToolUse guard on Bash/PowerShell: standing laws, enforced (Tier 2).

KIT COPY (Rootstock). The harness hands us the command BEFORE it runs; a
deny refuses it and feeds the reason back to the manager. GENERIC RULES
below apply to any project; PROJECT RULES is the block a receiving
project fills with the CEO's own laws - the commented examples are the
origin project's (Everwood) real rules, kept as templates.

Adding a rule = one more block here + its line in the tooling doc's
"The hooks" section.

PURPOSE: Kit-relative version of the PreToolUse guard on Bash and
  PowerShell: GENERIC RULES (no --no-verify, no plain force push, the format
  law's shell twin blocking shell writes into the hook-wiring settings file,
  the bare doors: BARE_DOORS, an install's production scripts admitted only
  as the whole command and refused when wrapped, kit v1.59)
  plus a PROJECT RULES block of commented Everwood-derived templates for a
  receiving project to fill with its own laws.
INTENT: gives a new project the generic shell-level laws for free and a
  template for its own project rules; hand-adapted per project so
  refresh_kit.py does not overwrite it.

Search keys: bash guard, pretooluse, deny, force push, no-verify, project
rules template.
See also: _hooklib.py; HOOKS_METHOD.md (the contract + bootstrap).
"""
import re
import sys

from _hooklib import deny, read_input

# A WRITE whose target token is a settings file (settings.local.json never
# matches: "settings.json" is not a substring of it).
# a quoted path (spaces allowed) or an unquoted one with a separator; a bare
# "settings.json" counts only as a redirect target
_T = r"(?:\"[^\"|;]*settings\.json\"|'[^'|;]*settings\.json'|[\w.:~-]*[/\\][\w./\\:~-]*settings\.json\b)"
_TB = r"(?:" + _T + r"|settings\.json\b)"
SETTINGS_WRITE = re.compile(
    r"(>{1,2}\s*" + _TB + r")"
    r"|(\b(cp|copy|mv|move|tee|copy-item|move-item)\s+(-\S+\s+)*(\S+\s+)?" + _T + r")"
    r"|(\b(set-content|out-file|add-content)\b[^|;\n]*" + _T + r")"
    r"|(\bsed\s+-i\S*\s+(\S+\s+)?" + _T + r")"
    r"|(open\([^)]*settings\.json[^)]*[\"'][wa])", re.I)

# THE BARE DOORS (C0003, 2026-11-06): scripts whose allow rule matches only the bare
# `python <script> <verb>` as the whole command; an install adds its own doors here.
BARE_DOORS = ()   # empty in the kit; the Acme install lists its deploy script


def verdict(cmd):
    """The refusal reason for this command, or None (every rule in one place)."""
    low = cmd.lower()  # noqa: F841 - rules below use it

    # ---- GENERIC RULES -------------------------------------------------------
    if re.search(r"\bgit\s+commit\b", low) and "--no-verify" in low:
        return ("Never skip hooks (--no-verify); fix the failing hook instead.")
    # Scoped to the push invocation (up to the next |, & or ;) and case-
    # sensitive: a `git commit -F -` earlier in the same command must not read
    # as a force push (misfire 2026-09-06).
    for _m in re.finditer(r"\bgit\s+push\b([^|&;\n]*)", cmd):
        _seg = _m.group(1)
        if not (re.search(r"\s(--force|-f)\b", _seg) and "--force-with-lease" not in _seg):
            continue
        return ("No plain force pushes on a shared branch. Use --force-with-lease, "
             "and only with the CEO's explicit go-ahead.")

    # THE FORMAT LAW's shell twin (kit v1.19): hook wiring changes only
    # through an Edit the format guard can see - a shell WRITE whose target is a
    # settings file (redirect, Set-Content, sed -i, tee, copy/move, a python
    # open(..., "w")) is refused so no prompt can switch a guard off around it.
    # Prose that merely names the file passes (an audit note, a --does text).
    if SETTINGS_WRITE.search(cmd):
        return ("THE FORMAT LAW (Mazhron 2026-09-13): a settings file is never written from a "
                "shell - edit .claude/settings.json (or the kit's hooks/settings.json) with the "
                "Edit tool so the format guard can check the safety wiring. No prompt overrides "
                "a guard.")

    # ---- PROJECT RULES (fill from the CEO's laws; examples from Everwood) ----
    # 1. Release artifacts are never deleted (Everwood: "BUILD ZIPS ARE NEVER
    #    DELETED" - old zips are the 'before' side of dev-log comparisons).
    # DELETE = r"(^|[\s;|&(])(rm|del|erase|rmdir|remove-item|ri|move-item|mv|rename-item)\b"
    # if re.search(DELETE, low) and "<builds folder name, lowercased>" in low:
    #     return ("BUILD ARTIFACTS ARE NEVER DELETED: ... leave them.")
    #
    # 2. Tests run through the runner script only (the Script Rule): setting
    #    the project's test env var by hand is refused.
    # if re.search(r"(\$env:<prefix>_\w*test\s*=|(^|[\s;&])<prefix>_\w*test\s*=\s*\S|export\s+<prefix>_\w*test)", low) \
    #         and "run_tests.py" not in low:
    #     return ("THE SCRIPT RULE: tests run through tools/run_tests.py ONLY.")
    #
    # 3. Text doctrine in commit messages (Everwood: no em/en dashes - commit
    #    subjects become the public changelog).
    # if re.search(r"\bgit\s+commit\b", low) and ("—" in cmd or "–" in cmd):
    #     return ("NO em or en dashes in commit messages - use a hyphen, colon or comma.")
    #
    # 4. Engine/config files that a shell write corrupts (Everwood: PowerShell's
    #    BOM breaks Godot's .tres parser).
    # if re.search(r"(set-content|out-file|add-content)[^|;\n]*\.tres\b", low) or \
    #         re.search(r">{1,2}\s*\"?[^\s\"|;]*\.tres\b", low):
    #     return ("Write resource files with the Write/Edit tool, never a shell redirect.")

    # THE BARE DEPLOY (C0003, 2026-11-06): the allow rule in settings.local.json
    # matches only the bare `python <door> <verb>` as the whole command; a cd
    # prefix, a chain, a pipe or a redirect hands the call to the auto-mode
    # classifier, which refuses a production deploy. Violated twice (2026-11-05
    # 16:17 and 2026-11-06 13:2x) in the Acme install, so the wrapped form is
    # refused here, before the classifier sees it, with the bare form named.
    for door in BARE_DOORS:
        d = re.escape(door)
        if re.search(r"(^|[\s;&|(])python\s+" + d, low) \
                and not re.fullmatch(r"\s*python\s+" + d + r"(\s+[^|&;><\n]*)?\s*", cmd):
            return ("THE BARE DEPLOY: run `python %s <verb>` as the WHOLE command, "
                    "alone in its call: no cd prefix, no chain, no pipe, no redirect. The allow rule "
                    "matches only that shape; a wrapped call goes to the classifier, which refuses it "
                    "(WORKFLOWS \"Deploy to the droplet\" step 3; C0003)." % door)

    return None


def _selftest():
    global BARE_DOORS
    BARE_DOORS = ("tools/deploy_droplet.py",)   # the selftest's own door
    cases = [
        ("echo x > .claude/settings.json", True),
        ("cat .claude/settings.json", False),
        ("python -m json.tool .claude/settings.json", False),
        ("cp a.json .claude/settings.json", True),
        ("Set-Content .claude/settings.json -Value x", True),
        ("sed -i 's/a/b/' \"Future Project MDs/hooks/settings.json\"", True),
        ("python - <<EOF\nopen('.claude/settings.json', 'w')\nEOF", True),
        ("echo x > .claude/settings.local.json", False),
        ("python tools/purpose_audit.py --flag x --does \"the guard copies settings.json wiring; open( in prose\"", False),
        ("git push --force", True),
        ("git push --force-with-lease", False),
        ("git commit --no-verify -m x", True),
        # THE BARE DEPLOY (C0003): the bare command passes, any wrap is refused
        ("python tools/deploy_droplet.py deploy", False),
        ("python tools/deploy_droplet.py status", False),
        ("python tools/deploy_droplet.py deploy main", False),
        ("cd \"C:/Users/x/Acme Co Program\" && python tools/deploy_droplet.py deploy 2>&1 | tail -6", True),
        ("python tools/deploy_droplet.py deploy | tail -3", True),
        ("python tools/deploy_droplet.py deploy && tail -1 docs/history/deploy_runs.txt", True),
        ("python tools/deploy_droplet.py deploy > out.txt", True),
        ("grep -n deploy_droplet.py WORKFLOWS.md | head", False),
    ]
    fails = 0
    for cmd, expect in cases:
        got = verdict(cmd) is not None
        print(("PASS  " if got == expect else "FAIL  ") + repr(cmd[:60]))
        fails += got != expect
    print("bash_guard selftest: %d failed" % fails)
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    data = read_input()
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return
    reason = verdict(cmd)
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()

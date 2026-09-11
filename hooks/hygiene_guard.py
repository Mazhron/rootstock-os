"""THE HYGIENE GUARD - Tier 3 (PostToolUse on Write|Edit|MultiEdit).

Mazhron 2026-09-11 ("we definitely don't want the readme falling behind
again"): the laws easiest to forget MID-BATCH are the ones that fire on a
file edit, not on a command - so the harness says them at the edit.

After every Write/Edit lands it looks at the file that changed and, when
one of these applies, hands the manager one line of context (never a
refusal, except the dash rule which BLOCKS so the line is fixed at once):

  KIT REFRESH  - the file is a portable original (a kit MD, a skill, a
                 hook, a reference tool): refresh its grab-copy in the kit
                 folder, UPGRADES.md + version bump if a concept changed,
                 the public README if a pillar/skill/hook/box item changed,
                 then sync_kit_repo.py. Editing a kit COPY directly names
                 the original instead. Editing the core instructions file
                 runs its lint at once and relays a FAIL.
  SEE-ALSO     - a touched section of a docs/systems wiki page carries no
                 "See also:" line (the link checker's hygiene rule, at the
                 moment of the edit instead of the next run).
  DASH         - player-facing text (data/*.tres, scripts/ui/*.gd,
                 DESCRIPTION.md, CHANGELOG.md) received an em or en dash
                 (the 2026-08-01 doctrine); the edit is BLOCKED with the
                 offending line so the sweep never runs again.
  IMPORT       - a new asset landed under Assets/: run the engine import
                 before the next test.

Stateless, no heavy imports, pattern matching only (~0.3 s interpreter
launch per edit is the whole cost). `--selftest` runs the in-process
checks. Everwood-specific names live in the CONFIG block at the top;
a kit install rewrites that block and nothing else.

Search keys: hygiene guard, PostToolUse, kit refresh reminder, see-also
lint, dash guard, import reminder, Tier 3.
See also: HOOKS_METHOD.md (Tier 3); docs/systems/tooling.md (The hooks);
tools/check_wiki_links.py (the after-the-fact twin of the See-also rule);
tools/sync_kit_repo.py (the README version check); WORKFLOWS.md "Edit the
future-project kit (Rootstock)".
"""
import json
import os
import re
import subprocess
import sys

from _hooklib import ROOT, read_input, emit

# ------------------------------------------------------------- CONFIG --
# The portable originals (repo-root MDs that have a grab-copy in the kit).
KIT_MDS = {
    "GODOT_FIELD_NOTES.md", "CLICKER_DESIGN_NOTES.md", "WIKI_METHOD.md",
    "SUBAGENT_METHOD.md", "REPORTING_METHOD.md", "WORKFLOW_METHOD.md",
    "SKILLS.md", "HOOKS_METHOD.md", "WORKSTATION_METHOD.md",
}
KIT_DIR = "Future Project MDs"           # the grab-copy folder (repo root)
KIT_ONLY = {"0 - READ ME FIRST, CLAUDE.md", "UPGRADES.md",  # no repo-root original
            "hooks/README.txt", "hooks/settings.json"}
SKILLS_DIR = ".claude/skills"
HOOKS_DIR = "tools/hooks"
REF_TOOLS_DIR = KIT_DIR + "/reference tools"
CORE_FILE = "CLAUDE.md"                  # its lint runs on edit
CORE_LINT = ["python", "tools/check_claude_md.py"]
KIT_SYNC = "python tools/sync_kit_repo.py"
README_HINT = "the public README (rootstock-os/README.md) if a pillar, skill, hook or box item changed"
WIKI_DIRS = ("docs/systems/",)           # See-also lint scope (= check_wiki_links.py)
PLAYER_TEXT = (                           # dash doctrine scope
    re.compile(r"^data/.*\.tres$"),
    re.compile(r"^scripts/ui/.*\.gd$"),
    re.compile(r"^(DESCRIPTION|CHANGELOG)\.md$"),
)
ASSET_DIR = "Assets/"
ASSET_EXT = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".ogg", ".wav", ".mp3")
IMPORT_HINT = "run `godot --headless --path . --import` before the next test"
# -----------------------------------------------------------------------

DASH = re.compile("[\u2014\u2013]")


def rel(path, cwd=None):
    """Repo-relative, forward slashes; None when the file is outside the repo."""
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(cwd or ROOT, path)
    p = os.path.normpath(os.path.abspath(p))
    root = os.path.normpath(ROOT)
    try:
        if os.path.commonpath([p.lower(), root.lower()]) != root.lower():
            return None
    except ValueError:
        return None
    return p[len(root):].lstrip("\\/").replace("\\", "/")


def new_texts(tool, tin):
    if tool == "Write":
        return [tin.get("content") or ""]
    if tool == "Edit":
        return [tin.get("new_string") or ""]
    if tool == "MultiEdit":
        return [(e or {}).get("new_string") or "" for e in tin.get("edits") or []]
    return []


# ------------------------------------------------------- the checks --
def kit_refresh(r, run_lint=True):
    """One line when a portable original (or a kit copy) changed."""
    name = os.path.basename(r)
    if r == CORE_FILE:
        if not run_lint:
            return "KIT/CORE: %s changed - its lint would run here" % r
        try:
            out = subprocess.run(CORE_LINT, cwd=ROOT, capture_output=True, text=True,
                                 timeout=20).stdout.strip()
        except Exception as e:  # noqa: BLE001 - a hook never crashes the turn
            out = "lint did not run (%s)" % e
        if "FAIL" in out:
            return "CORE LINT: " + out.replace("\n", " | ")
        return None
    if r in KIT_MDS:
        return ("KIT REFRESH: %s is a portable original - refresh '%s/%s' in this batch; "
                "UPGRADES.md entry + version bump if a concept changed; %s; then %s"
                % (r, KIT_DIR, name, README_HINT, KIT_SYNC))
    if r.startswith(SKILLS_DIR + "/") and name == "SKILL.md":
        skill = r.split("/")[2] if r.count("/") >= 3 else name
        return ("KIT REFRESH: skill '%s' is portable - refresh '%s/skills/%s/SKILL.md' and its "
                "SKILLS.md shelf entry (+ kit copy) in this batch; %s; then %s"
                % (skill, KIT_DIR, skill, README_HINT, KIT_SYNC))
    if r.startswith(HOOKS_DIR + "/") and r.endswith(".py") and "__pycache__" not in r:
        return ("KIT REFRESH: hook %s is portable - refresh '%s/hooks/%s', its HOOKS_METHOD.md "
                "tier text and hooks/README.txt in this batch; %s; then %s"
                % (name, KIT_DIR, name, README_HINT, KIT_SYNC))
    if r.startswith("tools/") and r.count("/") == 1 and r.endswith(".py"):
        try:
            refs = set(os.listdir(os.path.join(ROOT, REF_TOOLS_DIR)))
        except OSError:
            refs = set()
        if name in refs:
            return ("KIT REFRESH: %s has a kit reference copy - refresh '%s/%s' in this batch "
                    "(UPGRADES.md if its concept changed); then %s"
                    % (r, REF_TOOLS_DIR, name, KIT_SYNC))
        return None
    if r.startswith(KIT_DIR + "/"):
        sub = r[len(KIT_DIR) + 1:]
        if sub in KIT_ONLY:
            return ("KIT: %s is kit-only - if a concept entry was appended, bump CURRENT KIT "
                    "VERSION, keep the front door in step, refresh %s; then %s"
                    % (sub, README_HINT.split(" if ")[0], KIT_SYNC))
        if sub.startswith("reference tools/") or sub.startswith("hooks/") or sub.startswith("skills/"):
            return ("KIT COPY: %s is a grab-copy - the ORIGINAL lives in the repo (tools/, "
                    "tools/hooks/ or .claude/skills/); edit that and refresh the copy, "
                    "then %s" % (r, KIT_SYNC))
        if os.path.basename(sub) in KIT_MDS:
            return ("KIT COPY: %s is a grab-copy - edit the repo-root ORIGINAL %s and refresh "
                    "this copy, then %s" % (r, os.path.basename(sub), KIT_SYNC))
    return None


def _sections(lines):
    """[(heading_line_index, heading, body_lines)] for '## ' sections."""
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(lines)
        out.append((i, lines[i][3:].strip(), lines[i + 1:end]))
    return out


def see_also(r, texts, file_lines=None):
    """Touched docs/systems sections without a 'See also:' line."""
    if not any(r.startswith(d) for d in WIKI_DIRS) or not r.endswith(".md"):
        return None
    if file_lines is None:
        try:
            file_lines = open(os.path.join(ROOT, r), encoding="utf-8").read().split("\n")
        except OSError:
            return None
    secs = _sections(file_lines)
    if not secs:
        return None
    # Which sections did the edit touch? A Write touches all; an Edit
    # touches the section(s) containing any non-blank line of new_string.
    touched = []
    probe = [l.strip() for t in texts for l in t.split("\n") if l.strip()]
    for i, head, body in secs:
        if not probe:
            continue
        block = [l.strip() for l in [file_lines[i]] + body]
        if any(p in block for p in probe):
            touched.append((head, body))
    if not touched:
        return None
    missing = [h for h, body in touched
               if not any(l.lstrip().startswith("See also:") for l in body)]
    if not missing:
        return None
    return ("SEE-ALSO: %s - touched section(s) without a 'See also:' line: %s. Add one "
            "(topic -> file.md | ...) before moving on; the link checker reports it every run"
            % (r, "; ".join("## " + h for h in missing[:4])))


def dash(r, texts):
    """Em/en dash written into player-facing text -> the offending lines."""
    if not any(p.match(r) for p in PLAYER_TEXT):
        return None
    bad = []
    for t in texts:
        for l in t.split("\n"):
            if DASH.search(l):
                bad.append(l.strip()[:120])
    if not bad:
        return None
    return ("DASH: %s is player-facing text and the edit put an em/en dash into it "
            "(the 2026-08-01 doctrine: hyphen, colon or comma instead). Fix these lines now: %s"
            % (r, " || ".join(bad[:5])))


def asset_import(tool, r):
    if tool != "Write" or not r.startswith(ASSET_DIR) or not r.lower().endswith(ASSET_EXT):
        return None
    return "IMPORT: new asset %s - %s" % (r, IMPORT_HINT)


def evaluate(data, run_lint=True, file_lines=None):
    """-> (block_reason or None, [context lines])."""
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    if tool not in ("Write", "Edit", "MultiEdit"):
        return None, []
    r = rel(tin.get("file_path"), data.get("cwd"))
    if not r:
        return None, []
    texts = new_texts(tool, tin)
    block = dash(r, texts)
    ctx = [x for x in (kit_refresh(r, run_lint=run_lint),
                       see_also(r, texts, file_lines),
                       asset_import(tool, r)) if x]
    return block, ctx


# ------------------------------------------------------------ selftest --
def _selftest():
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    def run(tool, path, lines=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": {"file_path": path, **tin},
                         "cwd": ROOT}, run_lint=False, file_lines=lines)

    ap = lambda p: os.path.join(ROOT, p)  # noqa: E731
    b, c = run("Edit", ap("WIKI_METHOD.md"), old_string="a", new_string="b")
    check("portable MD -> kit refresh line naming the copy and the README",
          b is None and len(c) == 1 and "KIT REFRESH" in c[0]
          and "Future Project MDs/WIKI_METHOD.md" in c[0] and "README" in c[0])
    b, c = run("Edit", ap(".claude/skills/ship/SKILL.md"), old_string="a", new_string="b")
    check("skill -> kit refresh line naming skills/ship", c and "skills/ship/SKILL.md" in c[0])
    b, c = run("Edit", ap("tools/hooks/diet_guard.py"), old_string="a", new_string="b")
    check("hook -> kit refresh line naming hooks/ copy", c and "hooks/diet_guard.py" in c[0])
    b, c = run("Edit", ap("tools/standup.py"), old_string="a", new_string="b")
    check("reference tool -> refresh line", c and "reference tools/standup.py" in c[0])
    b, c = run("Edit", ap("tools/run_tests.py"), old_string="a", new_string="b")
    check("non-kit tool is silent", b is None and c == [])
    b, c = run("Edit", ap("Future Project MDs/WIKI_METHOD.md"), old_string="a", new_string="b")
    check("kit copy -> 'edit the original'", c and "KIT COPY" in c[0] and "WIKI_METHOD.md" in c[0])
    b, c = run("Edit", ap("Future Project MDs/UPGRADES.md"), old_string="a", new_string="b")
    check("UPGRADES.md -> version bump + README reminder", c and "CURRENT KIT VERSION" in c[0]
          and "README" in c[0])
    b, c = run("Edit", ap("Future Project MDs/hooks/README.txt"), old_string="a", new_string="b")
    check("kit-only hooks/README.txt is not called a copy", c and "KIT:" in c[0] and "KIT COPY" not in c[0])
    b, c = run("Edit", ap("CLAUDE.md"), old_string="a", new_string="b")
    check("core file -> lint hook point", c and "CORE" in c[0])
    b, c = run("Edit", ap("scripts/world/main.gd"), old_string="a", new_string="b")
    check("ordinary code file is silent", b is None and c == [])

    wiki = ["# T", "", "## One", "body one", "See also: x -> y.md", "", "## Two", "body two", ""]
    b, c = run("Edit", ap("docs/systems/soil.md"), lines=wiki, old_string="q", new_string="body two")
    check("touched section without See-also -> lint line naming it",
          c and "SEE-ALSO" in c[0] and "## Two" in c[0] and "## One" not in c[0])
    b, c = run("Edit", ap("docs/systems/soil.md"), lines=wiki, old_string="q", new_string="body one")
    check("touched section with See-also is silent", c == [])
    b, c = run("Write", ap("docs/systems/soil.md"), lines=wiki, content="\n".join(wiki))
    check("Write lints every section", c and "## Two" in c[0] and "## One" not in c[0])
    b, c = run("Edit", ap("docs/cold/soil.md"), lines=wiki, old_string="q", new_string="body two")
    check("cold shelf is out of scope", c == [])
    b, c = run("Edit", ap("CHANGELOG.md"), old_string="q", new_string="body two")
    check("root MD is out of See-also scope", not any("SEE-ALSO" in x for x in c))

    b, c = run("Edit", ap("data/species/oak.tres"), old_string="a", new_string="desc = \"tall \u2014 old\"")
    check("em dash in a .tres BLOCKS with the line", b and "DASH" in b and "tall" in b)
    b, c = run("Edit", ap("scripts/ui/menu.gd"), old_string="a", new_string="x = \"a \u2013 b\"")
    check("en dash in a UI script BLOCKS", b and "DASH" in b)
    b, c = run("Edit", ap("DESCRIPTION.md"), old_string="a", new_string="a \u2014 b")
    check("dash in DESCRIPTION.md BLOCKS", b and "DASH" in b)
    b, c = run("Edit", ap("data/species/oak.tres"), old_string="a", new_string="desc = \"tall - old\"")
    check("hyphen in a .tres passes", b is None)
    b, c = run("Edit", ap("docs/systems/soil.md"), lines=wiki, old_string="a", new_string="a \u2014 b")
    check("dash in an internal doc passes (docs are exempt)", b is None)
    b, c = run("Edit", ap("scripts/world/soil_grid.gd"), old_string="a", new_string="# a \u2014 b")
    check("dash in non-UI code passes", b is None)

    b, c = run("Write", ap("Assets/plants/oak.png"), content="")
    check("new asset -> import reminder", c and "IMPORT" in c[0])
    b, c = run("Edit", ap("Assets/plants/oak.png"), old_string="a", new_string="b")
    check("Edit of an asset is silent", c == [])

    b, c = run("Read", ap("WIKI_METHOD.md"))
    check("Read is ignored", b is None and c == [])
    b, c = evaluate({"tool_name": "Write", "tool_input": {"file_path": "C:/elsewhere/x.md",
                     "content": "a \u2014 b"}}, run_lint=False)
    check("file outside the repo is ignored", b is None and c == [])
    b, c = evaluate({}, run_lint=False)
    check("empty input is silent", b is None and c == [])

    print("hygiene_guard selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    data = read_input()
    if not data.get("tool_name"):
        return
    try:
        block, ctx = evaluate(data)
    except Exception as e:  # noqa: BLE001 - never crash the turn
        block, ctx = None, ["HYGIENE GUARD: skipped (%s)" % e]
    if block:
        emit({"decision": "block", "reason": "[HOOK hygiene_guard] " + block})
        return
    if ctx:
        emit({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                     "additionalContext": "[HOOK hygiene_guard] " + " || ".join(ctx)}})


if __name__ == "__main__":
    main()

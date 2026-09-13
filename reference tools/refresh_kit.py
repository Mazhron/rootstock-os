"""THE KIT REFRESH (the CEO's ruling 2026-09-13, INTENT.md "Rootstock is
updated and pushed whenever it is discussed").

PURPOSE: copy every portable ORIGINAL to its grab-copy in the kit folder
  (repo-root MDs, .claude/skills/*/SKILL.md, tools/hooks/*.py, the
  tools/*.py that have a reference copy), with the one substitution the
  kit carries in scripts (the owner's name -> "the CEO"); report the
  hand-adapted files it must never overwrite; `--check` only says what
  is out of step (the prompt hook's KIT UNSYNCED line).
INTENT: the CEO 2026-09-13: "Every time I discuss rootstock-os, or it's
  features, scripts, audits, intents, laws, etc. the intention is to
  update the future projects and rootstock-os folder and upload to git
  with updated readme and files whenever applicable." Refreshing by hand
  was the step that slipped; a script does it the same way every time.

    python tools/refresh_kit.py            # refresh every copy that differs; print what changed
    python tools/refresh_kit.py --check    # report only (exit 1 if anything is out of step)
    python tools/refresh_kit.py --dry-run  # show what would change
    python tools/refresh_kit.py --adopt tools/x.py   # add a NEW reference tool (or skill dir) to the kit

Never deletes: a file the kit has and the repo does not is reported, not
removed. ADAPTED files (hand-tailored copies, e.g. the shell guard with
its PROJECT RULES block) are named and skipped - diff them by hand when
the original changes. The mirror check (`--check`) also compares the kit
folder with the public repo clone so one line says both halves.

Search keys: kit refresh, grab-copy, refresh copies, kit unsynced, portable
originals, adopt a reference tool, CEO substitution, rootstock mirror.
See also: tools/sync_kit_repo.py (kit folder -> public repo; runs this
first); tools/hooks/prompt_gauge.py (the KIT UNSYNCED line); tools/hooks/
hygiene_guard.py (the reminder at the edit); WORKFLOWS.md "Edit the
future-project kit (Rootstock)"; INTENT.md.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ----------------------------------------------------------- CONFIG --
KIT_DIR = os.path.join(ROOT, "Future Project MDs")
KIT_REPO = os.path.normpath(os.path.join(ROOT, "..", "..", "..", "rootstock-os"))
HOOKS_DIR = os.path.join(ROOT, "tools", "hooks")
TOOLS_DIR = os.path.join(ROOT, "tools")
SKILLS_DIR = os.path.join(ROOT, ".claude", "skills")
ADAPTED = {"hooks/bash_guard.py"}          # hand-tailored kit copies: never overwritten
SUBST = [("the CEO's", "the CEO's"), ("the CEO", "the CEO")]   # scripts only; prose stays verbatim
JUNK = {"__pycache__", ".git"}
KEEP = {"README.md", "LICENSE", ".git"}    # kit-repo-only, never compared
# -----------------------------------------------------------------------


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def transform(text, is_script):
    if not is_script:
        return text
    for a, b in SUBST:
        text = text.replace(a, b)
    return text


def pairs():
    """[(original abs, kit-relative copy, is_script)] for every portable thing."""
    out = []
    kit_mds = {n for n in os.listdir(KIT_DIR) if n.endswith(".md")}
    for n in sorted(kit_mds):
        if os.path.isfile(os.path.join(ROOT, n)):
            out.append((os.path.join(ROOT, n), n, False))
    if os.path.isdir(SKILLS_DIR):
        for s in sorted(os.listdir(SKILLS_DIR)):
            src = os.path.join(SKILLS_DIR, s, "SKILL.md")
            if os.path.isfile(src):
                out.append((src, "skills/%s/SKILL.md" % s, False))
    if os.path.isdir(HOOKS_DIR):
        for f in sorted(os.listdir(HOOKS_DIR)):
            if f.endswith(".py"):
                out.append((os.path.join(HOOKS_DIR, f), "hooks/" + f, True))
    ref = os.path.join(KIT_DIR, "reference tools")
    if os.path.isdir(ref):
        for f in sorted(os.listdir(ref)):
            if f.endswith(".py") and os.path.isfile(os.path.join(TOOLS_DIR, f)):
                out.append((os.path.join(TOOLS_DIR, f), "reference tools/" + f, True))
    return out


def stale_copies():
    """[(kit-relative, reason)] where the kit copy differs from the transformed original."""
    out = []
    for src, rel, is_script in pairs():
        if rel in ADAPTED:
            continue
        dst = os.path.join(KIT_DIR, rel)
        want = transform(read(src), is_script)
        if not os.path.isfile(dst):
            out.append((rel, "no kit copy yet"))
        elif read(dst) != want:
            out.append((rel, "original changed"))
    return out


def mirror_diff():
    """Kit files whose public-repo twin is missing or different; None when no clone."""
    if not os.path.isdir(os.path.join(KIT_REPO, ".git")):
        return None
    out = []
    for base, dirs, files in os.walk(KIT_DIR):
        dirs[:] = [d for d in dirs if d not in JUNK]
        for f in files:
            if f.endswith(".pyc"):
                continue
            src = os.path.join(base, f)
            rel = os.path.relpath(src, KIT_DIR)
            dst = os.path.join(KIT_REPO, rel)
            if not os.path.isfile(dst) or read(src) != read(dst):
                out.append(rel.replace("\\", "/"))
    return out


def check_line():
    """One line for the prompt hook, or None when everything is in step."""
    parts = []
    st = stale_copies()
    if st:
        parts.append("%d original(s) newer than the kit copy (%s)" % (
            len(st), ", ".join(r for r, _ in st[:4]) + (", ..." if len(st) > 4 else "")))
    md = mirror_diff()
    if md:
        parts.append("%d kit file(s) not yet in the public mirror" % len(md))
    if not parts:
        return None
    return ("KIT UNSYNCED: " + "; ".join(parts) + " - `python tools/refresh_kit.py` then "
            "`python tools/sync_kit_repo.py` before the arc closes (the CEO 2026-09-13: "
            "whenever Rootstock is discussed, the kit and the public repo are updated)")


def refresh(dry_run=False):
    changed = []
    for src, rel, is_script in pairs():
        dst = os.path.join(KIT_DIR, rel)
        if rel in ADAPTED:
            print("ADAPTED (not auto-refreshed; diff by hand if the original changed): %s" % rel)
            continue
        want = transform(read(src), is_script)
        if os.path.isfile(dst) and read(dst) == want:
            continue
        changed.append(rel)
        print(("would refresh " if dry_run else "refreshed ") + rel)
        if not dry_run:
            write(dst, want)
    return changed


def adopt(path):
    p = os.path.abspath(path)
    if os.path.isdir(p) and os.path.isfile(os.path.join(p, "SKILL.md")):
        rel = "skills/%s/SKILL.md" % os.path.basename(p.rstrip("\\/"))
        write(os.path.join(KIT_DIR, rel), read(os.path.join(p, "SKILL.md")))
    elif p.endswith(".py") and os.path.dirname(p).lower() == TOOLS_DIR.lower():
        rel = "reference tools/" + os.path.basename(p)
        write(os.path.join(KIT_DIR, rel), transform(read(p), True))
    elif p.endswith(".py") and os.path.dirname(p).lower() == HOOKS_DIR.lower():
        rel = "hooks/" + os.path.basename(p)
        write(os.path.join(KIT_DIR, rel), transform(read(p), True))
    else:
        raise SystemExit("adopt takes a tools/*.py, a tools/hooks/*.py or a .claude/skills/<name> dir")
    print("adopted %s -> %s (add its UPGRADES.md entry, README box line and front-door step this batch)"
          % (path, rel))


def main(argv):
    if "--adopt" in argv:
        adopt(argv[argv.index("--adopt") + 1])
        return 0
    if "--check" in argv:
        line = check_line()
        print(line or "kit in step: every copy matches its original and the public mirror")
        return 1 if line else 0
    changed = refresh(dry_run="--dry-run" in argv)
    print("%d cop%s %s" % (len(changed), "y" if len(changed) == 1 else "ies",
                           "would change" if "--dry-run" in argv else "refreshed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

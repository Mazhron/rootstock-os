"""THE LOCAL MIRROR (the CEO 2026-09-20: "use J:\\Claude Project Backups").

After the 48k-file report the CEO asked for a fallback copy that does not
live on the same disk as the working tree. A BARE MIRROR is a git repo
with no working folder: only the object store and refs, the same thing
GitHub holds. Every commit, branch and tag of Everwood and rootstock-os
is pushed there, so a wiped working tree (or a wiped GitHub) is restored
with one `git clone`. It is NOT a browsable folder copy - untracked files
(build zips, user://, caches) are not in it, by design; git tracks what
matters.

Each repo carries a remote named `backup` (added by hand once per
workstation: `git remote add backup "J:/Claude Project Backups/<name>.git"`,
the bare repo made with `git init --bare`). This script pushes `--all`
and `--tags` to it (never `--mirror`: a mirror push PRUNES refs the
local side lacks, and nothing here deletes). A repo without the remote,
or a drive that is not mounted, is reported and skipped, never an error
that blocks a ship.

THE BROWSABLE COPY (the CEO 2026-09-20, the same evening: "Yes, I want
a plain browsable copy of the working folder in J"): after the pushes,
the Everwood working tree is robocopied to a plain folder BESIDE the
mirror (J:/Claude Project Backups/Everwood) that Explorer opens like the
original - build zips, the untracked GIMP palettes, everything the mirror
leaves out. /E adds and updates and never deletes (no /MIR, no /PURGE:
THE PRESERVATION LAW, and the preserve guard refuses those switches), so
a file retired here stays there as an "extra". .godot (the import cache,
rebuilt by --import) and .git (the mirror holds the history) are skipped.
The first copy moves a few GB; later runs copy only what changed.

Runs: the ship skill (after the origin push), the checkpoint skill,
run_all's `backup` group (in the session composite, so every standup
also refreshes the mirror), and the SessionEnd auto-checkpoint hook.

Usage:
  python tools/backup_push.py              # push both repos + folder copy, ledger
  python tools/backup_push.py --status     # show remotes, drive, copy; do nothing
  python tools/backup_push.py --no-folder  # pushes only (a quick hook path)

Ledger: docs/history/backup_runs.txt
  date time | ws | repo | remote | result   (repo "Everwood-folder" = the copy)

PURPOSE: Push every branch and tag of Everwood and rootstock-os to their
  bare `backup` remotes on the J: drive, then robocopy the Everwood
  working tree to a browsable folder beside the mirror (add/update only,
  never delete), one ledger line each, skipping (never failing) a repo
  whose remote or drive is absent.
INTENT: the CEO 2026-09-20: a real copy of the whole history on another
  SSD so the 48k-file catastrophe, or a lost GitHub, costs one clone; and
  a plain folder he can open without git.

Search keys: backup, mirror, bare repo, J drive, second copy, fallback,
push all, disaster recovery, browsable copy, folder copy, robocopy.
See also: WORKFLOWS.md "Ship a batch"; .claude/skills/ship; .claude/skills/
checkpoint; tools/hooks/session_end.py; docs/systems/tooling.md.
"""
import argparse
import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT_REPO = os.path.normpath(os.path.join(ROOT, "..", "..", "..", "rootstock-os"))
LEDGER = os.path.join(ROOT, "docs", "history", "backup_runs.txt")
REMOTE = "backup"
REPOS = [("Everwood", ROOT), ("rootstock-os", KIT_REPO)]

# THE BROWSABLE COPY (the CEO 2026-09-20: "Yes, I want a plain browsable
# copy of the working folder in J"). Beside the bare mirror, a plain folder
# copy of the working tree that Explorer can open: build zips, the untracked
# GIMP palettes, everything the mirror leaves out. robocopy /E adds and
# updates, never deletes (no /MIR, no /PURGE - THE PRESERVATION LAW; the
# preserve guard refuses those switches). Two folders are skipped: .godot
# (the import cache, 1.2 GB, rebuilt by --import) and .git (the mirror
# beside it already holds the history). The target sits next to the mirror:
# <mirror parent>/<name>, e.g. J:/Claude Project Backups/Everwood.
FOLDERS = [("Everwood", ROOT)]
FOLDER_SKIP_DIRS = [".godot", ".git"]


def which_ws():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def remote_url(cwd):
    r = git(["remote", "get-url", REMOTE], cwd)
    return r.stdout.strip() if r.returncode == 0 else None


def ledger(name, url, result):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    fresh = not os.path.isfile(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write("# BACKUP PUSHES (append-only; one line per repo per run). "
                     "date time | ws | repo | remote | result\n")
        fh.write("%s | %s | %s | %s | %s\n" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), which_ws(),
            name, url or "-", result))


def push_one(name, cwd, status_only):
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return "skipped: no repo at %s" % cwd, None
    url = remote_url(cwd)
    if not url:
        return "skipped: no `%s` remote (add it once per workstation)" % REMOTE, None
    if not os.path.isdir(url):
        return "skipped: mirror path not mounted (%s)" % url, url
    if status_only:
        head = git(["rev-parse", "--short", "HEAD"], cwd).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd).stdout.strip() or "main"
        there = git(["rev-parse", "--short", "refs/heads/" + branch], url).stdout.strip()
        return "ready (local %s, mirror %s)" % (head, there or "empty"), url
    a = git(["push", REMOTE, "--all"], cwd)
    t = git(["push", REMOTE, "--tags"], cwd)
    if a.returncode or t.returncode:
        err = (a.stderr + t.stderr).strip().splitlines()
        return "FAIL: %s" % (err[-1] if err else "push error"), url
    head = git(["rev-parse", "--short", "HEAD"], cwd).stdout.strip()
    return "ok (HEAD %s)" % head, url


def folder_target(cwd, name):
    """The browsable copy lives beside the mirror: <mirror parent>/<name>."""
    url = remote_url(cwd)
    if not url:
        return None
    return os.path.normpath(os.path.join(os.path.dirname(url.rstrip("/\\")), name))


def copy_folder(name, cwd, status_only):
    """robocopy the working tree to its browsable copy. Adds + updates only."""
    target = folder_target(cwd, name)
    if not target:
        return "skipped: no `%s` remote (the copy sits beside the mirror)" % REMOTE, None
    if not os.path.isdir(os.path.dirname(target)):
        return "skipped: backup drive not mounted (%s)" % os.path.dirname(target), target
    if status_only:
        if not os.path.isdir(target):
            return "ready (copy not made yet)", target
        n = sum(len(f) for _, _, f in os.walk(target))
        return "ready (copy holds %d files)" % n, target
    if os.name != "nt":
        return "skipped: robocopy is Windows-only", target
    cmd = ["robocopy", cwd, target, "/E", "/R:1", "/W:1",
           "/NFL", "/NDL", "/NJH", "/NP", "/XD"] + FOLDER_SKIP_DIRS
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    # robocopy exit codes: bits 1 copied, 2 extras, 4 mismatched; 8+ = failure.
    if r.returncode >= 8:
        tail = [l for l in r.stdout.splitlines() if l.strip()]
        return "FAIL: robocopy exit %d (%s)" % (r.returncode, tail[-1] if tail else "?"), target
    copied = extras = "?"
    for line in r.stdout.splitlines():
        if line.strip().startswith("Files :"):
            cols = line.split(":", 1)[1].split()
            if len(cols) >= 6:
                copied, extras = cols[1], cols[5]
    return "ok (copied %s files, %s extra kept)" % (copied, extras), target


def main():
    ap = argparse.ArgumentParser(description="Push all refs to the bare backup remotes")
    ap.add_argument("--status", action="store_true", help="show, push nothing")
    ap.add_argument("--no-folder", action="store_true",
                    help="mirror push only, skip the browsable folder copy")
    args = ap.parse_args()
    failed = False
    for name, cwd in REPOS:
        result, url = push_one(name, cwd, args.status)
        print("BACKUP %s -> %s: %s" % (name, url or "(no remote)", result))
        if not args.status:
            ledger(name, url, result)
        failed = failed or result.startswith("FAIL")
    if not args.no_folder:
        for name, cwd in FOLDERS:
            result, target = copy_folder(name, cwd, args.status)
            print("BACKUP %s-folder -> %s: %s" % (name, target or "(no target)", result))
            if not args.status:
                ledger(name + "-folder", target, result)
            failed = failed or result.startswith("FAIL")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

"""Suggests a version-bump size for the batch being shipped.

PURPOSE: Print a suggested version-bump size for the batch being shipped;
  the hint is advice only, a human decides; never edits any file except its
  own ledger.
INTENT: The ship ritual asks "bump if the batch warrants it"; a scripted
  first pass makes that a reading instead of a guess (the CEO 2026-09-29:
  "Do it if it makes sense").
Search keys: version bump, semantic versioning, changelog, shipment, batch,
  release, patch, minor.
See also: .claude/skills/ship/SKILL.md step 2; project.godot;
  docs/history/version_hint_runs.txt.
"""
import datetime
import os
import re
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_GODOT = os.path.join(ROOT, "project.godot")
LEDGER = os.path.join(ROOT, "docs", "history", "version_hint_runs.txt")
HEADER = ("# THE VERSION HINT LEDGER: one line per ship-time hint "
          "(tools/version_hint.py); the hint is advice, the bump is the owner's\n")


def workstation():
    """Detect workstation from home directory."""
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def get_version():
    """Extract version from project.godot."""
    try:
        with open(PROJECT_GODOT, 'r') as f:
            for line in f:
                match = re.search(r'config/version="([^"]+)"', line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"ERROR reading project.godot: {e}", file=sys.stderr)
    return None


def get_last_version_commit():
    """Find the last commit that changed the version line."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "-G", "config/version=",
             "--", "project.godot"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        commit = result.stdout.strip()
        return commit if commit else None
    except Exception as e:
        print(f"ERROR running git log: {e}", file=sys.stderr)
        return None


def get_diff_rows(commit_hash):
    """Get (status, path) tuples from git diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status",
             f"{commit_hash}..HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        rows = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                status, path = parts
                # Normalize path to forward slashes
                path = path.replace('\\', '/')
                rows.append((status, path))
        return rows
    except Exception as e:
        print(f"ERROR running git diff: {e}", file=sys.stderr)
        return []


def count_commits(commit_hash):
    """Count commits from commit_hash to HEAD."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{commit_hash}..HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        return int(result.stdout.strip())
    except Exception as e:
        print(f"ERROR running git rev-list: {e}", file=sys.stderr)
        return 0


def classify(rows):
    """Classify changes and return (size, reason).

    Args:
        rows: list of (status, path) tuples with forward slashes

    Returns:
        tuple of (size_str, reason_str)
    """
    game_paths = []
    new_game_paths = []

    for status, path in rows:
        is_game = (path.startswith("scripts/") or
                   path.startswith("scenes/") or
                   path.startswith("shaders/") or
                   path.startswith("data/"))

        if is_game:
            game_paths.append((status, path))
            if status.startswith("A"):
                new_game_paths.append(path)

    # No game path changed
    if not game_paths:
        return ("none", "docs and tools only")

    # Every changed game path is under data/
    all_data = all(path.startswith("data/") for _, path in game_paths)
    if all_data:
        count = len(game_paths)
        plural = "file" if count == 1 else "files"
        return ("patch", f"balance data only: {count} {plural}")

    # Any row with status starting "A" under scripts/ or scenes/
    if new_game_paths:
        new_under_code = [p for p in new_game_paths
                          if p.startswith("scripts/") or p.startswith("scenes/")]
        if new_under_code:
            return ("minor", f"new scene or script: {new_under_code[0]}")

    # Otherwise
    count = len(game_paths)
    plural = "file" if count == 1 else "files"
    return ("patch", f"{count} {plural} changed, none new")


def append_ledger(version, commits, size, reason):
    """Append one line to the ledger."""
    # Create header if file doesn't exist
    if not os.path.exists(LEDGER):
        try:
            os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
            with open(LEDGER, 'w') as f:
                f.write(HEADER)
        except Exception as e:
            print(f"ERROR creating ledger file: {e}", file=sys.stderr)
            return

    # Append ledger line
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M")
    ws = workstation()
    line = f"{date_time} | {ws} | {version} | {commits} | {size} | {reason}\n"

    try:
        with open(LEDGER, 'a') as f:
            f.write(line)
    except Exception as e:
        print(f"ERROR appending to ledger: {e}", file=sys.stderr)


def run_selftest():
    """Run selftest on classify() with hand-built row lists."""
    tests = [
        # Test 1: no game path changed
        {
            "name": "docs_and_tools_only",
            "rows": [
                ("M", "README.md"),
                ("M", "CHANGELOG.md"),
                ("M", "tools/other.py"),
            ],
            "expected": ("none", "docs and tools only"),
        },
        # Test 2: every changed game path is under data/
        {
            "name": "balance_data_only",
            "rows": [
                ("M", "data/species/oak.tres"),
                ("M", "data/species/birch.tres"),
                ("A", "data/balance/new_crop.tres"),
            ],
            "expected": ("patch", "balance data only: 3 files"),
        },
        # Test 3: new scene or script
        {
            "name": "new_scene",
            "rows": [
                ("A", "scenes/new_ui.tscn"),
                ("M", "scripts/core/game.gd"),
                ("M", "data/species/oak.tres"),
            ],
            "expected": ("minor", "new scene or script: scenes/new_ui.tscn"),
        },
        # Test 4: game files changed, none new
        {
            "name": "game_files_changed",
            "rows": [
                ("M", "scripts/core/game.gd"),
                ("M", "shaders/effect.gdshader"),
                ("M", "README.md"),
            ],
            "expected": ("patch", "2 files changed, none new"),
        },
    ]

    failed = 0
    for test in tests:
        result = classify(test["rows"])
        if result == test["expected"]:
            print(f"PASS  {test['name']}")
        else:
            print(f"FAIL  {test['name']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Got:      {result}")
            failed += 1

    print(f"version_hint selftest: {failed} failed")
    return 1 if failed > 0 else 0


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(run_selftest())

    # Get current version
    version = get_version()
    if not version:
        print("VERSION HINT: unknown (could not read version from project.godot)")
        return 0

    # Get last version commit
    last_commit = get_last_version_commit()
    if not last_commit:
        print("VERSION HINT: unknown (no version commit found)")
        return 0

    # Get diff and commit count
    diff_rows = get_diff_rows(last_commit)
    commits = count_commits(last_commit)

    # Classify changes
    size, reason = classify(diff_rows)

    # Print hint
    print(f"VERSION HINT: {size} (v{version}, {commits} commit(s) since the bump) - {reason}")

    # Append to ledger
    append_ledger(version, commits, size, reason)

    return 0


if __name__ == "__main__":
    sys.exit(main())

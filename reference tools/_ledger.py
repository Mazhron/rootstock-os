"""Shared helper: append a ledger line unless it duplicates the last one.

PURPOSE: One append_unless_identical() call site for the check-script
  ledgers (format_lint, purpose_audit, readme_lint, check_wiki_links and, since
  2026-09-20, lesson_log's CHECK line) so a rerun at an unchanged tree does not
  grow duplicate rows.
INTENT: 2026-09-14 owner ruling, on duplicate ledger rows appearing minutes
  apart (once via `python tools/run_all.py check`, again inside
  tools/sync_kit_repo.py's push gates, at an unchanged kit version): "How
  do we solve this?" - and on adding a trust-the-ledger guard here too:
  "Add the trust-the-ledger guard if it makes sense... The manager's
  decision: it makes sense - one shared helper, four call sites. Mirrors
  the spirit and wording of tools/run_tests.py's existing TRUST THE LEDGER
  guard for test groups, applied to these four result ledgers instead.

Search keys: trust the ledger, duplicate ledger rows, append_unless_identical,
ledger dedupe, ledger_heads, identical result not re-appended.
See also: tools/run_tests.py (the original TRUST THE LEDGER guard, test
groups); tools/format_lint.py, tools/purpose_audit.py, tools/readme_lint.py,
tools/check_wiki_links.py (the four callers); docs/history/ledger_heads.txt
(the sidecar state this module keeps); REPORTING_METHOD.md (the ledger law).
"""
import datetime
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(ROOT, "docs", "history", "ledger_heads.txt")

# These files are themselves the thing being appended to (or the sidecar that
# tracks it), so their own git status is excluded from the dirty signature -
# otherwise a script's own append would dirty the tree it just checked and
# no rerun could ever be trusted as "unchanged" again.
LEDGER_BASENAMES = {
    "format_lint_runs.txt", "purpose_audit_runs.txt", "readme_lint_runs.txt",
    "wiki_link_runs.txt", "ledger_heads.txt", "lesson_runs.txt",
}


def _git_state(root=ROOT):
    """Return (short HEAD hash, dirty-signature) or (None, None) if git is
    unavailable - callers must treat None as "unknown, never skip"."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root,
            capture_output=True, text=True, timeout=10)
        if head.returncode != 0:
            return None, None
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root,
            capture_output=True, text=True, timeout=10)
        kept = []
        for raw in status.stdout.splitlines():
            path_part = raw[3:] if len(raw) > 3 else ""
            if " -> " in path_part:
                path_part = path_part.split(" -> ")[-1]
            path_part = path_part.strip().strip('"')
            if os.path.basename(path_part) in LEDGER_BASENAMES:
                continue
            kept.append(raw)
        dirty_sig = hashlib.sha1("\n".join(kept).encode("utf-8")).hexdigest()[:12]
        return head.stdout.strip(), dirty_sig
    except (OSError, subprocess.SubprocessError):
        return None, None


def _last_data_line(path):
    """The last non-blank, non-comment line already in the ledger, or None."""
    if not os.path.isfile(path):
        return None
    last = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            s = raw.rstrip("\n")
            if not s or s.startswith("#"):
                continue
            last = s
    return last


def _read_state(state_path):
    """basename -> (head, dirty, last_appended_date_time)."""
    entries = {}
    if os.path.isfile(state_path):
        with open(state_path, encoding="utf-8") as fh:
            for raw in fh:
                s = raw.rstrip("\n")
                if not s or s.startswith("#"):
                    continue
                parts = [p.strip() for p in s.split(" | ")]
                if len(parts) >= 4:
                    entries[parts[0]] = (parts[1], parts[2], parts[3])
    return entries


def _write_state(state_path, entries):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    lines = ["# LEDGER HEADS (rewritten in place; one line per ledger). Used by\n",
             "# tools/_ledger.py to know whether HEAD/tree changed since a ledger's\n",
             "# last appended line - not append-only, this one small state file is\n",
             "# meant to be rewritten (the ledgers themselves never are).\n",
             "# ledger basename | head hash | dirty signature | last appended date time\n"]
    for basename in sorted(entries):
        head, dirty, when = entries[basename]
        lines.append("%s | %s | %s | %s\n" % (basename, head, dirty, when))
    with open(state_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)


def append_unless_identical(ledger_path, line, payload_from_col=2, note_prefix="",
                             state_path=None, head_provider=None):
    """Append `line` to the ledger at `ledger_path` unless the ledger's last
    data line is identical from `payload_from_col` onward, dated today, and
    HEAD/tree are unchanged since that line was written. Returns True if the
    line was appended, False if the append was skipped as a duplicate.
    """
    if not line.endswith("\n"):
        line += "\n"
    state_path = state_path or STATE_PATH
    head_provider = head_provider or _git_state
    basename = os.path.basename(ledger_path)

    new_parts = line.rstrip("\n").split(" | ")
    last_line = _last_data_line(ledger_path)
    head, dirty = head_provider()
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    skip = False
    if last_line is not None and head is not None:
        last_parts = last_line.split(" | ")
        if len(new_parts) > payload_from_col and len(last_parts) > payload_from_col:
            payload_new = " | ".join(new_parts[payload_from_col:])
            payload_last = " | ".join(last_parts[payload_from_col:])
            last_date = last_parts[0].strip().split(" ")[0]
            prev = _read_state(state_path).get(basename)
            if (payload_new == payload_last and last_date == today and
                    prev is not None and prev[0] == head and prev[1] == dirty):
                skip = True

    if skip:
        last_time = last_line.split(" | ")[0].strip()
        print("%sTRUST THE LEDGER: identical %s result at %s (HEAD %s, tree unchanged) "
              "- not re-appended" % (note_prefix, basename, last_time, head))
        return False

    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as fh:
        fh.write(line)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entries = _read_state(state_path)
    entries[basename] = (head if head is not None else "?",
                          dirty if dirty is not None else "?", now)
    _write_state(state_path, entries)
    return True


def selftest():
    # THE PRESERVATION LAW: this leaves its scratch files on disk rather than
    # deleting them (nothing here runs a delete) - a fresh temp subfolder per
    # run keeps that harmless.
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ledger_selftest_")
    ok = True
    ledger_path = os.path.join(tmp, "fake_runs.txt")
    state_path = os.path.join(tmp, "ledger_heads.txt")
    with open(ledger_path, "w", encoding="utf-8") as fh:
        fh.write("# fake ledger: date | ws | items | result\n")

    box = {"head": "abc123", "dirty": "d1"}

    def provider():
        return box["head"], box["dirty"]

    # 1) first data line always appends.
    r1 = append_unless_identical(
        ledger_path, "2026-09-14 10:00 | WS1 | 5 | PASS\n",
        payload_from_col=2, state_path=state_path, head_provider=provider)
    ok = ok and r1 is True
    print("append (first line):", "PASS" if r1 else "FAIL")

    # 2) identical payload, same day, unchanged HEAD/tree -> skip.
    r2 = append_unless_identical(
        ledger_path, "2026-09-14 10:05 | WS1 | 5 | PASS\n",
        payload_from_col=2, state_path=state_path, head_provider=provider)
    ok = ok and r2 is False
    print("skip (identical, unchanged):", "PASS" if r2 is False else "FAIL")

    # 3) HEAD changes -> append again even though payload is identical.
    box["head"] = "def456"
    r3 = append_unless_identical(
        ledger_path, "2026-09-14 10:10 | WS1 | 5 | PASS\n",
        payload_from_col=2, state_path=state_path, head_provider=provider)
    ok = ok and r3 is True
    print("append (after HEAD change):", "PASS" if r3 else "FAIL")

    # 4) different payload, same HEAD -> append.
    r4 = append_unless_identical(
        ledger_path, "2026-09-14 10:15 | WS1 | 6 | FAIL\n",
        payload_from_col=2, state_path=state_path, head_provider=provider)
    ok = ok and r4 is True
    print("append (payload changed):", "PASS" if r4 else "FAIL")

    # 5) identical payload but last line is from a prior day -> append.
    with open(ledger_path, "a", encoding="utf-8") as fh:
        fh.write("2020-01-01 00:00 | WS1 | 6 | FAIL\n")
    entries = _read_state(state_path)
    entries["fake_runs.txt"] = (box["head"], box["dirty"], "2020-01-01 00:00")
    _write_state(state_path, entries)
    r5 = append_unless_identical(
        ledger_path, "2026-09-14 10:20 | WS1 | 6 | FAIL\n",
        payload_from_col=2, state_path=state_path, head_provider=provider)
    ok = ok and r5 is True
    print("append (last line stale, prior day):", "PASS" if r5 else "FAIL")

    # 6) git unavailable (head is None) -> never skip.
    def no_git():
        return None, None
    r6 = append_unless_identical(
        ledger_path, "2026-09-14 10:20 | WS1 | 6 | FAIL\n",
        payload_from_col=2, state_path=state_path, head_provider=no_git)
    ok = ok and r6 is True
    print("append (git unavailable):", "PASS" if r6 else "FAIL")

    print("OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print("tools/_ledger.py is a library module - import append_unless_identical(); "
          "run with --selftest to exercise it.")

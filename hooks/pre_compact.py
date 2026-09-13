"""PreCompact hook: ledger every compaction (Tier 1, #4).

Appends one line to docs/history/compact_runs.txt - when, which WS,
version, manual/auto, context load, unbanked task count - so we can see
how often the lossy summary fires versus our lossless checkpoints. The
SessionStart hook re-injects the standup digest right after, which is the
real recovery; this hook only keeps the receipt.

Answers `--selftest` (house pattern: PASS/FAIL lines on a stub ledger,
never the real one).

PURPOSE: PreCompact hook that appends one ledger line per compaction (when,
  workstation, version, manual or auto trigger, context load, unbanked task
  count) to docs/history/compact_runs.txt, and on an auto trigger tells the
  manager the session_start hook will re-inject the standup digest right
  after.
INTENT: keeps a receipt of how often the harness's lossy auto-compact fires
  versus the project's lossless checkpoints, so the pattern is visible
  without re-reading anything.

Search keys: compact hook, auto compact ledger, compaction count.
See also: docs/history/compact_runs.txt (the ledger); tools/hooks/
session_start.py (the recovery); REPORTING_METHOD.md (the Ledger rule).
"""
import datetime
import os
import sys

from _hooklib import ROOT, emit, project_version, read_input
import checkpoint as cp

DEFAULT_LEDGER = os.path.join(ROOT, "docs", "history", "compact_runs.txt")


def ledger_line(ws, version, trigger, ctx, n, now):
    """The one data line this hook appends per compaction."""
    return "%s | %s | %s | %s | %s | tasks %d\n" % (
        now.strftime("%Y-%m-%d %H:%M"), ws, version, trigger, ctx, n)


def append_ledger(ws, version, trigger, ctx, n, now, ledger=DEFAULT_LEDGER):
    new = not os.path.isfile(ledger)
    with open(ledger, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# COMPACT RUNS (PreCompact hook): every harness "
                     "compaction - when | WS | version | manual/auto | "
                     "context load | unbanked tasks. Read the TAIL.\n")
        fh.write(ledger_line(ws, version, trigger, ctx, n, now))


def main():
    data = read_input()
    trigger = data.get("trigger", "?")
    ws = cp.which_ws()
    n = cp.load().get(ws, (0, ""))[0]
    load_ = cp.context_load()
    ctx = "ctx ~%dk" % (load_ // 1000) if load_ else "ctx ?"
    append_ledger(ws, project_version(), trigger, ctx, n,
                  datetime.datetime.now())
    if trigger == "auto":
        emit({"systemMessage": "[hook] auto-compact fired (%s, %d unbanked "
                               "tasks) - the summary is lossy; the standup "
                               "digest will be re-injected after it."
                               % (ctx, n)})


def _selftest():
    """Appends to a temp ledger only - never touches the real one."""
    import tempfile
    fails = 0
    tmpdir = tempfile.mkdtemp()
    ledger = os.path.join(tmpdir, "compact_runs.txt")
    now = datetime.datetime(2026, 9, 13, 12, 0)
    append_ledger("WS1", "0.1.0-alpha", "pipe-test", "ctx ~1k", 3, now,
                  ledger=ledger)
    lines = open(ledger, encoding="utf-8").readlines()
    ok = len(lines) == 2 and lines[0].startswith("# COMPACT RUNS")
    print(("PASS  " if ok else "FAIL  ") + "header line written on a new ledger")
    fails += not ok
    line = ledger_line("WS1", "0.1.0-alpha", "pipe-test", "ctx ~1k", 3, now)
    ok = len(line.rstrip("\n").split(" | ")) == 6
    print(("PASS  " if ok else "FAIL  ") + "data line carries the 6 fields")
    fails += not ok
    print("pre_compact selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

"""PreCompact hook: ledger every compaction (Tier 1, #4).

Appends one line to docs/history/compact_runs.txt - when, which WS,
version, manual/auto, context load, unbanked task count - so we can see
how often the lossy summary fires versus our lossless checkpoints. The
SessionStart hook re-injects the standup digest right after, which is the
real recovery; this hook only keeps the receipt.

Search keys: compact hook, auto compact ledger, compaction count.
See also: docs/history/compact_runs.txt (the ledger); tools/hooks/
session_start.py (the recovery); REPORTING_METHOD.md (the Ledger rule).
"""
import datetime
import os

from _hooklib import ROOT, emit, project_version, read_input
import checkpoint as cp

data = read_input()
trigger = data.get("trigger", "?")
ws = cp.which_ws()
n = cp.load().get(ws, (0, ""))[0]
load_ = cp.context_load()
ctx = "ctx ~%dk" % (load_ // 1000) if load_ else "ctx ?"
ledger = os.path.join(ROOT, "docs", "history", "compact_runs.txt")
new = not os.path.isfile(ledger)
with open(ledger, "a", encoding="utf-8") as fh:
    if new:
        fh.write("# COMPACT RUNS (PreCompact hook): every harness compaction - "
                 "when | WS | version | manual/auto | context load | unbanked "
                 "tasks. Read the TAIL.\n")
    fh.write("%s | %s | %s | %s | %s | tasks %d\n" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ws,
        project_version(), trigger, ctx, n))
if trigger == "auto":
    emit({"systemMessage": "[hook] auto-compact fired (%s, %d unbanked tasks) "
                           "- the summary is lossy; the standup digest will be "
                           "re-injected after it." % (ctx, n)})

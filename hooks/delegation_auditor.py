"""PostToolUse auditor on Agent/Task: the fabrication check runs itself
(the CEO 2026-09-26: "make these processes more fool proof... through
hooks").

The moment an employee's report lands, this hook reads the harness's own
metered figures out of the tool result - the numbers no model can fake -
and does mechanically what SUBAGENTS.md asked the manager to remember:
rule 9 (0 metered tool calls on a work task = a fabricated report), the
rule 3 cross-check (the report's TOOLS line against the meter), the
report-shape check (STAMP / TOOLS / WORKFLOW / INTENT lines present),
and rule 5's first half - one PENDING line appended to
docs/history/delegation_pending.txt with the metered truth, so no
delegation can silently vanish before it is verified and ledgered.
Resolution is a NEW line (append-only, read at the tail, never an edit):
`RESOLVED | <id> | OK/CORRECTED - <words>` after the manager verifies
cheap and writes the SUBAGENTS.md ledger line. verify_advisor refuses to
end a turn while a PENDING id has no RESOLVED line. Read-only searcher
types get the fabrication glance only, no pending line.

PURPOSE: PostToolUse hook that reads the harness-metered tool and token
  figures from an Agent/Task result, warns on rule 9's fabrication tell,
  a TOOLS-line mismatch or a malformed report, and appends one PENDING
  line per work delegation to docs/history/delegation_pending.txt for
  verify_advisor to hold open until a RESOLVED line follows.
INTENT: the CEO 2026-09-26: "Can we make these processes more fool proof
  in any way through hooks" - born of the Reddit case he relayed the same
  day: a manager that said its employees did their job when they had not.

Search keys: delegation auditor, fabrication check, rule 9, metered
tokens, tool_uses, pending ledger, RESOLVED line, TOOLS line mismatch.
See also: SUBAGENTS.md (rules 3, 5, 9); tools/hooks/verify_advisor.py
(the stop end); tools/hooks/brief_guard.py (the dispatch end);
docs/history/delegation_pending.txt (the pending ledger).
"""
import hashlib
import os
import re
import sys
import time

from _hooklib import ROOT, TOOLS, context, read_input

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

PENDING = os.path.join(ROOT, "docs", "history", "delegation_pending.txt")
READONLY_TYPES = {"explore", "plan", "claude-code-guide", "statusline-setup"}
TEMPLATE_LINES = ("STAMP:", "TOOLS:", "WORKFLOW:", "INTENT:")
# Metered-figure keys, lowercased with _ stripped: the harness's own count
# of the employee's tool calls and tokens (field names vary by build).
TOOL_KEYS = ("totaltoolusecount", "tooluses", "toolusecount", "numtooluses")
TOKEN_KEYS = ("totaltokens", "subagenttokens", "totaltokensused")


def _walk(obj, found, depth=0):
    if depth > 8:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower().replace("_", "")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if key in TOOL_KEYS:
                    found.setdefault("tools", int(v))
                elif key in TOKEN_KEYS:
                    found.setdefault("tokens", int(v))
            else:
                _walk(v, found, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, found, depth + 1)


def metered(tool_response):
    """{'tools': n, 'tokens': n} - whichever the result carries; {} if none."""
    found = {}
    _walk(tool_response, found)
    return found


def report_text(tool_response, depth=0):
    """Every string in the result, joined - the employee's report."""
    if isinstance(tool_response, str):
        return tool_response
    if depth > 8:
        return ""
    parts = []
    if isinstance(tool_response, dict):
        parts = [report_text(v, depth + 1) for v in tool_response.values()]
    elif isinstance(tool_response, list):
        parts = [report_text(v, depth + 1) for v in tool_response]
    return "\n".join(p for p in parts if p)


def tools_line_total(report):
    """The sum of the x<count> entries on the report's TOOLS line; None if
    there is no parseable TOOLS line."""
    m = re.search(r"^\s*TOOLS:(.*)$", report, re.M)
    if not m:
        return None
    counts = re.findall(r"x\s*(\d+)", m.group(1))
    return sum(int(c) for c in counts) if counts else None


def audit(report, meter, readonly):
    """The warning strings for one delegation result."""
    warns = []
    mt = meter.get("tools")
    if mt == 0:
        warns.append("RULE 9 FABRICATION TELL: the harness metered 0 tool calls - "
                     "a read/run task reporting results with 0 tool uses NEVER did "
                     "the work; reject the report, ledger it FAILED, re-brief")
    if readonly:
        return warns
    missing = [ln for ln in TEMPLATE_LINES if ln not in report]
    if missing:
        warns.append("report is missing %s (rule 3/14: reject or re-brief)"
                     % ", ".join(missing))
    claimed = tools_line_total(report)
    if claimed is not None and mt not in (None, 0):
        hi, lo = max(claimed, mt), min(claimed, mt)
        if lo > 0 and hi / lo > 3 and hi - lo > 5:
            warns.append("TOOLS line claims %d calls but the harness metered %d - "
                         "a big mismatch is a truthfulness signal (rule 3)" % (claimed, mt))
    return warns


def pending_line(meter, task, now=None):
    """(id, line) for the pending ledger."""
    ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(now))
    did = "D" + hashlib.sha1(("%s|%s|%s" % (ts, task, os.getpid())).encode("utf-8")).hexdigest()[:6]
    task = re.sub(r"\s+", " ", task or "").strip()[:70]
    line = "%s | %s | %s | PENDING | metered tools=%s tokens=%s | %s" % (
        ts, _ws(), did, meter.get("tools", "?"), meter.get("tokens", "?"), task)
    return did, line


def _ws():
    try:
        from workstation_survey import ws_name
        return ws_name()
    except Exception:  # noqa: BLE001 - a hook never crashes the turn
        return "?"


def main():
    data = read_input()
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    readonly = (ti.get("subagent_type") or "").strip().lower() in READONLY_TYPES
    report = report_text(data.get("tool_response"))
    meter = metered(data.get("tool_response"))
    warns = audit(report, meter, readonly)
    msg = []
    if not readonly:
        did, line = pending_line(meter, ti.get("description") or ti.get("prompt", ""))
        try:
            os.makedirs(os.path.dirname(PENDING), exist_ok=True)
            with open(PENDING, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            msg.append("Pending %s appended - verify cheap (test -> diff -> smell), "
                       "append the SUBAGENTS.md ledger line + resolve the intent claim, "
                       "then append `RESOLVED | %s | OK/CORRECTED - <words>` to "
                       "docs/history/delegation_pending.txt (a new line, never an edit)."
                       % (did, did))
        except OSError:
            pass
    if warns:
        msg.insert(0, "; ".join(warns) + ".")
    if msg:
        context("PostToolUse", "[HOOK delegation_auditor] " + " ".join(msg))
    sys.exit(0)


def _selftest():
    """Pure checks on metered/audit/pending_line; never touches the ledger."""
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    resp = {"content": [{"type": "text", "text": "STAMP: model=sonnet\nTOOLS: Read x4, Edit x2\n"
                                                 "WORKFLOW: n/a\nINTENT: did the thing"}],
            "meta": {"totalToolUseCount": 6, "totalTokens": 74000}}
    ok("metered figures are found under varied key shapes",
       metered(resp) == {"tools": 6, "tokens": 74000})
    ok("the report text is recovered from nested content",
       "STAMP:" in report_text(resp))
    ok("a clean work report warns nothing", audit(report_text(resp), metered(resp), False) == [])
    w = audit("looks done!", {"tools": 0}, False)
    ok("0 metered calls is the rule 9 tell", any("FABRICATION" in x for x in w))
    ok("a template-free report is named", any("STAMP:" in x for x in w))
    w = audit(report_text(resp), {"tools": 0}, True)
    ok("a read-only agent still gets the fabrication glance, nothing else",
       len(w) == 1 and "FABRICATION" in w[0])
    w = audit("STAMP: x\nTOOLS: Read x40\nWORKFLOW: n/a\nINTENT: y", {"tools": 6}, False)
    ok("a 40-claimed vs 6-metered TOOLS line is a mismatch", any("mismatch" in x for x in w))
    w = audit("STAMP: x\nTOOLS: Read x7\nWORKFLOW: n/a\nINTENT: y", {"tools": 6}, False)
    ok("7 claimed vs 6 metered is no mismatch", not any("mismatch" in x for x in w))
    ok("the TOOLS line total parses", tools_line_total("TOOLS: Read x4, Edit x2") == 6)
    did, line = pending_line({"tools": 6, "tokens": 74000}, "  wire   the thing  ")
    ok("the pending line carries id, PENDING, the meter and the task",
       did in line and "PENDING" in line and "tools=6" in line and "wire the thing" in line)
    print("delegation_auditor selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

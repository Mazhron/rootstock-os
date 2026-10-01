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

THE STOP-TIME CROSS-CHECK (2026-10-01): the same script is wired on
SubagentStop. A background employee's Agent result is only the launch
notice, so the PostToolUse branch cannot meter it; at the employee's own
stop the hook counts the tool_use blocks in its transcript (the meter the
harness also reports), sums its tokens, reads the hand-back report, and
holds the employee ONCE - "your TOOLS line says 18, the transcript holds
27; restate it" or "your report lacks STAMP / TOOLS" - then appends a
METER line to the pending ledger with the true figures and the verdict
(OK, RULE 3 MISS, MALFORMED, FABRICATION TELL). The miss line is a
self-count under selfcount_floor (0.7, owner-tuned in
.claude/fanout_limits.json) of the meter by three calls or more.

PURPOSE: PostToolUse hook that reads the harness-metered tool and token
  figures from an Agent/Task result, warns on rule 9's fabrication tell,
  a TOOLS-line mismatch or a malformed report, and appends one PENDING
  line per work delegation to docs/history/delegation_pending.txt for
  verify_advisor to hold open until a RESOLVED line follows; on
  SubagentStop it meters the employee's own transcript, holds the
  employee once over a malformed report or a self-count miss, and
  appends the METER line with the true figures.
INTENT: the CEO 2026-09-26: "Can we make these processes more fool proof
  in any way through hooks" - born of the Reddit case he relayed the same
  day: a manager that said its employees did their job when they had not.

Search keys: delegation auditor, fabrication check, rule 9, metered
tokens, tool_uses, pending ledger, RESOLVED line, TOOLS line mismatch,
SubagentStop, METER line, self-count miss, selfcount_floor, held once.
See also: SUBAGENTS.md (rules 3, 5, 9); tools/hooks/verify_advisor.py
(the stop end); tools/hooks/brief_guard.py (the dispatch end);
docs/history/delegation_pending.txt (the pending ledger).
"""
import hashlib
import os
import re
import sys
import time

from _hooklib import ROOT, TOOLS, context, emit, read_input

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
    """The sum of the x<count> entries on the report's TOOLS line (the LAST
    one when the text holds several: a restated line wins); None if there
    is no parseable TOOLS line."""
    lines = re.findall(r"^\s*TOOLS:(.*)$", report or "", re.M)
    if not lines:
        return None
    counts = re.findall(r"x\s*(\d+)", lines[-1])
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
        elif selfcount_miss(claimed, mt):
            warns.append("TOOLS line claims %d calls, the meter says %d - a self-count "
                         "under %d%% of the meter is a RULE 3 MISS; ledger the true "
                         "figure and the miss" % (claimed, mt, int(SELFCOUNT_FLOOR * 100)))
    return warns


# ------------------------------------------------- the employee's stop --
# THE STOP-TIME CROSS-CHECK (2026-10-01, the rule-3 tightening). The
# PostToolUse branch above sees the Agent call's RESULT; with a background
# employee that result is the launch notice ("Async agent launched"), so
# 24 of the first 25 pending lines carried tools=? tokens=? and rule 3 had
# nothing to cross-check. The SubagentStop event fires when the employee
# itself stops, foreground or background, with its own transcript path:
# every tool_use block in that transcript IS the meter (nine of nine
# matched the harness's figure exactly on the calibration day), the
# usage dicts give the tokens, and the report is the hand-back text.
SELFCOUNT_FLOOR = 0.7       # a TOOLS line under this share of the meter is a miss
SELFCOUNT_MIN_GAP = 3       # ...once the gap is at least this many calls
LIMITS_FILE = os.path.join(ROOT, ".claude", "fanout_limits.json")
HANDBACK_TOOLS = ("subagenthandback", "handback")


def _load_floor():
    """selfcount_floor from the owner's limits file (0.5..1.0), else the default."""
    try:
        import json
        with open(LIMITS_FILE, encoding="utf-8") as fh:
            v = (json.load(fh) or {}).get("selfcount_floor")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0.5 <= v <= 1.0:
            return float(v)
    except Exception:  # noqa: BLE001 - a hook never crashes the turn
        pass
    return SELFCOUNT_FLOOR


def selfcount_miss(claimed, metered_tools, floor=None):
    """True when the employee's own count is under `floor` of the meter by
    at least SELFCOUNT_MIN_GAP calls. Over-claims are the 3x rule above."""
    floor = SELFCOUNT_FLOOR if floor is None else floor
    if claimed is None or not metered_tools:
        return False
    return (metered_tools - claimed) >= SELFCOUNT_MIN_GAP and claimed < floor * metered_tools


def read_transcript(path):
    """(tool_uses, tokens, stamp_task, handback, last_text) from an employee
    transcript: tool_use blocks counted, output + cache-write tokens summed
    once per message id, the brief's `task=T-...` stamp from the first user
    turn, the last hand-back call's text ('' before it lands) and the last
    plain text block."""
    import json
    tools = tokens = 0
    seen = set()
    first_user = ""
    last_text = handback = ""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                msg = d.get("message") or {}
                content = msg.get("content")
                kind = d.get("type")
                if kind == "user" and not first_user:
                    if isinstance(content, str):
                        first_user = content
                    elif isinstance(content, list):
                        first_user = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                if kind != "assistant" or not isinstance(content, list):
                    continue
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use":
                        tools += 1
                        if str(b.get("name", "")).lower() in HANDBACK_TOOLS:
                            handback = report_text(b.get("input"))
                    elif b.get("type") == "text" and (b.get("text") or "").strip():
                        last_text = b["text"]
                mid = msg.get("id")
                if mid and mid not in seen:
                    seen.add(mid)
                    u = msg.get("usage") or {}
                    tokens += int(u.get("output_tokens", 0) or 0) + int(u.get("cache_creation_input_tokens", 0) or 0)
    except OSError:
        return None
    m = re.search(r"task=(T-[\w-]+)", first_user or "")
    return tools, tokens, (m.group(1) if m else ""), handback, last_text


def employee_transcript(data, exists=os.path.exists):
    """The employee's own transcript. The docs say transcript_path is the
    subagent's; this build hands the MANAGER's there (the first live run
    metered 116 calls and 428k tokens - the whole session) and the
    employee's under agent_transcript_path, which is tried first. Failing
    that field, the employee's file is
    <session dir>/<session_id>/subagents/agent-<agent_id>.jsonl, so that
    is tried after it; transcript_path is trusted only when its name
    carries the agent id. None when nothing on disk matches."""
    agent_id = str(data.get("agent_id") or "")
    tp = str(data.get("transcript_path") or "")
    sid = str(data.get("session_id") or "")
    cands = []
    atp = str(data.get("agent_transcript_path") or "")
    if atp:
        cands.append(atp)
    if tp and agent_id and os.path.basename(tp).startswith("agent-" + agent_id):
        cands.append(tp)
    if tp and agent_id:
        base = os.path.dirname(tp)
        if sid:
            cands.append(os.path.join(base, sid, "subagents", "agent-%s.jsonl" % agent_id))
        # the session file is <base>/<sid>.jsonl, so its folder is beside it
        stem = os.path.splitext(os.path.basename(tp))[0]
        cands.append(os.path.join(base, stem, "subagents", "agent-%s.jsonl" % agent_id))
    for c in cands:
        if exists(c):
            return c
    return None


def asked_before(agent_id, path=None):
    """True if this employee was already held once (an ASKED line at the tail)."""
    path = path or PENDING
    try:
        with open(path, encoding="utf-8") as fh:
            return any(("| ASKED | %s |" % agent_id) in ln for ln in fh)
    except OSError:
        return False


def stop_verdict(tools, claimed, report, floor=None):
    """(verdict, hold_reason): verdict for the METER line; hold_reason is
    the text that holds the employee once, or '' to let it stop."""
    missing = [ln for ln in TEMPLATE_LINES if ln not in (report or "")]
    if tools == 0 and report:
        return "FABRICATION TELL (0 tool calls)", ""
    if missing:
        return ("MALFORMED (missing %s)" % ", ".join(missing),
                "Your report is missing %s. End it with the four template lines: "
                "STAMP (model, effort, est_tokens, task, confidence), TOOLS (every tool "
                "you called with its count - the harness metered %d calls), WORKFLOW "
                "(matched <entry> | GAP: ... | n/a) and INTENT (one line, what you "
                "understood the task to be). Then stop." % (", ".join(missing), tools))
    if selfcount_miss(claimed, tools, floor):
        return ("RULE 3 MISS (claimed %d of %d)" % (claimed, tools),
                "Your TOOLS line claims %d calls; the transcript holds %d tool calls. "
                "Restate the TOOLS line with the true count per tool (count every call, "
                "including the ones that errored or were refused), keep the rest of the "
                "report as it is, and stop." % (claimed, tools))
    return "OK (claimed %s of %d)" % (claimed if claimed is not None else "?", tools), ""


def main_subagent_stop(data):
    """The SubagentStop branch: meter the transcript, hold the employee once
    for a malformed report or a self-count miss, then append the METER line
    (append-only, a new line, never an edit) for the manager's ledger."""
    agent_type = (data.get("agent_type") or "").strip().lower()
    if agent_type in READONLY_TYPES:
        sys.exit(0)
    agent_id = str(data.get("agent_id") or "?")
    path = employee_transcript(data)
    got = read_transcript(path) if path else None
    if got is None:
        sys.exit(0)
    tools, tokens, task, handback, last_text = got
    ts = time.strftime("%Y-%m-%d %H:%M")
    label = task or agent_id
    # THE UNION REPORT: the order of the hand-back and the stop event varies
    # (foreground: hand-back first; background: the stop first, then the
    # hand-back), and an employee puts its template lines in one or the
    # other. Judge everything it said last: the hand-back text, the last
    # text block and the harness's last_assistant_message; a restated TOOLS
    # line (the most recent) wins. A hold before the hand-back costs one
    # round trip and the hand-back stop answers it.
    report = "\n".join(x for x in (handback, last_text, data.get("last_assistant_message") or "") if x)
    if not report.strip():
        try:
            with open(PENDING, "a", encoding="utf-8") as fh:
                fh.write("%s | %s | METER | %s | tools=%d tokens=~%dk | claimed=? | NO REPORT ON DISK YET\n"
                         % (ts, _ws(), label, tools, tokens // 1000))
        except OSError:
            pass
        sys.exit(0)
    claimed = tools_line_total(report)
    verdict, hold = stop_verdict(tools, claimed, report, _load_floor())
    if hold and not data.get("stop_hook_active") and not asked_before(agent_id):
        try:
            with open(PENDING, "a", encoding="utf-8") as fh:
                fh.write("%s | %s | ASKED | %s | %s | %s\n" % (ts, _ws(), agent_id, label, verdict))
        except OSError:
            pass
        emit({"decision": "block", "reason": "[HOOK delegation_auditor] " + hold})
        sys.exit(0)
    try:
        with open(PENDING, "a", encoding="utf-8") as fh:
            fh.write("%s | %s | METER | %s | tools=%d tokens=~%dk | claimed=%s | %s%s\n" % (
                ts, _ws(), label, tools, tokens // 1000,
                claimed if claimed is not None else "?", verdict,
                (" | held once" if asked_before(agent_id) else "")
                + ("" if handback else " | pre-hand-back")))
    except OSError:
        pass
    sys.exit(0)


def launched_async(report):
    """True when the Agent result is the background launch notice, not a report."""
    # The whole text, not its head: the result can echo the brief first,
    # whose template lines also satisfy the shape check (seen 2026-10-01).
    low = (report or "").lower()
    return "agent launched successfully" in low or "working in the background" in low


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
    if data.get("hook_event_name") == "SubagentStop":
        main_subagent_stop(data)
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    readonly = (ti.get("subagent_type") or "").strip().lower() in READONLY_TYPES
    report = report_text(data.get("tool_response"))
    meter = metered(data.get("tool_response"))
    background = launched_async(report)
    warns = [] if background else audit(report, meter, readonly)
    msg = []
    if not readonly:
        did, line = pending_line(meter, ti.get("description") or ti.get("prompt", ""))
        try:
            os.makedirs(os.path.dirname(PENDING), exist_ok=True)
            with open(PENDING, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            msg.append("Pending %s appended%s - verify cheap (test -> diff -> smell), "
                       "append the SUBAGENTS.md ledger line + resolve the intent claim, "
                       "then append `RESOLVED | %s | OK/CORRECTED - <words>` to "
                       "docs/history/delegation_pending.txt (a new line, never an edit)."
                       % (did, " (background employee: the METER line with the true "
                               "tool and token figures lands at its stop)" if background else "",
                          did))
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
    ok("a restated TOOLS line wins", tools_line_total("TOOLS: Read x4\nmore\nTOOLS: Read x9, Grep x1") == 10)
    did, line = pending_line({"tools": 6, "tokens": 74000}, "  wire   the thing  ")
    ok("the pending line carries id, PENDING, the meter and the task",
       did in line and "PENDING" in line and "tools=6" in line and "wire the thing" in line)

    # the stop-time cross-check (2026-10-01)
    ok("a launch notice is recognised", launched_async("Async agent launched successfully. agentId: x"))
    ok("a report is not a launch notice", not launched_async(report_text(resp)))
    ok("18 of 27 is a self-count miss", selfcount_miss(18, 27))
    ok("20 of 21 is not", not selfcount_miss(20, 21))
    ok("5 of 7 is not (gap under the minimum)", not selfcount_miss(5, 7))
    ok("a floor of 0.9 catches 20 of 24", selfcount_miss(20, 24, 0.9))
    w = audit("STAMP: x\nTOOLS: Read x18\nWORKFLOW: n/a\nINTENT: y", {"tools": 27}, False)
    ok("the PostToolUse branch names the miss too", any("RULE 3 MISS" in x for x in w))
    good = "done.\nSTAMP: model=sonnet\nTOOLS: Read x9, Grep x1\nWORKFLOW: n/a\nINTENT: z"
    ok("a clean stop is OK", stop_verdict(10, 10, good) == ("OK (claimed 10 of 10)", ""))
    v, hold = stop_verdict(27, 18, good.replace("x9", "x17"))
    ok("a self-count miss holds the employee with the true count",
       v.startswith("RULE 3 MISS") and "27 tool calls" in hold)
    v, hold = stop_verdict(5, None, "all done, looks good")
    ok("a template-free report holds the employee", v.startswith("MALFORMED") and "STAMP" in hold)
    v, hold = stop_verdict(0, None, "I checked everything, all fine")
    ok("0 tool calls with a report is the fabrication tell, not held", "FABRICATION" in v and hold == "")
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tp = os.path.join(td, "agent-x.jsonl")
        rows = [{"type": "user", "message": {"content": "STAMP: task=T-1001-X-1 date=2026-10-01"}},
                {"type": "assistant", "message": {"id": "m1", "usage": {"output_tokens": 50, "cache_creation_input_tokens": 1000},
                 "content": [{"type": "tool_use", "name": "Read", "input": {}}, {"type": "tool_use", "name": "Grep", "input": {}}]}},
                {"type": "assistant", "message": {"id": "m1", "usage": {"output_tokens": 50, "cache_creation_input_tokens": 1000},
                 "content": [{"type": "text", "text": "partial"}]}},
                {"type": "assistant", "message": {"id": "m2", "usage": {"output_tokens": 200, "cache_creation_input_tokens": 0},
                 "content": [{"type": "tool_use", "name": "SubagentHandback", "input": {"message": good}}]}}]
        with open(tp, "w", encoding="utf-8") as fh:
            fh.write("\n".join(_json.dumps(r) for r in rows) + "\n")
        tools, tokens, task, rep, _last = read_transcript(tp)
        ok("the transcript meter counts every tool_use block, the hand-back included",
           tools == 3)
        ok("tokens sum once per message id", tokens == 1250)
        ok("the brief's stamp task id is found", task == "T-1001-X-1")
        ok("the report is the hand-back text", "TOOLS: Read x9" in rep)
        pend = os.path.join(td, "pending.txt")
        with open(pend, "w", encoding="utf-8") as fh:
            fh.write("2026-10-01 10:00 | WS1 | ASKED | agent_abc | T-1 | RULE 3 MISS\n")
        ok("an ASKED line at the tail means held before", asked_before("agent_abc", pend))
        ok("an unknown agent was not held", not asked_before("agent_zzz", pend))
    mgr = os.path.join("P", "sess1.jsonl")
    emp = os.path.join("P", "sess1", "subagents", "agent-a1.jsonl")
    ev = {"transcript_path": mgr, "session_id": "sess1", "agent_id": "a1"}
    ok("the employee file is found beside the manager's transcript",
       employee_transcript(ev, exists=lambda p: p == emp) == emp)
    ok("the manager's transcript is never metered as the employee's",
       employee_transcript(ev, exists=lambda p: p == mgr) is None)
    ok("agent_transcript_path wins when the build provides it",
       employee_transcript({"transcript_path": mgr, "agent_transcript_path": emp, "agent_id": "a1"},
                           exists=lambda p: p == emp) == emp)
    ok("a transcript_path that names the agent is trusted",
       employee_transcript({"transcript_path": emp, "agent_id": "a1"}, exists=lambda p: p == emp) == emp)
    v, hold = stop_verdict(2, 1, good.replace("Read x9, Grep x1", "Bash x1"))
    ok("the uncounted hand-back call alone is never a miss", v.startswith("OK") and hold == "")
    print("delegation_auditor selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

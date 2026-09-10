"""THE USAGE SHEET (Mazhron's ask 2026-09-03: one aggregate sheet - totals
per day, week, and month for every model and every tool, CSV for humans +
TXT twin, scripted).

WHERE THE NUMBERS COME FROM: the Claude Code harness writes a full JSONL
transcript of every session under ~/.claude/projects/<project>/*.jsonl.
Every assistant message in there carries the REAL API meter (model, input /
output / thinking tokens, cache reads and writes) and every tool call is
named - including sub-agent (employee) traffic, which is flagged and metered
under its own model. So unlike SUBAGENTS.md's self-estimates, everything in
this sheet is harness-metered truth for THIS machine. (Each workstation only
has its own transcripts; the sheet keeps WS1 and WS2 rows side by side and a
run only rewrites its own workstation's rows.)

WHAT A "TOOL COST" MEANS: a tool call itself is free; its cost is the result
text injected into context (estimated at chars/4), which is then re-read by
every later turn via cache. calls + context_est_tok is therefore the honest
per-tool figure; there is no per-tool dollar meter.

COSTS ARE ESTIMATES: token counts are real; the est_cost_usd column prices
them from the PRICING table below (blank when a model's price is not filled
in). The billing dashboard remains the only truth for dollars.

Outputs (REGENERATED whole each run - the transcripts are the ledger, this
is the derived sheet, so no append-only file here):
  docs/history/usage_metrics.txt  - OPEN THIS ONE: totals by day/week/month,
                                    then the BREAKDOWNS (Mazhron's ask
                                    2026-09-10): averages per request, the
                                    context window by month, averages per
                                    tool call, employee runs
  docs/history/usage_metrics.xlsx - THE SPREADSHEET (Mazhron's ask
                                    2026-09-10): header row frozen, every
                                    token column a Number with thousands
                                    separators, per-period TOTAL rows bold
                                    with a thick bottom border, total_tok +
                                    avg_tok per model/tool in columns O/P;
                                    sheets usage / per_request / employees
  docs/history/usage_metrics.csv  - the same rows in long format (+ avg_req
                                    rows per month/all)
  docs/history/usage_employees.csv - one row per sub-agent run (day, model,
                                    minutes, tokens, tool calls, est$, the
                                    brief's first line)
  docs/history/usage_cache.json   - incremental parse cache (transcripts are
                                    append-only; reruns only read new bytes)

WHAT "THE CONTEXT WINDOW" MEANS HERE: the harness never records what sits
in the window, but every request's prompt size is input + cache_read +
cache_create - that IS the box the model read that turn. The sheet reports
its average and its biggest per model per month; a growing average is a
session that should have checkpointed.

Usage:  python tools/usage_report.py            # in run_all's metrics group
Needs:  openpyxl (pip) for the .xlsx; without it the CSV/TXT still write
        and the run says so (WORKSTATION.md carries the row).

Search keys: usage, token costs, tool costs, metrics sheet, daily totals,
weekly totals, monthly totals, harness meter, transcript mining, average
tokens per request, per tool call, per employee, context window size.
See also: tools/metrics_report.py (task outcomes from SUBAGENTS.md);
REPORTING_METHOD.md; TOKEN_IDEAS.md.
"""
import csv
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "docs", "history")
CSV_OUT = os.path.join(HIST, "usage_metrics.csv")
TXT_OUT = os.path.join(HIST, "usage_metrics.txt")
EMP_OUT = os.path.join(HIST, "usage_employees.csv")
XLSX_OUT = os.path.join(HIST, "usage_metrics.xlsx")
CACHE = os.path.join(HIST, "usage_cache.json")
CACHE_VERSION = 2  # v2: per-file timestamps + label + biggest prompt

# $ per MILLION tokens: model -> (input, output). None = unknown; fill from
# the billing page / claude.com/pricing and the cost column comes alive.
# Cache pricing law: read = 0.1x input (0.025x on Fable 5.1); 5-min write =
# 1.25x; 1-hour write = 2x.
# Rates confirmed 2026-09-04 against Anthropic's published first-party API
# pricing (haiku 4.5 / sonnet 5 / opus 5 / fable 5). The old opus row was
# the Opus 4.1-era 15/75 - Opus 5-tier is 5/25.
# Third value = the CACHE READ multiplier on the input price: 0.1x on most
# models, 0.025x on Claude Fable 5.1 ($0.25/MTok - every "fable" message in
# these transcripts is claude-fable-5-1; corrected 2026-09-10 after Mazhron
# asked whether cache reads count: they do, at this discount).
PRICING = {
    "haiku": (1.0, 5.0, 0.1),
    "sonnet": (3.0, 15.0, 0.1),
    "opus": (5.0, 25.0, 0.1),
    "fable": (10.0, 50.0, 0.025),
}

FIELDS = ["period_type", "period", "ws", "scope", "name", "role", "count",
          "input_tok", "output_tok", "think_tok", "cache_read_tok",
          "cache_create_tok", "context_est_tok", "est_cost_usd",
          "total_tok", "avg_tok"]
# total_tok: a model row = every token metered (in + out + cache_rd +
# cache_wr); a tool row = the context its results injected; a TOTAL row =
# the period's model tokens. avg_tok = total_tok per request / per call.
EMP_FIELDS = ["ws", "day", "started", "minutes", "parent_session", "model",
              "msgs", "input_tok", "output_tok", "think_tok",
              "cache_read_tok", "cache_create_tok", "tool_calls",
              "ctx_est_tok", "avg_box_tok", "est_cost_usd", "brief"]


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def transcript_dirs():
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(base):
        return []
    return [os.path.join(base, d) for d in os.listdir(base)
            if "everwood" in d.lower()
            and os.path.isdir(os.path.join(base, d))]


def short_model(model):
    if model and model.startswith("claude-"):
        return model.split("-")[1]
    return model or "?"


def local_day(ts):
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def blank_model():
    return {"count": 0, "in": 0, "out": 0, "think": 0, "read": 0,
            "c5": 0, "c1": 0, "maxp": 0}


def box(m):
    """The prompt size the model read: fresh input + cache read + cache
    written. Summed over a bucket; divide by count for the average box."""
    return m["in"] + m["read"] + m["c5"] + m["c1"]


def first_text(msg, limit=90):
    """The first line of a user message (an employee's brief), for labels."""
    content = msg.get("content")
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for blk in content:
            if isinstance(blk, dict) and blk.get("type") == "text":
                text = blk.get("text") or ""
                break
    text = " ".join(text.split())
    return text[:limit] if text else ""


def parse_file(path, state, force_agent=False):
    """Stream one transcript, resuming from the cached byte offset.
    state = {"size", "offset", "last_id", "pending", "days"} (mutated).
    force_agent: employee transcripts (subagents/agent-*.jsonl) meter under
    role "agent" even where records lack the isSidechain flag."""
    size = os.path.getsize(path)
    if size == state.get("size") and state.get("days") is not None:
        return  # unchanged since last run
    if size < state.get("size", 0) or state.get("days") is None:
        state.update({"offset": 0, "last_id": "", "pending": {}, "days": {},
                      "t_first": "", "t_last": "", "label": ""})
    days, pending = state["days"], state["pending"]
    with open(path, "rb") as fh:
        fh.seek(state.get("offset", 0))
        for raw in fh:
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except (ValueError, UnicodeDecodeError):
                continue
            rtype = rec.get("type")
            ts = rec.get("timestamp") or ""
            if ts and rtype in ("assistant", "user"):
                if not state.get("t_first") or ts < state["t_first"]:
                    state["t_first"] = ts
                if ts > state.get("t_last", ""):
                    state["t_last"] = ts
            if rtype == "user" and not state.get("label"):
                state["label"] = first_text(rec.get("message") or {})
            if rtype == "assistant":
                msg = rec.get("message") or {}
                day = local_day(rec.get("timestamp", ""))
                if not day:
                    continue
                d = days.setdefault(day, {"models": {}, "tools": {}})
                for blk in msg.get("content") or []:
                    if isinstance(blk, dict) and blk.get("type") == "tool_use":
                        tool = blk.get("name") or "?"
                        pending[blk.get("id") or ""] = tool
                        t = d["tools"].setdefault(tool, {"calls": 0, "ctx": 0})
                        t["calls"] += 1
                # A message split across records repeats its meter; count once.
                mid = msg.get("id") or rec.get("requestId") or ""
                usage = msg.get("usage")
                if not usage or mid == state.get("last_id"):
                    continue
                state["last_id"] = mid
                model = short_model(msg.get("model"))
                if model in ("<synthetic>", "?"):
                    continue
                role = "agent" if (force_agent or rec.get("isSidechain")) \
                    else "main"
                m = d["models"].setdefault(model + "|" + role, blank_model())
                m["count"] += 1
                m["in"] += usage.get("input_tokens", 0) or 0
                m["out"] += usage.get("output_tokens", 0) or 0
                m["think"] += (usage.get("output_tokens_details") or {}
                               ).get("thinking_tokens", 0) or 0
                m["read"] += usage.get("cache_read_input_tokens", 0) or 0
                cc = usage.get("cache_creation") or {}
                c5 = cc.get("ephemeral_5m_input_tokens")
                c1 = cc.get("ephemeral_1h_input_tokens")
                if c5 is None and c1 is None:
                    c5 = usage.get("cache_creation_input_tokens", 0) or 0
                m["c5"] += c5 or 0
                m["c1"] += c1 or 0
                m["maxp"] = max(m["maxp"], (usage.get("input_tokens", 0) or 0)
                                + (usage.get("cache_read_input_tokens", 0) or 0)
                                + (c5 or 0) + (c1 or 0))
            elif rtype == "user":
                # Tool results: size them - that is what enters context.
                msg = rec.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                day = local_day(rec.get("timestamp", ""))
                if not day:
                    continue
                for blk in content:
                    if not (isinstance(blk, dict)
                            and blk.get("type") == "tool_result"):
                        continue
                    tool = pending.pop(blk.get("tool_use_id") or "", None)
                    if not tool:
                        continue
                    payload = rec.get("toolUseResult")
                    if payload is None:
                        payload = blk.get("content")
                    try:
                        est = len(json.dumps(payload, default=str)) // 4
                    except (TypeError, ValueError):
                        est = len(str(payload)) // 4
                    d = days.setdefault(day, {"models": {}, "tools": {}})
                    t = d["tools"].setdefault(tool, {"calls": 0, "ctx": 0})
                    t["ctx"] += est
        state["offset"] = fh.tell()
    state["size"] = size
    if len(pending) > 400:  # orphaned tool_use ids (interrupted calls)
        for k in list(pending)[:-200]:
            del pending[k]


def merge_bucket(tgt, d):
    for key, m in d["models"].items():
        t = tgt["models"].setdefault(key, blank_model())
        for k in m:
            if k == "maxp":
                t[k] = max(t[k], m[k])
            else:
                t[k] += m[k]
    for tool, v in d["tools"].items():
        t = tgt["tools"].setdefault(tool, {"calls": 0, "ctx": 0})
        t["calls"] += v["calls"]
        t["ctx"] += v["ctx"]


def merge_days(all_days, days):
    for day, d in days.items():
        merge_bucket(all_days.setdefault(day, {"models": {}, "tools": {}}), d)


def cost_usd(model, m):
    p = PRICING.get(model)
    if not p:
        return None
    return (m["in"] * p[0] + m["out"] * p[1] + m["read"] * p[2] * p[0]
            + m["c5"] * 1.25 * p[0] + m["c1"] * 2.0 * p[0]) / 1e6


def period_keys(day):
    dt = datetime.date.fromisoformat(day)
    iso = dt.isocalendar()
    return [("day", day), ("week", "%d-W%02d" % (iso[0], iso[1])),
            ("month", day[:7]), ("all", "all")]


def build_rows(all_days, ws):
    """day rows -> aggregated CSV rows for every period granularity."""
    agg = {}   # (ptype, period) -> {"models": {}, "tools": {}}
    for day, d in all_days.items():
        for ptype, period in period_keys(day):
            merge_bucket(agg.setdefault(
                (ptype, period), {"models": {}, "tools": {}}), d)
    rows = []
    order = {"day": 0, "week": 1, "month": 2, "all": 3}
    for (ptype, period) in sorted(agg, key=lambda k: (order[k[0]], k[1])):
        d = agg[(ptype, period)]
        total = blank_model()
        total_cost, cost_known = 0.0, True
        for key in sorted(d["models"]):
            model, role = key.split("|")
            m = d["models"][key]
            c = cost_usd(model, m)
            if c is None:
                cost_known = False
            else:
                total_cost += c
            for k in total:
                total[k] += m[k]
            tot = m["in"] + m["out"] + m["read"] + m["c5"] + m["c1"]
            rows.append([ptype, period, ws, "model", model, role, m["count"],
                         m["in"], m["out"], m["think"], m["read"],
                         m["c5"] + m["c1"], "",
                         "%.2f" % c if c is not None else "",
                         tot, tot // (m["count"] or 1)])
            if ptype == "all":
                MAXP[(ws, model, role)] = m["maxp"]
            elif ptype == "month":
                MAXP_M[(ws, period, model, role)] = m["maxp"]
        if ptype in ("month", "all"):
            # per-request averages: count = msgs, the token columns are
            # per message, context_est_tok = the average box, est$ per msg
            for key in sorted(d["models"]):
                model, role = key.split("|")
                m = d["models"][key]
                n = m["count"] or 1
                c = cost_usd(model, m)
                rows.append([ptype, period, ws, "avg_req", model, role,
                             m["count"], m["in"] // n, m["out"] // n,
                             m["think"] // n, m["read"] // n,
                             (m["c5"] + m["c1"]) // n, box(m) // n,
                             "%.4f" % (c / n) if c is not None else "",
                             "", ""])
        tool_ctx = 0
        for tool in sorted(d["tools"], key=lambda t: -d["tools"][t]["ctx"]):
            v = d["tools"][tool]
            tool_ctx += v["ctx"]
            rows.append([ptype, period, ws, "tool", tool, "-", v["calls"],
                         "", "", "", "", "", v["ctx"], "",
                         v["ctx"], v["ctx"] // (v["calls"] or 1)])
        # THE TOTAL ROW sits LAST in its period (Mazhron 2026-09-10: "in
        # line under their final record"); the .xlsx bolds it and rules a
        # thick border under it.
        tot = total["in"] + total["out"] + total["read"] + total["c5"] + total["c1"]
        rows.append([ptype, period, ws, "total", "all", "all", total["count"],
                     total["in"], total["out"], total["think"], total["read"],
                     total["c5"] + total["c1"], tool_ctx,
                     "%.2f" % total_cost if cost_known else "",
                     tot, tot // (total["count"] or 1)])
    return rows


def keep_other_ws(ws, path=CSV_OUT, fields=FIELDS, ws_col=2):
    """Rows from the other workstation survive a rerun here untouched."""
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in list(csv.reader(fh))[1:]
                if len(r) == len(fields) and r[ws_col] != ws]


def local_clock(ts):
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%H:%M")
    except (ValueError, AttributeError):
        return ""


def minutes_between(a, b):
    try:
        ta = datetime.datetime.fromisoformat(a.replace("Z", "+00:00"))
        tb = datetime.datetime.fromisoformat(b.replace("Z", "+00:00"))
        return max(0.0, (tb - ta).total_seconds() / 60.0)
    except (ValueError, AttributeError):
        return 0.0


def employee_rows(cache, ws):
    """One row per sub-agent transcript (a file under <session>/subagents/
    IS one employee run). Sorted newest first."""
    rows = []
    for path, state in cache["files"].items():
        parts = path.replace("\\", "/").split("/")
        if "subagents" not in parts or not state.get("days"):
            continue
        parent = parts[parts.index("subagents") - 1]
        total = blank_model()
        models = {}
        calls = ctx = 0
        for d in state["days"].values():
            for key, m in d["models"].items():
                models[key.split("|")[0]] = models.get(key.split("|")[0], 0) + m["count"]
                for k in total:
                    total[k] = max(total[k], m[k]) if k == "maxp" else total[k] + m[k]
            for v in d["tools"].values():
                calls += v["calls"]
                ctx += v["ctx"]
        if not total["count"]:
            continue
        model = max(models, key=models.get)
        cost = cost_usd(model, total)
        day = local_day(state.get("t_first") or "") or sorted(state["days"])[0]
        started = local_clock(state.get("t_first") or "")
        rows.append([ws, day, started,
                     "%.1f" % minutes_between(state.get("t_first", ""), state.get("t_last", "")),
                     parent[:8], model, total["count"], total["in"], total["out"],
                     total["think"], total["read"], total["c5"] + total["c1"],
                     calls, ctx, box(total) // (total["count"] or 1),
                     "%.2f" % cost if cost is not None else "",
                     state.get("label") or ""])
    rows.sort(key=lambda r: (r[1], r[2]), reverse=True)
    return rows


def ktok(n):
    return "~%dk" % round(int(n) / 1000.0) if int(n) >= 1000 else str(n)


def write_txt(rows, emp_rows, ws):
    by = {}
    for r in rows:
        by.setdefault((r[0], r[1], r[2]), []).append(r)
    lines = [
        "THE USAGE SHEET - harness-metered token usage, aggregated",
        "regenerated %s by tools/usage_report.py (CSV twin: usage_metrics.csv)"
        % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "READING IT: input/output = fresh tokens each API call; think = the",
        "output share spent reasoning; cache_read = context re-read each turn",
        "(cheap, 0.1x); cache_create = new context written (1.25-2x input",
        "price). A tool's cost is the context its results inject (ctx_est,",
        "chars/4) times every later re-read - calls alone do not price it.",
        "est$ prices known models only (fill PRICING in the script); the",
        "billing dashboard is the only dollar truth.",
        "",
        "SECTIONS: totals (all-time / month / week / day), then THE",
        "BREAKDOWNS at the bottom - averages per request, the context window",
        "by month, averages per tool call, employee runs, averages per day.",
        ""]
    order = {"all": 0, "month": 1, "week": 2, "day": 3}
    titles = {"all": "ALL-TIME", "month": "BY MONTH", "week": "BY WEEK",
              "day": "BY DAY (newest last)"}
    last_ptype = None
    day_count = {}
    for (ptype, period, ws) in sorted(
            by, key=lambda k: (order[k[0]], k[1], k[2])):
        if ptype != last_ptype:
            lines += ["=" * 66, titles[ptype], "=" * 66]
            last_ptype = ptype
        lines.append("-- %s %s" % (period, ws))
        lines.append("   %-8s %-6s %6s %9s %9s %8s %10s %10s %8s" % (
            "model", "role", "msgs", "input", "output", "think",
            "cache_rd", "cache_wr", "est$"))
        for r in by[(ptype, period, ws)]:
            if r[3] == "model":
                lines.append("   %-8s %-6s %6s %9s %9s %8s %10s %10s %8s" % (
                    r[4], r[5], r[6], ktok(r[7]), ktok(r[8]), ktok(r[9]),
                    ktok(r[10]), ktok(r[11]), r[13] or "-"))
        for r in by[(ptype, period, ws)]:
            if r[3] == "total":
                lines.append("   %-8s %-6s %6s %9s %9s %8s %10s %10s %8s" % (
                    "TOTAL", "", r[6], ktok(r[7]), ktok(r[8]), ktok(r[9]),
                    ktok(r[10]), ktok(r[11]), r[13] or "-"))
                if ptype == "day":
                    day_count[ws] = day_count.get(ws, 0) + 1
        tools = [r for r in by[(ptype, period, ws)] if r[3] == "tool"]
        if tools and ptype in ("all", "month"):
            lines.append("   tools by context injected: " + ", ".join(
                "%s x%s %s" % (r[4], r[6], ktok(r[12])) for r in tools[:10]))
        elif tools:
            lines.append("   top tools: " + ", ".join(
                "%s x%s %s" % (r[4], r[6], ktok(r[12])) for r in tools[:5]))
        lines.append("")
    lines += breakdown_lines(by, emp_rows)
    lines += ["=" * 66, "AVERAGES (per active day)", "=" * 66]
    for (ptype, period, ws) in sorted(by):
        if ptype != "all":
            continue
        n = day_count.get(ws) or 1
        for r in by[(ptype, period, ws)]:
            if r[3] == "total":
                lines.append(
                    "%s: %d active days | avg/day: %s msgs, %s in, %s out,"
                    " %s cache_rd, %s cache_wr" % (
                        ws, n, int(r[6]) // n, ktok(int(r[7]) // n),
                        ktok(int(r[8]) // n), ktok(int(r[10]) // n),
                        ktok(int(r[11]) // n)))
    with open(TXT_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def breakdown_lines(by, emp_rows):
    """THE BREAKDOWNS (Mazhron's ask 2026-09-10): per request, the context
    window by month, per tool call, employee runs."""
    L = []
    H = "=" * 66
    # 1. per request
    L += [H, "AVERAGES PER REQUEST (all-time; one request = one API call)", H,
          "   box = the prompt the model read that turn (input + cache_rd + cache_wr)"]
    for (ptype, period, ws) in sorted(by):
        if ptype != "all":
            continue
        L.append("-- %s" % ws)
        L.append("   %-8s %-6s %6s %8s %8s %8s %9s %9s %9s %9s %8s" % (
            "model", "role", "msgs", "in/req", "out/req", "think", "cache_rd",
            "cache_wr", "avg_box", "max_box", "est$/req"))
        maxes = {r[4] + "|" + r[5]: r for r in by[(ptype, period, ws)] if r[3] == "model"}
        for r in by[(ptype, period, ws)]:
            if r[3] != "avg_req":
                continue
            L.append("   %-8s %-6s %6s %8s %8s %8s %9s %9s %9s %9s %8s" % (
                r[4], r[5], r[6], ktok(r[7]), ktok(r[8]), ktok(r[9]), ktok(r[10]),
                ktok(r[11]), ktok(r[12]), ktok(MAXP.get((ws, r[4], r[5]), 0)),
                r[13] or "-"))
    L.append("")
    # 2. the context window by month (main role: what the manager re-reads)
    L += [H, "THE CONTEXT WINDOW BY MONTH (avg box per request; a rising avg = sessions that should have checkpointed)", H]
    for (ptype, period, ws) in sorted(by):
        if ptype != "month":
            continue
        cells = []
        for r in by[(ptype, period, ws)]:
            if r[3] == "avg_req":
                cells.append("%s/%s avg %s max %s (%s req)" % (
                    r[4], r[5], ktok(r[12]), ktok(MAXP_M.get((ws, period, r[4], r[5]), 0)), r[6]))
        L.append("-- %s %s: %s" % (period, ws, "; ".join(cells) if cells else "-"))
    L.append("")
    # 3. per tool call
    L += [H, "AVERAGES PER TOOL CALL (all-time; ctx = what the result injected, chars/4)", H]
    for (ptype, period, ws) in sorted(by):
        if ptype != "all":
            continue
        tools = [r for r in by[(ptype, period, ws)] if r[3] == "tool"]
        total_ctx = sum(int(r[12] or 0) for r in tools) or 1
        L.append("-- %s" % ws)
        L.append("   %-22s %7s %10s %10s %6s" % ("tool", "calls", "ctx_total", "ctx/call", "share"))
        for r in sorted(tools, key=lambda r: -int(r[12] or 0)):
            calls = int(r[6] or 0) or 1
            L.append("   %-22s %7s %10s %10s %5.1f%%" % (
                r[4][:22], r[6], ktok(r[12]), ktok(int(r[12] or 0) // calls),
                100.0 * int(r[12] or 0) / total_ctx))
    L.append("")
    # 4. employee runs
    L += [H, "EMPLOYEE RUNS (one sub-agent transcript = one run; full list: usage_employees.csv)", H]
    by_ws = {}
    for r in emp_rows:
        by_ws.setdefault(r[0], []).append(r)
    for ws in sorted(by_ws):
        runs = by_ws[ws]
        n = len(runs)
        L.append("-- %s: %d runs" % (ws, n))
        by_model = {}
        for r in runs:
            by_model.setdefault(r[5], []).append(r)
        L.append("   %-8s %5s %7s %8s %8s %9s %9s %7s %8s %8s" % (
            "model", "runs", "avg_min", "avg_msgs", "avg_in", "avg_out", "avg_cache", "avg_tool", "avg_box", "avg_est$"))
        for model in sorted(by_model):
            rs = by_model[model]
            k = len(rs)
            costs = [float(r[15]) for r in rs if r[15]]
            L.append("   %-8s %5d %7.1f %8d %8s %9s %9s %7d %8s %8s" % (
                model, k, sum(float(r[3]) for r in rs) / k,
                sum(int(r[6]) for r in rs) // k, ktok(sum(int(r[7]) for r in rs) // k),
                ktok(sum(int(r[8]) for r in rs) // k), ktok(sum(int(r[10]) for r in rs) // k),
                sum(int(r[12]) for r in rs) // k, ktok(sum(int(r[14]) for r in rs) // k),
                "%.2f" % (sum(costs) / len(costs)) if costs else "-"))
        L.append("   costliest runs:")
        for r in sorted(runs, key=lambda r: -(float(r[15]) if r[15] else 0))[:10]:
            L.append("   %s %s %-7s %5s min %4s tools %7s box  $%-6s %s" % (
                r[1], r[2], r[5], r[3], r[12], ktok(r[14]), r[15] or "-", r[16][:60]))
    if not by_ws:
        L.append("   (no sub-agent transcripts found)")
    L.append("")
    return L


MAXP = {}     # (ws, model, role) -> biggest prompt all-time
MAXP_M = {}   # (ws, month, model, role) -> biggest prompt that month


XLSX_NUMBER = "#,##0"        # the Format Cells screenshot: Number, 1000 separator
XLSX_MONEY = "#,##0.00"
NUMERIC_COLS = {"count", "input_tok", "output_tok", "think_tok",
                "cache_read_tok", "cache_create_tok", "context_est_tok",
                "total_tok", "avg_tok", "msgs", "tool_calls", "ctx_est_tok",
                "avg_box_tok"}
MONEY_COLS = {"est_cost_usd"}


def _xlsx_sheet(wb, title, fields, rows, total_scope_col=None, block_key=None):
    """THE SPREADSHEET RULE (REPORTING_METHOD.md): header frozen, numbers
    formatted with separators, TOTAL rows bold + thick bottom border,
    one thick border after every period block."""
    from openpyxl.styles import Font, Border, Side, Alignment
    ws_ = wb.create_sheet(title)
    ws_.append(fields)
    bold = Font(bold=True)
    thick = Border(bottom=Side(style="thick"))
    for c in ws_[1]:
        c.font = bold
        c.alignment = Alignment(horizontal="center")
    ws_.freeze_panes = "A2"
    ws_.auto_filter.ref = "A1:%s1" % ws_.cell(row=1, column=len(fields)).column_letter
    fmt = {}
    for i, f in enumerate(fields, 1):
        if f in NUMERIC_COLS:
            fmt[i] = XLSX_NUMBER
        elif f in MONEY_COLS:
            fmt[i] = XLSX_MONEY
    for r in rows:
        vals = []
        for i, v in enumerate(r, 1):
            if i in fmt and v not in ("", None):
                try:
                    v = float(v) if i in fmt and fmt[i] == XLSX_MONEY else int(float(v))
                except (TypeError, ValueError):
                    pass
            vals.append(v)
        ws_.append(vals)
        row = ws_.max_row
        for i in fmt:
            ws_.cell(row=row, column=i).number_format = fmt[i]
        if total_scope_col is not None and r[total_scope_col] == "total":
            for c in ws_[row]:
                c.font = bold
                c.border = thick
    widths = {"period_type": 11, "period": 12, "ws": 5, "scope": 8, "name": 16,
              "role": 6, "brief": 60, "parent_session": 14, "started": 8}
    for i, f in enumerate(fields, 1):
        ws_.column_dimensions[ws_.cell(row=1, column=i).column_letter].width = widths.get(f, 13)
    return ws_


def write_xlsx(rows, emp_rows):
    """usage_metrics.xlsx: sheets usage (model + tool rows, TOTAL last per
    period), per_request (the avg_req rows), employees. Returns a note."""
    try:
        import openpyxl
    except ImportError:
        return "openpyxl missing - no .xlsx (python -m pip install openpyxl)"
    order = {"day": 0, "week": 1, "month": 2, "all": 3}
    scope_rank = {"model": 0, "tool": 1, "total": 2}
    main = sorted([r for r in rows if r[3] in scope_rank],
                  key=lambda r: (order.get(r[0], 9), r[1], r[2], scope_rank[r[3]]))
    per_req = sorted([r for r in rows if r[3] == "avg_req"],
                     key=lambda r: (order.get(r[0], 9), r[1], r[2], r[4], r[5]))
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    _xlsx_sheet(wb, "usage", FIELDS, main, total_scope_col=3)
    _xlsx_sheet(wb, "per_request", FIELDS, per_req)
    _xlsx_sheet(wb, "employees", EMP_FIELDS, emp_rows)
    try:
        wb.save(XLSX_OUT)
    except PermissionError:
        return ("%s NOT rewritten - it is open in Excel; close it and rerun "
                "(CSV/TXT are current)" % os.path.relpath(XLSX_OUT, ROOT))
    return os.path.relpath(XLSX_OUT, ROOT)


def main():
    ws = workstation()
    cache = {"version": CACHE_VERSION, "files": {}}
    if os.path.isfile(CACHE):
        try:
            loaded = json.load(open(CACHE, encoding="utf-8"))
            if loaded.get("version") == CACHE_VERSION:
                cache = loaded
        except ValueError:
            pass
    all_days = {}
    n_files = 0
    for tdir in transcript_dirs():
        for base, _dirs, names in os.walk(tdir):
            for name in sorted(names):
                if not name.endswith(".jsonl"):
                    continue
                path = os.path.join(base, name)
                state = cache["files"].setdefault(path, {})
                parse_file(path, state,
                           force_agent="subagents" in base.lower())
                merge_days(all_days, state["days"])
                n_files += 1
    if not all_days:
        print("No transcripts found under ~/.claude/projects - nothing to do.")
        return
    os.makedirs(HIST, exist_ok=True)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    rows = build_rows(all_days, ws) + keep_other_ws(ws)
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        w.writerows(rows)
    emp = employee_rows(cache, ws) + keep_other_ws(ws, EMP_OUT, EMP_FIELDS, 0)
    with open(EMP_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(EMP_FIELDS)
        w.writerows(emp)
    write_txt(rows, emp, ws)
    xlsx_note = write_xlsx(rows, emp)
    days = sorted(all_days)
    total = blank_model()
    for d in all_days.values():
        for m in d["models"].values():
            for k in total:
                total[k] += m[k]
    print("USAGE SHEET: %d transcripts, %d active days (%s .. %s) on %s" % (
        n_files, len(days), days[0], days[-1], ws))
    print("  metered: %s msgs | in %s out %s | cache_rd %s cache_wr %s" % (
        total["count"], ktok(total["in"]), ktok(total["out"]),
        ktok(total["read"]), ktok(total["c5"] + total["c1"])))
    print("  -> OPEN %s (the spreadsheet: usage / per_request / employees)" % xlsx_note)
    print("     %s (totals + the breakdowns, plain text)" % os.path.relpath(TXT_OUT, ROOT))
    print("     csv twins: %s, %s (%d employee runs)" % (
        os.path.relpath(CSV_OUT, ROOT), os.path.relpath(EMP_OUT, ROOT),
        len([r for r in emp if r[0] == ws])))


if __name__ == "__main__":
    main()

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
  docs/history/usage_metrics.csv  - long format, day/week/month/all rows
  docs/history/usage_metrics.txt  - the same numbers as human tables
  docs/history/usage_cache.json   - incremental parse cache (transcripts are
                                    append-only; reruns only read new bytes)

Usage:  python tools/usage_report.py            # in run_all's metrics group

Search keys: usage, token costs, tool costs, metrics sheet, daily totals,
weekly totals, monthly totals, harness meter, transcript mining.
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
CACHE = os.path.join(HIST, "usage_cache.json")
CACHE_VERSION = 1

# $ per MILLION tokens: model -> (input, output). None = unknown; fill from
# the billing page / claude.com/pricing and the cost column comes alive.
# Cache pricing law: read = 0.1x input; 5-min write = 1.25x; 1-hour write = 2x.
PRICING = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
    "fable": None,   # fill from the billing dashboard when published
}

FIELDS = ["period_type", "period", "ws", "scope", "name", "role", "count",
          "input_tok", "output_tok", "think_tok", "cache_read_tok",
          "cache_create_tok", "context_est_tok", "est_cost_usd"]


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
            "c5": 0, "c1": 0}


def parse_file(path, state, force_agent=False):
    """Stream one transcript, resuming from the cached byte offset.
    state = {"size", "offset", "last_id", "pending", "days"} (mutated).
    force_agent: employee transcripts (subagents/agent-*.jsonl) meter under
    role "agent" even where records lack the isSidechain flag."""
    size = os.path.getsize(path)
    if size == state.get("size") and state.get("days") is not None:
        return  # unchanged since last run
    if size < state.get("size", 0) or state.get("days") is None:
        state.update({"offset": 0, "last_id": "", "pending": {}, "days": {}})
    days, pending = state["days"], state["pending"]
    with open(path, "rb") as fh:
        fh.seek(state.get("offset", 0))
        for raw in fh:
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except (ValueError, UnicodeDecodeError):
                continue
            rtype = rec.get("type")
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
    return (m["in"] * p[0] + m["out"] * p[1] + m["read"] * 0.1 * p[0]
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
            rows.append([ptype, period, ws, "model", model, role, m["count"],
                         m["in"], m["out"], m["think"], m["read"],
                         m["c5"] + m["c1"], "",
                         "%.2f" % c if c is not None else ""])
        rows.append([ptype, period, ws, "total", "all", "all", total["count"],
                     total["in"], total["out"], total["think"], total["read"],
                     total["c5"] + total["c1"], "",
                     "%.2f" % total_cost if cost_known else ""])
        for tool in sorted(d["tools"], key=lambda t: -d["tools"][t]["ctx"]):
            v = d["tools"][tool]
            rows.append([ptype, period, ws, "tool", tool, "-", v["calls"],
                         "", "", "", "", "", v["ctx"], ""])
    return rows


def keep_other_ws(ws):
    """Rows from the other workstation survive a rerun here untouched."""
    if not os.path.isfile(CSV_OUT):
        return []
    with open(CSV_OUT, encoding="utf-8", newline="") as fh:
        return [r for r in list(csv.reader(fh))[1:]
                if len(r) == len(FIELDS) and r[2] != ws]


def ktok(n):
    return "~%dk" % round(int(n) / 1000.0) if int(n) >= 1000 else str(n)


def write_txt(rows):
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
        "billing dashboard is the only dollar truth.", ""]
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
    write_txt(rows)
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
    print("  -> %s + .txt twin (+ cache)" % os.path.relpath(CSV_OUT, ROOT))


if __name__ == "__main__":
    main()

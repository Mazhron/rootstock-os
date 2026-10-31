"""THE OUTPUT SHAPE (kit v1.57, the CEO 2026-10-31: "produce better and more
efficient responses while saving the most amount of tokens"): where the
manager's OUTPUT tokens go, measured from the harness transcripts.

WHY: output is priced at 5x and the usage sheet shows it as one pillar. On
the origin's five newest WS2 sessions (222 requests, every one at effort
"high") the meter said 427k output tokens while the visible output - reply
text, tool inputs, the persisted thinking - came to ~164k: the other 62% was
thinking the transcript does not keep. The kit's law already said it
(WIKI_METHOD "EFFORT MATCHES THE TASK: thinking is output; routine doc and
ledger sessions run at lower effort") but nothing measured it, so nothing
moved. This script is the measure: per day, the metered output against the
visible output (the HIDDEN share), and the effort level each request ran at
(the harness records output_config.effort in its api-request lines), so the
daily verdict can say "effort high on 100% of requests and 62% of output
unseen" and the manager can answer with /effort for the routine arcs.

Usage:
    python tools/output_shape.py            # report + one ledger line
    python tools/output_shape.py --days 14  # window (default 30)
    python tools/output_shape.py --no-record
    python tools/output_shape.py --selftest

Walks ~/.claude/projects/<this repo's slug>/ recursively (employee
transcripts live in <session>/subagents/, LESSONS "Walk the transcript
tree, never list it"); the slug is the repo path with every non-alphanumeric
character replaced by "-", matched case-insensitively (the harness lowers
the drive letter on some installs). Read-only apart from its two files:
docs/history/output_shape.txt (rewritten) and output_shape_runs.txt
(append-only, one line per run, identical lines collapsed by _ledger).

PURPOSE: Measure, per day and over the last seven active days, the metered
  output tokens against the output visible in the transcript (text, tool
  inputs, kept thinking) and the effort level of each request, write the
  report and one ledger line, and say CHECK when effort runs high on most
  requests while most output is unseen thinking.
INTENT: the CEO 2026-10-31, on the per-prompt workflow: better responses at
  fewer tokens; the output diet's effort law gets its number so the daily
  verdict, not an impression, says when a session is thinking at the top
  tier over routine work.

Search keys: output shape, hidden output, thinking tokens, effort level,
effort high, output diet, 5x output, metered output, visible output,
output_config, api-request.
See also: WIKI_METHOD.md "The output diet"; tools/usage_report.py (the
pricing law and the daily line); tools/hooks/prompt_gauge.py (the EFFORT
line); WORKFLOW_METHOD.md "The seed entry: Act on a prompt" (the EFFORT
field); docs/history/output_shape.txt; docs/history/output_shape_runs.txt.
"""
import collections
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import _ledger  # noqa: E402

REPORT = os.path.join(ROOT, "docs", "history", "output_shape.txt")
LEDGER = os.path.join(ROOT, "docs", "history", "output_shape_runs.txt")
DAYS_DEFAULT = 30
ACTIVE_DAYS = 7
HIGH_SHARE_WARN = 0.80      # share of requests at effort high (or above) that earns a CHECK
HIDDEN_SHARE_WARN = 0.50    # share of metered output not visible in the transcript
EFFORT_RE = re.compile(r'"output_config"\s*:\s*\{[^{}]*"effort"\s*:\s*"([a-z]+)"')
LEVEL_ORDER = ("low", "medium", "high", "xhigh", "max")


def workstation():
    try:
        import checkpoint as cp
        return cp.which_ws()
    except Exception:  # noqa: BLE001
        return "ws"


def transcript_dir(root=ROOT, base=None):
    """The harness folder for this repo, or None."""
    base = base or os.path.join(os.path.expanduser("~"), ".claude", "projects")
    slug = re.sub(r"[^A-Za-z0-9-]", "-", os.path.abspath(root))
    try:
        for d in os.listdir(base):
            if d.lower() == slug.lower() and os.path.isdir(os.path.join(base, d)):
                return os.path.join(base, d)
    except OSError:
        pass
    return None


def jsonl_files(d):
    out = []
    for cur, _dirs, files in os.walk(d):
        for f in files:
            if f.endswith(".jsonl"):
                out.append(os.path.join(cur, f))
    return out


def records(files):
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        yield json.loads(line)
                    except ValueError:
                        continue
        except OSError:
            continue


def _day(rec):
    ts = rec.get("timestamp") or ""
    return ts[:10] if len(ts) >= 10 else ""


def summarize(recs):
    """Pure: {day: {requests, metered_out, visible_tok, effort: Counter}}."""
    days = collections.defaultdict(lambda: {"requests": 0, "metered_out": 0, "visible_tok": 0.0,
                                            "effort": collections.Counter()})
    seen = set()
    for rec in recs:
        t = rec.get("type")
        day = _day(rec)
        if not day:
            continue
        if t == "api-request":
            d = days[day]
            d["requests"] += 1
            m = EFFORT_RE.search(json.dumps(rec))
            d["effort"][m.group(1) if m else "unknown"] += 1
        elif t == "assistant":
            msg = rec.get("message") or {}
            u = msg.get("usage") or {}
            mid = msg.get("id")
            d = days[day]
            if u and mid and mid not in seen:
                seen.add(mid)
                d["metered_out"] += int(u.get("output_tokens") or 0)
            for b in msg.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    d["visible_tok"] += len(b.get("text") or "") / 4.0
                elif b.get("type") == "thinking":
                    d["visible_tok"] += len(b.get("thinking") or "") / 4.0
                elif b.get("type") == "tool_use":
                    d["visible_tok"] += len(json.dumps(b.get("input") or {})) / 4.0
    return dict(days)


def _hidden(d):
    if d["metered_out"] <= 0:
        return 0.0
    return max(0.0, 1.0 - d["visible_tok"] / float(d["metered_out"]))


def _high_share(counter):
    n = sum(counter.values())
    if not n:
        return 0.0, 0
    hi = sum(v for k, v in counter.items() if k in LEVEL_ORDER[2:])
    return hi / float(n), n


def window(days, n_active=ACTIVE_DAYS):
    """The last n active days (days with any request or output), totals."""
    active = [k for k in sorted(days) if days[k]["requests"] or days[k]["metered_out"]]
    pick = active[-n_active:]
    tot = {"requests": 0, "metered_out": 0, "visible_tok": 0.0, "effort": collections.Counter()}
    for k in pick:
        for f in ("requests", "metered_out", "visible_tok"):
            tot[f] += days[k][f]
        tot["effort"].update(days[k]["effort"])
    return pick, tot


def verdict(tot):
    hs, n = _high_share(tot["effort"])
    hid = _hidden(tot)
    if n and hs >= HIGH_SHARE_WARN and hid >= HIDDEN_SHARE_WARN:
        return ("CHECK: effort high or above on %d%% of %d requests and %d%% of the output "
                "unseen thinking - routine arcs run at /effort medium (WIKI_METHOD \"effort "
                "matches the task\"; the ROUTE block's EFFORT line names the entry's level)"
                % (round(hs * 100), n, round(hid * 100)))
    return "normal"


def _k(n):
    return "~%dk" % round(n / 1000.0) if n >= 1000 else "%d" % int(n)


def _mix(counter):
    return " ".join("%s %d" % (k, counter[k]) for k in LEVEL_ORDER + ("unknown",) if counter.get(k))


def report_lines(days, n_days):
    cutoff = (datetime.date.today() - datetime.timedelta(days=n_days)).isoformat()
    out = ["# THE OUTPUT SHAPE (rewritten each run by tools/output_shape.py; the ledger is "
           "output_shape_runs.txt)",
           "# day | requests | metered output | visible output | HIDDEN share | effort mix",
           "# HIDDEN = metered output minus the text, tool inputs and kept thinking in the "
           "transcript: thinking the harness does not persist, priced at 5x like the rest."]
    for k in sorted(days):
        if k < cutoff:
            continue
        d = days[k]
        out.append("%s | %d | %s | %s | %d%% | %s" % (
            k, d["requests"], _k(d["metered_out"]), _k(d["visible_tok"]),
            round(_hidden(d) * 100), _mix(d["effort"]) or "-"))
    pick, tot = window(days)
    out.append("")
    out.append("LAST %d ACTIVE DAYS (%s): requests %d | metered output %s | visible %s | hidden %d%% "
               "| effort %s" % (len(pick), ", ".join(pick) or "-", tot["requests"],
                                _k(tot["metered_out"]), _k(tot["visible_tok"]),
                                round(_hidden(tot) * 100), _mix(tot["effort"]) or "-"))
    out.append("VERDICT: " + verdict(tot))
    return out, pick, tot


def ledger_line(pick, tot):
    hs, n = _high_share(tot["effort"])
    return "%s | %s | active days %d | metered out %s | hidden %d%% | effort high+ %d%% of %d | %s" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), workstation(), len(pick),
        _k(tot["metered_out"]), round(_hidden(tot) * 100), round(hs * 100), n, verdict(tot))


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    n_days = DAYS_DEFAULT
    if "--days" in argv:
        n_days = int(argv[argv.index("--days") + 1])
    d = transcript_dir()
    if not d:
        print("output_shape: no harness transcripts for this repo (slug not found under "
              "~/.claude/projects) - nothing to measure")
        return 0
    days = summarize(records(jsonl_files(d)))
    lines, pick, tot = report_lines(days, n_days)
    print("\n".join(lines))
    line = ledger_line(pick, tot)
    if "--no-record" not in argv:
        try:
            os.makedirs(os.path.dirname(REPORT), exist_ok=True)
            with open(REPORT, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            if not os.path.isfile(LEDGER):
                with open(LEDGER, "w", encoding="utf-8") as fh:
                    fh.write("# THE OUTPUT SHAPE (append-only): date time | ws | active days | metered "
                             "out | hidden share | effort high+ share of requests | verdict. Detail "
                             "in output_shape.txt.\n")
            _ledger.append_unless_identical(LEDGER, line)
        except OSError as exc:
            print("ledger write failed: %s" % exc)
    print("\n" + line)
    return 0


def _selftest():
    fails = 0

    def check(label, ok):
        nonlocal fails
        print(("PASS  " if ok else "FAIL  ") + label)
        fails += not ok

    recs = [
        {"type": "api-request", "timestamp": "2026-10-30T10:00:00Z",
         "body": {"output_config": {"effort": "high"}, "thinking": {"type": "adaptive"}}},
        {"type": "api-request", "timestamp": "2026-10-30T10:01:00Z",
         "body": {"output_config": {"effort": "high"}}},
        {"type": "assistant", "timestamp": "2026-10-30T10:00:05Z",
         "message": {"id": "m1", "usage": {"output_tokens": 1000},
                     "content": [{"type": "text", "text": "x" * 400},
                                 {"type": "tool_use", "name": "Bash", "input": {"command": "y" * 380}}]}},
        {"type": "assistant", "timestamp": "2026-10-30T10:00:05Z",   # the same message id again
         "message": {"id": "m1", "usage": {"output_tokens": 1000}, "content": []}},
        {"type": "assistant", "timestamp": "2026-10-29T09:00:00Z",
         "message": {"id": "m2", "usage": {"output_tokens": 100},
                     "content": [{"type": "text", "text": "z" * 400}]}},
        {"type": "api-request", "timestamp": "2026-10-29T09:00:00Z",
         "body": {"output_config": {"effort": "medium"}}},
        {"type": "user", "message": {"content": "no timestamp, skipped"}},
    ]
    days = summarize(recs)
    d30 = days.get("2026-10-30")
    check("a repeated message id is metered once", d30 and d30["metered_out"] == 1000)
    check("visible output counts text and tool inputs at chars/4",
          d30 and 195 <= d30["visible_tok"] <= 205)
    check("hidden share is metered minus visible", d30 and 0.79 <= _hidden(d30) <= 0.81)
    check("effort read from the api-request body", d30["effort"] == {"high": 2}
          and days["2026-10-29"]["effort"] == {"medium": 1})
    pick, tot = window(days)
    check("the window takes the active days in order", pick == ["2026-10-29", "2026-10-30"])
    check("the CHECK verdict needs high effort AND hidden output",
          verdict({"effort": collections.Counter({"high": 9, "medium": 1}), "metered_out": 100,
                   "visible_tok": 40.0}).startswith("CHECK")
          and verdict({"effort": collections.Counter({"medium": 9, "high": 1}), "metered_out": 100,
                       "visible_tok": 40.0}) == "normal"
          and verdict({"effort": collections.Counter({"high": 9}), "metered_out": 100,
                       "visible_tok": 90.0}) == "normal")
    slug_ok = transcript_dir(root="C:\\Users\\x\\Desktop\\rootstock-os", base=os.devnull) is None
    check("a missing projects folder gives None, never a crash", slug_ok)
    lines, _, _ = report_lines(days, 365)
    check("the report carries the verdict line", any(x.startswith("VERDICT:") for x in lines))
    print("output_shape selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

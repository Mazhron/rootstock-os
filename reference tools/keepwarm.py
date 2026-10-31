"""THE KEEP-WARM TRIAL (Mazhron 2026-09-29, going to bed: "Please make sure we
are keeping real data to find whats best for short vs long term options.
Stick to the maximum of 16 pings and then give me feedback at the end.")

PURPOSE: Run and measure the cache keep-warm ping. `--ping` is what the
  scheduled ping turn calls: it appends one line to the ledger (time, ping N
  of 16, live context tokens, the trial id) and prints the exact reply the
  ping turn gives, or the stop line at the cap. `--report` reads the
  session's transcript and prices every ping turn from the harness's own
  usage records: cache read, cache write, output, the weighted cost, the
  context growth each ping left behind (the residue), hit or MISS, and the
  break-even against the one cache rewrite the pings exist to prevent, at
  both cache-read multipliers (0.025 on Fable 5.1, 0.1 on every other
  model), so the short-pause and the long-pause cases each get a number.
INTENT: The cache lives one hour after its last read; a pause longer than
  that rewrites the whole context at 2x. A ping re-reads it at the read
  multiplier instead. Whether that wins depends on the pause length, the
  context size, the model, and the residue each ping leaves in the context
  for every later turn to re-read. The WORKFLOWS entry priced the ping at
  0.1x and left the residue out; this script measures both so the decision
  (keep, retune, retire) rests on the ledger, not on the arithmetic that
  proposed the trial.

Usage:
    python tools/keepwarm.py --ping [--trial ID] [--cap 16] [--interval 55]
    python tools/keepwarm.py --report [--trial ID] [--session PREFIX] [--record]
    python tools/keepwarm.py --selftest

Ledger: docs/history/keepwarm_runs.txt (append-only; PING lines while the
trial runs, one REPORT line when --report --record is called). This script
writes nothing but ledger appends and deletes nothing (the selftest feeds
the parser lines in memory, no temp file).

Search keys: keep-warm, keepwarm, cache warm, ping trial, cache TTL, cache
rewrite, break-even, residue, 16 pings, 55 minutes, ScheduleWakeup.
See also: WORKFLOWS.md "Keep the cache warm across a pause"; tools/
usage_report.py (the pricing law, the miss detector); tools/checkpoint.py
(the transcript probe); docs/history/cache_misses.txt.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint as cp  # noqa: E402  (the transcript probe, which_ws)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "history", "keepwarm_runs.txt")
MARKER = "[keep-warm ping"          # every ping prompt starts with this
CAP_DEFAULT = 16
INTERVAL_DEFAULT = 55               # minutes between pings (the TTL is 60)
# the pricing law, copied from usage_report.py so this file imports nothing
# heavy at ping time
W_INPUT, W_WRITE_1H, W_OUTPUT = 1.0, 2.0, 5.0
READ_MULT = {"fable": 0.025, "other": 0.1}
MISS_SHARE = 0.5


def now_str():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def default_trial():
    return dt.date.today().strftime("T%Y%m%d")


def ledger_lines():
    if not os.path.isfile(LEDGER):
        return []
    with open(LEDGER, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip()]


def append(line):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8", newline="") as fh:
        fh.write(line + "\n")


# ------------------------------------------------------------------ ping --
def ping(trial, cap, interval):
    """Append the PING line and print the reply the ping turn gives."""
    n = sum(1 for ln in ledger_lines()
            if "| PING |" in ln and "| %s |" % trial in ln) + 1
    ctx = cp.context_load()
    ctx_s = "%dk" % (ctx // 1000) if ctx else "?"
    append("%s | %s | PING | %s | %d/%d | ctx %s | every %dm" % (
        now_str(), cp.which_ws(), trial, n, cap, ctx_s, interval))
    if n >= cap:
        print("keep-warm: stopped after %d pings (the cap); the report is "
              "next, then re-arm at a real turn if the pause continues" % cap)
        return 1
    print("keep-warm: ping %d of %d" % (n, cap))
    return 0


# ---------------------------------------------------------------- report --
def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text") or ""
            if isinstance(part, dict) and part.get("type") == "tool_result":
                return None          # a tool result, not a human prompt
    return ""


def _ts(rec):
    t = rec.get("timestamp")
    if not t:
        return None
    try:
        return dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def parse_pings(lines):
    """[{n, start, ctx, read, write, inp, out, model, real_turn_before}] -
    one per ping prompt in the transcript lines, its cost = every assistant
    record until the next human prompt."""
    pings, cur, real_since = [], None, False
    for ln in lines:
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        typ = rec.get("type")
        msg = rec.get("message") or {}
        if typ == "user":
            txt = _text(msg.get("content"))
            if txt is None:
                continue                     # tool result
            if txt.lstrip().startswith(MARKER):
                cur = {"n": len(pings) + 1, "start": _ts(rec), "ctx": 0,
                       "read": 0, "write": 0, "inp": 0, "out": 0,
                       "model": "?", "real_turn_before": real_since}
                pings.append(cur)
                real_since = False
            else:
                cur = None
                real_since = True
        elif typ == "assistant" and cur is not None:
            u = msg.get("usage") or {}
            if not u:
                continue
            rd = int(u.get("cache_read_input_tokens") or 0)
            wr = int(u.get("cache_creation_input_tokens") or 0)
            ip = int(u.get("input_tokens") or 0)
            cur["read"] += rd
            cur["write"] += wr
            cur["inp"] += ip
            cur["out"] += int(u.get("output_tokens") or 0)
            cur["ctx"] = max(cur["ctx"], rd + wr + ip)
            m = (msg.get("model") or "").lower()
            cur["model"] = "fable" if "fable" in m else (m or cur["model"])
    return pings


def weighted(p, mult):
    return (p["inp"] * W_INPUT + p["write"] * W_WRITE_1H
            + p["read"] * mult + p["out"] * W_OUTPUT)


def _k(n):
    n = float(n)
    if abs(n) >= 1000:
        return "%.1fk" % (n / 1000.0)
    return "%d" % n


def report_lines(pings, trial, interval=INTERVAL_DEFAULT):
    if not pings:
        return ["KEEP-WARM REPORT %s: no ping turns in this transcript" % trial]
    out = ["KEEP-WARM REPORT %s: %d ping(s), from the harness usage records"
           % (trial, len(pings))]
    out.append("  n | time  | gap | ctx    | read   | write | out | hit  | "
               "residue | weighted@fable | weighted@0.1")
    prev = None
    cum = {"fable": 0.0, "other": 0.0}
    misses = 0
    residues = []
    for p in pings:
        gap = ("%3dm" % ((p["start"] - prev["start"]).total_seconds() // 60)
               if prev and p["start"] and prev["start"] else "  -")
        hit = "MISS" if p["ctx"] and p["write"] >= MISS_SHARE * p["ctx"] else "hit"
        if hit == "MISS":
            misses += 1
        res = (p["ctx"] - prev["ctx"]) if prev else 0
        if prev and not p["real_turn_before"]:
            residues.append(res)
        wf, wo = weighted(p, READ_MULT["fable"]), weighted(p, READ_MULT["other"])
        cum["fable"] += wf
        cum["other"] += wo
        out.append(" %2d | %s | %s | %6s | %6s | %5s | %3d | %-4s | %+7s | %14s | %12s" % (
            p["n"], p["start"].strftime("%H:%M") if p["start"] else "?",
            gap, _k(p["ctx"]), _k(p["read"]), _k(p["write"]), p["out"], hit,
            (_k(res) if prev else "-") + ("*" if p["real_turn_before"] else ""),
            _k(wf), _k(wo)))
        prev = p
    ctx = pings[-1]["ctx"] or 1
    rewrite = ctx * W_WRITE_1H
    out.append("  (* = a real turn sat between this ping and the last, so "
               "its residue is not the ping's)")
    out.append("  context at the end: %s; one 1h-TTL rewrite of it costs %s "
               "weighted" % (_k(ctx), _k(rewrite)))
    for key, label in (("fable", "Fable 5.1, read 0.025x"),
                       ("other", "any other model, read 0.1x")):
        per = cum[key] / len(pings)
        be = rewrite / per if per else 0
        out.append("  %s: %d pings cost %s weighted (%s each) = %.0f%% of one "
                   "rewrite; break-even at %.0f pings" % (
                       label, len(pings), _k(cum[key]), _k(per),
                       100.0 * cum[key] / rewrite, be))
    if residues:
        avg = sum(residues) / len(residues)
        out.append("  residue: %s tokens per clean ping on average (%d "
                   "measured); %d pings leave %s in the context for every "
                   "later turn to re-read" % (
                       _k(avg), len(residues), len(pings), _k(avg * len(pings))))
    out.append("  misses: %d of %d pings found the cache cold (a MISS means "
               "the gap outran the TTL, or the prefix changed)" % (
                   misses, len(pings)))
    per_f = cum["fable"] / len(pings)
    if per_f > 0:
        hours = (rewrite / per_f) * (interval / 60.0)
        out.append("  verdict (Fable): pinging every %dm beats one rewrite for "
                   "any pause under ~%.0f hours; past that the rewrite is "
                   "cheaper. A checkpoint + /clear costs only the standup "
                   "digest, so the ping is for a pause with UNCOMMITTED "
                   "context, never after a checkpoint." % (interval, hours))
    return out


def find_transcript(prefix):
    files = cp._transcript_files()
    if prefix:
        for f in files:
            if os.path.basename(f).startswith(prefix):
                return f
        return None
    return files[0] if files else None


def report(trial, session, record, interval):
    path = find_transcript(session)
    if not path:
        print("KEEP-WARM REPORT: no transcript found")
        return 1
    with open(path, encoding="utf-8") as fh:
        pings = parse_pings(fh)
    lines = report_lines(pings, trial, interval)
    print("\n".join(lines))
    if record and pings:
        append("%s | %s | REPORT | %s | %s" % (
            now_str(), cp.which_ws(), trial, " // ".join(
                ln.strip() for ln in lines if not ln.startswith("  n |")
                and not re.match(r"^\s+\d+ \|", ln))))
    return 0


# -------------------------------------------------------------- selftest --
def _selftest():
    fails = 0

    def rec(typ, content=None, usage=None, ts="2026-09-29T06:00:00Z",
            model="claude-fable-5-1"):
        m = {"content": content}
        if usage:
            m["usage"] = usage
            m["model"] = model
        return json.dumps({"type": typ, "message": m, "timestamp": ts})

    def u(rd, wr, ip=10, out=20):
        return {"cache_read_input_tokens": rd, "cache_creation_input_tokens": wr,
                "input_tokens": ip, "output_tokens": out}

    lines = [
        rec("user", "hello there"),
        rec("assistant", [], u(100000, 500)),
        rec("user", MARKER + " one]", ts="2026-09-29T06:00:00Z"),
        rec("assistant", [], u(100500, 300), ts="2026-09-29T06:00:05Z"),
        rec("user", [{"type": "tool_result", "content": "x"}]),
        rec("assistant", [], u(100800, 200), ts="2026-09-29T06:00:10Z"),
        rec("user", MARKER + " two]", ts="2026-09-29T06:55:00Z"),
        rec("assistant", [], u(101000, 400), ts="2026-09-29T06:55:05Z"),
        rec("user", MARKER + " three]", ts="2026-09-29T08:10:00Z"),
        rec("assistant", [], u(0, 101400), ts="2026-09-29T08:10:05Z"),
    ]
    pings = parse_pings(lines)
    checks = [
        ("three pings parsed", len(pings) == 3),
        ("tool result does not end the ping turn", pings[0]["write"] == 500),
        ("first ping follows a real turn", pings[0]["real_turn_before"]),
        ("second ping is clean", not pings[1]["real_turn_before"]),
        ("context is the biggest box", pings[0]["ctx"] == 101010),
        ("model read as fable", pings[0]["model"] == "fable"),
    ]
    out = report_lines(pings, "SELFTEST")
    text = "\n".join(out)
    checks += [
        ("third ping is a MISS", len(out) > 4 and "MISS" in out[4]),
        ("gap of the second ping is 55m", " 55m " in text),
        ("verdict line present", "verdict (Fable)" in text),
        ("both multipliers reported", "read 0.025x" in text and "read 0.1x" in text),
    ]
    for name, ok in checks:
        print("%s: %s" % ("PASS" if ok else "FAIL", name))
        fails += 0 if ok else 1
    print("keepwarm selftest: %d failed" % fails)
    return 1 if fails else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ping", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--record", action="store_true", help="append the report to the ledger")
    ap.add_argument("--trial", default=default_trial())
    ap.add_argument("--cap", type=int, default=CAP_DEFAULT)
    ap.add_argument("--interval", type=int, default=INTERVAL_DEFAULT)
    ap.add_argument("--session", default=None, help="transcript file prefix; default newest")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.ping:
        return ping(a.trial, a.cap, a.interval)
    if a.report:
        return report(a.trial, a.session, a.record, a.interval)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

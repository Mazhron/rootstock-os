"""THE USAGE WINDOW (Rootstock T-0930-RS-2, the CEO's ask 2026-09-30: the
standup line is retrospective - "spend was +150%" the next morning - but
Anthropic's plan limits are rolling windows (five hours, seven days). This
gives a LIVE line while it is happening, so a prompt can be answered before
the plan's own five-hour window empties.

WHERE THE NUMBERS COME FROM: the same harness JSONL transcripts
tools/usage_report.py mines (transcript_dirs(), reused here by import so
there is exactly one place that knows where the transcripts live). Every
assistant message's usage dict is weighted the same way (idea 13's weights,
also imported): input 1x, cache write 1.25x/2x (5-minute/1-hour TTL), cache
read 0.1x flat, output 5x. Streamed messages repeat a message id; counted
once, same as usage_report.

INCREMENTAL BY DESIGN: unlike usage_report's day/week/month sheet, this
tool only needs the last 7 days, at 10-minute resolution, so the cache
(.claude/usage_window_state.json, gitignored) is small: per file, the byte
offset already read and the last message id seen (never re-parse a byte
twice); plus one running weighted-token sum per 10-minute slot, pruned once
a slot falls out of the 7-day range. A cold scan (no cache yet, or a big
backlog) is capped at SCAN_TIME_CAP seconds and simply finishes on the next
run instead of blocking a prompt.

THE THREE NUMBERS: last-5h weighted (rolling from now), the PEAK 5-hour
window inside the last 7 days (a sliding-window max over the 10-minute
slots - the worst stretch the plan has actually seen recently, which is a
better ceiling than a guessed plan quota), and 7d weighted (context). The
advise line only fires when the current 5-hour window is already most of
that peak AND past a floor (a quiet week's small peak should not trigger
noise); both numbers are owner-tuned in the same committed
.claude/fanout_limits.json the fan-out guard reads (window_warn_share,
window_floor_weighted), read the same tolerant way: a missing file or a bad
value never crashes the read, it just falls back to the named default.

Usage:  python tools/usage_window.py                 # the one-line read
        python tools/usage_window.py --json           # the numbers as JSON
        python tools/usage_window.py --advise         # prints ONLY when advised
        python tools/usage_window.py --advise --record  # + ledgers an advised reading
        python tools/usage_window.py --selftest       # synthetic transcripts, PASS/FAIL

WIRED FROM: tools/hooks/prompt_gauge.py calls gauge_line() (--advise
--record, in-process) on every prompt and prints the line only when it is
non-empty; the gauge stays silent on a normal turn either way.

PURPOSE: Mine the harness transcripts for a LIVE weighted-token read of the
  last 5 hours, the peak 5-hour window inside the last 7 days, and the 7-day
  total, printed as one line or advised only past an owner-tuned share of
  that peak; incremental (byte offset + 10-minute slot cache) so a warm read
  costs well under a second.
INTENT: the CEO's ask 2026-09-30: the project's budget reading is
  retrospective (a standup line the next morning); Anthropic's plan limits
  are rolling five-hour and seven-day windows, so a live line while it is
  happening catches a run away spend before the standup would.

Search keys: usage window, live budget, rolling window, five hour window,
seven day window, weighted tokens, peak window, window advised, plan limit,
sliding window, prompt gauge line.
See also: tools/usage_report.py (transcript_dirs, the weights, cache-miss
pricing - the retrospective sheet this tool complements); tools/hooks/
prompt_gauge.py (wires gauge_line() into every prompt); tools/hooks/
fanout_guard.py (the owner-tuned-numbers-in-fanout_limits.json convention);
docs/history/usage_window_runs.txt (the ADVISED ledger).
"""
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage_report as ur

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, ".claude", "usage_window_state.json")  # gitignored
CONFIG = os.path.join(ROOT, ".claude", "fanout_limits.json")  # COMMITTED, shared with fanout_guard
LEDGER = os.path.join(ROOT, "docs", "history", "usage_window_runs.txt")
LEDGER_HEADER = [
    "# THE USAGE WINDOW LEDGER (append-only; one line per ADVISED reading of "
    "tools/usage_window.py; the standup reads the TAIL)",
    "# date time | ws | last 5h weighted | peak 5h in 7d | share | 7d weighted | verdict",
]
CACHE_VERSION = 1

WINDOW_HOURS = 5                       # the live rolling window
WINDOW_SECONDS = WINDOW_HOURS * 3600
PEAK_DAYS = 7                          # both the file-age cutoff and the peak search range
PEAK_SECONDS = PEAK_DAYS * 86400
SLOT_MINUTES = 10                      # the cache's time resolution
SLOT_SECONDS = SLOT_MINUTES * 60
SCAN_TIME_CAP = 3.0                    # seconds; a cold scan bails and finishes next run
W_CACHE_READ = 0.1                     # flat (unlike usage_report's per-model read_mult;
                                        # this tool only needs the plan-share proxy)

# Owner-tuned numbers, shared file with fanout_guard (.claude/fanout_limits.json,
# COMMITTED). Defaults are named constants; a missing file or bad value falls
# back silently, same tolerance as fanout_guard.load_limits.
WINDOW_WARN_SHARE_DEFAULT = 0.8
WINDOW_FLOOR_WEIGHTED_DEFAULT = 1_000_000
WINDOW_DEFAULTS = {
    "window_warn_share": WINDOW_WARN_SHARE_DEFAULT,
    "window_floor_weighted": WINDOW_FLOOR_WEIGHTED_DEFAULT,
}


def load_window_limits(path=CONFIG):
    """WINDOW_DEFAULTS overlaid with the owner's tuned numbers from the same
    fanout_limits.json fanout_guard reads. A missing or broken file, an
    unknown key or a non-positive value falls back silently."""
    limits = dict(WINDOW_DEFAULTS)
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        for k in WINDOW_DEFAULTS:
            v = (raw or {}).get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                limits[k] = float(v)
    except Exception:
        pass
    return limits


def get_transcript_dirs():
    """The real transcript dirs, via usage_report (one source of truth).
    scan() takes a dirs list directly, which is how a selftest injects a
    temporary directory instead of monkeypatching this."""
    return ur.transcript_dirs()


def _epoch(ts):
    """ISO8601 harness timestamp -> UTC epoch seconds, or None."""
    try:
        dt = datetime.datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError):
        return None


def _load_state(path=STATE):
    if os.path.isfile(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
            if data.get("version") == CACHE_VERSION:
                return data
        except (ValueError, OSError):
            pass
    return {"version": CACHE_VERSION, "files": {}, "slots": {}}


def _save_state(state, path=STATE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def parse_transcript(path, fstate, slots, deadline):
    """Stream new bytes of one transcript into slots (mutates fstate and
    slots). Never re-parses a byte twice: a run resumes from fstate['offset'];
    an unchanged size is a no-op. Returns True if it stopped early because
    `deadline` (a time.time() value) passed - the caller should stop
    scanning further files and finish the rest on the next run."""
    size = os.path.getsize(path)
    offset = fstate.get("offset", 0)
    if offset == size:
        return False  # already caught up to EOF, nothing new
    if offset > size:
        offset = 0  # the file shrank (rotated/replaced) - start over
        fstate["last_id"] = ""
    last_id = fstate.get("last_id", "")
    hit_deadline = False
    with open(path, "rb") as fh:
        fh.seek(offset)
        while True:
            # Check the deadline BEFORE consuming the next line (not with a
            # `for raw in fh` + late break): the iterator protocol already
            # advances the read position the moment it hands back a line, so
            # breaking after that point would silently drop it. readline()
            # keeps fh.tell() exactly at the boundary between the last
            # processed line and the next unprocessed one.
            if time.time() > deadline:
                hit_deadline = True
                break
            raw = fh.readline()
            if not raw:
                break  # EOF
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except (ValueError, UnicodeDecodeError):
                continue
            if rec.get("type") != "assistant":
                continue
            epoch = _epoch(rec.get("timestamp"))
            if epoch is None:
                continue
            msg = rec.get("message") or {}
            usage = msg.get("usage")
            if not usage:
                continue
            # A message split across records repeats its meter; count once
            # (same simplification as usage_report.parse_file: streamed
            # duplicates are consecutive, so comparing to the last id seen
            # in this file is enough).
            mid = msg.get("id") or rec.get("requestId") or ""
            if mid and mid == last_id:
                continue
            last_id = mid
            model = ur.short_model(msg.get("model"))
            if model in ("<synthetic>", "?"):
                continue
            inp = usage.get("input_tokens", 0) or 0
            out = usage.get("output_tokens", 0) or 0
            rd = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation") or {}
            c5 = cc.get("ephemeral_5m_input_tokens")
            c1 = cc.get("ephemeral_1h_input_tokens")
            if c5 is None and c1 is None:
                c5 = usage.get("cache_creation_input_tokens", 0) or 0
            c5 = c5 or 0
            c1 = c1 or 0
            weight = (inp * ur.W_INPUT + out * ur.W_OUTPUT + rd * W_CACHE_READ
                      + c5 * ur.W_WRITE_5M + c1 * ur.W_WRITE_1H)
            slot = str(int(epoch // SLOT_SECONDS) * SLOT_SECONDS)
            slots[slot] = slots.get(slot, 0.0) + weight
        fstate["offset"] = fh.tell()
    fstate["last_id"] = last_id
    return hit_deadline


def _prune_slots(slots, now_epoch):
    """Drop slots that fell out of the 7-day range - the cache stays small
    without ever touching a transcript (this only trims the derived,
    internal cache dict, not any project file)."""
    cutoff = now_epoch - PEAK_SECONDS - SLOT_SECONDS
    for k in list(slots.keys()):
        if int(k) < cutoff:
            del slots[k]


def scan(dirs, state, now_epoch, cap_seconds=SCAN_TIME_CAP):
    """Incrementally parse every *.jsonl under `dirs` modified within the
    last PEAK_DAYS days into state['slots']. Mutates state in place."""
    slots = state.setdefault("slots", {})
    files = state.setdefault("files", {})
    age_limit = now_epoch - PEAK_SECONDS
    deadline = time.time() + cap_seconds
    for tdir in dirs:
        if not os.path.isdir(tdir):
            continue
        for base, _dirs, names in os.walk(tdir):
            for name in sorted(names):
                if not name.endswith(".jsonl"):
                    continue
                path = os.path.join(base, name)
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if mtime < age_limit:
                    continue
                fstate = files.setdefault(path, {})
                if parse_transcript(path, fstate, slots, deadline):
                    _prune_slots(slots, now_epoch)
                    return  # cold-scan cap: finish the rest next run
    _prune_slots(slots, now_epoch)


def _peak_window(items):
    """items: [(epoch, weight), ...] sorted ascending. Slides a WINDOW_SECONDS
    window whose start is each item's own epoch (sufficient to find the max
    of a step function that only changes at those boundaries) and returns
    the largest sum."""
    n = len(items)
    best = 0.0
    window_sum = 0.0
    j = 0
    for i in range(n):
        while j < n and items[j][0] < items[i][0] + WINDOW_SECONDS:
            window_sum += items[j][1]
            j += 1
        best = max(best, window_sum)
        window_sum -= items[i][1]
    return best


def compute(slots, now_epoch):
    """-> (last_5h_weighted, peak_5h_in_7d_weighted, seven_day_weighted)."""
    seven_d_cut = now_epoch - PEAK_SECONDS
    five_h_cut = now_epoch - WINDOW_SECONDS
    items = sorted((int(k), v) for k, v in slots.items() if int(k) >= seven_d_cut)
    last_5h = sum(v for k, v in items if k >= five_h_cut)
    seven_d = sum(v for _k, v in items)
    peak = _peak_window(items)
    peak = max(peak, last_5h)  # the current window is itself a candidate
    return last_5h, peak, seven_d


def _k(n):
    return int(round(n / 1000.0))


def format_line(last_5h, peak, seven_d):
    share = int(round(100.0 * last_5h / peak)) if peak > 0 else 0
    return ("USAGE WINDOW: last 5h ~%dk weighted | peak 5h in 7d ~%dk weighted | "
            "%d%% of peak | 7d ~%dk weighted"
            % (_k(last_5h), _k(peak), share, _k(seven_d)))


def advise_line(last_5h, peak, limits):
    """-> the ADVISED line, or None (the normal-turn case)."""
    if peak <= 0:
        return None
    if (last_5h >= limits["window_warn_share"] * peak
            and last_5h >= limits["window_floor_weighted"]):
        share = int(round(100.0 * last_5h / peak))
        return ("WINDOW ADVISED: last 5h ~%dk weighted is %d%% of your 7-day peak "
                "5h window (~%dk). Bank the work: checkpoint now, delegate the next "
                "big read, or pause." % (_k(last_5h), share, _k(peak)))
    return None


def maybe_record(last_5h, peak, seven_d, advised, state, now_epoch,
                  ledger_path=LEDGER, ws=None):
    """Append one ADVISED line, deduplicated per 10-minute slot via
    state['last_record_slot'] (the cache this tool already keeps - no
    fragile re-parsing of the ledger's own text). Returns True if it wrote."""
    if not advised:
        return False
    slot = int(now_epoch // SLOT_SECONDS)
    if state.get("last_record_slot") == slot:
        return False
    ws = ws or ur.workstation()
    share = int(round(100.0 * last_5h / peak)) if peak > 0 else 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | ~%dk | ~%dk | %d%% | ~%dk | ADVISED\n" % (
        now_str, ws, _k(last_5h), _k(peak), share, _k(seven_d))
    is_new = not os.path.isfile(ledger_path)
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as fh:
        if is_new:
            fh.write("\n".join(LEDGER_HEADER) + "\n")
        fh.write(line)
    state["last_record_slot"] = slot
    return True


def gauge_line():
    """What tools/hooks/prompt_gauge.py calls: --advise --record in one
    in-process call. Returns the ADVISED line, or None on a normal turn or
    on any failure (a live budget read must never be the thing that breaks
    a prompt)."""
    try:
        state = _load_state()
        now_epoch = time.time()
        scan(get_transcript_dirs(), state, now_epoch)
        last_5h, peak, seven_d = compute(state.get("slots", {}), now_epoch)
        limits = load_window_limits()
        line = advise_line(last_5h, peak, limits)
        if line:
            maybe_record(last_5h, peak, seven_d, line, state, now_epoch)
        _save_state(state)
        return line
    except Exception:  # noqa: BLE001 - never break the calling hook
        return None


# --------------------------------------------------------------- selftest --
def _make_transcript(dirpath, name, records):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path


def _asst(ts_epoch, mid, in_tok=1000, out_tok=200, read_tok=0, c5=0, c1=0):
    dt = datetime.datetime.fromtimestamp(ts_epoch, datetime.timezone.utc)
    return {
        "type": "assistant",
        "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "message": {
            "id": mid,
            "model": "claude-sonnet-5-20260101",
            "usage": {
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cache_read_input_tokens": read_tok,
                "cache_creation": {"ephemeral_5m_input_tokens": c5,
                                   "ephemeral_1h_input_tokens": c1},
            },
        },
    }


def _selftest():
    import tempfile
    fails = 0

    def check(ok, desc):
        nonlocal fails
        print(("PASS  " if ok else "FAIL  ") + desc)
        fails += not ok

    now = time.time()
    one_weight = 1000 * ur.W_INPUT + 200 * ur.W_OUTPUT  # the _asst() default box

    with tempfile.TemporaryDirectory() as tmp:
        # A message 2h ago (inside the 5h window) plus its streamed repeat
        # (same message id - must dedup to ONE count).
        recs = [
            _asst(now - 2 * 3600, "msg_a"),
            _asst(now - 2 * 3600, "msg_a"),  # streamed repeat, same id
        ]
        _make_transcript(tmp, "session_a.jsonl", recs)
        state = {"version": CACHE_VERSION, "files": {}, "slots": {}}
        scan([tmp], state, now)
        last_5h, peak, seven_d = compute(state["slots"], now)
        check(abs(last_5h - one_weight) < 1e-6,
              "weighting: input*1 + output*5 matches, dedup drops the streamed repeat")

        # Cache-write split (5m vs 1h) and a flat cache-read weight.
        with tempfile.TemporaryDirectory() as tmp2:
            rec = _asst(now - 60, "msg_b", in_tok=0, out_tok=0, read_tok=1000, c5=100, c1=50)
            _make_transcript(tmp2, "session_b.jsonl", [rec])
            state2 = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            scan([tmp2], state2, now)
            l5, pk, s7 = compute(state2["slots"], now)
            expected = 1000 * W_CACHE_READ + 100 * ur.W_WRITE_5M + 50 * ur.W_WRITE_1H
            check(abs(l5 - expected) < 1e-6,
                  "weighting: cache read 0.1x flat, cache write 5m/1h split honored")

        # 5h vs 7d: one message inside 5h, one outside 5h but inside 7d.
        with tempfile.TemporaryDirectory() as tmp3:
            recs3 = [_asst(now - 3600, "msg_in5h"),
                     _asst(now - 3 * 86400, "msg_in7d_only")]
            _make_transcript(tmp3, "session_c.jsonl", recs3)
            state3 = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            scan([tmp3], state3, now)
            l5, pk, s7 = compute(state3["slots"], now)
            check(abs(l5 - one_weight) < 1e-6, "5h sum excludes the 3-day-old message")
            check(abs(s7 - 2 * one_weight) < 1e-6, "7d sum includes both messages")

            # Peak window: a synthetic burst 2 days ago, well above the
            # current (near-zero) live window, must be the reported peak.
            burst_epoch = now - 2 * 86400
            burst_recs = [_asst(burst_epoch + i * 60, "burst_%d" % i, in_tok=5000, out_tok=1000)
                          for i in range(5)]
            _make_transcript(tmp3, "session_burst.jsonl", burst_recs)
            state3b = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            scan([tmp3], state3b, now)
            l5b, pkb, s7b = compute(state3b["slots"], now)
            burst_weight = 5 * (5000 * ur.W_INPUT + 1000 * ur.W_OUTPUT)
            check(pkb >= burst_weight - 1e-6 and pkb > l5b,
                  "peak 5h in 7d finds the old burst, not just the live window")

        # Cache: a second scan of unchanged files parses zero new bytes and
        # leaves the weighted sums unchanged.
        with tempfile.TemporaryDirectory() as tmp4:
            recs4 = [_asst(now - 100, "msg_cache")]
            path4 = _make_transcript(tmp4, "session_d.jsonl", recs4)
            state4 = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            scan([tmp4], state4, now)
            slots_after_1 = dict(state4["slots"])
            offset_after_1 = state4["files"][path4]["offset"]
            size4 = os.path.getsize(path4)
            scan([tmp4], state4, now)  # nothing changed on disk
            check(state4["files"][path4]["offset"] == offset_after_1 == size4,
                  "warm cache: offset already at EOF, nothing new to read")
            check(state4["slots"] == slots_after_1,
                  "warm cache: a second scan does not double-count")

        # Cold-scan cap: a near-zero deadline stops mid-file; a normal-cap
        # follow-up run finishes it (same total as one uncapped run).
        with tempfile.TemporaryDirectory() as tmp5:
            recs5 = [_asst(now - 500 + i, "cold_%d" % i) for i in range(50)]
            path5 = _make_transcript(tmp5, "session_e.jsonl", recs5)
            state5 = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            fstate = state5["files"].setdefault(path5, {})
            hit = parse_transcript(path5, fstate, state5["slots"], time.time() - 1)
            partial_offset = fstate.get("offset", 0)
            check(hit and partial_offset < os.path.getsize(path5),
                  "cold-scan cap: an exhausted deadline stops before EOF")
            hit2 = parse_transcript(path5, fstate, state5["slots"], time.time() + SCAN_TIME_CAP)
            check(not hit2 and fstate["offset"] == os.path.getsize(path5),
                  "cold-scan cap: the next run finishes from where it stopped")
            total_expected = 50 * one_weight
            check(abs(sum(state5["slots"].values()) - total_expected) < 1e-6,
                  "cold-scan cap: the two-part read sums to the same total as one pass")

        # Advise threshold, both sides.
        limits = {"window_warn_share": 0.8, "window_floor_weighted": 1000}
        ok_line = advise_line(10000, 12000, limits)  # 83% >= 80%, past the floor
        check(ok_line is not None and "WINDOW ADVISED" in ok_line,
              "advise fires past the share threshold and the floor")
        no_line_share = advise_line(5000, 12000, limits)  # 42% < 80%
        check(no_line_share is None, "advise silent below the share threshold")
        no_line_floor = advise_line(900, 1000, limits)  # 90% share, under the floor
        check(no_line_floor is None, "advise silent under the floor even at high share")

        # Record dedup: two calls in the same 10-minute slot write ONE line.
        with tempfile.TemporaryDirectory() as tmp6:
            ledger_path = os.path.join(tmp6, "usage_window_runs.txt")
            rec_state = {"version": CACHE_VERSION, "files": {}, "slots": {}}
            wrote1 = maybe_record(10000, 12000, 15000, ok_line, rec_state, now,
                                   ledger_path=ledger_path)
            wrote2 = maybe_record(10000, 12000, 15000, ok_line, rec_state, now,
                                   ledger_path=ledger_path)
            body = open(ledger_path, encoding="utf-8").read().splitlines()
            data_lines = [ln for ln in body if not ln.startswith("#")]
            check(wrote1 and not wrote2 and len(data_lines) == 1,
                  "record dedup: the same 10-minute slot writes only once")

    print("usage_window selftest: %d failed" % fails)
    return 1 if fails else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        sys.exit(_selftest())
    state = _load_state()
    now_epoch = time.time()
    scan(get_transcript_dirs(), state, now_epoch)
    last_5h, peak, seven_d = compute(state.get("slots", {}), now_epoch)
    if "--advise" in argv:
        limits = load_window_limits()
        line = advise_line(last_5h, peak, limits)
        if line:
            print(line)
            if "--record" in argv:
                maybe_record(last_5h, peak, seven_d, line, state, now_epoch)
        _save_state(state)
        return
    _save_state(state)
    if "--json" in argv:
        share = int(round(100.0 * last_5h / peak)) if peak > 0 else 0
        print(json.dumps({
            "last_5h_weighted": int(round(last_5h)),
            "peak_5h_in_7d_weighted": int(round(peak)),
            "share_pct": share,
            "seven_day_weighted": int(round(seven_d)),
        }))
        return
    print(format_line(last_5h, peak, seven_d))


if __name__ == "__main__":
    main()

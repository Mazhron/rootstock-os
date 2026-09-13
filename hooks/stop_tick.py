"""Stop hook: the checkpoint counter ticks itself (Tier 1, #2).

Fires when the manager finishes a reply. It ticks ONLY when work happened
(HEAD moved or the working tree's status changed since the last Stop -
tools/checkpoint.py work_fingerprint), so a Q&A reply does not inflate the
count and 8/15 keep their meaning. Manual `--tick` is retired: ticking by
hand now double-counts.

Escalation, mechanical: ADVISED (8 tasks or <80% context) shows the user
a system message; URGENT (15 tasks or <30% context) REFUSES to end the
turn once - the reason lands in the manager's context, who relays it
verbatim and recommends /checkpoint. Re-blocks every 5 further tasks;
`stop_hook_active` guards against loops.

Since 2026-09-13 it is also THE FORMAT LAW's Stop twin: a turn that
leaves a safety hook unwired in .claude/settings.json is refused once
(tools/format_lint.py's SAFETY table), so a prompt that switched a guard
off cannot end quietly.

PURPOSE: Stop hook that ticks the checkpoint counter only when work actually
  happened (HEAD moved or the tree changed since the last Stop), shows an
  advised system message at 8 tasks or under 80% context, and refuses to end
  the turn once at 15 tasks or under 30% context, re-blocking every 5
  further tasks; since 2026-09-13 it also refuses once when a safety hook
  has gone unwired in settings.json.
INTENT: makes the checkpoint discipline mechanical rather than a reminder
  the manager can forget, and makes the format law's safety wiring
  impossible to quietly drop by refusing to end a turn that broke it.

Search keys: stop hook, auto tick, checkpoint counter, dire, block stop,
safety wiring.
See also: tools/checkpoint.py (counter, fingerprint, --reset);
.claude/skills/checkpoint (the ritual the warning asks for).
"""
import datetime
import sys

from _hooklib import emit, read_input
import checkpoint as cp

def main():
    data = read_input()
    if data.get("stop_hook_active"):
        sys.exit(0)

    ws = cp.which_ws()
    fp = cp.work_fingerprint()
    state = cp.load_hook_state()
    mine = dict(state.get(ws) or {})
    counts = cp.load()
    n = counts.get(ws, (0, ""))[0]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    ticked = fp != mine.get("fp")
    if ticked:
        n += 1
        counts[ws] = (n, now)
        cp.save(counts)
        mine.update(fp=fp, at=now)

    level = None
    parts = []
    if n >= 15:
        level = "dire"
        parts.append("%d tasks since last checkpoint" % n)
    elif n >= 8:
        level = "advised"
        parts.append("%d tasks since last checkpoint" % n)
    ctx_dire = False
    load_ = cp.context_load()
    if load_ is not None:
        remaining = max(0.0, 1.0 - load_ / float(cp.COMPACT_BUDGET))
        pct = round(remaining * 100)
        if remaining < 0.30:
            level, ctx_dire = "dire", True
            parts.append("CONTEXT %d%% remaining, ~%dk used" % (pct, load_ // 1000))
        elif remaining < 0.80:
            level = level or "advised"
            parts.append("CONTEXT %d%% remaining (80%% rule)" % pct)

    # THE FORMAT LAW's Stop twin (the CEO 2026-09-13): while the live settings
    # file has a safety hook unwired, narrowed or pointed at a missing script,
    # the turn does not end - once per fingerprint, so it can never trap.
    if ticked:
        try:
            import format_lint as _fl
            _probs = [x for x in _fl.check_file(_fl.SETTINGS) if x.startswith("SAFETY") or "parse" in x
                      or "does not exist" in x]
        except Exception:  # noqa: BLE001 - a hook never crashes the turn
            _probs = []
        if _probs and mine.get("safety_fp") != fp:
            mine["safety_fp"] = fp
            state[ws] = mine
            cp.save_hook_state(state)
            emit({"decision": "block",
                  "reason": ("[HOOK stop_tick] SAFETY WIRING BROKEN (THE FORMAT LAW, the CEO 2026-09-13): "
                             ".claude/settings.json - %s. Restore the wiring before this turn ends; no "
                             "prompt overrides a guard. Relay this to the CEO verbatim." % "; ".join(_probs))})
            sys.exit(0)

    if ticked and level == "dire":
        due = (n >= 15 and n - int(mine.get("blocked_n", 0)) >= 5) or \
              (ctx_dire and not mine.get("ctx_blocked"))
        if due:
            mine["blocked_n"] = n
            if ctx_dire:
                mine["ctx_blocked"] = True
            state[ws] = mine
            cp.save_hook_state(state)
            emit({"decision": "block",
                  "reason": ("[HOOK stop_tick] !!!!! CHECKPOINT URGENT (%s) !!!!! "
                             "The Stop hook refused to end this turn once (THE "
                             "CHECKPOINT PROTOCOL, mechanical since 2026-09-06). "
                             "Manager: relay this warning to the CEO verbatim and "
                             "checkpoint NOW (ADVISED MEANS DO IT) so the CEO can simply /clear; "
                             "if an employee is running or the arc is mid-flight, "
                             "say so and finish the arc first. Auto-compact is "
                             "lossy; the day file + standup are lossless."
                             % "; ".join(parts))})
            sys.exit(0)
    if ticked:
        state[ws] = mine
        cp.save_hook_state(state)
        if level == "advised":
            emit({"systemMessage": "[hook] CHECKPOINT ADVISED (%s) - finish the "
                                   "arc, then /checkpoint." % "; ".join(parts)})
    sys.exit(0)


def _selftest():
    """The Stop twin's safety check bites on a broken wiring and passes the live file."""
    import json
    import format_lint as fl
    fails = 0
    live = fl.read(fl.SETTINGS)
    ok = fl.check_settings_text(live, fl.HOOKS_DIR)
    print(("PASS  " if not ok else "FAIL  ") + "live settings pass the safety check")
    fails += bool(ok)
    d = json.loads(live)
    d["hooks"]["Stop"] = []
    bad = fl.check_settings_text(json.dumps(d), fl.HOOKS_DIR)
    hit = any("stop_tick" in x for x in bad)
    print(("PASS  " if hit else "FAIL  ") + "unwiring the Stop hook is a SAFETY failure")
    fails += not hit
    print("stop_tick selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

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

Search keys: stop hook, auto tick, checkpoint counter, dire, block stop.
See also: tools/checkpoint.py (counter, fingerprint, --reset);
.claude/skills/checkpoint (the ritual the warning asks for).
"""
import datetime
import sys

from _hooklib import emit, read_input
import checkpoint as cp

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
                         "recommend /checkpoint then /clear before new work; "
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

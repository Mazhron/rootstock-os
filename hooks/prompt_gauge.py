"""UserPromptSubmit hook: the context gauge + task counter, every prompt
(Tier 1, #3). SILENT unless a threshold is crossed - zero tokens on a
normal turn. When it speaks, the manager relays the line verbatim
(the CEO's 80% rule 2026-09-04; the 8/15 task thresholds 2026-09-02).

Search keys: prompt hook, context gauge, 80 percent rule, task counter.
See also: tools/checkpoint.py (thresholds + the transcript probe);
tools/hooks/stop_tick.py (the tick that feeds the counter).
"""
from _hooklib import read_input  # noqa: F401  (sets sys.path)
import checkpoint as cp

read_input()
ws = cp.which_ws()
n = cp.load().get(ws, (0, ""))[0]
lines = []
if n >= 15:
    lines.append("!!!!! CHECKPOINT URGENT (%d tasks since last checkpoint) - "
                 "checkpoint before taking new work !!!!!" % n)
elif n >= 8:
    lines.append("~~ CHECKPOINT ADVISED (%d tasks since last checkpoint) - "
                 "finish the arc, then checkpoint ~~" % n)
load_ = cp.context_load()
if load_ is not None:
    remaining = max(0.0, 1.0 - load_ / float(cp.COMPACT_BUDGET))
    pct = round(remaining * 100)
    if remaining < 0.30:
        lines.append("!!!!! CHECKPOINT URGENT (CONTEXT: %d%% remaining, ~%dk "
                     "used) - checkpoint + /clear NOW; auto-compact is lossy "
                     "!!!!!" % (pct, load_ // 1000))
    elif remaining < 0.80:
        lines.append("~~ CHECKPOINT ADVISED (CONTEXT: %d%% remaining, ~%dk "
                     "used; the CEO's 80%% rule) - suggest checkpoint + /clear "
                     "at the next arc boundary ~~" % (pct, load_ // 1000))
if lines:
    print("[HOOK prompt_gauge] " + " | ".join(lines)
          + " (relay to the CEO verbatim)")

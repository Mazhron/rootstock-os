---
name: checkpoint
description: Close an arc safely - push, refresh the day file's WHERE WE LEFT OFF with both sides of the final exchange, reset the task counter, and emit the safe-to-clear marker. Use at arc end or when the checkpoint counter warns.
---

# /checkpoint - close the arc so the chat can be cleared losslessly

PRECONDITIONS (refuse and say why if any fail):
- No employee (sub-agent) running.
- No uncommitted work; never checkpoint mid-arc.

SEQUENCE
1. Push everything (tree clean, remote up to date).
2. Refresh the NEWEST day file's `## WHERE WE LEFT OFF` section
   (docs/history/days/YYYY-MM-DD-WS#.md; create today's file + a
   days_index.txt line if it does not exist). The section carries:
   - USER'S LAST PROMPT (condensed)
   - MANAGER'S LAST RESPONSE (condensed) - BOTH sides, always
   - STATE (version, tree, what shipped this arc)
   - OPEN QUEUE / NEXT LIKELY
3. Run `python tools/checkpoint.py --reset`.
4. Commit + push the day-file refresh.
5. End the reply with the marker, verbatim:
   "CHECKPOINT - safe to /clear. Nothing in this chat exists only in this chat."

Also: run `python tools/checkpoint.py --tick` after EVERY completed task in
normal work; relay its warnings (advised at 8, dire at 15) verbatim.

IF THE SCRIPTS/DAY FILES ARE MISSING (new project): bootstrap them per
REPORTING_METHOD.md, or ask the user for their future-project kit.

Search keys: checkpoint, safe to clear, day file, context budget, arc end.
See also: standup skill (resumption side); ship skill (per-batch, smaller).

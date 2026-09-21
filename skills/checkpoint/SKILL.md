---
name: checkpoint
description: Close an arc safely - push, refresh the day file's WHERE WE LEFT OFF with both sides of the final exchange, reset the task counter, and emit the safe-to-clear marker. Use at arc end or when the checkpoint counter warns.
---

# /checkpoint - close the arc so the chat can be cleared losslessly

PURPOSE: Close an arc safely: push, refresh the day file's WHERE WE LEFT OFF
  section with both sides of the final exchange verbatim, reset the task
  counter, and emit the safe-to-clear marker.
INTENT: Mazhron's ruling 2026-09-10, ADVISED MEANS DO IT: the owner never
  has to ask to checkpoint, they simply /clear afterward, so after /clear
  the owner should have nothing lost, everything they need is given back
  unprompted.

ADVISED MEANS DO IT (the owner's ruling 2026-09-10): when the prompt
gauge or the Stop hook says CHECKPOINT ADVISED, run this sequence at the
END OF THAT REPLY, unprompted - the owner never has to ask, they simply
/clear afterwards. Mid-arc: finish the current step, ship it, then
checkpoint before taking new work.

PRECONDITIONS (refuse and say why if any fail):
- No employee (sub-agent) running.
- No uncommitted work; never checkpoint mid-arc.

SEQUENCE
0. Close the loop (THE LOOP LAW, 2026-09-14): `python tools/run_all.py
   session` (regen + check + metrics append their ledgers; the session-
   start hook also runs it once a day, so this is usually seconds). If the
   Stop hook said CHANGELOG UNEXPORTED, run `python tools/export_changelog.py`
   now. Ask once: was anything this arc done by hand twice? Then it is a
   WORKFLOW GAP - write the WORKFLOWS.md entry (or brief a haiku) before
   pushing. Ask a second time: was anything this arc learned by trial and
   error, or corrected? Then it is a LESSON (THE LESSON LAW, 2026-09-20):
   write or amend the LESSONS.md entry before pushing.
1. Push everything (tree clean, remote up to date), then
   `python tools/backup_push.py` (THE LOCAL MIRROR + THE BROWSABLE COPY).
2. Refresh the NEWEST day file's `## WHERE WE LEFT OFF` section
   (docs/history/days/YYYY-MM-DD-WS#.md; create today's file + a
   days_index.txt line if it does not exist). The section carries:
   - USER'S LAST PROMPT (VERBATIM - copied word for word, unabridged,
     in a fenced quote block; NEVER condensed or paraphrased)
   - MANAGER'S LAST RESPONSE (VERBATIM) - BOTH sides, always. MECHANICS:
     the response stored is the checkpoint reply itself, so write this
     section containing the reply you are ABOUT to send, then send
     exactly that text. The user must recognize their own words at the
     next standup - a paraphrase is a failed checkpoint.
     (SAFETY NET: standup independently mines the true final exchange
     from the harness transcript, so a mid-arc /clear no longer loses
     post-checkpoint work - but this section remains the committed,
     searchable record; keep writing it faithfully.)
   - STATE (version, tree, what shipped this arc)
   - OPEN QUEUE / NEXT LIKELY
3. Commit + push the day-file refresh.
4. Run `python tools/checkpoint.py --reset` LAST - it also stores the
   Stop hook's work fingerprint, so the checkpoint commit itself is not
   counted as a task.
5. End the reply with the marker, verbatim:
   "CHECKPOINT - safe to /clear. Nothing in this chat exists only in this chat."

The counter TICKS ITSELF (Stop hook, 2026-09-06) whenever a reply changed
the tree or HEAD - never tick by hand, it double-counts. Relay its warnings
(advised at 8, dire at 15 - at dire the Stop hook refuses to end the turn
once and the prompt hook repeats the line) verbatim.

THE CONTEXT GAUGE (Mazhron's 80% rule, 2026-09-04): every tick/status
also prints the live context load, probed from the harness transcript.
REGARDLESS of the task count, once less than 80% of the auto-compact
budget remains, CHECKPOINT at the end of the current reply if the arc
is closed (ADVISED MEANS DO IT); under 30% remaining, treat it as
URGENT and checkpoint before taking new work. Auto-compact is a lossy summary - the day file + standup are
lossless, so clearing early is always the cheaper path. Relay the
gauge line and its warnings verbatim, like the task warnings.

THE NET UNDER THIS RITUAL (the owner's ask 2026-09-20): the SessionEnd
hook (tools/hooks/session_end.py) runs at /clear. With nothing unbanked
it writes one ledger line; with unbanked work it does steps 1-4 by
itself, mechanically (the exchange mined from the transcript, an AUTO
section, a "Checkpoint (auto)" commit, origin + mirror, the reset) and
leaves NEXT LIKELY unwritten. It exists so a forgotten checkpoint loses
nothing; it is not a reason to skip this ritual.

IF THE SCRIPTS/DAY FILES ARE MISSING (new project): bootstrap them per
REPORTING_METHOD.md, or ask the user for their future-project kit.

Search keys: checkpoint, safe to clear, day file, context budget, arc end.
See also: standup skill (resumption side); ship skill (per-batch, smaller).

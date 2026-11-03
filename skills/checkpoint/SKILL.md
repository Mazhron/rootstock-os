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
gauge or the Stop hook says CHECKPOINT DUE (formerly ADVISED), run this
sequence at the END OF THAT REPLY, unprompted - the owner never has to
ask, they simply /clear afterwards. THE DUE LINE (the owner 2026-10-12:
"change this hook from advising a checkpoint to DO the checkpoint ...
Any conversation after should have a checkpoint happen until the
clear/standup ritual is complete"): past the 80% context line the hook
prints DUE on every prompt, and every one of those replies ends with
this sequence; an open arc is checkpointed AS OPEN (WHERE WE LEFT OFF
names the step mid-way). Mid-batch: ship the step first, then checkpoint
in the same reply. Only a running employee waits.

PRECONDITIONS (the one wait):
- No employee (sub-agent) running. Uncommitted work is not a refusal:
  ship it first, then checkpoint in the same reply; an open arc is
  checkpointed as open (THE DUE LINE above).

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
2. Refresh THIS MACHINE's newest day file's `## WHERE WE LEFT OFF`
   section (docs/history/days/YYYY-MM-DD-WS#.md where WS# is
   tools/workstation_survey.ws_name(), NEVER the file the standup's
   SAME DAY line named, which is the newest by timestamp and may be the
   other machine's - LESSONS "The standup's SAME DAY line"; create
   today's file + a days_index.txt line if it does not exist). The section carries:
   - USER'S LAST PROMPT (VERBATIM - copied word for word, unabridged,
     in a fenced quote block; NEVER condensed or paraphrased)
   - MANAGER'S LAST RESPONSE - BOTH sides, always. MECHANICS (THE
     SAFEGUARD FIX, Mazhron 2026-11-03 PM, reverting the morning's
     whole-turn rule): the response stored is the FINAL MESSAGE of the
     turn, the one written to stand alone, capped at about 2000
     characters and never containing a quoted copy of an earlier
     exchange (a relay never nests). The working lines written between
     tool calls are not the reply. If the assessment that matters was
     given earlier in the turn, restate its conclusion in the final
     message so the final message carries it. The user must recognize
     their own prompt at the next standup; the reply side is the
     conclusion, not a transcript. THE VERBATIM OPENER (Mazhron
     2026-11-03 15:35: "I prefer a verbatim opener. Even if it costs a
     little bit more."): the next standup quotes this stored reply
     word for word, so write it to be read back; a session opener's own
     final message never re-quotes the relay it just gave (the miner
     strips a nested relay, but the day file copy is written by hand).
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
5. End the reply with the marker, the gauge tail pasted from --reset's
   "marker tail:" line (Mazhron 2026-11-02 - the same shape every hook
   prints, due or not):
   "CHECKPOINT - safe to /clear (CONTEXT: 75% remaining, ~228k used of
   ~925k (25% used); 0 task(s)). Nothing in this chat exists only in this chat."
6. ARM THE KEEP-WARM (kit v1.57, the owner's yes 2026-10-31) when this
   reply leaves the session open (the owner has not said they are
   clearing now): one ScheduleWakeup per WORKFLOWS.md "Keep the cache
   warm across a pause" (delaySeconds 3300, noop true, the ping prompt
   from the entry; cap 25 on Fable, 9 elsewhere). A /clear ends it for
   free; a pause of an hour or more is one cache rewrite saved (~90k-230k
   weighted each on the origin's ledger). The old WHEN line (never after
   a checkpoint) is kept in the entry; to go back, skip this step.

The counter TICKS ITSELF (Stop hook, 2026-09-06) whenever a reply changed
the tree or HEAD - never tick by hand, it double-counts. Relay its warnings
(advised at 8, dire at 15 - at dire the Stop hook refuses to end the turn
once, then again every five tasks, and the prompt hook repeats the line)
verbatim.

THE CONTEXT GAUGE (Mazhron's 80% rule, 2026-09-04): every tick/status
also prints the live context load, probed from the harness transcript.
REGARDLESS of the task count, once less than 80% of the auto-compact
budget remains, CHECKPOINT at the end of the current reply and of every
reply after it until the /clear (THE DUE LINE); under 30% remaining, treat it as
URGENT and checkpoint before taking new work. Auto-compact is a lossy summary - the day file + standup are
lossless, so clearing early is always the cheaper path. Relay the
gauge line and its warnings verbatim, like the task warnings. THE PERCENT
LINE (Mazhron 2026-10-30: "be sure in the future to give me % used or
left"): the prompt hook prints the percent on EVERY prompt, DUE or not,
and every reply states it in one line, usually the last.

THE NET UNDER THIS RITUAL (the owner's ask 2026-09-20): the SessionEnd
hook (tools/hooks/session_end.py) runs at /clear. With nothing unbanked
it writes one ledger line; with unbanked work it does steps 1-4 by
itself, mechanically (the exchange mined from the transcript, an AUTO
section, a "Checkpoint (auto)" commit, origin + mirror, the reset) and
leaves NEXT LIKELY unwritten. It exists so a forgotten checkpoint loses
nothing; it is not a reason to skip this ritual.

IF THE SCRIPTS/DAY FILES ARE MISSING (new project): bootstrap them per
REPORTING_METHOD.md, or ask the user for their future-project kit.

Search keys: checkpoint, safe to clear, day file, context budget, arc end,
keep-warm, arm the ping.
See also: standup skill (resumption side); ship skill (per-batch, smaller).

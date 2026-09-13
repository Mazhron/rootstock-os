---
name: correct
description: Walk a correction - ask what needs correcting, record the owner's words, resolve the intent claim DIFFERENT, then fire /intent, then fix - invoked when the user says "correct", "correction", "that's wrong", "not what I meant", "fix that", or invokes /correct.
---

# /correct - record the words, ask the why, then fix

PURPOSE: Walk a correction: ask what needs correcting, record the owner's
  words, resolve the open intent claim DIFFERENT, fire /intent, then fix the
  thing.
INTENT: Mazhron's ruling 2026-09-13: a correction is not just a fix, it is
  evidence about a misread intent; recording it before fixing means a lost
  session loses nothing, and asking what the intent was right after captures
  the mismatch while it is still fresh.

THE POINT (Mazhron's ruling 2026-09-13): a correction is not just a fix,
it is evidence about a misread intent. Recording it before fixing means a
lost session loses nothing, and asking "what was the intent?" right after
means the mismatch gets captured while it is still fresh.

1. ASK exactly: "What about the last thing I did needs correcting?" and
   wait for the answer.
2. RECORD IT before fixing anything:
   `python tools/correction_log.py --record --actor <fable, or the
   employee's model if an employee built the thing> --shipped "<what was
   built, 3-10 words>" --wrong "<Mazhron's words, VERBATIM>" [--intent-id
   <the open claim's id, from python tools/intent_log.py --pending or
   --last>] [--intent-ref "<INTENT.md heading if known>"]`
   - the script resolves the named intent claim DIFFERENT with
     source=correction by itself; nothing else to do for that step.
3. SAY BACK, in one line, what will be fixed. Then ask exactly: "What was
   the intent?" and run the /intent skill's steps on the answer - this is
   the feedback loop: correction, then why, while the mismatch is fresh.
4. FIX the thing.
5. `python tools/correction_log.py --fixed <id> --fix "<commit subject or
   note>"` and ship.
6. If the correction reveals a rule that will recur, add the law where it
   belongs (a CLAUDE.md standing rule or the relevant method file) with a
   pointer to the INTENT.md section just filed.

RULES
- Never argue the correction inside this skill. THE CONTRADICTION RULE
  lives elsewhere: if the correction contradicts an earlier ruling, say so
  in one line and ask - never silently comply, never silently refuse.
- Never record a paraphrase - Mazhron's words go in --wrong exactly as
  said.
- The record is written BEFORE the fix, so a lost session loses nothing.
- An employee's mistake is still recorded here (actor = its model) and
  also tallied in SUBAGENTS.md's ledger by the manager - two ledgers, one
  event.

Search keys: correct, correction, that's wrong, not what I meant, fix
that, correction ritual, feedback loop.
See also: tools/correction_log.py; /intent skill (fired as step 3);
INTENT.md; SUBAGENTS.md (employee corrections tally, rule 6 escalation);
WORKFLOWS.md "Correct a mistake".

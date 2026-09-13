---
name: intent
description: Record the WHY of a ruling in the owner's words and resolve the open intent claim - invoked when the user says "intent", "the why", "what I meant", after a correction, or when the manager hits a "what did the user mean by this?" question.
---

# /intent - file the why in the owner's own words, then close the claim

PURPOSE: Record the WHY of a ruling in the owner's own words in INTENT.md
  and resolve the open intent claim comparing the manager's reading against
  it.
INTENT: Mazhron's ruling 2026-09-13: a ruling is not just a rule, it is a
  WHY, and knowing the why lets Claude or any employee make the same call
  next time without asking.

THE POINT (Mazhron's ruling 2026-09-13): a ruling is not just a rule, it
is a WHY - and knowing the why lets Claude or any employee make the same
call next time without asking. INTENT.md holds one section per ruling;
this skill is how a section gets filed and how the running comparison
(Claude's reading vs Mazhron's actual intent) gets closed out.

1. GET THE WORDS. If Mazhron has not yet stated the intent in this
   conversation, ask exactly: "What was the intent?" and wait. If he
   already stated it, quote it back and confirm before filing - never
   file words that were not actually said.
2. FILE THE SECTION in INTENT.md, in the existing format:
   - a searchable `## <nouns>` heading naming what a search would look for
   - `ASKED (Mazhron YYYY-MM-DD): "..."` - his prompt VERBATIM, never
     paraphrased
   - `WHY (verbatim): "..."` - his reasons, numbered where he numbered them
   - `GENERALIZES TO (manager's reading): ...` - marked as the manager's
     own reading, never presented as his words
   - `LIVES IN: ...` - the law, file or script the rule lives in
   - a `Tags: intent, ... | one-line brief` line
   - a `See also:` line
   If a section for this ruling already exists, extend it - append a
   dated ASKED/WHY pair under the existing heading - rather than filing a
   duplicate.
3. RESOLVE THE OPEN CLAIM:
   `python tools/intent_log.py --pending` to find the claim, then
   `python tools/intent_log.py --resolve <id> --theirs "<Mazhron's words>"
   --verdict same|similar|different --source stated|correction
   --intent-ref "<the heading just filed>"`
   - SAME: the manager's claimed reading matched.
   - SIMILAR: matched in substance, a detail differed and was adjusted.
   - DIFFERENT: a rebuild or correction was needed.
   Source is `correction` when the /correct skill led here, `stated`
   otherwise.
4. POINT THE LAW. If a rule in CLAUDE.md or a method file carries this
   ruling, add one line to it: "(intent: INTENT.md '<heading>')" - one
   line, nothing else about that law moves.
5. Ship with the current batch - no separate commit needed for this alone.

RULES
- Mazhron's words are sacred: verbatim, no cleanup, no dashes added where
  he did not write them.
- Never write an intent Mazhron did not state. A guess belongs only in
  GENERALIZES TO, marked as the manager's reading.
- No employee ever invokes this skill - filing intent is the manager's
  job; an employee that hits the question relays it up instead.

Search keys: intent, the why, what I meant, record intent, file a ruling,
resolve claim, same similar different.
See also: INTENT.md (the sections themselves); tools/intent_log.py;
/correct skill (fires this as its third step); INTENT_METHOD.md
(portable); WORKFLOWS.md "Record an intent".

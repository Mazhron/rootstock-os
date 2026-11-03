---
name: brief
description: Compose and dispatch a sub-agent (employee) brief that follows the delegation laws - stamped, self-contained, budget-capped, diff-only reporting - then verify cheap and ledger the outcome. Use whenever delegating a task.
---

# /brief - delegate a task by the laws

PURPOSE: Compose and dispatch a sub-agent (employee) brief that follows the
  delegation laws, stamped, self-contained, budget-capped, diff-only
  reporting, then verify cheap and ledger the outcome.
INTENT: So delegated work stays safe and reviewable: the employee starts
  self-contained, is capped at about 30 tool calls, never deletes, respects
  the fan-out limits, and the manager logs an intent claim and ledgers the
  outcome afterward. Since the /brief diet (Mazhron 2026-11-03) the fixed
  rules live in EMPLOYEE_RULES.md beside this file and the brief carries
  the task plus a four-line pointer, never the rules rewritten.

Read SUBAGENTS.md RULES + ASSIGNMENTS first (never the ledger unless
appending/auditing). Then compose the brief with ALL of:

1. STAMP: task id, date, workstation, assigned model (from the assignments
   table; escalate a task type's model when its correction rate passes ~25%).
   THE EMPLOYEE MODEL RULE (kit v1.40): the Agent call's `model` field is
   set explicitly, always - a call without one inherits the manager's own
   model, and the manager's tier is never an employee; the brief guard
   refuses a work dispatch whose model is missing or names that tier.
2. SELF-CONTAINED CONTEXT: everything the employee needs inline or by exact
   file/section pointer - an employee starts with an EMPTY context and must
   not wander the repo discovering things. A task type with a standing
   contract (the mockup: mock/BRIEF.md) is pointed at by path, never pasted;
   the brief then holds only the task, the data each verb must change, the
   probe lines and the pointers.
3. THE RULES BLOCK (the diet, 2026-11-03): four lines, verbatim, the root
   filled in, that point at the fixed text and keep the tokens the brief
   guard checks for (STAMP:, TOOLS:, WORKFLOW:, INTENT:, "STOP and report",
   "THE PRESERVATION LAW"); nothing from EMPLOYEE_RULES.md is restated:
   ```
   RULES (binding; read this file first, by path): <root>\.claude\skills\brief\EMPLOYEE_RULES.md
   - THE PRESERVATION LAW holds (no deletion code, no delete command); past ~30 tool calls or the same step failed twice, STOP and report what you have.
   - Independent reads in ONE turn; fix what is wrong inside your files and say so, report what is outside them; report the diff, never whole files.
   - End your report with the four footer lines of that file: STAMP: ... / TOOLS: ... / WORKFLOW: matched <entry named below> | GAP: ... | n/a / INTENT: <the task in your own words>.
   ```
   A task-specific exception to a law (a mockup page's splice is its Delete
   verb) is one added clause, not a rewrite of the law.
4. THE WORKFLOW AND INTENT POINTERS (rules 11 and 14): for a repeatable
   multi-step task, NAME the WORKFLOWS.md entry and paste its STEPS (only
   the steps, never the whole entry); if the task rests on a ruling whose
   why matters, `Grep "^## " INTENT.md` and PASTE that section (never "see
   INTENT.md"). "Never touch" names the files other employees own.
5. THE FAN-OUT CHECK (rule 12): before dispatch, count. A handful of
   employees in this batch (4 is the habit), no employee that spawns
   employees, no Workflow tool unless Mazhron asked for it. Needs dozens?
   That is a design problem - split, script, or ask - not a bigger
   fan-out. If the fan-out guard refuses a spawn (8 in a minute, 25 in
   ten, or runaway token velocity - the owner's numbers via /runaway),
   stop and report; never resume the same loop and never raise a limit
   to get past it.

AFTER THE EMPLOYEE RETURNS
- Log the INTENT line as a claim (`python tools/intent_log.py --claim
  --actor <model> --task "..." --mine "<the line>"`) and resolve it once
  verified with ALL THREE flags (`python tools/intent_log.py --resolve <id>
  --theirs "<the task as you meant it, 15 words at most>" --verdict
  SAME|SIMILAR|DIFFERENT --source inferred|stated`; the tool refuses a
  resolve missing any one, 2026-10-13); a correction goes through /correct
  (tools/correction_log.py, actor = the model) which resolves the claim
  DIFFERENT itself.
- Verify cheap, in order: tests/probes first, spot-read the diff second,
  full read only on smell.
- Watch for fabrication (it has happened): claims must match the diff.
- LEDGER the outcome in SUBAGENTS.md (append-only, with correction tally):
  the line's free text is 60 words at most; the diff and the ledger of
  tools say the rest.
- A reported WORKFLOW GAP gets captured in the same batch: write the
  WORKFLOWS.md entry, or brief a haiku with the employee's report + the
  entry template (WORKFLOW_METHOD.md).

The manager keeps: design, laws, architecture, verification, pushes.

Search keys: delegation, employee brief, sub-agent, stamp, fabrication check,
brief diet, rules block.
See also: EMPLOYEE_RULES.md (beside this file: the fixed text); SUBAGENTS.md
(this project's table); SUBAGENT_METHOD.md (portable); mock/BRIEF.md.

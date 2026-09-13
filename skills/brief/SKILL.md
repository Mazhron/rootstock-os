---
name: brief
description: Compose and dispatch a sub-agent (employee) brief that follows the delegation laws - stamped, self-contained, budget-capped, diff-only reporting - then verify cheap and ledger the outcome. Use whenever delegating a task.
---

# /brief - delegate a task by the laws

Read SUBAGENTS.md RULES + ASSIGNMENTS first (never the ledger unless
appending/auditing). Then compose the brief with ALL of:

1. STAMP: task id, date, workstation, assigned model (from the assignments
   table; escalate a task type's model when its correction rate passes ~25%).
2. SELF-CONTAINED CONTEXT: everything the employee needs inline or by exact
   file/section pointer - an employee starts with an EMPTY context and must
   not wander the repo discovering things.
3. TOKEN BUDGET LINE, verbatim: "If you exceed ~30 tool calls or fail the
   same step twice, STOP and report what you have."
4. REPORT FORMAT: write files directly; report `git diff --stat` + changed
   hunks + a short summary. NEVER paste whole file bodies back.
5. THE WORKFLOW LINE (rule 11): for a repeatable multi-step task, NAME the
   WORKFLOWS.md entry and paste its STEPS into the brief; the employee's
   stamp ends with "WORKFLOW: matched <entry> | GAP: <uncovered process> |
   n/a".
6. THE FAN-OUT CHECK (rule 12): before dispatch, count. A handful of
   employees in this batch (4 is the habit), no employee that spawns
   employees, no Workflow tool unless Mazhron asked for it. Needs dozens?
   That is a design problem - split, script, or ask - not a bigger
   fan-out. If the fan-out guard refuses a spawn (8 in a minute, 25 in
   ten, or runaway token velocity - the owner's numbers via /runaway),
   stop and report; never resume the same loop and never raise a limit
   to get past it.

7. THE PRESERVATION LINE (rule 13, 2026-09-10), verbatim in every brief:
   "THE PRESERVATION LAW: your work contains NO deletion code and runs no
   delete command; move or retire instead (tools/retire.py,
   tools/cold_shelf.py); a harness hook refuses writes containing
   deletion calls. If the task seems to need a deletion, STOP and report."
8. THE INTENT LINE (rule 14, 2026-09-13): if the task rests on a ruling
   whose why matters, `Grep "^## " INTENT.md` and PASTE the relevant
   section into the brief (never "see INTENT.md"). Every brief ends by
   requiring "INTENT: <one line: what you understood the task to be, in
   your own words>" after the STAMP/TOOLS/WORKFLOW lines.

AFTER THE EMPLOYEE RETURNS
- Log the INTENT line as a claim (`python tools/intent_log.py --claim
  --actor <model> --task "..." --mine "<the line>"`) and resolve it once
  verified (SAME / SIMILAR / DIFFERENT, source inferred or stated); a
  correction goes through /correct (tools/correction_log.py, actor = the
  model) which resolves the claim DIFFERENT itself.
- Verify cheap, in order: tests/probes first, spot-read the diff second,
  full read only on smell.
- Watch for fabrication (it has happened): claims must match the diff.
- LEDGER the outcome in SUBAGENTS.md (append-only, with correction tally).
- A reported WORKFLOW GAP gets captured in the same batch: write the
  WORKFLOWS.md entry, or brief a haiku with the employee's report + the
  entry template (WORKFLOW_METHOD.md).

The manager keeps: design, laws, architecture, verification, pushes.

Search keys: delegation, employee brief, sub-agent, stamp, fabrication check.
See also: SUBAGENTS.md (this project's table); SUBAGENT_METHOD.md (portable).

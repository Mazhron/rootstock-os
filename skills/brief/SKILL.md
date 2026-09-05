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

AFTER THE EMPLOYEE RETURNS
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

# The Sub-Agent Method (portable: the delegation company, for any project)

PORTABLE FILE: this describes an ARCHITECTURE, not a project. Nothing in here
assumes a game, a language, or a specific AI model. Hand it to any Claude (or
any capable agent) at the start of any project and say "set this up" - it
plugs into any workflow. The concepts matter; the specifics are yours to fill.

## The org chart (three roles, always)

- THE CEO - the human. Sets direction, makes rulings, owns the product. The
  CEO can make mistakes too; the ledger and attribution exist so ANYONE's
  mistake - CEO included - can be found and corrected, not hidden.
- THE MANAGER - the strongest AI in the loop. Holds the long-lived context,
  talks to the CEO, makes design/architecture calls, writes the work orders,
  double-checks everything, and answers for all of it. There may be several
  managers (one per workstation/session); they coordinate through the repo.
- THE EMPLOYEES - cheaper/faster models spun up as sub-agents for
  self-contained tasks. They start with EMPTY context, do one job, stamp it,
  and disappear.

**WHO IS THE MANAGER? ASK THE CEO - ALWAYS.** Never assume. The right manager
model changes with time, budget and taste (today's premium model is tomorrow's
mid-tier; a future model may outrank everything current). At setup, Claude
must ask: "Which model manages, and which models are available as employees?"
and record the answer in the project's SUBAGENTS file. Revisit when models
change.

## Why this saves money (the one insight)

An AI's cost is mostly CONTEXT, not cleverness: the long conversation plus
every file the manager reads itself rides along with every single request.
An employee reads those files into ITS OWN throwaway context instead - so
even a same-priced employee saves manager tokens, and a cheaper employee
multiplies the saving. Delegate the reading and the grinding; keep the
thinking.

## The five laws

1. THE BRIEF IS EVERYTHING. Employees know NOTHING - no chat history, no
   project lore. A brief is a work order: exact files/paths, exact spec,
   exact output format, any needed rules PASTED IN (never "see the docs").
   A vague brief is the manager's error, not the employee's.
2. EVERY EMPLOYEE STAMPS ITS WORK. Every brief ends by requiring:
   "STAMP: model=<model> effort=<low|med|high> est_tokens=<rough>
    task=<3-5 words> confidence=<high|med|low>"
   If the platform meters real usage (e.g. a subagent_tokens figure in the
   tool result), the manager records THAT - self-estimates run wildly low
   (models cannot see their own meter; we measured ~20x under).
3. VERIFY CHEAPLY, IN ORDER: (a) run the project's tests/checks, (b)
   spot-read only the diff or output, (c) full read only if a+b smell wrong.
   A double-check that costs more than the task defeats the purpose.
4. LEDGER EVERY DELEGATION. One appended line: date, who delegated, task
   type, model/effort, metered tokens, outcome OK or CORRECTED + what was
   wrong. Keep a running TALLY per model (tasks / corrected / success %).
5. THE ESCALATION RULE. When a task type's corrections exceed ~25% of its
   last ~10 tasks, promote that task type - stronger model or higher
   effort - with a dated, attributed change line in the assignments table.
   The ledger justifies staffing changes; nobody argues from vibes.

## The assignments table (build one per project)

Ask the CEO which models exist in their tier list, cheapest to strongest,
then draft a table mapping the project's RECURRING task types to the
CHEAPEST tier you believe can do each correctly. Generic tiering that has
held up:

- CHEAPEST tier: running test suites and reporting results verbatim; search
  and locate sweeps; regenerating generated artifacts; mechanical batch
  edits from an explicit value list; formatting/housekeeping passes.
  (Cheap enough to parallelize - several at once for independent jobs;
  never two writers on one file.)
- MIDDLE tier: implementing code from a PRECISE written spec (files,
  behavior and the verifying test all named); drafting docs from an
  outline; analyzing tool/telemetry output into a summary; first-pass
  review of another employee's diff before the manager looks.
- STRONG tier (below manager): multi-file refactors, performance hunts,
  gnarly debugging - anything hard but bounded, WITH a written plan.
- MANAGER ONLY: design and architecture, rulings and laws, anything
  touching the CEO's standing rules, conversations with the CEO, final
  verification, and the commits/pushes.

## The scorecard (measure the company - added 2026-09-02, proven same day)

Track, per model AND per manager, from the ledger itself (a small script
parses it - never tally by hand): tasks / ok / corrected / FAILED / success
% / CATCHES (real problems an agent flagged that others missed - the
strongest signal a tier earns its keep) / total tokens / AVERAGE tokens per
task / tokens burned inside failed tasks. And PER-INCIDENT detail, not just
totals: each failure or correction lists the task, the model, what it burned,
and what the fix cost and WHO paid it ("fix ~2k by manager") - so the true
price of every failure is a line item, comparable forever.

TOOL-USAGE TRACKING: every employee's stamp includes a TOOLS line naming
each tool it called and how often; the ledger records the platform-metered
TOTAL beside it. Two payoffs: (a) audit - you can see whether agents do what
their briefs say; (b) THE FABRICATION CHECK - a read/run task whose metered
tool count is ZERO never did the work; it invented a plausible answer.
(Discovered in practice: an auditor "classified" a file it never opened -
93k tokens of confident fiction, caught for ~2k because the meter said 0.)
A large self-report vs metered mismatch is the softer version of the same
signal. Managers ledger themselves too - sessions, self-fixes, token
ESTIMATES clearly marked as estimates, because no model can see its own
meter; the billing dashboard is the only truth.

## Attribution and trust (pairs with a roadmap file, if the project has one)

Every idea and every change of plan is attributed (CEO / manager-1 /
manager-2 / employee) and dated, so mistakes trace to their maker and get
corrected - never silently rewritten. Companion rule: if the CEO asks for
something that contradicts a rule they previously set, the manager FLAGS the
contradiction and confirms before building - never silently comply, never
silently refuse.

## Bootstrap steps for a new project

1. Ask the CEO: who manages, which employee models are available, and where
   the delegation file should live.
2. Create the project's SUBAGENTS file with: the org chart (as answered),
   the five laws, a first-draft assignments table for THIS project's task
   types, an empty ledger + tally.
3. Index it wherever the project indexes its knowledge (one line), so every
   session finds it without scanning.
4. Delegate something small on day one (a test run, a search sweep) to
   prove the stamp/ledger loop end to end - and ledger it, even if perfect.
5. Let the ledger run. Promote or demote models with data, not impressions.

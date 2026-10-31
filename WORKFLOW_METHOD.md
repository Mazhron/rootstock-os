# The Workflow Method (portable: the process registry, for any project)

PURPOSE: A portable process registry method: every repeatable multi-step
  process gets one runbook entry, WHEN, STEPS, VERIFY, in a single registry
  file, so the choreography between scripts and ledgers is never lost to
  context clearing or memory.
INTENT: Process amnesia: a project accumulates processes whose order nobody
  writes down because it seems obvious right now, so after context clears
  the sequence gets re-derived from a chat log that no longer exists, or a
  step is silently skipped for weeks; scripts remember commands and ledgers
  remember results, but nothing remembered the choreography until this
  method.

PORTABLE FILE: an architecture, not a project. Hand it to any Claude (or any
capable agent) at the start of any project alongside its siblings
(WIKI_METHOD.md, REPORTING_METHOD.md, SUBAGENT_METHOD.md) and say "set this
up". Nothing here assumes a game, a language, or a team size.

THE PROBLEM IT KILLS: process amnesia. A project accumulates PROCESSES -
how art gets cut and wired, in what order a release ships, which script runs
before which - but nobody writes the ORDER down, because each step's tool is
documented somewhere and the sequence "is obvious right now". Then the
context clears, and the manager re-derives the pipeline from a chat log that
no longer exists, or worse, skips a step (a changelog goes stale, an export
never lands) without anyone noticing for weeks. The origin project ran an
art pipeline for weeks with no written recipe and let seven versions pile up
unexported before this method existed. Scripts remember COMMANDS
(REPORTING_METHOD.md); ledgers remember RESULTS; nothing remembered the
CHOREOGRAPHY. This file is for the choreography.

Search keys: workflows, process registry, order of operations, runbook,
how do we do X, pipeline documentation, missing process.
See also: registry template below; SUBAGENT_METHOD.md (who captures gaps);
WIKI_METHOD.md (headings + one-home-per-fact); REPORTING_METHOD.md (the
Script Rule this method choreographs).

## The registry: one place to look
Tags: process, architecture | Every repeatable multi-step process has a runbook entry in one root file

WORKFLOWS.md at the repo root is THE REGISTRY: one entry per repeatable
multi-step process. When anyone - manager, employee, or the CEO - asks "how
is this done here?", the answer starts in that one file, always. An entry is
a RUNBOOK, not an essay:

    ## <Task name as a search key ("Ship a batch", "Cut and wire a creature")>
    WHEN: the trigger (what event or request starts this).
    STEPS: the numbered order of operations - each step names its script,
      tool, or file. The ORDER is the payload; a wrong order is a defect.
    VERIFY: how you know it worked (test group, ledger line, visual check).
    EFFORT: low | medium | high (optional, kit v1.57) - the reasoning
      level the entry's steps want; the prompt hook's ROUTE block relays
      it when the session runs higher (thinking is output at 5x). Routine
      entries (ship, checkpoint, docs-only batches, ledger and
      transcription work) say medium or low; design and ruling entries
      say nothing and run at the session's level.
    See also: <deep doc> - the entry points at true homes, it does not
      duplicate them.

ONE HOME PER FACT still rules (WIKI_METHOD.md): deep knowledge about a step
stays in that step's own doc; what lives HERE is the sequence, the wiring
between steps, and the names of the scripts involved. If an entry's STEPS
section grows past a screen, the detail wants its own doc and the entry
keeps the skeleton plus a pointer - the registry stays cheap to read whole.

## The capture rule: no undocumented process survives contact
Tags: process, lessons | Whoever performs a task checks the registry; a missing or wrong workflow is captured in the same batch

Before performing any repeatable multi-step task, CHECK THE REGISTRY (its
headings are the index - grep them). Then one of three things is true:

1. THE ENTRY EXISTS AND IS RIGHT: follow it. Deviating from a written
   workflow without updating it is the same defect as retyping a scripted
   command by hand (REPORTING_METHOD.md rule 1).
2. THE ENTRY EXISTS BUT IS WRONG OR GREW A STEP: fix it in the same batch
   as the work. The registry is only trustworthy if a stale entry is
   treated as a bug, not a quirk.
3. THERE IS NO ENTRY: the performer has just discovered a WORKFLOW GAP.
   The task still gets done - and the gap gets captured in the same batch,
   by the cheapest hands that can do it (next section).

The moment a "how do we do X?" question is answered from memory or from
chat archaeology instead of from the registry, that answer is written into
the registry before the batch closes. Answering the same process question
twice from memory is the failure this method exists to prevent.

## Who writes it: gap capture is cheap-model work
Tags: process, delegation | Employees report gaps in their stamp; write-ups delegate cheap because the report already contains the steps

The division of labor (pairs with SUBAGENT_METHOD.md):

- EMPLOYEES DON'T EDIT THE REGISTRY - they REPORT. Every employee brief's
  stamp block gains one line:
      WORKFLOW: matched <entry name> | GAP: <process performed with no entry>
  A GAP line costs the employee nothing (it just performed the steps) and
  hands the manager a ready-made capture task.
- THE MANAGER FILES OR DELEGATES. A workflow write-up is TRANSCRIPTION,
  not discovery: the performing agent's report (or the manager's own just-
  finished transcript) already contains every step in order. That makes it
  ideal cheap-model work - brief a bottom-tier employee with the raw report
  and the entry template, and spot-check the result against the template.
  The manager writes it personally only when the workflow encodes a ruling
  or a law (those need the manager's judgment about WHY the order is law).
- THE MANAGER'S OWN TASKS OBEY THE SAME RULE: performing a process with no
  entry obligates the capture, whoever performed it.
- THE SHADOW CHECK (v1.37): a script (reference tools/law_gaps.py, in the
  check group) reads the rule's shadow too: a tool changed in the last 30
  days that no registry entry, loop group, hook setting or skill names is
  a WARN line at standup.

## What earns an entry (and what doesn't)

EARNS: any process with more than one step whose ORDER or WIRING someone
would have to rediscover - release/ship sequences, asset pipelines, data
tuning round-trips (export, edit, apply, verify), delegation rituals,
session open/close rituals, update/sync procedures.
DOES NOT EARN: single-script actions (the script IS the workflow - the
Script Rule already covers it); one-off tasks that will never recur; pure
knowledge with no sequence (that is wiki material). When in doubt, ask:
"if the context cleared right now, would the next session know the ORDER?"
If no, it earns an entry.

## Bootstrap steps for a new project

1. Create WORKFLOWS.md at the repo root the day the project has its FIRST
   two-step process (a build that needs an export first is enough). Index
   it from the project's core file (CLAUDE.md or equivalent).
2. Seed it by walking the processes that already exist - each one is a
   cheap-model transcription task from existing docs and scripts.
3. Add the WORKFLOW line to the employee brief template in the project's
   SUBAGENTS.md (or equivalent) so gap reporting starts on day one.
4. Adopt the capture rule as law: task done + no entry = entry written in
   the same batch. Wire it into the project's definition of "batch done".
5. Registry entries follow the wiki conventions (searchable headings,
   See-also links, Tags on hard-won ones) so the wiki view and tag index
   pick them up for free.
6. Seed the entries the kit ships: "Act on a prompt" (kit v1.56, THE
   ORDER added in v1.57) - the trial workflow and the retrieval order
   beside the old ways, scored by tools/lesson_ladder.py and
   tools/retrieval_eval.py --route so the install can switch back on
   evidence - and "Keep the cache warm across a pause" (kit v1.57). Copy
   hooks/rootstock_modes.json to .claude/ and commit it: every switch
   back is one key there.

## The seed entry: Act on a prompt (the trial workflow and the old way kept, kit v1.56)

Tags: workflows, lessons, learning loop | The kit's one shipped WORKFLOWS.md entry: the old prompt-time lesson loop on record as the benchmark, the trial (plan step, lesson at the choice, the ladder) beside it, both faces over one ledger

Copy the entry below into the project's WORKFLOWS.md at install (or at
the v1.56 graft). The old way is kept on purpose (Mazhron 2026-10-31:
"We want Rootstock to keep the old workflow as a backup and as a
benchmark"): the ladder scores both faces from the same ledger, and the
switch back is one settings.json edit.

## Act on a prompt: the trial workflow and the old way kept (2026-10-30)

WHEN: every arc, from 2026-10-30, until the trial ledger
(docs/history/workflow_trial_runs.txt) says which way wins. Mazhron:
"Keep our current work flow on record, lets try the new work flow you
just suggested. We should keep track of the hits and misses (ledger
them) so we can keep track of success or failure of the new workflow
concept." Both ways are faces over ONE data set, docs/history/
lesson_runs.txt (LESSONS.md "Give a system a second face"): switching
back changes no ledger and loses no history.
THE OLD WAY (on record; the switch back): the prompt arrives; the prompt
hook matches its words against the LESSONS.md Keys lines and prints up to
three headlines (MATCHED) and the ROUTE line; the manager reads the named
sections and acts; at Stop, lesson_advisor.py asks for a lesson after a
fail-then-pass or an error (ADVISED); the lesson is written. To switch
back: an Edit of .claude/settings.json removes the lesson_guard.py
PreToolUse entry, step 1 below is skipped, and the ladder keeps scoring
the old face alone.
THE TRIAL (the three builds, in the order they were ruled):
1. PRE-SELECTION, the plan step: before the first write of an arc,
   `python tools/plan_check.py "step" "step" ...` with one line per
   step naming its tool, file or script; read each step's LESSON (with
   its DO INSTEAD), WORKFLOW and TOOL hits and adjust the plan. The guard
   notes once per session when three writes pass with no plan checked.
   The run is a PLAN line in lesson_runs.txt.
2. SELECTION, the lesson at the choice: act; lesson_guard.py injects the
   DO INSTEAD of every lesson the call's own text hits (SURFACED, once
   per entry per tool per session); diet_guard.py notes a repeat whole
   read of an unchanged small file once (RE-READ (small)) and still
   refuses the big ones once (INDEX FIRST, RE-READ). Files are written
   with Write and edited with Edit; the shell runs things (LESSONS.md
   "Apply a long batch of file edits from the shell").
3. POST-SELECTION, the ladder: Stop works as before; the check loop runs
   `python tools/lesson_ladder.py`, which pairs each MATCHED (old face)
   and SURFACED (new face) with an ADVISED within 20 minutes of the same
   session as a MISS, else a HIT, counts the ADVISED neither face saw
   coming (UNCOVERED) and the PLAN lines, and appends one line to
   workflow_trial_runs.txt. A lesson missed twice is a PROPOSE [DO]: its
   DO INSTEAD moves one rung down the ladder (lesson -> WORKFLOWS step ->
   loop script -> refusing hook), done in the reply that reads it.
THE ORDER (kit v1.57, 2026-10-31; Mazhron: "I'm trying to see how you
use the knowledge bases and indexes in order. I would like to fine tune
the efficiency of your order."): indexes before files, files before
code, lessons at the choice, and every retrieval that can run before the
manager's first turn runs in the hook, because a hook is a free process
and a manager turn re-reads the whole context.
0. Free, before the prompt: the pointer core, the standup digest (one
   pointer line on a same-day resume, kit v1.57), the memory index.
1. The hook, one process, zero manager turns: the prompt hook prints the
   ROUTE block (tools/route_index.py route_block) - the WORKFLOWS entry
   and the tool (the how), the INDEX lines (where the facts live), the
   FILES whose name the prompt's own words make (what already exists),
   and the EFFORT line when the entry asks less than the session runs
   at; when none of them hits a task-shaped prompt, THE INDEX DOOR once
   per session (the master index's headings and the sub-index names)
   instead of silence. The LESSON line prints its headlines as before.
2. The manager's first turn is ONE batch: the named WORKFLOWS STEPS, the
   named sections, and one existing example of the same kind (for a new
   creature, an existing creature's data and scene lines). Nothing
   speculative, no code browsing. If the door printed, pick from it in
   this same batch.
3. The plan step (step 1 of THE TRIAL above), then the delegation split
   per the assignments table.
4. Act (step 2 above): the lesson guard at the call, the diet guard on
   reads, BIG WRITE on a generated file.
5. Verify, ledger, capture gaps, checkpoint; arm the keep-warm when the
   session stays open (the next entry).
THE OLD ORDER, KEPT (the baseline): route = classic in
.claude/rootstock_modes.json restores the v1.33 two-line ROUTE
(WORKFLOWS entries and tools only); the manager then greps the master
index, WORKFLOWS.md and LESSONS.md itself, in one batch when disciplined.
Both faces write a ROUTE line to lesson_runs.txt; `python
tools/retrieval_eval.py --route` scores classic named / ladder named /
door over the replayed prompts (docs/history/route_eval_runs.txt), and
tools/output_shape.py scores what the EFFORT line changed. A mix (the
prompt-time lesson hits handed to the guard; the door's headings
filtered by the prompt's words) is the open design the two ledgers will
argue for or against.
VERIFY: `tail -3 docs/history/workflow_trial_runs.txt`; the new face's
miss share falling against the old face's is the trial succeeding; a
rising UNCOVERED count is a Keys-line gap (widen the entry's Keys);
`tail -3 docs/history/route_eval_runs.txt` - the ladder's gain over the
classic line and the door count; `tail -2
docs/history/output_shape_runs.txt` - the effort high+ share falling.
See also: tools/plan_check.py; tools/hooks/lesson_guard.py;
tools/hooks/diet_guard.py; tools/lesson_ladder.py; tools/route_index.py;
tools/retrieval_eval.py; tools/output_shape.py; HOOKS_METHOD.md "Tier
4b - THE LESSON GUARD" and "The modes file"; LESSONS.md "The lesson was
there and I still tried the thing it says not to" and "The retrieval
order was improvised per prompt".

## Keep the cache warm across a pause (the keep-warm ping, kit v1.57)

WHEN: the end of every checkpoint reply that leaves the session open (not
a /clear), and any reply that leaves uncommitted context open for an hour
or more. Measured (the origin, 2026-09-29, `tools/keepwarm.py --report`):
on Fable 5.1 at 0.025x cache reads, nine pings cost 36% of one 1h-TTL
rewrite, and pinging every 55 minutes beats the rewrite for any pause
under ~23 hours; on a 0.1x model the break-even is nine pings (~8
hours). The origin's October ledger had six TTL-gap misses at ~90k-230k
weighted each and no pings, two of them after checkpoints.
THE OLD WHEN LINE, KEPT (2026-09-29): "a session with UNCOMMITTED
context that will be left open for an hour or more ... NEVER after a
checkpoint: a /clear then costs only the standup digest". It was priced
at 0.1x reads; the 0.025x verdict and the misses after checkpoints
reversed it (UPGRADES.md v1.57, FLAGGED). To go back: drop step 6 from
the checkpoint skill and arm only mid-arc.
EFFORT: low
STEPS:
1. Arm, in the reply that leaves the session open: ScheduleWakeup with
   delaySeconds 3300, noop true, and this prompt: "[keep-warm ping,
   WORKFLOWS "Keep the cache warm across a pause"] Not the CEO. No
   project work; ignore any hook line. ONE Bash call: `python
   tools/keepwarm.py --ping --trial <id> --cap <N>` (the id fixed at
   arming; N = 25 on Fable, 9 on any other model: the break-even). If it
   prints "ping N of <cap>", reply with that line exactly and call
   ScheduleWakeup again (3300, noop true, this same prompt). If it prints
   "stopped after <cap> pings", run `python tools/keepwarm.py --report
   --record`, reply with the report under one line of reading (keep,
   retune, retire), and call ScheduleWakeup with stop true."
2. The cap stops the loop itself; a real turn after it re-arms by step 1
   if the pause continues. The prompt hook prints nothing on a ping (THE
   KEEP-WARM EXCLUSION, tools/hooks/prompt_gauge.py); any hook line on a
   ping turn waits for the next real turn.
3. Stop early: ScheduleWakeup with stop true, or /clear (the loop is
   session-only; never CronCreate, which survives a /clear).
VERIFY: `python tools/keepwarm.py --report` (the metrics group): every
ping a hit, gaps ~55 m, the cumulative cost under one rewrite; the 1h-12h
buckets of cache_misses.txt shrinking. If the pings cost more than the
misses they replace, retire the step and say so in the entry.
See also: tools/keepwarm.py; docs/history/keepwarm_runs.txt;
docs/history/cache_misses.txt; tools/usage_report.py (the pricing law);
tools/hooks/prompt_gauge.py (the exclusion); .claude/skills/checkpoint
(step 6, ARM THE KEEP-WARM).

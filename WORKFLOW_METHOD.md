# The Workflow Method (portable: the process registry, for any project)

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

# READ ME FIRST - the kit's front door (an install runbook, read once)

PURPOSE: The kit's front door: walks a receiving Claude through the install
  in order (ask the CEO first, then the wiki, reporting and session
  rituals, the delegation company, the skills and hooks, the companions,
  the optional boards) by POINTING at each method file's bootstrap
  section, so the operating system lands the same way every time.
INTENT: the methods encode lessons already paid for, so a receiving Claude
  installs them in order instead of improvising a different architecture.
  This file is NOT a CLAUDE.md and never loads per session: it is read
  once, at install, then the project's own lean CLAUDE.md takes over
  (WIKI_METHOD.md "The hot core and the sub-indexes" says how big that is).

Search keys: bootstrap, new project setup, kit install, read me first,
  front door, install order.

You have been handed ROOTSTOCK, a portable operating system for running a
software project with Claude, distilled from a shipped project (Everwood,
2026). Four pillars: a token-cheap KNOWLEDGE WIKI, a scripted REPORTING
discipline, a DELEGATION company of sub-agents, and SESSION RITUALS
packaged as skills; hooks make the laws mechanical. Install it in order,
asking the STEP 0 questions first. Do not improvise a different
architecture.

Roles: the person who gave you this kit is the CEO; you are the MANAGER;
sub-agents you spawn are EMPLOYEES. The full kit assumes git, Python 3 and
Claude Code; without one of them the install is PARTIAL and every skip is
recorded in the install stamp (see MISSING PREREQUISITES).

## STEP 0 - ask the CEO before building anything

1. Project name, language/engine, repo location (git init if needed).
2. WHO MANAGES: which Claude model is the manager, which are employees
   (SUBAGENT_METHOD.md forbids assuming).
3. One workstation or several (ledgers and day files stamp per machine).
4. Which domain files apply: GODOT_FIELD_NOTES.md (Godot),
   CLICKER_DESIGN_NOTES.md (idle/clicker); otherwise keep them unindexed
   in reference/ as examples of what such files become.
5. UPDATE POLICY for future kit concepts: ask / auto / relevant / never
   (default ask; lives in the install stamp; the CEO changes it by saying so).

THE BROWNFIELD RULE (an existing project): inventory first, ADOPT what
already plays each role under its own name, PROPOSE the install as a plan,
and touch no existing file before the CEO's explicit yes. Production-
sensitive files are untouchable without a named go-ahead.

MISSING PREREQUISITES: no git means skip the push/checkpoint-push steps and
the update check; not Claude Code means skip the skills shelf, the
transcript-mined last exchange and the usage sheet (the checkpoint writes
the exchange into the day file by hand). Record each skip in the stamp
("| no-git | no-skills").

## STEP 1 - the wiki (WIKI_METHOD.md, "Bootstrapping a NEW project")

Everything else is indexed into it, so it comes first: the project's
CLAUDE.md as THE POINTER CORE (the project in a paragraph, how to read,
how to verify, the laws no hook enforces, ONE pointer to the master
index; under Anthropic's 200-line target, the lint fails past 200 lines
or 2,000 tokens and warns past 1,000: WIKI_METHOD.md "The hot core and
the sub-indexes"; the origin lands ~900 tokens), docs/index/
MASTER_INDEX.md (the one door: every topic file, root file, sub-index and
rule, one line each), .claude/rules/ path-scoped rules for what only
matters while one part of the codebase is open (copy rules/wiki.md from
the kit; write the project's own code and text rules with a `paths:`
field), docs/systems/ topic files, docs/index/ sub-indexes for what falls
out of the core, the lint (reference tools/check_claude_md.py) and the
mover (reference tools/core_diet.py) in the check group. Copy the portable
MDs to the repo root and index each with one line in the master index.
Create WORKFLOWS.md
(WORKFLOW_METHOD.md) the day the first two-step process exists. Stamp the
install: "Rootstock vX.Y installed <date> | updates: <policy>" in the
core's index (version: UPGRADES.md).

## STEP 2 - reporting + session rituals (REPORTING_METHOD.md, bootstrap)

docs/history/ + the runner; from "reference tools/" (they work; adapt
paths, do not rewrite): standup.py (the digest + THE LAST EXCHANGE mined
verbatim from the harness transcripts), checkpoint.py (the counter + the
protocol), the daily log (days/ + days_index.txt), usage_report.py (the
weighted sheet + THE DAILY LINE), rootstock_update_check.py wired into
standup, run_all.py (THE LOOP LAW: every habitual script is called by
it). Day one: a baseline run in a ledger. Then WORKSTATION.md from the
survey (WORKSTATION_METHOD.md; workstation_survey.py in the check group).

## STEP 3 - the delegation company (SUBAGENT_METHOD.md, bootstrap)

SUBAGENTS.md from the STEP 0 answers (org chart, the laws, a first
assignments table, an empty ledger); delegate something small the same
day to prove stamp -> brief -> verify -> ledger end to end; the stamp
carries the WORKFLOW line (WORKFLOW_METHOD.md) and the INTENT line
(INTENT_METHOD.md).

## STEP 4 - the skills shelf and the hooks (SKILLS.md, HOOKS_METHOD.md)

Copy skills/ to .claude/skills/ and SKILLS.md to the root; the nine
rituals call the tools from steps 1-3, so they go live last. THE SKILLS
RULE: a ritual born or amended updates its skill in the same batch.
Then the hooks: copy hooks/ to tools/hooks/, merge the settings template
into .claude/settings.json, fill the bash guard's PROJECT RULES from the
STEP 0 laws, run every --selftest, pipe-test one real call
(HOOKS_METHOD.md's tiers say what each guard refuses and why; only the
CEO edits safety wiring). Then the loops that measure the loop, each in
its method file: the learning loop (WIKI_METHOD.md), the intent loop
(INTENT_METHOD.md), the format law + the purpose audit (CONTRIBUTING.md),
the README gate (only if this project publishes a fact-derived README),
and the lesson loop (LESSONS.md at the root, hooks/lesson_advisor.py,
reference tools/lesson_log.py: the one right way is read before the
first try and a lesson is asked for the moment a turn shows trial and
error; hooks/README.txt has the steps).

## STEP 5 - optional boards (adopt when the CEO wants them)

A TOKEN_IDEAS.md savings board; a NEXT_STEPS.md roadmap with attribution
and a FUTURE_FEATURES.md pin board; a public CHANGELOG fed by readable
commit subjects.

## DEFINITION OF DONE

standup.py runs clean and prints the core's size; check_claude_md.py
passes (the core under 200 lines and inside its token budget, every rule
by path, the master index complete); the format lint passes and FLAGS.md
flags every kit thing;
SUBAGENTS.md has one real ledger line; the skills answer to their slash
commands; the first commit is in. From then on: every write grows the
wiki, every repeatable action becomes a script, every result lands in a
ledger, every batch ships, every arc checkpoints.

One law to carry verbatim (THE CONTRADICTION RULE): if the CEO asks for
something that contradicts a rule they previously set, FLAG it and get
explicit confirmation - never silently comply, never silently refuse.

## UPDATING AN EXISTING INSTALL

Never reinstall, never copy kit files over project files. Open UPGRADES.md
(the graft log), read the entries newer than the project's install stamp,
act per the CEO's update policy, graft each chosen CONCEPT onto the
project's own files in its own names, bump the stamp.

See also: UPGRADES.md (the graft protocol); CONTRIBUTING.md (the format
  law); WIKI_METHOD.md, REPORTING_METHOD.md, SUBAGENT_METHOD.md, SKILLS.md,
  HOOKS_METHOD.md, WORKFLOW_METHOD.md, WORKSTATION_METHOD.md,
  INTENT_METHOD.md, LESSONS.md (the files this door points at).

# WORKSTATION_METHOD.md - the machine inventory that installs itself (PORTABLE, part of the future-project kit)

Founded 2026-09-06 on Mazhron's ask: "we should have a 'new workstation'
document that lists our complete setup, all the installation packages,
software we installed (such as python), etc. so that any Claude can get
any workstation up to par ... so that any user could simply set up a new
workstation based on their current. Their Claude would add their setup to
the document." Everything else in the kit assumes the tools already run:
Python for the scripts and hooks, the engine for tests and builds, the
art programs for the pipeline. Nothing recorded WHAT those were. A second
machine, a reinstall, or a collaborator's laptop meant rediscovering the
setup from error messages. This file makes the setup a document that a
Claude can read and act on.

Search keys: workstation, new machine, setup, install, prerequisites,
inventory, survey, up to par, second workstation, onboarding.
See also: WIKI_METHOD.md (where the doc lives in the library),
REPORTING_METHOD.md (the survey is a scripted run with a ledger),
HOOKS_METHOD.md (the hooks are the first thing that breaks on a bare
machine), WORKFLOW_METHOD.md (the registry entry that runs the setup).

## THE WORKSTATION RULE
Tags: process, architecture | The machine inventory lives in a file; new machines install from it, and every gain is written back the same batch

1. THE DOCUMENT: the project keeps ONE workstation file (Everwood:
   WORKSTATION.md at repo root) with a requirement table - what is
   needed, WHY (which script or ritual depends on it), what the origin
   machine has (version + path), and how to install it - split into
   REQUIRED and OPTIONAL. Plus one section per known machine (its
   inventory and its deltas) and the on-disk layout the scripts assume.
2. THE WRITE-BACK: whenever a machine gains something a script, hook or
   ritual depends on - a package, a tool, an extension, a path, an env
   var - the manager records it in the document IN THE SAME BATCH, with
   its why. A dependency that lives only in a script's import line or a
   hardcoded path is a workstation bug.
3. THE SURVEY: a script (Everwood: tools/workstation_survey.py) mirrors
   the requirement table as a CHECKS list and prints HAVE / MISSING per
   line, exits non-zero when a required item is missing, and appends one
   summary line to a ledger (docs/history/workstation_runs.txt). "Up to
   par" is what the survey says, not what anyone remembers. It sits in
   the parent loop's check group so it runs with the other lints.
4. THE INSTALL: on a new machine, the receiving Claude reads the document
   and installs the REQUIRED table top to bottom (the scripting language
   first - hooks need it from the first session), then runs the survey
   until it says yes, then adds the machine's own section. Machine
   paths never get hardcoded singly: a candidates list + env override
   (the origin's run_tests.py / make_builds.py pattern) so both machines
   stay first-class.

## What the requirement table records (one row per need)

| column | meaning |
|---|---|
| need | the thing, with the name scripts call it by (`python`, `node`) |
| why | the script, hook, law or ritual that depends on it - the reason it is in the table at all |
| origin has | version + path on the machine that wrote the row |
| install | the exact install move (site, installer option, pip line, env var) |

Record the NON-needs too ("no gh CLI, pushes over HTTPS"; "no ffmpeg,
PIL does it") - a new Claude otherwise installs them defensively.

## Per-machine sections

Each known machine gets a section: its name as the project's ledgers
know it (WS1/WS2 in Everwood), the survey line that proved it up to par,
and its DELTAS from the origin (a portable install at a different path,
a different drive, a missing optional). Anything that does not travel
via git (per-machine art palettes, harness transcripts, local settings)
is named there so nobody looks for it on the other machine.

## The Claude-side settings belong in it too

The harness's own configuration is part of the setup: the user-level
settings (effort level etc.), the project-level settings that travel
with the repo (the hooks), what is per-machine and gitignored (hook
state), and where the harness keeps transcripts. A new machine that has
the code but not the harness setup is not up to par.

## BOOTSTRAP (new project)

1. Day one, right after the wiki: create WORKSTATION.md (or your name for
   it) with the REQUIRED table for what you already depend on - usually
   the scripting language, the engine/runtime, git, the editor + the
   Claude Code extension - and the OPTIONAL table for the art/design
   tools. One row per need, with its why. THE ASK: a receiving Claude
   surveys the CEO's CURRENT machine (versions, paths, extensions) and
   writes the first inventory section from what it finds, then asks the
   CEO what it could not see (Steam drives, cloud tools, accounts).
2. Copy the reference survey ("reference tools/workstation_survey.py")
   and rewrite its CHECKS table to match your rows; keep the ledger line.
   Wire it into the parent loop's check group.
3. Add the registry entry "Bring a new workstation up to par" (WHEN: a
   new or reinstalled machine; STEPS: install REQUIRED top to bottom,
   clone into the layout, survey until YES, add the machine section;
   VERIFY: the survey's ledger line).
4. Index the file in CLAUDE.md with one line; add the WRITE-BACK rule
   to the standing rules ("a new dependency goes into the workstation
   doc in the same batch").
5. First survey run = the origin machine's inventory section. From then
   on every new dependency writes itself back as part of normal work.

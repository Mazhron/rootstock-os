# Rootstock

### A Project Operating System for Claude

**Graft your next project onto proven roots.** Rootstock is a portable,
plug-and-play operating system for running a software project with Claude:
a knowledge wiki that keeps context cheap, a reporting discipline that
makes results permanent, a delegation company of sub-agents that does the
heavy reading for pennies, and session rituals that make clearing your
chat completely lossless.

Grown in [Everwood](https://github.com/Mazhron/Everwood), an idle/clicker
game built end to end with Claude, by **Mazhron (Travis Rhoda)**.

---

## The problem: context is the bill

An AI assistant's real cost is not the question you ask. It is the CONTEXT:
the whole conversation, plus every file the model has read, rides along
with EVERY subsequent request. A six-hour session answers its last question
at several times the price of its first one. Every file read wholesale is a
tax you keep paying for the rest of the session.

Everything in Rootstock is a variation on one insight:

> Keep the manager's context small, and let cheap, disposable contexts do
> the reading.

## The four pillars

### 1. The Knowledge Wiki (WIKI_METHOD.md)

Project knowledge lives in a web of small topic files, not in one giant
document and not in the chat. The core instruction file (CLAUDE.md) stays
lean: laws, process, and a one-line-per-file index. The conventions that
make it work:

- **Read cheap.** Grep a file's headings first (about 50 tokens), then read
  only the section you need. Never read a topic file whole.
- **Headings are search keys.** Every section is named for what a search
  would look for, never "Misc" or "More fixes".
- **Cross-references.** Sections end with "See also" lines pointing at
  related topics WITH their file, so a hop needs no search.
- **One home per fact.** Engine lessons, genre lessons, and project details
  each live in exactly one layer, so nothing is read twice.
- **Incremental growth.** Every file touched during normal work gains
  proper headings and links then and there. No stop-the-world passes.

A lint script guards the core's line budget and keeps the index honest.

The wiki's growth rule is deliberate: files and indexes are nearly free
(disk for you, section-reads for Claude), so the manager's instinct is FIT
the existing home, else FOUND a new topic file and index on the spot, with
scripts that auto-discover new files so growth needs no wiring. Rootstock
is an ever-expanding web by design: ten thousand small files and four
hundred indexes beat one bloated document that taxes every read. The lint
prints the file count; at round milestones the manager mentions it, purely
as good news.

### 2. The Reporting Discipline (REPORTING_METHOD.md)

Anything repeatable becomes a SCRIPT; every result lands in a LEDGER.

- **The Script Rule.** Tests, fixes, imports, exports, probes: scripted
  once, changed only to add or fix, never re-typed in chat.
- **Ledgers.** Every run appends one labeled line to a history file. You
  read the TAIL, never the whole file, and runs compare across versions
  without re-reading anything.
- **Trust the ledger.** A green test at an unchanged version is never
  re-run "for confidence". The runner warns if you try.

This is not just thrift. On its first day in Everwood, the discipline
caught three real bugs, because scripted runs with ledgered baselines make
regressions impossible to hand-wave.

### 3. The Delegation Company (SUBAGENT_METHOD.md)

Three roles, always: the human is the **CEO**, the Claude you talk to is
the **MANAGER**, and sub-agents are **EMPLOYEES** with fresh, empty,
disposable contexts.

- The manager never reads a big unfamiliar file inline (that plants it in
  the expensive context forever). An employee reads it in a throwaway
  context and returns a ten-line map.
- Every brief is STAMPED (task, date, model), SELF-CONTAINED, and carries a
  budget line: exceed ~30 tool calls or fail the same step twice, and the
  employee stops and reports instead of running up a bill.
- Employees write files directly and report the diff, never paste bodies.
- **The fabrication check.** Claims must match the diff. This is not
  hypothetical: the method exists because a delegated audit once returned a
  fabricated report, and the ledger caught it.
- **The scorecard.** An append-only performance ledger tracks every
  employee task with correction tallies. Models are promoted or demoted on
  data, not impressions. Failures are priced per incident.

The manager keeps design, laws, architecture, verification, and pushes.

### 4. Lossless Sessions (the rituals, packaged as skills)

The endgame: you can clear your chat at any checkpoint and lose NOTHING,
because context lives in files, not in the conversation.

- **The Daily Log.** Each work day gets a file: the CEO's asks, the
  completions, and a WHERE WE LEFT OFF section carrying both sides of the
  final exchange (your last prompt AND the manager's last response).
- **The Checkpoint Protocol.** A counter ticks after every task and warns
  when the session gets heavy. At an arc's end the manager pushes,
  refreshes the day file, and emits the marker: "CHECKPOINT - safe to
  /clear. Nothing in this chat exists only in this chat."
- **Standup.** Every fresh session opens with one script that prints the
  last exchange, the state, ledger tails, and the open roadmap. A cleared
  session re-arms in about 15-20k tokens instead of dragging hundreds of
  thousands.

Four rituals ship as Claude Code skills, invocable as slash commands:
`/standup`, `/checkpoint`, `/ship`, `/brief`.

## What it saves, concretely

| Habit it replaces | Rootstock way | The saving |
|---|---|---|
| Reading files wholesale | Grep headings, read one section | A 50k read becomes ~1-2k |
| Re-explaining project state each session | Standup digest from ledgers | 5-10x smaller session opens |
| Marathon sessions that get pricier every turn | Checkpoint + /clear, losslessly | Later turns cost a fraction |
| The manager reading big files | Employee distills in a throwaway context | ~50k permanent becomes ~1k |
| Re-running green tests "to be sure" | Trust the ledger (runner enforces it) | Whole probe runs, skipped |
| Runaway agent loops | Budget line in every brief | Partial report instead of a bill |

The unglamorous truth this kit encodes: there is no magic compression
trick. The savings come from structure, scripts, and discipline. (The kit's
origin project evaluated the viral "let the AI invent its own compressed
language" idea and declined it with receipts; prompts are under 1% of
session cost. Structure is where the money is.)

## Quick start

1. Give this repo's contents to Claude (Claude Code, any capable model).
2. Say: **read "0 - READ ME FIRST, CLAUDE.md" and install the kit.**
3. Answer its STEP 0 questions (project name, who manages, which employee
   models are available, how many workstations).
4. Claude builds the operating system in order: wiki, reporting, delegation,
   skills, and finishes with a definition of done you can verify.

That is the whole handoff. The front-door file exists precisely so that a
stranger's Claude needs no other instructions.

## What is in the box

| File | What it is |
|---|---|
| `0 - READ ME FIRST, CLAUDE.md` | The front door: install order, STEP 0 questions, definition of done |
| `WIKI_METHOD.md` | The knowledge wiki: token mechanics, conventions, bootstrap |
| `REPORTING_METHOD.md` | Scripts + ledgers: the three rules, runner spec, bootstrap |
| `SUBAGENT_METHOD.md` | The delegation company: org chart, five laws, scorecard, bootstrap |
| `SKILLS.md` | The skills shelf: what each ritual-skill does and the skills rule |
| `skills/` | The four skills, ready to drop into `.claude/skills/` |
| `reference tools/` | Working standup, checkpoint, and lint scripts to adapt, not rewrite |
| `GODOT_FIELD_NOTES.md` | Domain example: hard-won Godot engine lessons (skip if not Godot) |
| `CLICKER_DESIGN_NOTES.md` | Domain example: idle/clicker genre lessons (skip if not that genre) |

The two domain files double as templates for what YOUR project's
engine-notes and genre-notes files should grow into.

## Origin

Every rule in this kit was paid for in Everwood: the fabrication check
exists because a fabricated report happened; the budget line exists because
runaway loops happened; the keep-old-builds law exists because a deleted
zip cost a dev-log comparison. Nothing here is theoretical. The kit is
model-agnostic by design; in a new project, Claude is required to ASK who
manages rather than assume.

Built by **Mazhron (Travis Rhoda)** with Claude.
Watch the game it grew from: Everwood, on [YouTube @Mazhron](https://www.youtube.com/@Mazhron).
Play it before it launches: [Everwood on itch.io](https://mazhron.itch.io/everwood).

## License

MIT. Take it, graft it, grow something.

# SKILLS.md - the skills shelf (PORTABLE, part of the future-project kit)

Founded 2026-09-03 on Mazhron's ruling: rituals that live only as law text
get executed from memory; rituals that live as SKILLS get executed from the
script. A skill is a markdown instruction pack in `.claude/skills/<name>/
SKILL.md`; typing `/<name>` in Claude Code loads it and Claude follows it.
Skills cost nothing at rest - they load only when invoked or clearly needed.

Search keys: skills, slash commands, rituals, plug and play, new project.
See also: SUBAGENT_METHOD.md (delegation the /brief skill enforces),
REPORTING_METHOD.md (the ledgers /standup and /checkpoint read/write),
WIKI_METHOD.md (the conventions every skill assumes), CLAUDE.md (the laws
the skills operationalize).

## The shelf (what each skill does)

- **/standup** - session opener. Runs the standup digest and hands back the
  last exchange (user's prompt + manager's response, both sides, VERBATIM -
  exact words, never paraphrased; mined from the HARNESS TRANSCRIPT, the
  ground-truth record on disk, so it survives a mid-arc /clear) and the
  project state before anything else. Use at every session start and after
  /clear.
- **/checkpoint** - arc closer. Push, refresh the day file's WHERE WE LEFT
  OFF (both sides of the final exchange VERBATIM + state + next-likely;
  write the reply into the file, then send that exact text), reset the
  task counter, emit the safe-to-clear marker. Refuses mid-arc, with
  uncommitted work, or with a running employee.
- **/ship** - batch shipper. Player-readable commit, push, build zips
  (never deleting old ones), counter tick. Runs after every completed
  batch, unprompted.
- **/brief** - delegation composer. Builds a sub-agent brief per the
  delegation laws (stamp, self-contained context, token budget line,
  diff-only reporting), then verifies cheap and ledgers the outcome.

## THE SKILLS RULE (standing, Mazhron 2026-09-03)

When a ritual or law is BORN or AMENDED, its skill is added or updated IN
THE SAME BATCH - law text and skill never drift apart. And whenever a skill
changes, REFRESH its copy in the future-project kit folder ("Future Project
MDs/skills/" plus this file) in the same batch, like every other kit file.

## New-project bootstrap (plug and play)

THE MASTER SEQUENCE lives in the kit folder's front door: "0 - READ ME
FIRST, CLAUDE.md" (kit-folder-only file; a new project's Claude reads it
and installs the whole operating system in order: wiki -> reporting ->
delegation -> skills). Skills go LAST because they call the tools the
earlier steps build; each skill degrades gracefully by pointing at its
METHOD file when a tool is missing. Nothing in the skills is
Everwood-specific except named examples (marked "in Everwood").

## Change log

- 2026-09-03 WS1: shelf founded with /standup, /checkpoint, /ship, /brief;
  THE SKILLS RULE established; kit copies created.

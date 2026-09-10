# The Knowledge Wiki Method

A portable system for organizing a project's knowledge so an AI assistant
(Claude) finds anything in three cheap hops and never wastes tokens reading
what it does not need. Developed on Everwood (2026-08); written so a future
project can bootstrap it with one instruction: **"Read WIKI_METHOD.md and
set this up for this project."**

---

## Why it works (the token mechanics)

Claude's file access has three operations with very different costs:

1. **Glob** (file names) - nearly free.
2. **Grep** (content search) - searches WITHOUT loading the file; only the
   matching lines return. Grepping a 5,000-line file for its headings costs
   ~50 tokens. This is the load-bearing fact.
3. **Read** - the only real cost, and it takes offset/limit: read lines
   200-260 and pay only for those. What is read once stays in context for
   the session.

Plus one standing cost: the instruction file (CLAUDE.md) is loaded IN FULL
every single session. Everything else is opt-in.

Therefore: keep the always-loaded core tiny, make every other file findable
by name, every section findable by heading, and every related topic
reachable by an explicit pointer - and lookups cost tens of tokens instead
of thousands.

## The architecture (three layers, one home per fact)

1. **THE LEAN CORE - CLAUDE.md** (always loaded): laws, process,
   active/handoff notes, and THE INDEX - one descriptive line per library
   file. Budget it (Everwood: ~250 lines, hard alarm at 700 via a lint
   script). Knowledge that is read every session (ship process, test
   commands, standing rules) lives here; everything else does not.
2. **THE TOPIC LIBRARY - docs/systems/*.md** (read on demand): one file
   per subject (soil, fauna, ui, performance...). Read ONLY when touching
   that subject. Grows without limit; the core never grows with it.
3. **PORTABLE NOTES - repo root** (carried to future projects): engine
   lessons (GODOT_FIELD_NOTES.md), genre lessons (CLICKER_DESIGN_NOTES.md),
   and this file. Rule: engine fact -> engine notes; genre pattern -> genre
   notes; project detail -> topic library. ONE home per fact - split homes
   drift.

## The three-hop lookup

1. The CORE's index line picks the FILE (no file is opened).
2. `Grep "^## " <file>` returns the live section index - every heading
   with its line number (~50 tokens; can never rot like a hand-written
   table of contents, because the headings ARE the index).
3. `Read <file> offset=<line> limit=<n>` loads just that section - and the
   section's closing `See also:` line names each connected topic WITH its
   file, so the next hop needs no search at all.

## The conventions (the law)

- **HEADINGS ARE SEARCH KEYS.** Every section starts `## <searchable
  nouns>` naming what a search would look for ("## Vision cones", never
  "## More fixes" or "## Misc"). A file of unheadlined prose is invisible
  to hop 2 - headline it the first time you touch it.
- **CROSS-REFERENCES.** Sections end with one line:
  `See also: topic -> file.md | topic -> file.md`
  pointing at everything this topic interacts with, wherever it lives -
  other library files, the portable notes, design docs. (Example: a
  creature's section points to the plants it eats in flora.md, its sprites
  in art-pipeline.md, its upgrades in meta.md.)
- **READ CHEAP.** Grep headings first; Read sections only; never read a
  topic file whole except in a deliberate full pass.
- **ONE INDEX LINE PER FILE** in the core, with a description good enough
  to pick the right file without opening any. A lint script keeps the
  index and the disk in sync and alarms when the core bloats
  (reference implementation: Everwood's tools/check_claude_md.py).
- **GROW INCREMENTALLY - THIS IS THE STANDING PRACTICE, NOT A PROJECT.**
  Never stop work for a library-wide pass. Instead, EVERY TIME a file is
  written, updated, or created - every feature, upgrade, fix, ruling -
  the touched sections get proper headings and See also lines then and
  there, cross-referencing whatever already exists. The web thickens as a
  side effect of normal work until everything connects to everything.
- **NEW FILES WHENEVER A SUBJECT OUTGROWS ITS HOME** - plus its index
  line, plus See also lines linking it into the web both ways.
- **RESOLVED/HISTORICAL notes move to a history file** so live files stay
  current; superseded sections say so where they stand.
- **TAGS + THE KNOWLEDGE INDEX (Mazhron approved 2026-09-03).** A section
  whose content is hard-won (a lesson, a trap, a doctrine) carries, directly
  under its heading: `Tags: tag1, tag2 | one-line brief of the takeaway`.
  Starter tags: lessons, gotchas, architecture, performance, process,
  design, economy - invent a new one only when none fits. A script compiles
  every Tags line into a GENERATED index file (one section per tag, one
  clickable line per entry linking to the fact's TRUE home - no
  duplication), so a HUMAN browsing the wiki gets every pitfall and lesson
  at their fingertips, and new files/tags grow the index automatically
  (reference implementation: Everwood's tools/export_tag_index.py ->
  KNOWLEDGE_INDEX.md). Tag new hard-won sections as they are written -
  same incremental law as headings.

## The expansion doctrine (files are cheap - grow fearlessly)
Tags: process, architecture | Default to new topic files and indexes; storage and tail-reads are nearly free, cramming is not

Mazhron's ruling, 2026-09-03. The economics that make the whole method work:
a txt/md knowledge file costs the user almost nothing (disk) and costs
Claude almost nothing (it is only read section-by-section, on demand). A
script is a one-line run, chained into the repeatable "run everything"
chain. What is EXPENSIVE is the opposite instinct: cramming unlike
knowledge into a file where it does not belong, making every file longer,
every grep noisier, and the web harder to traverse.

So the manager's filing instinct, in order:
1. FIT: new knowledge goes into the existing topic file + index where it
   belongs (one home per fact).
2. FOUND: if it does not fit any current home - a different genre, a
   different domain, a kind of information likely to recur - CREATE the
   new topic file and its index line ON THE SPOT, and wire it into the
   scripts (or better: write scripts that AUTO-DISCOVER new files, like a
   tag-index exporter that sweeps whole directories, so growth needs no
   wiring at all).
3. NEVER HESITATE on file count. Ten thousand small files and four hundred
   indexes that are cheap to hop beat one bloated file that taxes every
   read. An ever-expanding web IS the design goal, not a smell.
4. THE MILESTONE HEADS-UP: if the user sets a file limit, honor it; and
   when the knowledge-file count crosses a round milestone (~1000), the
   manager MENTIONS it once - purely informational, growth is good, no
   action required (a lint script can print the count so nobody counts by
   hand).

See also: conventions -> this file | one home per fact -> this file |
tag index -> tools/export_tag_index.py (reference).

## Bootstrapping a NEW project (what Claude does on request)

1. Create/diet CLAUDE.md into the lean core: laws + process + index,
   inside a line budget. Move existing deep knowledge verbatim into topic
   files under docs/ (or create the first few empty topic files the
   project obviously needs).
2. Write the index (one line per topic file) and a lint script that
   checks core size + index/disk sync; wire it into the workflow ("run it
   whenever the core grows").
3. Copy the portable notes from the previous project (engine notes, genre
   notes, this file) into the repo root and index them.
4. Add THE WIKI CONVENTION block to CLAUDE.md (read-cheap, search-key
   headings, See also lines, incremental growth, one home per fact).
5. From then on, follow the standing practice: every write expands the web.

## The read diet: size before you read (the 10k rule)
Tags: lessons, economy, process | A whole-file read past ~10k tokens is section-read or delegated; the harness knows the size before the read, so a warn-only hook says it at the cliff edge

Born 2026-09-10 from the origin CEO's weighted-usage insight: only the
tokens that count against the plan matter, and under those weights (input
1, cache write 1.25-2, cache read 0.1 or 0.025, output 5) everything the
manager reads is WRITTEN into the context at 1.25x and re-read every later
turn. A 24k-token file read inline costs ~30k weighted up front and rides
in every request for the rest of the session; the same file section-read
costs 2-4k; the same file understood by an employee in a throwaway
context comes back as a 2k summary at the employee's price.

THE RULE: know the size before you read. The signals are free - the byte
size on disk (divide by four), the heading index from a grep, the line
count. A whole-file read past ~10k tokens is either SECTION-READ (grep the
headings, read one section by offset/limit or `sed -n A,Bp`) or DELEGATED
(an "understand this file/system" step goes to an employee; the manager
takes the summary). The one fair exception: an EDIT that needs the exact
text - say so and proceed.

WHY NOT A COUNT IN EVERY HEADING (the CEO's first idea): a hand-typed
token count goes stale the moment the section grows and costs output at
5x to maintain. The count is GENERATED instead, at the cliff edge: the
kit's diet guard hook (HOOKS_METHOD.md Tier 2c) reads the file size before
the Read or the cat runs and says "this is ~24k tokens, 12 sections -
section-read or delegate" as a warning, never a refusal. The usage sheet's
daily line then grades the day (heavy whole-file reads, section-read
share) against the previous seven, so a slip is named the next morning.

See also: The output diet (below) | HOOKS_METHOD.md Tier 2c (the diet guard) | SUBAGENT_METHOD.md "Why this saves money" (the 10k delegation line) | REPORTING_METHOD.md (THE WEIGHTED COLUMN + THE COMPARISON RULE)

## The output diet (every emitted token costs 5x)
Tags: lessons, economy, process | Output is weighted 5x and every tool result is written at 1.25x; the manager's emit habits are a budget lever, not a style choice

Same origin, same day (the CEO: "a permanent rule not only for this
machine but for Rootstock-os as a whole"). Under the budget weights the
manager's OUTPUT - prose, edits, briefs, thinking - is a fifth of the bill
at five times the price of input, and every TOOL RESULT is context written
at 1.25x and re-read forever. So the emit habits are law:

- EDIT over WRITE: a Write re-emits the whole file; an Edit emits the
  change. (A NEW file is one Write, never incremental appends.)
- SCRIPTS GENERATE DOCUMENTS: tables, indexes, ledgers, changelogs, sheets
  are produced by scripts (the Script Rule); the manager never types what
  a script can render.
- NEVER RESTATE: a result the table, the ledger or the diff already
  carries is pointed at, not repeated in prose. A reply leads with the
  outcome and stops when the content stops.
- LIMITERS ON CHATTY COMMANDS: git log with a count, git diff with a path
  or --stat, listings with a depth or a filter, installs with -q, test
  runs through the runner that prints one verdict. The diet guard hook
  says the limiter when one is missing (warn-only, capped per session).
- BRIEFS ARE SELF-CONTAINED, NOT PADDED: an employee's brief is output too.
- EFFORT MATCHES THE TASK: thinking is output; routine doc and ledger
  sessions run at lower effort, the high setting is for design and
  debugging (where the platform exposes the knob).

See also: The read diet (above) | HOOKS_METHOD.md Tier 2c | REPORTING_METHOD.md "The Script Rule" | SUBAGENT_METHOD.md law 1 (the brief)

## Maintenance honesty

- When MOVING a section between files, update the See also lines that
  pointed at it (grep the topic name across the library - cheap).
- When two files accumulate overlapping coverage, merge to one home and
  leave a pointer in the other.
- The index description is part of the interface: when a file's scope
  shifts, its index line shifts with it.
- Cross-references are for NAVIGATION, not prose: one compact line, plain
  arrows, no sentences.

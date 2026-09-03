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

## Maintenance honesty

- When MOVING a section between files, update the See also lines that
  pointed at it (grep the topic name across the library - cheap).
- When two files accumulate overlapping coverage, merge to one home and
  leave a pointer in the other.
- The index description is part of the interface: when a file's scope
  shifts, its index line shifts with it.
- Cross-references are for NAVIGATION, not prose: one compact line, plain
  arrows, no sentences.

# The Knowledge Wiki Method

PURPOSE: A portable system for organizing a project's knowledge (a lean
  CLAUDE.md core, a docs/systems topic library, portable root notes) so an
  AI assistant finds anything in three cheap hops, Glob, Grep for headings,
  then a targeted Read, without wasting tokens.
INTENT: Developed on Everwood so a future project can bootstrap the same
  system with one instruction, keeping token costs low without losing
  findability.

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

1. **THE POINTER CORE - CLAUDE.md** (always loaded): the project in a
   paragraph, how to read, how to verify, the laws no hook enforces, and
   ONE pointer to the master index. Under Anthropic's 200-line target
   (the lint fails past LINE_BUDGET 200 / TOKEN_BUDGET 2,000, warns past
   1,000; the origin lands ~900 tokens, a fresh install lower). Rules that
   only matter for part of the codebase live in .claude/rules/ with
   `paths:` front matter and load only while a matching file is read.
   Everything else is one line in docs/index/MASTER_INDEX.md, the one
   door, and what falls out of use in the core moves there BY SCRIPT
   (the section below).
2. **THE TOPIC LIBRARY - docs/systems/*.md** (read on demand): one file
   per subject (soil, fauna, ui, performance...). Read ONLY when touching
   that subject. Grows without limit; the core never grows with it.
3. **PORTABLE NOTES - repo root** (carried to future projects): engine
   lessons (GODOT_FIELD_NOTES.md), genre lessons (CLICKER_DESIGN_NOTES.md),
   and this file. Rule: engine fact -> engine notes; genre pattern -> genre
   notes; project detail -> topic library. ONE home per fact - split homes
   drift.

## The harness memory (machine-local facts only; the trim ruling)

The harness keeps its own per-machine, per-folder auto-memory OUTSIDE the
repo (in Claude Code: %USERPROFILE%\.claude\projects\<slug>\memory\ - an
always-loaded MEMORY.md index over bodies read on demand). It looks like a
fourth knowledge layer; the rule (the CEO's trim ruling, 2026-09-22) is
that it never holds a fact the repo can own. It does not travel between
machines, is never pulled, reviewed or linted, and drifts stale invisibly
- the repo is the shared, versioned home. Auto-memory keeps ONLY
machine-local facts the repo cannot carry: this machine's exe paths,
installs, PATH quirks. (The workstation file's per-machine inventory is
the repo-side record of the same ground; the two must agree.)
THE TRIM, when auto-memory has grown repo-shaped facts: bank each body
VERBATIM into a topic file (provenance line + a pointer to the repo file
that owns the LIVE fact), rewrite the memory file as a superseded stub
pointing at the bank, and open a tally ledger in the history folder - one
line each time a banked fact is needed again (date | machine | section |
what needed it). A threshold (first pass: 3 hits on one fact, or 5 total,
inside 30 days) raises a PROPOSE to restore that fact to auto-memory; the
owner decides (the learning loop). Nothing is deleted - the preservation
law covers memories too; a wrong memory is marked superseded in place.

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
the Read or the cat runs. INDEX FIRST (the CEO's order 2026-09-10 PM,
"section or split as necessary ... should not require my approval"): the
first whole read of a big file in a session is REFUSED and the refusal
carries the file's own index (headings or function lines with line
numbers, ~1-3% of the file), so the next call reads one section; the
same call repeated passes with a warning only - the editing exception
needs no words. The usage sheet's daily line then grades the day (heavy
whole-file reads, section-read share) against the previous seven, and
the big-reads ledger (tools/big_reads.py) names WHICH files were read
whole and the fix each needs (section it, index it, grep it). THE
STANDING ORDER: the manager sections or splits what that ledger names
without asking. THE MEASUREMENT LESSON (2026-09-10): the first "21 big
reads a day" were screenshots - an image is priced by PIXELS (~1-2k
tokens), never by its base64 bytes; a diet metric that counts pictures
as text proposes fixes for a habit nobody has. Check what a metric
counts before acting on it.

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

## The cold shelf (rarely-used knowledge moves, never dies)
Tags: architecture, process, lessons | Prune means MOVE: cold sections go to docs/cold/ verbatim, indexed, with a stub left at the old heading; nothing is ever deleted

THE PRESERVATION LAW, knowledge side (the origin CEO, 2026-09-10, when the
manager proposed "pruning" dead knowledge): "the knowledge should never
be lost... all of this is hard fought, hard earned knowledge, even the
rarely used knowledge." So the wiki has a COLD SHELF:
- docs/cold/<same basename as the hot file>.md holds sections moved out
  of the hot file VERBATIM (heading + body byte for byte, one provenance
  comment under the heading: moved from where, when, why, how many lines).
- The hot file KEEPS the heading, with a two-line stub under it: "Moved
  to the cold shelf <date> (<reason>): docs/cold/<file> - read only when
  this topic comes up." + a See-also to the index. Heading greps still
  land, and the record of the move is at the old address.
- docs/cold/INDEX.md is the append-only index (date | moved/restored |
  hot file | heading | lines | reason | shelf file). It gets ONE line in
  the core file's library index, and a shelf file is read ONLY when a
  stub or the index says the topic moved there - never preemptively.
- The mover is a script (tools/cold_shelf.py: --move, --restore, --list,
  --check, --dry-run); it contains no deletion code and refuses to
  overwrite anything on the shelf. --restore brings a section back and
  leaves a "restored" note on the shelf, so the shelf is history too.
- CANDIDATES come from the heat map (tools/wiki_heat.py mines the harness
  transcripts for read counts per section; "cold" = untouched by any read,
  whole reads included, for --days). The OWNER picks what moves. A script
  proposes; a human rules; nothing moves on its own.
- COLD BY READ COUNT IS NOT A SHELF REASON (the CEO's ruling 2026-09-10:
  "in a game situation, we only touch certain files at certain times ...
  we built the wiki not only for your reference, but for a human
  reference"). The heat map therefore says WHY each cold file is cold,
  from git activity in the code area it documents: active-unread (the
  code moved AFTER the doc was last opened - the one class worth a look:
  a heading that is not a search key, a stale section, or knowledge that
  was not needed), current (opened since the code last moved), dormant
  (the code did not move), process (laws, registry, roadmap - read when
  the ritual calls), reference (lore, store copy, changelog - for humans)
  and archive (history, the shelf). Only active-unread ever reaches a
  proposal. The origin project's first count of 367 cold sections was
  180 changelog entries, 25 shipped-roadmap entries, history, and a
  counting flaw (a whole-file read did not count as seeing a section):
  zero system sections were actually cold. Audit the audit before acting.
Why this shape and not deletion: the token cost of a cold section is one
heading line in every heading grep and a share of every whole-file read
of its host. Moving it removes that cost; deleting it would also remove
the knowledge, and the knowledge was the point. The stub costs two lines.
See also: the learning loop -> this file (next section); THE PRESERVATION
LAW -> SUBAGENT_METHOD.md law 7 | HOOKS_METHOD.md Tier 2d; the mover ->
tools/cold_shelf.py; the candidates -> tools/wiki_heat.py.

## The hot core and the sub-indexes (the core diet: CLAUDE.md never bloats again)
Tags: architecture, economy, lessons | CLAUDE.md is a pointer core under Anthropic's 200-line target; knowledge has three homes (always / when a matching file is read / on demand behind the master index); sections that fall out of use move by script, one stub line each, verbatim and reversible

The origin project's CLAUDE.md grew from ~250 lines to ~10k tokens in
three weeks while its own law said "index only" - laws were promoted in
full text, index lines became paragraphs, and nothing measured it. A
Reddit reader measured the kit's front door instead (it was named
"...CLAUDE.md") and called the whole thing slop. The CEO's ruling
(2026-09-14): "CLAUDE.md is the main index that keeps the most used
information (similar to your heatmap concept) and once they fall out of
the high-use heatmap, they get moved (by script) to the appropriate index
out of CLAUDE.md ... These indexes can grow much more than the CLAUDE.md
file. They will need to have appropriate names for the files and sections
inside that connect to the appropriate knowledge txt files."

THE SECOND RULING (Mazhron 2026-09-14, after reading Anthropic's memory
doc, code.claude.com/docs/en/memory): "Claude.md should simply point to
everything else ... Claude.md doesn't need to load 2-5k tokens each
time, Claude.MD just needs to guide Claude on where to go to get the
information Claude needs which Claude will add to it's cache/context as
needed only." Anthropic's page settles the mechanics: target under 200
lines per file; imports and unscoped rules load at launch, so moving
must-read text into them "helps organization but doesn't reduce
context"; a rule with a `paths:` field loads only when Claude reads a
matching file; CLAUDE.md is guidance, hooks are the enforcement layer.
So KNOWLEDGE HAS THREE HOMES, by WHEN it is needed:
- ALWAYS -> CLAUDE.md, the pointer core: the project in a paragraph, how
  to read, how to verify (build commands belong here, Anthropic says),
  the laws no hook enforces, one line each. Nothing else is restated.
- WHEN A MATCHING FILE IS READ -> .claude/rules/<topic>.md with `paths:`
  front matter (game code rules for scripts/, text rules for data/ and
  ui/, wiki hygiene for every .md). The harness loads them itself; no
  hook, no Read call, no output tokens. A rule WITHOUT paths loads every
  session, so the lint counts its tokens against the core budget.
- ON DEMAND -> docs/index/MASTER_INDEX.md, THE ONE DOOR: every topic
  file, root file, sub-index, law stub, rule and knowledge file, one
  line each, and every destination listed DIRECTLY (each hop costs a
  Read; never chain three files to reach a fact).
A must-read chain enforced by hook was considered and rejected: a file
Claude must read every session costs the same as if it sat in CLAUDE.md
plus a Read call, and a hook cannot make Claude read, only inject or
block. The saving is in loading rules only when they apply.

THE LAW:
1. CLAUDE.md is THE POINTER CORE, budgeted in lines AND tokens: the lint
   (check_claude_md.py) FAILS past LINE_BUDGET (200, Anthropic's target)
   or TOKEN_BUDGET (bytes/4; 2,000, the owner's action line), WARNS past
   WARN_TOKENS (1,000), requires CLAUDE.md to name the master index and
   the master index to list every docs/systems and docs/index file and
   every rule, and fails on a rule with no `paths:` field. The answer is
   never a raised budget. standup prints the OK/WARN line every session
   so the owner sees the size; the hygiene guard runs the lint the moment
   CLAUDE.md, the master index or a rule is edited. The origin lands at
   ~900 tokens / 68 lines; a fresh install lower.
2. Every `## `/`### ` section of the core is a UNIT. A unit that should
   be movable carries `Index: <name>` (its sub-index); `Index: core` pins
   it. A hard-won unit carries `Tags: ... | brief` - the brief becomes
   its stub, so the core still states the law in one sentence.
3. HEAT (tools/core_diet.py, the check group, BEFORE the lint): explicit
   reads of the unit's lines (the transcript cache wiki_heat keeps), reads
   of the wiki files the unit points at (its follows), and whether git
   touched it inside the window (`core_cold_days`, trend_limits.json,
   30). A unit with none of the three is COLD.
4. THE MOVE (by script, in the loop): `--move` moves every COLD routed
   unit VERBATIM into docs/index/<name>.md (a wiki file: headings are
   search keys, each section keeps its Tags and See-also lines that
   connect it to its knowledge files, a provenance comment records the
   origin) and, while the core is still over budget, the coldest routed
   units next. Each move leaves ONE line in the MASTER INDEX's "## The
   sub-indexes" block: `- <heading> -> docs/index/<name>.md | <brief>`
   (the block lived in CLAUDE.md itself until the pointer core).
   A COLD unit with no Index line is only PROPOSED - a human names its
   home. `--move-section` is the manager's explicit call; `--restore`
   reverses a move (the unit returns after the unit it followed).
5. THE SUB-INDEXES grow without limit (docs/index/laws.md, library.md,
   process.md, gotchas.md, code.md in the origin) and are read like any
   wiki file: `Grep "^## "` then the section. The scanners (wiki_heat,
   check_wiki_links, export_tag_index, export_wiki_view, cold_shelf)
   discover docs/index/ as wiki files; the lint requires every sub-index
   to be named in the master index, and the master index in the core.
6. NOTHING IS DELETED (the preservation law): a move is verbatim,
   stubbed, ledgered (docs/history/core_diet.txt regenerated,
   core_diet_runs.txt appended) and reversible. The laws that matter most
   are HOOKS anyway (the hooks rule) - the prose in the core is a pointer,
   the guard is the law.

What this is NOT: the cold shelf. The cold shelf takes rarely-READ topic
sections out of hot topic files, by a human's choice. The core diet takes
sections out of the one ALWAYS-LOADED file, by script, on heat and budget,
because that file's size is the only standing cost in the system.

See also: the architecture (layer 1) above; the cold shelf below;
tools/core_diet.py; tools/check_claude_md.py; docs/index/MASTER_INDEX.md;
.claude/rules/; WORKFLOWS.md "Diet the core (move a CLAUDE.md section to
a sub-index)" and "Add or change a path-scoped rule"; INTENT.md "The core
diet" (both rulings); the hooks rule -> HOOKS_METHOD.md;
https://code.claude.com/docs/en/memory (Anthropic: size, rules, imports).

## The learning loop (ledgers measure, scripts propose, the owner rules)
Tags: architecture, process | Three read-only scripts close the loop: dead links, section heat, and ledger trends turned into PROPOSE lines at standup

The origin CEO asked (2026-09-10) whether the system learns. Honest
answer: the model cannot change its weights; the PROJECT learns, in
files, and only where discipline puts the lesson down. The loop that
makes learning less dependent on discipline:
1. MEASURE - every ritual appends a ledger (tests, builds, usage, links,
   heat, employees, compactions, grants, retirements).
2. NOTICE - tools/ledger_trends.py reads the ledger tails against a
   THRESHOLDS table (`--limits` prints it) and emits PROPOSE lines: the
   read diet slipping (CHECK verdicts, big whole-file reads), a flaky
   test group, dead wiki links, a cold-shelf sweep due, an employee
   model past the escalation rule, too many compactions. Standup prints
   the block right after THE BUDGET. When the proposal set changes, one
   line lands in docs/history/proposal_runs.txt - the loop has history.
3. RULE - the owner reads the proposals and says yes, no, or later. The
   manager never applies one unasked. A proposal that keeps recurring
   with a no is a threshold to retune, not a rule to force.
4. GROW - the yes becomes a law, a hook, a threshold change or a cold-
   shelf move, filed per the conventions; the next ledger line shows
   whether it worked.
What it still is not: automatic. Edges in the wiki exist only where a
session wrote them (the link checker catches the dead ones, not the
missing ones); heat is lexical (a Read at a line range mapped to the
CURRENT headings, approximate for old reads); and nothing rewrites a
rule by itself, by design - the CEO ruled that a script never deletes
and the same spirit governs what a script may decide.
See also: the cold shelf -> this file (previous section); the scripts ->
tools/check_wiki_links.py | tools/wiki_heat.py | tools/ledger_trends.py;
the ledgers discipline -> REPORTING_METHOD.md; the escalation rule ->
SUBAGENT_METHOD.md law 5.

Search keys: wiki method, knowledge library, three-hop lookup, CLAUDE.md
  core, hot core, sub-index, core diet, token budget, docs systems library

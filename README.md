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

Kit version: **v1.42** (2026-10-01). The graft log `UPGRADES.md` is the
single source of truth; this line is checked against it on every sync.

---

## What loads every session, what Anthropic says, and what guards it

The installed CLAUDE.md is a POINTER file: the project in a paragraph, how
to read, how to verify, the laws no hook enforces, and one line naming the
master index. It stays under Anthropic's own 200-line target for a
CLAUDE.md file. This repository looks large because it is install
instructions, method files and reference scripts, read ONCE by the Claude
doing the install; none of it is a CLAUDE.md and none of it loads into a
session's context.

| What | When it loads | Size (origin project, 2026-09-14) |
|---|---|---|
| CLAUDE.md, the pointer core | Every session, automatically | ~900 tokens, 68 lines |
| A path-scoped rule (`.claude/rules/*.md`) | Only while a matching file is open | a few hundred tokens each |
| The standup digest | Once, at session start / after /clear | ~2.5k-3.5k tokens (was ~4.3k before the digest diet: only verdicts, moved ledgers and the last exchange print in full; four loss-test trims since, the last on 2026-09-29) |
| The master index / wiki (47 files) | NEVER whole. A section at a time, on demand | ~289k tokens on disk, ~0 by default |
| The front door `0 - READ ME FIRST.md` | Once, at install | ~1.8k tokens |

Knowledge has three homes, by WHEN it is needed:

- **ALWAYS.** CLAUDE.md itself: the pointer core.
- **WHEN A MATCHING FILE IS READ.** A `.claude/rules/*.md` file with a
  `paths:` front matter field, loaded by Claude Code itself, not by a hook
  or a Read call.
- **ON DEMAND.** `docs/index/MASTER_INDEX.md`, the one door: every topic
  file, root file, sub-index, law stub, rule and knowledge file, one line
  each, every destination listed directly.

What guards the shape:

- **The token-budget lint** (`check_claude_md.py`) fails past LINE_BUDGET
  200 (Anthropic's own number) or TOKEN_BUDGET 2,000 (the owner's action
  line), and WARNS past WARN_TOKENS 1,500 (retuned from 1,000 in v1.37,
  after it fired every session with no cold unit to move). It also
  requires CLAUDE.md to
  name the master index, the master index to list every topic file,
  sub-index and rule, and it fails a rule file that has no `paths:` field,
  because such a rule would load every session and its tokens belong to
  the core's budget.
- **The standup digest** prints the lint's OK/WARN line every session, so
  the size is visible without asking.
- **The hygiene guard**, a PostToolUse hook, runs the lint the moment
  CLAUDE.md, the master index or a rule is edited.
- **The core diet** (`core_diet.py`) moves a cold section out of the core
  by script, verbatim and reversibly, leaving one stub line in the master
  index. Cold is three signals at once, not a read count: no explicit
  read of the section's lines, no read of the wiki files it points at,
  and no git touch inside the window (30 days by default).

Anthropic's own guidance: https://code.claude.com/docs/en/memory. Its
words: target under 200 lines per CLAUDE.md file, longer files consume
more context and reduce adherence; it gives no token figure of its own.
The 1,000-token number that circulates online is a community estimate,
not Anthropic's.

## The problem: context is the bill

An AI assistant's real cost is not the question you ask. It is the CONTEXT:
the whole conversation, plus every file the model has read, rides along
with EVERY subsequent request. A six-hour session answers its last question
at several times the price of its first one. Every file read wholesale is a
tax you keep paying for the rest of the session.

Everything in Rootstock is a variation on one insight:

> Keep the manager's context small, and let cheap, disposable contexts do
> the reading.

### "Doesn't a wiki make the context HEAVIER?" (what actually loads)

The natural objection: more files means more to read, so the context gets
fat and token-hungry. It would, if the files loaded. They do not. Almost
nothing in Rootstock rides in the context by default:

| What | When it enters context | Size (origin project, 2026-09-14) |
|---|---|---|
| CLAUDE.md, the pointer core | Every session, automatically | ~900 tokens, 68 lines (was ~3.5k that same morning, ~10k before the core diet) |
| A path-scoped rule (`.claude/rules/*.md`) | Only while a matching file is open | a few hundred tokens each |
| The standup digest | Once, at session start / after /clear | ~2.5k-3.5k tokens (was ~4.3k before the digest diet: only verdicts, moved ledgers and the last exchange print in full; four loss-test trims since, the last on 2026-09-29) |
| The wiki (47 files) | NEVER whole. A section at a time, on demand | ~289k tokens ON DISK; ~0 in context |
| Skills | Only the one invoked, when invoked | a few hundred tokens each |
| Hooks | Never (they are scripts; only their one-line output enters) | ~0 |

So a session opens at roughly 3.5k-4.5k tokens of context (the core plus
the digest) for a project whose written knowledge is ~289k. The core is a sliver of the wiki, and a linter
(`check_claude_md.py`) fails when it grows past budget, because THAT is
the one file that is a standing cost. The rule that keeps it small:
CLAUDE.md is a POINTER file, one pointer to `docs/index/MASTER_INDEX.md`;
the index lines live in the master index, and knowledge lives in the topic
files. Since v1.22 the budget is in tokens and a script (the core diet,
below) moves what falls out of use, so the number cannot drift up again
unnoticed.

The rest is reachable, not loaded. Claude greps a file's `## ` headings
(~50 tokens, the file itself never loads), then reads the one section it
needs with offset/limit (~1-2k). The origin project's daily meter shows
85-95% of reads landing as section reads, and a hook says the size out
loud before any whole-file read past ~10k. The "where we left off" record
is a few hundred tokens of verbatim exchange, which replaces the several
thousand it takes to re-explain state to a fresh session by hand.

The honest caveat: dump everything into CLAUDE.md and yes, every session
pays for all of it. That is exactly the failure Rootstock is built
against, and the reason the core is guarded by a linter rather than by
willpower.

### The installed CLAUDE.md: what it holds and how big it is

Knowledge has three homes, by when it is needed. ALWAYS lives in
CLAUDE.md, the pointer core: the project in a paragraph, how to read, how
to verify, the laws no hook enforces, and one pointer to
`docs/index/MASTER_INDEX.md`. WHEN A MATCHING FILE IS READ lives in a
`.claude/rules/*.md` file with a `paths:` front matter field, loaded by
Claude Code itself while that kind of file is open, never by a hook. ON
DEMAND lives in the master index, the one door: every topic file, root
file, sub-index, law stub, rule and knowledge file, one line each.

The origin project's own core sits at 68 lines, ~900 tokens. It stays that
size on its own: the token-budget lint (`check_claude_md.py`) fails past
budget and the budget is never raised, and the core diet (`core_diet.py`,
kit v1.22) runs before it, moving the coldest routed sections VERBATIM out
to sub-index files under the index folder - each move leaves one pointer
line in the master index, and a hard-won section's Tags brief stays
behind as its stub - reversible with `--restore`.

The honest line: the origin's own core had drifted to ~10k tokens before
any of this existed, then to ~3.5k after the first fix. The mechanism took
two rulings the same day: the CEO first ordered the token-budgeted diet,
then asked whether CLAUDE.md should simply point to everything else. A
read of Anthropic's own memory page settled the mechanics, and the second
ruling followed: a pointer core, a single master index, and rules that
load only by path.

### The receipts: 44 metered days of the origin project

None of the above is a guess. The harness writes a full transcript of every
session, and every request in it carries the real API meter; Rootstock's
usage sheet ("reference tools/usage_report.py") totals those meters per
model and per tool by day, week, and month. From Everwood, the origin
project - one machine, 2026-07-22 to 2026-09-03, 7,573 metered requests:

- The model GENERATED ~7.6M tokens. To generate them it RE-READ ~3.8
  BILLION tokens of context - 498 tokens re-read for every token written.
  Cached re-reads are billed at a tenth of the input price and context is
  STILL roughly 93% of the weighted token bill. The bill is the context.
- The most expensive tool by far is reading files: ~22.6M tokens of file
  content injected across 955 Reads - nearly 8x all Edits and Writes
  combined - and every injected token is then re-read by every later turn.
  Whatever teaches the model to read less, wins.

And the before/after, same model, same project, from the sheet:

- **The wiki diet** (adopted Aug 24: grep a file's headings, read only the
  section you need). Average file content injected per Read: ~35k tokens
  before (Aug 1-23), ~21k after (Aug 24 - Sep 1), ~10k once the habits
  compounded (Sep 2-3). Same codebase, 71% less paid per read.
- **The checkpoint protocol** (adopted Sep 2: day files make /clear
  lossless, so sessions actually end). In the last days of the
  endless-session era, context had accreted until the model was re-reading
  810-898k tokens PER REQUEST (Aug 26-27). The first two cleared-session
  days averaged ~267k per request - a 69% cut against that peak - while
  Sep 3 did three times the requests of an Aug 26-27 day.

### The weighted receipts (the same window six days on: 50 days, 2026-09-10)

Raw token counts flatter the wrong column. What counts against a plan is
WEIGHTED: input x1, cache write x1.25 (x2 on a one-hour cache), cache read
x0.1 (x0.025 on the model that discounts it), output x5 - the API's own
price ratios. Re-run on those weights, the same machine's 4.2 billion raw
tokens over 50 days were about 366 million weighted, and the split is not
what the raw column suggests:

- Cache READS, the giant raw number, were 41% of the weighted bill. Cache
  WRITES - new context entering the prefix - were 29% at the five-minute
  write rate the pillar shares assume, and the model's own OUTPUT (prose,
  edits, thinking) 13%. Fresh input rounds to zero. The shares stop at
  ~83% because this machine ran the one-hour cache, whose doubled write
  price is the rest: counted at its true rate, writes were the largest
  pillar at ~46%, which is the method file's finding (writes first, reads
  second) from its earlier window.
- Prefix REWRITES nobody chose - a cache that expired, a core file edited
  mid-session - were 24% of the all-time budget. They are now counted per
  day, because a waste with a name gets fixed.

The kit's usage sheet leads with the weighted number and keeps the raw one
as trivia beside it; the fan-out guard meters with the same weights; and
every day is judged against the previous seven (spend, cache misses,
whole-file reads) with a verdict the standup digest relays the next
morning. A number without a comparison means nothing.

Different days do different work, so read the percentages as one project's
honest metering, not a controlled benchmark. But the mechanism is
arithmetic, not anecdote: a session that clears re-reads a small context
many times instead of a huge one, and a model that reads sections stops
paying for whole files on every turn that follows.

## The four pillars, and two companions

### 1. The Knowledge Wiki (WIKI_METHOD.md)

Project knowledge lives in a web of small topic files, not in one giant
document and not in the chat. The core instruction file (CLAUDE.md) stays
lean: laws, process, and a one-line-per-file index. The method bootstraps
a brand-new project from a single instruction; these are the conventions
that make it work:

- **Read cheap.** Grep a file's headings first (about 50 tokens), then read
  only the section you need. Never read a topic file whole.
- **Headings are search keys.** Every section is named for what a search
  would look for, never "Misc" or "More fixes".
- **Cross-references.** Sections end with "See also" lines pointing at
  related topics WITH their file, so a hop needs no search. Moving a
  section updates every See also that pointed at it; two files that
  grow overlapping coverage merge to one home and leave a pointer.
- **One home per fact.** Engine lessons, genre lessons, and project details
  each live in exactly one layer, because split homes drift.
- **Tags and the knowledge index.** A hard-won section (a lesson, a trap,
  a doctrine) carries a one-line `Tags:` brief, and a script compiles
  every Tags line into a generated knowledge index - the wiki browsed by
  topic instead of by file.
- **The harness memory stays machine-local (the trim ruling).** The
  harness's own per-machine auto-memory never holds a fact the repo can
  own: it does not travel between machines, is never pulled, reviewed or
  linted, so it drifts stale invisibly. It keeps only this machine's exe
  paths, installs and quirks. Repo-shaped memories are banked verbatim
  into a topic file, superseded in place with a stub, and a tally ledger
  counts every later need of a banked fact - enough hits proposes a
  restore, and the owner decides.
- **Incremental growth.** Every file touched during normal work gains
  proper headings and links then and there. No stop-the-world passes.
- **Size before you read (the 10k rule).** A whole-file read past ~10k
  tokens is section-read or handed to an employee; the diet guard refuses
  the first whole read of a big file (once per file per session) with the
  file's own index attached, and warns on every later one. Editing that
  needs the exact text is the one fair exception: the same call repeated
  passes.
- **The output diet.** Every emitted token costs five; every tool result
  is written into context at 1.25x and re-read forever. Edit over Write,
  scripts generate documents, nothing restated that a table already says,
  limiters on chatty commands.

- **Nothing is deleted (the preservation law).** Neither the manager nor
  any employee deletes a file, record or tree without the owner's yes
  given twice, and no script is written that deletes. A file RETIRES to a
  shelf folder; a rarely-read wiki section moves VERBATIM to a cold shelf
  with a stub left behind; a wrong fact is marked superseded in place. A
  hook (described with the rest in the hooks section below) refuses
  delete verbs, work-discarding git verbs and deletion calls
  written into code; the rare real deletion is recorded with the owner's
  two acknowledgments, word for word, before the one command runs.
- **The wiki learns (the learning loop).** Three read-only scripts close
  the loop: a link checker finds dead cross-references, a heat map mines
  the transcripts for reads per section and says WHY a cold page is cold
  (code moved after the doc was last opened is the only kind worth a
  look; cold by read count is never a reason to shelve), and a trends
  script turns ledger tails into PROPOSE lines at standup when a threshold
  crosses. Nothing is applied by a script; and since v1.35 every line
  carries its class: a [DO] proposal (an audit, a digest trim, a stale
  loop group, dead links, an unwritten lesson: anything a script, a hook
  or an employee carries) is done in the reply that reads it, never
  offered as a choice, while an [ASK] proposal (an open question, a
  shelf, a game number) waits for the owner. "The owner decides" names
  the ASK class, not the mechanics. A done [DO] clears by its own
  ledger, never by memory: since v1.36 a named corrections pattern is a
  PATTERN row in the corrections ledger, and the proposal stays quiet
  until a new correction lands.
- **The lessons book (the lesson loop).** Steps live in the process
  registry; judgment lives in LESSONS.md: one entry per task shape, THE
  ONE RIGHT WAY first, then TRIED / FAILED BECAUSE / DO INSTEAD, then
  nuance lines as they accumulate. The prompt hook names the entry to
  read before the first tool call, and since v1.33 the ROUTE line beside
  it: the process-registry entry and the script whose heading, WHEN line
  or search keys the prompt already hits, so "does software already
  handle this" is a lookup and not an inference (Hightower's "infer once,
  export, run without inference", applied to the routing itself). The
  Stop hook asks for the entry the moment a turn shows trial and error;
  a check script lints the shape and a ledger counts advised against
  written; the enforcing hooks live in the hooks section below. The
  origin's first entry: read the existing spread before briefing a
  numbers task.
- **The whole-read ledger.** Beyond the 10k rule above, a per-file ledger
  names which files were read whole and the fix each needs; the manager
  sections or splits them unasked. Pictures are priced by pixels, never
  by their bytes.

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

- **The Script Rule.** Tests, builds, imports, exports, probes, reports,
  data regeneration: scripted once, changed only to add a capability or
  fix a defect, never re-typed in chat. A compliant runner owns every
  legal run combination and refuses an illegal one quoting the law,
  parses its own pass/fail, names the machine, and keeps long soak runs
  out of the default sweep.
- **The Baseline Rule.** The first act after a runner exists is a FULL
  baseline recorded in its ledger; a regression is then a visible line
  flip, never a memory.
- **Ledgers.** Every run appends one labeled line to a history file: date
  and time, machine (or agent, identified automatically from hostname or
  user path, never typed), project version, what ran, the result,
  and the failures if any. You read the TAIL, never the whole file, and
  runs compare across versions without re-reading anything. The test
  for a new kind of run: a number that matters enough to mention in a
  conversation matters enough to append. A ledger is never pruned: one
  that grows huge starts a dated continuation file with a pointer left
  behind, because the history is the product.
- **Sheets a human opens get a spreadsheet twin.** The CSV and TXT stay
  for grep and git diffs; the .xlsx has a frozen header, thousands
  separators and a bold total per period - because a sheet nobody can
  skim is a sheet nobody reviews, and numbers nobody reviews change
  nothing. When the spreadsheet library is missing the run still writes
  the CSV and TXT and says the .xlsx was skipped; a ledger run never
  crashes over formatting.
- **Trust the ledger.** A green test at an unchanged version is never
  re-run "for confidence"; the runner warns if you try. This one rides in
  the origin project's always-loaded core rather than in the method file:
  it is the ledger rule's flip side, read before every verification.

The usage sheet and its weighted column - the receipts sections earlier
on this page - are the same discipline pointed at the AI bill itself,
with a pair of rules of its own: the transcripts ARE the ledger, so the sheet
regenerates whole instead of appending, and its rows are keyed by machine,
because each machine sees only its own transcripts.

This is not just thrift. On its first day in Everwood, the discipline
caught three real bugs, because scripted runs with ledgered baselines make
regressions impossible to hand-wave.

### 3. The Delegation Company (SUBAGENT_METHOD.md)

Three roles, always: the human is the **CEO**, the Claude you talk to is
the **MANAGER**, and sub-agents are **EMPLOYEES** with fresh, empty,
disposable contexts. Which model manages is the CEO's standing choice,
asked at setup and revisited as models change - never assumed.

- The manager never reads a big unfamiliar file inline (that plants it in
  the expensive context forever). Past the same ~10k line the wiki's
  read diet draws, an employee reads it in a throwaway context and
  returns a short map instead.
- **Who gets what.** An assignments table per project maps task types to
  models, cheapest first: the cheapest model runs tests, search sweeps and
  mechanical batch edits; the middle tier implements from a precise spec,
  drafts doc sections and does first-pass review; the strong tier takes
  multi-file refactors and gnarly bugs with a written plan; design,
  architecture, rulings, verification and pushes never leave the manager.
  Cheap employees run several at once for independent jobs, never two
  writers on one file. And every dispatch names its model in the call:
  a model-less one inherits the manager's own tier, the one tier that is
  never an employee, so the brief guard refuses it (v1.40).
- Every brief is STAMPED (task, date, model), SELF-CONTAINED, and carries a
  budget line: exceed ~30 tool calls or fail the same step twice, and the
  employee stops and reports instead of running up a bill. The report ends
  with the employee's own stamp: model, effort, tokens, confidence, and
  the tools it used.
- **How many at once.** A handful of employees per batch (four is the
  habit), never a burst, never an employee that spawns employees. A task
  that seems to need dozens is a design problem - split it, script it,
  or ask the CEO - never a bigger fan-out. A harness hook refuses the runaway shapes outright and
  only the owner tunes its numbers, through `/runaway`. An employee whose
  task seems to need a deletion stops and reports: the preservation law
  binds staff too.
- Employees write files directly and report the diff, never paste bodies.
- **The fabrication check.** Claims must match the diff, and the stamp's
  tool count must match the harness meter: a claimed read or run with a
  metered tool count of zero was invented. This is not hypothetical: the
  check exists because a delegated audit once "classified" a file it
  never opened (93k tokens of fiction, caught for about 2k because the
  meter said zero).
- **The truthfulness hooks** (v1.30) make the mechanical parts of that
  mechanical: a work brief missing its required lines is refused at
  dispatch; the moment a result lands, a hook reads the harness-metered
  figures (the numbers no model can fake), flags a zero-call "success"
  or a tool count claimed at several times the meter, and appends one
  pending line per delegation; a Stop hook (its tag: LEDGER ADVISED) then refuses to end the turn
  while a delegation sits unverified and unledgered. What stays
  judgment - whether the diff matches the claims - stays audited
  through the ledgers instead.
- **Verify cheaply, in order.** Tests or probes first, a spot-read of the
  diff second, a full read only when those smell wrong: the manager's
  check never costs more than the task did.
- **Attribution.** Every idea and change of plan is attributed and dated,
  so a mistake traces to its maker. When the CEO asks for something that
  contradicts a rule they set earlier, the manager flags the
  contradiction and confirms before building - never silently comply,
  never silently refuse.
- **The scorecard.** An append-only performance ledger tracks every
  employee task (who delegated, task type, model and effort, metered
  tokens, outcome) with correction tallies. The escalation rule: when a
  task type's corrections pass ~25% of its last ~10 tasks, that task type
  is promoted to a stronger model, with a dated line saying so. The
  assignment itself is the manager's (v1.37): any task type may drop a
  tier on trial without asking, and the rate moves it back up (a trial
  is ledgered with "trial" in its line, so the rate counts it); the only
  fixed line is the owner's choice for their project (in the origin
  project the top model is never an employee, to save tokens). Catches -
  real problems an employee flagged that everyone else missed - are
  tallied too, the strongest signal a tier earns its keep. Models
  move on data, not impressions.

The manager keeps design, laws, architecture, verification, and pushes.

### 4. Lossless Sessions (the rituals, packaged as skills)

The endgame: you can clear your chat at any checkpoint and lose NOTHING,
because context lives in files, not in the conversation.

- **The Daily Log.** Each work day gets a file: the CEO's asks, the
  completions, and a WHERE WE LEFT OFF section carrying both sides of the
  final exchange (your last prompt AND the manager's last response).
- **The Checkpoint Protocol.** A counter ticks whenever a reply actually
  changed the tree or the commit (a pure question never ticks) and warns
  at 8 tasks (dire at 15) or when less than 80% of the context budget
  remains; ADVISED MEANS DO IT, so the owner never has to ask - and since
  v1.31 THE HOOK LAW: every line a hook prints that names work (a
  checkpoint, a lesson, a kit sync, a changelog export) is an order the
  manager carries out inside that reply, worded as such, never a note
  relayed for the owner to act on; the same warning seen twice is the
  failure; and since v1.34 the SOURCE is closed too: a reply that names
  a checkpoint as the natural next step has just ordered one, and the
  Stop hook refuses the reply once until it ends with the safe-to-clear
  marker (naming a checkpoint is making it). Under 30% of the context
  budget the checkpoint is urgent and comes before any new work. At an
  arc's end the manager runs the session loop, then asks two questions
  before pushing: was anything this arc done by hand twice (then it is a
  process-registry entry, the loop law), and was anything learned by
  trial and error or corrected (then it is a lesson, the lesson law);
  then pushes, refreshes the day file, and emits the marker:
  "CHECKPOINT - safe to /clear. Nothing in this chat exists only in this
  chat." It refuses with an employee running or work uncommitted. A
  checkpoint is where the method learns, not only where it saves.
- **The proposal law (v1.35).** A standup proposal is a source of the
  same kind as a named checkpoint: a reply that names a [DO] proposal
  its ledger still raises is refused once until the proposal is done
  (PROPOSAL NAMED); only an [ASK] proposal is a question for the owner.
- **The net under it (v1.28).** A session end (/clear, a closed window)
  runs a hook that checks for unbanked work. Nothing unbanked: one ledger
  line. Otherwise it banks the bytes itself - both sides of the final
  exchange from the transcript into the day file as an AUTO section, a
  commit, a push to origin and to the local mirror, the counter reset -
  so a forgotten checkpoint loses nothing. The manager still writes the
  judgment (state, open queue, next likely) at the next real one.
- **Standup.** Every fresh session opens with one script that prints the
  last exchange (mined verbatim from the harness transcript on disk, so
  it survives a mid-arc /clear), the state, ledger tails, the open roadmap, and THE BUDGET:
  yesterday's and today's weighted spend judged against the previous seven
  active days, with the reason when something went wrong. In the origin
  project's measurements, a cleared session re-arms in about 15-20k
  tokens instead of dragging hundreds of thousands.

Nine rituals ship as Claude Code skills, invocable as slash commands:
`/standup`, `/checkpoint`, `/ship`, `/brief`, `/runaway`, `/preserve`,
`/intent`, `/correct`, and `/flag`. `/preserve` is the preservation law's
front (retire a file, shelve a wiki section, or walk the twice-acknowledged
delete grant, in that order); `/flag` is the purpose audit (green, yellow
or red, filed in FLAGS.md); `/intent` records the why of a ruling in the
owner's words; `/correct` walks a correction, asks for the intent, then
makes the fix and logs it;
`/runaway` shows and tunes the fan-out guard's numbers, owner only;
`/brief` composes an employee's work order by the delegation laws. `/ship`
is the one you will use most: sanity-check tests (trusting the ledger),
ask the security question (did this diff touch secrets, env, auth,
headers, CORS, hosting or database rules? then the audit runs first;
v1.39), read the scripted version hint (none, patch or minor from what changed
since the last bump; never major) and bump if warranted, commit with a
player-readable subject, push, run
the build script without deleting old builds, sync the kit if kit files
changed, and export the changelog unprompted.

### The hooks: laws the harness enforces itself (HOOKS_METHOD.md)

A skill runs when invoked; a hook runs when the harness reaches a moment.
Anything a law can enforce mechanically becomes a hook, not a longer
reminder. Fifteen ship in `hooks/`, wired by one settings file:

- **Session start** injects the standup digest by itself - after a /clear
  the manager has everything back before anyone types a word.
- **Every prompt** carries a silent context gauge that speaks only when a
  threshold is crossed, and since v1.33 the ROUTE line: the registry
  entries and reference tools the prompt already hits, named before the
  first tool call, and since v1.40 the live usage window: last five hours
  against the worst five hours of the last seven days, spoken only when
  the window is already most of the peak and ledgered when it speaks;
  **every reply** ticks the checkpoint counter when
  work actually happened, and refuses to end the turn once it is dire.
- **Before compaction** a ledger line records what was at stake.
- **Session end** is the checkpoint's net (v1.28): with nothing unbanked
  it writes one ledger line; with unbanked work it mines the final
  exchange from the transcript into the day file, commits, pushes to
  origin and the local mirror, and resets the counter.
- **The lesson advisor** reads each finished turn for trial and error -
  the same command run again after an error, repeated edit misses, a
  FAIL followed by a PASS, a claim resolved DIFFERENT, an employee
  briefed twice, a prompt that reads as a correction - and refuses to end
  the turn once with LESSON ADVISED, so the lesson lands in LESSONS.md
  before the arc moves on. Never the same turn twice; a turn that wrote
  the lesson passes. The same hook holds the manager to its own words:
  a reply that names a checkpoint as due without banking one, or names
  a standup [DO] proposal the trend script still raises, is refused once
  (v1.34, v1.35). The prompt gauge carries the other end: a prompt
  whose words hit an entry's Keys line gets that entry named before the
  first tool call.
- **The shell guard** refuses what the CEO's laws forbid (no force push, no
  skipped hooks, plus the project's own rules). Beside it, at zero runtime
  cost, the kit settings file's permissions.deny block (v1.40) refuses a
  Read or Edit of .env files, key material and credential folders, and
  the destructive shell one-liners.
- **The fan-out guard** is catastrophe-only: it refuses a burst or flood of
  sub-agent spawns or runaway token velocity - each self-clearing - and
  warns on the rest. It exists because a manager once spawned 821 agents
  on "check my markdown files". The default numbers: 8 spawns in a
  minute, 25 in ten, or 10M weighted tokens in two minutes. The CEO tunes
  them with `/runaway`; the manager never raises one on its own.
- **The diet guard** says a file's size before a whole read past ~10k
  tokens and the missing limiter on a chatty command, at the moment of
  the decision; the first whole read of a big file per file per session
  is refused with the file's own index in the refusal, and the same call
  repeated passes; since v1.40 a later whole read of that file, unchanged
  since, is refused once more as already in context (the re-read rule,
  cleared by compaction).
- **The preserve guard** refuses delete verbs (bare names, pipelines and
  the mirror verbs included), work-discarding git verbs (every force
  push included) and deletion calls written into scripts, and reads
  every script a command executes before it runs - the whole file when
  git does not track it, only the uncommitted added lines when it does -
  refusing one that deletes. The session scratchpad and prose
  files pass; one command passes per delete grant the owner acknowledged
  twice. A drive root, the home folder, the repo root, any .git folder,
  a bare wildcard, a `..` climb or a variable target pass never, and a crash in the guard fails closed.
- **The hygiene guard** runs AFTER every file edit and says the law that
  applies to that file: refresh the kit copy (and this README) when a
  portable original changes, add the missing See-also line to a wiki
  section, fix a forbidden character in player-facing text (the only one of
  its rules that blocks), run the engine import after a new asset. It exists because
  this README once fell two versions behind while the law to refresh it
  was already written.
- **The delegation truth set** (v1.30, a trio) watches the Agent
  tool itself: the brief guard refuses a work dispatch whose brief lacks
  the stamp template, the intent line, the budget line or the
  preservation line, and since v1.40 one whose model is missing (which
  silently inherits the manager's own tier) or explicitly names it;
  the delegation auditor reads the metered tool and
  token figures out of every result, names a fabricated report (zero
  metered calls) or an inflated tool count, and appends a pending
  ledger line, and since v1.42 it also runs at the employee's own stop:
  it counts the employee's transcript (a background employee's result
  is only a launch notice, so this is the only meter there is), holds
  the employee once when its self-reported tool count is under 70% of
  the truth or its template lines are missing, and ledgers the true
  figures; the verify advisor refuses to end a turn while a
  delegation is pending without a resolution line. It exists because of
  a public case where a manager said its sub-agents did their job when
  they had not.
- **The format guard** runs BEFORE an edit of the settings file and
  refuses one that would unwire, narrow or mis-point a safety hook (or
  not parse), and AFTER every edit of a kit thing, blocking one that
  leaves the thing without its header (PURPOSE, INTENT, search keys, see
  also) with the rewrite command in the reason. Two more hooks back it
  up: the shell guard refuses shell writes into a settings file, and the
  Stop hook refuses to end a turn while the live wiring is broken, so no
  prompt, brief or contributed patch switches a guard off quietly. It exists because a community kit
  needs a guardrail that does not depend on the reader's good faith.

The contract, plainly, because a worried reader asks these first:

- **Hooks need Claude Code.** They are wired through `.claude/settings.json`,
  which is Claude Code's mechanism. In another client (the Claude app,
  Cowork, an IDE plugin) the laws are prose again; the wiki and the
  rituals still work, the enforcement does not.
- **A hook cannot trap you.** Each Stop hook refuses to end a turn at
  most once per crossing (the checkpoint counter re-blocks only every
  five further tasks; the advisors never repeat the same slice or set),
  and each checks the harness's own loop flag so it can never refuse
  forever. Every other
  refusal is one command, with the reason printed; the next command runs.
- **A broken hook CAN lock you out**, which is the one real hazard: a
  hook that exits with the blocking code (a mis-typed path, a missing
  interpreter) refuses every tool call, not just the one it meant to
  guard. The fix is one line in settings.json; every kit hook answers
  `--selftest` and is tested by piping a fake event into it before it is
  wired. A selftest proves the cases its author imagined; since v1.40 the
  guard replay (`guard_replay.py`) runs the last N days of recorded tool
  calls, employee sessions included, through the guards' judge functions
  in a sandbox and prints per rule what would be refused now, what was
  refused live, the NEW catches and the LOST ones - read the LOST column
  before trusting a guard change.
- **Turning one off** is removing its line from settings.json, for every
  hook outside the safety tier; unwiring a safety hook is exactly the
  edit the format guard refuses. No hook keeps
  state a project must migrate: the gitignored state files age out on
  their own.
- **Cost.** Tokens: none (a hook is a script; only its one-line verdict
  enters the context). Time: one interpreter launch per trigger, about
  0.3 seconds, and a shell command runs four of them in a row.
- **What is not built yet.** On the pin board: a notification hook that
  toasts the OS when the manager is waiting on you; it ships when the
  CEO asks. A second idea, a hook refusing an employee's report when its
  stamp is missing, was deferred outright when the truthfulness set
  landed - the auditor already names a malformed report the moment it
  lands.

### The intent loop (INTENT_METHOD.md)

A rule tells Claude what to do; the reason tells it what to do in the
case the rule never named. So every ruling gets a section in the
project's INTENT.md: the owner's ask verbatim, the owner's numbered
reasons verbatim, the manager's reading marked as the manager's, and
where the rule lives. Before building, the manager logs its OWN reading
of the ask; employees state theirs in a stamp line. When the owner's
intent is known, the claim resolves SAME, SIMILAR or DIFFERENT, with its
source named (stated, revealed by a correction, or inferred, which is
counted apart so it never inflates the rate). A small toolchain backs it - an
intent log, a correction log, a report script, a systems audit - and the
report turns that log into day, week and month agreement rates per
actor, a text file for Claude and a csv with a spreadsheet twin for you,
and calls the trend improving, steady or declining. The owner's reason, in the owner's words: real data, past
against present, and a trend that says whether the feedback loop works.
One ordering law rides with the audits - security first, then cost, then
efficiency: a number behind a REFUSAL stays in code; a number behind a
PROPOSAL may live in a tunable data file. The fan-out guard's numbers
are the ruled exception, the owner's by name, tuned through `/runaway`.

`/correct` closes the loop from the other side: it asks what about the
last thing needs correcting, records your words verbatim, marks the
claim DIFFERENT, then asks "What was the intent?" and `/intent` files
the why while the mismatch is fresh. A systems audit, ledgered and
proposed on a cadence, has read-only employees look at tokens, process,
knowledge and shipped features and return proposals only. No employee
applies anything; since v1.35 the manager does every standup [DO]
proposal in the reply that reads it (the systems audit's own included,
with the README audit, the digest trim, a stale loop group, dead
links, an unwritten lesson, a stale claim) and relays only the [ASK]
ones; the audit itself runs in the reply whose standup proposed it.

The first systems audit ran on 2026-09-14 (kit v1.21; the night of the
13th's session, ledgered after midnight). Four read-only
employees returned 26 proposals; the owner ruled on every one. What it
found and what changed: habitual scripts were being run by hand and their
ledgers drifted, so THE LOOP LAW now holds (a script that runs more than
once is called by the parent loop, `reference tools/run_all.py`, which
ledgers every group run; the session-start hook runs the session group
once a day; standup shows each group's age; ledger trends proposes when
one goes stale). Four check scripts re-appended identical rows at an
unchanged tree, so they share a trust-the-ledger helper. Three ledgers
the preservation law promised had never been born, so the movers got
selftests and the ledgers exist. Open questions to the owner now have
their own ledger with an age nudge. The standup digest's size, a per-arc
cost line and a cache-miss ledger with causes are measured, not guessed.

### The format law and the purpose audit (CONTRIBUTING.md)

Two guardrails for a kit that is meant to take contributions, ours or
yours:

- **The format law.** Every thing in the kit (a script, a hook, a skill,
  a method file, the hooks README, the front door itself) carries one
  header: `PURPOSE:` (what it
  does, plainly), `INTENT:` (why it exists, in the words of whoever asked
  for it), search keys and see-also links. A lint derives the scope from
  the kit folder itself, names every thing that lacks the header, and
  the publish script refuses to push on a failure. A missing header is
  added BY SCRIPT after a read-only look (`format_lint.py --rewrite`
  inserts only the missing lines), never by hand. The format guard hook
  above makes it a law rather than a reminder.
- **The purpose audit.** Before an update merges, and whenever a thing is
  unflagged or has changed since its last flag, a Claude (or a person)
  reads it, compares what its PURPOSE line says against what the body
  does, and flags it: GREEN does what it says and nothing more; YELLOW
  matches in substance but something is off (fix later, may ship); RED
  does what its purpose does not say or crosses a law (deletes, disables
  a guard, unbounded spend, routes around a refusal) and the owner sees
  it before it ships. The
  ritual is read-only, then flag, then explain: the auditor never edits
  the thing in the audit turn. `FLAGS.md` is the one committed file that
  references every flag, hashed to the exact version reviewed, tallied at
  the top, and open to any reviewer's findings by pull request. The
  tally's stamp moves only when a flag moves, never on a no-change run,
  so the mirror check never warns over noise. A thing with no PURPOSE
  line cannot be GREEN. `/flag`
  walks the ritual; `purpose_audit.py --pending` lists what needs one.
  The kit's own first audit (v1.19) flagged 58 things: 53 green, 5
  yellow, 0 red. v1.20 closed all five the next morning, one of them by
  the first independent read of the front door, which found the header
  undersold what the file installs and the skill list gone stale. Three
  author passes had missed both.

`CONTRIBUTING.md` carries both laws in full, plus what a contributed
update looks like (the header, the graft-log entry, a passing lint, a
flag from someone other than the author, nothing deleted, no em or en
dashes).

### The two companions (WORKFLOW_METHOD.md, WORKSTATION_METHOD.md)

Two smaller disciplines ride with the pillars. Neither saves tokens
directly; both stop a kind of amnesia.

- **The process registry.** A project accumulates multi-step processes
  (the ship order, an art pipeline, a retune round-trip) that nobody
  writes down, so the sequence is re-derived from memory or a vanished
  chat, and a step gets skipped. WORKFLOWS.md holds ONE runbook entry per
  repeatable process: WHEN it applies, the STEPS with the scripts named,
  how to VERIFY. The capture rule: whoever performs such a task checks
  the registry first; a stale entry is a bug fixed in the same batch; a
  missing entry is a gap the manager files in the same batch, or hands to
  the cheapest model as transcription work. Employees never edit it; they
  report gaps on their stamp line. Since v1.37 a script (`law_gaps.py`)
  reads the rule's shadow too: a tool changed in 30 days that no
  registry entry, loop group, hook setting or skill names is a WARN line
  at standup.
- **The workstation inventory.** One document listing every package,
  tool, path and setting the project's scripts and hooks depend on, split
  REQUIRED and OPTIONAL, with the need, the why, and the install command
  for each (WORKSTATION.md), the harness's own settings included (user
  level, project level, what is per-machine and gitignored), plus a
  survey script
  (`workstation_survey.py`) that proves a machine up to par. A second
  machine, a reinstall or a collaborator sets up from a document instead
  of from error messages. The rule: a new dependency goes into the
  inventory and the survey in the same batch that introduced it.

## What it saves, concretely

| Habit it replaces | Rootstock way | The saving |
|---|---|---|
| Reading files wholesale | Grep headings, read one section | A 50k read becomes ~1-2k |
| Re-explaining project state each session | Standup digest from ledgers | 5-10x smaller session opens |
| Marathon sessions that get pricier every turn | Checkpoint + /clear, losslessly | Later turns cost a fraction |
| The manager reading big files | Employee distills in a throwaway context | ~50k permanent becomes ~1k |
| Re-running green tests "to be sure" | Trust the ledger (runner enforces it) | Whole probe runs, skipped |
| Runaway agent loops | Budget line in every brief, plus the fan-out guard | Partial report instead of a bill |
| Reading a 24k-token file inline | The diet guard says the size first; section-read or delegate | ~30k weighted becomes ~3k, and it stops riding every later turn |
| Cost numbers with no baseline | The daily line judges each day against the previous seven | Waste gets a name the next morning |
| A screenshot counted as a 100k read | Pictures priced by pixels | Diet proposals aimed at real habits, not phantom ones |
| A deleted file, a wiped tree | Retire, shelve, or ask twice | Knowledge never lost; a bad script cannot cost a folder |
| Laws forgotten mid-batch | The hygiene guard speaks at the edit | The kit copy and this README stay in step by themselves |

The unglamorous truth this kit encodes: there is no magic compression
trick. The savings come from structure, scripts, and discipline. (The kit's
origin project evaluated the viral "let the AI invent its own compressed
language" idea and declined it with receipts; prompts are under 1% of
session cost. Structure is where the money is.)

## What you need (and what still works without it)

The FULL kit assumes three things: **git**, **Python 3**, and **Claude
Code** (the skills install into `.claude/skills/`; the standup
last-exchange replay and the usage sheet mine Claude Code's local
transcripts in `~/.claude/projects/`). The reference scripts come from the
origin project and degrade gracefully rather than crash, but they are
meant to be adapted - version strings, ledger names, and paths are
per-project.

Missing a prerequisite is fine, and the front door knows what to do about
it: no git means the push/update machinery is skipped while day files,
ledgers, the wiki, and the sub-agent brief rules all still work; no Claude
Code means the skills and transcript miners are skipped and the checkpoint
writes the exchange into the day file by hand. Every skip is recorded in
the install stamp itself, so a later update knows what was never
installed. And the methods are worth taking a la
carte - the day-file ritual, the append-only ledgers, and the brief rules
(stamped, self-contained, budgeted, claims-must-match-the-diff) each stand
alone. An honest partial install beats a pretend full one.

**Installing into an existing project?** The front door's BROWNFIELD RULE
applies: Claude inventories what you already have (your own split
knowledge files and logging scripts count as installed pieces), proposes a
mapping, and gets your approval before touching any existing file - a
production-sensitive file needs a go-ahead naming it, not a general
yes. It never restructures a live repo unasked.

## Quick start

1. Give this repo's contents to Claude (Claude Code, any capable model).
2. Say: **read "0 - READ ME FIRST.md" and install the kit.**
3. Answer its STEP 0 questions: project, engine and repo; who manages and
   which employee models are available; one workstation or several; which
   domain-notes files apply; and your update policy (ask, auto, relevant
   or never).
4. Claude builds the operating system in order: the wiki (and the process
   registry the day the first two-step process exists), reporting, the
   session rituals and the workstation inventory, delegation, skills,
   hooks, then the loops that measure the loop: the learning loop, the
   intent loop, the format law and purpose audit, the README gate, the
   lesson loop, and the route line beside it. Last, the optional boards
   (ideas, roadmap, changelog) and, if the project has a backend, a key,
   an env file, a database or accounts, the security audit's bootstrap
   before the first public release; a project with none writes its
   exemption and moves on.
5. It finishes with a definition of done you can verify yourself: the
   standup script runs clean, the core lint passes (CLAUDE.md under
   Anthropic's 200-line target and its token budget, every rule declared
   by path, the master index complete - the lint keeps all of it true),
   the format lint passes and FLAGS.md flags every kit thing,
   the delegation ledger has one real line, the skills answer to their
   slash commands, and the first commit is in.

That is the whole handoff. The front-door file exists precisely so that a
stranger's Claude needs no other instructions. The front door is an
install runbook read once (~1.8k tokens); it is not a CLAUDE.md and never
loads per session.

## Updating an installed project

Rootstock keeps growing, but an installed project must NEVER be updated by
copying newer kit files over it. An install is an adaptation: Claude
renamed paths, tailored the core file, and your project has since grown its
own knowledge into those files - overwriting them would destroy the very
thing the system protects. So the kit updates CONCEPTS, not files:

- The kit is versioned, and `UPGRADES.md` is its **graft log**: one entry
  per concept added, each with WHAT it is, which kit files CARRY it, how
  to GRAFT it onto an existing install, and, from v1.17 on, which README
  section it touched (so a concept cannot ship without deciding whether
  this page needs to know).
- This page is checked, not trusted. A parity lint derives every count on
  it (laws, skills, hooks, scripts, the box table, the version line) from
  the kit's own files, and the kit's publish script refuses to push while
  any of them disagree. A ledgered README audit cadence (distinct from
  the purpose audit below) proposes a fresh
  cross-reference (four read-only employees, one lane each, reading every
  method file against this page) once the kit has taken more commits or
  days than the owner's thresholds allow since the last one; the trend
  script prints how far past those thresholds the kit sits.
- Installing stamps a line into the project's CLAUDE.md:
  `Rootstock vX.Y installed <date> | updates: <policy>`, with any skipped
  prerequisite recorded on the same line (`| no-git`). An install that
  predates versioning counts as v1.0; the update adds the line while it
  is there.
- To update: pull this repo (or hand Claude the new folder) and say
  **update rootstock**. Claude reads the graft log's entries newer than
  the project's stamp, applies each concept to the project's OWN files in
  its own names and voice, and bumps the stamp. The one exception to
  never-copy: a file the project does not have at all (a genuinely new
  MD or reference script) is copied in fresh, then adapted and indexed. Anything that would
  contradict a choice you made on purpose gets flagged, never overwritten.
- You don't have to remember any of this: the install wires
  `rootstock_update_check.py` into your project's standup, which checks
  this repo weekly (offline-safe, one ledger line per check) and reports
  newer grafts by itself. What it does on the network: one HTTPS fetch of
  this repo's UPGRADES.md, at most once a week, or a read of a local clone
  if you point it at one. It sends nothing about your project anywhere.
- **You choose the noise level.** The stamp carries your update policy -
  `ask` (default: present the grafts, you pick), `auto` (apply everything,
  report after), `relevant` (only offer grafts that benefit your project;
  skipped ones are never re-offered), or `never` (quiet unless you ask).
  Change it any time by telling Claude "update automatically", "stop
  asking about updates", or "only show me relevant updates".

## Questions people ask

- **Does it need Claude Code?** For the full kit, yes. What carries to
  other clients (the Claude app, Cowork, Cursor, the API): the wiki
  carries fully, it is plain markdown any model can read if the client's
  project instructions point at the front door; the day files, ledgers
  and brief rules carry as method; the skills carry where the client runs
  skills, though ours shell out to Python; the hooks do not carry at all.
- **Isn't a 5k-token CLAUDE.md the opposite of lean?** It would be, and it
  is not one: the file a reader measured was the install runbook, since
  renamed ("0 - READ ME FIRST.md") so the name cannot mislead. The
  per-session CLAUDE.md Rootstock builds is a pointer core: one pointer to
  the master index, the laws no hook enforces, and the process every
  session needs, budgeted in tokens by a lint that fails and never raises,
  with a script that moves cold sections out. See "The installed
  CLAUDE.md: what it holds and how big it is" above.
- **How big is the CLAUDE.md this actually installs?** Anthropic's own
  guidance targets under 200 lines per CLAUDE.md file; it gives no token
  figure. The 1,000-token number that circulates online is a community
  estimate, not Anthropic's. The origin project's installed core is 68
  lines, about 900 tokens, guarded by a lint that fails past 2,000 tokens
  or 200 lines and warns past 1,500 tokens (v1.37; it warned at 1,000
  until the warning fired every session with nothing left to move).
- **Does it improve my prompts?** No, and that is the point. It moves
  the CONTEXT (wiki, ledgers, day files) and the INTERPRETATION (laws,
  hooks, the process registry) out of the prompt and into files read
  every session. A miss gets filed once as a ruling, a memory or a hook
  instead of being rephrased into every prompt after it; and because a
  fresh session is free, a lazy one-line prompt still lands.
- **Does it work with models other than Claude?** The methods are model
  agnostic and the front door makes Claude ASK who manages rather than
  assume. The skills and hooks are Claude Code mechanisms.
- **Is anything sent anywhere?** No. Everything is local files and git.
  The only network calls are the optional weekly fetch of this repo's
  graft log and, when you run the security audit with `--url`, plain
  requests to your own deployment to read its headers; nothing about your
  project leaves your machine.
- **Can I take part of it?** Yes; see "What you need" above. The wiki
  conventions alone are the biggest single saving.
- **Can I use it commercially?** MIT. Yes.
- **Can I drive it from my phone?** Yes, through Claude Code's Remote
  Control: `/remote-control` (alias `/rc`) in a running session prints a
  QR code, the
  Claude app's Code tab scans it, and the phone becomes a second keyboard
  for that SAME session, with its files, tools and hooks. The workstation
  stays on. A checkpoint `/clear` resets the phone's view too and needs
  no re-pairing. Whether a `/clear` typed on the phone fires the
  session-start hook is not stated in Anthropic's docs; the kit records
  it as unconfirmed until one clear from the phone prints the standup
  digest. It needs a Pro, Max, Team or Enterprise login; an API key
  alone, Bedrock, Vertex, Foundry or a custom base URL rule it out. When
  the workstation must go off, a cloud session (claude.ai/code) clones
  the remote and runs on Anthropic's machines, without the engine, hooks
  or test runners, so it suits reading and planning, not building.
  `WORKSTATION_METHOD.md` "Drive a session from a phone" has the
  requirements and limits.
- **Does it check the app I build, or only my process?** Both, since
  v1.39. Everything above audits the process. `SECURITY_METHOD.md`
  audits the app: before the first public release (a URL, a store
  listing, a showcase post), and before any release
  that touched secrets, env files, auth, headers, CORS, hosting or
  database rules, the checklist runs and a ledger line says PASS. It
  exists because a survey of 100 AI-built apps found 37 shipping a
  server-side secret in their frontend JavaScript and 78 missing a
  security header, mostly an env variable renamed `VITE_` or
  `NEXT_PUBLIC_` to silence a build error. The script half
  (`security_audit.py`) greps a build for secret shapes and reads your
  own site's headers, exposed paths and CORS answer, read-only; the
  judgment half (database rules, auth per route) is a checklist an
  employee walks. A key that was ever public is rotated, never merely
  removed.
- **Can I contribute?** Yes, by pull request, under two guardrails that
  apply to the kit's own authors too: every new or changed thing carries
  the header (`PURPOSE:`, `INTENT:`, search keys, see also) or the lint
  refuses it, and every changed thing gets a read-only purpose audit
  (GREEN / YELLOW / RED) filed in `FLAGS.md`, ideally by someone other
  than its author. `CONTRIBUTING.md` has the whole of it. A RED is a
  question for the maintainer, not a rejection.

## What is in the box

| File | What it is |
|---|---|
| `0 - READ ME FIRST.md` | The front door: an install runbook read once (STEP 0 questions, the install order as pointers, definition of done); not a CLAUDE.md |
| `WIKI_METHOD.md` | The knowledge wiki: token mechanics, conventions, bootstrap |
| `LESSONS.md` | The one-right-way book: the lesson law, the entry shape, and the origin's first entries; grepped before any task, fed by the lesson advisor hook |
| `REPORTING_METHOD.md` | Scripts + ledgers: the three rules, runner spec, bootstrap |
| `SUBAGENT_METHOD.md` | The delegation company: org chart, seven laws, assignments table, scorecard, bootstrap |
| `SKILLS.md` | The skills shelf: what each ritual-skill does and the skills rule |
| `skills/` | The nine skills, ready to drop into `.claude/skills/` |
| `rules/` | The first path-scoped rule, `wiki.md`: drop into `.claude/rules/`, loads only while a markdown file is open; write your own game and text rules beside it |
| `HOOKS_METHOD.md` | The hooks: the contract, the fifteen kit hooks, tiers, bootstrap |
| `hooks/` | The fifteen hook scripts and `_hooklib.py`, the shared library they import (drop into `tools/hooks/`), `README.txt` with the per-hook setup steps, plus the settings template (merge into `.claude/settings.json`; since v1.40 it carries a permissions.deny block: destructive shell shapes and Read/Edit of .env files, key material and credentials) |
| `WORKFLOW_METHOD.md` | The process registry: one runbook entry per repeatable task, the capture rule |
| `WORKSTATION_METHOD.md` | The machine inventory: document, survey script, new-machine runbook |
| `INTENT_METHOD.md` | The intent loop: the why file in the owner's words, the claim-and-verdict ledger, the correction ritual, the agreement report, the systems audit, bootstrap |
| `SECURITY_METHOD.md` | The pre-production security audit: the gate before an app, SaaS or site with a backend, a key, an env file or user data goes public; the rotation law, the prefix law, the nine-class checklist (secrets in the client, headers, exposed files, CORS, database rules, auth per route, dependencies, logs, the game-export note), the ledger line, the workflow entry, bootstrap |
| `reference tools/` | 35 working scripts to adapt, not rewrite. Day one: standup, checkpoint, core lint with a token budget, usage sheet (weighted, with the daily line and the per-arc line), update check, the parent loop (run_all, the loop ledger). Adopt when wanted: tag index, workstation survey, the learning loop (link checker, heat map, ledger trends, big reads), the preservation movers (retire, cold shelf, delete grant), the README gate (parity lint, audit ledger), the intent loop (intent log, correction ledger, intent report, systems audit ledger, open questions), the format law and the purpose audit (format lint, purpose audit, kit refresh), the core diet (core_diet.py, the hot core's mover), trust the ledger for the check scripts, the lesson loop (lesson_log.py: the prompt match, the trial-and-error scan, the lint), the route line (route_index.py: the registry entry and the script a prompt already has, named before the first tool call), the local mirror (backup_push.py: every branch and tag to a bare repo on another drive), the law ledgers (law_gaps.py: the archive sweep and the workflow-rule proxy, WARN lines in the check group), the ship-time version hint (version_hint.py: none, patch or minor from what changed since the last bump; never major), the pre-production security audit (security_audit.py: secret shapes in a build folder, the security headers, the exposed-file paths and the CORS answer of your own deployment, read-only, with a ledger line), the live usage window (usage_window.py: last five hours against the seven-day peak, spoken by the prompt gauge only when it matters, each spoken reading ledgered), the guard replay (guard_replay.py: the guards' judge functions run over the last N days of recorded tool calls, employee sessions included, with the NEW and LOST columns and a ledger line) |
| `UPGRADES.md` | The graft log: kit version + how updates apply to installed projects |
| `CONTRIBUTING.md` | The format law and the purpose audit: the one header every thing carries, the read-only flag ritual, what a contributed update looks like |
| `FLAGS.md` | The flag ledger: every kit thing's latest GREEN / YELLOW / RED, hashed to the version reviewed, tallied, append-only |
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

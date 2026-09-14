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

Kit version: **v1.25** (2026-09-14). The graft log `UPGRADES.md` is the
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
| The standup digest | Once, at session start / after /clear | ~1.6k-2k tokens (was ~4.3k before the digest diet the same evening: only verdicts and moved ledgers print in full) |
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
  line), and WARNS past WARN_TOKENS 1,000. It also requires CLAUDE.md to
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
  index.

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
| The standup digest | Once, at session start / after /clear | ~1.6k-2k tokens (was ~4.3k before the digest diet the same evening: only verdicts and moved ledgers print in full) |
| The wiki (47 files) | NEVER whole. A section at a time, on demand | ~289k tokens ON DISK; ~0 in context |
| Skills | Only the one invoked, when invoked | a few hundred tokens each |
| Hooks | Never (they are scripts; only their one-line output enters) | ~0 |

So a session opens at roughly 4.3k tokens of context for a project whose
written knowledge is ~289k. The core is a sliver of the wiki, and a linter
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
to the master index, leaving one stub line behind, reversible with
`--restore`.

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

### The weighted receipts (50 days, 2026-09-10)

Raw token counts flatter the wrong column. What counts against a plan is
WEIGHTED: input x1, cache write x1.25 (x2 on a one-hour cache), cache read
x0.1 (x0.025 on the model that discounts it), output x5 - the API's own
price ratios. Re-run on those weights, the same machine's 4.2 billion raw
tokens over 50 days were about 366 million weighted, and the split is not
what the raw column suggests:

- Cache READS, the giant raw number, were 41% of the weighted bill. Cache
  WRITES - new context entering the prefix - were 29%, and the model's own
  OUTPUT (prose, edits, thinking) 13%. Fresh input rounds to zero.
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
- **Size before you read (the 10k rule).** A whole-file read past ~10k
  tokens is section-read or handed to an employee; a warn-only hook says
  the file's size and section count at the moment of the read. Editing
  that needs the exact text is the one fair exception.
- **The output diet.** Every emitted token costs five; every tool result
  is written into context at 1.25x and re-read forever. Edit over Write,
  scripts generate documents, nothing restated that a table already says,
  limiters on chatty commands.

- **Nothing is deleted (the preservation law).** Neither the manager nor
  any employee deletes a file, record or tree without the owner's yes
  given twice, and no script is written that deletes. A file RETIRES to a
  shelf folder; a rarely-read wiki section moves VERBATIM to a cold shelf
  with a stub left behind; a wrong fact is marked superseded in place. A
  hook refuses delete verbs, work-discarding git verbs and deletion calls
  written into code; the rare real deletion is recorded with the owner's
  two acknowledgments, word for word, before the one command runs.
- **The wiki learns (the learning loop).** Three read-only scripts close
  the loop: a link checker finds dead cross-references, a heat map mines
  the transcripts for reads per section and says WHY a cold page is cold
  (code moved after the doc was last opened is the only kind worth a
  look; cold by read count is never a reason to shelve), and a trends
  script turns ledger tails into PROPOSE lines at standup when a threshold
  crosses. Nothing is applied by itself; the owner decides.
- **Index first.** The first whole read of a big file in a session is
  refused, and the refusal carries the file's own index (headings or
  function lines with line numbers) so the next call reads one section.
  The same call repeated passes. A per-file ledger names which files were
  read whole and the fix each needs; the manager sections or splits them
  unasked. Pictures are priced by pixels, never by their bytes.

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
- **Ledgers.** Every run appends one labeled line to a history file: date
  and time, machine (or agent), project version, what ran, the result,
  and the failures if any. You read the TAIL, never the whole file, and
  runs compare across versions without re-reading anything.
- **Sheets a human opens get a spreadsheet twin.** The CSV and TXT stay
  for grep and git diffs; the .xlsx has a frozen header, thousands
  separators and a bold total per period. Numbers you cannot read do not
  change behaviour.
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
- **Who gets what.** An assignments table per project maps task types to
  models, cheapest first: the cheapest model runs tests, search sweeps and
  mechanical batch edits; the middle tier implements from a precise spec,
  drafts doc sections and does first-pass review; the strong tier takes
  multi-file refactors and gnarly bugs with a written plan; design,
  architecture, rulings, verification and pushes never leave the manager.
- Every brief is STAMPED (task, date, model), SELF-CONTAINED, and carries a
  budget line: exceed ~30 tool calls or fail the same step twice, and the
  employee stops and reports instead of running up a bill. The report ends
  with the employee's own stamp: model, effort, tokens, confidence, and
  the tools it used.
- **How many at once.** A handful of employees per batch (four is the
  habit), never a burst, never an employee that spawns employees. A task
  that seems to need dozens is a design question for the CEO, not a
  bigger fan-out.
- Employees write files directly and report the diff, never paste bodies.
- **The fabrication check.** Claims must match the diff, and the stamp's
  tool count must match the harness meter: a claimed read or run with a
  metered tool count of zero was invented. This is not hypothetical: the
  method exists because a delegated audit once "classified" a file it
  never opened (93k tokens of fiction, caught for about 2k).
- **The scorecard.** An append-only performance ledger tracks every
  employee task (who delegated, task type, model and effort, metered
  tokens, outcome) with correction tallies. The escalation rule: when a
  task type's corrections pass ~25% of its last ~10 tasks, that task type
  is promoted to a stronger model, with a dated line saying so. Models
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
  when the session gets heavy. At an arc's end the manager pushes,
  refreshes the day file, and emits the marker: "CHECKPOINT - safe to
  /clear. Nothing in this chat exists only in this chat."
- **Standup.** Every fresh session opens with one script that prints the
  last exchange, the state, ledger tails, the open roadmap, and THE BUDGET:
  yesterday's and today's weighted spend judged against the previous seven
  active days, with the reason when something went wrong. A cleared
  session re-arms in about 15-20k tokens instead of dragging hundreds of
  thousands.

Nine rituals ship as Claude Code skills, invocable as slash commands:
`/standup`, `/checkpoint`, `/ship`, `/brief`, `/runaway`, `/preserve`,
`/intent`, `/correct`, and `/flag`
(the preservation law's front: retire a file, shelve a wiki section, or
walk the twice-acknowledged delete grant, in that order). `/ship` is the
one you will use most: sanity-check tests (trusting the ledger), bump the
version if warranted, commit with a player-readable subject, push, run
the build script without deleting old builds, sync the kit if kit files
changed, and export the changelog unprompted.

### The hooks: laws the harness enforces itself (HOOKS_METHOD.md)

A skill runs when invoked; a hook runs when the harness reaches a moment.
Anything a law can enforce mechanically becomes a hook, not a longer
reminder. Ten ship in `hooks/`, wired by one settings file:

- **Session start** injects the standup digest by itself - after a /clear
  the manager has everything back before anyone types a word.
- **Every prompt** carries a silent context gauge that speaks only when a
  threshold is crossed; **every reply** ticks the checkpoint counter when
  work actually happened, and refuses to end the turn once it is dire.
- **Before compaction** a ledger line records what was at stake.
- **The shell guard** refuses what the CEO's laws forbid (no force push, no
  skipped hooks, plus the project's own rules).
- **The fan-out guard** is catastrophe-only: it refuses a burst or flood of
  sub-agent spawns or runaway token velocity - each self-clearing - and
  warns on the rest. It exists because a manager once spawned 821 agents
  on "check my markdown files". The default numbers: 8 spawns in a
  minute, 25 in ten, or 10M weighted tokens in two minutes. The CEO tunes
  them with `/runaway`; the manager never raises one on its own.
- **The diet guard** says a file's size before a whole read past ~10k
  tokens and the missing limiter on a chatty command, at the moment of
  the decision; the first whole read of a big file per session is
  refused with the file's own index in the refusal, and the same call
  repeated passes.
- **The preserve guard** refuses delete verbs, work-discarding git verbs
  and deletion calls written into scripts. The session scratchpad and
  prose files pass; one command passes per delete grant the owner
  acknowledged twice. A drive root, the home folder or the repo root pass
  never.
- **The hygiene guard** runs AFTER every file edit and says the law that
  applies to that file: refresh the kit copy (and this README) when a
  portable original changes, add the missing See-also line to a wiki
  section, fix a forbidden character in player-facing text (the one
  block), run the engine import after a new asset. It exists because
  this README once fell two versions behind while the law to refresh it
  was already written.
- **The format guard** runs BEFORE an edit of the settings file and
  refuses one that would unwire, narrow or mis-point a safety hook (or
  not parse), and AFTER every edit of a kit thing, blocking one that
  leaves the thing without its header (PURPOSE, INTENT, search keys, see
  also) with the rewrite command in the reason. The shell guard refuses
  shell writes into a settings file and the Stop hook refuses to end a
  turn while the live wiring is broken, so no prompt, brief or contributed
  patch switches a guard off quietly. It exists because a community kit
  needs a guardrail that does not depend on the reader's good faith.

The contract, plainly, because a worried reader asks these first:

- **Hooks need Claude Code.** They are wired through `.claude/settings.json`,
  which is Claude Code's mechanism. In another client (the Claude app,
  Cowork, an IDE plugin) the laws are prose again; the wiki and the
  rituals still work, the enforcement does not.
- **A hook cannot trap you.** The Stop hook refuses to end a turn once per
  threshold crossing, re-blocks only every five further tasks, and checks
  the harness's own loop flag so it can never refuse forever. Every other
  refusal is one command, with the reason printed; the next command runs.
- **A broken hook CAN lock you out**, which is the one real hazard: a
  hook that exits with the blocking code (a mis-typed path, a missing
  interpreter) refuses every tool call, not just the one it meant to
  guard. The fix is one line in settings.json; every kit hook answers
  `--selftest` and is tested by piping a fake event into it before it is
  wired.
- **Turning one off** is removing its line from settings.json. No hook has
  state that survives being unwired.
- **Cost.** Tokens: none (a hook is a script; only its one-line verdict
  enters the context). Time: one interpreter launch per trigger, about
  0.3 seconds, and a shell command runs four of them in a row.
- **What is not built yet.** Two ideas wait on the pin board: a hook that
  refuses an employee's report when its stamp is missing, and a
  notification hook that toasts the OS when the manager is waiting on
  you. Neither ships until the CEO asks.

### The intent loop (INTENT_METHOD.md)

A rule tells Claude what to do; the reason tells it what to do in the
case the rule never named. So every ruling gets a section in the
project's INTENT.md: the owner's ask verbatim, the owner's numbered
reasons verbatim, the manager's reading marked as the manager's, and
where the rule lives. Before building, the manager logs its OWN reading
of the ask; employees state theirs in a stamp line. When the owner's
intent is known, the claim resolves SAME, SIMILAR or DIFFERENT, with its
source named (stated, revealed by a correction, or self-judged, which is
counted apart so it never inflates the rate). A script turns that log
into day, week and month agreement rates per actor, a text file for
Claude and a spreadsheet for you, and calls the trend improving, steady
or declining. The owner's reason, in the owner's words: real data, past
against present, and a trend that says whether the feedback loop works.

`/correct` closes the loop from the other side: it asks what about the
last thing needs correcting, records your words verbatim, marks the
claim DIFFERENT, then asks "What was the intent?" and `/intent` files
the why while the mismatch is fresh. A systems audit, ledgered and
proposed on a cadence, has read-only employees look at tokens, process,
knowledge and shipped features and return proposals only. Nothing in
this loop applies anything by itself; the owner decides.

The first systems audit ran on 2026-09-13 (kit v1.21). Four read-only
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
  a method file, the front door) carries one header: `PURPOSE:` (what it
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
  a guard, unbounded spend) and the owner sees it before it ships. The
  ritual is read-only, then flag, then explain: the auditor never edits
  the thing in the audit turn. `FLAGS.md` is the one committed file that
  references every flag, hashed to the exact version reviewed, tallied at
  the top, and open to any reviewer's findings by pull request. The
  tally's stamp moves only when a flag moves, never on a no-change run,
  so the mirror check never warns over noise. `/flag`
  walks the ritual; `purpose_audit.py --pending` lists what needs one.
  The kit's own first audit (v1.19) flagged 58 things: 53 green, 5
  yellow, 0 red. v1.20 closed all five the next morning, one of them by
  the first independent read of the front door, which found the header
  undersold what the file installs. Three author passes had missed it.

`CONTRIBUTING.md` carries both laws in full, plus what a contributed
update looks like (the header, the graft-log entry, a passing lint, a
flag from someone other than the author, nothing deleted).

### The two companions (WORKFLOW_METHOD.md, WORKSTATION_METHOD.md)

Two smaller disciplines ride with the pillars. Neither saves tokens
directly; both stop a kind of amnesia.

- **The process registry.** A project accumulates multi-step processes
  (the ship order, an art pipeline, a retune round-trip) that nobody
  writes down, so the sequence is re-derived from memory or a vanished
  chat, and a step gets skipped. WORKFLOWS.md holds ONE runbook entry per
  repeatable process: WHEN it applies, the STEPS with the scripts named,
  how to VERIFY. The capture rule: before any such task the manager checks
  the registry; a stale entry is a bug fixed in the same batch; a missing
  entry is a gap the performer writes up in the same batch (transcription
  work, so it goes to the cheapest model). Employees never edit it; they
  report gaps on their stamp line.
- **The workstation inventory.** One document listing every package,
  tool, path and setting the project's scripts and hooks depend on, split
  REQUIRED and OPTIONAL, with the need, the why, and the install command
  for each, plus a survey script that proves a machine up to par. A second
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
writes the session record by hand. And the methods are worth taking a la
carte - the day-file ritual, the append-only ledgers, and the brief rules
(stamped, self-contained, budgeted, claims-must-match-the-diff) each stand
alone. An honest partial install beats a pretend full one.

**Installing into an existing project?** The front door's BROWNFIELD RULE
applies: Claude inventories what you already have (your own split
knowledge files and logging scripts count as installed pieces), proposes a
mapping, and gets your approval before touching any existing file. It
never restructures a live repo unasked.

## Quick start

1. Give this repo's contents to Claude (Claude Code, any capable model).
2. Say: **read "0 - READ ME FIRST.md" and install the kit.**
3. Answer its STEP 0 questions: project, engine and repo; who manages and
   which employee models are available; one workstation or several; which
   domain-notes files apply; and your update policy (ask, auto, relevant
   or never).
4. Claude builds the operating system in order: wiki, reporting and the
   session rituals, delegation, skills, hooks, the process registry and
   the workstation inventory.
5. It finishes with a definition of done you can verify yourself: the
   standup script runs clean, the lint passes, the resulting CLAUDE.md
   lands under Anthropic's 200-line target and the lint keeps it there,
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
  to GRAFT it onto an existing install, and which README section it
  touched (so a concept cannot ship without deciding whether this page
  needs to know).
- This page is checked, not trusted. A parity lint derives every count on
  it (laws, skills, hooks, scripts, the box table, the version line) from
  the kit's own files, and the kit's publish script refuses to push while
  any of them disagree. A ledgered audit cadence proposes a fresh
  cross-reference, by employees who read every method file against this
  page, whenever the kit has moved far enough since the last one.
- Installing stamps a line into the project's CLAUDE.md:
  `Rootstock vX.Y installed <date> | updates: <policy>`.
- To update: pull this repo (or hand Claude the new folder) and say
  **update rootstock**. Claude reads the graft log's entries newer than
  the project's stamp, applies each concept to the project's OWN files in
  its own names and voice, and bumps the stamp. Anything that would
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
  or 200 lines and warns past 1,000 tokens.
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
  The only network call is the optional weekly fetch of this repo's graft
  log, and nothing about your project leaves your machine.
- **Can I take part of it?** Yes; see "What you need" above. The wiki
  conventions alone are the biggest single saving.
- **Can I use it commercially?** MIT. Yes.
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
| `REPORTING_METHOD.md` | Scripts + ledgers: the three rules, runner spec, bootstrap |
| `SUBAGENT_METHOD.md` | The delegation company: org chart, seven laws, assignments table, scorecard, bootstrap |
| `SKILLS.md` | The skills shelf: what each ritual-skill does and the skills rule |
| `skills/` | The nine skills, ready to drop into `.claude/skills/` |
| `rules/` | The first path-scoped rule, `wiki.md`: drop into `.claude/rules/`, loads only while a markdown file is open; write your own game and text rules beside it |
| `HOOKS_METHOD.md` | The hooks: the contract, the ten kit hooks, tiers, bootstrap |
| `hooks/` | The ten hook scripts (drop into `tools/hooks/`) plus the settings template (merge into `.claude/settings.json`) |
| `WORKFLOW_METHOD.md` | The process registry: one runbook entry per repeatable task, the capture rule |
| `WORKSTATION_METHOD.md` | The machine inventory: document, survey script, new-machine runbook |
| `INTENT_METHOD.md` | The intent loop: the why file in the owner's words, the claim-and-verdict ledger, the correction ritual, the agreement report, the systems audit, bootstrap |
| `reference tools/` | 27 working scripts to adapt, not rewrite. Day one: standup, checkpoint, core lint with a token budget, usage sheet (weighted, with the daily line and the per-arc line), update check, the parent loop (run_all, the loop ledger). Adopt when wanted: tag index, workstation survey, the learning loop (link checker, heat map, ledger trends, big reads), the preservation movers (retire, cold shelf, delete grant), the README gate (parity lint, audit ledger), the intent loop (intent log, correction ledger, intent report, systems audit ledger, open questions), the format law and the purpose audit (format lint, purpose audit, kit refresh), the core diet (core_diet.py, the hot core's mover), trust the ledger for the check scripts |
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

# UPGRADES.md - the graft log (how Rootstock updates without overwriting)

PURPOSE: The append only graft log: every kit concept update, recorded as
  WHAT it is, which kit files CARRY it, how to GRAFT it onto an installed
  project's own files, and which README section it touched, so installs
  update by concept rather than by overwriting a project's customized files.
INTENT: an installed Rootstock is an adaptation, not a copy, so the kit must
  never update a project by overwriting its files; this log is the one place
  updates travel as grafts instead.

CURRENT KIT VERSION: **v1.28** (this file is the single source of truth for
the kit's version; entries below are append-only, oldest first).

Search keys: updates, upgrade, graft, version, pull changes, kit update.

## Why updates are GRAFTS, never file copies

An installed Rootstock is an ADAPTATION, not a copy: the receiving Claude
renamed paths, tailored CLAUDE.md, rewired scripts, and the project has
since grown its own knowledge INTO those files. Copying a newer kit file
over an installed one would destroy exactly the thing the system exists to
protect. So the kit never updates files in a project - it updates CONCEPTS.
Each entry below is a scion: the idea, where it lives in the kit, and how
to graft it onto a project's own files, whatever they are named there.

## THE GRAFT PROTOCOL (for the Claude performing an update)

1. Find the installed version: the project's CLAUDE.md carries a line
   "Rootstock vX.Y installed <date> | updates: <policy>" (an install that
   predates version marks counts as v1.0 - add the line while you are
   there). The POLICY word is the CEO's standing answer to "should I
   update?": **ask** (default - present newer grafts, CEO picks), **auto**
   (graft everything newer, report after), **relevant** (offer only grafts
   that benefit THIS project; record skips so they are never re-offered),
   **never** (check only when the CEO explicitly asks). The CEO changes it
   any time by saying so ("update automatically", "stop asking about
   updates", "only show me relevant updates").
2. Get the current kit (the CEO hands you the folder, or pull
   github.com/Mazhron/rootstock-os) and read THIS file's entries NEWER
   than the installed version.
3. For each entry, in order: read its GRAFT instructions, then apply the
   concept to the project's OWN files - additive edits in the project's
   own names, paths, and voice. NEVER copy a kit file over an existing
   project file. A file the project does not have at all (a genuinely new
   MD or reference script) may be copied fresh, then adapted and indexed.
4. If a graft contradicts something the CEO customized on purpose, THE
   CONTRADICTION RULE applies: flag it, ask, never silently overwrite
   their choice with ours.
5. Bump the project's "Rootstock vX.Y installed" line to the new version
   and ship the batch. One graft batch per update; the project's own
   changelog records what was grafted.

## The entries

Every entry carries WHAT (the concept), CARRIES (the kit files that hold
it), GRAFT (how it lands on an installed project's own files) and, from
v1.17 on, README (the public-README section the concept touched, or
"none, wording only" - the parity lint refuses a newest entry without it).

### v1.0 - 2026-09-03 - The public release
WHAT: the four pillars as first published: the knowledge wiki
(WIKI_METHOD.md), the reporting discipline (REPORTING_METHOD.md), the
delegation company (SUBAGENT_METHOD.md), the skills shelf (SKILLS.md +
skills/), the front door install order, and the verbatim checkpoint law
(both sides of the final exchange, exact words).
CARRIES: every kit file at publication.
GRAFT: not applicable - this is the baseline an install starts from.

### v1.1 - 2026-09-03 - The usage sheet
WHAT: the harness transcripts (~/.claude/projects/) meter every request
for real - model, input/output/thinking tokens, cache reads/writes, every
tool call named, sub-agents included. A miner script aggregates them into
one regenerated CSV+TXT sheet: totals per day/week/month per model and
per tool, workstation-keyed. Ends self-estimated token figures; shows
where context money actually goes (first finding: file Reads dwarf
everything - the wiki diet is the lever).
CARRIES: REPORTING_METHOD.md section "The usage sheet: mine the harness
meter, never self-estimate"; reference tools/usage_report.py; front door
STEP 2 paragraph.
GRAFT: copy usage_report.py fresh into the project's tools/, adapt its
output paths + the project-name filter in transcript_dirs(), add it to
the project's runner/metrics group, and add the section to the project's
copy of REPORTING_METHOD.md (or its local equivalent). Nothing existing
is touched.

### v1.2 - 2026-09-03 - The graft log itself
WHAT: this update mechanism. The kit carries a version and an append-only
log of concept entries; installs carry a "Rootstock vX.Y installed" line
in CLAUDE.md; updates are performed by grafting newer entries onto the
project's own files per the protocol above.
CARRIES: UPGRADES.md (this file); front door STEP 1 (the version line) +
the UPDATING section.
GRAFT: add the "Rootstock v1.2 installed" line to the project's CLAUDE.md
index. Do NOT copy this file into projects - the graft log lives in the
KIT only, where it stays current; a project needs just its version line.

### v1.3 - 2026-09-03 - The update check + the update policy
WHAT: projects stop discovering updates by luck. A small script reads the
project's install stamp, fetches the kit's UPGRADES.md (local clone or
the public repo over HTTPS), compares versions, prints any newer grafts,
and states what the CEO's update POLICY (ask/auto/relevant/never, kept in
the stamp line) tells the manager to do. Checks are rate-limited to
weekly, never fail offline, and ledger one line per check; wired into
standup, the reminder rides an existing habit instead of being one more
thing to remember.
CARRIES: reference tools/rootstock_update_check.py; the protocol's stamp
+ policy wording above; front door STEP 1 stamp + UPDATING section.
GRAFT: copy rootstock_update_check.py fresh into the project's tools/,
adapt STAMP_FILE/KIT_CLONE at its top, add it to the project's standup
script or runner group, and extend the project's stamp line with
"| updates: ask" (or the CEO's chosen policy - ask them once).

### v1.4 - 2026-09-03 - The last exchange from ground truth
WHAT: standup's verbatim replay of the final exchange (CEO's last prompt +
manager's last response) no longer depends on the day file, which is only
as fresh as the last checkpoint - a mid-arc /clear used to replay a STALE
or condensed exchange (it failed three times in one day before this).
Standup now mines THE LAST EXCHANGE directly from the harness transcripts
(~/.claude/projects/<slug>/*.jsonl, the same ground truth the usage sheet
meters): newest assistant text reply + the user prompt before it, skipping
tool results, command wrappers, and the standup trigger itself. Word for
word, image attachments counted, immune to manager discipline. The
day-file WHERE WE LEFT OFF remains the committed, searchable record.
CARRIES: reference tools/standup.py (print_last_exchange + the transcript
helpers); skills/standup + skills/checkpoint SKILL.md wording; front door
STEP 2 (both the script bullet and the protocol paragraph).
GRAFT: copy the _slug/_transcript_files/_mine_exchange/print_last_exchange
block from reference tools/standup.py into the project's standup script
and call it first; refresh the project's standup + checkpoint skills from
the kit's skills/ copies. Nothing else changes.

### v1.5 - 2026-09-03 - Honest prerequisites + the brownfield rule
WHAT: the first outside review (a stranger's Claude, fed the repo) found
two assumptions the kit never stated - it expects git and Claude Code -
and a real hazard: "install the kit" pointed at a live production repo
invited an unapproved restructure. Now written down: the front door opens
with WHAT THE FULL KIT ASSUMES; STEP 0 gains THE BROWNFIELD RULE
(inventory first, adopt what already exists under other names, propose
the mapping, get explicit CEO approval before editing anything existing,
never a stop-the-world restructure, production-sensitive files
untouchable without a named go-ahead) and MISSING PREREQUISITES (no git
or no Claude Code = a PARTIAL install of the pieces that stand alone,
skips recorded in the install stamp). reference tools/standup.py now
degrades instead of crashing when project.godot, git, CLAUDE.md, or
NEXT_STEPS.md are absent. README gains "What you need (and what still
works without it)".
CARRIES: front door (assumes block + the two STEP 0 rules); reference
tools/standup.py; the kit repo's README.
GRAFT: nothing to apply to healthy installed projects - this entry
protects FUTURE installs. If a project was installed partially, add the
skip markers to its stamp line (e.g. "| no-git") so update checks stop
offering machinery it cannot run.

### v1.6 - 2026-09-05 - The workflow registry (process amnesia killed)
WHAT: the kit remembered commands (the Script Rule) and results (ledgers)
but not CHOREOGRAPHY - the ORDER of a multi-step process. The origin
project ran an art pipeline for weeks with no written recipe and let seven
versions pile up unexported before noticing; after a /clear, order of
operations was re-derived from chat that no longer existed. Now:
WORKFLOWS.md at the repo root is THE PROCESS REGISTRY - one WHEN/STEPS/
VERIFY runbook entry per repeatable multi-step process, pointing at deep
docs rather than duplicating them. THE CAPTURE RULE: whoever performs a
process checks the registry first; a stale entry is a bug fixed in the
same batch; a missing entry is a WORKFLOW GAP captured in the same batch.
Employees never edit the registry - their stamp gains a WORKFLOW line
("matched <entry> | GAP: <uncovered process>") and the manager files the
gap or delegates the write-up to the cheapest model (a write-up is
transcription of the performer's own report, not discovery).
CARRIES: WORKFLOW_METHOD.md (the portable method + entry template +
bootstrap); front door STEP 1 (create the registry) and STEP 3 (the
WORKFLOW stamp line); skills/brief SKILL.md (compose item 5 + the
after-return gap step).
GRAFT: copy WORKFLOW_METHOD.md fresh to the project's repo root and index
it; create the project's WORKFLOWS.md seeded by transcribing its existing
processes (cheap-model work from existing docs and scripts); add the
WORKFLOW line to the stamp template in the project's SUBAGENTS.md
equivalent plus a cheap-tier "workflow write-up" row to its assignments
table; refresh the project's brief skill from the kit copy; add the
capture rule to the project's standing laws in its own voice.

### v1.7 - 2026-09-06 - The hooks (laws the harness enforces itself)
WHAT: every ritual ran from the manager's memory and every law was prose;
after a /clear the CEO had nothing until someone typed "standup", the
checkpoint counter ticked only when remembered, "never delete a build
zip" was a sentence. Claude Code HOOKS - scripts the harness runs at fixed
moments - fix the class. Five ship: SessionStart injects the standup
digest (startup/resume/clear/compact); Stop ticks the checkpoint counter
only when work happened (HEAD or tree-status fingerprint) and REFUSES to
end the turn once at DIRE; UserPromptSubmit prints the context gauge only
when a threshold is crossed; PreCompact ledgers every compaction;
PreToolUse on the shell tools denies what the laws forbid (generic:
--no-verify, plain force push; project block: the origin's build-zip,
runner-only, commit-dash and resource-file rules as templates). THE HOOKS
RULE: a law the harness can enforce mechanically gets a hook, not a
reminder. Manual --tick is retired (double-counts). Tier 3/4 ideas
(wiki/kit hygiene on Write|Edit, subagent stamp check, OS toasts) are
recorded in HOOKS_METHOD.md and the origin project's pin board.
CARRIES: HOOKS_METHOD.md (contract, the five hooks, tiers, bootstrap);
hooks/ (five scripts + _hooklib.py + settings.json template); reference
tools/checkpoint.py (work_fingerprint + hook state, reset stores the
fingerprint); skills/standup, checkpoint, ship (hook-aware wording); front
door STEP 4 (hooks install with the skills).
GRAFT: copy hooks/ into the project's tools/hooks/ (or its scripts folder;
the scripts find the repo root from their own path and import the
checkpoint script from the folder above); adapt bash_guard.py's PROJECT
RULES block to the CEO's laws; install hooks/settings.json as
.claude/settings.json (MERGE into an existing one, never replace arrays);
gitignore .claude/hooks_state.json; add work_fingerprint /
load_hook_state / save_hook_state to the project's checkpoint script (or
copy the reference one); reorder its checkpoint ritual so --reset runs
LAST; strike every "tick by hand" instruction from laws and skills;
pipe-test each hook; add the registry entry "Add or change a harness
hook" and a "The hooks" section to the tooling doc; index HOOKS_METHOD.md.

### v1.8 - 2026-09-06 - The workstation inventory (a machine that installs itself)
WHAT: the whole kit assumes tools already run - Python for scripts and
hooks, the engine for tests and builds, the art programs - and nothing
recorded what they were. A second machine, a reinstall or a
collaborator's laptop meant rediscovering the setup from error messages.
THE WORKSTATION RULE: the project keeps ONE workstation document
(requirement tables with the WHY per row + the install move, split
REQUIRED/OPTIONAL, the non-needs too, one section per known machine with
its deltas, the on-disk layout, and the harness's own settings); every
new dependency is written back to it in the same batch; a survey script
mirrors the tables and prints HAVE/MISSING, exits non-zero on a missing
required item, and ledgers one line; a new machine installs from the
document and is "up to par" when the survey says so. Machine paths go
through candidates + env override, never a lone hardcoded string.
CARRIES: WORKSTATION_METHOD.md (the rule, the table columns, per-machine
sections, bootstrap - including THE ASK: the receiving Claude surveys the
CEO's current machine and writes the first inventory from what it finds);
reference tools/workstation_survey.py (a working CHECKS-table probe with
ledger line; rewrite its rows); front door STEP 2 (the survey installs
with the reporting scripts).
GRAFT: create the project's workstation document from a survey of the
machine you are on (versions, paths, extensions, harness settings) plus
the CEO's answers for what you cannot see; copy the reference survey and
rewrite CHECKS to match; wire it into the parent loop's check group; add
the registry entry "Bring a new workstation up to par"; index the doc in
CLAUDE.md and add the write-back rule to the standing rules.

### v1.9 - 2026-09-10 - The fan-out guard (a runaway the manager cannot cause)

WHAT: a publicly reported catastrophe - a manager asked to "check my
markdown files for consistency" spawned 821 sub-agents and burned 50M+
tokens in thirty seconds - is the one mistake that outspends a month of
work in one turn. The delegation method gains LAW 6, THE FAN-OUT LAW:
sub-agents are spent money; a batch is a handful of parallel employees,
a session a dozen, never a burst, never an employee that spawns
employees, bulk-orchestration tools only at the CEO's per-use word; a
task that seems to need more is a design problem, never a bigger
fan-out. And because a law the manager can forget is not a guard rail,
the hooks gain TIER 2b: a PreToolUse hook on EVERY tool that meters the
session's spend from the transcript and refuses ONLY the runaway shapes
- a burst of spawns inside a minute, a flood inside ten, or token
velocity no real work produces - each clearing itself after a cooldown,
and warns the CEO (a system message) on everything else: spawn count,
session spend, velocity, the orchestration tool. CATASTROPHE-ONLY by
the origin CEO's ruling, hours after a strict first cut (session caps,
locks, CEO-only unlock commands) proved to be a rail on the path
instead of the cliff edge: "I don't want to have to type these commands
all the time and neither will any users who use Rootstock-os. I just
wanted to prevent complete runaway agents and gigantic token spend."
CARRIES: SUBAGENT_METHOD.md law 6; HOOKS_METHOD.md Tier 2b (+ the
cliff-edge lesson in its change log); hooks/fanout_guard.py (the guard,
LIMITS at the top, `--status` / `--resume` / `--selftest`);
hooks/settings.json (the every-tool PreToolUse entry); skills/brief
step 6 (the fan-out check before dispatch); front door THE HOOKS
paragraph.
GRAFT: add law 6 to the project's delegation rules and the fan-out check
to its brief skill; copy fanout_guard.py into the project's hooks
folder, set LIMITS with the CEO (the defaults never fire on real work),
run `--selftest`, gitignore `.claude/fanout_state.json`, wire the
every-tool PreToolUse entry, pipe one real tool call through it; add the
standing rule to the core instructions file and the row to the tooling
doc's hooks table. Nothing for the CEO to type afterwards - that is the
point.

### v1.10 - 2026-09-10 - The runaway numbers belong to the CEO
WHAT: the fan-out guard's limits stop being constants the manager edits
and become the CEO's setting. The origin CEO's ask, hours after the
catastrophe-only ruling: a skill "that allows the user to tune their
own runaway numbers. Calling the skill will give the current numbers
and then allow for changes." The script keeps DEFAULTS; the CEO's tuned
numbers live in a committed `.claude/fanout_limits.json` that overlays
them per key (junk falls back, a missing file means defaults), so a
kit graft never overwrites what the CEO chose. The guard grows
`--limits` (every number current vs default with its one-line meaning),
`--set key=value ...` (refusing a warn step above its halt, writing
nothing on any error) and `--defaults`; its self-test always runs at
DEFAULTS so tuning cannot fail it. The /runaway skill is the
conversational front: show, ask, set, selftest, commit. Only the CEO
tunes; the manager never raises a limit to get past a refusal.
CARRIES: hooks/fanout_guard.py (DEFAULTS + MEANING + load_limits /
set_limits / limits_table, the three flags, six new self-tests);
skills/runaway/SKILL.md; SKILLS.md shelf entry; HOOKS_METHOD.md Tier 2b
("THE NUMBERS ARE THE CEO'S") + change log; SUBAGENT_METHOD.md law 6
(the numbers clause); skills/brief step 6 (never raise a limit to get
past a refusal); hooks/README.txt; front door STEP 4 + THE FAN-OUT
GUARD paragraph.
GRAFT: replace the project's fanout_guard.py with the kit's (keep any
project wording; if the project had edited LIMITS by hand, move those
values into .claude/fanout_limits.json with `--set` and let the script
return to DEFAULTS); copy skills/runaway; add the shelf entry and the
law 6 clause; commit the JSON file (it is NOT gitignored - that is the
point); run `--selftest` and `--limits` once.

### v1.11 - 2026-09-10 - The spreadsheet rule (a sheet a human opens is an .xlsx)
WHAT: the origin CEO opened the usage CSV in Excel and asked for what no
CSV can carry - a frozen header row, thousands separators on every token
column, bold TOTAL rows in line under each period's last record with the
averages beside them, and a thick border under each total so the periods
read apart - "I want future Rootstock users to have their Claude
automatically do this when their Claude builds it." So THE SPREADSHEET
RULE joins the reporting method: any script producing a sheet a person
will open also writes an .xlsx twin in that shape (CSV/TXT stay for grep
and diffs), degrading to CSV-only with a printed note when the library is
missing. The reference usage sheet also grew THE BREAKDOWNS the same day:
averages per request, the context-window "box" (input + cache read +
cache written per request, average and biggest, by month), averages per
tool call, and per-employee runs (one sub-agent transcript = one run,
with its brief's first line) in their own CSV.
CARRIES: REPORTING_METHOD.md "THE SPREADSHEET RULE" section; reference
tools/usage_report.py (write_xlsx / _xlsx_sheet, the breakdowns, cache
v2, TOTAL rows last in their period, total_tok / avg_tok columns); front
door STEP 2 reference-tools paragraph; the openpyxl row for the
workstation inventory + survey.
GRAFT: add the rule section to the project's reporting doc; give every
human-opened sheet an .xlsx writer per the section's mechanics (or adapt
the reference script's two functions); add openpyxl to the workstation
inventory + survey CHECKS; run the sheet once and open the .xlsx to see
the frozen header and the ruled totals.

### v1.12 - 2026-09-10 - The weighted column, the comparison rule, and the diet guard
WHAT: the origin CEO's insight that only BUDGET-WEIGHTED tokens matter
("It's cool to see I used 200 million tokens, but my budget is only being
hit by 5 million. That should be the concept for any of the pillars"),
built end to end the same day. (1) THE WEIGHTED COLUMN: the usage sheet
prices every token by the API's own ratios (input 1, cache write 1.25 /
2 on the 1-hour cache, cache read 0.1 or 0.025, output 5) and makes that
the headline; raw is trivia beside it; the fan-out guard meters with the
same read weight per model. (2) CACHE MISSES counted and priced: a
request after a session's first whose cache write is most of its prompt
is a prefix rewrite - the origin's all-time waste was 24% of its budget.
(3) THE COMPARISON RULE ("a number without comparison means nothing"):
a daily line file, one line per active day judged against the previous
seven - weighted spend, misses, heavy whole-file reads, section-read
share - with a CHECK / normal / LOW verdict and the reason named; standup
prints its tail as THE BUDGET block and a CHECK is relayed verbatim.
(4) THE READ DIET (the 10k rule) and THE OUTPUT DIET (every emitted token
costs 5x) become law in the wiki method; the delegation method gains the
10k delegation line. (5) THE DIET GUARD (hooks/diet_guard.py, Tier 2c):
warn-only PreToolUse on Read|Bash|PowerShell - says a file's size and
sections before a whole read past 10k tokens, and the missing limiter on
a chatty shell shape (git log without a count, bare git diff, recursive
listings, noisy installs), capped per session. Never a refusal.
CARRIES: reference tools/usage_report.py (weighted, misses, read-diet
classes, pillar/diet sections, usage_daily.txt, --quiet, cache v3);
reference tools/standup.py (print_budget, --no-usage); reference
tools/checkpoint.py (usage outputs in FP_IGNORE); hooks/diet_guard.py +
settings.json entry + hooks/README.txt; hooks/fanout_guard.py
(READ_MULT); WIKI_METHOD.md "The read diet" + "The output diet";
REPORTING_METHOD.md "THE WEIGHTED COLUMN + THE COMPARISON RULE";
SUBAGENT_METHOD.md "THE 10k LINE"; HOOKS_METHOD.md Tier 2c + bootstrap
step 7 + change log; SKILLS.md + skills/standup (THE BUDGET block); front
door STEP 2 + THE DIET GUARD paragraph.
GRAFT: add weighted_tok (and the miss columns) to the project's usage
sheet per the reporting section, or adapt the reference script's
weighted() / daily_lines(); have standup print the daily line's tail;
exclude the sheet's outputs from the checkpoint fingerprint; copy
hooks/diet_guard.py fresh (nothing project-specific in it), wire its
PreToolUse entry, run --selftest, gitignore .claude/diet_state.json;
add the two diet sections to the project's wiki method and the 10k line
to its delegation method; if the project's fan-out guard predates this,
add READ_MULT so its meter agrees with the sheet.

### v1.13 - 2026-09-10 - Advised means do it (the checkpoint advisory becomes the act)
WHAT: the origin CEO, seeing a CHECKPOINT ADVISED line relayed for the
second prompt running: "If a checkpoint is advised, you should do it.
That way if you advise a checkpoint a user doesn't need to ask you to
checkpoint, they can simply clear. If the checkpoint is a script, there
is no reason not to just run it at the time a checkpoint is advised."
So an ADVISED line from the prompt gauge or the Stop hook is an
instruction: the manager runs the checkpoint ritual at the end of that
reply, unprompted, provided the arc is closed and the tree is committed;
the CEO then simply /clears. Mid-arc, the manager finishes the current
step, ships it, and checkpoints before taking new work. The hooks' own
wording changed to match ("checkpoint at the end of this reply if the
arc is closed" instead of "suggest ... at the next arc boundary"). The
honest limit stays: the day file stores the manager's final reply word
for word, which no script can see before it is sent, so the script does
the mechanics and the manager writes the two paragraphs.
CARRIES: skills/checkpoint/SKILL.md (the rule at the top + the gauge
paragraph); hooks/prompt_gauge.py + hooks/stop_tick.py (ADVISED
wording); HOOKS_METHOD.md Tier 1 item 2 + change log; SKILLS.md change
log; the origin's core-file checkpoint protocol.
GRAFT: add the ADVISED MEANS DO IT paragraph to the project's checkpoint
skill and its checkpoint law; reword the project's gauge/stop hook
ADVISED strings so they say "checkpoint at the end of this reply if the
arc is closed" (keep the project's own owner name); nothing else moves.

### v1.14 - 2026-09-10 - The preservation law, the cold shelf, the learning loop
WHAT: two of the origin CEO's asks in one evening. (1) THE PRESERVATION
LAW, after public reports of an agent whose script deleted a person's
files and another that wiped a machine: "You nor any of your employees
should ever delete a file, record, etc. without express permission from
the user. There should be no script created to delete either (without
express permission of the user and a complete, double acknowledged
approval of such)... We never want to lose knowledge, all of this is
hard fought, hard earned knowledge, even the rarely used knowledge."
Hence hooks/preserve_guard.py (Tier 2d, a refusal on delete verbs,
work-discarding git verbs and deletion calls written into scripts;
scratchpad and prose pass; one command per double-acknowledged grant;
drive roots / home / repo root never), reference tools/delete_grant.py
(the four verbatim texts, single use, ledgered), reference
tools/retire.py (files move to a shelf folder, ledgered) and reference
tools/cold_shelf.py (rarely-read wiki sections move to docs/cold/
verbatim with a stub at the old heading and an index; --restore
reverses). (2) THE LEARNING LOOP, after "does Rootstock learn?": three
read-only scripts - check_wiki_links.py (dead See-also targets),
wiki_heat.py (read counts per wiki section mined from the harness
transcripts; the cold candidates), ledger_trends.py (ledger tails vs a
thresholds table -> PROPOSE lines printed at standup; nothing applied,
the CEO rules). The audit the law forced found the kit-mirror script
emptying its target before copying; it now refuses a target whose
README does not name the kit and reports stale files instead.
CARRIES: hooks/preserve_guard.py + hooks/settings.json (its PreToolUse
entry) + hooks/README.txt; reference tools/{delete_grant, retire,
cold_shelf, check_wiki_links, wiki_heat, ledger_trends}.py;
HOOKS_METHOD.md Tier 2d + bootstrap step 8 + change log; WIKI_METHOD.md
"The cold shelf" + "The learning loop"; SUBAGENT_METHOD.md law 7;
skills/brief (THE PRESERVATION LINE, step 7); SKILLS.md change log; the
front door's STEP 4 hooks block.
GRAFT: copy the guard + wire its entry + selftest + gitignore the grant
file; copy the three movers and the three loop scripts into tools/ and
wire the loop scripts into the project's check/metrics groups and its
standup (the trends block prints after the budget block); add law 7 to
the project's delegation rules and the preservation line to its brief
skill; add the two registry entries (delete ritual; retire/cold shelf);
give the core file a one-line index entry for docs/cold/INDEX.md and the
law's paragraph. Then AUDIT existing scripts for deletion calls and
bring each to the CEO - convert to a move, or keep with the CEO's word
recorded. Nothing else moves; a project's own shelf folder name and
thresholds are its own.


### v1.15 - 2026-09-10 - Index-first reads, pictures priced by pixels, why cold is cold
WHAT: three corrections to the learning loop, all born the evening the
loop's first proposals were audited. (1) INDEX FIRST in the diet guard:
the first whole read of a big file per session is refused and the
refusal carries the file's own index (headings or function lines with
line numbers, capped at 80); the same call repeated passes with a
warning - the CEO's "section or split ... should not require my
approval" made mechanical. (2) The usage sheet prices an image read by
PIXELS (~w*h/750 after the API downscale, ~1-2k tokens), never by its
base64 bytes: the old sizing made every screenshot a 100k "big read"
and the sheet proposed diet fixes for a habit nobody had. A per-file
big-reads ledger (tools/big_reads.py) names WHICH files were read whole
and the fix each needs; the manager acts on it unasked. (3) The heat
map says WHY a cold file is cold (git activity in the code area it
documents: active-unread / current / dormant / process / reference /
archive) and a whole-file read counts as seeing a section; only
active-unread ever reaches a proposal - cold by read count is never a
shelf reason (the CEO: game work touches certain files at certain times;
the wiki is a human reference too). Trends proposals count only
diet-named CHECKs and judge big reads on the last three active days.
CARRIES: hooks/diet_guard.py (INDEX FIRST, image silence, selftest);
reference tools/{usage_report, wiki_heat, ledger_trends, big_reads}.py;
HOOKS_METHOD.md Tier 2c + change log; WIKI_METHOD.md "The read diet"
(index first, the measurement lesson) + "The cold shelf" (why cold).
GRAFT: refresh the diet guard and run its selftest; copy big_reads.py
into tools/ and add it to the metrics group; if the project's usage
sheet sizes tool results, add image_tokens and bump its cache version;
give wiki_heat an AREA_MAP for the project's own doc->code areas (the
kit copy carries Everwood's as the worked example - replace it); reword
the project's cold proposal to active-unread only. Nothing else moves.

### v1.16 - 2026-09-11 - The hygiene guard, the README check, and /preserve
WHAT: the first PostToolUse hook and the preservation law's front, born
the morning the kit's public README was found two versions behind (the
CEO: "we definitely don't want the readme falling behind again"). (1)
THE HYGIENE GUARD (Tier 3): after every Write/Edit lands, one stateless
script says the law that applies to THAT file at the moment of the edit:
a portable original -> refresh its kit copy, the graft log + version if
a concept changed, the public README if a pillar/skill/hook/box item
changed, then sync; a kit copy edited directly -> edit the original; the
core instructions file -> its lint runs and a FAIL is relayed; a touched
wiki-topic section without a See-also line -> named; a forbidden
character (em/en dash) in player-facing text -> the edit is BLOCKED with
the offending lines; a new asset -> run the import. (2) THE README
CHECK: the kit sync script refuses to push while the public README's
"Kit version:" line lags the graft log's CURRENT KIT VERSION - the one
mechanical place a README-only-in-the-public-repo can be caught. (3)
/preserve: the preservation law lived in prose plus three loose scripts;
the skill takes a target and offers retire, shelve, then the
twice-acknowledged delete grant, in that order, with the exact words
recorded. Lesson: a reminder that fires at the edit is worth ten in a
law file - the README fell behind while the law to refresh it was
already written.
CARRIES: hooks/hygiene_guard.py (+ its PostToolUse entry in
hooks/settings.json, hooks/README.txt); HOOKS_METHOD.md Tier 3 +
bootstrap step 9 + change log; skills/preserve/SKILL.md; SKILLS.md
(shelf entry + change log); the front door STEP 4; WORKFLOW_METHOD's
instance gains a README step in "Edit the future-project kit".
GRAFT: copy hygiene_guard.py, rewrite its CONFIG block for the project
(portable file names, kit folder, skills/hooks dirs, core file + lint
command, wiki dirs, player-text patterns, assets folder), wire the
Write|Edit|MultiEdit PostToolUse entry, run `--selftest` (25 checks).
A project that publishes its own kit: add a "Kit version: vX.Y" line to
the public README and the version check to its sync script. Copy the
/preserve skill and list it on the shelf. A project with no player-
facing text keeps the DASH rule's pattern list empty. Nothing else
moves.

### v1.17 - 2026-09-13 - The README gate (parity lint, graft README line, audit cadence)
WHAT: the 09-13 four-employee audit of the public README found three
prose slips the v1.16 version check could not see (a law count still
"six", settings.json sent to the wrong folder, a mechanic misdescribed)
and a page of mechanics nobody had been asked to write. The CEO: "What
can we do to prevent the Readme from falling behind so far and missing
information like that in the future?" Three layers, cheapest first.
(1) THE PARITY LINT: a script derives every countable README fact from
the kit folder itself - the law count from the delegation method's
numbered list (and its heading's own number word), the skills from the
skills dir (count word + every /name), the hooks from the hooks dir, the
reference-tool count, every box-table row against the kit's top level
and back, the version line - plus a small CLAIMS table of grep-able
prose facts (a must-match and a must-not-match per slip already seen).
The kit sync REFUSES to push on any FAIL; the check group runs it; a
ledger line per run. (2) THE GRAFT README LINE: every graft entry gains
a fourth field, README, naming the public-README section the concept
touched or "none, wording only"; the lint fails while the newest entry
lacks it, so "did this reach the front page?" is decided when the
concept ships, not remembered later. (3) THE AUDIT CADENCE: the audit
itself (read-only employees compare the README against every method
file, the skills, the hooks and the front door) is ledgered with
`--record`; ledger_trends PROPOSES the next one at standup when the kit
folder has moved past a commit count or an age since the last line
(owner's thresholds). Lesson: a version line is one fact; a README is
a hundred, and the ones that drift are the ones no script reads.
CARRIES: reference tools/readme_lint.py (+ its refusal in the kit sync
script and its check-group line), reference tools/readme_audit.py,
reference tools/ledger_trends.py (rule 7 + two thresholds), this file's
README field (from this entry on), the process registry's kit entry
(step 3 rewritten) and its new "Audit the public README" entry.
GRAFT: a project that publishes its own kit or keeps any public README
whose facts derive from files: copy readme_lint.py, rewrite its CONFIG
block (README path, source-of-truth files, box heading, CLAIMS rows),
call it from the publish/sync script as a refusal, add it to the check
group, run `--selftest`. Add the README field to the project's own
graft-log entries from its next entry on. Copy readme_audit.py, graft
rule 7 and the two thresholds into the project's ledger_trends, record
the last audit (or let the "none on record" proposal ask for the
first). A project with no public README skips this entry whole.
README: "Updating an installed project" (the README field + the gate
sentence), "What is in the box" (reference tools: sixteen), the
"Kit version:" line.

### v1.18 - 2026-09-13 - The intent loop (INTENT.md, the comparison ledger, /correct, the systems audit)
WHAT: the CEO, the same morning as the README gate: "I believe Intent would
help cover the 'why' of something which may help you or any Claude make
better decisions in the future. It's not as important that you know to
make looping scripts because you were told to, it's almost more important
that you understand we make looping scripts because 1.) It decreases your
token usage, 2.) It's done the same every time and very structured, 3.)
It's something that triggers without asking." Four parts. (1) THE INTENT
FILE: one INTENT.md per project, one section per ruling - ASKED (the
owner's prompt verbatim), WHY (the owner's numbered reasons verbatim),
GENERALIZES TO (the manager's reading, marked as such), LIVES IN; a brief
pastes the section; a missing section IS the question to ask. (2) THE
COMPARISON LEDGER: before building, the manager logs its OWN reading of
the ask (a CLAIM); employees state theirs in a stamp line; when the
owner's intent is known the claim resolves SAME / SIMILAR / DIFFERENT
with its source named (stated / correction / inferred - self-judged
agreement is counted apart so it never inflates the rate). A script turns
the log into day / week / month / actor agreement rates - txt for Claude,
csv + xlsx for a human - and calls the trend IMPROVING / STEADY /
DECLINING. The owner's why, verbatim: "we 1.) Want to have real data, 2.)
We want to compare past to present, 3.) We want to know if we are
improving, staying the same, or declining because each one of those will
tell us something about our feedback loop." (3) THE CORRECTION RITUAL:
/correct asks "What about the last thing I did needs correcting?",
records the owner's words verbatim, resolves the open claim DIFFERENT by
itself, then asks "What was the intent?" and /intent files the why - one
feedback loop. (4) THE SYSTEMS AUDIT: the loop measured but never thought;
a ledgered, cadence-proposed audit by a handful of read-only employees
in four lanes (tokens, process, knowledge, features) returns proposals
only. Three new trend rules propose on a declining agreement, stale
claims, clustered corrections and audit age. Lesson: knowing the rule
lets a Claude comply; knowing the why lets it decide the case the rule
never named.
CARRIES: INTENT_METHOD.md (the portable method + bootstrap); reference
tools/intent_log.py, correction_log.py, intent_report.py,
systems_audit.py, ledger_trends.py (rules 8-10 + four thresholds);
skills/intent and skills/correct (+ SKILLS.md shelf entries); the /brief
skill's step 8 (paste the intent, require the INTENT line); the front
door's THE INTENT LOOP step.
GRAFT: create INTENT.md from INTENT_METHOD.md's format with the first
ruling the day one is made (never a backfill sweep); copy the four
scripts, adapt paths; add intent_report to the metrics loop; graft rules
8-10 + thresholds into the project's ledger_trends; copy the two skills
and list them on the shelf; add the employee INTENT stamp line to the
delegation rules and the paste-the-section step to the brief ritual; add
INTENT.md and INTENT_METHOD.md index lines to the core file. A project
with no owner rulings yet still creates the empty INTENT.md - the first
correction fills it.
README: "4. Lossless Sessions" (eight rituals, /intent and /correct), a
new "The intent loop (INTENT_METHOD.md)" section after the hooks, "What
is in the box" (INTENT_METHOD.md row, reference tools: twenty), the "Kit
version:" line.

See also: 'Future Project MDs/CONTRIBUTING.md' (the format law); '0 - READ
  ME FIRST, CLAUDE.md' (installs from this log);
  tools/rootstock_update_check.py (reads this file to check for updates).

### v1.19 - 2026-09-13 - The format law, the purpose audit and the kit-sync ruling (CONTRIBUTING.md, FLAGS.md, /flag, the format guard)
WHAT: the CEO, the same day as the intent loop, three rulings in one
prompt. (1) THE KIT-SYNC RULING: "Every time I discuss rootstock-os, or
it's features, scripts, audits, intents, laws , etc. the intention is to
update the future projects and rootstock-os folder and upload to git
with updated readme and files whenever applicable." A kit refresh script
(originals -> copies, the owner-name substitution in scripts, adapted
copies reported not overwritten) runs first inside the sync, and the
prompt hook says KIT UNSYNCED until copies and mirror agree. (2) THE
PURPOSE AUDIT: "Rootstock-os will eventually, hopefully, turn into a
community involved system. Guardrails need to be in place so that
anything written in updates must have a comment describing the purpose
and intent of the 'thing' in the update. Claude MUST compare the purpose
and intent of the thing vs what the thing actually reads whether it's a
script, hook, code or injectable prompt. If there is reason to flag it,
Claude should flag them green, yellow or red. Claude should always
read-only -> Flag -> Explain. There should be a file that directly
references anything that is green, yellow or red flags, tally them and
put them in the git for review. Any Claude can review and put their
findings there for future review." FLAGS.md is that file: one entry per
audit (SAYS from the thing's PURPOSE line, DOES, FLAG, hash of the exact
version), append-only, the tally regenerated at its top by script, STALE
when the thing changes; the /flag skill and a WORKFLOWS entry carry the
ritual; employees may flag (delegation rule 15) and report RED upward.
(3) THE FORMAT LAW: "Any updates, upgrades, hooks, scripts, etc need to
be in the same format so that they work with our current filing system.
Anything without proper format should be flagged, a script should
re-write it after review-only audit. This will be a law and may need
this to be a hook somehow so that no one can inject a prompt that
overrides safety protocols." Every kit thing carries PURPOSE / INTENT /
Search keys / See also (a hook also --selftest + _hooklib, a skill its
frontmatter, the settings template its SAFETY wiring); the format lint
derives the scope from the kit folder, flags the rest, and --rewrite
inserts ONLY the missing lines with the reviewer's words after a
read-only look; the format guard hook (Tier 3b) blocks an unformatted
edit and REFUSES a settings edit that unwires, narrows or mis-points a
safety hook, with the shell guard (no shell writes into a settings file)
and the Stop hook (refuses the turn while the wiring is broken) as
twins. The first audit: four read-only employees flagged every kit thing
in one batch (FLAGS.md carries the result). Lesson: a guardrail for a
community kit cannot depend on the reader's good faith; it has to be a
script that flags, a script that rewrites, and a hook that refuses.
CARRIES: CONTRIBUTING.md (the two laws for contributors); FLAGS.md (the
ledger); reference tools/format_lint.py, purpose_audit.py,
refresh_kit.py; hooks/format_guard.py + its settings.json entries
(PreToolUse and PostToolUse on Write|Edit|MultiEdit); hooks/bash_guard.py
rule (no shell writes into a settings file); hooks/stop_tick.py (the
Stop twin); hooks/prompt_gauge.py (the KIT UNSYNCED line); skills/flag;
SUBAGENT_METHOD.md law + SKILLS.md shelf entry; HOOKS_METHOD.md Tier 3b;
the front door's THE FORMAT GUARD + THE PURPOSE AUDIT step and the
definition of done; the sync script's refresh + first gate + tally.
GRAFT: copy the three scripts and the hook, adapt the CONFIG blocks
(kit folder, hooks/skills dirs, settings path); wire the hook's two
entries; add the settings-file rule to the project's shell guard and the
Stop twin to its stop hook; add format_lint + purpose_audit --pending to
the check group and the refresh + gate + tally to the publish script;
copy CONTRIBUTING.md and let the first status run create FLAGS.md; run
`format_lint.py` and rewrite each failing header BY SCRIPT after a
read-only look (never by hand); then audit every thing once (a handful
of read-only employees, one list each) so FLAGS.md starts with real
data; add the /flag skill to the shelf and the flag rule to the
delegation rules. A project with no public kit still keeps the format
law for its own tools and hooks.
README: "The hooks" (ten, the format guard bullet), "4. Lossless
Sessions" (nine rituals, /flag), a new "The format law and the purpose
audit (CONTRIBUTING.md)" section after the intent loop, "What is in the
box" (CONTRIBUTING.md + FLAGS.md rows, skills: nine, hooks: ten,
reference tools: 23), "Questions people ask" (Can I contribute?), the
"Kit version:" line.

### v1.20 - 2026-09-13 - The first audit's yellows closed (every hook answers --selftest, the front door read independently)
WHAT: the CEO read the five yellows from the kit's first purpose audit
(v1.19) and said "Do it all, make it happen." (1) The three info-only
hooks (session_start, prompt_gauge, pre_compact) now answer
`--selftest` like every guard: module-level work moved into main(), the
pure builders (ledger line, gauge lines, header) factored out so a
selftest never touches stdin, a real ledger or the standup script; live
output byte-identical. Every hook in the kit now carries a selftest,
which the format lint already expected. (2) The diet guard's docstring
and the hooks README stopped saying it "never refuses": it refuses once
per big file (INDEX FIRST, v1.15) and warns on everything else. (3) The
front door got its first full read by a reviewer who did not write it.
The read found the PURPOSE line claimed a four-pillar install while a
third of the file installs the hooks, and the STEP 4 skill list lacked
/correct /intent /flag; both fixed, re-read, GREEN. FLAGS.md: 58
flagged, 58 GREEN, 0 YELLOW, 0 RED.
CARRIES: hooks/pre_compact.py, hooks/prompt_gauge.py,
hooks/session_start.py (the selftests); hooks/diet_guard.py and
hooks/README.txt (the wording); the front door's PURPOSE line and STEP
4 list; FLAGS.md (the re-flags); HOOKS_METHOD.md change log.
GRAFT: copy the three hooks over the installed ones if they were taken
unchanged (their live behaviour is identical; only the structure and
the selftest are new) - if the project adapted them, graft the main()
split and the _selftest() by hand and keep the project's text. Reword
the diet guard's docstring the same way if the install kept the v1.12
wording. Re-flag whatever changed. Then the lesson, which is the real
graft: have a non-author read the front door of YOUR install whole once;
three author passes missed what one independent read found.
README: "The hooks" (the contract bullet: every kit hook answers
--selftest), "The format law and the purpose audit" (the first audit's
outcome line), the "Kit version:" line.

### v1.21 - 2026-09-14 - The first systems audit, ruled and built (the loop law, trust the ledger, the ledgers born, open questions)
WHAT: the systems audit (v1.18) ran for real: four read-only employees,
one lane each, 26 proposals with evidence, nothing applied by the audit.
The CEO ruled on all 26 the same night; this version is what the rulings
built. (1) THE LOOP LAW ("Any script that should be run multiple times
must be called by the main looping script; every action, every
standup"): run_all.py ledgers every group run (loop_runs.txt), the
session-start hook runs the session group once a day and measures the
digest it injects (digest_size.txt), standup shows THE LOOP (each
group's age), ledger_trends proposes on a stale group (rule 13), a big
digest (rule 12) and an old open question (rule 11); probes ride every
build. (2) TRUST THE LEDGER for the check scripts: _ledger.py, one
helper at four append sites (format lint, purpose audit, README lint,
link check) skips an identical result at an unchanged tree - gotcha
found on the way: a ledger's own append changes the tree signature, so
the ledgers exclude themselves. (3) The three preservation ledgers
(retired_files, delete_grants, corrections) had never been born; the
movers got --selftest against a temp dir and the ledgers exist
header-only. (4) open_questions.py: a ledger for decisions only the
owner can make, with age, shown in standup. (5) usage_report: avg tokens
per Read on the daily line, usage_by_arc.txt (checkpoint to checkpoint,
per-commit verdict), cache_misses.txt with causes (first finding: TTL
gaps dominate - the price of coming back after an hour, not a habit).
(6) stop_tick warns CHANGELOG UNEXPORTED; /checkpoint closes the loop
first; /flag's batch rule sends more than five things to one employee
("employee is cheap. Manager is not."). (7) Proposal-only thresholds
moved to .claude/trend_limits.json; guard numbers stay in code
(SECURITY FIRST, then cost, then efficiency - the CEO's order).
CARRIES: reference tools/run_all.py, open_questions.py, _ledger.py
(new); reference tools/standup.py, ledger_trends.py, usage_report.py,
format_lint.py, purpose_audit.py, readme_lint.py, check_wiki_links.py,
retire.py, delete_grant.py, correction_log.py; hooks/session_start.py,
hooks/stop_tick.py; skills/checkpoint, skills/flag; INTENT_METHOD.md
(the loop law + security-first sections); this entry.
GRAFT: adopt run_all.py's GROUPS for your own habitual scripts, then let
the session-start hook call it (the hook degrades to a note when
run_all.py is absent). Wire _ledger.append_unless_identical at every
append site you have that can run twice at one tree. Run the three
movers' --selftest once and let them birth their ledgers. Add the three
trend rules and the limits JSON; keep your guards' numbers in code.
Seed open_questions.txt with whatever your owner has not answered yet.
README: "The intent loop" (the first audit's outcome paragraph), "What
is in the box" (26 scripts, the parent loop, open questions, trust the
ledger).

### v1.22 - 2026-09-14 - The core diet (CLAUDE.md is the hot core; cold sections move by script to sub-indexes; the front door renamed)
WHAT: (1) A Reddit reader measured the kit's front door, then named
"0 - READ ME FIRST, CLAUDE.md", at ~5k tokens and called the kit slop.
The file was an install runbook, never a per-session CLAUDE.md, but the
name invited the misread and the origin's real CLAUDE.md had drifted to
~10k tokens while its own law said "index only". The CEO's ruling: the
core keeps the most-used information and what falls out of the heat map
moves BY SCRIPT into named, growable sub-indexes. (2) THE HOT CORE: the
core lint (check_claude_md.py) now FAILS on a TOKEN budget (bytes/4;
TOKEN_BUDGET, origin 3,500) and requires every docs/index/ sub-index to be
named in the core. (3) THE MOVER: reference tools/core_diet.py measures
every core section's heat (explicit reads of its lines from the
transcript cache, reads of the wiki files it points at, git recency
inside `core_cold_days`), moves COLD routed sections (`Index: <name>`;
`Index: core` pins) verbatim into docs/index/<name>.md with a provenance
comment and, while still over budget, the coldest routed sections next;
each move leaves ONE stub line (`- heading -> docs/index/x.md | brief`,
the brief from the section's Tags line) in the core's "## The
sub-indexes" block. Unrouted cold sections are only PROPOSED.
`--move-section` is the explicit call, `--restore` reverses, `--selftest`
proves the round trip. It runs in the check group BEFORE the lint. (4)
The scanners (wiki_heat, check_wiki_links, export_tag_index,
export_wiki_view, cold_shelf) discover docs/index/*.md as wiki files.
(5) THE FRONT DOOR is renamed "0 - READ ME FIRST.md" and cut to
pointers (~1.8k tokens from ~4.5k): each step points at its method
file's bootstrap section instead of restating it. (6) THE DIGEST DIET:
standup prints the day file's STATE/NEXT lines but not its copy of the
exchange when the transcript block already replayed it, and one tail
line per ledger instead of two. (7) The origin's CLAUDE.md went from
~10k tokens to ~3.5k: the standing rules to docs/index/laws.md, the
long-form library + kit rules to library.md, versioning/changelog to
process.md, engine gotchas to gotchas.md, the folder map to code.md.
CARRIES: reference tools/core_diet.py (new); reference tools/
check_claude_md.py, run_all.py, standup.py, wiki_heat.py,
check_wiki_links.py, export_tag_index.py, cold_shelf.py;
hooks/hygiene_guard.py (the front door's name); WIKI_METHOD.md "The hot
core and the sub-indexes" + the architecture layer 1; the front door
"0 - READ ME FIRST.md" (renamed, rewritten); this entry.
GRAFT: give your core lint a TOKEN budget (bytes/4) and fail on it; copy
core_diet.py, adapt CORE_NAME / INDEX_DIRNAME / the trend-limits key,
run `--selftest`, put it in the check group BEFORE the lint; stamp your
core's sections with `Index: <name>` (laws, library, process, gotchas,
code are the origin's names - use your own) and `Tags: ... | brief`;
run `--move-section` for what should leave now and let the loop handle
the rest; teach your wiki scanners the docs/index/ folder; if your
project's install file carries "CLAUDE.md" in its name and is not one,
rename it. Trim your standup the same two ways if its digest passes
~24k bytes.
README: "Doesn't a wiki make the context HEAVIER?" (the table's core and
digest rows), the new "The installed CLAUDE.md: what it holds and how
big it is" subsection, "Quick start" (the front door's name), "Questions
people ask" (the Reddit question), "What is in the box" (the front door
row, 27 scripts, core_diet).

### v1.25 - 2026-09-14 - The digest diet (the standup prints what the manager acts on; the loss test)
WHAT: after the core diet and the pointer core, the standup digest was
the largest fixed load at session start (~4.3k tokens on the origin).
Measured by block, LEDGER TAILS was 35% of it (33 ledgers, one full line
each, most unchanged for days) and several blocks repeated another (the
daily usage line, the open questions, the day index, the summary twin of
every *_runs ledger). The CEO's condition: "the most important pieces are
context and efficiency. As long as there is no loss there, I'm happy."
THE LOSS TEST: a line leaves the digest only when it duplicates another
block, or carries no verdict and is one `tail -1` away by a path the
digest already prints. Never cut: THE LAST EXCHANGE (the verbatim law)
and WHERE WE LEFT OFF. The rest: a ledger's newest line prints in full
only when it carries a verdict (CHECK, FAIL, RED n, STALE, WARN, UNSYNCED,
a cliff) or is newer than the previous standup (digest_size.txt's last
line); the others collapse to `name date` on shared "quiet" lines;
duplicated ledgers are skipped; commits 12 -> 5; RECENT DAYS prints each
day's first clause. Same session, before/after: 17.4 KB -> 6.3 KB (-64%).
The warn threshold followed the size down (digest_warn_bytes 24000 ->
12000), so growth is caught at the new floor, not the old ceiling.
CARRIES: reference tools/standup.py (SHOWN_ELSEWHERE, has_verdict,
line_stamp, last_standup_stamp, tails_plan, wrap_names, first_clause,
--selftest); reference tools/ledger_trends.py (the lowered default);
REPORTING_METHOD.md is unchanged (the ledgers themselves are untouched).
GRAFT: copy standup.py fresh (keep the project's version-source block);
lower digest_warn_bytes in the project's trend_limits.json to about twice
its post-diet digest size; add the project's own verdict words to
_VERDICT if its ledgers use others; add any ledger another block already
prints to SHOWN_ELSEWHERE. Then run the digest twice and diff: every line
that left must fail the loss test.
README: "What actually loads" tables (the digest row: ~1.6k-2k tokens).

### v1.24 - 2026-09-14 - The quiet audit (FLAGS.md's stamp means last changed, not last run)
WHAT: the purpose audit's tally block carries an "Updated" stamp, and the
loop runs the audit at every standup, so the stamp was rewritten every
session even when no flag, row or count had moved. The mirror check saw
one byte-different kit file and the prompt hook said KIT UNSYNCED on
every prompt over nothing (the origin's open question Q0003). The CEO
ruled option 2, fix the cause, over the cheap fix of teaching the mirror
check to ignore that line: the audit now compares the fresh tally block
against the one in the file with the stamp masked, and skips the write
when nothing else changed. The stamp now means LAST CHANGED; the runs
ledger (purpose_audit_runs.txt) still records every run. A generated
line inside a committed file must not churn on a no-op run: a sync
warning that fires on noise trains everyone to ignore it.
CARRIES: reference tools/purpose_audit.py (regenerate() returns False on
a stamp-only difference; selftest covers both branches); FLAGS.md (the
generated tally, unchanged in shape).
GRAFT: copy purpose_audit.py fresh over the project's adapted copy (the
change is inside regenerate() and one helper; keep any local KIT_DIR or
ledger-path edits). If the project's mirror check or sync hook was taught
to ignore the Updated line as a workaround, drop that exception in the
same batch. Any other generated stamp in a committed file gets the same
treatment: rewrite on change, never on a run.
README: "The format law and the purpose audit" (one sentence: the tally
stamp moves only when a flag moves).

### v1.23 - 2026-09-14 - The pointer core (CLAUDE.md points, the master index lists, rules load by path; Anthropic's 200-line target guarded)
WHAT: (1) THE SECOND RULING on the core, the same day as v1.22. The CEO
asked whether a single MASTER_INDEX would be the right call ("Claude.md
should simply point to everything else") and had the manager read
Anthropic's memory page (code.claude.com/docs/en/memory) before ruling.
The page settles the mechanics: target under 200 lines per CLAUDE.md;
`@path` imports and rules WITHOUT a paths field load at launch, so moving
must-read text into them "helps organization but doesn't reduce context";
a `.claude/rules/*.md` file WITH `paths:` front matter loads only when
Claude reads a matching file; CLAUDE.md is guidance and hooks are the
enforcement layer; block HTML comments are stripped before injection.
The CEO's must-read chain enforced by hook was dropped by his own
verdict ("your response is likely more correct than mine"); the master
index and the smallest-possible core were kept. (2) KNOWLEDGE HAS THREE
HOMES, by when it is needed: ALWAYS -> CLAUDE.md, the pointer core (the
project in a paragraph, how to read, how to verify, the laws no hook
enforces, one pointer to the master index; the origin: 68 lines, ~900
tokens, from ~3.5k); WHEN A MATCHING FILE IS READ -> path-scoped rules
(the origin: game-code.md for scripts/scenes/shaders, player-text.md for
.tres/ui/store/changelog text, wiki.md for every .md; each moved VERBATIM
with the core diet's provenance comment so --restore still works; the
format header sits in a stripped HTML comment, free); ON DEMAND ->
docs/index/MASTER_INDEX.md, THE ONE DOOR (every topic file, root file,
sub-index, law stub, rule and knowledge file, one line each, every
destination direct). The cross-workstation notes moved to
docs/index/notes.md; standup prints their headlines from there. (3) THE
GUARD: check_claude_md.py now fails past LINE_BUDGET 200 (Anthropic's
number) or TOKEN_BUDGET 2,000 (the CEO's action line), WARNS past
WARN_TOKENS 1,000, requires CLAUDE.md to name the master index, the
master index to list every docs/systems and docs/index file and every
rule, and fails on a rule with no paths field (it would load every
session; its tokens are counted against the core). standup prints the
lint's OK/WARN line under "== THE CORE" so the owner sees the size every
session; the hygiene guard runs the lint the moment CLAUDE.md, the master
index or a rule is edited. (4) core_diet.py's stub block now lives in the
master index, not the core (selftest proves the round trip both ways;
a pre-v1.23 core still holding its own block restores cleanly). (5)
check_wiki_links treats the master index like the core (every docs/
mention must resolve); refresh_kit carries PORTABLE_RULES (rules/wiki.md
travels; game and text rules stay per project). (6) WORKFLOWS gained "Add
or change a path-scoped rule"; the front door's STEP 1 and definition of
done name the master index, the rules and the size line.
CARRIES: rules/wiki.md (new, the first kit rule); reference tools/
check_claude_md.py, core_diet.py, standup.py, check_wiki_links.py,
refresh_kit.py; hooks/hygiene_guard.py (CORE_CONTRACT); WIKI_METHOD.md
(architecture layer 1 + "The hot core and the sub-indexes": the second
ruling and the three homes); the front door STEP 1 + definition of done;
this entry.
GRAFT: rewrite your core as a pointer file (identity, how to read, how to
verify, the laws no hook enforces, ONE line naming docs/index/
MASTER_INDEX.md); build the master index from the core's old library
lines and its sub-index stub block; move each part-of-the-codebase rule
set VERBATIM into `.claude/rules/<topic>.md` with a `paths:` list first
and the core-diet provenance comment; copy rules/wiki.md and adjust its
paths; take the new check_claude_md.py (set LINE_BUDGET 200, TOKEN_BUDGET
and WARN_TOKENS to your owner's numbers, never raise them later),
core_diet.py, standup.py, check_wiki_links.py, refresh_kit.py and the
hygiene guard; run core_diet --selftest and check_claude_md; confirm a
rule loads by opening a matching file and running /context.
README: the new top section "What loads every session, what Anthropic
says, and what guards it" (right after the intro), the "Doesn't a wiki
make the context HEAVIER?" table (core row ~900 tokens / 68 lines), "The
installed CLAUDE.md: what it holds and how big it is" (rewritten for the
three homes), "Quick start" (the core lands under Anthropic's target),
"What is in the box" (the rules/ row, 27 scripts), "Questions people ask"
(the size question answered with Anthropic's number).

### v1.26 - 2026-09-20 - The lesson loop (LESSONS.md, the one right way first; LESSON ADVISED)
WHAT: the kit learned WHAT (the wiki, the tag index) and captured HOW in
steps (WORKFLOW_METHOD.md), but judgment - do this first, here is what
looked right and was not, here is what changes when A differs from B -
had no home and nothing pushed the manager to write it. The CEO's ask:
"something to push you to write what you learned, as well as push you to
add to the knowledge base ... so in the future you don't make the same
mistakes and just do the one correct way first". THE LESSON LAW: one
book, LESSONS.md, one entry per task shape (heading in a prompt's words;
Tags + Keys lines; THE ONE RIGHT WAY; dated TRIED / FAILED BECAUSE / DO
INSTEAD; NUANCE lines; See also to the detail's home), grepped before any
task the way the process registry is. Both ends are mechanical: the
prompt hook names the entries whose Keys hit the prompt (THE LESSON
LINE, at most three, with line numbers); the new Stop hook scans the
turn's transcript slice for trial-and-error signals (the same command run
again after an error, repeated edit misses, a FAIL then a PASS, an intent
claim resolved DIFFERENT, an employee briefed twice, a correction prompt)
and refuses to end the turn once with LESSON ADVISED (a block reaches the
manager; a systemMessage does not); never the same slice twice; a turn
that edited the book passes as WRITTEN. The correction ledger prints
LESSON ADVISED after a DIFFERENT. Measured: lesson_runs.txt (MATCHED /
ADVISED / WRITTEN / CHECK); `lesson_log.py --check` in the check group
lints the entries; ledger_trends rule 14 proposes when advised lines pile
up with no entry written. Origin lesson on the first day: a long heredoc
through the shell tool fails on Windows past ~100 lines; the Write tool
and a scratchpad edit script are the one right way.
CARRIES: LESSONS.md (new: the law, the entry shape, the origin's first
five entries); hooks/lesson_advisor.py (new); hooks/prompt_gauge.py (THE
LESSON LINE); hooks/settings.json (the second Stop entry); hooks/
README.txt; reference tools/lesson_log.py (new); reference tools/
correction_log.py (the LESSON ADVISED print); reference tools/
ledger_trends.py (rule 14 + lesson_advised_unwritten); reference tools/
run_all.py (check group); reference tools/_ledger.py (the ledger name);
hooks/hygiene_guard.py (LESSONS.md in KIT_MDS); HOOKS_METHOD.md (Tier 1
item 5 + change log); skills/checkpoint/SKILL.md (step 0 asks for the
lesson); the front door STEP 4; this entry.
GRAFT: copy LESSONS.md to the project root and keep its top (the law and
the entry shape); retire the origin's entries to a cold shelf or keep
the ones that carry (the heredoc one carries to any Windows project);
copy lesson_log.py to tools/ and lesson_advisor.py to tools/hooks/; take
the new prompt_gauge.py or graft its LESSON LINE block (six lines in
main, two selftest lines); add the Stop entry beside stop_tick's; add
`.claude/lesson_state.json` to .gitignore; add `["tools/lesson_log.py",
"--check"]` to run_all's check group and `lesson_runs.txt` to _ledger's
LEDGER_BASENAMES; graft rule 14 and the `lesson_advised_unwritten` key
into ledger_trends (and trend_limits.json if the project has one); add
LESSONS.md to the hygiene guard's KIT_MDS if the project keeps a kit; add
the LESSON ADVISED print to correction_log's DIFFERENT path; add the
read-cheap line and the law line to the core (two lines each); add the
"Write or amend a lesson" workflow entry and the checkpoint step 0
sentence; run every --selftest and pipe-test the Stop hook once for real.
README: "The hooks" (the eleventh hook, the count), "What is in the box"
(the LESSONS.md row, the hooks count, the reference tools count and the
lesson loop in the adopt list), and the new bullet "The lessons book (the
lesson loop)" under the wiki pillar.

### v1.27 - 2026-09-20 - The preserve guard hardened (the 48,000-file report: the script that runs is read first)
WHAT: a public report the same day - an agent asked to rebuild a mirror
wrote a remover to Temp, ran it in a later command, and its os.walk went
through Windows directory junctions (islink() is False for a junction)
into the live tree and the repo's .git: 48,000 files, the object store
emptied, git unable to restore anything. The CEO: "We need to prevent
this at all costs ... make sure what we have is robust enough". Probed
with the incident's own shapes before reading the guard, fourteen of
twenty-nine passed straight through: a heredoc body written to a
SCRIPT file was exempt (the cat/tee exemption), a script being EXECUTED
was never looked at, a bare-name target (rm build) needed a path
character, a pipeline into the remove cmdlet had no argument to match,
robocopy /MIR and rsync --delete were unknown, git checkout of a path,
switch --discard-changes, force-with-lease, branch -f and filter-branch
were open, .git/objects and a variable target ($DIR) were grantable, and
a crash in the guard allowed the call. All closed: the guard now reads
every script a command executes (the whole file when git does not track
it, the uncommitted added lines when it does; grep/cat/diff is reading,
not running), scans heredoc bodies aimed at script files, takes bare
names and pipelines, knows the mirror verbs and the remaining git
shapes, refuses any .git folder and any variable target with no grant
possible, and falls back to a crude substring check on a crash (fail
closed). Seventy-two selftest checks. The guard refused its own
hardening five times (two-letter helper names that read as verbs,
pattern sources that matched themselves) - reworded every time, never
routed around; that is the new LESSONS.md entry.
CARRIES: hooks/preserve_guard.py (the whole hardening); hooks/README.txt
(the line); HOOKS_METHOD.md (Tier 2d: HARDENED, RUN, FAILS CLOSED);
LESSONS.md ("Harden a guard against a public incident"); the origin's
docs/systems/tooling.md row and WORKFLOWS.md "Delete something" NEVER
line (project-side, described here so a graft knows to mirror them);
this entry.
GRAFT: take the new hooks/preserve_guard.py whole (no project-specific
lines in it; the never-list reads the repo root from _hooklib) and run
`python tools/hooks/preserve_guard.py --selftest`; note that a tracked
script with an uncommitted diff that ADDS a deletion call is refused
when run until committed or granted, and a committed script that
cleans its own temp file is untouched; add the NEVER line to the
project's delete workflow entry and the tooling row; copy the LESSONS.md
entry if the project keeps a lessons book. Expect the guard to refuse
edits to itself whose new text names a verb: split the literal or write
the verb as r[m].
README: "The hooks" (the preserve guard bullet: bare names, pipelines,
mirror verbs, every force push, executed scripts read first, .git and
variable targets, fail closed); no count changed.

### v1.28 - 2026-09-20 - The auto-checkpoint on session end, and the local mirror
WHAT: two asks the same evening. (1) The CEO: "Can we make /clear
automatically check for a checkpoint, and if none was done, perform a
checkpoint before clearing?" The harness fires SessionEnd at /clear
(and logout, stdin closed, other; resume is a suspension) with the
transcript path and a 60 s budget; it cannot hold the clear back and
the manager is gone. So a twelfth hook does the MECHANICS alone, only
when work is unbanked (a change outside the ledger folder or a commit
off origin): the final exchange mined verbatim from the transcript into
the day file as an AUTO section (the old one kept as SUPERSEDED), a
"Checkpoint (auto)" commit, a push to origin and the mirror, the
counter reset. Nothing unbanked = one ledger line. The judgment
paragraphs are still the manager's, at the next real checkpoint. (2)
After the 48,000-file report the CEO asked what a bare mirror is and
named a drive: a reference tool pushes every branch and tag of the
project and the kit repo to bare repos on another disk, from the ship
and checkpoint rituals, the session loop and the new hook. Branches
were assessed the same day as not the safeguard for that failure.
Also in this version: the second README audit (four read-only lanes,
T-0920-RA-1..4) - twelve prose slips fixed, nine new CLAIMS rows so
they cannot recur, six mechanics the README never said.
CARRIES: hooks/session_end.py (new); hooks/settings.json (the
SessionEnd block, timeout 55); hooks/README.txt (the line);
HOOKS_METHOD.md (Tier 1 #6, the heading's count, the change log);
reference tools/backup_push.py (new); reference tools/run_all.py (the
backup group inside session); reference tools/format_lint.py (the
SAFETY row); reference tools/readme_lint.py (nine CLAIMS rows);
skills/ship + skills/checkpoint (the mirror step, the net paragraph);
this entry.
GRAFT: copy hooks/session_end.py whole and merge the SessionEnd block
into .claude/settings.json (timeout 55; the harness's SessionEnd
budget is 60 s); it imports checkpoint.py and standup.py from tools/,
so both reference tools must be installed. Run `--selftest` (18
checks; the throwaway repo stays in the OS temp folder - the preserve
guard refuses a script that removes its own sandbox). For the mirror:
`git init --bare <other drive>/<name>.git`, `git remote add backup
<that path>` in each repo, copy backup_push.py and set its REPOS list,
add the backup group to run_all's GROUPS and the session composite,
add the step to the ship and checkpoint skills. Add session_end.py to
format_lint's SAFETY table so unwiring it is refused. Expect the first
/clear after installing to write "already checkpointed" to
docs/history/session_end_runs.txt when the tree was clean.
README: "The hooks" (Twelve, the Session end bullet); "4. Lossless
Sessions" (the checkpoint thresholds, the net bullet, the standup
miner); "What is in the box" (hooks/ row names _hooklib.py and
README.txt, 29 reference tools, the local mirror); plus the audit's
fixes across pillars 1-3, the hooks, the intent loop, the companions,
Quick start and Updating.

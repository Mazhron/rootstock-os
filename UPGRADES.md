# UPGRADES.md - the graft log (how Rootstock updates without overwriting)

CURRENT KIT VERSION: **v1.15** (this file is the single source of truth for
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

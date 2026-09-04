# READ ME FIRST, CLAUDE - the kit's front door

You have been handed the FUTURE-PROJECT KIT: a portable operating system
for running a software project with Claude, distilled from a real shipped
project (Everwood, 2026). It gives a project four pillars: a token-cheap
KNOWLEDGE WIKI, a scripted REPORTING discipline, a DELEGATION company of
sub-agents, and SESSION RITUALS packaged as skills. Your job right now is
to install it, in order, asking the questions below first. Do not improvise
a different architecture - the methods encode lessons already paid for.

Roles: the person who gave you this kit is the CEO. You (the Claude reading
this) are the MANAGER. Sub-agents you spawn are EMPLOYEES.

Search keys: bootstrap, new project setup, kit install, read me first.

## STEP 0 - ask the CEO before building anything

1. Project name, language/engine, and repo location (git init if needed).
2. WHO MANAGES: which Claude model runs as manager, and which models are
   available as employees? (SUBAGENT_METHOD.md forbids assuming.)
3. One workstation or several? (Ledgers and day files are stamped per
   workstation; multi-machine projects relay notes through CLAUDE.md.)
4. Which domain files apply: GODOT_FIELD_NOTES.md is Godot-engine-specific;
   CLICKER_DESIGN_NOTES.md is idle/clicker-genre-specific. If the project
   is neither, leave them in a "reference/" folder unindexed - they are
   examples of what an engine-notes / genre-notes file should become.
5. UPDATE POLICY: when the kit itself gains new concepts, should I ask
   which to graft (ask), apply them all (auto), offer only ones that
   benefit this project (relevant), or stay quiet unless asked (never)?
   Default is ask; the answer lives in the install stamp and changes any
   time the CEO says so.

## STEP 1 - the wiki (WIKI_METHOD.md, bootstrap section)

Everything else gets indexed into this, so it comes first. Create the new
project's CLAUDE.md as a LEAN CORE (laws + process + library index, inside
a line budget), create docs/systems/ for topic files, add THE WIKI
CONVENTION block, and write a lint script that checks core size + index
sync (reference copy provided: reference tools/check_claude_md.py). Copy
the kit's portable MDs to the repo root and index each with one line.
Stamp the install: add the line "Rootstock vX.Y installed <date> |
updates: ask" to the new CLAUDE.md's index (current version: see
UPGRADES.md in the kit) - it is how future updates know where this
project stands, and the last word is the CEO's UPDATE POLICY
(ask/auto/relevant/never; ask the CEO once at STEP 0, changeable any
time by just saying so).

## STEP 2 - reporting + session rituals (REPORTING_METHOD.md)

Create docs/history/ and the runner script the day the first repeatable
thing exists. Then build the session loop:
- tools/standup.py - the session opener (digest + THE LAST EXCHANGE mined
  verbatim from the harness transcripts + WHERE WE LEFT OFF).
- tools/checkpoint.py - the task counter + checkpoint protocol.
- docs/history/days/ + days_index.txt - the daily log.
Reference copies of both scripts are in "reference tools/" - they WORK but
carry the origin project's ledger names and paths; adapt, don't rewrite.
Same folder: usage_report.py, the usage sheet (REPORTING_METHOD.md section
"mine the harness meter") - it mines ~/.claude/projects/ transcripts for
real per-model/per-tool token totals by day/week/month; adapt its output
paths + the project-name filter in transcript_dirs() and it works in any
Claude Code project unchanged. Also rootstock_update_check.py - adapt its
config lines and WIRE IT INTO YOUR STANDUP script (it is weekly
rate-limited, offline-safe, and one ledger line per check), so "is there
a newer Rootstock?" answers itself per the CEO's update policy instead of
depending on anyone remembering to ask.
The protocol they serve: tick after every task; at arc end push, refresh
the day file's WHERE WE LEFT OFF with BOTH sides of the final exchange
(CEO's last prompt + manager's last response, VERBATIM - exact words in
quote blocks, never condensed; write the reply into the file, then send
that exact text), reset, and emit the safe-to-clear marker. The verbatim
replay itself is MECHANICAL: standup mines the final exchange from the
harness transcripts (~/.claude/projects/<slug>/*.jsonl), so a mid-arc
/clear cannot lose it and no one's discipline is load-bearing; the
day-file copy is the committed, searchable record. Day one:
record a baseline run in a ledger.

## STEP 3 - the delegation company (SUBAGENT_METHOD.md, bootstrap section)

Using the CEO's STEP-0 answers: create SUBAGENTS.md (org chart, the five
laws, a first-draft assignments table for THIS project's task types, an
empty performance ledger), index it, and delegate something small the same
day to prove the stamp/brief/verify/ledger loop end to end.

## STEP 4 - the skills shelf (SKILLS.md)

Copy the kit's skills/ folder into the repo as .claude/skills/ and
SKILLS.md to the repo root; index it. The skills (/standup /checkpoint
/ship /brief) call the tools built in steps 1-3, so they go live last.
Adopt THE SKILLS RULE: a ritual born or amended updates its skill in the
same batch.

## STEP 5 - optional boards (adopt when the CEO wants them)

- TOKEN_IDEAS.md style savings board (any token-saving idea, recorded).
- NEXT_STEPS.md roadmap with attribution + FUTURE_FEATURES.md pin board.
- A public CHANGELOG fed by player/user-readable commit subjects.

## DEFINITION OF DONE

standup.py runs clean; the lint passes; SUBAGENTS.md has one real ledger
line; the skills answer to their slash commands; and the first commit is
in ("the operating system boots"). From then on the standing habits carry
it: every write grows the wiki, every repeatable action becomes a script,
every result lands in a ledger, every batch ships, every arc checkpoints.

One law to carry verbatim (THE CONTRADICTION RULE): if the CEO asks for
something that contradicts a rule they previously set, FLAG it and get
explicit confirmation - never silently comply, never silently refuse.

## UPDATING AN EXISTING INSTALL (later, when the kit has moved on)

If this project already runs Rootstock and the CEO hands you a newer kit
(or says "update rootstock", or the standup update check reports newer
grafts), do NOT reinstall and do NOT copy kit files over project files -
the project's adapted files and grown knowledge are the product. Open the
kit's UPGRADES.md (the graft log) and follow THE GRAFT PROTOCOL there:
read the entries newer than the project's "Rootstock vX.Y installed"
line, act per the CEO's update policy (ask/auto/relevant/never - stored
in that same line), graft each chosen CONCEPT onto the project's own
files in its own names and voice, then bump the version line.

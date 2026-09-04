# UPGRADES.md - the graft log (how Rootstock updates without overwriting)

CURRENT KIT VERSION: **v1.5** (this file is the single source of truth for
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

### v1.5 - 2026-09-04 - Honest prerequisites + the brownfield rule
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

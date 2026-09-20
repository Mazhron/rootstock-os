# HOOKS_METHOD.md - laws the harness enforces itself (PORTABLE, part of the future-project kit)

PURPOSE: Documents the harness hooks, session start, prompt, stop,
  compaction, and tool-call guards, that enforce CLAUDE.md's laws
  mechanically instead of relying on the manager's memory, plus the hook
  contract and the kit's hook roster.
INTENT: Founded on Mazhron's question: Claude has a thing called hooks, are
  there any we could create and add to our workflows. Every law and ritual
  previously ran from the manager's memory; a hook turns Claude should into
  Claude cannot.

Founded 2026-09-06 on Mazhron's question "Claude has a thing called hooks -
are there any we could create and add to our workflows?". The answer was
yes, and the reason is structural: every law in CLAUDE.md, every ritual on
the skills shelf, ran from the manager's MEMORY. After a /clear the CEO
had nothing until someone typed "standup"; the checkpoint counter ticked
only when the manager remembered; "never delete a build zip" was a
sentence. A HOOK is a script the HARNESS runs at a fixed moment, with no
one remembering anything. It turns "Claude should" into "Claude can't".

Search keys: hooks, harness hooks, settings.json, session start, stop
hook, pretooluse, deny, block, context gauge, auto standup, auto tick.
See also: SKILLS.md (the voluntary twin: skills run when invoked, hooks
run when the harness reaches a moment), REPORTING_METHOD.md (the ledgers
the hooks feed), SUBAGENT_METHOD.md (the stamp a Tier-4 hook will check),
WORKFLOW_METHOD.md (the registry entry "Add or change a harness hook").

## THE HOOKS RULE (standing, Mazhron 2026-09-06)

A law the harness CAN enforce mechanically gets a hook, not a prose
reminder. The test: does the law fire at a moment the harness exposes
(session start, prompt submit, before/after a tool call, manager stop,
compaction, employee stop)? If yes, script it. Prose stays for judgment
calls; hooks take the mechanical ones. Adding a hook is a normal batch:
script + wiring + pipe test + its doc line + (if portable) the kit copy
and an UPGRADES entry.

## The contract (what a hook is, mechanically)

- Wiring: `.claude/settings.json` (project-level, CHECKED IN - it travels
  to every workstation via git) maps an EVENT (+ optional tool MATCHER) to
  a command. The command form that survives Windows paths with spaces and
  a missing env var: `python "${CLAUDE_PROJECT_DIR:-.}/tools/hooks/x.py"`.
- Input: one JSON object on stdin. Common fields: `session_id`,
  `transcript_path`, `cwd`; per event: `source` (SessionStart:
  startup/resume/clear/compact), `trigger` (PreCompact: manual/auto),
  `tool_name` + `tool_input` (PreToolUse; a shell tool's command is
  `tool_input.command`), `stop_hook_active` (Stop: true when this stop
  was already refused once - the loop guard).
- Output: exit 0 + plain stdout = injected as context (UserPromptSubmit,
  SessionStart); JSON `{"hookSpecificOutput": {"hookEventName": E,
  "additionalContext": T}}` does the same explicitly; PreToolUse deny =
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse",
  "permissionDecision": "deny", "permissionDecisionReason": R}}`; Stop
  refuse = `{"decision": "block", "reason": R}`; `{"systemMessage": M}`
  shows the user a line without touching the model's context.
- Exit 2 = BLOCKING ERROR with stderr fed back. A Python "can't open
  file" is exit 2 - a mis-pathed PreToolUse hook refuses EVERY tool call.
  Hence the `${CLAUDE_PROJECT_DIR:-.}` form, never a bare relative path,
  and a try/except around anything that can throw.
- A broken settings.json silently disables every hook in it: validate
  with `python -m json.tool .claude/settings.json` after each edit.
- The settings watcher picks up edits live for directories that had a
  settings file at session start; a brand-new file MAY need /hooks or a
  restart (in the origin project it was picked up live).
- Cost: one interpreter launch (~0.3 s) per trigger. Fine for session,
  prompt, stop, compact and shell-command hooks; a PostToolUse hook on
  every Write/Edit must stay a pattern match with no heavy imports.

## The kit hooks (hooks/ - eleven scripts + _hooklib + settings.json)

TIER 1 - the resumption + checkpoint loop:
1. `session_start.py` (SessionStart, all sources): runs the standup
   script and injects the digest with a relay instruction. Resumption no
   longer depends on anyone typing "standup"; after an auto-compaction the
   digest re-anchors the summary.
2. `stop_tick.py` (Stop): ticks the checkpoint counter ONLY when work
   happened - `work_fingerprint()` in the checkpoint script = HEAD + the
   working tree's porcelain status minus bookkeeping files. A Q&A reply
   does not tick. ADVISED (8 tasks or <80% context) = a system message
   to the user; URGENT (15 tasks or <30% context) = the hook REFUSES to
   end the turn once (re-blocks every 5 tasks; `stop_hook_active` guards
   the loop) and the reason tells the manager to relay and checkpoint.
   Manual `--tick` is retired (it double-counts next to the hook).
   ADVISED MEANS DO IT (kit v1.13, the origin CEO's ruling 2026-09-10:
   "If a checkpoint is advised, you should do it. That way a user
   doesn't need to ask you to checkpoint, they can simply clear"): an
   ADVISED line from either hook is an instruction, not a suggestion -
   the manager runs the checkpoint ritual at the end of that reply if
   the arc is closed and the tree is committed, and the CEO just
   /clears. Mid-arc: finish the step, ship, then checkpoint. Why the
   whole thing is not one script: the day file stores both sides of the
   final exchange word for word, and the manager's side is the reply
   being written at that moment - no script can see it before it is
   sent. The script does the mechanics (push, fingerprint, reset); the
   manager writes the two paragraphs.
3. `prompt_gauge.py` (UserPromptSubmit): silent unless a threshold is
   crossed; then one line the manager relays verbatim. Zero tokens on a
   normal turn.
4. `pre_compact.py` (PreCompact): one ledger line per compaction
   (when/WS/version/manual-auto/context/unbanked tasks) in
   docs/history/compact_runs.txt; a system message on auto.
5. `lesson_advisor.py` (Stop; kit v1.26, THE LESSON LOOP, the CEO's ask
   2026-09-20: "something to push you to write what you learned, as
   well as push you to add to the knowledge base"): the checkpoint
   counter's twin for learning. It reads the turn's transcript slice
   (since the last Stop, a line pointer per transcript in .claude/
   lesson_state.json) through reference tools/lesson_log.py and, on a
   trial-and-error signal - the same command run again after an error,
   repeated edit misses, a FAIL followed by a PASS, an intent claim
   resolved DIFFERENT, an employee briefed twice, a prompt that reads as
   a correction - REFUSES to end the turn once with LESSON ADVISED, and
   ADVISED MEANS DO IT: the manager writes or amends the LESSONS.md
   entry for the task shape (or the wiki fact under a Tags line, or one
   line saying why there is no lesson) before the turn ends. A block is
   used, not a systemMessage, because only a block's reason reaches the
   manager. Never the same slice twice; a turn that edited the book is
   ledgered WRITTEN and passes. The prompt end lives in prompt_gauge.py
   (THE LESSON LINE: the entries whose Keys hit the prompt, read before
   the first tool call). Ledger: docs/history/lesson_runs.txt; the
   check loop lints the book and ledger_trends proposes when advised
   lines pile up unwritten. State file: gitignore it.

TIER 2 - shell guards (`bash_guard.py`, PreToolUse on Bash|PowerShell):
generic rules - no `--no-verify`, no plain force push - plus a PROJECT
RULES block the receiving project fills with its own laws. The origin
project's examples: no delete/move in the builds folder (build zips are
never deleted), tests only through the runner script (never set the test
env var by hand), no em/en dashes in commit text (subjects become the
public changelog), no shell writes/redirects into engine resource files
(the BOM gotcha).

TIER 2b - THE FAN-OUT GUARD (`fanout_guard.py`, PreToolUse on EVERY
tool; kit v1.9, the CEO's ask 2026-09-10 after a public report of a
manager spawning 821 sub-agents and burning 50M+ tokens in thirty
seconds). CATASTROPHE-ONLY by the CEO's ruling the same day ("this
might be too restrictive... I just wanted to prevent complete runaway
agents and gigantic token spend"): nothing fires on real work, nothing
needs a command to lift, and the manager is never locked out for more
than a cooldown.
- THE SPEND METER: every call folds the NEW bytes of the session
  transcript and its employee transcripts into raw + WEIGHTED tokens
  (weighted ~ cost: input 1, cache write 1.25, cache read 0.1, output 5;
  byte offsets in the state file, so a warm call costs ~0.06 s). The
  first sight of a file backfills totals without feeding the velocity
  meter, so installing mid-session never trips on catch-up.
- REFUSES only the runaway shapes: a BURST (8 spawns inside 60 s,
  machine-wide - the 821 shape), a FLOOD (25 spawns inside 10 min per
  session - a loop, not a plan), and RUNAWAY VELOCITY (10M weighted
  tokens inside 120 s: every tool call refused until the window drains,
  a self-clearing cooldown; the manager can still talk and report).
- WARNS, never refuses, on everything else: a systemMessage the CEO sees
  plus a context line the manager relays - every 10 spawns, every 10M
  weighted tokens, velocity past 3M inside the window, and a one-time
  reminder when the bulk-orchestration tool runs.
- No unlock file, no --allow commands, no self-edit lock: `--status`
  shows the meter, `--resume` clears it early, `--selftest` runs the
  twenty-four pipe tests in-process (always at DEFAULTS, so tuning can
  never fail them). The manager-side rule is the delegation method's
  law 6 (THE FAN-OUT LAW); the guard is what makes it true on a bad day.
- THE NUMBERS ARE THE CEO'S (kit v1.10, the origin CEO's ask
  2026-09-10): the script carries DEFAULTS; the CEO's tuned numbers live
  in `.claude/fanout_limits.json` (COMMITTED - they travel with the repo
  and survive a kit graft; a missing or junk file falls back per key).
  `--limits` prints every number current vs default with its meaning,
  `--set key=value ...` writes (refusing a warn threshold above its halt),
  `--defaults` forgets. The /runaway skill (SKILLS.md) is the
  conversational front: show, ask, set, selftest, commit. The manager
  never raises a limit on its own - a refusal still means stop and
  report.

TIER 2c - THE DIET GUARD (`diet_guard.py`, PreToolUse on Read|Bash|
PowerShell; kit v1.12, the origin CEO's ruling 2026-09-10 after the
weighted-usage insight: only the tokens that count against the plan
matter, and under those weights the manager's context is written at
1.25x and every tool result rides in it forever). Nothing to type; one
refusal shape only (INDEX FIRST, kit v1.15), the rest warn-only:
- INDEX FIRST (kit v1.15, the origin CEO's order 2026-09-10 PM: "section
  or split as necessary ... should not require my approval ... part of
  the looping scripts"): the FIRST whole read of a big file per file per
  session is refused, and the refusal carries the file's own index -
  `## ` headings for markdown, func/class/def lines for code, each with
  its line number, capped at 80 - so the next call reads one section by
  offset/limit. The SAME call repeated passes with the warning only (the
  editing exception, no words needed). A file with no structure only
  warns; an image is silent (priced by pixels, ~1-2k tokens however many
  bytes it holds - sizing pictures by their bytes was the bug that made
  the origin project's "21 big reads a day": they were screenshots).
- THE READ DIET (the 10k rule): every later whole-file Read (no
  offset/limit) or bare cat/type/Get-Content of a file past ~10k tokens
  gets one line at the moment of the decision - the size, the line
  count, how many `## ` sections it has, and the cheaper move (grep the
  headings and read one section; or, for an understand-this step,
  delegate the reading to an employee and take back a summary). The CEO's own idea was a token count
  in every heading; that went stale by design and cost output to
  maintain, so the count is GENERATED at the cliff edge instead - the
  harness knows the file size before the read happens. Editing that
  needs the exact text is a fair reason to proceed; the guard says so.
- THE OUTPUT DIET: a chatty shell shape with no limiter - git log
  without a count, a bare git diff, a recursive listing, a noisy
  install - gets the limiter to add, at most three times per session
  per shape so a deliberate choice is not nagged.
- `--selftest` runs the in-process checks; state in
  `.claude/diet_state.json` (gitignored). The outcome is graded by the
  usage sheet's daily line (REPORTING_METHOD.md, THE COMPARISON RULE):
  heavy whole-file reads and section-read share, each day against the
  previous seven, so a bad day is named the next morning.

TIER 2d - THE PRESERVE GUARD (`preserve_guard.py`, PreToolUse on Bash|
PowerShell|Write|Edit|MultiEdit|NotebookEdit; kit v1.14, the origin CEO's
ruling 2026-09-10 after public reports of an agent whose script deleted a
person's files and another that wiped a machine: "You nor any of your
employees should ever delete a file, record, etc. without express
permission from the user. There should be no script created to delete
either"). A REFUSAL, the second one in the kit after the fan-out guard,
and like it aimed at the cliff edge only:
- SHELL: delete verbs with a path argument (rm, rmdir, rd, del, erase,
  unlink, shred, Remove-Item, ri, Clear-Content, format, diskpart,
  truncate), find -delete, xargs rm, moves into nul or /dev/null, the
  git verbs that discard work or history (rm, clean, reset --hard,
  checkout -- path, restore path, branch -d/-D, push --delete, stash
  drop/clear, worktree remove, tag -d, reflog expire, gc --prune), and
  deletion CALLS inside a one-liner or an executed heredoc.
- WRITE: content that adds deletion calls to a non-prose file (the
  os/shutil/pathlib calls, the engine's file removal, fs.rm, File.Delete,
  a Remove-Item or rm -rf line in a script). Prose files pass: a law
  written down names the verbs it bans, and the guard refused its own
  author's documentation twice before that exemption existed.
- PASSES: every path inside the session scratchpad (the harness's own
  per-session junk); a heredoc body fed to cat/tee; ONE command matching
  a live GRANT.
- THE GRANT (tools/delete_grant.py, reference tools/): the manager asks
  naming the exact target, the CEO says yes, the manager restates, the
  CEO says yes again, and the four texts are recorded VERBATIM in
  .claude/delete_grant.json (gitignored, 15 minutes, single use - the
  guard marks it used, never removes it) plus a committed ledger
  docs/history/delete_grants.txt. The grant script itself refuses the
  never-list.
- NEVER, grant or not: a drive root, the home folder, the repo root or
  its .git, a bare wildcard, a path that climbs out with "..". Those
  shapes have no legitimate use in an agent's hands.
- THE MOVERS replace deletion: tools/retire.py moves a file to
  _retired/<same relative path> with a ledger line; tools/cold_shelf.py
  moves a rarely-read wiki section to docs/cold/ verbatim with a stub at
  the old heading and an index line (WIKI_METHOD.md "The cold shelf").
  A wrong memory is marked superseded in place.
- `--selftest` runs 35 in-process checks. No state file; the grant is
  the only thing it reads besides the tool input.
The lesson that shaped it: the guard fired on its author within a
minute of being wired (the settings watcher is live) - first on a
docstring that mentioned the remove call, then on the documentation
table naming the banned verbs. Both were the guard working as written;
the fix was a prose exemption, not a workaround. And the audit the law
forced turned up one real hazard: the kit-mirror script wiped its
target folder before copying, which a misconfigured path would have
turned into an emptied directory. It now refuses a target whose README
does not name the kit and reports stale files instead of removing them.

State: `.claude/hooks_state.json` (gitignored - the fingerprint is per
machine); `.claude/fanout_state.json` (gitignored, the guard's meter);
`.claude/diet_state.json` (gitignored, the diet guard's per-session caps);
`.claude/delete_grant.json` (gitignored, the single-use grant). The checkpoint script's `--reset` stores the fingerprint LAST so
the checkpoint commit itself is not counted; the checkpoint ritual's step
order is commit + push, THEN reset, THEN the marker.

## Tier 3 - THE HYGIENE GUARD (hygiene_guard.py, PostToolUse on Write|Edit|MultiEdit)
Tags: process, lessons | The laws easiest to forget mid-batch fire on a file edit, not a command - so the harness says them at the edit (kit v1.16)

Born 2026-09-11 when the public README was found two kit versions
behind: three law batches had shipped in one evening and nothing said
"refresh the README" at the moment the originals changed. The CEO:
"we definitely don't want the readme falling behind again." One script,
pattern matching only, no state, one interpreter launch per edit
(~0.3 s). It runs AFTER the edit lands and answers with context lines -
never a refusal - except the dash rule, which BLOCKS (PostToolUse
"decision: block" feeds the reason back so the line is fixed at once).
Its CONFIG block at the top names the project's files; a kit install
rewrites that block and nothing else.

1. KIT REFRESH: the edited file is a portable original (a kit MD, a
   skill's SKILL.md, a hook script, a tool that has a reference copy) ->
   one line naming the grab-copy to refresh, the graft-log entry + version
   bump if a concept changed, the public README if a pillar / skill /
   hook / box item changed, then the sync script. Editing a kit COPY
   directly names the original instead; editing the graft log reminds of
   the version line; editing the core instructions file runs its lint at
   once and relays a FAIL (silent when OK).
2. SEE-ALSO: a touched section of a wiki topic page (the link checker's
   hygiene scope) carries no "See also:" line -> the heading is named at
   the edit, instead of in the next link-checker run. A Write lints every
   section; an Edit only the section(s) its new text landed in.
3. DASH (BLOCKS): player-facing text (resource files, UI scripts, the
   store copy, the changelog) received an em or en dash -> the offending
   lines come back and the manager fixes them before anything else. The
   origin project's 217-dash sweep never runs again.
4. IMPORT: a new asset file landed under the assets folder -> "run the
   engine import before the next test".

Companion, not a hook: the kit sync script REFUSES to push while the
README's "Kit version:" line lags the graft log's CURRENT KIT VERSION -
the README lives only in the public repo, so the sync is the one place a
stale one can be caught mechanically.

`--selftest` runs 25 in-process checks (every rule, its scope edges, the
outside-the-repo and empty-input cases).

See also: WORKFLOWS.md "Edit the future-project kit (Rootstock)"; the
link checker (reference tools/check_wiki_links.py, the after-the-fact
twin of rule 2); SKILLS.md (THE SKILLS RULE the kit-refresh line backs).

## Tier 3b - THE FORMAT GUARD (format_guard.py, PreToolUse + PostToolUse on Write|Edit|MultiEdit)
Tags: process, architecture, lessons | A community kit needs a guardrail that does not depend on the reader's good faith: a hook that refuses the unsafe settings edit and blocks the unformatted one (kit v1.19)

Born 2026-09-13 from the CEO's three-part ruling on community updates
(INTENT.md "The format law"): "Anything without proper format should be
flagged, a script should re-write it after review-only audit. This will
be a law and may need this to be a hook somehow so that no one can
inject a prompt that overrides safety protocols." One script, stateless,
one JSON parse plus pattern matching, ~0.3 s per edit; it imports the
format lint (reference tools/format_lint.py) and dispatches on the
event name:

1. BEFORE an edit of a settings file (.claude/settings.json or the kit's
   hooks/settings.json): the would-be text is computed (a Write's
   content; an Edit's old -> new applied to the current file) and
   REFUSED if it would not parse, would name a hook script that does not
   exist beside it, or would leave any SAFETY hook unwired, narrowed or
   mis-pointed. The SAFETY table lives in the lint: preserve_guard,
   bash_guard, fanout_guard, diet_guard, hygiene_guard, format_guard,
   stop_tick, each with the event and the tools its matcher must cover.
   Only the CEO changes the wiring, by hand; a prompt, a brief or a
   contributed patch cannot.
2. AFTER any edit of a kit thing or its original: the lint runs on that
   one file and the edit is BLOCKED (PostToolUse "decision: block" - the
   reason comes back, the edit stays) until the header is right:
   PURPOSE, INTENT, Search keys, See also; a hook's --selftest and
   _hooklib import; a skill's frontmatter. The reason carries the
   rewrite command (`format_lint.py --rewrite <path> --purpose ...
   --intent ...`), which inserts only the missing lines after a
   read-only look - never a hand edit.

Two twins close the other doors: the shell guard refuses a shell write
into a settings file (redirect, Set-Content, sed -i, tee, copy/move, a
python one-liner), and the Stop hook refuses to end the turn once per
fingerprint while the live settings file fails the safety check. The
three together are what "no one can inject a prompt that overrides
safety protocols" means mechanically.

`--selftest` runs the in-process checks against the live settings file
(deny on an unwiring Write, on a rename to a missing script, on
unparsable JSON; silence on a timeout edit; silence on out-of-scope
files). Install: wire both entries from the kit's settings.json, run the
selftest, then `python tools/format_lint.py` to see what the project's
own tools and hooks lack.

See also: reference tools/format_lint.py (the checks, the scope, the
rewrite); reference tools/purpose_audit.py + FLAGS.md (the audit the
PURPOSE line serves); CONTRIBUTING.md (the law for contributors);
SKILLS.md (/flag); WORKFLOWS "Format-check and rewrite a kit thing".

## Tier 4 (ideas, not built - the origin project pinned them)

TIER 4 - the company: SubagentStop refuses an employee's stop when its
report lacks the stamp / workflow line; Notification -> an OS toast when
the manager waits on permission or idles after a long employee run.

## Bootstrap (new project)

1. Copy the kit's hooks/ folder to the project's tools/hooks/ (or wherever
   its scripts live; the scripts locate the repo root from their own path
   and import the checkpoint script from the folder above them).
2. Copy hooks/settings.json to .claude/settings.json (MERGE if the project
   already has one - never replace its arrays). Validate with json.tool.
3. Gitignore `.claude/hooks_state.json` and `.claude/settings.local.json`.
4. Make sure the project's checkpoint script has `work_fingerprint`,
   `load_hook_state`, `save_hook_state` (the kit's reference
   tools/checkpoint.py carries them); reorder its checkpoint ritual so
   `--reset` runs last; strike every "tick by hand" instruction from its
   laws and skills.
5. Fill the bash guard's PROJECT RULES block from the CEO's STEP-0 laws.
6. Pipe-test every hook with synthesized stdin (`echo '{"tool_input":
   {"command":"..."}}' | python tools/hooks/bash_guard.py`); trigger the
   shell guard live once. Add the WORKFLOW entry "Add or change a harness
   hook" to the process registry and a "The hooks" section to the tooling
   doc (the table of event/script/does + the gotchas above).
7. The diet guard needs nothing project-specific: wire its
   Read|Bash|PowerShell PreToolUse entry (the template settings.json has
   it), run `python tools/hooks/diet_guard.py --selftest`, gitignore
   `.claude/diet_state.json`. If the project's checkpoint script
   fingerprints the tree, exclude the usage sheet's outputs (the
   reference copy does) so standup's silent refresh never counts as work.
8. The preserve guard needs nothing project-specific either: wire its
   Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit PreToolUse entry
   (the template settings.json has it), run `python
   tools/hooks/preserve_guard.py --selftest`, gitignore
   `.claude/delete_grant.json`, copy delete_grant.py, retire.py and
   cold_shelf.py from reference tools/ into tools/. Then AUDIT the
   project's existing scripts for deletion calls (grep the os/shutil/
   pathlib removal calls and the shell verbs) and bring each to the CEO:
   convert to a move, or keep with the CEO's word on record. Add the
   registry entries "Delete something (the grant ritual)" and "Retire a
   file or move a wiki section to the cold shelf".
9. The hygiene guard (Tier 3): rewrite its CONFIG block (the portable
   MD names, the kit folder, the skills/hooks dirs, the core file + its
   lint command, the wiki dirs the link checker lints, the player-text
   patterns, the assets folder + import hint), wire its
   Write|Edit|MultiEdit PostToolUse entry (the template settings.json
   has it), run `python tools/hooks/hygiene_guard.py --selftest`. No
   state file. Give the public README (if the project publishes a kit)
   a "Kit version: vX.Y" line so the sync script's check can hold.

## Change log

- 2026-09-06 WS1: founded. Tier 1 + 2 built and pipe-tested in Everwood
  (kit v1.7); Tier 3/4 pinned on the origin project's FUTURE_FEATURES.md.
- 2026-09-10 WS1: Tier 2b, the fan-out guard (kit v1.9) - the CEO's ask
  after the 821-agents report. The first cut was STRICT (session caps,
  a workflow lock, a self-edit lock, CEO-only unlock commands, a bash
  rule refusing the manager); it locked its own author out mid-batch
  and, within the hour, the CEO ruled it too restrictive: "I don't want
  to have to type these commands all the time and neither will any
  users who use Rootstock-os. I just wanted to prevent complete runaway
  agents and gigantic token spend." Loosened to CATASTROPHE-ONLY the
  same day (burst/flood/velocity refusals that clear themselves;
  warnings for the rest; no unlock machinery). Lesson: a guard rail is
  for the cliff edge, not the path - if a normal day ever needs a
  command to get past it, the rail is in the wrong place.
- 2026-09-10 WS1 (later): the numbers become the CEO's (kit v1.10) -
  `--limits` / `--set` / `--defaults` on the guard, a committed
  .claude/fanout_limits.json over the script's DEFAULTS, and the /runaway
  skill as the front. Rule of thumb that fell out: a guard's defaults
  belong to the kit, its tuning to the project - keep them in separate
  files so a graft never overwrites what the CEO chose.
- 2026-09-10 WS1 (evening): Tier 2c, the diet guard (kit v1.12) - born
  from the CEO's weighted-usage insight ("the most important token counts
  are the ones that actually count against a user's usage amount"). The
  usage sheet had shown that under budget weights cache WRITES are the
  top pillar and output is a fifth; the two leaks are whole-file reads
  and chatty tool results, and both are visible BEFORE the call. Hence a
  warn-only PreToolUse guard that says the number at the decision point.
  Lesson: a hook can enforce a diet only if it never blocks - the manager
  sometimes needs the whole file (an edit), and a refusal there would
  breed workarounds; a one-line cost at the cliff edge changes the habit
  without a fight.
- 2026-09-10 WS1 (night): ADVISED MEANS DO IT (kit v1.13) - the CEO:
  "If the checkpoint is a script, there is no reason not to just run it
  at the time a checkpoint is advised." Both hooks' ADVISED lines now
  say "checkpoint at the end of this reply if the arc is closed"; the
  checkpoint skill carries the rule at its top. An advisory the manager
  merely relays is a nag; an advisory the manager acts on is a law.
- 2026-09-10 WS1 (night): Tier 2d, the preserve guard (kit v1.14) - the
  CEO's ruling after public reports of an agent whose script deleted a
  person's files and another that wiped a machine: nobody deletes, no
  script deletes, and a real deletion is granted twice and recorded. The
  same evening the CEO asked whether the system learns, and the answer
  became three read-only scripts (link checker, section heat map, ledger
  trends -> proposals at standup) plus the cold shelf: pruning means
  MOVING to an indexed shelf, never deleting - "all of this is hard
  fought, hard earned knowledge, even the rarely used knowledge." The
  guard refused its own author twice within minutes (a docstring, then
  the documentation naming the banned verbs); prose files are exempt now.
  The audit it forced found the kit-mirror script emptying its target
  folder before copying - a misconfigured path away from the horror
  story - and that is fixed too.
- 2026-09-10 PM (kit v1.15): Tier 2c gains INDEX FIRST - the first whole
  read of a big file per session is refused with the file's index in the
  refusal, the same call repeated passes; images are silent (priced by
  pixels). Born when the origin project's "21 big reads a day" turned out
  to be screenshots sized by their bytes.
- 2026-09-11 WS1: Tier 3, the hygiene guard (kit v1.16) - the first
  PostToolUse hook. Born when the public README was found two kit
  versions behind; the CEO: "we definitely don't want the readme falling
  behind again." Kit-refresh reminder (naming the README), See-also lint
  at the edit, the dash rule as a block, the import reminder; plus the
  sync script's README version check. Tier 4 stays pinned. Lesson: a
  reminder that fires at the moment of the edit is worth ten in a law
  file - the README fell behind while the law was already written.
- 2026-09-13 WS1 (kit v1.19): Tier 3b, the format guard - the first hook
  that runs BEFORE and AFTER the same tools. Born from the CEO's ruling
  on community updates: every kit thing carries one header, a script
  flags the rest and rewrites only the missing lines after a read-only
  look, and a hook refuses a settings edit that would unwire a safety
  hook, so "no one can inject a prompt that overrides safety protocols".
  Twins in the shell guard (no shell writes into a settings file) and
  the Stop hook (refuses the turn while the wiring is broken); the prompt
  gauge gained the KIT UNSYNCED line the same day. Lesson: a guardrail
  for a community kit cannot depend on good faith; it is a script that
  flags, a script that rewrites, and a hook that refuses.
- 2026-09-13 PM (kit v1.20): the first purpose audit's five yellows closed.
  The three info-only hooks (session_start, prompt_gauge, pre_compact)
  gained `--selftest` with no live change (module work into main(), pure
  builders factored so a selftest never touches stdin, a real ledger or
  the standup script); every hook in the kit now answers `--selftest`.
  The diet guard's docstring stopped claiming it never refuses (it
  refuses once, INDEX FIRST). The front door got its first independent
  full read, which found the PURPOSE line undersold the hooks install
  and a stale skill list; both fixed, then GREEN. Lesson: the audit
  loop works on the kit's own authors - a non-author read found what
  three author passes had not.
- 2026-09-14 (kit v1.21): THE LOOP LAW landed in two hooks. session_start
  now runs the parent loop's session group once a day before the digest
  (a note says it ran or when it last ran; a missing run_all.py degrades
  to a note) and appends the digest's byte size to digest_size.txt every
  time it fires, so the injected context is measured, not guessed.
  stop_tick adds a warn-only CHANGELOG UNEXPORTED line when commits sit
  past the changelog anchor (once per count; silent when no anchor
  exists). Both selftests extended. The systems audit that asked for
  this is in INTENT_METHOD.md "The loop law".

- 2026-09-20 WS1: Tier 1 gains the lesson advisor (kit v1.26), THE LESSON
  LOOP's stop end, with the prompt end in prompt_gauge.py and the book in
  LESSONS.md. The CEO's ask: a system that learns HOW, not only what -
  the one right way first, then the pitfalls as headlines, so trial and
  error is paid for once. Design note: a Stop hook's systemMessage
  reaches the user, its block reason reaches the manager; an instruction
  to the manager must be a block, guarded so it can never trap (once per
  slice signature, stop_hook_active, WRITTEN passes).

# HOOKS_METHOD.md - laws the harness enforces itself (PORTABLE, part of the future-project kit)

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

## The kit hooks (hooks/ - six scripts + _hooklib + settings.json)

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
3. `prompt_gauge.py` (UserPromptSubmit): silent unless a threshold is
   crossed; then one line the manager relays verbatim. Zero tokens on a
   normal turn.
4. `pre_compact.py` (PreCompact): one ledger line per compaction
   (when/WS/version/manual-auto/context/unbanked tasks) in
   docs/history/compact_runs.txt; a system message on auto.

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
  eighteen pipe tests in-process. All numbers live in LIMITS and change
  only at the CEO's word. The manager-side rule is the delegation
  method's law 6 (THE FAN-OUT LAW); the guard is what makes it true on a
  bad day.

State: `.claude/hooks_state.json` (gitignored - the fingerprint is per
machine); `.claude/fanout_state.json` (gitignored, the guard's meter). The checkpoint script's `--reset` stores the fingerprint LAST so
the checkpoint commit itself is not counted; the checkpoint ritual's step
order is commit + push, THEN reset, THEN the marker.

## Tiers 3 and 4 (ideas, not built - the origin project pinned them)

TIER 3 - wiki and kit hygiene (PostToolUse on Write|Edit): lint the core
instructions file on edit; check a touched wiki section has its See-also
line; remind to refresh the kit copy when a portable original changes;
fail an edit that puts a forbidden character into player-facing text;
remind to run the engine import after a new asset lands.
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

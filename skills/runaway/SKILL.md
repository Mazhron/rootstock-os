---
name: runaway
description: Show and tune the fan-out guard's runaway numbers (spawn burst and flood caps, token velocity halt, the warning steps). Use when the user says "runaway", asks what the guard's limits are, or wants them changed. Only the owner tunes - never invoke it to raise a limit on your own.
---

# /runaway - the guard's numbers, in the owner's hands

The fan-out guard (tools/hooks/fanout_guard.py, a PreToolUse hook on every
tool) refuses only runaway shapes and warns on the rest. Its DEFAULTS live
in the script; the owner's TUNED numbers live in `.claude/fanout_limits.json`
(COMMITTED - they travel with the repo and survive a kit graft). This skill
is the conversational front for that file.

1. Run `python tools/hooks/fanout_guard.py --limits` and relay the table
   in plain words: each of the nine numbers, current vs default (a `*`
   marks a tuned one), and what crossing it does. Lead with the three
   REFUSALS (burst_cap per machine, flood_cap per session, velocity_halt),
   then the warn-only steps. Say whether the file exists.
2. If the invocation carried changes (`/runaway burst_cap=12 flood_cap=40`),
   apply them straight away; otherwise ask which numbers change and to
   what. Offer, never enforce: the defaults never fire on real work, so a
   limit is worth raising only when the guard has actually spoken on
   honest work; velocity_warn must stay below velocity_halt (the script
   refuses otherwise); windows are seconds, caps are counts, velocity is
   WEIGHTED tokens (input 1, cache write 1.25, cache read 0.1, output 5).
3. `python tools/hooks/fanout_guard.py --set key=value ...` (several at
   once; underscores and commas in numbers are fine). A refusal prints
   why and writes nothing - relay it verbatim. `--defaults` forgets all
   tuning and removes the file.
4. `python tools/hooks/fanout_guard.py --selftest` must still print PASS.
   It always runs at DEFAULTS, so tuning cannot break it; a FAIL means
   the script, not the numbers.
5. Show the new table, then commit `.claude/fanout_limits.json` with the
   batch (a player-readable subject; a harness change, no build, no kit
   refresh - the kit ships the defaults and each project keeps its own
   file). Nothing to restart: the guard reads the file on every call.

RULES
- Only the owner tunes. The manager never runs `--set` unprompted and
  never raises a limit to get past a refusal - a refusal from the guard
  means stop and report (SUBAGENTS.md rule 12 / SUBAGENT_METHOD.md law 6).
- Lowering is always safe to do at the owner's word; raising deserves the
  one-line reminder in step 2, then the owner's answer stands.

IF THE SCRIPT IS MISSING (new project): the hooks are not installed yet.
Ask the owner for their future-project kit (HOOKS_METHOD.md Tier 2b
carries the guard and its bootstrap) before improvising limits.

Search keys: runaway, runaway numbers, fan-out limits, agent cap, spawn
cap, token velocity, tune the guard, fanout_limits.json.
See also: HOOKS_METHOD.md (Tier 2b); SKILLS.md (the shelf); SUBAGENTS.md
rule 12; brief skill step 6 (the fan-out check).

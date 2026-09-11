Rootstock hooks (kit v1.16). Install per HOOKS_METHOD.md 'Bootstrap':
  tools/hooks/  <- these .py files (bash_guard.py: fill PROJECT RULES)
  .claude/settings.json  <- settings.json (merge if one exists)
  .gitignore  <- .claude/hooks_state.json, .claude/settings.local.json,
                 .claude/fanout_state.json, .claude/diet_state.json
The scripts import the checkpoint script from the folder above them
(reference tools/checkpoint.py carries work_fingerprint + hook state).
fanout_guard.py (Tier 2b, the catastrophe-only circuit breaker): keep
its DEFAULTS, run `python tools/hooks/fanout_guard.py --selftest`, wire
its every-tool PreToolUse entry. It refuses only a burst or flood of
sub-agent spawns or runaway token velocity (all self-clearing) and
warns on the rest; nothing for the CEO to type. The CEO tunes the
numbers through the /runaway skill (skills/runaway): `--limits` shows,
`--set key=value` writes .claude/fanout_limits.json - COMMIT that file,
it is the CEO's setting and travels with the repo.
diet_guard.py (Tier 2c, kit v1.12, warn-only): nothing to fill in.
Wire its Read|Bash|PowerShell PreToolUse entry (settings.json has it) and
run `python tools/hooks/diet_guard.py --selftest`. It says a file's size
before a whole read past ~10k tokens and the missing limiter on a chatty
shell command; it never refuses.
preserve_guard.py (Tier 2d, kit v1.14, a REFUSAL): nothing to fill in.
Wire its Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit PreToolUse
entry (settings.json has it), run `python tools/hooks/preserve_guard.py
--selftest`, gitignore .claude/delete_grant.json. It refuses delete
verbs, work-discarding git verbs and deletion calls written into
scripts; the session scratchpad and prose files pass; one command
passes per grant recorded by reference tools/delete_grant.py (the
CEO's two acknowledgments, verbatim). Movers that replace deletion:
reference tools/retire.py (files) and reference tools/cold_shelf.py
(wiki sections). Audit the project's existing scripts for deletion
calls when installing and bring each to the CEO.
hygiene_guard.py (Tier 3, kit v1.16, the first PostToolUse hook):
rewrite its CONFIG block for the project (the portable MD names, the
kit folder, the skills/hooks dirs, the core file + its lint command,
the wiki dirs to lint, the player-text patterns, the assets folder),
wire its Write|Edit|MultiEdit PostToolUse entry (settings.json has it),
run `python tools/hooks/hygiene_guard.py --selftest`. No state file.
After every edit it says the law that applies to that file: refresh the
kit copy (and the public README), add the missing See-also line, fix a
forbidden character in player-facing text (the one BLOCK), run the
import after a new asset. The /preserve skill (skills/preserve) is the
preservation law's front: retire, shelve, or the twice-acknowledged
delete grant, in that order.

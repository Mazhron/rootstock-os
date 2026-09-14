Rootstock hooks (kit v1.20). Install per HOOKS_METHOD.md 'Bootstrap':

PURPOSE: Installation notes for the Rootstock hooks folder: what each hook
  file needs filled in or wired (bash_guard.py's PROJECT RULES,
  fanout_guard.py's numbers via the runaway skill, hygiene_guard.py's CONFIG
  block) and the gitignore entries a new project needs.
INTENT: gives a receiving project the exact per-hook setup steps so the kit
  installs correctly instead of by trial and error.
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
diet_guard.py (Tier 2c, kit v1.12; INDEX FIRST kit v1.15): nothing to
fill in. Wire its Read|Bash|PowerShell PreToolUse entry (settings.json
has it) and run `python tools/hooks/diet_guard.py --selftest`. It refuses
exactly once: the FIRST whole read of a file past ~10k tokens per session
comes back as the file's own index; the same call repeated passes with a
warning. Everything else is warn-only: a file's size before a later big
read, the missing limiter on a chatty shell command.
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
format_guard.py (Tier 3b, kit v1.19, a REFUSAL and a BLOCK): nothing to
fill in; it imports reference tools/format_lint.py (copy that to tools/
first and adapt its CONFIG block: kit folder, hooks/skills dirs,
settings path). Wire BOTH entries from settings.json (PreToolUse and
PostToolUse on Write|Edit|MultiEdit), run `python tools/hooks/format_guard.py
--selftest`. Before an edit of a settings file it refuses one that would
unwire, narrow or mis-point a SAFETY hook (or not parse); after an edit
of any kit thing it blocks one that leaves the thing without its header
(PURPOSE / INTENT / Search keys / See also) and names the rewrite
command. Add the settings-file rule to bash_guard.py (the kit copy has
it in GENERIC RULES) and the Stop twin from stop_tick.py. Then run
`python tools/format_lint.py` once: every tool and hook it names gets
its header by `--rewrite` after a read-only look, never by hand; and
`python tools/purpose_audit.py` creates FLAGS.md for the first audit
(see CONTRIBUTING.md and skills/flag).

THE LOOP LAW (kit v1.21, 2026-09-14): session_start.py runs the parent
loop's session group (reference tools/run_all.py) once a day before the
digest and ledgers the digest's size (digest_size.txt); stop_tick.py warns
CHANGELOG UNEXPORTED when commits sit past a changelog anchor (silent
without one). A project without run_all.py gets a one-line note, never a
failure. Both hooks' --selftest cover the new paths.


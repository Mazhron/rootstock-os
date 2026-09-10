Rootstock hooks (kit v1.10). Install per HOOKS_METHOD.md 'Bootstrap':
  tools/hooks/  <- these .py files (bash_guard.py: fill PROJECT RULES)
  .claude/settings.json  <- settings.json (merge if one exists)
  .gitignore  <- .claude/hooks_state.json, .claude/settings.local.json,
                 .claude/fanout_state.json
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

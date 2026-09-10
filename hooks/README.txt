Rootstock hooks (kit v1.9). Install per HOOKS_METHOD.md 'Bootstrap':
  tools/hooks/  <- these .py files (bash_guard.py: fill PROJECT RULES)
  .claude/settings.json  <- settings.json (merge if one exists)
  .gitignore  <- .claude/hooks_state.json, .claude/settings.local.json,
                 .claude/fanout_state.json
The scripts import the checkpoint script from the folder above them
(reference tools/checkpoint.py carries work_fingerprint + hook state).
fanout_guard.py (Tier 2b, the catastrophe-only circuit breaker): set
LIMITS with the CEO, run `python tools/hooks/fanout_guard.py --selftest`,
wire its every-tool PreToolUse entry. It refuses only a burst or flood
of sub-agent spawns or runaway token velocity (all self-clearing) and
warns on the rest; nothing for the CEO to type.

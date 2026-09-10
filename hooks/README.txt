Rootstock hooks (kit v1.9). Install per HOOKS_METHOD.md 'Bootstrap':
  tools/hooks/  <- these .py files (bash_guard.py: fill PROJECT RULES)
  .claude/settings.json  <- settings.json (merge if one exists)
  .gitignore  <- .claude/hooks_state.json, .claude/settings.local.json,
                 .claude/fanout_state.json, .claude/fanout_unlock.json
The scripts import the checkpoint script from the folder above them
(reference tools/checkpoint.py carries work_fingerprint + hook state).
fanout_guard.py (Tier 2b, the fan-out circuit breaker): copy it UNWIRED,
set LIMITS with the CEO, run `python tools/hooks/fanout_guard.py
--selftest`, and wire its every-tool PreToolUse entry LAST - it locks its
own files the moment the settings watcher sees it, and from then on only
the CEO's --allow-*/--resume commands move the rail.

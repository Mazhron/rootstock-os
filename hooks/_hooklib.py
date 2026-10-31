"""Shared plumbing for THE HOOKS (the CEO's ask 2026-09-06: "are there any
hooks we could create and add to our workflows?").

A hook is a script the HARNESS runs at a fixed moment (session start,
prompt submit, before a tool call, when the manager stops, before a
compaction). It reads one JSON object on stdin and answers on stdout:
plain text or {"hookSpecificOutput": {"additionalContext": ...}} is
injected into the manager's context; a PreToolUse "deny" refuses the tool
call and feeds the reason back; a Stop "block" refuses to end the turn
once. Wiring lives in .claude/settings.json (checked in - travels to both
workstations). Everything here is import-only.

PURPOSE: Shared plumbing every hook imports: reads the harness's JSON from
  stdin, emits JSON back for deny, block or context decisions, and resolves
  the project version; import-only, no side effects on its own.
INTENT: are there any hooks we could create and add to our workflows?

Search keys: hooks, harness hooks, settings.json, hook input, deny, block.
See also: docs/systems/tooling.md (the hooks section); HOOKS_METHOD.md
(portable method); tools/checkpoint.py (the counter the Stop hook ticks).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def read_input():
    """The harness's stdin JSON; {} on anything odd (a hook must never crash
    the turn over a parse error)."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def emit(obj):
    # ensure_ascii (the default) keeps Windows consoles out of the picture.
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()


def deny(reason):
    """PreToolUse: refuse the call; the reason reaches the manager."""
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                 "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})
    sys.exit(0)


def context(event, text):
    """Inject text into the manager's context (SessionStart etc.)."""
    emit({"hookSpecificOutput": {"hookEventName": event,
                                 "additionalContext": text}})


MODES = os.path.join(ROOT, ".claude", "rootstock_modes.json")   # committed: the CEO's switches
MODES_DEFAULT = {
    "route": "ladder",           # prompt hook ROUTE: "ladder" (v1.57, four layers + the index door) | "classic" (v1.33, workflows + tools)
    "resume_digest": "pointer",  # SessionStart on resume: "pointer" (v1.57, one line) | "full" (the whole digest, the old way)
    "big_write_warn": True,      # diet guard on Write: a BIG WRITE note past ~4k tokens of content (v1.57) | False = silent
    "effort_line": True,         # prompt hook: the EFFORT line when the matched entry asks another level (v1.57) | False
}


def modes():
    """THE MODES FILE (the CEO 2026-10-31, kit v1.57: "keep the old way
    stored ... as a baseline, and in case the new way is worse"): every
    behaviour v1.57 added sits behind one key here; the old code path stays
    in place and is selected by flipping the key. Missing file or key means
    the default above; a parse error means the defaults, never a crash."""
    out = dict(MODES_DEFAULT)
    try:
        with open(MODES, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            out.update({k: v for k, v in data.items() if k in MODES_DEFAULT})
    except Exception:
        pass
    return out


def mode(key, default=None):
    """One switch's value (see modes())."""
    return modes().get(key, MODES_DEFAULT.get(key, default))


def project_version():
    try:
        import re
        txt = open(os.path.join(ROOT, "project.godot"), encoding="utf-8").read()
        m = re.search(r'config/version="([^"]+)"', txt)
        return m.group(1) if m else "?"
    except OSError:
        return "?"

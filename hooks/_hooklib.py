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


def project_version():
    try:
        import re
        txt = open(os.path.join(ROOT, "project.godot"), encoding="utf-8").read()
        m = re.search(r'config/version="([^"]+)"', txt)
        return m.group(1) if m else "?"
    except OSError:
        return "?"

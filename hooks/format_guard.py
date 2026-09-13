"""THE FORMAT GUARD - Tier 3b (PreToolUse + PostToolUse on Write|Edit|MultiEdit).

PURPOSE: enforce THE FORMAT LAW at the edit. BEFORE a Write/Edit lands on
  a settings file (.claude/settings.json or the kit's hooks/settings.json)
  it computes the would-be text and REFUSES it if any SAFETY hook would be
  unwired, narrowed or pointed at a missing script - so no prompt, brief
  or contributed patch can switch a guard off. AFTER a Write/Edit lands
  on any kit thing or its original, it runs the format lint on that one
  file and BLOCKS (the reason comes back, the edit stays) until the
  header is right - the rewrite command is in the reason.
INTENT: the CEO 2026-09-13: "Anything without proper format should be
  flagged, a script should re-write it after review-only audit. This will
  be a law and may need this to be a hook somehow so that no one can
  inject a prompt that overrides safety protocols." The lint says what is
  wrong; the hook is what makes it a law instead of a reminder.

Stateless; pattern matching plus one JSON parse; ~0.3 s per edit. A
Stop-hook twin (stop_tick.py) refuses to end the turn while the live
settings file fails the safety check, and the shell guard refuses shell
writes into a settings file, so the only way to change hook wiring is an
Edit this guard can see. `--selftest` runs the in-process checks.

Search keys: format guard, safety wiring, settings.json guard, unwire a
hook, PostToolUse block, format law hook, Tier 3b.
See also: tools/format_lint.py (the checks + the rewrite); tools/hooks/
hygiene_guard.py (Tier 3, the reminders); tools/hooks/stop_tick.py (the
Stop twin); tools/hooks/bash_guard.py (the shell twin); HOOKS_METHOD.md
(Tier 3b); "Future Project MDs/CONTRIBUTING.md" (the law for
contributors); WORKFLOWS.md "Add or change a harness hook".
"""
import os
import sys

from _hooklib import ROOT, read_input, emit, deny

try:
    import format_lint as fl
except Exception:  # noqa: BLE001 - a hook never crashes the turn
    fl = None


def would_be_text(tool, tin, current):
    """The file text after this edit, or None when it cannot be known."""
    if tool == "Write":
        return tin.get("content") or ""
    if current is None:
        return None
    if tool == "Edit":
        old, new = tin.get("old_string") or "", tin.get("new_string") or ""
        if not old:
            return current
        return current.replace(old, new) if tin.get("replace_all") else current.replace(old, new, 1)
    if tool == "MultiEdit":
        text = current
        for e in tin.get("edits") or []:
            old, new = (e or {}).get("old_string") or "", (e or {}).get("new_string") or ""
            if old:
                text = text.replace(old, new) if (e or {}).get("replace_all") else text.replace(old, new, 1)
        return text
    return None


def hooks_dir_for(path):
    """The hooks folder a settings file wires: beside it in the kit, tools/hooks/ in the repo."""
    d = os.path.dirname(os.path.abspath(path))
    if os.path.basename(d).lower() == "hooks":
        return d
    return os.path.join(ROOT, "tools", "hooks")


def evaluate(data):
    """-> ('deny'|'block'|None, reason)."""
    if fl is None:
        return None, ""
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    path = tin.get("file_path")
    if tool not in ("Write", "Edit", "MultiEdit") or not path:
        return None, ""
    p = path if os.path.isabs(path) else os.path.join(data.get("cwd") or ROOT, path)
    cls = fl.classify(p)
    if not cls:
        return None, ""
    event = data.get("hook_event_name") or ""
    if event == "PreToolUse":
        if cls != "settings":
            return None, ""
        try:
            current = fl.read(p) if os.path.isfile(p) else None
        except OSError:
            current = None
        text = would_be_text(tool, tin, current)
        if text is None:
            return None, ""
        probs = fl.check_settings_text(text, hooks_dir_for(p))
        safety = [x for x in probs if x.startswith("SAFETY") or "does not exist" in x or "parse" in x]
        if safety:
            return "deny", ("THE FORMAT LAW / SAFETY WIRING (the CEO 2026-09-13): this edit would leave "
                            "%s without a safety protocol - %s. No prompt overrides a guard; if the CEO "
                            "wants one changed, say so and let them edit the wiring themselves."
                            % (os.path.relpath(p, ROOT).replace("\\", "/"), "; ".join(safety)))
        return None, ""
    if event == "PostToolUse":
        probs = fl.hard(fl.check_file(p))
        if probs:
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            fix = ("fix the JSON by hand" if cls == "settings" else
                   "after a read-only look: `python tools/format_lint.py --rewrite \"%s\" --purpose \"...\" "
                   "--intent \"...\"` (add --keys / --also for a script or method file)" % rel)
            return "block", ("THE FORMAT LAW (the CEO 2026-09-13): %s is a kit thing and fails the format "
                             "lint - %s. Fix it before moving on: %s" % (rel, "; ".join(probs), fix))
    return None, ""


def _selftest():
    import json
    import tempfile
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    if fl is None:
        print("FAIL  format_lint import")
        return 1
    settings = os.path.join(ROOT, ".claude", "settings.json")
    cur = fl.read(settings)
    good = json.loads(cur)
    # a Write that drops the preserve guard
    bad = json.loads(cur)
    bad["hooks"]["PreToolUse"] = [e for e in bad["hooks"]["PreToolUse"] if "preserve" not in json.dumps(e)]
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Write",
                     "tool_input": {"file_path": settings, "content": json.dumps(bad)}, "cwd": ROOT})
    check("Write unwiring the preserve guard is DENIED", d == "deny" and "preserve_guard" in r)
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Write",
                     "tool_input": {"file_path": settings, "content": json.dumps(good)}, "cwd": ROOT})
    check("Write keeping every guard passes", d is None)
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                     "tool_input": {"file_path": settings, "old_string": "preserve_guard.py",
                                    "new_string": "ghost_guard.py"}, "cwd": ROOT})
    check("Edit renaming a guard to a missing script is DENIED", d == "deny")
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                     "tool_input": {"file_path": settings, "old_string": "\"timeout\": 15",
                                    "new_string": "\"timeout\": 16"}, "cwd": ROOT})
    check("Edit touching a timeout passes", d is None)
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Write",
                     "tool_input": {"file_path": settings, "content": "{broken"}, "cwd": ROOT})
    check("Write of unparsable settings is DENIED", d == "deny" and "parse" in r)
    d, r = evaluate({"hook_event_name": "PreToolUse", "tool_name": "Write",
                     "tool_input": {"file_path": os.path.join(ROOT, "tools", "hooks", "diet_guard.py"),
                                    "content": "x"}, "cwd": ROOT})
    check("PreToolUse ignores non-settings files", d is None)
    with tempfile.TemporaryDirectory() as td:
        # PostToolUse on an in-scope file: simulate via a kit-relative temp inside the kit? No -
        # never write junk into the kit. Use the classify + check path on a real passing file instead.
        d, r = evaluate({"hook_event_name": "PostToolUse", "tool_name": "Edit",
                         "tool_input": {"file_path": os.path.join(ROOT, "tools", "hooks", "format_guard.py"),
                                        "old_string": "a", "new_string": "b"}, "cwd": ROOT})
        check("PostToolUse on a formatted hook is silent", d is None)
        out = os.path.join(td, "x.gd")
        d, r = evaluate({"hook_event_name": "PostToolUse", "tool_name": "Write",
                         "tool_input": {"file_path": out, "content": "x"}, "cwd": ROOT})
        check("PostToolUse ignores an out-of-scope file", d is None)
    d, r = evaluate({}, )
    check("empty input is silent", d is None)
    print("format_guard selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    data = read_input()
    if not data.get("tool_name"):
        return
    try:
        verdict, reason = evaluate(data)
    except Exception as e:  # noqa: BLE001 - never crash the turn
        verdict, reason = None, "format guard skipped (%s)" % e
    if verdict == "deny":
        deny("[HOOK format_guard] " + reason)
    if verdict == "block":
        emit({"decision": "block", "reason": "[HOOK format_guard] " + reason})


if __name__ == "__main__":
    main()

"""PreToolUse guard on Agent/Task: a work brief carries its laws or it
does not dispatch (the CEO 2026-09-26: "make these processes more fool
proof... through hooks").

SUBAGENTS.md rule 3 (the stamp template), the budget line, rule 13 (the
preservation line) and rule 14 (the intent line) were discipline; this
makes them mechanical. A dispatch to a WORK agent type whose prompt is
missing any required piece is refused with the missing pieces named, so
a malformed brief costs a refusal, never a spent employee. Read-only
searcher types (Explore, Plan, claude-code-guide, statusline-setup) pass
untouched - they edit nothing and their fan-out is fanout_guard's job.

PURPOSE: PreToolUse guard that refuses an Agent/Task dispatch to a work
  agent type when the brief is missing the stamp template (STAMP/TOOLS/
  WORKFLOW), the INTENT line ask, the budget line or THE PRESERVATION LAW
  line; silent for read-only agent types and complete briefs.
INTENT: the CEO 2026-09-26: "Can we make these processes more fool proof
  in any way through hooks" - the brief laws existed, nothing enforced
  them at the dispatch moment.

Search keys: brief guard, delegation, stamp line, budget line,
preservation line, intent line, Agent tool, dispatch refusal.
See also: SUBAGENTS.md (rules 3, 13, 14); .claude/skills/brief;
tools/hooks/delegation_auditor.py (the result end);
tools/hooks/fanout_guard.py (spawn rate, a different law).
"""
import sys

from _hooklib import deny, read_input

# Searcher types: read-only, no employee laws to carry.
READONLY_TYPES = {"explore", "plan", "claude-code-guide", "statusline-setup"}

# piece -> the substring a complete brief must carry (the /brief skill
# emits all of these verbatim).
REQUIRED = {
    "the STAMP line (rule 3)": "STAMP:",
    "the TOOLS line (rule 3)": "TOOLS:",
    "the WORKFLOW line (rule 11)": "WORKFLOW:",
    "the INTENT line (rule 14)": "INTENT:",
    "the budget line (rule 3: ~30 tool calls, STOP and report)": "STOP and report",
    "THE PRESERVATION LAW line (rule 13)": "THE PRESERVATION LAW",
}


def missing_pieces(prompt, subagent_type):
    """The REQUIRED pieces absent from this brief; [] for read-only types."""
    if (subagent_type or "").strip().lower() in READONLY_TYPES:
        return []
    text = prompt or ""
    return [name for name, token in REQUIRED.items() if token not in text]


def main():
    data = read_input()
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    gaps = missing_pieces(ti.get("prompt", ""), ti.get("subagent_type", ""))
    if gaps:
        deny("[HOOK brief_guard] BRIEF INCOMPLETE - this dispatch would start an "
             "employee without its laws. Missing: %s. Compose the brief through the "
             "/brief skill (SUBAGENTS.md rules 3, 11, 13, 14 paste the exact lines); "
             "read-only searches go to the Explore or Plan agent type instead."
             % "; ".join(gaps))
    sys.exit(0)


def _selftest():
    """Pure checks on missing_pieces(); reads nothing, writes nothing."""
    fails = 0

    def ok(label, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + label)
        fails += not cond

    full = ("Do the task. THE PRESERVATION LAW: no deletion code. If you exceed "
            "~30 tool calls or fail the same step twice, STOP and report what you "
            "have. End with STAMP: ... TOOLS: ... WORKFLOW: ... INTENT: ...")
    ok("a complete brief passes", missing_pieces(full, "general-purpose") == [])
    ok("an empty brief names every piece", len(missing_pieces("", "claude")) == len(REQUIRED))
    gaps = missing_pieces(full.replace("INTENT:", "intent -"), "claude")
    ok("a missing INTENT line is named alone", gaps == ["the INTENT line (rule 14)"])
    gaps = missing_pieces(full.replace("STOP and report", "do your best"), None)
    ok("a missing budget line is named (unset type = work type)",
       gaps == ["the budget line (rule 3: ~30 tool calls, STOP and report)"])
    ok("an Explore search passes with no template", missing_pieces("find X", "Explore") == [])
    ok("a Plan agent passes with no template", missing_pieces("plan X", "plan") == [])
    print("brief_guard selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

"""PreToolUse guard on Agent/Task: a work brief carries its laws or it
does not dispatch (the CEO 2026-09-26: "make these processes more fool
proof... through hooks").

SUBAGENTS.md rule 3 (the stamp template), the budget line, rule 13 (the
preservation line) and rule 14 (the intent line) were discipline; this
makes them mechanical. A dispatch to a WORK agent type whose prompt is
missing any required piece is refused with the missing pieces named, so
a malformed brief costs a refusal, never a spent employee. Read-only
searcher types (Explore, Plan, claude-code-guide, statusline-setup and the
project's own explore and lookup agents) carry no brief laws - they edit
nothing and their fan-out is fanout_guard's job - but since kit v1.54 they
DO carry THE EMPLOYEE MODEL RULE: the harness's Explore type has no model
of its own, so a model-less search inherited the manager's tier silently
(the usage sheet showed it, the CEO 2026-10-22: "give the search and lookup
ones a cheaper model"). A read-only dispatch now passes only when its
model is in the call or PINNED by its agent file (.claude/agents/<type>.md,
`model:` in the front matter); the two harness helpers that carry their
own model (claude-code-guide, statusline-setup) pass as before.

PURPOSE: PreToolUse guard that refuses an Agent/Task dispatch to a work
  agent type when the brief is missing the stamp template (STAMP/TOOLS/
  WORKFLOW), the INTENT line ask, the budget line or THE PRESERVATION LAW
  line; also refuses THE EMPLOYEE MODEL RULE (SUBAGENTS.md rule 6): a
  dispatch whose tool_input.model is missing/empty, or matches Fable
  (case-insensitive, even inside a longer id like "claude-fable-5-1"),
  since a model-less dispatch inherits the parent model (Fable), and
  Fable is never an employee; read-only agent types skip the brief
  pieces but keep the model rule, their model taken from the call or
  from the `model:` pin of .claude/agents/<type>.md (kit v1.54); silent
  for complete briefs and pinned searches.
INTENT: the CEO 2026-09-26: "Can we make these processes more fool proof
  in any way through hooks" - the brief laws existed, nothing enforced
  them at the dispatch moment. Extended 2026-09-30 per the CEO's rule 6
  ruling (2026-09-29): "You are the manager, you make the decision... I
  believe Fable is the only one you cannot use per my decision to save on
  tokens" - the harness inherits Fable silently when no model is passed.
  Extended 2026-10-22 (kit v1.54) to read-only types after the usage
  sheet showed searches on the manager's tier: the CEO, "give the search
  and lookup ones a cheaper model."

Search keys: brief guard, delegation, stamp line, budget line,
preservation line, intent line, Agent tool, dispatch refusal, employee
model rule, fable, model field, rule 6, pinned model, agent file,
explore agent, lookup agent, read-only search.
See also: SUBAGENTS.md (rules 3, 6, 13, 14); .claude/skills/brief;
tools/hooks/delegation_auditor.py (the result end);
tools/hooks/fanout_guard.py (spawn rate, a different law);
.claude/agents/explore.md, .claude/agents/lookup.md (the pinned searchers).
"""
import os
import re
import sys

from _hooklib import ROOT, deny, read_input

# Searcher types: read-only, no brief laws to carry (the model rule still applies).
READONLY_TYPES = {"explore", "plan", "claude-code-guide", "statusline-setup", "lookup"}
# Harness-defined helpers whose own definition carries a model: never model-less.
HARNESS_PINNED = {"claude-code-guide", "statusline-setup"}
# Project agent files: <type>.md with `model:` in the front matter pins the dispatch's model.
AGENTS_DIR = os.path.join(ROOT, ".claude", "agents")
_MODEL_LINE = re.compile(r"^model:\s*(\S+)", re.M)

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


# THE EMPLOYEE MODEL RULE (the CEO 2026-09-29, SUBAGENTS.md rule 6): a
# dispatch with no `model` field inherits the parent's model, and the
# parent is Fable - who is never an employee. _MODEL_UNCHECKED is the
# sentinel default so the existing 2-arg callers keep working unchanged.
_MODEL_UNCHECKED = object()
_FABLE_RE = re.compile(r"fable", re.I)
MODEL_RULE_MSG = ("THE EMPLOYEE MODEL RULE (the CEO 2026-09-29, SUBAGENTS.md rule 6): "
                  "Fable is never an employee, and a dispatch with no model inherits "
                  "Fable. Pass model=haiku|sonnet|opus per SUBAGENTS.md THE ASSIGNMENTS.")
SEARCH_MODEL_MSG = ("THE EMPLOYEE MODEL RULE for a read-only search (the CEO 2026-10-22, kit "
                    "v1.54): a search or lookup dispatch with no model inherits Fable. Use the "
                    "project's explore or lookup agent (.claude/agents, pinned to haiku) or "
                    "pass model=haiku.")


def pinned_model_text(text):
    """The `model:` value in an agent file's front matter ('' when none)."""
    if not (text or "").startswith("---"):
        return ""
    end = text.find("\n---", 3)
    head = text[3:end] if end != -1 else text[3:]
    m = _MODEL_LINE.search(head)
    return m.group(1).strip() if m else ""


def pinned_model(subagent_type, agents_dir=AGENTS_DIR):
    """The model .claude/agents/<type>.md pins for this dispatch, '' when no file."""
    name = (subagent_type or "").strip()
    if not name:
        return ""
    for cand in (name, name.lower()):
        p = os.path.join(agents_dir, cand + ".md")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return pinned_model_text(f.read())
            except OSError:
                return ""
    return ""


def missing_pieces(prompt, subagent_type, model=_MODEL_UNCHECKED, pinned=""):
    """The REQUIRED pieces absent from this brief; the brief pieces are skipped
    for read-only types. `model` is optional: pass the dispatch's
    tool_input.model to also check THE EMPLOYEE MODEL RULE (a missing or
    Fable-inheriting model is reported as one more named piece: MODEL_RULE_MSG
    for a work type, SEARCH_MODEL_MSG for a read-only one); `pinned` is the
    model the dispatch's agent file pins (pinned_model), taken when the call
    sets none. The sentinel default leaves the model unchecked, so existing
    2-arg callers are unaffected; the harness's own pinned helpers pass."""
    kind = (subagent_type or "").strip().lower()
    gaps = []
    if kind not in READONLY_TYPES:
        text = prompt or ""
        gaps = [name for name, token in REQUIRED.items() if token not in text]
    if model is not _MODEL_UNCHECKED and kind not in HARNESS_PINNED:
        effective = (model or "").strip() or (pinned or "").strip()
        if not effective or _FABLE_RE.search(effective):
            gaps.append(SEARCH_MODEL_MSG if kind in READONLY_TYPES else MODEL_RULE_MSG)
    return gaps


def main():
    data = read_input()
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    kind = ti.get("subagent_type", "")
    gaps = missing_pieces(ti.get("prompt", ""), kind, ti.get("model", ""), pinned_model(kind))
    if gaps:
        deny("[HOOK brief_guard] BRIEF INCOMPLETE - this dispatch would start an "
             "employee without its laws. Missing: %s. Compose the brief through the "
             "/brief skill (SUBAGENTS.md rules 3, 6, 11, 13, 14 paste the exact lines); "
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

    # THE EMPLOYEE MODEL RULE (rule 6): checked only when a third arg is given.
    ok("a complete brief with model=sonnet passes",
       missing_pieces(full, "general-purpose", "sonnet") == [])
    ok("model=fable is refused naming the model rule alone",
       missing_pieces(full, "general-purpose", "fable") == [MODEL_RULE_MSG])
    ok("model=claude-fable-5-1 is refused (fable inside a longer id)",
       missing_pieces(full, "general-purpose", "claude-fable-5-1") == [MODEL_RULE_MSG])
    ok("a missing model is refused",
       missing_pieces(full, "general-purpose", "") == [MODEL_RULE_MSG])
    # THE PINNED SEARCH (kit v1.54): read-only types keep the model rule.
    ok("an Explore search with no model and no agent pin is refused (kit v1.54)",
       missing_pieces("find X", "Explore", "") == [SEARCH_MODEL_MSG])
    ok("an explore dispatch pinned to haiku by its agent file passes with no model",
       missing_pieces("find X", "explore", "", pinned="haiku") == [])
    ok("a lookup pinned to fable is refused",
       missing_pieces("what is X", "lookup", "", pinned="claude-fable-5-1") == [SEARCH_MODEL_MSG])
    ok("claude-code-guide passes with no model (the harness pins it)",
       missing_pieces("how do I", "claude-code-guide", "") == [])
    ok("a work dispatch pinned to sonnet by its agent file passes with no model",
       missing_pieces(full, "general-purpose", "", pinned="sonnet") == [])
    ok("the front matter parser reads model:",
       pinned_model_text("---\nname: explore\nmodel: haiku\ntools: Read\n---\n\n# explore\n") == "haiku")
    ok("no front matter means no pin", pinned_model_text("# explore\nmodel: haiku\n") == "")
    ok("a missing agents dir means no pin", pinned_model("explore", os.path.join(ROOT, "no-such-dir")) == "")
    ok("two-arg callers are unaffected (model left unchecked by default)",
       missing_pieces(full, "general-purpose") == [])
    print("brief_guard selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

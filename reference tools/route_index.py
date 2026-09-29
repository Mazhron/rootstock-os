"""THE ROUTE LINE (the CEO 2026-09-28, after Kelsey Hightower's Zero Token
Architecture: "infer once, export the logic, run it without inference" -
the one place Rootstock still inferred every turn was WHICH exported thing
handles this prompt). The prompt end of the script rule: match a prompt's
words against every WORKFLOWS.md entry (its heading + WHEN line) and every
reference tool's Search keys line, and name the scripted way before the
first tool call, so the routing is a lookup and not a per-turn inference.

Usage:
    python tools/route_index.py --match "<prompt text>"   # what the prompt hook would say
    python tools/route_index.py --selftest

No ledger: a route hit is a pointer, not a result (the tool it names keeps
its own ledger). Scoring is lesson_log's: a multi-word key needs every word
(2 points), a single word scores 1; prompts under four content words never
match; at most two workflows and two tools are named, best first.

PURPOSE: Match a prompt against the headings and WHEN lines of WORKFLOWS.md
  and the Search keys of every tools/ and tools/hooks/ script, and print the
  ROUTE line the prompt hook relays, so an existing workflow or script is
  named before the manager re-derives it.
INTENT: the CEO 2026-09-28, adopting the ZTA gate: "get done what you think
  should get done" - the check "does software already handle this" becomes a
  hook lookup at zero tokens instead of the manager's inference every turn.

Search keys: route line, route index, which workflow, which script, scripted
way, zero token, script rule prompt end, existing tool lookup.
See also: WORKFLOWS.md (the registry it reads); tools/lesson_log.py (the
matcher and stopwords it reuses); tools/hooks/prompt_gauge.py (the hook that
prints the line); docs/index/laws.md "The script rule".
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import lesson_log as _ll  # noqa: E402

REGISTRY = os.path.join(ROOT, "WORKFLOWS.md")
TOOL_GLOBS = ("tools/*.py", "tools/hooks/*.py")
WF_MIN_SCORE = 3       # a heading word plus a WHEN phrase, or three heading words
TOOL_MIN_SCORE = 2     # one multi-word Search key, or two single keys
WF_CAP = 2
TOOL_CAP = 2
SPLIT = re.compile(r"[,;:/()\-]|\bor\b|\band\b")
DOC_CLOSE = '"' * 3


def _phrases(text):
    return [p.strip() for p in SPLIT.split(text or "") if len(_ll.words(p)) >= 1]


def workflow_entries(text=None):
    """[{heading, line, keys[]}] per `## ` entry: heading words as single keys,
    heading and WHEN phrases as multi-word keys."""
    if text is None:
        try:
            with open(REGISTRY, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return []
    out = []
    cur = None
    for i, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("## "):
            head = raw[3:].strip()
            cur = {"heading": head, "line": i, "keys": [], "when": []}
            cur["keys"] = list(dict.fromkeys(_ll.words(head)))
            cur["keys"] += [p for p in _phrases(head) if len(_ll.words(p)) > 1]
            out.append(cur)
            continue
        if cur is None:
            continue
        if raw.startswith("WHEN:"):
            cur["when"] = [raw[5:].strip()]
        elif raw.startswith("STEPS") and cur["when"]:
            cur["keys"] += [p for p in _phrases(" ".join(cur["when"])) if len(_ll.words(p)) > 1]
            cur["when"] = []
        elif cur["when"] and raw.strip():
            cur["when"].append(raw.strip())
    return out


def tool_entries():
    """[{heading, line, keys[], path}] per script with a Search keys line."""
    out = []
    for pat in TOOL_GLOBS:
        for path in sorted(glob.glob(os.path.join(ROOT, pat))):
            base = os.path.basename(path)
            if base.startswith("_"):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
            except OSError:
                continue
            keys, grab, start = [], False, 0
            for i, raw in enumerate(lines[:80], 1):
                m = re.match(r"\s*Search keys:\s*(.*)$", raw)
                if m:
                    keys.append(m.group(1))
                    grab, start = True, i
                    continue
                if grab:
                    if not raw.strip() or raw.lstrip().startswith(("See also", DOC_CLOSE)):
                        break
                    keys.append(raw.strip())
            if keys:
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                ks = [k.strip().rstrip(".") for k in " ".join(keys).split(",") if k.strip()]
                out.append({"heading": rel, "line": start, "keys": ks, "path": rel})
    return out


def _score(prompt, ents, min_score, cap):
    saved = _ll.MIN_SCORE
    _ll.MIN_SCORE = min_score
    try:
        hits = _ll.match(prompt, ents)
    finally:
        _ll.MIN_SCORE = saved
    return hits[:cap]


def match(prompt):
    """(workflow hits, tool hits) - each [(score, entry)], best first."""
    return (_score(prompt, workflow_entries(), WF_MIN_SCORE, WF_CAP),
            _score(prompt, tool_entries(), TOOL_MIN_SCORE, TOOL_CAP))


def match_lines(prompt):
    """The lines the prompt hook prints (empty on a normal prompt)."""
    wf, tl = match(prompt)
    if not wf and not tl:
        return []
    out = ["ROUTE: the scripted way exists - check it before re-deriving (THE SCRIPT RULE):"]
    for _, e in wf:
        out.append("  WORKFLOWS.md line %d \"%s\"" % (e["line"], e["heading"]))
    for _, e in tl:
        out.append("  %s - %s" % (e["path"], "; ".join(e["keys"][:3])))
    return out


def _selftest():
    fails = 0
    ok = any("WORKFLOWS.md line" in x for x in match_lines(
        "ship this docs-only batch: commit, export the changelog and push, no build"))
    print(("PASS  " if ok else "FAIL  ") + "a ship prompt names a WORKFLOWS entry")
    fails += not ok
    ok = any("tools/checkpoint.py" in x for x in match_lines(
        "reset the checkpoint counter and read the context budget before we clear"))
    print(("PASS  " if ok else "FAIL  ") + "a checkpoint prompt names the checkpoint tool by its Search keys")
    fails += not ok
    ok = match_lines("standup") == []
    print(("PASS  " if ok else "FAIL  ") + "a short prompt gets no route line")
    fails += not ok
    ok = match_lines("the pine tree looks too dark against the winter snow tiles") == []
    print(("PASS  " if ok else "FAIL  ") + "a game-art prompt gets no route line")
    fails += not ok
    ok = len(workflow_entries()) >= 20 and len(tool_entries()) >= 20
    print(("PASS  " if ok else "FAIL  ") + "the registry and the tools both index")
    fails += not ok
    print("route_index selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(_selftest())
    if "--match" in argv:
        print("\n".join(match_lines(argv[argv.index("--match") + 1])) or "(no route line)")
        sys.exit(0)
    print(__doc__.split("\n\n")[1])

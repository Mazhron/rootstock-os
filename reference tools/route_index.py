"""THE ROUTE LINE (the CEO 2026-09-28, after Kelsey Hightower's Zero Token
Architecture: "infer once, export the logic, run it without inference" -
the one place Rootstock still inferred every turn was WHICH exported thing
handles this prompt). The prompt end of the script rule: match a prompt's
words against every WORKFLOWS.md entry (its heading + WHEN line) and every
reference tool's Search keys line, and name the scripted way before the
first tool call, so the routing is a lookup and not a per-turn inference.

THE RETRIEVAL LADDER (kit v1.57, the CEO 2026-10-31: "I'm trying to see how
you use the knowledge bases and indexes in order. I would like to fine tune
the efficiency of your order."): the classic line named the how (a WORKFLOWS
entry) and the tool; the manager then improvised the rest, one grep per
turn, with synonyms it happened to think of, and the CEO's own test prompt
("Please add a gnome to my game") got no line at all. route_block() does
the whole retrieval before the manager's first turn, in one free process:
  1. the WORKFLOWS entries and tools (the how) - the classic matcher, unchanged;
  2. the INDEX lines (where the facts live): docs/index/MASTER_INDEX.md and
     KNOWLEDGE_INDEX.md entries whose words the prompt hits;
  3. the FILES that already exist: paths under the repo whose name is made
     of the prompt's own words (a gnome.tscn when the prompt says gnome);
  4. EFFORT: the level the matched entry's `EFFORT:` line asks for, against
     the level in use, so routine work is not thought through at the top;
and when none of the four hits a task-shaped prompt it prints THE INDEX
DOOR once per session (the master index's own headings) instead of staying
silent, so the manager picks a section by eye in the first batch instead
of guessing synonyms across three turns. The classic two-line output is
match_lines(), byte-for-byte as before; the prompt hook picks by the modes
file (.claude/rootstock_modes.json, route = ladder | classic). Both faces
ledger one ROUTE line in docs/history/lesson_runs.txt so
tools/retrieval_eval.py --route can score them against each other.

Usage:
    python tools/route_index.py --match "<prompt text>"   # the classic line
    python tools/route_index.py --block "<prompt text>"   # the ladder block (no ledger, no TOC state)
    python tools/route_index.py --selftest

Scoring is lesson_log's: a multi-word key needs every word (2 points), a
single word scores 1; prompts under four content words never match; at most
two workflows and two tools are named, best first; index lines and files
three each.

PURPOSE: Match a prompt against the headings and WHEN lines of WORKFLOWS.md,
  the Search keys of every tools/ and tools/hooks/ script, and (v1.57) the
  index files' entry lines and the repo's own file names, and print the
  ROUTE line or block the prompt hook relays, so an existing workflow,
  script, topic section or file is named before the manager re-derives it,
  with the index headings as the door when nothing hits.
INTENT: the CEO 2026-09-28, adopting the ZTA gate: "get done what you think
  should get done" - the check "does software already handle this" becomes a
  hook lookup at zero tokens instead of the manager's inference every turn;
  and 2026-10-31: indexes before files, files before code, every retrieval
  that can run before the manager's first turn runs in the hook.

Search keys: route line, route index, which workflow, which script, scripted
way, zero token, script rule prompt end, existing tool lookup, retrieval
ladder, index door, route block, where the facts live, effort line.
See also: WORKFLOWS.md (the registry it reads); docs/index/MASTER_INDEX.md
and KNOWLEDGE_INDEX.md (the index layer); tools/lesson_log.py (the matcher
and stopwords it reuses); tools/hooks/prompt_gauge.py (the hook that prints
the line or the block); tools/retrieval_eval.py (--route scores both
faces); docs/index/laws.md "The script rule"; WORKFLOW_METHOD.md "The seed
entry: Act on a prompt".
"""
import glob
import json
import os
import re
import sys
import time

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

# ---- the ladder's layers (v1.57) ----
INDEX_FILES = ("docs/index/MASTER_INDEX.md", "KNOWLEDGE_INDEX.md")
INDEX_MIN_SCORE = 2    # two prompt words on one index line, or one phrase
INDEX_CAP = 3
FILES_CAP = 3
FILE_EXT = (".json", ".tres", ".tscn", ".gd", ".cs", ".py", ".js", ".ts", ".csv",
            ".yaml", ".yml", ".toml", ".cfg", ".txt")
FILE_WALK_CAP = 6000   # files looked at, at most, per prompt
SKIP_DIRS = {".git", ".godot", ".import", "node_modules", "__pycache__", ".claude",
             "_retired", "history", "Future Project MDs", "exports", "build", "dist"}
# Words too generic to route on by themselves (the index and file layers only).
GENERIC = set("""game project file files folder add new make create build use using update
change fix please need want like work thing things data main test tests index config
readme doc docs note notes list item items part parts version tool tools script scripts
system systems""".split())
LADDER_MIN_WORDS = 3   # content words for the index, file and door layers ("add a gnome to my game" is three)
TOC_MIN_WORDS = 3      # a task-shaped prompt with a specific word gets the door; "run it again" does not
TOC_CAP = 30
ROUTE_STATE = os.path.join(ROOT, ".claude", "route_state.json")   # gitignored: the door once per session
KEEP_SESSIONS = 20


def _phrases(text):
    return [p.strip() for p in SPLIT.split(text or "") if len(_ll.words(p)) >= 1]


def workflow_entries(text=None):
    """[{heading, line, keys[], effort}] per `## ` entry: heading words as single
    keys, heading and WHEN phrases as multi-word keys; an `EFFORT:` line
    (v1.57, optional) is the level the entry asks for."""
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
            cur = {"heading": head, "line": i, "keys": [], "when": [], "effort": ""}
            cur["keys"] = list(dict.fromkeys(_ll.words(head)))
            cur["keys"] += [p for p in _phrases(head) if len(_ll.words(p)) > 1]
            out.append(cur)
            continue
        if cur is None:
            continue
        if raw.startswith("WHEN:"):
            cur["when"] = [raw[5:].strip()]
        elif raw.startswith("EFFORT:"):
            lvl = raw[7:].strip().split()
            cur["effort"] = lvl[0].lower().strip(".,;") if lvl else ""
        elif raw.startswith("STEPS") and cur["when"]:
            cur["keys"] += [p for p in _phrases(" ".join(cur["when"])) if len(_ll.words(p)) > 1]
            cur["when"] = []
        elif cur["when"] and raw.strip() and not raw.startswith("EFFORT:"):
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
    """THE CLASSIC LINE (v1.33, kept byte-for-byte as the old way): the lines
    the prompt hook prints in route=classic mode (empty on a normal prompt)."""
    wf, tl = match(prompt)
    if not wf and not tl:
        return []
    out = ["ROUTE: the scripted way exists - check it before re-deriving (THE SCRIPT RULE):"]
    for _, e in wf:
        out.append("  WORKFLOWS.md line %d \"%s\"" % (e["line"], e["heading"]))
    for _, e in tl:
        out.append("  %s - %s" % (e["path"], "; ".join(e["keys"][:3])))
    return out


# ------------------------------------------------------- the ladder (v1.57) --
def _norm(w):
    """lesson_log's crude stem leaves "gnome" whole and turns "gnomes" into
    "gnom"; the index and file layers compare a trailing-e-less form so the
    singular in a prompt meets the plural in an index line. The classic
    matcher is untouched."""
    return w[:-1] if len(w) > 3 and w.endswith("e") else w


def _specific(ws):
    return [_norm(w) for w in ws if w not in GENERIC]


def index_entries(text=None, rel="docs/index/MASTER_INDEX.md"):
    """[{heading, line, keys[], path}] per entry line (`- ...` bullets and `## `
    headings) of one index file: the line's specific words as single keys,
    its phrases as multi-word keys. `text` given = pure (selftest)."""
    if text is None:
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return []
    out = []
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not (s.startswith("- ") or s.startswith("## ")):
            continue
        body = s[2:] if s.startswith("- ") else s[3:]
        body = re.sub(r"\]\([^)]*\)", "", body)          # markdown link targets out
        single = list(dict.fromkeys(_specific(_ll.words(body))))
        if not single:
            continue
        keys = single + [p for p in _phrases(body) if len(_specific(_ll.words(p))) > 1]
        out.append({"heading": body[:110], "line": i, "keys": keys, "path": rel})
    return out


def index_hits(prompt):
    """[(score, entry)] over every index file, best first, INDEX_CAP at most;
    the prompt's generic words never count."""
    have = set(_specific(_ll.words(prompt)))
    if len(have) < 1:
        return []
    hits = []
    for rel in INDEX_FILES:
        for e in index_entries(rel=rel):
            score = 0
            for key in e["keys"]:
                kw = _specific(_ll.words(key))
                if kw and all(w in have for w in kw):
                    score += 2 if len(kw) > 1 else 1
            if score >= INDEX_MIN_SCORE:
                hits.append((score, e))
    hits.sort(key=lambda t: (-t[0], t[1]["path"], t[1]["line"]))
    return hits[:INDEX_CAP]


def _stem_words(name):
    base = os.path.splitext(name)[0]
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)      # camelCase -> two words
    return _specific(_ll.words(re.sub(r"[_\-.]+", " ", base)))


_FILES = {}


def file_list(root=ROOT):
    """The repo's candidate files (relpaths, FILE_EXT only, SKIP_DIRS pruned,
    FILE_WALK_CAP at most), walked once per process and cached."""
    if root in _FILES:
        return _FILES[root]
    out = []
    n = 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            n += 1
            if n > FILE_WALK_CAP:
                _FILES[root] = out
                return out
            if f.lower().endswith(FILE_EXT):
                out.append(os.path.relpath(os.path.join(d, f), root).replace("\\", "/"))
    _FILES[root] = out
    return out


def file_hits(prompt, root=ROOT, walk=None):
    """[(score, relpath)] for files whose name is made of the prompt's own
    specific words (every stem word present), best first, FILES_CAP at most.
    `walk` given = pure (an iterable of relpaths, selftest)."""
    have = set(_specific(_ll.words(prompt)))
    if not have:
        return []
    hits = []
    if walk is None:
        walk = file_list(root)
    for rel in walk:
        if not rel.lower().endswith(FILE_EXT):
            continue
        sw = _stem_words(os.path.basename(rel))
        if sw and all(w in have for w in sw):
            hits.append((len(sw), rel))
    hits.sort(key=lambda t: (-t[0], t[1]))
    return hits[:FILES_CAP]


def toc_lines(text=None, rel="docs/index/MASTER_INDEX.md"):
    """The index door: the master index's `## ` headings, TOC_CAP at most."""
    if text is None:
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return []
    heads = [ln[3:].strip() for ln in text.splitlines() if ln.startswith("## ")]
    return heads[:TOC_CAP]


def effort_line(wf_hits, effort_now):
    """EFFORT: the matched entry's level against the level in use. Empty when
    no matched entry carries an EFFORT: line, or when they already agree."""
    asks = [(e["effort"], e["heading"]) for _, e in wf_hits if e.get("effort")]
    if not asks:
        return ""
    lvl, head = asks[0]
    if effort_now and effort_now.lower() == lvl:
        return ""
    if effort_now:
        return ("EFFORT: \"%s\" asks %s; this session runs %s - /effort %s for this arc "
                "(thinking is output at 5x; WIKI_METHOD \"effort matches the task\")"
                % (head, lvl, effort_now, lvl))
    return "EFFORT: \"%s\" asks %s (/effort %s for this arc)" % (head, lvl, lvl)


def _door_shown(session_id, now=None, state_path=ROUTE_STATE, mark=True):
    """True when the index door already went to this session. With mark, the
    first call records it. Never raises."""
    if not session_id:
        return False
    now = now or time.time()
    try:
        state = json.load(open(state_path, encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except Exception:
        state = {}
    shown = session_id in state
    if mark and not shown:
        state[session_id] = now
        if len(state) > KEEP_SESSIONS:
            for k in sorted(state, key=lambda k: state[k])[:-KEEP_SESSIONS]:
                state.pop(k, None)
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump(state, fh)
        except OSError:
            pass
    return shown


def route_block(prompt, session_id=None, effort_now=None, door=True):
    """THE LADDER (v1.57): -> (lines, counts). Lines empty on a short or
    hit-less prompt that already had its door. counts = {wf, tools, index,
    files, toc}. `door=False` = never touch the state (the --block CLI)."""
    counts = {"wf": 0, "tools": 0, "index": 0, "files": 0, "toc": 0}
    ws = _ll.words(prompt)
    # THE LADDER'S FLOOR: the classic matchers keep lesson_log's four content
    # words ("yes", "standup" never match); the index, file and door layers
    # run from LADDER_MIN_WORDS with at least one specific word, because the
    # CEO's own test prompt ("please add a gnome to my game") is three content
    # words after stopwords and one of them is the whole point.
    if len(ws) < LADDER_MIN_WORDS or not _specific(ws):
        return [], counts
    wf, tl = match(prompt)
    ih = index_hits(prompt)
    fh = file_hits(prompt)
    counts.update(wf=len(wf), tools=len(tl), index=len(ih), files=len(fh))
    out = []
    if wf or tl or ih or fh:
        out.append("ROUTE (the retrieval ladder): read what is named here in ONE batch before "
                   "the first write - the how, where the facts live, what already exists:")
        for _, e in wf:
            out.append("  WORKFLOWS.md line %d \"%s\"" % (e["line"], e["heading"]))
        for _, e in tl:
            out.append("  %s - %s" % (e["path"], "; ".join(e["keys"][:3])))
        for _, e in ih:
            out.append("  INDEX %s line %d: %s" % (e["path"], e["line"], e["heading"]))
        if fh:
            out.append("  FILES: " + "; ".join(rel for _, rel in fh))
        el = effort_line(wf, effort_now)
        if el:
            out.append("  " + el)
        return out, counts
    if len(ws) >= TOC_MIN_WORDS and door and not _door_shown(session_id):
        heads = toc_lines()
        if heads:
            counts["toc"] = 1
            out.append("ROUTE: no Keys line hits this prompt - THE INDEX DOOR (once per session): "
                       "pick the section whose heading fits and read it in the first batch, "
                       "with `Grep \"^## \" WORKFLOWS.md` and LESSONS.md, instead of guessing "
                       "synonyms one grep per turn. docs/index/MASTER_INDEX.md sections:")
            out.append("  " + " | ".join(heads))
            subs = subindex_names()
            if subs:
                out.append("  sub-indexes (docs/index/): " + ", ".join(subs))
    return out, counts


def subindex_names(root=ROOT):
    """The sub-index files beside the master index, by name (the door's
    second line): code, gotchas, laws, library ... as the project has them."""
    try:
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(root, "docs", "index"))
                       if f.endswith(".md") and f != "MASTER_INDEX.md")
    except OSError:
        return []
    return names[:12]


def route_record(mode_name, counts, prompt):
    """One ROUTE ledger line (both faces, so --route can compare them)."""
    try:
        _ll.record("ROUTE", "mode=%s | wf %d | tools %d | index %d | files %d | toc %d | %s"
                   % (mode_name, counts.get("wf", 0), counts.get("tools", 0),
                      counts.get("index", 0), counts.get("files", 0), counts.get("toc", 0),
                      re.sub(r"\s+", " ", prompt or "")[:70]))
    except Exception:  # noqa: BLE001 - a ledger failure never breaks the hook
        pass


# ----------------------------------------------------------------- selftest --
_INDEX = """# the master index
## Systems
- docs/systems/fauna.md - the creatures: gnomes, squirrels, the critter scheduler, hiding sinks
- docs/systems/plan.md - the roadmap in sections
## Laws
- docs/index/laws.md - the laws, one stub each
"""
_WF = """## Cut and wire new creature or plant art
WHEN: a new creature, critter or plant sheet lands in Assets.
EFFORT: medium
STEPS:
1. x
## Ship a batch
WHEN: a batch is done.
STEPS:
1. y
"""


def _selftest():
    fails = 0

    def check(label, ok):
        nonlocal fails
        print(("PASS  " if ok else "FAIL  ") + label)
        fails += not ok

    check("a ship prompt names a WORKFLOWS entry", any("WORKFLOWS.md line" in x for x in match_lines(
        "ship this docs-only batch: commit, export the changelog and push, no build")))
    check("a checkpoint prompt names the checkpoint tool by its Search keys",
          any("tools/checkpoint.py" in x for x in match_lines(
              "reset the checkpoint counter and read the context budget before we clear")))
    check("a short prompt gets no route line", match_lines("standup") == [])
    check("a game-art prompt gets no route line",
          match_lines("the pine tree looks too dark against the winter snow tiles") == [])
    check("the registry and the tools both index",
          len(workflow_entries()) >= 20 and len(tool_entries()) >= 20)
    # the ladder (v1.57), pure parts
    ents = workflow_entries(_WF)
    check("EFFORT: line parsed per entry", ents[0]["effort"] == "medium" and ents[1]["effort"] == "")
    ih = index_entries(_INDEX)
    check("index entries: bullets and headings, generic-only lines dropped",
          any("fauna" in e["heading"] for e in ih) and all(e["keys"] for e in ih))
    have = set(_specific(_ll.words("please add a gnome to my game")))
    fauna = [e for e in ih if "fauna" in e["heading"]][0]
    check("the gnome prompt's specific words hit the fauna index line",
          any(all(w in have for w in _specific(_ll.words(k))) for k in fauna["keys"]))
    fh = file_hits("please add a gnome to my game",
                   walk=["data/creatures/gnome.tscn", "data/creatures/squirrel.tscn", "docs/gnome.md",
                         "scripts/game_main.gd"])
    check("file layer: gnome.tscn hits, squirrel and game_main do not, .md ignored",
          [r for _, r in fh] == ["data/creatures/gnome.tscn"])
    check("effort line when the entry asks another level",
          "asks medium" in effort_line([(3, ents[0])], "high") and "/effort medium" in effort_line([(3, ents[0])], "high"))
    check("no effort line when levels agree or no entry asks",
          effort_line([(3, ents[0])], "medium") == "" and effort_line([(3, ents[1])], "high") == "")
    check("the door lists the index headings", toc_lines(_INDEX) == ["Systems", "Laws"])
    lines, counts = route_block("yes", door=False)
    check("a short prompt gets no block", lines == [] and counts["toc"] == 0)
    lines, counts = route_block(
        "ship this docs-only batch: commit, export the changelog and push, no build", door=False)
    check("a routed prompt gets the ladder block with the WORKFLOWS line",
          lines and lines[0].startswith("ROUTE (the retrieval ladder)") and counts["wf"] >= 1)
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(prefix="route_state_"), "route_state.json")
    check("the door is once per session",
          _door_shown("s1", state_path=tmp) is False and _door_shown("s1", state_path=tmp) is True
          and _door_shown("s2", state_path=tmp) is False)
    print("route_index selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(_selftest())
    if "--match" in argv:
        print("\n".join(match_lines(argv[argv.index("--match") + 1])) or "(no route line)")
        sys.exit(0)
    if "--block" in argv:
        lines, counts = route_block(argv[argv.index("--block") + 1], door=False)
        print("\n".join(lines) or "(no block; counts %s)" % counts)
        sys.exit(0)
    print(__doc__.split("\n\n")[1])

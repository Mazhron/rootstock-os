"""THE KNOWLEDGE SPLIT (NS-38 phase 2, the CEO 2026-10-13: "Lets work on
Phase 2" on the manager's assessment: "Kind times domain:
knowledge/<kind>/<domain>.md ... A manifest the front door reads ... The
first split is really core versus godot, and the lesson log script already
parses entries by tag, so a script can do the move. Under the preservation
law the old file stays as a pointer index.").

The kit's LESSONS.md used to be a whole copy of the origin's book. Now the
origin's LESSONS.md stays whole (the prompt hook, the lesson lint and the
retrieval evaluation all read it there) and THIS script derives the kit's
view from it on every kit refresh:

  knowledge/lessons/<domain>.md   one file per domain that has entries,
                                  each entry verbatim (heading, Tags, Keys,
                                  THE ONE RIGHT WAY, the TRIED bullets)
  knowledge/MANIFEST.md           one row per knowledge file: path, kind,
                                  domain, ~tokens, entries, one sentence;
                                  then the WANTED rows (a kind x domain with
                                  no file yet) - what STEP 0 reads
  LESSONS.md (kit copy)           the origin's preamble (the lesson law,
                                  the entry shape) plus a pointer index:
                                  every heading under the file that holds it

THE DOMAIN of an entry comes from its Tags line through DOMAIN_BY_TAG
(first match wins, in table order), then the per-heading OVERRIDES for the
entries whose tags say less than their text; everything else is `harness`
(Claude Code and process). A domain with no entries gets no file (the
caution: "Do not split finely before content exists. Many empty files are
noise to the pulling Claude and look abandoned to a contributor."); the
manifest's WANTED rows name the holes instead of stub files.

    python tools/split_knowledge.py            # regenerate what changed; one ledger line
    python tools/split_knowledge.py --dry-run  # say what would change
    python tools/split_knowledge.py --check    # STALE lines or "in step" (exit 0 either way; refresh_kit --check carries it)
    python tools/split_knowledge.py --selftest

tools/refresh_kit.py skips LESSONS.md in its pair copy (SPLIT) and calls
generate() after the copies, so `python tools/refresh_kit.py` is the one
command that keeps the split in step; the sync runs it first. Never
deletes: a knowledge file whose domain lost every entry is reported, not
removed (THE PRESERVATION LAW).

THE LEDGER: docs/history/knowledge_split_runs.txt, one line per run:
date time | ws | entries | per-domain counts | files | wanted | changed.
Through tools/_ledger.py, so an unchanged rerun does not grow it.

PURPOSE: Derive the kit's knowledge tree from the origin's LESSONS.md:
  split every entry by domain (Tags, then the override table, else
  harness) into knowledge/lessons/<domain>.md, write the manifest the
  front door reads (one row per knowledge file plus the wanted holes) and
  rewrite the kit's LESSONS.md as the lesson law plus a pointer index;
  report what changed and ledger one line. Never deletes.
INTENT: the CEO 2026-10-13 (NS-38 phase 2): a stranger's Claude should pull
  only the knowledge that matches the engine and language it answered at
  STEP 0, instead of reading a 1,700-line book that is mostly harness
  lessons; the manifest is the search key across files, the Tags and Keys
  lines stay the search keys inside one. The origin keeps one book because
  every hook reads it there; the split is a derived view, regenerated.
Search keys: knowledge split, kind x domain, manifest, knowledge/lessons,
  pointer index, LESSONS.md kit copy, domain by tag, wanted rows, phase 2,
  rootstock knowledge tree, STEP 0 pull.
See also: tools/refresh_kit.py (calls generate; SPLIT); tools/lesson_log.py
  (entries(), the parser this reuses); tools/sync_kit_repo.py (the push);
  docs/systems/rootstock-community.md "The roadmap (NS-38, three phases)";
  WORKFLOWS.md "Edit the future-project kit (Rootstock)"; the kit's
  knowledge/MANIFEST.md and 0 - READ ME FIRST.md STEP 0 item 4.
"""
import os
import re
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import lesson_log  # noqa: E402  (entries(), workstation())

KIT_DIR = os.path.join(ROOT, "Future Project MDs")
BOOK = os.path.join(ROOT, "LESSONS.md")
LEDGER = os.path.join(ROOT, "docs", "history", "knowledge_split_runs.txt")
TOOL = "tools/split_knowledge.py"

# ----------------------------------------------------------- CONFIG --
KINDS = ("lessons", "gotchas", "field notes", "design notes", "graphics")
DOMAINS = ("harness", "godot", "unity", "unreal", "cpp", "2d", "3d")
DOMAIN_WORDS = {
    "harness": "Claude Code and the process around it: hooks, ledgers, delegation, git, the kit",
    "godot": "the Godot engine: GDScript, scenes, resources, the editor, its tests",
    "unity": "the Unity engine", "unreal": "the Unreal engine", "cpp": "C++",
    "2d": "2D art and placement: sheets, slices, baselines, pixels",
    "3d": "3D art and scenes",
}
DEFAULT_DOMAIN = "harness"
# (tag -> domain), first match in table order wins; tags are compared lower-cased.
DOMAIN_BY_TAG = (
    ("art", "2d"), ("placement", "2d"), ("sprite", "2d"), ("pixel art", "2d"),
    ("godot", "godot"), ("gdscript", "godot"), ("ui", "godot"), ("creative mode", "godot"),
    ("unity", "unity"), ("unreal", "unreal"), ("cpp", "cpp"), ("c++", "cpp"), ("3d", "3d"),
)
# heading prefix -> domain, for entries whose Tags say less than their text
OVERRIDES = (
    ("Write an engine resource file (.tres, .tscn)", "godot"),
)
# The knowledge files that are not derived from the book: (kit path, kind, domain, sentence)
OTHER_FILES = (
    ("GODOT_FIELD_NOTES.md", "field notes", "godot",
     "Hard-won Godot 4.4 engine knowledge: rendering and performance costs, simulation "
     "architecture, GDScript and API gotchas, the measurement toolkit"),
    ("CLICKER_DESIGN_NOTES.md", "design notes", "any (the idle/clicker genre)",
     "Genre knowledge: cost curves, clicking and auto-click patterns, progression gating, "
     "the prestige economy, offline progress, feedback economics, balance telemetry"),
)
# (kind, domain, what would fill it) - the holes a contributor could fill; no stub files
WANTED = (
    ("field notes", "unity", "What Unity charged you for: a page in the shape of GODOT_FIELD_NOTES.md"),
    ("field notes", "unreal", "The same for Unreal"),
    ("gotchas", "cpp", "C++ gotchas met while building, each with THE ONE RIGHT WAY first"),
    ("graphics", "2d", "How 2D art is made and cut for an engine: sheets, slices, palettes, the tools"),
    ("lessons", "harness", "The nine silent-trial prompts in the origin's docs/history/retrieval_eval.txt: lessons nobody has written"),
)
# -----------------------------------------------------------------------


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def tokens(text):
    return int(len(text) / 4)


def entry_tags(entry):
    for raw in entry["body"]:
        m = re.match(r"Tags:\s*([^|]*)", raw)
        if m:
            return [t.strip().lower() for t in m.group(1).split(",") if t.strip()]
    return []


def domain_of(entry):
    """The domain an entry belongs to: overrides, then the tag table, else harness."""
    for prefix, dom in OVERRIDES:
        if entry["heading"].startswith(prefix):
            return dom
    tags = entry_tags(entry)
    for tag, dom in DOMAIN_BY_TAG:
        if tag in tags:
            return dom
    return DEFAULT_DOMAIN


def split(text):
    """-> (preamble, {domain: [entry, ...]}) in book order."""
    preamble = text.split("\n## ", 1)[0].rstrip("\n") + "\n"
    groups = {}
    for e in lesson_log.entries(text):
        groups.setdefault(domain_of(e), []).append(e)
    return preamble, groups


def entry_text(entry):
    body = "\n".join(entry["body"]).rstrip("\n")
    return "## %s\n%s\n" % (entry["heading"], body)


def domain_file(domain, ents, stamp):
    tags = sorted({t for e in ents for t in entry_tags(e) if t != "lessons"})
    named = ", ".join(tags[:4]) + (" and %d more" % (len(tags) - 4) if len(tags) > 4 else "")
    rel = "knowledge/lessons/%s.md" % domain
    head = [
        "# Lessons - %s (the one-right-way book, the %s slice)" % (domain, domain),
        "GENERATED by %s from the origin's LESSONS.md (%s) - edit the origin's entry, never this copy." % (TOOL, stamp),
        "",
        "PURPOSE: The %s slice of the one-right-way book, %d entr%s whose Tags" % (domain, len(ents), "y" if len(ents) == 1 else "ies"),
        "  name %s:" % (named or "no area"),
        "  each is THE ONE RIGHT WAY first, then TRIED / FAILED BECAUSE / DO",
        "  INSTEAD, verbatim from the origin, so a project in this domain reads",
        "  only what applies to it.",
        "INTENT: the CEO 2026-10-13 (NS-38 phase 2, the knowledge split): a",
        "  stranger's Claude pulls the domain it answered at STEP 0 and nothing",
        "  else; the manifest is the search key across files, the Tags and Keys",
        "  lines the search keys inside this one. This domain: %s." % DOMAIN_WORDS.get(domain, domain),
        "",
        "Search keys: lessons %s, %s, the one right way, knowledge split." % (domain, ", ".join(tags[:8]) or domain),
        "See also: knowledge/MANIFEST.md (every knowledge file, one row each);",
        "  LESSONS.md (the lesson law, the entry shape, the pointer index);",
        "  WORKFLOW_METHOD.md (the steps; a lesson is the judgment).",
        "",
    ]
    return rel, "\n".join(head) + "\n".join(entry_text(e) for e in ents)


def pointer_book(preamble, groups, stamp):
    total = sum(len(v) for v in groups.values())
    preamble = re.sub(
        r"^PURPOSE:.*?(?=^INTENT:)",
        "PURPOSE: The lesson law and the entry shape of the one-right-way book, plus\n"
        "  a pointer index: every one of the origin's %d entries under the\n"
        "  knowledge/lessons/<domain>.md file that holds it verbatim, so a project\n"
        "  seeds its own LESSONS.md from the slices the manifest matched.\n" % total,
        preamble, count=1, flags=re.S | re.M)
    lines = [
        "## Where the entries live (the knowledge split, NS-38 phase 2)",
        "Tags: lessons, kit, knowledge split | The %d entries of the origin's book, split by domain into knowledge/lessons/<domain>.md; this file keeps the law, the entry shape and this pointer index" % total,
        "Keys: where is the lesson, which knowledge file, knowledge split, manifest, domain file, pointer index, lessons by domain",
        "",
        "THE ONE RIGHT WAY: read knowledge/MANIFEST.md, pull the rows whose domain",
        "matches your engine and language (harness always applies), and grep",
        "`^## ` in those files the way the lesson law says. Every entry below is",
        "verbatim in the file named; nothing was dropped (THE PRESERVATION LAW).",
        "GENERATED by %s (%s) - a contributed lesson goes through community/inbox/," % (TOOL, stamp),
        "the origin's LESSONS.md is the source, this index follows on the next refresh.",
        "",
    ]
    for domain in sorted(groups, key=lambda d: (DOMAINS.index(d) if d in DOMAINS else 99, d)):
        ents = groups[domain]
        lines.append("knowledge/lessons/%s.md (%d):" % (domain, len(ents)))
        lines.extend("- %s" % e["heading"] for e in ents)
        lines.append("")
    lines.append("See also: knowledge/MANIFEST.md; knowledge/lessons/ (the files);")
    lines.append("  CONTRIBUTING.md \"The community path\" (how an entry arrives from outside).")
    return preamble + "\n" + "\n".join(lines) + "\n"


def manifest(groups, files, stamp):
    """files: {rel: text} of the generated domain files, for sizes."""
    rows = []
    for domain in sorted(groups, key=lambda d: (DOMAINS.index(d) if d in DOMAINS else 99, d)):
        rel = "knowledge/lessons/%s.md" % domain
        ents = groups[domain]
        rows.append((rel, "lessons", domain, tokens(files[rel]), str(len(ents)),
                     "THE ONE RIGHT WAY per task shape; %s" % DOMAIN_WORDS.get(domain, domain)))
    for rel, kind, domain, sentence in OTHER_FILES:
        p = os.path.join(KIT_DIR, rel)
        if os.path.isfile(p):
            txt = read(p)
            rows.append((rel, kind, domain, tokens(txt), str(len(re.findall(r"^## ", txt, re.M))), sentence))
    have = {(k, d) for _, k, d, _, _, _ in rows}
    lines = [
        "# The knowledge manifest (what to pull, by kind and domain)",
        "GENERATED by %s (%s) - edit the tables' sources, never this file." % (TOOL, stamp),
        "",
        "PURPOSE: One row per knowledge file in the kit (path, kind, domain, size",
        "  in tokens, entries, one sentence) and one row per wanted hole, so the",
        "  front door's STEP 0 pulls only the rows whose domain matches the CEO's",
        "  answers and a contributor sees where a page is missing.",
        "INTENT: the CEO 2026-10-13 (NS-38 phase 2) on the manager's assessment:",
        "  \"A manifest the front door reads. One line per file: kind, domain, size",
        "  in tokens, one sentence. STEP 0 pulls what matches the answers and",
        "  nothing else.\" And the caution: \"Do not split finely before content",
        "  exists ... Files appear when there is something to put in them.\"",
        "",
        "## The taxonomy",
        "Kinds: %s." % ", ".join(KINDS),
        "Domains: %s (harness is Claude Code and process; it applies to every" % ", ".join(DOMAINS),
        "project). A file exists only when it has content; a WANTED row names a",
        "hole a contribution could fill (community/inbox/, the stamp line carries",
        "the kind and the domain). Tokens are characters over four.",
        "",
        "## The files",
        "| File | Kind | Domain | ~Tokens | Entries | What it holds |",
        "|---|---|---|---|---|---|",
    ]
    for rel, kind, domain, tok, n, sentence in rows:
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (rel, kind, domain, "{:,}".format(tok), n, sentence))
    lines += ["", "## Wanted (no file yet)", "| Kind | Domain | What would fill it |", "|---|---|---|"]
    for kind, domain, what in WANTED:
        if (kind, domain) in have and kind != "lessons":
            continue
        lines.append("| %s | %s | %s |" % (kind, domain, what))
    lines += [
        "",
        "Search keys: manifest, knowledge files, which files apply, kind, domain,",
        "  wanted, STEP 0, pull only what matches, tokens per file.",
        "See also: 0 - READ ME FIRST.md STEP 0 item 4 (the question this answers);",
        "  LESSONS.md (the pointer index); CONTRIBUTING.md \"The community path\";",
        "  community/README.md in the public repo (how a wanted row gets filled).",
        "",
    ]
    return "\n".join(lines)


def build(book_text=None, stamp=None):
    """-> ({kit-relative path: text}, groups) for the whole derived view."""
    text = read(BOOK) if book_text is None else book_text
    stamp = stamp or datetime.datetime.now().strftime("%Y-%m-%d")
    preamble, groups = split(text)
    files = {}
    for domain, ents in groups.items():
        rel, body = domain_file(domain, ents, stamp)
        files[rel] = body
    files["knowledge/MANIFEST.md"] = manifest(groups, files, stamp)
    files["LESSONS.md"] = pointer_book(preamble, groups, stamp)
    return files, groups


def _same_but_stamp(a, b):
    """True when two texts differ only in the GENERATED line's stamp date."""
    strip = lambda s: re.sub(r"^(GENERATED by [^\n]*?)\(\d{4}-\d{2}-\d{2}\)", r"\1(date)", s, flags=re.M)  # noqa: E731
    return strip(a) == strip(b)


def stale(kit_dir=KIT_DIR, files=None):
    """[(rel, reason)] for every derived file the kit does not hold in this shape."""
    files = files if files is not None else build()[0]
    out = []
    for rel, want in sorted(files.items()):
        p = os.path.join(kit_dir, rel)
        if not os.path.isfile(p):
            out.append((rel, "not in the kit yet"))
        elif not _same_but_stamp(read(p), want):
            out.append((rel, "origin changed"))
    return out


def orphans(kit_dir=KIT_DIR, files=None):
    """Derived files the kit holds that this run did not produce (a domain that lost its entries). Reported, never removed."""
    files = files if files is not None else build()[0]
    d = os.path.join(kit_dir, "knowledge", "lessons")
    if not os.path.isdir(d):
        return []
    return sorted("knowledge/lessons/" + f for f in os.listdir(d)
                  if f.endswith(".md") and "knowledge/lessons/" + f not in files)


def generate(dry_run=False, kit_dir=KIT_DIR, book_text=None, ledger=True):
    """Write every derived file that changed; -> [kit-relative paths changed]."""
    files, groups = build(book_text)
    changed = [rel for rel, _ in stale(kit_dir, files)]
    for rel in changed:
        print(("would write " if dry_run else "wrote ") + rel)
        if not dry_run:
            write(os.path.join(kit_dir, rel), files[rel])
    for rel in orphans(kit_dir, files):
        print("ORPHAN (kept, never deleted; its domain has no entries now): " + rel)
    counts = ", ".join("%s %d" % (d, len(groups[d])) for d in sorted(groups, key=lambda d: -len(groups[d])))
    total = sum(len(v) for v in groups.values())
    wanted = len(re.findall(r"^\| [a-z0-9]", files["knowledge/MANIFEST.md"].split("## Wanted", 1)[1], re.M))
    print("knowledge split: %d entries -> %s | %d derived file(s) | %d wanted row(s) | %d changed%s"
          % (total, counts, len(files), wanted, len(changed), " (dry run)" if dry_run else ""))
    if ledger and not dry_run:
        _ledger_line("%d entries | %s | files %d | wanted %d | changed %d" % (total, counts, len(files), wanted, len(changed)))
    return changed


def check_line(kit_dir=KIT_DIR):
    """One clause for refresh_kit's KIT UNSYNCED line, or None when in step."""
    st = stale(kit_dir)
    if not st:
        return None
    return "knowledge split stale: %s" % ", ".join(r for r, _ in st[:4]) + (", ..." if len(st) > 4 else "")


def _ledger_line(payload):
    try:
        import _ledger
    except ImportError:
        return
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | %s" % (now, lesson_log.workstation(), payload)
    if not os.path.isfile(LEDGER):
        write(LEDGER, "# knowledge_split_runs - one line per split run (tools/split_knowledge.py)\n"
                      "# date time | ws | entries | per-domain counts | files | wanted | changed\n")
    _ledger.append_unless_identical(LEDGER, line, payload_from_col=2)


SAMPLE_BOOK = """# LESSONS - the one-right-way book

PURPOSE: a sample.
INTENT: a sample.

Search keys: sample.
See also: nothing.

## A harness thing
Tags: lessons, process | brief one
Keys: a, b

THE ONE RIGHT WAY: do a.
See also: x.

## A godot thing
Tags: lessons, testing, godot | brief two
Keys: c

THE ONE RIGHT WAY: do c.
See also: y.

## Write an engine resource file (.tres, .tscn) from a script
Tags: lessons, gotchas | brief three
Keys: d

THE ONE RIGHT WAY: do d.
See also: z.

## An art thing
Tags: lessons, art, placement | brief four
Keys: e

THE ONE RIGHT WAY: do e.
See also: w.
"""


def selftest():
    import tempfile
    fails = []

    ran = [0]

    def check(name, cond):
        ran[0] += 1
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    files, groups = build(SAMPLE_BOOK, stamp="2026-10-13")
    check("harness is the default domain", [e["heading"] for e in groups.get("harness", [])] == ["A harness thing"])
    check("a godot tag lands in godot", any(e["heading"] == "A godot thing" for e in groups.get("godot", [])))
    check("the .tres override lands in godot", any(e["heading"].startswith("Write an engine resource") for e in groups.get("godot", [])))
    check("art tags land in 2d", [e["heading"] for e in groups.get("2d", [])] == ["An art thing"])
    check("no file for a domain without entries", "knowledge/lessons/unity.md" not in files)
    check("three domain files + manifest + pointer", len(files) == 5)
    check("every entry is verbatim in its file",
          all(entry_text(e) in files["knowledge/lessons/%s.md" % d] for d, es in groups.items() for e in es))
    check("the pointer index names every heading",
          all(("- " + e["heading"]) in files["LESSONS.md"] for es in groups.values() for e in es))
    check("the pointer keeps the preamble", files["LESSONS.md"].startswith("# LESSONS - the one-right-way book"))
    check("the pointer entry has the required shape",
          all(k in files["LESSONS.md"] for k in lesson_log.REQUIRED))
    man = files["knowledge/MANIFEST.md"]
    check("the manifest lists each derived file", all(("| `knowledge/lessons/%s.md` |" % d) in man for d in groups))
    check("the manifest carries wanted rows", "| field notes | unity |" in man)
    check("every derived file carries the format header",
          all(all(k in t for k in ("PURPOSE:", "INTENT:", "Search keys:", "See also:")) for t in files.values()))
    tmp = tempfile.mkdtemp(prefix="split_knowledge_")
    first = generate(dry_run=False, kit_dir=tmp, book_text=SAMPLE_BOOK, ledger=False)
    check("first generate writes every file", len(first) == 5)
    second = generate(dry_run=False, kit_dir=tmp, book_text=SAMPLE_BOOK, ledger=False)
    check("second generate at the same book changes nothing", second == [])
    check("check_line is None when in step", stale(tmp, build(SAMPLE_BOOK)[0]) == [])
    moved = SAMPLE_BOOK.replace("Tags: lessons, art, placement", "Tags: lessons, godot")
    third = generate(dry_run=True, kit_dir=tmp, book_text=moved, ledger=False)
    check("a moved entry stales its new file, the manifest and the pointer (the old file is an orphan)", len(third) == 3)
    check("the file it left is an orphan, reported, still there",
          orphans(tmp, build(moved)[0]) == ["knowledge/lessons/2d.md"] and os.path.isfile(os.path.join(tmp, "knowledge", "lessons", "2d.md")))
    print("SELFTEST %s (%d check(s), %d fail(s))" % ("PASS" if not fails else "FAIL", ran[0], len(fails)))
    return 0 if not fails else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--check" in argv:
        st = stale()
        for rel, why in st:
            print("STALE %s (%s)" % (rel, why))
        for rel in orphans():
            print("ORPHAN (kept): %s" % rel)
        print("knowledge split: " + ("%d stale - `python tools/refresh_kit.py`" % len(st) if st
                                     else "in step with the origin's LESSONS.md"))
        return 0
    generate(dry_run="--dry-run" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

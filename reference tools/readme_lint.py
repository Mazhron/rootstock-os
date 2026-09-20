"""THE README PARITY LINT (the CEO 2026-09-13: "What can we do to prevent
the Readme from falling behind so far and missing information like that
in the future?" - "Lets build it.")

    python tools/readme_lint.py            # check, ledger a line, exit 1 on FAIL
    python tools/readme_lint.py --quiet    # one summary line only
    python tools/readme_lint.py --selftest # prove the checks bite

The public README (rootstock-os/README.md) lives only in the kit repo and
no script used to read its CLAIMS - only its version line. The 09-13
audit found three slips a version check cannot see: a law count in prose
("six" after the seventh law joined), a wrong destination for
settings.json, and a mechanic described slightly wrong. This lint derives
every countable fact from its SOURCE OF TRUTH in the kit folder and
compares it with what the README says:

  laws          numbered items under SUBAGENT_METHOD.md's laws heading
                (and the heading's own number word must agree)
  skills        the dirs in kit skills/ - count word + every /name named
  hooks         the *.py in kit hooks/ (minus the shared lib) - count word
  reference     the files in "reference tools/" - count word
  the box       every top-level kit entry has a box-table row and every
                row names a real entry (a renamed or retired file shows)
  version       README "Kit version: vX.Y" == UPGRADES.md CURRENT KIT VERSION
  graft README  the newest UPGRADES.md entry carries a README: line naming
                the README section it touched (or "none, wording only")
  number words  ANY "<number word> laws|skills|hooks|hook scripts|rituals|
                working scripts" claim in the README must equal the truth
  claims table  small grep-able facts (CLAIMS below): a regex that must
                match and one that must not - extend it when an audit
                finds a prose slip a count cannot express

tools/sync_kit_repo.py runs this and REFUSES to push on any FAIL; run_all's
check group runs it; each run appends to docs/history/readme_lint_runs.txt.
A machine without the kit clone prints SKIP and exits 0 (a ledger line
says so) - the lint is a publish gate, not a workstation requirement.

PURPOSE: Derives every countable README fact (laws, skills, hooks, reference
  tools, the box table, version, the graft README line, number word claims,
  prose claims) from the kit folder itself and compares it with what the
  public README says, ledgering PASS, FAIL or SKIP each run.
INTENT: the CEO 2026-09-13: 'What can we do to prevent the Readme from
  falling behind so far and missing information like that in the future?'
  'Lets build it.'

Search keys: readme lint, readme parity, readme drift, kit readme, public
readme, box table, count check, rootstock readme.
See also: tools/sync_kit_repo.py (the refusal); tools/readme_audit.py (the
cadence for the unwritten-answer class); tools/ledger_trends.py (proposes
an audit); WORKFLOWS.md "Edit the future-project kit (Rootstock)";
docs/systems/tooling.md "The README parity lint and audit cadence".
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ledger

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ----------------------------------------------------------- CONFIG --
KIT_DIR = os.path.join(ROOT, "Future Project MDs")
KIT_REPO = os.path.normpath(os.path.join(ROOT, "..", "..", "..", "rootstock-os"))
README = os.path.join(KIT_REPO, "README.md")
UPGRADES = os.path.join(KIT_DIR, "UPGRADES.md")
LAWS_FILE = os.path.join(KIT_DIR, "SUBAGENT_METHOD.md")
LAWS_HEADING = re.compile(r"^## The (\w+) laws\s*$", re.M)
SKILLS_DIR = os.path.join(KIT_DIR, "skills")
HOOKS_DIR = os.path.join(KIT_DIR, "hooks")
HOOK_LIB = {"_hooklib.py"}
REF_DIR = os.path.join(KIT_DIR, "reference tools")
BOX_HEADING = "## What is in the box"
BOX_SKIP = {"__pycache__"}
LEDGER = os.path.join(ROOT, "docs", "history", "readme_lint_runs.txt")
# Grep-able prose facts. (label, must_match, must_not_match) - regexes on
# the README text, case-insensitive. Add a row whenever an audit finds a
# prose slip that no count expresses; never remove one (a slip that
# happened once can happen again).
CLAIMS = [
    ("settings.json merges into .claude/settings.json (not tools/hooks)",
     r"merge into `\.claude/settings\.json`",
     r"settings template.*into `tools/hooks/`"),
    ("the checkpoint counter ticks when work happened (not after every task)",
     r"ticks the checkpoint counter when\s+work actually happened",
     r"ticks (the counter )?after every task"),
    ("the delegation company is described with the current law count",
     None,
     r"\bsix laws\b"),
    # 2026-09-20 audit (T-0920-RA-1..4): the prose slips the count check cannot see
    ("the diet guard refuses the first whole read, it is not warn-only",
     None, r"warn-only hook"),
    ("the preserve guard reads every executed script, tracked or not",
     r"every script a command executes", r"every untracked script"),
    ("intent sources are stated, correction or inferred",
     None, r"self-judged"),
    ("the capture rule binds whoever performs, the manager files the gap",
     r"whoever performs such a task checks", r"a gap the performer writes up"),
    ("/preserve is the preservation law's front, not /flag",
     r"`/preserve` is the preservation law's\s+front", r"`/flag`\s*\(the preservation"),
    ("the script rule lists builds, not fixes",
     r"Tests, builds, imports", r"Tests, fixes, imports"),
    ("the graft log's README field dates from v1.17",
     r"from v1\.17 on", None),
    ("the box names _hooklib.py and hooks/README.txt",
     r"`_hooklib\.py`.*`README\.txt` with the per-hook", None),
    ("the first systems audit is dated by its ledger (2026-09-14)",
     None, r"systems audit ran on 2026-09-13"),
]
NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
                "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
# ------------------------------------------------------------------------


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def word(n):
    return NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else str(n)


def to_num(tok):
    tok = tok.lower()
    if tok.isdigit():
        return int(tok)
    return NUMBER_WORDS.index(tok) if tok in NUMBER_WORDS else None


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def truths():
    """Derive every countable fact from the kit folder."""
    t = {}
    laws_txt = read(LAWS_FILE)
    m = LAWS_HEADING.search(laws_txt)
    body = laws_txt[m.end():] if m else ""
    body = body.split("\n## ", 1)[0]
    t["laws"] = len(re.findall(r"^\d+\. ", body, re.M))
    t["laws_heading_word"] = m.group(1).lower() if m else None
    t["skills"] = sorted(d for d in os.listdir(SKILLS_DIR)
                         if os.path.isdir(os.path.join(SKILLS_DIR, d)) and d not in BOX_SKIP)
    t["hooks"] = sorted(f for f in os.listdir(HOOKS_DIR)
                        if f.endswith(".py") and f not in HOOK_LIB)
    t["reference"] = sorted(f for f in os.listdir(REF_DIR)
                            if f not in BOX_SKIP and not f.endswith(".pyc"))
    t["box"] = sorted(n for n in os.listdir(KIT_DIR) if n not in BOX_SKIP)
    up = read(UPGRADES)
    m = re.search(r"CURRENT KIT VERSION:\s*\**v(\d+\.\d+)", up)
    t["version"] = m.group(1) if m else None
    entries = re.split(r"^### v", up, flags=re.M)
    newest = entries[-1] if len(entries) > 1 else ""
    t["newest_entry"] = newest.split("\n", 1)[0].strip()
    t["newest_has_readme_line"] = bool(re.search(r"^README:", newest, re.M))
    return t


def checks(readme, t):
    """Return a list of (ok, label, detail)."""
    out = []
    low = readme.lower()

    def add(ok, label, detail=""):
        out.append((bool(ok), label, detail))

    # 1. laws: the method's own heading + the README's claims
    add(t["laws_heading_word"] == word(t["laws"]),
        "SUBAGENT_METHOD.md heading counts its laws",
        "heading says %r, %d numbered laws" % (t["laws_heading_word"], t["laws"]))
    # 2-4. counts as number words anywhere in the README
    nouns = {
        "laws": t["laws"], "skills": len(t["skills"]),
        "rituals ship": len(t["skills"]), "ritual-skills": len(t["skills"]),
        "hooks": len(t["hooks"]), "hook scripts": len(t["hooks"]),
        "kit hooks": len(t["hooks"]), "ship in `hooks/`": len(t["hooks"]),
        "working scripts": len(t["reference"]),
    }
    pat = re.compile(r"\b(%s|\d+)\s+(%s)" % ("|".join(NUMBER_WORDS),
                                            "|".join(re.escape(k) for k in nouns)), re.I)
    seen = {}
    for m in pat.finditer(readme):
        n, noun = to_num(m.group(1)), m.group(2).lower()
        seen.setdefault(noun, []).append(n)
        add(n == nouns[noun], "README count: %s" % m.group(0).strip(),
            "truth is %d" % nouns[noun])
    families = {"laws": ("laws",), "skills": ("skills", "rituals ship", "ritual-skills"),
                "hooks": ("hooks", "hook scripts", "kit hooks", "ship in `hooks/`"),
                "reference tools": ("working scripts",)}
    for fam, keys in families.items():
        add(any(k in seen for k in keys), "README states the %s count somewhere" % fam,
            "" if any(k in seen for k in keys) else "no '<number> %s' claim found" % fam)
    # 5. every skill named as a slash command
    for s in t["skills"]:
        add(("/" + s) in readme, "README names skill /%s" % s)
    # 6. the box table
    box = readme.split(BOX_HEADING, 1)[1].split("\n## ", 1)[0] if BOX_HEADING in readme else ""
    rows = re.findall(r"^\| `([^`]+)` \|", box, re.M)
    names = {r.rstrip("/") for r in rows}
    for n in t["box"]:
        add(n in names, "box table lists %s" % n)
    for r in names:
        add(r in t["box"], "box table row %r exists in the kit" % r)
    # 7. version
    m = re.search(r"Kit version:\s*\**v(\d+\.\d+)", readme)
    rv = m.group(1) if m else None
    add(rv == t["version"], "README kit version matches UPGRADES.md",
        "README v%s, graft log v%s" % (rv, t["version"]))
    # 8. the graft README line
    add(t["newest_has_readme_line"], "newest graft entry (%s) carries a README: line"
        % t["newest_entry"], "add 'README: <section touched>' or 'README: none, wording only'")
    # 9. prose claims
    for label, must, must_not in CLAIMS:
        ok = True
        detail = ""
        if must and not re.search(must, readme, re.I | re.S):
            ok, detail = False, "expected text not found: /%s/" % must
        if must_not and re.search(must_not, readme, re.I | re.S):
            ok, detail = False, "forbidden text present: /%s/" % must_not
        add(ok, "claim: " + label, detail)
    return out


def ledger(status, t, fails, nchecks):
    new = not os.path.isfile(LEDGER)
    if new:
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write("# README PARITY LINT (append-only; one line per run). Read the TAIL.\n"
                     "# date time | ws | kit version | checks | fails | PASS/FAIL/SKIP | detail\n")
    line = "%s | %s | v%s | %d | %d | %s | %s\n" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), workstation(),
        t.get("version") if t else "?", nchecks, len(fails), status,
        "; ".join(f[1] for f in fails)[:300] or "clean")
    _ledger.append_unless_identical(LEDGER, line)


def main(argv):
    quiet = "--quiet" in argv
    if "--selftest" in argv:
        return selftest()
    if not os.path.isfile(README):
        print("README LINT: SKIP - no kit clone at %s (a publish gate, not a "
              "workstation requirement)" % KIT_REPO)
        ledger("SKIP", None, [], 0)
        return 0
    t = truths()
    res = checks(read(README), t)
    fails = [r for r in res if not r[0]]
    status = "FAIL" if fails else "PASS"
    if not quiet:
        for ok, label, detail in res:
            if not ok or "--verbose" in argv:
                print("  %s  %s%s" % ("ok  " if ok else "FAIL", label,
                                      (" - " + detail) if detail else ""))
    print("README LINT: %s - %d checks, %d fail (kit v%s, %d laws, %d skills, %d hooks, "
          "%d reference tools, %d box entries)"
          % (status, len(res), len(fails), t["version"], t["laws"], len(t["skills"]),
             len(t["hooks"]), len(t["reference"]), len(t["box"])))
    ledger(status, t, fails, len(res))
    return 1 if fails else 0


def selftest():
    """Prove the checks bite: a README with the 09-13 slips must FAIL them."""
    t = truths()
    good = read(README) if os.path.isfile(README) else None
    if good is None:
        print("SELFTEST: SKIP (no README at %s)" % README)
        return 0
    base = checks(good, t)
    n = 0
    fail = 0

    def expect(cond, label):
        nonlocal n, fail
        n += 1
        if not cond:
            fail += 1
        print("  %s  %s" % ("ok  " if cond else "FAIL", label))

    expect(all(r[0] for r in base), "the live README passes (%d checks)" % len(base))
    bad = good.replace("seven laws", "six laws")
    expect(any(not r[0] and "six laws" in r[1] for r in checks(bad, t)),
           "a 'six laws' claim is caught")
    bad = re.sub(r"merge into `\.claude/settings\.json`",
                 "drop into `tools/hooks/`", good)
    expect(any(not r[0] and "settings.json" in r[1] for r in checks(bad, t)),
           "the settings.json destination slip is caught")
    bad = re.sub(r"(Kit version:\s*\**v)(\d+\.\d+)", r"\g<1>0.1", good)
    expect(any(not r[0] and "kit version" in r[1] for r in checks(bad, t)),
           "a lagging version line is caught")
    bad = good.replace("| `skills/` |", "| `skulls/` |")
    expect(any(not r[0] and r[1] == "box table lists skills" for r in checks(bad, t)),
           "a missing box-table row is caught")
    expect(any(not r[0] and "skulls" in r[1] for r in checks(bad, t)),
           "a box-table row naming a non-existent entry is caught")
    bad = good.replace("/preserve", "/keep")
    expect(any(not r[0] and "/preserve" in r[1] for r in checks(bad, t)),
           "an unnamed skill is caught")
    t2 = dict(t, newest_has_readme_line=False)
    expect(any(not r[0] and "README: line" in r[1] for r in checks(good, t2)),
           "a graft entry without a README: line is caught")
    print("SELFTEST: %s - %d checks, %d fail" % ("FAIL" if fail else "PASS", n, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

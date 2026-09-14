"""THE PURPOSE AUDIT (the CEO's ruling 2026-09-13, INTENT.md "The purpose
audit: read-only, flag green / yellow / red, explain, file for review").

PURPOSE: keep the kit's flag ledger (FLAGS.md in the kit folder): every
  kit thing's latest flag (GREEN / YELLOW / RED), who gave it and when,
  whether the thing changed since (STALE), the ones nobody has audited
  yet (UNFLAGGED), and the tally - regenerated in place from the entries;
  `--flag` appends one entry (SAYS = the thing's own PURPOSE line, DOES =
  what the reviewer found it actually does, FLAG = why the color).
INTENT: the CEO 2026-09-13: "Claude MUST compare the purpose and intent of
  the thing vs what the thing actually reads whether it's a script, hook,
  code or injectable prompt. If there is reason to flag it, Claude should
  flag them green, yellow or red. Claude should always read-only -> Flag
  -> Explain. There should be a file that directly references anything
  that is green, yellow or red flags, tally them and put them in the git
  for review. Any Claude can review and put their findings there for
  future review."

    python tools/purpose_audit.py                     # status: every item, its flag, STALE/UNFLAGGED; tally; ledger line
    python tools/purpose_audit.py --pending           # only the items that need an audit (unflagged or stale)
    python tools/purpose_audit.py --flag "hooks/preserve_guard.py" --color green --by fable \\
        --does "<what it actually does>" --note "<why this color; what to fix if not green>"
    python tools/purpose_audit.py --selftest

THE COLORS (also in the kit's CONTRIBUTING.md):
  GREEN   the thing does what its PURPOSE says and nothing more.
  YELLOW  matches in substance, but something is off: a side effect the
          purpose does not mention, a gap, a vague or unfilled purpose
          line, a stale copy. Fix in a later batch; it may ship.
  RED     does something its purpose does not say, or crosses a law
          (deletes, disables a guard, unbounded spend, routes around a
          refusal). Bring it to the owner before it merges or ships.
THE RITUAL: read-only -> flag -> explain. The auditor never edits the
thing in the audit turn; the entry carries the explanation; the fix is
its own batch after the owner has read the flag. A rewrite of a MISSING
header goes through tools/format_lint.py --rewrite, never by hand.

Items are keyed by their kit-relative path (what the public repo shows)
and hashed from the kit copy, so a contributor's flag and ours name the
same thing. The runs ledger (docs/history/purpose_audit_runs.txt) carries
one tally line per status run for standup and the trends. The tally's
"Updated" stamp means LAST CHANGED, not last run: a status run whose rows
and counts match the file leaves FLAGS.md byte-identical, so the loop's
audit never makes the mirror check cry KIT UNSYNCED over nothing (Q0003,
the CEO 2026-09-14: option 2, fix the cause).

Search keys: purpose audit, flags, green yellow red, flag ledger, FLAGS.md,
read-only audit, stale flag, unflagged, contributor review, says does.
See also: tools/format_lint.py (the header the SAYS line comes from);
"Future Project MDs/FLAGS.md" (the ledger itself); "Future Project
MDs/CONTRIBUTING.md" (the law for contributors); .claude/skills/flag (the
ritual); tools/sync_kit_repo.py (warns on RED / unflagged at publish);
WORKFLOWS.md "Audit a kit thing's purpose (flag it)"; INTENT.md.
"""
import contextlib
import datetime
import hashlib
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ledger

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ----------------------------------------------------------- CONFIG --
KIT_DIR = os.path.join(ROOT, "Future Project MDs")
FLAGS = os.path.join(KIT_DIR, "FLAGS.md")
LEDGER = os.path.join(ROOT, "docs", "history", "purpose_audit_runs.txt")
LOCK = os.path.join(ROOT, ".claude", "flags.lock")   # gitignored; held only while appending
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_NAMES = {"FLAGS.md", "LICENSE", ".gitignore"}
COLORS = ("GREEN", "YELLOW", "RED")
TALLY_START = "<!-- tally:start -->"
TALLY_END = "<!-- tally:end -->"
FLAGS_HEADING = "## The flags (append-only, newest last)"
# -----------------------------------------------------------------------
NL = chr(10)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def items(kit=None):
    """Kit-relative paths of every auditable thing, sorted."""
    kit = kit or KIT_DIR
    out = []
    for base, dirs, files in os.walk(kit):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_NAMES:
                continue
            out.append(os.path.relpath(os.path.join(base, f), kit).replace("\\", "/"))
    return sorted(out)


def digest(path):
    try:
        return hashlib.sha1(read(path).encode("utf-8")).hexdigest()[:8]
    except OSError:
        return "missing"


def purpose_line(path):
    try:
        m = re.search(r"^\s*(?:\"\"\"|''')?\s*PURPOSE:\s*(.*(?:\n  \S.*)*)", read(path), re.M)
    except OSError:
        return None
    if not m:
        return None
    return " ".join(l.strip() for l in m.group(1).split("\n")).strip()


# ---------------------------------------------------------- FLAGS.md --
HEAD = re.compile(r"^### (\S+ \S+) \| (.+?) \| (GREEN|YELLOW|RED) \| (.+?) \| (\S+) \| ([0-9a-f]{8}|missing)\s*$")


def parse(text):
    """-> [entry dicts] in file order."""
    entries = []
    cur = None
    for line in text.split("\n"):
        m = HEAD.match(line)
        if m:
            cur = {"when": m.group(1), "item": m.group(2), "color": m.group(3), "by": m.group(4),
                   "ws": m.group(5), "hash": m.group(6), "says": "", "does": "", "flag": ""}
            entries.append(cur)
            continue
        if cur is None:
            continue
        for k in ("SAYS", "DOES", "FLAG"):
            if line.startswith(k + ":"):
                cur[k.lower()] = line[len(k) + 1:].strip()
    return entries


def latest(entries):
    out = {}
    for e in entries:
        out[e["item"]] = e
    return out


def status(kit=None, text=None):
    """-> (rows, tally). rows: [(item, state, color, by, when)]."""
    kit = kit or KIT_DIR
    text = text if text is not None else (read(FLAGS) if os.path.isfile(FLAGS) else "")
    last = latest(parse(text))
    rows = []
    tally = {"items": 0, "green": 0, "yellow": 0, "red": 0, "unflagged": 0, "stale": 0}
    for it in items(kit):
        tally["items"] += 1
        e = last.get(it)
        if not e:
            rows.append((it, "UNFLAGGED", "", "", ""))
            tally["unflagged"] += 1
            continue
        h = digest(os.path.join(kit, it))
        state = "STALE" if h != e["hash"] else "ok"
        if state == "STALE":
            tally["stale"] += 1
        tally[e["color"].lower()] += 1
        rows.append((it, state, e["color"], e["by"], e["when"]))
    for it, e in last.items():
        if it not in {r[0] for r in rows}:
            rows.append((it, "GONE", e["color"], e["by"], e["when"]))
    return rows, tally


def tally_block(rows, tally, now=None):
    now = now or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [TALLY_START,
             "Updated %s | items %d | GREEN %d | YELLOW %d | RED %d | unflagged %d | stale %d"
             % (now, tally["items"], tally["green"], tally["yellow"], tally["red"],
                tally["unflagged"], tally["stale"]),
             "", "| item | flag | state | by | when |", "|---|---|---|---|---|"]
    for it, state, color, by, when in rows:
        lines.append("| %s | %s | %s | %s | %s |" % (it, color or "-", state, by or "-", when or "-"))
    lines.append(TALLY_END)
    return "\n".join(lines)


def skeleton():
    return """# FLAGS.md - the purpose audit ledger (green / yellow / red, for review)

PURPOSE: the one file that references every kit thing's flag - what its
  PURPOSE line says, what a read-only audit found it actually does, the
  color, the explanation - tallied at the top and committed so anyone
  can review it and any Claude can add findings.
INTENT: the CEO 2026-09-13: "Claude should always read-only -> Flag ->
  Explain. There should be a file that directly references anything that
  is green, yellow or red flags, tally them and put them in the git for
  review. Any Claude can review and put their findings there for future
  review."

HOW TO USE THIS FILE: the tally block is GENERATED by reference
tools/purpose_audit.py (never hand-edit it); the entries below the flags
heading are APPEND-ONLY, one per audit of one thing, newest last -
`python tools/purpose_audit.py --flag "<kit path>" --color green|yellow|red
--by <who> --does "..." --note "..."` writes one. GREEN: does what its
PURPOSE says and nothing more. YELLOW: matches in substance, something is
off (a side effect, a gap, a vague purpose); fix later, may ship. RED:
does what its purpose does not say or crosses a law (deletes, disables a
guard, unbounded spend); the owner sees it before it merges. STALE: the
thing changed since its last flag - audit it again. A contributor files
the same way, by pull request; the entry's hash names the exact version
reviewed.

Search keys: flags, purpose audit, green yellow red, review ledger,
contributor review, stale, unflagged.
See also: CONTRIBUTING.md (the format law + the audit ritual); reference
tools/purpose_audit.py (the tally + the --flag writer); reference
tools/format_lint.py (the header the SAYS line comes from); skills/flag
(the ritual as a slash command); UPGRADES.md (the graft log).

## The tally (generated - never hand-edit this block)

%s
%s

%s
""" % (TALLY_START, TALLY_END, FLAGS_HEADING)


def regenerate(rows, tally, path=None):
    path = path or FLAGS
    text = read(path) if os.path.isfile(path) else skeleton()
    if TALLY_START not in text or TALLY_END not in text:
        raise SystemExit("FLAGS.md has no tally markers (%s / %s) - restore them by hand" % (TALLY_START, TALLY_END))
    a = text.index(TALLY_START)
    b = text.index(TALLY_END) + len(TALLY_END)
    fresh = tally_block(rows, tally)
    if _same_but_stamp(text[a:b], fresh):
        return False  # Q0003 (the CEO 2026-09-14, option 2): nothing changed, leave the file alone
    write(path, text[:a] + fresh + text[b:])
    return True


def _same_but_stamp(old_block, new_block):
    """True when two tally blocks differ only in the Updated timestamp, so a
    no-change run leaves FLAGS.md byte-identical (the mirror check stays
    quiet; the run itself is still in purpose_audit_runs.txt)."""
    strip = lambda t: re.sub(r"^Updated \S+ \S+", "Updated", t, count=1, flags=re.M)
    return strip(old_block) == strip(new_block)


@contextlib.contextmanager
def locked(lock=None):
    """Serialize concurrent --flag writers (several employees on one audit).
    Byte-range lock on a persistent lock file; nothing is ever deleted."""
    lock = lock or LOCK
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    fh = open(lock, "a+b")
    try:
        deadline = time.time() + 30
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() > deadline:
                    raise SystemExit("FLAGS.md is locked by another writer for 30 s - retry")
                time.sleep(0.2)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()


def add_flag(item, color, by, does, note, path=None, kit=None, now=None):
    with locked(None if path is None else path + ".lock"):
        return _add_flag(item, color, by, does, note, path, kit, now)


def _add_flag(item, color, by, does, note, path=None, kit=None, now=None):
    path = path or FLAGS
    kit = kit or KIT_DIR
    color = color.upper()
    if color not in COLORS:
        raise SystemExit("color must be one of green / yellow / red")
    item = item.replace("\\", "/").strip("/")
    full = os.path.join(kit, item)
    if not os.path.isfile(full):
        raise SystemExit("no such kit thing: %s (paths are kit-relative, e.g. hooks/preserve_guard.py)" % item)
    says = purpose_line(full)
    if says is None and color == "GREEN" and not item.endswith(".json"):
        raise SystemExit("%s has no PURPOSE line - a thing without a stated purpose cannot be GREEN; "
                         "flag it yellow (or red) and rewrite the header with format_lint.py --rewrite "
                         "in a later batch" % item)
    if not does or not note:
        raise SystemExit("--does and --note are both required: the audit is read-only -> flag -> EXPLAIN")
    if re.search("[—–]", does + note):
        raise SystemExit("no em or en dashes in a flag entry (the text doctrine) - use a hyphen, colon or comma")
    now = now or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = "\n### %s | %s | %s | %s | %s | %s\nSAYS: %s\nDOES: %s\nFLAG: %s\n" % (
        now, item, color, by, workstation(), digest(full),
        says if says is not None else "(no PURPOSE line)", does.strip(), note.strip())
    text = read(path) if os.path.isfile(path) else skeleton()
    if FLAGS_HEADING not in text:
        text = text.rstrip("\n") + "\n\n" + FLAGS_HEADING + "\n"
    text = text.rstrip("\n") + "\n" + entry
    write(path, text)
    rows, tally = status(kit, text)
    regenerate(rows, tally, path)
    return entry.strip()


def ledger(tally):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | %d | %d | %d | %d | %d | %d\n" % (
        now, workstation(), tally["items"], tally["green"], tally["yellow"], tally["red"],
        tally["unflagged"], tally["stale"])
    if not os.path.isfile(LEDGER):
        with open(LEDGER, "w", encoding="utf-8") as f:
            f.write("# purpose audit runs: date | ws | items | green | yellow | red | unflagged | stale\n")
    _ledger.append_unless_identical(LEDGER, line)
    return line.strip()


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--flag" in argv:
        def opt(flag, default=None):
            return argv[argv.index(flag) + 1] if flag in argv else default
        entry = add_flag(opt("--flag"), opt("--color", ""), opt("--by", "unknown"),
                         opt("--does", ""), opt("--note", ""))
        print(entry)
        return 0
    rows, tally = status()
    pending = "--pending" in argv
    for it, state, color, by, when in rows:
        if pending and state not in ("UNFLAGGED", "STALE"):
            continue
        print("%-9s %-7s %s%s" % (state, color or "-", it, ("  (%s, %s)" % (by, when)) if by else ""))
    regenerate(rows, tally)
    line = ledger(tally)
    print("PURPOSE AUDIT: items %d | GREEN %d | YELLOW %d | RED %d | unflagged %d | stale %d%s"
          % (tally["items"], tally["green"], tally["yellow"], tally["red"], tally["unflagged"],
             tally["stale"], "  <- RED flags await the owner" if tally["red"] else ""))
    print("ledger: " + line)
    return 0


def selftest():
    import tempfile
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        kit = os.path.join(td, "kit")
        os.makedirs(os.path.join(kit, "hooks"))
        write(os.path.join(kit, "hooks", "a.py"), '"""PURPOSE: guards the thing well enough.\nINTENT: owner.\n"""\n')
        write(os.path.join(kit, "b.md"), "# B\n\nno purpose here\n")
        write(os.path.join(kit, "FLAGS.md"), "x")  # skipped by name
        fpath = os.path.join(td, "F.md")
        check("items skip FLAGS.md and list kit-relative paths", items(kit) == ["b.md", "hooks/a.py"])
        rows, t = status(kit, "")
        check("no ledger -> all unflagged", t["unflagged"] == 2 and all(r[1] == "UNFLAGGED" for r in rows))
        e = add_flag("hooks/a.py", "green", "tester", "guards it", "matches", path=fpath, kit=kit, now="2026-09-13 12:00")
        check("flag entry carries SAYS from the PURPOSE line", "SAYS: guards the thing well enough." in e)
        txt = read(fpath)
        check("FLAGS.md was created from the skeleton with a tally", TALLY_START in txt and "GREEN 1" in txt)
        try:
            add_flag("b.md", "green", "tester", "x", "y", path=fpath, kit=kit)
            check("green without a PURPOSE line is refused", False)
        except SystemExit as ex:
            check("green without a PURPOSE line is refused", "cannot be GREEN" in str(ex))
        add_flag("b.md", "yellow", "tester", "documents b", "no purpose line yet", path=fpath, kit=kit, now="2026-09-13 12:01")
        rows, t = status(kit, read(fpath))
        check("tally counts one green and one yellow", t["green"] == 1 and t["yellow"] == 1 and t["unflagged"] == 0)
        write(os.path.join(kit, "hooks", "a.py"), '"""PURPOSE: guards the thing well enough.\nINTENT: owner.\n"""\nchanged = 1\n')
        rows, t = status(kit, read(fpath))
        check("a changed file is STALE", t["stale"] == 1 and [r for r in rows if r[0] == "hooks/a.py"][0][1] == "STALE")
        add_flag("hooks/a.py", "red", "tester", "now also writes", "writes outside its purpose", path=fpath, kit=kit, now="2026-09-13 12:02")
        rows, t = status(kit, read(fpath))
        check("newest entry wins; red counted; no longer stale", t["red"] == 1 and t["green"] == 0 and t["stale"] == 0)
        n = read(fpath).count("### ")
        check("entries are append-only (three kept)", n == 3)
        rows, t = status(kit, read(fpath))
        regenerate(rows, t, path=fpath)
        before = read(fpath)
        check("regenerate with nothing changed leaves FLAGS.md byte-identical (Q0003)",
              regenerate(rows, t, path=fpath) is False and read(fpath) == before)
        t2 = dict(t, green=t["green"] + 1)
        check("regenerate with a changed tally rewrites the block",
              regenerate(rows, t2, path=fpath) is True and read(fpath) != before)
        try:
            add_flag("hooks/a.py", "green", "t", "does — x", "y", path=fpath, kit=kit)
            check("em dash in an entry is refused", False)
        except SystemExit as ex:
            check("em dash in an entry is refused", "dash" in str(ex))
        try:
            add_flag("hooks/a.py", "blue", "t", "x", "y", path=fpath, kit=kit)
            check("bad color refused", False)
        except SystemExit:
            check("bad color refused", True)
        try:
            add_flag("nope.py", "green", "t", "x", "y", path=fpath, kit=kit)
            check("unknown item refused", False)
        except SystemExit:
            check("unknown item refused", True)
    print("purpose_audit selftest: %d failed" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

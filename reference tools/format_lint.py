"""THE FORMAT LINT (the CEO's ruling 2026-09-13, INTENT.md "The format law:
one header for every kit thing, flagged when missing, rewritten by script").

PURPOSE: check every kit thing (a script, a hook, a skill, a method file,
  the hooks README, the settings template) and its repo original for the
  one header the filing system needs - PURPOSE, INTENT, Search keys, See
  also - plus the safety wiring in settings.json; report PASS/FAIL per
  file with the reason; on request rewrite ONLY the missing scaffold
  lines, never the body.
INTENT: the CEO 2026-09-13: "Any updates, upgrades, hooks, scripts, etc
  need to be in the same format so that they work with our current filing
  system. Anything without proper format should be flagged, a script
  should re-write it after review-only audit. This will be a law and may
  need this to be a hook somehow so that no one can inject a prompt that
  overrides safety protocols."

    python tools/format_lint.py                  # every kit thing + originals; ledger line; exit 1 on FAIL
    python tools/format_lint.py --quiet          # one summary line
    python tools/format_lint.py --file <path>    # one file (what the format guard runs)
    python tools/format_lint.py --rewrite <path> --purpose "..." --intent "..." [--keys "..."] [--also "..."]
    python tools/format_lint.py --selftest

THE FORMAT (the whole law, also in the kit's CONTRIBUTING.md):
  every thing carries, in its header (a Python module docstring; the lines
  right after a Markdown file's title; the top of a .txt), these lines:
    PURPOSE: what the thing does, plainly, one or two lines
    INTENT:  why it exists - the owner's words, or an INTENT.md heading
    Search keys: ...      See also: ...   (the wiki convention; scripts + MDs)
  a hook script also carries a --selftest and imports _hooklib;
  a skill's SKILL.md carries the frontmatter (name = its folder, description);
  a settings template parses, names only hook scripts that exist beside it,
  and keeps every SAFETY hook wired with its required matcher (the part no
  prompt may override - the format guard refuses the edit, the Stop hook
  refuses the turn).
  A placeholder "(unfilled)" is scaffolding, not a header: it still FAILS,
  so a rewrite without the reviewer's words never passes by itself.

Scope is DERIVED, never listed: every file in the kit folder, plus the
repo original of each (tools/hooks/*.py, the tools/*.py that have a
reference copy, .claude/skills/*/SKILL.md, the repo-root MDs the kit
mirrors, .claude/settings.json). A file outside that scope is never
touched by this lint or its hook.

Search keys: format lint, format law, purpose line, intent line, header
format, kit format, safety wiring, settings.json check, rewrite scaffold,
contributing.
See also: tools/hooks/format_guard.py (the hook: refuses the unsafe
settings edit, blocks the unformatted edit); tools/purpose_audit.py (the
flag ledger the audit files into); tools/refresh_kit.py (originals ->
kit copies); tools/sync_kit_repo.py (refuses to publish on FAIL);
"Future Project MDs/CONTRIBUTING.md" (the law for contributors);
WORKFLOWS.md "Format-check and rewrite a kit thing"; INTENT.md.
"""
import datetime
import json
import os
import re
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ledger

NL = chr(10)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ----------------------------------------------------------- CONFIG --
KIT_DIR = os.path.join(ROOT, "Future Project MDs")
HOOKS_DIR = os.path.join(ROOT, "tools", "hooks")
TOOLS_DIR = os.path.join(ROOT, "tools")
SKILLS_DIR = os.path.join(ROOT, ".claude", "skills")
SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
LEDGER = os.path.join(ROOT, "docs", "history", "format_lint_runs.txt")
HOOK_LIB = "_hooklib.py"
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_NAMES = {"LICENSE", ".gitignore"}
# The safety protocols: hook script -> [(event, required tools in its matcher)].
# An absent matcher matches every tool, which satisfies any requirement.
SAFETY = {
    "preserve_guard.py": [("PreToolUse", {"Bash", "Write", "Edit"})],
    "bash_guard.py":     [("PreToolUse", {"Bash"})],
    "fanout_guard.py":   [("PreToolUse", set())],
    "diet_guard.py":     [("PreToolUse", {"Read", "Bash"})],
    "hygiene_guard.py":  [("PostToolUse", {"Write", "Edit"})],
    "format_guard.py":   [("PreToolUse", {"Write", "Edit"}), ("PostToolUse", {"Write", "Edit"})],
    "stop_tick.py":      [("Stop", set())],
}
PLACEHOLDER = "(unfilled - a read-only audit fills this; see FLAGS.md)"
MIN_TEXT = 12
# -----------------------------------------------------------------------


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def norm(path):
    return os.path.normpath(os.path.abspath(path))


def under(path, folder):
    try:
        return os.path.commonpath([norm(path).lower(), norm(folder).lower()]) == norm(folder).lower()
    except ValueError:
        return False


# ------------------------------------------------------------- scope --
def kit_md_names():
    try:
        return {n for n in os.listdir(KIT_DIR) if n.endswith(".md")}
    except OSError:
        return set()


def ref_tool_names():
    try:
        return {n for n in os.listdir(os.path.join(KIT_DIR, "reference tools")) if n.endswith(".py")}
    except OSError:
        return set()


def classify(path):
    """-> 'py' | 'hook' | 'skill' | 'md' | 'txt' | 'settings' | None (out of scope)."""
    p = norm(path)
    name = os.path.basename(p)
    if name in SKIP_NAMES or any(s in p.split(os.sep) for s in SKIP_DIRS):
        return None
    if under(p, KIT_DIR):
        rel = os.path.relpath(p, KIT_DIR).replace("\\", "/")
        if name == "settings.json":
            return "settings"
        if name.endswith(".py"):
            return "hook" if rel.startswith("hooks/") else "py"
        if name == "SKILL.md":
            return "skill"
        if name.endswith(".md"):
            return "md"
        if name.endswith(".txt"):
            return "txt"
        return None
    if p.lower() == norm(SETTINGS).lower():
        return "settings"
    if under(p, HOOKS_DIR) and name.endswith(".py"):
        return "hook"
    if under(p, SKILLS_DIR) and name == "SKILL.md":
        return "skill"
    if os.path.dirname(p).lower() == norm(TOOLS_DIR).lower() and name in ref_tool_names():
        return "py"
    if os.path.dirname(p).lower() == norm(ROOT).lower() and name in kit_md_names():
        return "md"
    return None


def scope():
    """[(abs path, class)] - the kit folder whole, then each original."""
    items = []
    for base, dirs, files in os.walk(KIT_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            p = os.path.join(base, f)
            c = classify(p)
            if c:
                items.append((p, c))
    originals = []
    if os.path.isdir(HOOKS_DIR):
        originals += [os.path.join(HOOKS_DIR, f) for f in sorted(os.listdir(HOOKS_DIR)) if f.endswith(".py")]
    originals += [os.path.join(TOOLS_DIR, n) for n in sorted(ref_tool_names())]
    if os.path.isdir(SKILLS_DIR):
        originals += [os.path.join(SKILLS_DIR, d, "SKILL.md") for d in sorted(os.listdir(SKILLS_DIR))]
    originals += [os.path.join(ROOT, n) for n in sorted(kit_md_names())]
    originals.append(SETTINGS)
    for p in originals:
        if os.path.isfile(p):
            c = classify(p)
            if c:
                items.append((p, c))
    return items


# ------------------------------------------------------------ checks --
Q = r"^\s*(?:\"\"\"|''')?\s*"   # a header line may open the docstring itself
LINE = {
    "purpose": re.compile(Q + r"PURPOSE:\s*(.*)$", re.M),
    "intent": re.compile(Q + r"INTENT:\s*(.*)$", re.M),
    "keys": re.compile(Q + r"Search keys:\s*(.*)$", re.M),
    "also": re.compile(Q + r"See also:\s*(.*)$", re.M),
}
LABEL = {"purpose": "PURPOSE:", "intent": "INTENT:", "keys": "Search keys:", "also": "See also:"}


def filled(text, key):
    m = LINE[key].search(text)
    if not m:
        return False
    body = m.group(1).strip()
    need = MIN_TEXT if key in ("purpose", "intent") else 3
    return len(body) >= need and not body.lower().startswith("(unfilled")


def docstring_span(lines):
    """(open_idx, close_idx) of the module docstring, or None. A one-line
    docstring returns the same index twice."""
    for i, l in enumerate(lines[:12]):
        s = l.strip()
        if not s or s.startswith("#"):
            continue
        for q in ('"""', "'''"):
            if s.startswith(q):
                if s.count(q) >= 2:
                    return i, i
                for j in range(i + 1, len(lines)):
                    if q in lines[j]:
                        return i, j
                return i, len(lines) - 1
        return None
    return None


def check_text(text, cls, path=""):
    """-> [problem strings]; empty = PASS."""
    probs = []
    name = os.path.basename(path)
    if cls == "settings":
        return check_settings_text(text, os.path.dirname(path) if under(path, KIT_DIR) else HOOKS_DIR)
    need = ["purpose", "intent"]
    if cls in ("py", "hook", "md"):
        need += ["keys", "also"]
    for k in need:
        if not LINE[k].search(text):
            probs.append("missing %s line" % LABEL[k])
        elif not filled(text, k):
            probs.append("%s line is a placeholder or too short" % LABEL[k])
    if cls in ("py", "hook"):
        if docstring_span(text.split("\n")) is None:
            probs.append("no module docstring (the header lives there)")
    if cls == "hook" and name != HOOK_LIB:
        if "_hooklib" not in text:
            probs.append("hook does not import _hooklib")
        if "--selftest" not in text:
            # a hook that can refuse or block can lock the user out on a bug:
            # its selftest is required; an info-only hook gets a WARN line
            if "deny(" in text or '"block"' in text:
                probs.append("hook can refuse/block but has no --selftest")
            else:
                probs.append("WARN: info-only hook has no --selftest")
    if cls == "skill":
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            probs.append("no frontmatter (--- name/description ---)")
        else:
            fm = m.group(1)
            nm = re.search(r"^name:\s*(\S+)", fm, re.M)
            folder = os.path.basename(os.path.dirname(norm(path)))
            if not nm:
                probs.append("frontmatter has no name:")
            elif path and nm.group(1) != folder:
                probs.append("frontmatter name '%s' != folder '%s'" % (nm.group(1), folder))
            if not re.search(r"^description:\s*\S", fm, re.M):
                probs.append("frontmatter has no description:")
    if cls in ("md", "skill") and not re.search(r"^# \S", text, re.M):
        probs.append("no '# ' title line")
    return probs


def check_settings_text(text, hooks_dir):
    probs = []
    try:
        data = json.loads(text)
    except Exception as e:  # noqa: BLE001
        return ["settings.json does not parse (%s) - a broken file silently disables EVERY hook" % e]
    hooks = (data or {}).get("hooks") or {}
    wired = {}  # script name -> [(event, matcher)]
    for event, entries in hooks.items():
        for entry in entries or []:
            matcher = (entry or {}).get("matcher") or ""
            for h in (entry or {}).get("hooks") or []:
                cmd = (h or {}).get("command") or ""
                m = re.search(r"hooks/([A-Za-z0-9_]+\.py)", cmd)
                if not m:
                    continue
                wired.setdefault(m.group(1), []).append((event, matcher))
                if hooks_dir and not os.path.isfile(os.path.join(hooks_dir, m.group(1))):
                    probs.append("command names hooks/%s which does not exist beside it" % m.group(1))
    for script, reqs in SAFETY.items():
        if hooks_dir and not os.path.isfile(os.path.join(hooks_dir, script)):
            continue  # a kit that has not adopted this hook yet is not unsafe
        for event, tools in reqs:
            ok = False
            for ev, matcher in wired.get(script, []):
                if ev != event:
                    continue
                have = {t.strip() for t in matcher.split("|") if t.strip()}
                if not matcher or tools <= have:
                    ok = True
            if not ok:
                probs.append("SAFETY: %s is not wired on %s%s" % (
                    script, event, (" for " + "|".join(sorted(tools))) if tools else ""))
    return probs


def hard(probs):
    """The failures that count; WARN lines are reported, never a FAIL."""
    return [p for p in probs if not p.startswith("WARN")]


def check_file(path):
    cls = classify(path)
    if not cls:
        return []
    try:
        text = read(path)
    except OSError as e:
        return ["unreadable (%s)" % e]
    return check_text(text, cls, path)


# ----------------------------------------------------------- rewrite --
def _block(key, value, width=76):
    """'PURPOSE: text' wrapped, continuation lines indented two spaces."""
    first = LABEL[key] + " "
    return textwrap.fill(value, width=width, initial_indent=first,
                         subsequent_indent="  ").split("\n")


def _replace_placeholder(lines, key, value):
    for i, l in enumerate(lines):
        m = re.match(r"^(\s*(?:\"\"\"|''')?\s*)" + re.escape(LABEL[key]) + r"\s*(.*)$", l)
        if m and m.group(2).strip().lower().startswith("(unfilled"):
            lines[i] = m.group(1) + LABEL[key] + " " + value
            return True
    return False


def rewrite(path, purpose=None, intent=None, keys=None, also=None, cls=None):
    """Insert the missing scaffold lines; replace placeholders; never remove.
    -> list of what changed. cls overrides classification (tests only)."""
    cls = cls or classify(path)
    if not cls:
        raise SystemExit("out of scope: %s (the format law covers kit things and their originals)" % path)
    if cls == "settings":
        raise SystemExit("settings.json carries no header - its rule is the safety wiring; fix the JSON by hand")
    text = read(path)
    lines = text.split("\n")
    values = {"purpose": purpose or PLACEHOLDER, "intent": intent or PLACEHOLDER}
    if cls in ("py", "hook", "md"):
        values.update(keys=keys or PLACEHOLDER, also=also or PLACEHOLDER)
    changed = []
    for k, v in list(values.items()):
        if LINE[k].search(text):
            if _replace_placeholder(lines, k, v):
                changed.append("filled " + LABEL[k])
            values.pop(k)
    head = [k for k in ("purpose", "intent") if k in values]
    tail = [k for k in ("keys", "also") if k in values]
    if cls in ("py", "hook"):
        span = docstring_span(lines)
        if span is None:
            i = 0
            while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i][:40]):
                i += 1
            block = ['"""' + _block("purpose", values["purpose"])[0]]
            block += _block("purpose", values["purpose"])[1:]
            block += _block("intent", values["intent"])
            block += [""] + _block("keys", values.get("keys", PLACEHOLDER))
            block += _block("also", values.get("also", PLACEHOLDER)) + ['"""', ""]
            lines[i:i] = block
            changed.append("created the module docstring with the header")
        else:
            o, c = span
            if o == c:  # one-line docstring: open it up
                s = lines[o]
                q = '"""' if '"""' in s else "'''"
                body = s.strip()[3:-3]
                lines[o:o + 1] = [q + body, q]
                c = o + 1
            ins = []
            for k in head:
                ins += _block(k, values[k])
            tail_ins = []
            for k in tail:
                tail_ins += _block(k, values[k])
            # head lines go before "Search keys:" if it is inside the docstring, else before the close
            anchor = None
            for j in range(o + 1, c):
                if LINE["keys"].match(lines[j]):
                    anchor = j
                    break
            close_line = lines[c]
            q = '"""' if '"""' in close_line else "'''"
            pre = close_line[:close_line.index(q)]
            if pre.strip():  # text before the closing quotes: split it
                lines[c:c + 1] = [pre.rstrip(), q + close_line[close_line.index(q) + 3:]]
                c += 1
            if anchor is None:
                if ins and lines[c - 1].strip():
                    ins = [""] + ins
                lines[c:c] = ins + ([""] if (ins and tail_ins) else []) + tail_ins
            else:
                lines[c:c] = tail_ins
                lines[anchor:anchor] = ins + ([""] if ins else [])
            if ins or tail_ins:
                changed.append("inserted " + ", ".join(LABEL[k] for k in head + tail))
    else:  # md, skill, txt
        ins = []
        for k in head:
            ins += _block(k, values[k])
        if ins:
            at = 0
            if cls in ("md", "skill"):
                start = 0
                if cls == "skill" and lines and lines[0].strip() == "---":
                    for j in range(1, len(lines)):
                        if lines[j].strip() == "---":
                            start = j + 1
                            break
                for j in range(start, len(lines)):
                    if lines[j].startswith("# "):
                        at = j + 1
                        break
                else:
                    at = start
            else:
                at = 1 if lines and lines[0].strip() else 0
            lines[at:at] = [""] + ins
            changed.append("inserted " + ", ".join(LABEL[k] for k in head))
        tail_ins = []
        for k in tail:
            tail_ins += _block(k, values[k])
        if tail_ins:
            while lines and not lines[-1].strip():
                lines.pop()
            lines += [""] + tail_ins + [""]
            changed.append("appended " + ", ".join(LABEL[k] for k in tail))
    if changed:
        write(path, "\n".join(lines))
    return changed


# ------------------------------------------------------------ ledger --
def ledger(items, fails):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    names = "; ".join(os.path.relpath(p, ROOT).replace("\\", "/") for p, _ in fails[:4])
    line = "%s | %s | %d | %d | %s | %s\n" % (now, workstation(), len(items), len(fails),
                                              "FAIL" if fails else "PASS", names or "clean")
    if not os.path.isfile(LEDGER):
        with open(LEDGER, "w", encoding="utf-8") as f:
            f.write("# format lint runs: date | ws | items | failing | PASS/FAIL | first failing\n")
    _ledger.append_unless_identical(LEDGER, line)
    return line.strip()


def main(argv):
    if "--selftest" in argv:
        return selftest()
    quiet = "--quiet" in argv
    if "--rewrite" in argv:
        i = argv.index("--rewrite")
        path = argv[i + 1]

        def opt(flag):
            return argv[argv.index(flag) + 1] if flag in argv else None
        changed = rewrite(path, opt("--purpose"), opt("--intent"), opt("--keys"), opt("--also"))
        print("rewrote %s: %s" % (path, "; ".join(changed) if changed else "nothing to add"))
        probs = check_file(path)
        print("now: " + ("PASS" if not hard(probs) else "FAIL") + (" - " + "; ".join(probs) if probs else ""))
        return 1 if hard(probs) else 0
    if "--file" in argv:
        path = argv[argv.index("--file") + 1]
        cls = classify(path)
        if not cls:
            print("out of scope: %s" % path)
            return 0
        probs = check_file(path)
        print(("PASS  " if not hard(probs) else "FAIL  ") + path + ("" if not probs else " - " + "; ".join(probs)))
        return 1 if hard(probs) else 0
    items = scope()
    fails = []
    for p, c in items:
        probs = check_text(read(p), c, p)
        r = os.path.relpath(p, ROOT).replace("\\", "/")
        if hard(probs):
            fails.append((p, probs))
            if not quiet:
                print("FAIL  [%s] %s - %s" % (c, r, "; ".join(probs)))
        elif not quiet:
            print("%s  [%s] %s%s" % ("WARN" if probs else "PASS", c, r, (" - " + "; ".join(probs)) if probs else ""))
    line = ledger(items, fails)
    print(("FORMAT LINT %s: %d items, %d failing" % ("FAIL" if fails else "PASS", len(items), len(fails)))
          + (" - rewrite with `python tools/format_lint.py --rewrite <path> --purpose ... --intent ...` "
             "after a read-only audit" if fails else ""))
    print("ledger: " + line)
    return 1 if fails else 0


# ---------------------------------------------------------- selftest --
def selftest():
    import tempfile
    fails = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    good_py = ('"""Title.\n\nPURPOSE: does the thing plainly enough.\nINTENT: because the owner said so.\n\n'
               'Search keys: a, b, c, d.\nSee also: x.md.\n"""\nimport sys\n')
    check("good py passes", check_text(good_py, "py", "x.py") == [])
    bad_py = '"""Title only.\n\nSearch keys: a, b, c, d.\nSee also: x.md.\n"""\n'
    p = check_text(bad_py, "py", "x.py")
    check("py without PURPOSE/INTENT fails on both", any("PURPOSE" in x for x in p) and any("INTENT" in x for x in p))
    ph = good_py.replace("does the thing plainly enough.", PLACEHOLDER)
    check("placeholder PURPOSE still fails", any("placeholder" in x for x in check_text(ph, "py", "x.py")))
    check("short PURPOSE fails", any("short" in x for x in check_text(
        good_py.replace("does the thing plainly enough.", "short"), "py", "x.py")))
    hook_ok = good_py.replace("import sys", "from _hooklib import read_input\n# --selftest")
    check("hook with _hooklib + selftest passes", check_text(hook_ok, "hook", "g.py") == [])
    check("info-only hook missing selftest is a WARN", any(x.startswith("WARN") for x in check_text(
        good_py.replace("import sys", "from _hooklib import x"), "hook", "g.py")))
    check("refusing hook missing selftest FAILS", any("refuse" in x for x in hard(check_text(
        good_py.replace("import sys", "from _hooklib import deny\ndeny('x')"), "hook", "g.py"))))
    check("_hooklib itself needs no import", not any("import" in x for x in check_text(good_py, "hook", HOOK_LIB)))
    skill_ok = "---\nname: ship\ndescription: ships.\n---\n\n# /ship\n\nPURPOSE: ships the batch every time.\nINTENT: the owner asked for it.\n"
    check("skill passes", check_text(skill_ok, "skill", os.path.join("k", "ship", "SKILL.md")) == [])
    check("skill name != folder fails", any("folder" in x for x in check_text(
        skill_ok, "skill", os.path.join("k", "brief", "SKILL.md"))))
    check("skill without frontmatter fails", any("frontmatter" in x for x in check_text(
        skill_ok.split("---\n\n")[-1], "skill", os.path.join("k", "ship", "SKILL.md"))))
    md_ok = "# T\n\nPURPOSE: explains the method fully.\nINTENT: the owner wanted it written.\n\nSearch keys: a, b, c, d.\nSee also: y.md.\n"
    check("md passes", check_text(md_ok, "md", "T.md") == [])
    check("md without See also fails", any("See also" in x for x in check_text(md_ok.replace("See also", "See"), "md", "T.md")))
    check("txt needs only PURPOSE/INTENT", check_text("t\nPURPOSE: explains the hooks folder.\nINTENT: the owner wanted it.\n", "txt", "R.txt") == [])

    # settings: safety wiring
    with tempfile.TemporaryDirectory() as td:
        for s in SAFETY:
            open(os.path.join(td, s), "w").write("#")
        good = {"hooks": {
            "PreToolUse": [{"matcher": "Bash|PowerShell", "hooks": [{"command": "python hooks/bash_guard.py"}]},
                           {"matcher": "Bash|PowerShell|Write|Edit|MultiEdit", "hooks": [{"command": "python hooks/preserve_guard.py"}]},
                           {"matcher": "Read|Bash|PowerShell", "hooks": [{"command": "python hooks/diet_guard.py"}]},
                           {"hooks": [{"command": "python hooks/fanout_guard.py"}]},
                           {"matcher": "Write|Edit|MultiEdit", "hooks": [{"command": "python hooks/format_guard.py"}]}],
            "PostToolUse": [{"matcher": "Write|Edit|MultiEdit", "hooks": [{"command": "python hooks/hygiene_guard.py"},
                                                                          {"command": "python hooks/format_guard.py"}]}],
            "Stop": [{"hooks": [{"command": "python hooks/stop_tick.py"}]}]}}
        check("fully wired settings pass", check_settings_text(json.dumps(good), td) == [])
        bad = json.loads(json.dumps(good))
        bad["hooks"]["PreToolUse"] = [e for e in bad["hooks"]["PreToolUse"] if "preserve" not in json.dumps(e)]
        p = check_settings_text(json.dumps(bad), td)
        check("unwiring the preserve guard is a SAFETY failure", any("SAFETY: preserve_guard" in x for x in p))
        bad = json.loads(json.dumps(good))
        bad["hooks"]["PreToolUse"][1]["matcher"] = "Bash"
        p = check_settings_text(json.dumps(bad), td)
        check("narrowing a safety matcher fails", any("preserve_guard" in x and "Write" in x for x in p))
        bad = json.loads(json.dumps(good))
        bad["hooks"]["Stop"] = []
        check("dropping the Stop hook fails", any("stop_tick" in x for x in check_settings_text(json.dumps(bad), td)))
        bad = json.loads(json.dumps(good))
        bad["hooks"]["PreToolUse"].append({"hooks": [{"command": "python hooks/ghost.py"}]})
        check("a command naming a missing script fails", any("ghost.py" in x for x in check_settings_text(json.dumps(bad), td)))
        check("unparsable settings fail", any("parse" in x for x in check_settings_text("{nope", td)))
        check("one-line docstring span found", docstring_span(['"""One line."""', "import os"]) == (0, 0))
    with tempfile.TemporaryDirectory() as td:
        J = lambda *ls: NL.join(ls) + NL  # noqa: E731
        tmp = os.path.join(td, "t.py")
        write(tmp, J('"""Only a title.', "", "Search keys: a, b, c, d.", "See also: x.md.", '"""', "import os"))
        ch = rewrite(tmp, "does a temporary thing for the test.", "the selftest needs a file to rewrite.", cls="py")
        txt = read(tmp)
        check("rewrite inserts PURPOSE/INTENT before Search keys",
              "PURPOSE:" in txt and txt.index("PURPOSE:") < txt.index("Search keys:") and ch)
        check("rewritten file passes", check_text(txt, "py", tmp) == [])
        check("rewrite is idempotent", rewrite(tmp, "does a temporary thing for the test.", "x" * 20, cls="py") == [])
        write(tmp, J("import os"))
        rewrite(tmp, cls="py")
        txt = read(tmp)
        check("no docstring -> one is created with placeholders", txt.startswith('"""PURPOSE:') and PLACEHOLDER in txt)
        check("placeholders still FAIL the lint", check_text(txt, "py", tmp) != [])
        ch = rewrite(tmp, "fills the placeholder now for real.", "the reviewer supplied the words.",
                     "a, b, c, d, e.", "x.md, y.md.", cls="py")
        check("placeholders get filled in place", check_text(read(tmp), "py", tmp) == [] and any("filled" in c for c in ch))
        write(tmp, J('"""One line."""', "import os"))
        rewrite(tmp, "opens a one-line docstring for the test.", "the selftest asked for it.", "a, b, c, d.", "z.md.", cls="py")
        check("one-line docstring is opened and passes", check_text(read(tmp), "py", tmp) == [])
        tmpmd = os.path.join(td, "T.md")
        write(tmpmd, J("# Title", "", "body"))
        rewrite(tmpmd, "explains a temporary thing.", "the selftest asked for it.", "a, b, c, d.", "z.md.", cls="md")
        txt = read(tmpmd)
        check("md rewrite puts the header after the title and the keys at the end",
              txt.index("# Title") < txt.index("PURPOSE:") < txt.index("body") < txt.index("Search keys:"))
        check("md rewrite passes", check_text(txt, "md", tmpmd) == [])
        sk = os.path.join(td, "ship", "SKILL.md")
        os.makedirs(os.path.dirname(sk))
        write(sk, J("---", "name: ship", "description: ships.", "---", "", "# /ship", "", "body"))
        rewrite(sk, "ships the batch every time.", "the owner asked for it.", cls="skill")
        txt = read(sk)
        check("skill rewrite lands after the title, inside the body",
              txt.index("# /ship") < txt.index("PURPOSE:") < txt.index("body") and check_text(txt, "skill", sk) == [])
    check("classify: kit hook", classify(os.path.join(KIT_DIR, "hooks", "diet_guard.py")) == "hook")
    check("classify: original hook", classify(os.path.join(HOOKS_DIR, "diet_guard.py")) == "hook")
    check("classify: kit skill", classify(os.path.join(KIT_DIR, "skills", "ship", "SKILL.md")) == "skill")
    check("classify: repo settings", classify(SETTINGS) == "settings")
    check("classify: game script is out of scope", classify(os.path.join(ROOT, "scripts", "world", "main.gd")) is None)
    check("classify: non-kit tool is out of scope", classify(os.path.join(TOOLS_DIR, "run_tests.py")) is None)
    print("format_lint selftest: %d failed" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

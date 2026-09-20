"""PreToolUse guard on Bash/PowerShell/Write/Edit: THE PRESERVATION LAW.

the CEO's ruling 2026-09-10, after public reports of an agent that wrote a
script which deleted someone's personal files and another that wiped a
machine: neither the manager nor any employee deletes a file, record or
tree without the owner's EXPRESS, DOUBLE-ACKNOWLEDGED permission, and no
script is written that deletes. Knowledge is never lost: files RETIRE
(tools/retire.py -> _retired/), wiki sections go to the COLD SHELF
(tools/cold_shelf.py -> docs/cold/), both indexed.

What this guard refuses (Tier 2d):
  SHELL (Bash, PowerShell): delete verbs with a path argument (rm, rmdir,
    rd, del, erase, unlink, shred, Remove-Item, ri, Clear-Content, format,
    diskpart, truncate), find -delete / xargs rm, moves into nul or
    /dev/null, and the git verbs that discard work or history (rm, clean,
    reset --hard, checkout -- <path>, restore <path>, branch -d/-D, push
    --delete, stash drop/clear, worktree remove, tag -d, reflog expire).
    Deletion CALLS inside a one-liner or an executed heredoc count too.
    HARDENED 2026-09-20 after a public report (an agent's throwaway
    remover, written to Temp and run in a later command, walked a tree
    through Windows directory junctions - os.walk and islink() do not
    stop at a junction - and emptied a repo's .git; 48,000 files): a
    bare-name target (rm build), a pipeline or foreach body feeding a
    delete verb, find -exec, the mirror verbs (robocopy with its mirror or
    purge switch, rsync with its delete flag), git checkout of a path or `.`, git
    switch --discard-changes, force pushes of every kind, branch -f/-M,
    filter-branch and prune; a heredoc body written to a SCRIPT file is
    scanned (only a prose target is skipped); and every script the
    command EXECUTES (python x.py, pwsh -File, bash x.sh, node ...) is
    read and scanned before it runs - the whole file if git does not
    track it, the uncommitted added lines if it does. A variable target
    ($DIR, %X%) is refused outright: the guard cannot read it, so no
    grant can cover it. A crash in the guard falls back to a crude
    substring check (fail closed on the obvious verbs, never fail open).
  WRITE (Write, Edit, MultiEdit, NotebookEdit): content that adds deletion
    calls to a file (os.remove, shutil.rmtree, Path.unlink, DirAccess
    remove, fs.rm, File.Delete, Remove-Item in a script...).
What it lets through:
  - deletes whose every path lies inside the session scratchpad
    (%TEMP%/claude/...), the harness's own per-session junk;
  - a heredoc BODY fed to cat/tee (a file write that merely mentions a
    verb) - a body fed to an interpreter is scanned;
  - ONE command matching a live GRANT: tools/delete_grant.py records the
    manager's question and the owner's two acknowledgments (verbatim) in
    .claude/delete_grant.json + the docs/history/delete_grants.txt ledger;
    the guard consumes the grant on first use (marks it used, never
    deletes the file).
NEVER, grant or not: a drive root, the home folder, the repo root, any
.git folder, a bare or dot-slash wildcard, a .. climb, a variable target.
Those have no legitimate shape.

A refusal is the owner's standing decision: stop, and either move the
thing (retire / cold shelf) or ask the CEO twice and record the grant.
`--selftest` runs the in-process checks (no harness needed).

PURPOSE: PreToolUse guard on Bash, PowerShell, Write, Edit, MultiEdit and
  NotebookEdit implementing the preservation law: refuses shell delete verbs
  (bare names, pipelines, foreach bodies, find -exec and the mirror verbs
  included), git verbs that discard work or rewrite history (every force
  push included), deletion calls written into a non-prose file, and any
  script a command executes whose untracked body or uncommitted added lines
  carry a deletion shape; narrow exceptions for the session scratchpad,
  prose files, heredoc bodies aimed at prose, permission-rule strings in a
  settings file, and one command consumed against a twice-acknowledged
  delete grant; a drive root, the home folder, the repo root, any .git
  folder, a bare wildcard, a .. climb or a variable target are refused even
  with a grant; a crash falls back to a crude check that refuses.
INTENT: stops the manager or an employee from deleting anything without the
  owner's express, double-acknowledged permission, after public reports of
  an agent's script that deleted personal files and another that wiped a
  machine; knowledge moves instead of disappearing.

Search keys: preservation law, delete guard, never delete, grant,
double acknowledgment, retire, cold shelf, rm guard, git reset hard.
See also: tools/delete_grant.py (the grant); tools/retire.py (files move,
never die); tools/cold_shelf.py (wiki sections); docs/systems/tooling.md
(The hooks); HOOKS_METHOD.md (portable); WIKI_METHOD.md (the cold shelf).
"""
import json
import os
import re
import subprocess
import sys
import time

from _hooklib import ROOT, deny, read_input

GRANT = os.path.join(ROOT, ".claude", "delete_grant.json")
LAW = ("THE PRESERVATION LAW (the CEO's ruling 2026-09-10): nothing is "
       "deleted or discarded without the owner's express, double-acknowledged "
       "permission, and no script is written that deletes. ")
HOW = ("MOVE instead: `python tools/retire.py <path> --reason ...` (files -> "
       "_retired/, ledgered) or `python tools/cold_shelf.py --move` (wiki "
       "sections -> docs/cold/). If the CEO has approved THIS exact deletion "
       "twice, record both acknowledgments verbatim: `python tools/delete_grant.py "
       "--target \"<path>\" --ask \"<your question>\" --ack1 \"<first yes>\" "
       "--ack2 \"<second yes>\"`, then retry ONCE.")

# Deletion CALLS (code in any language). Written with escapes so this
# file's own source never matches its own patterns.
CODE = [
    r"\bos\s*\.\s*(remove|unlink|rmdir|removedirs)\s*\(",
    r"\bshutil\s*\.\s*rmtree\s*\(",
    r"\.\s*unlink\s*\(\s*(missing_ok\s*=\s*\w+\s*)?\)",
    r"\.\s*rmdir\s*\(\s*\)",
    r"\bsend2trash\s*\(",
    r"\bDirAccess\s*\.\s*remove(_absolute)?\s*\(",
    r"\bOS\s*\.\s*move_to_trash\s*\(",
    r"\bfs\s*\.\s*(rm|rmSync|unlink|unlinkSync|rmdir|rmdirSync)\s*\(",
    r"\b(File|Directory)\s*\.\s*Delete\s*\(",
    r"\[System\.IO\.(File|Directory)\]\s*::\s*Delete\s*\(",
    r"\bos\s*\.\s*system\s*\([^)]*\b(rm|rd|del|rmdir|erase)\b",
    r"\bsubprocess\s*\.\s*\w+\s*\([^)]*['\"](rm|rd|del|rmdir|erase|unlink|shred|remove[-]item)['\"]",
    r"\bpromises\s*\.\s*(rm|unlink|rmdir)\s*\(",
    r"\brimraf\s*\(",
    r"\b(shutil\s*\.\s*move|os\s*\.\s*(rename|replace))\s*\([^)]*(/dev/null|\bnul\b)",
]
# Shell delete shapes inside a SCRIPT body (a .ps1/.sh/.bat being written,
# a heredoc aimed at a script file, an untracked script about to run).
# Matched case-insensitively.
SCRIPT_VERBS = [
    r"(^|[\s;&(`{\"'])(remove[-]item(?=\s)|r[i](?=\s)|r[m]\s+-\w*[rf]|r[m]dir\s+/s|r[d]\s+/s|d[e]l\s+/[sq]|erase\s+/[sq])",
    r"(?m)^\s*r[m]\s+[^-\s]",
    r"(\||\{)\s*(remove[-]item|r[i]|r[m]|d[e]l|r[d]|r[m]dir)(?=\s|$)",
    r"\brobocopy\b[^\n]*\s/(mir|purge)\b",
    r"\brsync\b[^\n]*\s--delete",
    r"\bfind\b[^\n]*\s(-delete|-exec\s+(rm|rmdir|unlink|shred))\b",
    r"\bgit\s+(clean|reset\s+--hard|push\b[^\n]*\s(--force|-f)|filter-branch)\b",
]
# Files the shell can execute; an untracked one is read before it runs.
SCRIPT_EXT = (".py", ".pyw", ".ps1", ".sh", ".bash", ".bat", ".cmd", ".js",
              ".mjs", ".ts", ".rb", ".pl", ".gd")
# Shell verbs that need a path-like argument (so `del d[k]` in Python
# text or `rm` as a word in prose never fires).
ARG = r"(\s+-{1,2}[\w:-]+)*\s+(?P<arg>[^\s;|&]*[\\/.*~][^\s;|&]*)"
# Any argument at all (a bare name: rm build) - only where the verb STARTS
# a command (line start, ;, |, &, (, `, {, cmd /c, -c "..."), so a verb
# inside prose or a commit message never fires.
BARE = r"(\s+-{1,2}[\w:-]+)*\s+(?P<arg>[^\s;|&<>-][^\s;|&<>]*)"
SEP = r"(^|[\s;|&(`{\"'\n]|/[ck]\s+|-c(ommand)?\s+\"?)"
START = r"(^|[;|&(`{\n]|/[ck]\s+|-c(ommand)?\s+\"?)\s*"
VERBS = [
    SEP + r"(?P<verb>rm|rmdir|rd|del|erase|unlink|shred|remove[-]item|ri|"
    r"clear[-]content|clc|truncate)(\.exe)?" + ARG,
    START + r"(?P<verb>rm|rmdir|rd|erase|shred|remove[-]item|ri)(\.exe)?" + BARE,
    r"(\|\s*|(foreach(-object)?|%)\s*\{\s*)(?P<verb>rm|rmdir|rd|del|erase|remove[-]item|ri)\b",
    r"(^|[\s;|&(`])(?P<verb>format)\s+(?P<arg>[a-z]:)",
    r"(^|[\s;|&(`])(?P<verb>format-volume|diskpart|cipher\s+/w)",
    r"\bfind\b[^|;&\n]*\s(?P<verb>-delete)\b",
    r"\bfind\b[^|;&\n]*-exec\s+(?P<verb>rm|rmdir|unlink|shred)\b",
    r"\|\s*xargs\b[^|;&\n]*\s(?P<verb>rm|del|rd|rmdir|remove[-]item)\b",
    r"\b(?P<verb>mv|move|move-item)\b[^|;&\n]*\s(?P<arg>/dev/null|nul)\b",
    r"\brobocopy\b[^|;&\n]*\s(?P<verb>/mir|/purge)\b",
    r"\brsync\b[^|;&\n]*\s(?P<verb>--delete)",
]
GIT = [
    (r"\bgit\s+(?P<verb>rm)\b", "removes tracked files"),
    (r"\bgit\s+(?P<verb>clean)\b", "deletes untracked files"),
    (r"\bgit\s+reset\s+(?P<verb>--hard|--merge)\b", "discards uncommitted work"),
    (r"\bgit\s+(?P<verb>checkout)\s+(\S+\s+)?--\s+\S", "discards working-tree changes"),
    (r"\bgit\s+(?P<verb>restore)\b(?![^|;&\n]*--staged)", "discards working-tree changes"),
    (r"\bgit\s+branch\s+(?P<verb>-[dD]|--delete)\b", "deletes a branch"),
    (r"\bgit\s+push\b[^|;&\n]*(?P<verb>--delete|\s:\S)", "deletes a remote branch"),
    (r"\bgit\s+stash\s+(?P<verb>drop|clear)\b", "deletes stashed work"),
    (r"\bgit\s+worktree\s+(?P<verb>remove|prune)\b", "deletes a worktree"),
    (r"\bgit\s+tag\s+(?P<verb>-d|--delete)\b", "deletes a tag"),
    (r"\bgit\s+update-ref\s+(?P<verb>-d)\b", "deletes a ref"),
    (r"\bgit\s+reflog\s+(?P<verb>expire|delete)\b", "erases history"),
    (r"\bgit\s+gc\b[^|;&\n]*(?P<verb>--prune)", "erases history"),
    # 2026-09-20 hardening.
    (r"\bgit\s+checkout\s+(?P<verb>\.|-f|--force)(\s|$)", "discards working-tree changes"),
    (r"\bgit\s+checkout\s+(?!-[bBt]\b|--orphan|--track)(\S+\s+)+(?P<verb>[^\s-]\S*[/.]\S*)(\s|$)",
     "checkout of a path discards working-tree changes"),
    (r"\bgit\s+checkout\s+(?P<verb>[^\s-]\S*\.(gd|py|md|txt|tres|tscn|json|cfg|csv|ps1|sh|godot|import|png|html|js|css))(\s|$)",
     "checkout of a file discards working-tree changes"),
    (r"\bgit\s+switch\s+[^|;&\n]*(?P<verb>--discard-changes|-f|--force)\b", "discards working-tree changes"),
    (r"\bgit\s+push\b[^|;&\n]*\s(?P<verb>--force(-with-lease|-if-includes)?(=\S+)?|-f|\+\S+)", "rewrites remote history"),
    (r"\bgit\s+branch\s+(?P<verb>-f|--force|-M)\b", "overwrites a branch pointer"),
    (r"\bgit\s+(?P<verb>filter-branch|filter-repo|prune|prune-packed)\b", "erases history"),
]
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# Documentation is not a script: a law written down names the verbs it
# bans (the guard refused its own tooling.md row on first contact).
PROSE_EXT = (".md", ".txt", ".rst", ".csv", ".html")
SHELL_TOOLS = ("Bash", "PowerShell")


def _norm(p):
    p = (p or "").strip().strip("'\"`").replace("\\", "/").lower().rstrip("/")
    home = os.path.expanduser("~").replace("\\", "/").lower().rstrip("/")
    for tok in ("~", "$home", "${home}", "%userprofile%", "$env:userprofile"):
        if p == tok or p.startswith(tok + "/"):
            p = home + p[len(tok):]
    return p


def scratch_root():
    for var in ("TEMP", "TMP", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            base = base.replace("\\", "/").lower().rstrip("/")
            if var == "LOCALAPPDATA":
                base += "/temp"
            return base + "/claude"
    return "/tmp/claude"


def never_reason(paths):
    """A target no grant can cover - returns the reason or None."""
    home = os.path.expanduser("~").replace("\\", "/").lower().rstrip("/")
    root = ROOT.replace("\\", "/").lower().rstrip("/")
    for p in paths:
        if p in ("", "*", "/*", "/", ".", "./", "..", "../", "./*", "~/*", "*/*"):
            return "a bare root or wildcard target"
        if re.fullmatch(r"[a-z]:(/\*?)?", p):
            return "a drive root"
        if p in (home, home + "/*"):
            return "the home folder"
        if p in (root, root + "/*"):
            return "the repo root"
        if re.search(r"(^|/)\.git(/|$)", p):
            return "a .git folder"
        if p.startswith("../") or "/../" in p:
            return "a path that climbs out with .."
        if p.startswith(("$", "%")) or "$(" in p or "${" in p or re.search(r"%\w+%", p):
            return ("a variable target (the guard cannot read it, so no grant "
                    "can cover it - name the path literally)")
    return None


def strip_write_heredocs(cmd):
    """Drop heredoc / here-string BODIES that only feed a file write
    (cat/tee/Set-Content/Out-File): mentioning a verb in text is not
    running it. Bodies fed to bash/sh/python/pwsh stay and get scanned."""
    def repl(m):
        head, tag = m.group(1), m.group(3)
        if re.search(r"\b(cat|tee|set-content|out-file|add-content)\b", head, re.I):
            # 2026-09-20: only a PROSE target is skipped; a body aimed at a
            # script file (or an unknown target) is scanned like code.
            tgt = re.search(r"(>{1,2}|tee|-path|-filepath)\s*\"?'?([^\s\"'|;&]+)", head, re.I)
            name = (tgt.group(2) if tgt else "").lower()
            if name.endswith(PROSE_EXT):
                return head + "\n<HEREDOC BODY>\n" + tag
        return m.group(0)
    cmd = re.sub(r"([^\n]*<<-?\s*['\"]?(\w+)['\"]?[^\n]*)\n.*?\n(\2)[ \t]*(?=\n|$)",
                 repl, cmd, flags=re.S)
    cmd = re.sub(r"(@['\"]\n).*?(\n['\"]@)", r"\1<HERESTRING BODY>\2", cmd, flags=re.S)
    return cmd


def load_grant():
    try:
        with open(GRANT, encoding="utf-8") as fh:
            g = json.load(fh)
    except (OSError, ValueError):
        return None
    return g if grant_valid(g) else None


def grant_valid(g):
    if not isinstance(g, dict) or g.get("used"):
        return False
    try:
        if float(g.get("expires_at") or 0) < time.time():
            return False
    except (TypeError, ValueError):
        return False
    return bool(g.get("target") and g.get("ack1") and g.get("ack2") and g.get("ask"))


def consume_grant(g):
    g["used"] = True
    g["used_at"] = time.strftime("%Y-%m-%d %H:%M")
    try:
        with open(GRANT, "w", encoding="utf-8") as fh:
            json.dump(g, fh, indent=2)
    except OSError:
        pass


def grant_covers(g, text):
    if not grant_valid(g):
        return False
    return _norm(g["target"]) in _norm(text).replace("\n", " ") or \
        _norm(g["target"]) in text.replace("\\", "/").lower()


def scan_text(text):
    """The first deletion shape in a script body, or None."""
    for pat in CODE:
        m = re.search(pat, text)
        if m:
            return m.group(0).strip()
    for pat in SCRIPT_VERBS:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(0).strip()
    return None


_SCRIPT_TOK = re.compile(r"\"([^\"]+)\"|'([^']+)'|(\|\||&&|[|;&()])|([^\s\"'|;&<>()]+)")
_RUNNERS = re.compile(r"^(python[\d.]*|py|pythonw|pwsh|powershell(\.exe)?|bash|sh|zsh|"
                      r"node|deno|bun|ruby|perl|godot\S*|cmd(\.exe)?|call|&|\.|source|exec|"
                      r"start|nohup|time|timeout|xvfb-run|uv|poetry|pipx)$", re.I)


def executed_scripts(cmd, cwd):
    """Existing script files the command EXECUTES: a script token (quoted
    or not, variables expanded) that starts a command, follows a separator,
    or follows an interpreter / runner word (flags in between allowed).
    Naming a script to grep, cat or diff it is reading, not running."""
    toks = []
    for m in _SCRIPT_TOK.finditer(cmd):
        if m.group(3):
            toks.append(("sep", m.group(3)))
        else:
            toks.append(("tok", m.group(1) or m.group(2) or m.group(4) or ""))
    out = []
    for i, (kind, tok) in enumerate(toks):
        if kind != "tok" or not tok.lower().endswith(SCRIPT_EXT):
            continue
        # The segment this token sits in (back to the last separator): it
        # runs if it starts the segment, or any earlier word in the segment
        # is a runner (python -u -X dev x.py; timeout 30 python x.py).
        j = i - 1
        seg = []
        while j >= 0 and toks[j][0] == "tok":
            seg.append(toks[j][1])
            j -= 1
        runs = (not seg or any(_RUNNERS.match(w) for w in seg)
                or tok.startswith(("./", ".\\")))
        if not runs:
            continue
        p = os.path.expandvars(os.path.expanduser(tok))
        if not os.path.isabs(p):
            p = os.path.join(cwd or ROOT, p)
        p = os.path.normpath(p)
        if os.path.isfile(p) and p not in out:
            out.append(p)
    return out


def _git(args):
    try:
        r = subprocess.run(["git", "-C", ROOT] + args, capture_output=True, timeout=10)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except Exception:
        return 1, ""


def script_body_to_scan(path):
    """What of a script to scan before it runs: the whole file when git does
    not track it (a throwaway, whatever wrote it); only the uncommitted ADDED
    lines when it does (a committed script was reviewed; its own temp-file
    cleanup is not new)."""
    root = ROOT.replace("\\", "/").lower().rstrip("/")
    ap = os.path.abspath(path).replace("\\", "/")
    rel = ap[len(root) + 1:] if ap.lower().startswith(root + "/") else None
    if rel is not None:
        code, _ = _git(["ls-files", "--error-unmatch", rel])
        if code == 0:
            _, diff = _git(["diff", "HEAD", "--", rel])
            return "\n".join(ln[1:] for ln in diff.splitlines()
                             if ln.startswith("+") and not ln.startswith("+++"))
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(400_000)
    except OSError:
        return ""


def executed_script_reason(cmd, cwd, grant, consume):
    """Deny reason if the command executes a script that deletes, else None."""
    for sp in executed_scripts(cmd, cwd):
        found = scan_text(script_body_to_scan(sp))
        if not found:
            continue
        if grant and grant_covers(grant, sp):
            if consume:
                consume_grant(grant)
            return None
        return (LAW + "This command runs %s, and that script carries a deletion "
                "shape (%s) that no commit has reviewed. A script written to Temp "
                "and run later is the shape that emptied a repository in the "
                "public report of 2026-09-20. Take the deletion out (retire or "
                "move instead), commit a reviewed version, or ask the CEO twice "
                "and record a grant naming this script, then retry once."
                % (os.path.basename(sp), found))
    return None


def crude_reason(tool, tin):
    """The fail-CLOSED fallback when evaluate() itself crashes: a plain
    substring look for the obvious verbs. Never fail open on a guard bug."""
    text = " ".join(str(v) for v in (tin or {}).values()).lower()
    if tool in SHELL_TOOLS or tool in WRITE_TOOLS:
        for needle in ("rm " + "-r", "rmdir", "remove" + "-item", "rmtree", ".unlink(",
                       "os.remove", "del /", "rd " + "/s", "reset --hard", "git " + "clean",
                       "robocopy", "rsync", "-delete", "filter-branch", "--force"):
            if needle in text:
                return (LAW + "The guard hit an internal error and fell back to a "
                        "crude check, which saw %r. Fix the guard (python tools/hooks/"
                        "preserve_guard.py --selftest) before retrying." % needle)
    return None


def evaluate(data, grant=None, consume=True):
    """-> None (allow) or the deny reason. Pure apart from consume_grant."""
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    if tool in SHELL_TOOLS:
        cmd = tin.get("command") or ""
        if not cmd:
            return None
        scan = strip_write_heredocs(cmd)
        hit = None
        paths = []
        for pat in VERBS:
            m = re.search(pat, scan, flags=re.I)
            if m:
                hit = "`%s`" % m.group("verb")
                seg = scan[m.start("verb"):]
                seg = re.split(r"[|;&\n]", seg, maxsplit=1)[0]
                paths = [_norm(t) for t in re.findall(r"\"[^\"]+\"|'[^']+'|\S+", seg)[1:]
                         if not t.startswith("-") and not t.startswith("/")
                         or re.match(r"/[\w.]", t)]
                break
        if not hit:
            for pat, what in GIT:
                m = re.search(pat, scan, flags=re.I)
                if m:
                    hit = "`git ... %s` (%s)" % (m.group("verb"), what)
                    break
        if not hit:
            for pat in CODE:
                m = re.search(pat, scan)
                if m:
                    hit = "a deletion call (%s)" % m.group(0).strip()
                    break
        if not hit:
            return executed_script_reason(cmd, data.get("cwd"), grant, consume)
        nv = never_reason(paths)
        if nv:
            return (LAW + "This command targets %s - no grant covers that shape. "
                    "It will not run." % nv)
        sr = scratch_root()
        if paths and all(p.startswith(sr + "/") for p in paths):
            return None  # the session's own scratch junk
        if grant and grant_covers(grant, cmd):
            if consume:
                consume_grant(grant)
            return None
        return (LAW + "This command runs %s. %s" % (hit, HOW))
    if tool in WRITE_TOOLS:
        target = tin.get("file_path") or tin.get("notebook_path") or "?"
        if target.lower().endswith(PROSE_EXT):
            return None  # prose cannot run; the law is about scripts
        if tool == "Write":
            texts = [tin.get("content") or ""]
        elif tool == "Edit":
            texts = [tin.get("new_string") or ""]
        elif tool == "MultiEdit":
            texts = [(e or {}).get("new_string") or "" for e in tin.get("edits") or []]
        else:
            texts = [tin.get("new_source") or ""]
        body = "\n".join(texts)
        if not body:
            return None
        if os.path.basename(target).lower() in ("settings.json", "settings.local.json"):
            # A harness permission RULE that names a verb (a deny-list entry
            # for the remove verb on a root) is a lock, not deletion code;
            # the format guard keeps the wiring honest. Only the rule
            # strings are dropped - anything else in the file is scanned.
            body = re.sub(r"\"(Bash|PowerShell)\([^\"]*\)\"", "\"<RULE>\"", body)
        for pat in CODE + SCRIPT_VERBS:
            m = re.search(pat, body, flags=re.I if pat in SCRIPT_VERBS else 0)
            if m:
                if grant and grant_covers(grant, target):
                    if consume:
                        consume_grant(grant)
                    return None
                return (LAW + "This write puts deletion code (%s) into %s. Scripts "
                        "never delete: retire or move instead (tools/retire.py, "
                        "tools/cold_shelf.py). A script's own temp file from the "
                        "same run is the one fair case - if that is what this is, "
                        "ask the CEO and record a grant naming this file, then "
                        "retry once." % (m.group(0).strip(), os.path.basename(target)))
        return None
    return None


def selftest():
    fails = []

    def run(tool, grant=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin}, grant=grant, consume=False)

    def check(name, cond):
        check.count += 1
        print(("ok   " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)
    check.count = 0

    sr = scratch_root()
    g = {"target": "docs/old_notes.md", "ask": "q", "ack1": "yes", "ack2": "yes",
         "expires_at": time.time() + 600}
    check("rm of a repo file is refused", run("Bash", command="rm docs/old_notes.md") is not None)
    check("rm -rf of a folder is refused", run("Bash", command="rm -rf build/") is not None)
    check("Remove-Item is refused", run("PowerShell", command="Remove-Item -Recurse docs\\x") is not None)
    check("del with a path is refused", run("PowerShell", command="del C:\\stuff\\a.txt") is not None)
    check("python del statement passes", run("Bash", command="python -c \"d={}; del d['k']\"") is None)
    check("git reset --hard is refused", run("Bash", command="git reset --hard HEAD~1") is not None)
    check("git checkout -- path is refused", run("Bash", command="git checkout -- scripts/a.gd") is not None)
    check("git restore path is refused", run("Bash", command="git restore scripts/a.gd") is not None)
    check("git restore --staged passes", run("Bash", command="git restore --staged scripts/a.gd") is None)
    check("git clean is refused", run("Bash", command="git clean -fd") is not None)
    check("git branch -D is refused", run("Bash", command="git branch -D old") is not None)
    check("git stash drop is refused", run("Bash", command="git stash drop") is not None)
    check("plain git commit passes", run("Bash", command="git commit -m \"remove the rm word from prose\"") is None)
    check("find -delete is refused", run("Bash", command="find . -name '*.pyc' -delete") is not None)
    check("xargs rm is refused", run("Bash", command="ls | xargs rm") is not None)
    check("os.remove one-liner is refused", run("Bash", command="python -c \"import os; os.remove('x')\"") is not None)
    check("scratchpad delete passes", run("Bash", command="rm -rf %s/abc/tmp.txt" % sr) is None)
    check("scratchpad plus repo path is refused",
          run("Bash", command="rm %s/a.txt docs/b.md" % sr) is not None)
    check("drive root is refused even with grant",
          "drive root" in (run("Bash", grant={**g, "target": "C:\\"}, command="rm -rf C:\\") or ""))
    check("home folder is refused even with grant",
          "home folder" in (run("Bash", grant={**g, "target": "~"}, command="rm -rf ~") or ""))
    check("dotdot climb is refused", run("Bash", command="rm -rf ../../other") is not None)
    check("grant lets the named delete through", run("Bash", grant=g, command="rm docs/old_notes.md") is None)
    check("grant does not cover another path", run("Bash", grant=g, command="rm docs/other.md") is not None)
    check("expired grant is ignored",
          run("Bash", grant={**g, "expires_at": time.time() - 1}, command="rm docs/old_notes.md") is not None)
    check("cat heredoc mentioning rm passes",
          run("Bash", command="cat > notes.md <<'EOF'\nnever run rm -rf /tmp/x\nEOF") is None)
    check("bash heredoc running rm is refused",
          run("Bash", command="bash <<'EOF'\nrm -rf docs/x\nEOF") is not None)
    check("Write with os.remove is refused",
          run("Write", file_path="tools/x.py", content="import os\nos.remove(p)\n") is not None)
    check("Write with shutil.rmtree is refused",
          run("Write", file_path="tools/x.py", content="shutil.rmtree(d)") is not None)
    check("Write with Path.unlink is refused",
          run("Write", file_path="tools/x.py", content="Path(p).unlink()") is not None)
    check("Edit adding DirAccess.remove_absolute is refused",
          run("Edit", file_path="scripts/a.gd", old_string="x", new_string="DirAccess.remove_absolute(p)") is not None)
    check("Edit with plain prose passes",
          run("Edit", file_path="docs/a.md", old_string="x", new_string="never delete; retire instead (os.remove is banned)") is None)
    check("Write with a grant naming the file passes",
          run("Write", grant={**g, "target": "tools/x.py"}, file_path="tools/x.py", content="os.remove(p)") is None)
    check("MultiEdit with rm -rf in a script is refused",
          run("MultiEdit", file_path="tools/x.sh", edits=[{"new_string": "rm -rf $DIR"}]) is not None)
    check("Read is ignored", run("Read", file_path="x") is None)
    # Split so this file never matches its own patterns.
    verbs = "Remove" + "-Item -Recurse $d, " + "rm " + "-rf $d and the rmtree call"
    check("markdown naming the verbs passes",
          run("Edit", file_path="docs/systems/tooling.md", old_string="x",
              new_string="| the guard refuses %s |" % verbs) is None)
    check("a .py naming the same verbs is still refused",
          run("Write", file_path="tools/x.py", content="# %s\n" % verbs) is not None)
    # 2026-09-20 hardening (the 48k-file public report). Literals are split
    # so this file never matches its own patterns.
    RMRF = "rm " + "-rf"
    CMDLET = "Remove" + "-Item"
    check("a bare folder name after rm dash rf is refused", run("Bash", command=RMRF + " build") is not None)
    check("rm of a bare file name is refused", run("Bash", command="rm LICENSE") is not None)
    check("rm --help passes", run("Bash", command="rm --help") is None)
    check("a pipeline into the remove cmdlet is refused",
          run("PowerShell", command="gci -Recurse Runners | " + CMDLET + " -Recurse -Force") is not None)
    check("a foreach body running the alias is refused", run("PowerShell", command="gci . | % { r" + "i $_ }") is not None)
    check("robocopy mirror switch is refused", run("PowerShell", command="robocopy C:\\src C:\\dst /M" + "IR") is not None)
    check("plain robocopy passes", run("PowerShell", command="robocopy C:\\src C:\\dst /E") is None)
    check("rsync with its delete flag is refused", run("Bash", command="rsync -a --del" + "ete src/ dst/") is not None)
    check("find exec into rm is refused", run("Bash", command="find . -name '*.pyc' -ex" + "ec rm {} \\;") is not None)
    check("git checkout . is refused", run("Bash", command="git checkout .") is not None)
    check("git checkout HEAD path is refused", run("Bash", command="git checkout HEAD scripts/a.gd") is not None)
    check("git checkout of a file is refused", run("Bash", command="git checkout scripts/a.gd") is not None)
    check("git checkout of a branch passes", run("Bash", command="git checkout main") is None)
    check("git checkout -b passes", run("Bash", command="git checkout -b feature/x") is None)
    check("git switch --discard-changes is refused", run("Bash", command="git switch --discard-changes main") is not None)
    check("force-with-lease push needs a grant", run("Bash", command="git push --for" + "ce-with-lease origin main") is not None)
    check("plain push passes", run("Bash", command="git push origin main") is None)
    check("git branch -f is refused", run("Bash", command="git branch -f main HEAD~5") is not None)
    check("git history filter is refused", run("Bash", command="git filter-" + "branch --all") is not None)
    check(".git/objects is refused even with grant",
          "a .git folder" in (run("Bash", grant={**g, "target": ".git/objects"}, command=RMRF + " .git/objects") or ""))
    check("a variable target is refused even with grant",
          "variable" in (run("Bash", grant={**g, "target": "$DIR"}, command=RMRF + ' "$DIR"') or ""))
    check("dot-slash wildcard is refused even with grant",
          "wildcard" in (run("Bash", grant={**g, "target": "./*"}, command=RMRF + " ./*") or ""))
    check("cat heredoc writing a deletion script is refused",
          run("Bash", command="cat > x.py <<'EOF'\nimport shutil\nshutil." + "rmtree(p)\nEOF") is not None)
    check("cat heredoc into prose mentioning rmtree passes",
          run("Bash", command="cat > x.md <<'EOF'\nshutil." + "rmtree(p) is banned\nEOF") is None)
    check("fs.promises.rm in a one-liner is refused",
          run("Bash", command="node -e \"require('fs').promises." + "rm('x')\"") is not None)
    check("subprocess with the rd switch in a write is refused",
          run("Write", file_path="tools/x.py", content="subprocess.run(['cmd','/c','r" + "d','/s','/q',p])") is not None)
    check("the rd switch in a .bat write is refused", run("Write", file_path="tools/x.bat", content="rd" + " /s /q build") is not None)
    # An untracked script that deletes is caught when it is RUN, whatever wrote it.
    import tempfile
    tmpd = tempfile.mkdtemp(prefix="everwood_preserve_selftest_")
    bad = os.path.join(tmpd, "remover.py")
    good = os.path.join(tmpd, "walker.py")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("import os, shutil\nfor r, d, f in os.walk(p):\n    shutil." + "rmtree(r)\n")
    with open(good, "w", encoding="utf-8") as fh:
        fh.write("import os\nfor r, d, f in os.walk(p):\n    print(r)\n")
    check("running an untracked deletion script is refused", run("Bash", command="python \"%s\"" % bad) is not None)
    check("running an untracked harmless script passes", run("Bash", command="python \"%s\"" % good) is None)
    check("grepping a deletion script is reading, not running", run("Bash", command="grep -n walk \"%s\"" % bad) is None)
    check("running it with flags in between is still refused", run("Bash", command="python -u -X dev \"%s\"" % bad) is not None)
    check("running it after && is still refused", run("Bash", command="cd x && \"%s\"" % bad) is not None)
    check("a grant naming the script lets it run", run("Bash", grant={**g, "target": bad}, command="python \"%s\"" % bad) is None)
    check("running a tracked, clean script passes", run("Bash", command="python tools/hooks/preserve_guard.py --selftest") is None)
    check("a settings.json deny RULE naming the verb passes",
          run("Edit", file_path=".claude/settings.json", old_string="x",
              new_string="\"deny\": [\"Bash(" + RMRF + " /)\", \"Bash(git push --for" + "ce:*)\"]") is None)
    check("a settings.json hook COMMAND that deletes is still refused",
          run("Edit", file_path=".claude/settings.json", old_string="x",
              new_string="\"command\": \"" + RMRF + " docs\"") is not None)
    check("the crude fallback refuses an obvious verb", crude_reason("Bash", {"command": RMRF + " docs"}) is not None)
    check("the crude fallback passes a plain command", crude_reason("Bash", {"command": "git status"}) is None)
    print("preserve_guard selftest: %d checks, %d failed" % (check.count, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    data = read_input()
    if not data.get("tool_name"):
        sys.exit(0)
    try:
        reason = evaluate(data, grant=load_grant())
    except Exception as exc:  # a guard must never crash the turn - nor fail open
        sys.stderr.write("preserve_guard: %r\n" % (exc,))
        reason = crude_reason(data.get("tool_name") or "", data.get("tool_input") or {})
    if reason:
        deny(reason)
    sys.exit(0)

"""PreToolUse guard on Bash/PowerShell/Write/Edit: THE PRESERVATION LAW.

Mazhron's ruling 2026-09-10, after public reports of an agent that wrote a
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
NEVER, grant or not: a drive root, the home folder, the repo root or its
.git, a bare wildcard. Those have no legitimate shape.

A refusal is the owner's standing decision: stop, and either move the
thing (retire / cold shelf) or ask Mazhron twice and record the grant.
`--selftest` runs the in-process checks (no harness needed).

Search keys: preservation law, delete guard, never delete, grant,
double acknowledgment, retire, cold shelf, rm guard, git reset hard.
See also: tools/delete_grant.py (the grant); tools/retire.py (files move,
never die); tools/cold_shelf.py (wiki sections); docs/systems/tooling.md
(The hooks); HOOKS_METHOD.md (portable); WIKI_METHOD.md (the cold shelf).
"""
import json
import os
import re
import sys
import time

from _hooklib import ROOT, deny, read_input

GRANT = os.path.join(ROOT, ".claude", "delete_grant.json")
LAW = ("THE PRESERVATION LAW (Mazhron's ruling 2026-09-10): nothing is "
       "deleted or discarded without the owner's express, double-acknowledged "
       "permission, and no script is written that deletes. ")
HOW = ("MOVE instead: `python tools/retire.py <path> --reason ...` (files -> "
       "_retired/, ledgered) or `python tools/cold_shelf.py --move` (wiki "
       "sections -> docs/cold/). If Mazhron has approved THIS exact deletion "
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
    r"\bos\s*\.\s*system\s*\([^)]*\b(rm|del|rmdir)\b",
    r"\bsubprocess\s*\.\s*\w+\s*\([^)]*['\"](rm|del|rmdir|remove-item)['\"]",
]
# Shell verbs that need a path-like argument (so `del d[k]` in Python
# text or `rm` as a word in prose never fires).
ARG = r"(\s+-{1,2}[\w-]+)*\s+(?P<arg>[^\s;|&]*[\\/.*~][^\s;|&]*)"
VERBS = [
    r"(^|[\s;|&(`])(?P<verb>rm|rmdir|rd|del|erase|unlink|shred|remove-item|ri|"
    r"clear-content|clc|truncate)(\.exe)?" + ARG,
    r"(^|[\s;|&(`])(?P<verb>format)\s+(?P<arg>[a-z]:)",
    r"(^|[\s;|&(`])(?P<verb>format-volume|diskpart|cipher\s+/w)",
    r"\bfind\b[^|;&\n]*\s(?P<verb>-delete)\b",
    r"\|\s*xargs\b[^|;&\n]*\s(?P<verb>rm|del|remove-item)\b",
    r"\b(?P<verb>mv|move|move-item)\b[^|;&\n]*\s(?P<arg>/dev/null|nul)\b",
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
        if p in ("", "*", "/*", "/", ".", "./", "..", "../"):
            return "a bare root or wildcard target"
        if re.fullmatch(r"[a-z]:(/\*?)?", p):
            return "a drive root"
        if p in (home, home + "/*"):
            return "the home folder"
        if p in (root, root + "/*", root + "/.git", root + "/.git/*"):
            return "the repo root or its .git"
        if p.startswith("../") or "/../" in p:
            return "a path that climbs out with .."
    return None


def strip_write_heredocs(cmd):
    """Drop heredoc / here-string BODIES that only feed a file write
    (cat/tee/Set-Content/Out-File): mentioning a verb in text is not
    running it. Bodies fed to bash/sh/python/pwsh stay and get scanned."""
    def repl(m):
        head, tag = m.group(1), m.group(3)
        if re.search(r"\b(cat|tee|set-content|out-file|add-content)\b", head, re.I):
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
                seg = scan[m.start():]
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
            return None
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
        for pat in CODE + [r"(^|[\s;|&(`])(remove-item|rm\s+-r[f]?|rmdir\s+/s|del\s+/[sq])\b"]:
            m = re.search(pat, body, flags=re.I if pat.startswith("(^|") else 0)
            if m:
                if grant and grant_covers(grant, target):
                    if consume:
                        consume_grant(grant)
                    return None
                return (LAW + "This write puts deletion code (%s) into %s. Scripts "
                        "never delete: retire or move instead (tools/retire.py, "
                        "tools/cold_shelf.py). A script's own temp file from the "
                        "same run is the one fair case - if that is what this is, "
                        "ask Mazhron and record a grant naming this file, then "
                        "retry once." % (m.group(0).strip(), os.path.basename(target)))
        return None
    return None


def selftest():
    fails = []

    def run(tool, grant=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin}, grant=grant, consume=False)

    def check(name, cond):
        print(("ok   " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

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
    print("preserve_guard selftest: %d checks, %d failed" % (35, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    data = read_input()
    if not data.get("tool_name"):
        sys.exit(0)
    try:
        reason = evaluate(data, grant=load_grant())
    except Exception as exc:  # a guard must never crash the turn
        reason = None
        sys.stderr.write("preserve_guard: %r\n" % (exc,))
    if reason:
        deny(reason)
    sys.exit(0)

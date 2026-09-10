"""THE DIET GUARD (PreToolUse on Read|Bash|PowerShell, warn-only): the
read diet and the output diet, enforced at the cliff edge (Tier 2c,
KIT COPY (Rootstock v1.12) - the origin CEO's ruling 2026-09-10,
born in Everwood from its TOKEN_IDEAS 15 + 18).

WHY: under the budget weights, the manager's context is written at 1.25x
(2x on the 1-hour cache) and re-read on every later turn; tool RESULTS are
the bulk of what gets written. Two habits leak the most:
  1. A whole-file read of something big (idea 15). A 24k-token file read
     inline costs ~30k weighted to write and rides in the box for the rest
     of the session. The same file section-read costs 2-4k; understood by
     an employee it comes back as a 2k summary.
  2. A chatty shell command with no limiter (idea 18): git log without a
     count, a bare git diff, a recursive listing, a noisy install. The
     result is context nobody asked for.
The harness knows the file size and the command BEFORE the call runs, so
this hook says so at the moment of the decision - the guard rail at the
cliff edge, never a command to type. It NEVER refuses: the manager may
have a reason (editing needs exact text). It says the number and the
cheaper move; the daily line in the usage sheet reports the outcome.

WHAT IT SAYS:
  READ DIET: <file> is ~Nk tokens (L lines, S '## ' sections) - whole read.
    Section-read it (Grep "^## " then offset/limit, or sed -n A,Bp) or, if
    this is an understand-this step, delegate the reading to an employee.
  OUTPUT DIET: <shape> - add a limiter (| head -n, -n N, --stat, -q ...).
Shell shapes are warned at most WARN_CAP times per session per shape so a
deliberate choice is not nagged; the big-read warning fires every time,
because every big read is a fresh decision.

Search keys: diet guard, read diet, output diet, big read, whole-file read,
chatty command, limiter, pretooluse warn, 10k rule.
See also: fanout_guard.py (the same warn shape); WIKI_METHOD.md (the read
diet + the output diet laws); reference tools/usage_report.py (the daily
line that grades the outcome); HOOKS_METHOD.md Tier 2c.
"""
import json
import os
import re
import sys
import time

from _hooklib import ROOT, emit, read_input

BIG_READ_TOK = 10_000         # the 10k rule (TOKEN_IDEAS 15)
BYTES_PER_TOK = 4
WARN_CAP = 3                  # shell-shape warnings per session per shape
STATE = os.path.join(ROOT, ".claude", "diet_state.json")  # gitignored
KEEP_SESSIONS = 20

# Shell reads: cat / type / Get-Content / gc <path> with no section limiter.
_SHELL_READ = re.compile(r"(^|[\s;|&(])(cat|type|get-content|gc)\s+((?:-\S+\s+)*)([^\s;|&]+)", re.I)
_LIMITED = re.compile(r"(^|[\s;|&(])(sed\s+-n|head\b|tail\b|awk\b)|-totalcount|-tail\b|select-object\s+-(first|last)|select\s+-(first|last)|\|\s*(wc|grep|findstr|select-string|sort|uniq|cut)\b", re.I)

# Chatty shell shapes (idea 18): (name, trigger regex, ok-if regex, hint).
SHAPES = [
    ("git log without a count",
     r"\bgit\s+log\b", r"\s-n\s*\d|\s-\d+\b|--max-count|\|\s*(head|tail|wc|grep|findstr)\b|--oneline\s+[^|]*-\d|-\d+\s|\s\S+\.\.\S+",
     "add -n 20 (or --oneline -n) so the result is a screen, not a history"),
    ("bare git diff",
     r"\bgit\s+diff\b(?![^|;&]*(\s--stat|\s--name-only|\s--name-status|\s--\s|\s[\w./\\-]+\.\w{1,5}\b))", r"\|\s*(head|tail|wc|grep|findstr)\b",
     "name a path, or --stat first; a whole-tree diff is the biggest tool result there is"),
    ("recursive listing without a limiter",
     r"(\bls\s+[^|;&]*-\w*R|\bfind\s+[^|;&]*(-name|-type|\.)|get-childitem[^|;&]*-recurse|\bgci\b[^|;&]*-recurse|\btree\b)",
     r"-maxdepth\s*\d|-depth\s*\d|\|\s*(head|tail|wc|grep|findstr|select-object|measure)\b|-name\s+\S|-filter\s+\S|-include\s+\S",
     "use Glob/Grep, or add -maxdepth / a name filter / | head"),
    ("noisy install",
     r"\b(pip|pip3|python\s+-m\s+pip)\s+install\b|\bnpm\s+(install|i|ci)\b",
     r"\s-q\b|--quiet|--silent|\|\s*tail\b|>\s*\S",
     "add -q (pip) or --silent (npm); the install log is re-read every turn afterward"),
]


def _load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def _save(state):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        sessions = state.setdefault("sessions", {})
        if len(sessions) > KEEP_SESSIONS:
            for sid in sorted(sessions, key=lambda k: sessions[k].get("t", 0))[:-KEEP_SESSIONS]:
                del sessions[sid]
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except OSError:
        pass


def _ktok(n):
    return "~%dk" % round(n / 1000.0) if n >= 1000 else str(n)


def file_size_info(path, cwd):
    """-> (est_tokens, lines, sections) or None when unreadable."""
    if not path:
        return None
    p = os.path.expanduser(path.strip("\"'"))
    if not os.path.isabs(p):
        p = os.path.join(cwd or ROOT, p)
    try:
        size = os.path.getsize(p)
        if size < BIG_READ_TOK * BYTES_PER_TOK:
            return (size // BYTES_PER_TOK, None, None)
        lines = sections = 0
        with open(p, "rb") as fh:
            for ln in fh:
                lines += 1
                if ln.startswith(b"## "):
                    sections += 1
        return (size // BYTES_PER_TOK, lines, sections)
    except OSError:
        return None


def _read_hint(name, est, lines, sections):
    move = ("Grep \"^## \" it first (%d sections) and read one with offset/limit" % sections
            if sections else "read it with offset/limit (sed -n A,Bp) in slices")
    return ("READ DIET: %s is %s tokens (%s lines) - a WHOLE read writes that into the "
            "context at 1.25x and re-reads it every later turn. %s; if this is an "
            "understand-this step, delegate the reading to an employee and take back a "
            "summary. Editing that needs the exact text is a fair reason to proceed."
            % (name, _ktok(est), lines if lines is not None else "?", move))


def evaluate(data, state, now=None):
    """-> (message or "", state). Pure apart from the clock and the disk."""
    now = now or time.time()
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    cwd = data.get("cwd") or ROOT
    sid = data.get("session_id") or "unknown"
    s = state.setdefault("sessions", {}).setdefault(sid, {"t": now, "shapes": {}})
    s["t"] = now
    msgs = []

    if tool == "Read":
        if not (tin.get("offset") or tin.get("limit")):
            info = file_size_info(tin.get("file_path"), cwd)
            if info and info[0] >= BIG_READ_TOK:
                msgs.append(_read_hint(os.path.basename(tin.get("file_path") or "?"), *info))
    elif tool in ("Bash", "PowerShell"):
        cmd = tin.get("command") or ""
        if cmd:
            if not _LIMITED.search(cmd):
                for m in _SHELL_READ.finditer(cmd):
                    info = file_size_info(m.group(4), cwd)
                    if info and info[0] >= BIG_READ_TOK:
                        msgs.append(_read_hint(os.path.basename(m.group(4).strip("\"'")), *info))
            for name, trig, ok, hint in SHAPES:
                if re.search(trig, cmd, re.I) and not re.search(ok, cmd, re.I):
                    n = s["shapes"].get(name, 0) + 1
                    s["shapes"][name] = n
                    if n <= WARN_CAP:
                        msgs.append("OUTPUT DIET: %s - %s (tool results are written at 1.25x "
                                    "and re-read forever)%s" % (
                                        name, hint,
                                        "; last warning this session for this shape" if n == WARN_CAP else ""))
    if not msgs:
        return ("", state)
    return ("[HOOK diet_guard] " + " | ".join(msgs), state)


# ------------------------------------------------------------ selftest --
def _selftest():
    import tempfile
    fails = []

    def check(name, cond):
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            fails.append(name)

    tmp = tempfile.mkdtemp()
    big = os.path.join(tmp, "big.md")
    with open(big, "w", encoding="utf-8") as fh:
        fh.write("## Section\n" + ("x" * 79 + "\n") * 700)  # ~56k bytes -> ~14k tok
    small = os.path.join(tmp, "small.md")
    with open(small, "w", encoding="utf-8") as fh:
        fh.write("hello\n")

    def run(tool, sess="s1", state=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin, "cwd": tmp,
                         "session_id": sess}, state if state is not None else {})[0]

    check("big whole Read warns", "READ DIET" in run("Read", file_path=big))
    check("big Read with limit is silent", run("Read", file_path=big, limit=40) == "")
    check("small whole Read is silent", run("Read", file_path=small) == "")
    check("cat big file warns", "READ DIET" in run("Bash", command="cat big.md"))
    check("cat -n big file warns", "READ DIET" in run("Bash", command="cat -n big.md"))
    check("sed -n slice is silent", run("Bash", command="sed -n 1,40p big.md") == "")
    check("cat | head is silent", run("Bash", command="cat big.md | head -50") == "")
    check("Get-Content big warns", "READ DIET" in run("PowerShell", command="Get-Content big.md"))
    check("Get-Content -TotalCount silent", run("PowerShell", command="Get-Content big.md -TotalCount 20") == "")
    check("missing file is silent", run("Bash", command="cat nothere.md") == "")
    check("git log bare warns", "git log" in run("Bash", command="git log"))
    check("git log -n 5 silent", run("Bash", command="git log --oneline -n 5") == "")
    check("git log -5 silent", run("Bash", command="git log --oneline -5") == "")
    check("git log | head silent", run("Bash", command="git log | head -20") == "")
    check("bare git diff warns", "git diff" in run("Bash", command="git diff"))
    check("git diff --stat silent", run("Bash", command="git diff --stat") == "")
    check("git diff path silent", run("Bash", command="git diff tools/x.py") == "")
    check("git diff HEAD~1 -- path silent", run("Bash", command="git diff HEAD~1 -- tools") == "")
    check("find without limiter warns", "recursive" in run("Bash", command="find . -type f"))
    check("find -name silent", run("Bash", command="find . -name '*.py'") == "")
    check("ls -R warns", "recursive" in run("Bash", command="ls -R"))
    check("gci -Recurse | head silent", run("PowerShell", command="Get-ChildItem -Recurse | Select-Object -First 5") == "")
    check("pip install warns", "noisy install" in run("Bash", command="pip install openpyxl"))
    check("pip install -q silent", run("Bash", command="pip install -q openpyxl") == "")
    st = {}
    for _ in range(WARN_CAP + 2):
        last = run("Bash", sess="cap", state=st, command="git log")
    check("shape warning capped per session", last == "" and st["sessions"]["cap"]["shapes"]["git log without a count"] == WARN_CAP + 2)
    check("read warning never capped", all("READ DIET" in run("Bash", sess="cap", state=st, command="cat big.md") for _ in range(WARN_CAP + 1)))
    check("junk input is silent", evaluate({}, {})[0] == "")
    print("diet_guard selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    data = read_input()
    if not data.get("tool_name"):
        return
    state = _load()
    try:
        msg, state = evaluate(data, state)
    except Exception as e:  # a guard must never crash the turn
        msg = ""
        state.setdefault("errors", []).append(str(e)[:200])
        state["errors"] = state["errors"][-5:]
    _save(state)
    if msg:
        emit({"systemMessage": msg,
              "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "additionalContext": msg}})


if __name__ == "__main__":
    main()

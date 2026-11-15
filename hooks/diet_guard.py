"""THE DIET GUARD (PreToolUse on Read|Bash|PowerShell|Write|Edit|MultiEdit|
Grep|mcp__.*; refuses ONCE per big whole read, warns on everything else): the read diet and the output diet,
enforced at the cliff edge (Tier 2c, the CEO's ruling 2026-09-10 -
TOKEN_IDEAS 15 + 18; INDEX FIRST 2026-09-10 PM, TOKEN_IDEAS 21).

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
cliff edge, never a command to type. It refuses exactly ONCE: the first
whole read of a big file in a session comes back as the file's own index
(INDEX FIRST, below); the same call repeated passes with a warning,
because the manager may have a reason (editing needs exact text).
Everything else is warn-only. It says the number and the cheaper move;
the daily line in the usage sheet reports the outcome.

WHAT IT SAYS:
  READ DIET: <file> is ~Nk tokens (L lines, S '## ' sections) - whole read.
    Section-read it (Grep "^## " then offset/limit, or sed -n A,Bp) or, if
    this is an understand-this step, delegate the reading to an employee.
  OUTPUT DIET: <shape> - add a limiter (| head -n, -n N, --stat, -q ...).
  TRIP DIET: N <shape> calls on new targets (<targets>) - the rest of
    this trip is one script run once that prints a verdict (the third
    same-shaped call on a new target inside the last TRIP_WINDOW counted
    calls, so a read-then-edit trip that alternates two shapes still
    shows; once per shape per session; warn-only). v1.62: with
    trip_diet_refuse = true in the modes file that third call is refused
    ONCE instead and the same call repeated passes; every note is graded
    in docs/history/trip_diet_runs.txt (HEEDED, WALKED, MOVED-ON) and
    `--trips` prints the tally; a run of one MCP tool is counted there
    as MCP-RUN and says nothing (a shell script cannot reach an MCP tool).
  RE-READ (diet guard): <file> is unchanged since its whole read this
    session and already in context - denied once per fingerprint (the file
    changing resets it); the next identical call passes with a warning,
    the same repeat-passes mechanism as INDEX FIRST.
  BIG WRITE (kit v1.57, warn-only, PreToolUse on Write): <file> is ~Nk
    tokens of manager output, written at 5x - a generated or mechanical
    file is employee or script work (the origin's measure: two single
    Writes of install scripts cost 28.6k output tokens, ~143k weighted).
    Off with big_write_warn = false in .claude/rootstock_modes.json.
Shell shapes are warned at most WARN_CAP times per session per shape so a
deliberate choice is not nagged; the big-read warning fires every time,
because every big read is a fresh decision.

PURPOSE: PreToolUse guard on Read, Bash and PowerShell enforcing the read
  diet and output diet: warns when a shell command shape (git log, git diff,
  recursive listing, install) has no limiter, and on the first whole read of
  a file over about 10k tokens in a session it denies once and returns the
  file's own section or function index instead; the same call repeated
  afterward passes with a warning only; a LATER whole read of that same
  file in the same session, fingerprint (mtime_ns+size) unchanged since the
  admitted read, is denied once more as RE-READ and passes on repeat;
  forget_session_reads() clears a session's RE-READ marks (not its INDEX
  FIRST marks) after a compaction empties the context; on Write (v1.57) it
  warns once per file per session when the content is past about 4k tokens
  of manager output, naming the employee or script route; on the third
  same-shaped call on a new target within the last six counted calls
  (Edit, MultiEdit, Write, Read by file; Bash, PowerShell by verb; Grep by
  pattern, one place per call) it notes TRIP DIET once per shape per
  session (2026-11-03, code mode): the rest of the trip as one script run
  once; with trip_diet_refuse = true (v1.62, off by default) that call is
  denied once instead and passes on repeat; it appends one line per note
  and per outcome (HEEDED, WALKED, MOVED-ON), and one MCP-RUN line per
  silent run of a single MCP tool, to docs/history/trip_diet_runs.txt;
  `--trips` prints that ledger's tally and writes nothing.
INTENT: section or split ... should not require my approval ... part of the
  looping scripts

Search keys: diet guard, read diet, output diet, big read, whole-file read,
chatty command, limiter, pretooluse warn, 10k rule, re-read, RE-READ,
fingerprint, admitted read, forget_session_reads, big write, BIG WRITE,
manager output, 5x, trip diet, TRIP DIET, one-script trip, code mode,
programmatic tool calling, same-shaped calls, trip window, interleaved
trip, trip_diet_refuse, refuse once, trip_diet_runs, HEEDED, WALKED,
MOVED-ON, MCP-RUN, --trips, trip tally.
See also: tools/hooks/fanout_guard.py (the same warn shape); TOKEN_IDEAS.md
ideas 15-18; WIKI_METHOD.md (the read diet + the output diet laws);
tools/usage_report.py (the daily line that grades the outcome);
docs/systems/tooling.md (The hooks); tools/hooks/pre_compact.py (calls
forget_session_reads() so the RE-READ marks don't outlive a compaction);
docs/history/trip_diet_runs.txt (the trip diet's outcome ledger).
"""
import json
import os
import re
import sys
import time

from _hooklib import ROOT, emit, mode, read_input

BIG_READ_TOK = 10_000         # the 10k rule (TOKEN_IDEAS 15)
BIG_WRITE_TOK = 4_000         # THE BIG WRITE (v1.57): content past this is a 5x output question
BYTES_PER_TOK = 4
WARN_CAP = 3                  # shell-shape warnings per session per shape
TRIP_N = 3                    # THE TRIP DIET (2026-11-03): same-shaped calls on new targets before the note
TRIP_WINDOW = 6               # v1.62: counted calls kept in view, so two shapes alternating (read, edit, read, edit) still show
TRIP_FOLLOW = 4               # v1.62: counted calls after a note before it is graded MOVED-ON
TRIP_LEDGER = os.path.join(ROOT, "docs", "history", "trip_diet_runs.txt")
TRIP_HEAD = ("# the trip diet's notes and outcomes: date time | event | shape | n | targets | session "
             "(NOTE or REFUSED, then HEEDED = a script followed, WALKED = the same shape went on, "
             "MOVED-ON = neither within %d calls; MCP-RUN = a silent count)" % TRIP_FOLLOW)
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


def forget_session_reads(session_id, state=None):
    """Compaction empties the manager's context, so a file's RE-READ marks
    must go with it - it is no longer "already in context." Clears this
    session's admitted-read fingerprints and RE-READ-offered flags; leaves
    INDEX FIRST's own per-file marks alone (those track "the index was
    already served," which stays true across a compaction). State
    bookkeeping only - no file is touched, nothing is deleted from disk.

    With no `state` given, operates on the real on-disk STATE (the normal
    call from pre_compact.py: load, clear, save). A `state` dict may be
    passed directly (tests, or a caller already holding one) and is
    mutated in place with no disk I/O."""
    owns = state is None
    if owns:
        state = _load()
    sess = state.get("sessions", {}).get(session_id)
    if sess:
        sess.pop("admitted_reads", None)
        sess.pop("reread_offered", None)
    if owns:
        _save(state)
    return state


def _ktok(n):
    return "~%dk" % round(n / 1000.0) if n >= 1000 else str(n)


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")  # priced by pixels, not bytes
INDEX_CAP = 80                # index entries served at most
_CODE_HEAD = re.compile(rb"^\s*(static\s+func|func|class_name|class|def|async\s+def|signal)\b")


def _resolve(path, cwd):
    p = os.path.expanduser((path or "").strip("\"'"))
    if p and not os.path.isabs(p):
        p = os.path.join(cwd or ROOT, p)
    return p


def file_size_info(path, cwd):
    """-> (est_tokens, lines, sections) or None when unreadable or an image."""
    if not path:
        return None
    p = _resolve(path, cwd)
    if p.lower().endswith(IMAGE_EXT):
        return None  # ~1-2k tokens however big the file is
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


def file_index(path, cwd):
    """-> ["<line>: <heading or signature>", ...] - the file's own table of
    contents: `## ` headings for markdown, func/class/def lines for code.
    Empty when the file has no such structure (a log, a dump)."""
    p = _resolve(path, cwd)
    md = p.lower().endswith((".md", ".markdown", ".txt"))
    out = []
    try:
        with open(p, "rb") as fh:
            for i, ln in enumerate(fh, 1):
                if md:
                    hit = ln.startswith(b"## ")
                else:
                    hit = bool(_CODE_HEAD.match(ln))
                if hit:
                    text = ln.decode("utf-8", "replace").strip()
                    if len(text) > 72:
                        text = text[:69] + "..."
                    out.append("%d: %s" % (i, text))
                    if len(out) >= INDEX_CAP:
                        out.append("... (capped at %d entries)" % INDEX_CAP)
                        break
    except OSError:
        return []
    return out


def _read_hint(name, est, lines, sections):
    move = ("Grep \"^## \" it first (%d sections) and read one with offset/limit" % sections
            if sections else "read it with offset/limit (sed -n A,Bp) in slices")
    return ("READ DIET: %s is %s tokens (%s lines) - a WHOLE read writes that into the "
            "context at 1.25x and re-reads it every later turn. %s; if this is an "
            "understand-this step, delegate the reading to an employee and take back a "
            "summary. Editing that needs the exact text is a fair reason to proceed."
            % (name, _ktok(est), lines if lines is not None else "?", move))


def _fingerprint(path):
    """<mtime_ns>:<size> for the RE-READ check - changes whenever the file's
    content could have changed; None when it can't be stat'd (gone, no
    permission)."""
    try:
        st = os.stat(path)
        return "%d:%d" % (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _reread_msg(name, est):
    """RE-READ (the CEO's Rootstock take, 2026-09-30): a later whole read of
    a file this session already read whole and unchanged since - denied
    once, same repeat-passes mechanism as INDEX FIRST."""
    return ("RE-READ (diet guard): %s is unchanged since its whole read this session and "
            "is already in context (%s tokens). Grep the section you need, or Read with "
            "offset/limit. If the context was compacted since, repeat the call once and it "
            "passes." % (name, _ktok(est)))


def _index_first(name, est, lines, index):
    """INDEX FIRST (the CEO 2026-09-10, "section or split ... should not require
    my approval ... part of the looping scripts"): the first whole read of a
    big file in a session is answered with the file's own index instead of
    the file - ~1-3% of the tokens - and the same call repeated passes."""
    return ("INDEX FIRST (diet guard): %s is %s tokens (%s lines); here is its index "
            "(line: heading) so you can read ONE section with offset/limit or sed -n "
            "A,Bp instead of the whole file:\n  %s\nIf you truly need the whole file "
            "(editing that needs the exact text), repeat the same call - the second "
            "attempt passes with a warning only."
            % (name, _ktok(est), lines if lines is not None else "?", "\n  ".join(index)))


_SCRIPTY = re.compile(r"<<\s*['\"]?\w+|python3?\s+-c?\s|\bpython3?\s+\S+\.py\b", re.I)
_LEAD_CD = re.compile(r"^\s*(?:cd\s+(?:\"[^\"]*\"|'[^']*'|\S+)\s*(?:&&|;)\s*)+", re.I)


def _trip_shape(tool, tin):
    """THE TRIP DIET's eye (2026-11-03; v1.62 adds MultiEdit as an Edit,
    Grep by pattern and MCP tools by name): -> (shape, target) for a call that
    can be one step of a trip, ("", "") for a call that is not counted, and
    (None, "") for a shell call that is itself a script - a heredoc, a
    `python -`, a .py run, three or more chained steps - which resets the
    run because it IS the move the note asks for."""
    if tool in ("Edit", "MultiEdit", "Write", "Read"):
        p = tin.get("file_path") or ""
        shape = "Edit" if tool == "MultiEdit" else tool
        return (shape, os.path.basename(p.strip("\"'")).lower()) if p else ("", "")
    if tool == "Grep":
        # v1.62: the same question asked of a new place is a trip step; a
        # new pattern is a new question (an investigation) and a search
        # with no place named is one call already - neither is counted.
        pat = (tin.get("pattern") or "").strip()
        where = ("%s %s" % (tin.get("path") or "", tin.get("glob") or "")).strip()
        if not pat or not where:
            return ("", "")
        return ("Grep /%s/" % pat[:40], where.replace("\\", "/").lower())
    if tool.startswith("mcp__"):
        # v1.62: counted, never noted - a shell script cannot reach an MCP
        # tool, so the ledger's MCP-RUN lines only answer "do MCP trips
        # happen here" before anyone builds a door for them.
        try:
            target = json.dumps(tin, sort_keys=True, default=str)
        except Exception:
            target = str(tin)
        return ("mcp " + tool[5:], target[:200])
    if tool in ("Bash", "PowerShell"):
        cmd = (tin.get("command") or "").strip()
        if not cmd:
            return ("", "")
        if _SCRIPTY.search(cmd) or len(re.split(r"&&|;|\|\||\n", cmd)) >= 3:
            return (None, "")
        body = _LEAD_CD.sub("", cmd)
        m = re.match(r"\S+", body)
        if not m:
            return ("", "")
        verb = m.group(0).lower().rsplit("/", 1)[-1]
        if verb in ("cd", "echo", "pwd", "ls", "dir"):
            return ("", "")
        return ("shell " + verb, body)
    return ("", "")


def _trip_line(now, word, shape, n, names, sid):
    """One trip-ledger line; a pipe or a newline inside a field would break the columns."""
    def clean(x):
        return str(x).replace("|", "/").replace("\r", " ").replace("\n", " ")[:160]
    return "%s | %s | %s | %s | %s | %s" % (
        time.strftime("%Y-%m-%d %H:%M", time.localtime(now)), word, clean(shape), n, clean(names),
        clean(sid)[:8])


def _flush_trips(state, path=None):
    """Append the events evaluate() queued to the trip ledger (header on first
    write) and take them off the state so they are never saved or written twice."""
    events = state.pop("_trip_events", None)
    if not events:
        return 0
    path = path or TRIP_LEDGER
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            if new:
                fh.write(TRIP_HEAD + "\n")
            fh.write("\n".join(events) + "\n")
    except OSError:
        return 0
    return len(events)


def trip_tally(path=None):
    """-> ({event: count}, first date) read from the trip ledger; no writes."""
    counts, first = {}, ""
    try:
        with open(path or TRIP_LEDGER, encoding="utf-8") as fh:
            for ln in fh:
                parts = [p.strip() for p in ln.split(" | ")]
                if ln.startswith("#") or len(parts) < 3:
                    continue
                first = first or parts[0][:10]
                counts[parts[1]] = counts.get(parts[1], 0) + 1
    except OSError:
        pass
    return counts, first


def trip_tally_line(path=None):
    """The one line the usage sheet and `--trips` print: was the note heeded?"""
    c, first = trip_tally(path)
    notes = c.get("NOTE", 0) + c.get("REFUSED", 0)
    if not notes and not c.get("MCP-RUN"):
        return "TRIP DIET: no note recorded yet (docs/history/trip_diet_runs.txt)"
    graded = c.get("HEEDED", 0) + c.get("WALKED", 0) + c.get("MOVED-ON", 0)
    return ("TRIP DIET since %s: %d notes (%d of them refusals) | heeded %d (a script followed) | "
            "walked on %d | moved on %d | ungraded %d | MCP runs %d (silent)" % (
                first or "?", notes, c.get("REFUSED", 0), c.get("HEEDED", 0), c.get("WALKED", 0),
                c.get("MOVED-ON", 0), max(0, notes - graded), c.get("MCP-RUN", 0)))


def evaluate(data, state, now=None):
    """-> (message or "", state, action). action is "" or "deny" (the
    index-first refusal). Pure apart from the clock and the disk."""
    now = now or time.time()
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    cwd = data.get("cwd") or ROOT
    sid = data.get("session_id") or "unknown"
    s = state.setdefault("sessions", {}).setdefault(sid, {"t": now, "shapes": {}})
    s["t"] = now
    offered = s.setdefault("offered", {})
    admitted = s.setdefault("admitted_reads", {})      # key -> fingerprint at admission
    reread_offered = s.setdefault("reread_offered", {})  # key -> RE-READ already denied once
    msgs = []
    action = ""

    def small_repeat(raw_path, info):
        """THE SESSION READ SET (the trial workflow, the CEO 2026-10-30): a
        whole read of a small file is remembered by fingerprint; a later whole
        read of the same file, unchanged since, gets ONE note (never a
        refusal) - it is already in context. Compaction clears the set
        (pre_compact.py forget_session_reads), so a post-compaction read is
        silent. Yesterday's budget line counted 105 small whole reads against
        26 section reads; this is the measure's hook end."""
        resolved = _resolve(raw_path, cwd)
        key = resolved.replace("\\", "/").lower()
        fp = _fingerprint(resolved)
        if fp is None:
            return None
        prev = admitted.get(key)
        if prev is None or prev != fp:
            admitted[key] = fp
            reread_offered.pop(key, None)
            return None
        if key in reread_offered:
            return None
        reread_offered[key] = now
        name = os.path.basename(raw_path.strip("\"'"))
        return ("", "RE-READ (small): %s is unchanged since its whole read this session (~%s "
                    "tokens) and is already in context; Grep the section or Read with "
                    "offset/limit (if the context was compacted since, read on - this note "
                    "is once per file per session)" % (name, _ktok(info[0])))

    def whole_read(raw_path):
        """One big whole read: the first per file per session is denied with
        the index (INDEX FIRST); the next admitted read of the same file
        records its fingerprint; a LATER read of that file, unchanged since,
        is denied once more (RE-READ) and passes on repeat; a changed file
        (different fingerprint) always passes and resets the mark."""
        info = file_size_info(raw_path, cwd)
        if not info:
            return None
        if info[0] < BIG_READ_TOK:
            return small_repeat(raw_path, info)
        name = os.path.basename(raw_path.strip("\"'"))
        resolved = _resolve(raw_path, cwd)
        key = resolved.replace("\\", "/").lower()
        if key not in offered:
            index = file_index(raw_path, cwd)
            if index:
                offered[key] = now
                return ("deny", _index_first(name, info[0], info[1], index))
            return ("", _read_hint(name, *info))
        fp = _fingerprint(resolved)
        if fp is not None:
            prev = admitted.get(key)
            if prev is None:
                admitted[key] = fp                     # first admission: baseline it
            elif prev != fp:
                admitted[key] = fp                     # changed since - fresh baseline
                reread_offered.pop(key, None)
            elif key not in reread_offered:
                reread_offered[key] = now
                return ("deny", _reread_msg(name, info[0]))
        return ("", _read_hint(name, *info))

    if tool == "Read":
        if not (tin.get("offset") or tin.get("limit")) and tin.get("file_path"):
            r = whole_read(tin.get("file_path"))
            if r:
                action = action or r[0]
                msgs.append(r[1])
    elif tool in ("Bash", "PowerShell"):
        cmd = tin.get("command") or ""
        if cmd:
            if not _LIMITED.search(cmd):
                for m in _SHELL_READ.finditer(cmd):
                    r = whole_read(m.group(4))
                    if r:
                        action = action or r[0]
                        msgs.append(r[1])
            for name, trig, ok, hint in SHAPES:
                if re.search(trig, cmd, re.I) and not re.search(ok, cmd, re.I):
                    n = s["shapes"].get(name, 0) + 1
                    s["shapes"][name] = n
                    if n <= WARN_CAP:
                        msgs.append("OUTPUT DIET: %s - %s (tool results are written at 1.25x "
                                    "and re-read forever)%s" % (
                                        name, hint,
                                        "; last warning this session for this shape" if n == WARN_CAP else ""))
    elif tool == "Write" and mode("big_write_warn", True):
        # THE BIG WRITE (kit v1.57, the CEO's yes 2026-10-31): the manager's
        # own output is the 5x pillar; a whole generated file typed through
        # Write is the dearest way to produce it. Warn-only, once per file
        # per session; the manager proceeds when the file needs its exact text.
        content = tin.get("content") or ""
        est = len(content.encode("utf-8", "replace")) // BYTES_PER_TOK
        raw_path = tin.get("file_path") or ""
        key = "write:" + _resolve(raw_path, cwd).replace("\\", "/").lower() if raw_path else "write:?"
        if est >= BIG_WRITE_TOK and key not in offered:
            offered[key] = now
            msgs.append("BIG WRITE: %s is %s tokens of manager output (written at 5x) - a "
                        "generated or mechanical file is employee or script work (SUBAGENT_METHOD: "
                        "the cheapest tier regenerates artifacts; a script writes a document; "
                        "a patch goes as an Edit); proceed only if it needs the manager's exact "
                        "text (once per file per session)" % (os.path.basename(raw_path) or "?",
                                                              _ktok(est)))
    # THE TRIP DIET (the CEO 2026-11-03, after Code Mode / programmatic tool
    # calling: "the AI writes the whole trip as code ... runs once in a
    # sandbox ... returns only the answer"): three same-shaped calls on
    # different targets are a trip walked one tool call at a time, every
    # result written into the context at 1.25x. One note per shape per
    # session; a repeat on the same target is a retry and does not count; a
    # shell call that is itself a script clears the view.
    # v1.62 (2026-11-15): the view is the last TRIP_WINDOW counted calls, not
    # an unbroken run, because the commonest trip alternates two shapes
    # (read a, edit a, read b, edit b) and never made three in a row; a note
    # is graded by what follows it; trip_diet_refuse = true refuses that
    # third call once (the INDEX FIRST shape: the same call repeated passes).
    if tool and mode("trip_diet_warn", True):
        shape, target = _trip_shape(tool, tin)
        trip = s.get("trip")
        if not isinstance(trip, dict) or not isinstance(trip.get("win"), list):
            trip = {"win": []}                  # also retires the older {"shape", "items"} state
        s["trip"] = trip
        win = trip["win"]
        pending = trip.get("note")              # {"shape", "targets", "left"} from a note until it is graded
        events = state.setdefault("_trip_events", [])   # main() appends these to the ledger; evaluate() writes nothing

        def grade(word):
            events.append(_trip_line(now, word, pending["shape"], "", "", sid))
            trip.pop("note", None)

        if shape is None:
            if pending:
                grade("HEEDED")
            del win[:]
        elif shape:
            fresh = [shape, target] not in win
            if fresh and pending:
                if shape == pending["shape"] and target not in pending["targets"]:
                    grade("WALKED")
                else:
                    pending["left"] -= 1
                    if pending["left"] <= 0:
                        grade("MOVED-ON")
            if fresh:
                win.append([shape, target])
                del win[:-TRIP_WINDOW]
            items = [t for sh, t in win if sh == shape]
            key = "trip:" + shape
            if len(items) >= TRIP_N and key not in offered and not trip.get("note"):
                offered[key] = now
                names = ", ".join(t if len(t) <= 40 else t[:37] + "..." for t in items)
                if shape.startswith("mcp "):
                    events.append(_trip_line(now, "MCP-RUN", shape, len(items), "", sid))
                else:
                    refuse = bool(mode("trip_diet_refuse", False))
                    trip["note"] = {"shape": shape, "targets": list(items), "left": TRIP_FOLLOW}
                    events.append(_trip_line(now, "REFUSED" if refuse else "NOTE", shape, len(items), names, sid))
                    text = ("%d %s calls on new targets (%s) - the rest of this trip is "
                            "ONE script run once that prints a verdict (counts, PASS/FAIL, the "
                            "few lines needed); each call's result here is written into the "
                            "context at 1.25x and re-read forever (LESSONS.md \"The one-script "
                            "trip\"; once per shape per session)" % (len(items), shape, names))
                    if refuse:
                        action = action or "deny"
                        msgs.append("TRIP DIET (refused once): " + text + ". If one result "
                                    "decides the next, repeat the same call - it passes.")
                    else:
                        msgs.append("TRIP DIET: " + text)
    if not msgs:
        return ("", state, "")
    return ("[HOOK diet_guard] " + " | ".join(msgs), state, action)


# ------------------------------------------------------------ selftest --
def _selftest():
    import tempfile
    fails = []
    # The selftest judges the code, never this project's switches: a modes
    # file with big_write_warn or trip_diet_warn off must not fail it (v1.62).
    from _hooklib import MODES_DEFAULT
    globals()["mode"] = lambda key, default=None: MODES_DEFAULT.get(key, default)

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

    code = os.path.join(tmp, "big.gd")
    with open(code, "w", encoding="utf-8") as fh:
        fh.write("extends Node\n" + ("func f%d():\n\tpass\n" % 0) + ("#" * 79 + "\n") * 700
                 + "func last():\n\tpass\n")
    flat = os.path.join(tmp, "flat.log")
    with open(flat, "w", encoding="utf-8") as fh:
        fh.write(("x" * 79 + "\n") * 700)
    png = os.path.join(tmp, "shot.png")
    with open(png, "wb") as fh:
        fh.write(b"\x89PNG" + b"\0" * (BIG_READ_TOK * BYTES_PER_TOK))

    def run(tool, sess="s1", state=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin, "cwd": tmp,
                         "session_id": sess}, state if state is not None else {})[0]

    def act(tool, sess="s1", state=None, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin, "cwd": tmp,
                         "session_id": sess}, state if state is not None else {})[2]

    rs = {}
    s1 = evaluate({"tool_name": "Read", "tool_input": {"file_path": small}, "cwd": tmp,
                   "session_id": "rs"}, rs)
    s2 = evaluate({"tool_name": "Read", "tool_input": {"file_path": small}, "cwd": tmp,
                   "session_id": "rs"}, rs)
    s3 = evaluate({"tool_name": "Read", "tool_input": {"file_path": small}, "cwd": tmp,
                   "session_id": "rs"}, rs)
    check("first small whole Read is silent", s1[0] == "" and s1[2] == "")
    check("second identical small Read gets the RE-READ note, no deny",
          "RE-READ (small)" in s2[0] and s2[2] == "")
    check("the small RE-READ note is once per file per session", s3[0] == "")
    with open(small, "a", encoding="utf-8") as fh:
        fh.write("changed\n")
    s4 = evaluate({"tool_name": "Read", "tool_input": {"file_path": small}, "cwd": tmp,
                   "session_id": "rs"}, rs)
    check("a changed small file reads silently and re-baselines", s4[0] == "")
    forget_session_reads("rs", rs)
    s5 = evaluate({"tool_name": "Read", "tool_input": {"file_path": small}, "cwd": tmp,
                   "session_id": "rs"}, rs)
    check("compaction clears the small read set too", s5[0] == "")

    st = {}
    first = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                      "session_id": "ix"}, st)
    second = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                       "session_id": "ix"}, st)
    check("first big whole Read is INDEX FIRST (deny)", first[2] == "deny" and "INDEX FIRST" in first[0]
          and "1: ## Section" in first[0])
    check("second identical Read passes with a warning", second[2] == "" and "READ DIET" in second[0])
    check("index-first is per session", act("Read", sess="other", state=st, file_path=big) == "deny")
    check("code file index lists funcs", "func last()" in run("Read", file_path=code)
          and act("Read", file_path=code) == "deny")
    check("no-structure file warns, never denies", act("Read", file_path=flat) == ""
          and "READ DIET" in run("Read", file_path=flat))
    check("image Read is silent (pixels, not bytes)", run("Read", file_path=png) == "")
    check("big Read with limit is silent", run("Read", file_path=big, limit=40) == "")
    check("small whole Read is silent", run("Read", file_path=small) == "")
    check("cat big file is INDEX FIRST", act("Bash", command="cat big.md") == "deny")
    check("cat -n big file is INDEX FIRST", "INDEX FIRST" in run("Bash", command="cat -n big.md"))
    check("sed -n slice is silent", run("Bash", command="sed -n 1,40p big.md") == "")
    check("cat | head is silent", run("Bash", command="cat big.md | head -50") == "")
    check("Get-Content big is INDEX FIRST", "INDEX FIRST" in run("PowerShell", command="Get-Content big.md"))
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
    reads = [run("Bash", sess="cap", state=st, command="cat big.md") for _ in range(WARN_CAP + 2)]
    # never silently capped like the shape warnings are (none of these is ""):
    # INDEX FIRST once, then READ DIET, then RE-READ once (the file is
    # unchanged), then READ DIET forever after.
    check("read warning never capped", "INDEX FIRST" in reads[0] and "READ DIET" in reads[1]
          and "RE-READ" in reads[2] and all("READ DIET" in r for r in reads[3:])
          and all(r != "" for r in reads))
    check("junk input is silent", evaluate({}, {})[0] == "")

    # THE BIG WRITE (v1.57): warn-only, past BIG_WRITE_TOK, once per file per session
    bw = {}
    gen = os.path.join(tmp, "generated_install.py")
    first_w = run("Write", sess="bw", state=bw, file_path=gen, content="x" * (BIG_WRITE_TOK * 4 + 400))
    again_w = run("Write", sess="bw", state=bw, file_path=gen, content="x" * (BIG_WRITE_TOK * 4 + 400))
    check("big Write warns once with the size and the employee route",
          "BIG WRITE" in first_w and "employee or script" in first_w and again_w == ""
          and act("Write", sess="bw2", file_path=gen, content="x" * (BIG_WRITE_TOK * 4 + 400)) == "")
    check("small Write is silent", run("Write", file_path=gen, content="x" * 2000) == "")

    # RE-READ dedup: a later whole read of a file already admitted this
    # session, unchanged, is denied once more; the next passes; a changed
    # file skips it; forget_session_reads() resets the marks.
    rr = {}
    evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
              "session_id": "rr"}, rr)                          # INDEX FIRST deny
    evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
              "session_id": "rr"}, rr)                          # admitted, fp recorded
    third = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                      "session_id": "rr"}, rr)
    check("second unchanged whole read is refused with RE-READ",
          third[2] == "deny" and "RE-READ" in third[0])
    fourth = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                       "session_id": "rr"}, rr)
    check("the third whole read passes with a warning", fourth[2] == "" and "READ DIET" in fourth[0])
    check("an offset/limit read never triggers RE-READ",
          run("Read", sess="rr", state=rr, file_path=big, limit=40) == "")
    with open(big, "a", encoding="utf-8") as fh:
        fh.write("## More\n" + ("y" * 79 + "\n") * 10)          # different size -> new fingerprint
    changed = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                        "session_id": "rr"}, rr)
    check("a changed file (different fingerprint) passes",
          changed[2] == "" and "READ DIET" in changed[0])
    reread_again = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                             "session_id": "rr"}, rr)
    check("RE-READ can fire again on the new baseline",
          reread_again[2] == "deny" and "RE-READ" in reread_again[0])
    forget_session_reads("rr", rr)
    after_forget = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                             "session_id": "rr"}, rr)
    check("after forget_session_reads the next whole read is admitted again",
          after_forget[2] == "" and "READ DIET" in after_forget[0])
    diff_sess = evaluate({"tool_name": "Read", "tool_input": {"file_path": big}, "cwd": tmp,
                          "session_id": "rr-other"}, rr)
    check("a different session is unaffected by rr's RE-READ state",
          diff_sess[2] == "deny" and "INDEX FIRST" in diff_sess[0])

    # THE TRIP DIET (2026-11-03): the third same-shaped call on a new target
    # gets one note per shape per session; a retry does not count; a script
    # in between resets the run.
    td = {}
    e = [run("Edit", sess="td", state=td, file_path=n, old_string="x", new_string="y")
         for n in ("a.py", "b.py", "c.py", "d.py")]
    check("three Edits on different files get one TRIP DIET note, the fourth is silent",
          e[0] == "" and e[1] == "" and "TRIP DIET" in e[2] and "a.py, b.py, c.py" in e[2]
          and "ONE script" in e[2] and e[3] == "")
    td2 = {}
    for _ in range(TRIP_N + 1):
        same = run("Edit", sess="td2", state=td2, file_path="a.py", old_string="x", new_string="y")
    check("repeated Edits of the same file are a retry, not a trip", same == "")
    td3 = {}
    run("Edit", sess="td3", state=td3, file_path="a.py", old_string="x", new_string="y")
    run("Edit", sess="td3", state=td3, file_path="b.py", old_string="x", new_string="y")
    mid = run("Bash", sess="td3", state=td3, command="python - <<'EOF'\nprint(1)\nEOF")
    third = run("Edit", sess="td3", state=td3, file_path="c.py", old_string="x", new_string="y")
    check("a script in between resets the run and is never counted", mid == "" and third == "")
    td4 = {}
    b = [run("Bash", sess="td4", state=td4, command="sed -n %d,%dp small.md" % (i, i + 5))
         for i in (1, 10, 20)]
    check("three same-verb shell calls on new targets get the note",
          b[0] == "" and b[1] == "" and "TRIP DIET" in b[2] and "shell sed" in b[2])
    td5 = {}
    run("Edit", sess="td5", state=td5, file_path="a.py", old_string="x", new_string="y")
    run("Edit", sess="td5", state=td5, file_path="b.py", old_string="x", new_string="y")
    run("Bash", sess="td5", state=td5, command="git status --short")
    back = run("Edit", sess="td5", state=td5, file_path="c.py", old_string="x", new_string="y")
    check("a different shape in between no longer hides the trip (v1.62, the window)",
          "TRIP DIET" in back and "a.py, b.py, c.py" in back)
    td6 = {}
    chained = run("Bash", sess="td6", state=td6, command="cd x && git add -A && git commit -q -m m && git push")
    check("a chained three-step shell line is a script, not a trip step", chained == "")

    # v1.62: the window, the wider eye, the outcome ledger, the refuse switch.
    def ev(state, tool, sess, **tin):
        return evaluate({"tool_name": tool, "tool_input": tin, "cwd": tmp, "session_id": sess}, state)

    def words(state):
        return [ln.split(" | ")[1] for ln in state.get("_trip_events", [])]

    w1 = {}
    seq = []
    for n in ("a.py", "b.py", "c.py"):
        seq.append(ev(w1, "Read", "w1", file_path=n, offset=1, limit=5)[0])
        seq.append(ev(w1, "Edit", "w1", file_path=n, old_string="x", new_string="y")[0])
    check("read-then-edit across three files gets ONE note, at the third Read",
          [bool(x) for x in seq] == [False, False, False, False, True, False] and "3 Read calls" in seq[4])
    ev(w1, "Read", "w1", file_path="d.py", offset=1, limit=5)
    check("the same shape going on after a note is graded WALKED", words(w1) == ["NOTE", "WALKED"])
    w2 = {}
    for n in ("a.py", "b.py", "c.py"):
        ev(w2, "Edit", "w2", file_path=n, old_string="x", new_string="y")
    ev(w2, "Bash", "w2", command="python - <<'EOF'\nprint(1)\nEOF")
    check("a script after a note is graded HEEDED", words(w2) == ["NOTE", "HEEDED"])
    w3 = {}
    for n in ("a.py", "b.py", "c.py"):
        ev(w3, "Edit", "w3", file_path=n, old_string="x", new_string="y")
    for i in range(TRIP_FOLLOW):
        ev(w3, "Bash", "w3", command="%s --version" % ("git", "node", "pip", "gh", "npm", "go")[i])
    check("neither within TRIP_FOLLOW calls is graded MOVED-ON", words(w3) == ["NOTE", "MOVED-ON"])
    w4 = {}
    far = [ev(w4, "Edit", "w4", file_path=n, old_string="x", new_string="y")[0] for n in ("a.py", "b.py")]
    for i in range(TRIP_WINDOW):
        ev(w4, "Bash", "w4", command="%s --version" % ("git", "node", "pip", "gh", "npm", "go")[i])
    far.append(ev(w4, "Edit", "w4", file_path="c.py", old_string="x", new_string="y")[0])
    check("two Edits that left the window do not make a trip with a later third", far == ["", "", ""])
    w5 = {}
    me = [ev(w5, t, "w5", file_path=n, old_string="x", new_string="y")[0]
          for t, n in (("Edit", "a.py"), ("MultiEdit", "b.py"), ("Edit", "c.py"))]
    check("a MultiEdit counts as an Edit", "3 Edit calls" in me[2])
    w6 = {}
    g = [ev(w6, "Grep", "w6", pattern="TODO", path=p)[0] for p in ("src/a", "src/b", "src/c")]
    check("one pattern asked of three places is a trip", g[0] == "" and g[1] == "" and "Grep /TODO/" in g[2])
    w7 = {}
    g2 = [ev(w7, "Grep", "w7", pattern=p, path="src")[0] for p in ("alpha", "beta", "gamma")]
    g2 += [ev(w7, "Grep", "w7", pattern="delta")[0]]
    check("three different patterns are an investigation, never a trip", g2 == ["", "", "", ""])
    w8 = {}
    m = [ev(w8, "mcp__docs__read", "w8", id=str(i)) for i in range(3)]
    check("a run of one MCP tool is counted in the ledger and says nothing",
          all(x[0] == "" and x[2] == "" for x in m) and words(w8) == ["MCP-RUN"])
    w9 = {}
    real_mode = globals()["mode"]
    globals()["mode"] = lambda k, d=None: True if k == "trip_diet_refuse" else real_mode(k, d)
    try:
        r = [ev(w9, "Edit", "w9", file_path=n, old_string="x", new_string="y") for n in ("a.py", "b.py", "c.py")]
        again = ev(w9, "Edit", "w9", file_path="c.py", old_string="x", new_string="y")
    finally:
        globals()["mode"] = real_mode
    check("trip_diet_refuse denies the third call once and the same call repeated passes",
          r[1][2] == "" and r[2][2] == "deny" and "refused once" in r[2][0]
          and again[2] == "" and again[0] == "" and words(w9) == ["REFUSED"])
    led = os.path.join(tmp, "trip_diet_runs.txt")
    wrote = _flush_trips(w1, led) + _flush_trips(w2, led) + _flush_trips(w9, led) + _flush_trips(w8, led)
    counts, _first = trip_tally(led)
    check("the ledger takes the queued lines once and the tally reads them back",
          wrote == 6 and "_trip_events" not in w1 and _flush_trips(w1, led) == 0
          and counts == {"NOTE": 2, "WALKED": 1, "HEEDED": 1, "REFUSED": 1, "MCP-RUN": 1}
          and open(led, encoding="utf-8").readline().startswith("# the trip diet")
          and "3 notes (1 of them refusals) | heeded 1" in trip_tally_line(led)
          and "ungraded 1 | MCP runs 1" in trip_tally_line(led))
    old = {"sessions": {"w10": {"t": 1, "shapes": {}, "trip": {"shape": "Edit", "items": ["a.py", "b.py"]}}}}
    check("state saved by the older guard is read without a crash",
          ev(old, "Edit", "w10", file_path="c.py", old_string="x", new_string="y")[0] == "")

    print("diet_guard selftest: %d failed" % len(fails))
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    if "--trips" in sys.argv[1:]:
        print(trip_tally_line())
        return
    data = read_input()
    if not data.get("tool_name"):
        return
    state = _load()
    action = ""
    try:
        msg, state, action = evaluate(data, state)
    except Exception as e:  # a guard must never crash the turn
        msg = ""
        state.setdefault("errors", []).append(str(e)[:200])
        state["errors"] = state["errors"][-5:]
    _flush_trips(state)
    _save(state)
    if action == "deny":
        # INDEX FIRST, RE-READ or (trip_diet_refuse on) TRIP DIET: refused ONCE and the reason
        # carries the index or the unchanged-fingerprint notice; the same
        # call repeated passes (see _index_first, _reread_msg).
        emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "permissionDecision": "deny",
                                     "permissionDecisionReason": msg}})
    elif msg:
        emit({"systemMessage": msg,
              "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "additionalContext": msg}})


if __name__ == "__main__":
    main()

"""Stop hook: the checkpoint counter ticks itself (Tier 1, #2).

Fires when the manager finishes a reply. It ticks ONLY when work happened
(HEAD moved or the working tree's status changed since the last Stop -
tools/checkpoint.py work_fingerprint), so a Q&A reply does not inflate the
count and 8/15 keep their meaning. Manual `--tick` is retired: ticking by
hand now double-counts.

Escalation, mechanical: ADVISED (8 tasks or <80% context) shows the user
a system message; URGENT (15 tasks or <30% context) REFUSES to end the
turn once - the reason lands in the manager's context, who relays it
verbatim and recommends /checkpoint. Re-blocks every 5 further tasks;
`stop_hook_active` guards against loops.

Since 2026-09-13 it is also THE FORMAT LAW's Stop twin: a turn that
leaves a safety hook unwired in .claude/settings.json is refused once
(tools/format_lint.py's SAFETY table), so a prompt that switched a guard
off cannot end quietly.

THE CHANGELOG WARNING (the CEO's ruling 2026-09-14): if tools/
.changelog_anchor exists and HEAD has moved past it, one context line is
added to whatever this hook already emits (or, if it would otherwise emit
nothing, its own systemMessage) naming how many commits are unexported.
Warn-only, never a refusal, and never repeated for the same commit count
in a session (docs/history/checkpoint_state.txt's hook state carries the
dedup key, same file the tick counter already uses). The count skips
commits whose subject starts with "changelog:" - the export's own commit
(the exporter filters them the same way), so a fresh export is silent
(the 2026-09-28 fix: it warned "1 commit" after every export). THE
WARNING IS A STEP (the CEO 2026-09-28, correction C0003: "A Warning from
the hook means do it, not relay the message for the user to do"): the
manager runs the export inside that reply; the line is worded as an
order to the manager, never as a note for the CEO.

THE CHECKPOINT NAMED CHECK (the CEO 2026-09-28, correction C0004, after a
reply closed with "a checkpoint and clear is the natural next step
whenever you want to stop": "If this is the case, you should have just
done a checkpoint. Any reference to a checkpoint from any valid source
should prompt you to do it."): the hook reads this turn's reply text from
the transcript (every assistant text block since the last typed prompt);
if it names a checkpoint as due (the word near next / natural / due /
advised / ready / time to / should / whenever) and does not carry the
safe-to-clear marker, the turn is refused once per prompt with CHECKPOINT
NAMED, and the manager makes the checkpoint before the reply ends. A
reply that made it ends with the marker and passes; a mention of the
counter or the state file alone never trips it.

PURPOSE: Stop hook that ticks the checkpoint counter only when work actually
  happened (HEAD moved or the tree changed since the last Stop), shows an
  advised system message at 8 tasks or under 80% context, refuses to end
  the turn once at 15 tasks or under 30% context (re-blocking every 5
  further tasks), refuses once when a safety hook has gone unwired in
  settings.json, warns once per unexported commit count when the
  changelog anchor has fallen behind HEAD, and since 2026-09-28 refuses
  once per prompt when the reply names a checkpoint as due without the
  safe-to-clear marker (the reply text read from the transcript).
INTENT: makes the checkpoint discipline mechanical rather than a reminder
  the manager can forget, makes the format law's safety wiring impossible
  to quietly drop by refusing to end a turn that broke it, and makes an
  unexported changelog visible without anyone having to remember to check.

Search keys: stop hook, auto tick, checkpoint counter, dire, block stop,
safety wiring, changelog warning, changelog anchor, checkpoint named,
reply names a checkpoint.
See also: tools/checkpoint.py (counter, fingerprint, --reset);
tools/export_changelog.py (the anchor file); .claude/skills/checkpoint
(the ritual the warning asks for); tools/lesson_log.py (the transcript
reader the named check borrows).
"""
import datetime
import os
import re
import subprocess
import sys

from _hooklib import emit, read_input
import checkpoint as cp

CHANGELOG_ANCHOR = os.path.join(cp.ROOT, "tools", ".changelog_anchor")

# THE CHECKPOINT NAMED CHECK (C0004): "checkpoint" within a sentence of a
# due-word, either order; the marker a made checkpoint ends with.
_DUE = r"(next|natural|due|advised|ready|time to|should|whenever|now)"
CP_DUE_RE = re.compile(r"checkpoint[^.\n]{0,80}\b" + _DUE + r"\b|\b" + _DUE + r"\b[^.\n]{0,80}checkpoint", re.I)
CP_MARKER = "safe to /clear"


def checkpoint_named(text):
    """True when the reply names a checkpoint as due and did not make one."""
    if not text or CP_MARKER in text.lower():
        return False
    return bool(CP_DUE_RE.search(text))


def reply_text(transcript_path):
    """(this turn's reply text, index of the prompt it answers): every
    assistant text block since the last typed prompt. ("", -1) on any trouble."""
    try:
        import lesson_log as _ll
        recs, _ = _ll._records(transcript_path)
        idx = _ll.user_text_indexes(recs)
        start = idx[-1] + 1 if idx else 0
        texts = [b.get("text", "") for r in recs[start:]
                 if r.get("type") == "assistant" and not r.get("isSidechain")
                 for b in _ll._blocks(r) if b.get("type") == "text"]
        return "\n".join(texts), (idx[-1] if idx else -1)
    except Exception:  # noqa: BLE001 - a hook never crashes the turn
        return "", -1


def _commits_since_anchor(anchor_path=CHANGELOG_ANCHOR, head="HEAD"):
    """Count of UNEXPORTED commits since the changelog anchor - commits
    whose subject does not start with "changelog:" (the export's own
    commit, filtered exactly as the exporter filters it) - or None when
    there is no anchor file (a project without a changelog) or git can't
    answer. `head` is the range end (tests point it at a known commit)."""
    if not os.path.isfile(anchor_path):
        return None
    anchor = open(anchor_path, encoding="utf-8").read().strip()
    if not anchor:
        return None
    try:
        r = subprocess.run(["git", "log", "--format=%s", "%s..%s" % (anchor, head)],
                           cwd=cp.ROOT, capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return None
        return sum(1 for line in r.stdout.splitlines()
                   if line.strip() and not line.strip().lower().startswith("changelog:"))
    except Exception:
        return None


def changelog_note(mine, n_commits):
    """The warn-once-per-count changelog line, updating `mine`'s dedup key
    in place. None when there is nothing to say (no anchor, 0 commits, or
    this exact count was already warned about this session)."""
    if not n_commits:
        return None
    if mine.get("changelog_warned_n") == n_commits:
        return None
    mine["changelog_warned_n"] = n_commits
    return ("[stop_tick] CHANGELOG UNEXPORTED: %d commit(s) since the last "
            "export - MANAGER: run `python tools/export_changelog.py` and push "
            "before this reply ends (a step, never a note for the CEO; "
            "make_builds runs it itself)" % n_commits)

def main():
    data = read_input()
    if data.get("stop_hook_active"):
        sys.exit(0)

    ws = cp.which_ws()
    fp = cp.work_fingerprint()
    state = cp.load_hook_state()
    mine = dict(state.get(ws) or {})
    counts = cp.load()
    n = counts.get(ws, (0, ""))[0]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    note = changelog_note(mine, _commits_since_anchor())

    ticked = fp != mine.get("fp")
    if ticked:
        n += 1
        counts[ws] = (n, now)
        cp.save(counts)
        mine.update(fp=fp, at=now)

    level = None
    parts = []
    if n >= 15:
        level = "dire"
        parts.append("%d tasks since last checkpoint" % n)
    elif n >= 8:
        level = "advised"
        parts.append("%d tasks since last checkpoint" % n)
    ctx_dire = False
    load_ = cp.context_load()
    if load_ is not None:
        remaining = max(0.0, 1.0 - load_ / float(cp.COMPACT_BUDGET))
        pct = round(remaining * 100)
        if remaining < 0.30:
            level, ctx_dire = "dire", True
            parts.append("CONTEXT %d%% remaining, ~%dk used" % (pct, load_ // 1000))
        elif remaining < 0.80:
            level = level or "advised"
            parts.append("CONTEXT %d%% remaining (80%% rule)" % pct)

    # THE FORMAT LAW's Stop twin (the CEO 2026-09-13): while the live settings
    # file has a safety hook unwired, narrowed or pointed at a missing script,
    # the turn does not end - once per fingerprint, so it can never trap.
    if ticked:
        try:
            import format_lint as _fl
            _probs = [x for x in _fl.check_file(_fl.SETTINGS) if x.startswith("SAFETY") or "parse" in x
                      or "does not exist" in x]
        except Exception:  # noqa: BLE001 - a hook never crashes the turn
            _probs = []
        if _probs and mine.get("safety_fp") != fp:
            mine["safety_fp"] = fp
            state[ws] = mine
            cp.save_hook_state(state)
            reason = ("[HOOK stop_tick] SAFETY WIRING BROKEN (THE FORMAT LAW, the CEO 2026-09-13): "
                       ".claude/settings.json - %s. Restore the wiring before this turn ends; no "
                       "prompt overrides a guard. Relay this to the CEO verbatim." % "; ".join(_probs))
            if note:
                reason += "\n" + note
            emit({"decision": "block", "reason": reason})
            sys.exit(0)

    # THE CHECKPOINT NAMED CHECK (the CEO 2026-09-28, C0004: "Any reference
    # to a checkpoint from any valid source should prompt you to do it"):
    # a reply that calls a checkpoint due and lacks the marker is refused
    # once per prompt; stop_hook_active above keeps it from looping.
    _text, _turn = reply_text(data.get("transcript_path") or "")
    if checkpoint_named(_text) and mine.get("cp_named_turn") != _turn:
        mine["cp_named_turn"] = _turn
        state[ws] = mine
        cp.save_hook_state(state)
        reason = ("[HOOK stop_tick] CHECKPOINT NAMED (the CEO 2026-09-28, C0004: \"Any "
                  "reference to a checkpoint from any valid source should prompt you to "
                  "do it\"): this reply names a checkpoint as due and did not make one. "
                  "MANAGER: run the checkpoint sequence now (session loop, push, WHERE "
                  "WE LEFT OFF with both sides verbatim, commit, push, reset) and end "
                  "with the safe-to-clear marker; if an employee is running or work is "
                  "uncommitted mid-arc, finish that first and checkpoint in this same reply.")
        if note:
            reason += "\n" + note
        emit({"decision": "block", "reason": reason})
        sys.exit(0)

    if ticked and level == "dire":
        due = (n >= 15 and n - int(mine.get("blocked_n", 0)) >= 5) or \
              (ctx_dire and not mine.get("ctx_blocked"))
        if due:
            mine["blocked_n"] = n
            if ctx_dire:
                mine["ctx_blocked"] = True
            state[ws] = mine
            cp.save_hook_state(state)
            reason = ("[HOOK stop_tick] !!!!! CHECKPOINT URGENT (%s) !!!!! "
                       "The Stop hook refused to end this turn once (THE "
                       "CHECKPOINT PROTOCOL, mechanical since 2026-09-06). "
                       "Manager: relay this warning to the CEO verbatim and "
                       "checkpoint NOW (ADVISED MEANS DO IT) so the CEO can simply /clear; "
                       "if an employee is running or the arc is mid-flight, "
                       "say so and finish the arc first. Auto-compact is "
                       "lossy; the day file + standup are lossless."
                       % "; ".join(parts))
            if note:
                reason += "\n" + note
            emit({"decision": "block", "reason": reason})
            sys.exit(0)
    if ticked:
        state[ws] = mine
        cp.save_hook_state(state)
        if level == "advised":
            msg = ("[hook] CHECKPOINT ADVISED (%s) - finish the "
                   "arc, then /checkpoint." % "; ".join(parts))
            if note:
                msg += "\n" + note
            emit({"systemMessage": msg})
            sys.exit(0)
    if note:
        state[ws] = mine
        cp.save_hook_state(state)
        emit({"systemMessage": note})
    sys.exit(0)


def _selftest():
    """The Stop twin's safety check bites on a broken wiring and passes the
    live file; the changelog warning is checked on temp anchor files only
    (never the real tools/.changelog_anchor)."""
    import json
    import tempfile
    import format_lint as fl
    fails = 0
    live = fl.read(fl.SETTINGS)
    ok = fl.check_settings_text(live, fl.HOOKS_DIR)
    print(("PASS  " if not ok else "FAIL  ") + "live settings pass the safety check")
    fails += bool(ok)
    d = json.loads(live)
    d["hooks"]["Stop"] = []
    bad = fl.check_settings_text(json.dumps(d), fl.HOOKS_DIR)
    hit = any("stop_tick" in x for x in bad)
    print(("PASS  " if hit else "FAIL  ") + "unwiring the Stop hook is a SAFETY failure")
    fails += not hit

    missing = os.path.join(tempfile.gettempdir(), "everwood_stop_tick_selftest_missing.txt")
    ok = _commits_since_anchor(missing) is None
    print(("PASS  " if ok else "FAIL  ") + "changelog: missing anchor file -> None (silent)")
    fails += not ok

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cp.ROOT,
                          capture_output=True, text=True, timeout=20).stdout.strip()
    at_head = os.path.join(tempfile.gettempdir(), "everwood_stop_tick_selftest_head.txt")
    with open(at_head, "w", encoding="utf-8") as fh:
        fh.write(head)
    n0 = _commits_since_anchor(at_head)
    ok = n0 == 0
    print(("PASS  " if ok else "FAIL  ") + "changelog: anchor at HEAD -> 0 commits (silent)")
    fails += not ok
    ok = changelog_note({}, n0) is None
    print(("PASS  " if ok else "FAIL  ") + "changelog: 0 commits -> no note")
    fails += not ok

    roots = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=cp.ROOT,
                           capture_output=True, text=True, timeout=20).stdout.strip().splitlines()
    root_commit = roots[0] if roots else head
    behind = os.path.join(tempfile.gettempdir(), "everwood_stop_tick_selftest_behind.txt")
    with open(behind, "w", encoding="utf-8") as fh:
        fh.write(root_commit)
    n2 = _commits_since_anchor(behind)
    ok = n2 is not None and n2 > 0
    print(("PASS  " if ok else "FAIL  ") + "changelog: anchor behind HEAD -> commit count > 0")
    fails += not ok
    mine = {}
    note1 = changelog_note(mine, n2)
    ok = bool(note1) and "CHANGELOG UNEXPORTED" in note1 and str(n2) in note1
    print(("PASS  " if ok else "FAIL  ") + "changelog: behind anchor produces the warning line")
    fails += not ok
    note2 = changelog_note(mine, n2)
    ok = note2 is None
    print(("PASS  " if ok else "FAIL  ") + "changelog: same commit count never warned twice")
    fails += not ok

    # THE INCIDENT SHAPE (2026-09-28): right after an export the anchor sits
    # at the export's parent and HEAD is the "changelog:" commit itself, so
    # a raw count said 1 and the hook warned after every export. The range
    # anchor..<export commit> must count 0.
    exp = subprocess.run(["git", "log", "-1", "--grep=^changelog:", "--format=%H"],
                         cwd=cp.ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
    if exp:
        parent = subprocess.run(["git", "rev-parse", exp + "^"], cwd=cp.ROOT,
                                capture_output=True, text=True, timeout=20).stdout.strip()
        at_parent = os.path.join(tempfile.gettempdir(), "everwood_stop_tick_selftest_export.txt")
        with open(at_parent, "w", encoding="utf-8") as fh:
            fh.write(parent)
        n3 = _commits_since_anchor(at_parent, head=exp)
        ok = n3 == 0
        print(("PASS  " if ok else "FAIL  ") + "changelog: the export commit itself never counts (anchor at its parent -> 0)")
        fails += not ok
    else:
        print("SKIP  changelog: no changelog: commit in this repo to test against")

    # THE CHECKPOINT NAMED CHECK (C0004): the incident sentence trips it, a
    # made checkpoint (the marker) passes, a bare mention of the counter or
    # the state file passes, an ADVISED relay without the marker trips it.
    ok = checkpoint_named("The checkpoint counter has ticked through a full arc tonight, "
                          "so a checkpoint and clear is the natural next step whenever you want to stop.")
    print(("PASS  " if ok else "FAIL  ") + "named: the C0004 sentence trips the check")
    fails += not ok
    ok = not checkpoint_named("Checkpoint done: the counter reset.\n\nCHECKPOINT - safe to /clear. "
                              "Nothing in this chat exists only in this chat.")
    print(("PASS  " if ok else "FAIL  ") + "named: a reply that made the checkpoint (the marker) passes")
    fails += not ok
    ok = not checkpoint_named("The only uncommitted file is checkpoint_state.txt, which the loop rewrites.")
    print(("PASS  " if ok else "FAIL  ") + "named: a bare mention of the state file passes")
    fails += not ok
    ok = checkpoint_named("The prompt hook said CHECKPOINT ADVISED at 80% context; I will do it later.")
    print(("PASS  " if ok else "FAIL  ") + "named: an ADVISED relay without the marker trips it")
    fails += not ok
    ok = not checkpoint_named("")
    print(("PASS  " if ok else "FAIL  ") + "named: empty text passes")
    fails += not ok

    print("stop_tick selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

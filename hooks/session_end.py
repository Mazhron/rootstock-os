"""SessionEnd hook: THE AUTO-CHECKPOINT on /clear (the CEO's ask 2026-09-20).

"Can we make /clear automatically check for a checkpoint, and if none was
done, perform a checkpoint before clearing? If there was a checkpoint, it
just clears, if there wasn't a checkpoint it does it then clears."

The harness fires SessionEnd when the session ends (reason: clear, logout,
prompt_input_exit, other; `resume` is a suspension and is ignored). It
cannot hold the clear back and the manager is already gone, so this hook
does the MECHANICS of a checkpoint by itself and only when work is UNBANKED:

  unbanked = a tracked or untracked change outside docs/history/ (ledger
             churn is not work) OR a commit not yet on origin.

Nothing unbanked -> one ledger line ("already checkpointed"), nothing else:
the clear was already safe. Something unbanked -> the AUTO-CHECKPOINT:
1. mine the final prompt + reply VERBATIM from THIS session's transcript
   (the harness passes transcript_path; the standup script's miner);
2. refresh the newest day file's `## WHERE WE LEFT OFF`: the old section
   is KEPT above it under a SUPERSEDED heading (THE PRESERVATION LAW), the
   new one is marked AUTO with the exchange, a mechanical STATE (version,
   HEAD, the files banked) and an honest "NEXT LIKELY: not written - the
   manager did not close this arc"; today's file + a days_index.txt line
   are created if missing;
3. `git add -A` + commit (subject "Checkpoint (auto): ...", the files
   listed in the body) + push the current branch to origin + the backup
   mirror (tools/backup_push.py, THE LOCAL MIRROR);
4. reset the checkpoint counter and store the work fingerprint, exactly
   as `checkpoint.py --reset` does, so the commit is not a task.
Every step is best-effort and ledgered (docs/history/session_end_runs.txt);
the hook NEVER raises - an exception becomes a ledger line and exit 0,
because the session is ending regardless.

What it is NOT: the manager's checkpoint. The manager's version carries
the arc's judgment (STATE in prose, OPEN QUEUE, NEXT LIKELY); this one
banks the bytes so nothing is lost, and the next standup shows an
"AUTO" section so the manager knows the arc was never properly closed.
ADVISED MEANS DO IT still stands; this is the net under it.

Answers `--selftest` (house pattern): builds a throwaway repo with its own
bare origin in a fresh OS temp folder and runs the real path against it,
so the working tree is never touched by a test. The temp folder is left
for the OS (nothing here removes anything); its path is printed.

PURPOSE: SessionEnd hook that, when the session ends with work unbanked
  (changes outside docs/history/ or commits not on origin), mines the final
  exchange from the transcript, refreshes the day file's WHERE WE LEFT OFF
  as an AUTO section, commits, pushes to origin and the backup mirror, and
  resets the checkpoint counter; it does nothing but ledger when the tree
  was already checkpointed.
INTENT: the CEO 2026-09-20: /clear should check for a checkpoint and do one
  itself when none was done, so a cleared session never loses work.

Search keys: session end hook, auto checkpoint, clear hook, unbanked work,
safety net, lossless clear, transcript miner.
See also: .claude/skills/checkpoint (the manager's ritual); tools/checkpoint.py
(the counter + fingerprint); tools/standup.py (_mine_exchange, and the WHERE
WE LEFT OFF replay); tools/backup_push.py (THE LOCAL MIRROR); HOOKS_METHOD.md
"The kit hooks"; docs/systems/tooling.md "The hooks".
"""
import datetime
import json
import os
import re
import subprocess
import sys

from _hooklib import ROOT, TOOLS, project_version, read_input
import checkpoint as cp

LEDGER_NAME = os.path.join("docs", "history", "session_end_runs.txt")
DAYS_REL = os.path.join("docs", "history", "days")
BOOKKEEPING_PREFIX = "docs/history/"
SECTION = "## WHERE WE LEFT OFF"
_CAP = 12000  # chars per side written to the day file


def git(args, cwd, timeout=30):
    try:
        return subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except Exception as e:  # never raise out of a hook
        class R:
            returncode, stdout, stderr = 1, "", str(e)
        return R()


def unbanked(root):
    """(work paths outside the ledgers, unpushed commit count)."""
    st = git(["status", "--porcelain", "--untracked-files=all"], root).stdout
    work = []
    for ln in st.splitlines():
        if len(ln) < 4:
            continue
        path = ln[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ")[-1]
        p = path.replace("\\", "/")
        if p.startswith(BOOKKEEPING_PREFIX) or any(x in p for x in cp.FP_IGNORE):
            continue
        work.append(p)
    r = git(["rev-list", "--count", "@{u}..HEAD"], root)
    unpushed = int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip().isdigit() else 0
    return work, unpushed


def mine(transcript_path):
    """(user_ts, user_txt, imgs, asst_ts, asst_txt) or None."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        import standup
        got = standup._mine_exchange(transcript_path)
    except Exception:
        return None
    if not got:
        return None
    asst_ts, user_ts, user_txt, imgs, asst_txt = got
    return user_ts, user_txt, imgs, asst_ts, asst_txt


def _stamp(ts):
    try:
        return datetime.datetime.fromisoformat(
            ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return ts or "?"


def _quote(text, cap=_CAP):
    body = (text or "").strip() or "(no text)"
    if len(body) > cap:
        body = body[:cap] + "\n[truncated - full text in the transcript]"
    return "\n".join("> " + ln for ln in body.splitlines())


def build_section(exchange, state, now, reason):
    when = now.strftime("%Y-%m-%d %H:%M")
    out = [SECTION, "",
           "AUTO-CHECKPOINT by the SessionEnd hook (%s, reason: %s). The manager "
           "did not close this arc; the exchange below is mined verbatim from "
           "the harness transcript and STATE is mechanical." % (when, reason), ""]
    if exchange:
        user_ts, user_txt, imgs, asst_ts, asst_txt = exchange
        out += ["USER'S LAST PROMPT (verbatim, %s):" % _stamp(user_ts), "",
                _quote(user_txt)]
        if imgs:
            out.append("> [+ %d image attachment(s)]" % imgs)
        out += ["", "MANAGER'S LAST RESPONSE (verbatim, %s):" % _stamp(asst_ts), "",
                _quote(asst_txt), ""]
    else:
        out += ["(no exchange could be mined from the transcript - the next "
                "standup's THE LAST EXCHANGE is the record)", ""]
    out += ["- STATE (mechanical): " + state,
            "- OPEN QUEUE / NEXT LIKELY: not written (auto). Read the section "
            "above this one and the standup digest; the manager writes the "
            "real closing paragraphs at the next checkpoint.", ""]
    return "\n".join(out)


def refresh_day_file(root, ws, now, section_text):
    """Write the AUTO section into today's day file (created if missing),
    keeping any existing WHERE WE LEFT OFF above it as SUPERSEDED. Returns
    the file's path relative to root."""
    days = os.path.join(root, DAYS_REL)
    os.makedirs(days, exist_ok=True)
    day = now.strftime("%Y-%m-%d")
    name = "%s-%s.md" % (day, ws)
    path = os.path.join(days, name)
    rel = "docs/history/days/" + name
    created = not os.path.isfile(path)
    if created:
        text = ("# %s %s - day file created by the SessionEnd auto-checkpoint\n\n"
                "The manager had not opened a day file for this date when the "
                "session ended with unbanked work. Sections above WHERE WE "
                "LEFT OFF are the manager's to add.\n\n" % (day, ws))
    else:
        text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    superseded = "## SUPERSEDED at %s: where we left off before the auto-checkpoint" % \
        now.strftime("%H:%M")
    # Rename every live section (each one stays in the file), then append the new one.
    text = re.sub(r"^## WHERE WE LEFT OFF[^\n]*$", superseded, text, flags=re.M)
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + section_text
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    if created:
        idx = os.path.join(root, "docs", "history", "days_index.txt")
        with open(idx, "a", encoding="utf-8") as fh:
            fh.write("%s | %s | days/%s | (auto-checkpoint on session end; the "
                     "manager fills this summary)\n" % (day, ws, name))
    return rel


def ledger(root, ws, reason, verdict, now):
    path = os.path.join(root, LEDGER_NAME)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fresh = not os.path.isfile(path)
    with open(path, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write("# SESSION END (SessionEnd hook; append-only). "
                     "date time | ws | reason | verdict. Read the TAIL.\n")
        fh.write("%s | %s | %s | %s\n" % (
            now.strftime("%Y-%m-%d %H:%M"), ws, reason, verdict))


def backup_push(root):
    script = os.path.join(TOOLS, "backup_push.py")
    if not os.path.isfile(script):
        return "no backup_push.py"
    try:
        r = subprocess.run([sys.executable, script], cwd=root, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=25)
        return "ok" if r.returncode == 0 else "FAIL"
    except Exception as e:
        return "FAIL (%s)" % e


def reset_counter(ws, now):
    counts = cp.load()
    counts[ws] = (0, now.strftime("%Y-%m-%d %H:%M") + " (auto-checkpoint)")
    cp.save(counts)
    state = cp.load_hook_state()
    state[ws] = {"fp": cp.work_fingerprint(),
                 "at": now.strftime("%Y-%m-%d %H:%M") + " (auto-checkpoint)"}
    cp.save_hook_state(state)


def auto_checkpoint(root, ws, reason, transcript_path, now, version="?",
                    push=True, do_backup=True, reset=None):
    """The whole ritual, mechanical. Returns the verdict string that was
    ledgered ('already checkpointed' or 'AUTO-CHECKPOINT ...')."""
    work, unpushed = unbanked(root)
    if not work and not unpushed:
        v = "already checkpointed (nothing unbanked)"
        ledger(root, ws, reason, v, now)
        return v
    exchange = mine(transcript_path)
    head = git(["rev-parse", "--short", "HEAD"], root).stdout.strip() or "?"
    shown = ", ".join(work[:12]) + (" (+%d more)" % (len(work) - 12) if len(work) > 12 else "")
    state = "version %s, HEAD %s%s, %d file(s) banked: %s" % (
        version, head, " + %d unpushed commit(s)" % unpushed if unpushed else "",
        len(work), shown or "none (commits only)")
    day_rel = refresh_day_file(root, ws, now, build_section(exchange, state, now, reason))
    verdict = "AUTO-CHECKPOINT: %d file(s), %d unpushed commit(s), exchange %s, day file %s" % (
        len(work), unpushed, "mined" if exchange else "not mined", day_rel)
    ledger(root, ws, reason, verdict, now)
    git(["add", "-A"], root)
    subject = "Checkpoint (auto): the session ended with unbanked work, banked by the SessionEnd hook"
    body = ("Reason: %s. Files banked: %d. Unpushed commits before this: %d.\n%s\n\n"
            "Made by tools/hooks/session_end.py, not by the manager; the day "
            "file's WHERE WE LEFT OFF is marked AUTO.\n\n"
            "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" % (
                reason, len(work), unpushed, "\n".join("- " + p for p in work[:40])))
    c = git(["commit", "-q", "-m", subject, "-m", body], root)
    if c.returncode and work:
        ledger(root, ws, reason, "commit FAILED: %s" % (c.stderr.strip().splitlines() or ["?"])[-1], now)
    if push:
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip() or "HEAD"
        p = git(["push", "origin", branch], root, timeout=30)
        if p.returncode:
            ledger(root, ws, reason, "origin push FAILED: %s" %
                   (p.stderr.strip().splitlines() or ["?"])[-1], now)
    if do_backup:
        b = backup_push(root)
        if b != "ok":
            ledger(root, ws, reason, "backup push: %s" % b, now)
    if reset:
        reset(ws, now)
    return verdict


def main():
    data = read_input()
    reason = data.get("reason", "?")
    if reason == "resume":
        return
    now = datetime.datetime.now()
    ws = cp.which_ws()
    try:
        auto_checkpoint(ROOT, ws, reason, data.get("transcript_path"), now,
                        version=project_version(), reset=reset_counter)
    except Exception as e:
        try:
            ledger(ROOT, ws, reason, "ERROR: %s" % e, now)
        except Exception:
            pass


# ----------------------------------------------------------------- selftest
def _selftest():
    import tempfile
    fails = 0

    def check(ok, what):
        nonlocal fails
        print(("PASS " if ok else "FAIL ") + what)
        fails += 0 if ok else 1

    tmp = tempfile.mkdtemp(prefix="session_end_selftest_")
    print("selftest sandbox (left for the OS temp cleanup): %s" % tmp)
    work = os.path.join(tmp, "work")
    origin = os.path.join(tmp, "origin.git")
    git(["init", "-q", "--bare", origin], tmp)
    git(["init", "-q", "-b", "main", work], tmp)
    git(["config", "user.email", "selftest@example.invalid"], work)
    git(["config", "user.name", "selftest"], work)
    git(["remote", "add", "origin", origin], work)
    os.makedirs(os.path.join(work, "docs", "history", "days"))
    open(os.path.join(work, "a.txt"), "w").write("one\n")
    git(["add", "-A"], work)
    git(["commit", "-q", "-m", "first"], work)
    git(["push", "-q", "-u", "origin", "main"], work)
    now = datetime.datetime(2026, 9, 20, 18, 30)
    day = os.path.join(work, "docs", "history", "days", "2026-09-20-WS1.md")

    # 1. clean tree, everything pushed -> noop
    v = auto_checkpoint(work, "WS1", "clear", None, now, do_backup=False)
    check(v.startswith("already checkpointed"), "clean tree is already checkpointed")
    check(not os.path.isfile(day), "noop writes no day file")

    # 2. ledger-only churn is not work
    open(os.path.join(work, "docs", "history", "loop_runs.txt"), "w").write("x\n")
    v = auto_checkpoint(work, "WS1", "clear", None, now, do_backup=False)
    check(v.startswith("already checkpointed"), "docs/history churn does not count as work")

    # 3. the transcript miner on a stub
    tr = os.path.join(tmp, "stub.jsonl")
    with open(tr, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user", "timestamp": "2026-09-20T18:00:00Z",
                             "message": {"content": "Please fix the willow"}}) + "\n")
        fh.write(json.dumps({"type": "assistant", "timestamp": "2026-09-20T18:01:00Z",
                             "message": {"content": [{"type": "text",
                                                      "text": "The willow is fixed."}]}}) + "\n")
    ex = mine(tr)
    check(ex is not None and ex[1] == "Please fix the willow" and ex[4] == "The willow is fixed.",
          "miner returns both sides verbatim")

    # 4. unbanked work -> commit, push, day file with AUTO + the old section kept
    open(day, "w", encoding="utf-8").write("# day\n\n## WHERE WE LEFT OFF\n\nold words\n")
    open(os.path.join(work, "b.txt"), "w").write("two\n")
    v = auto_checkpoint(work, "WS1", "clear", tr, now, version="9.9", do_backup=False)
    check(v.startswith("AUTO-CHECKPOINT: 1 file(s)"), "dirty tree triggers the auto-checkpoint")
    log = git(["log", "-1", "--format=%s"], work).stdout.strip()
    check(log.startswith("Checkpoint (auto)"), "commit subject is the auto subject")
    check(git(["status", "--porcelain"], work).stdout.strip() == "", "tree clean after the commit")
    check(git(["rev-parse", "HEAD"], work).stdout.strip() ==
          git(["rev-parse", "main"], origin).stdout.strip(), "origin carries the auto commit")
    txt = open(day, encoding="utf-8").read()
    check("## SUPERSEDED at 18:30" in txt and "old words" in txt, "old section kept as SUPERSEDED")
    check(txt.count(SECTION) == 1 and "AUTO-CHECKPOINT by the SessionEnd hook" in txt,
          "one live WHERE WE LEFT OFF, marked AUTO")
    check("> Please fix the willow" in txt and "> The willow is fixed." in txt,
          "both sides of the exchange in the day file")
    check("NEXT LIKELY: not written" in txt, "honest about the missing judgment")
    m = re.search(r"## WHERE WE LEFT OFF.*?(?=\n## |\Z)", txt, flags=re.S)
    check(m is not None and "AUTO-CHECKPOINT" in m.group(0), "standup's regex finds the AUTO section")
    led = open(os.path.join(work, LEDGER_NAME), encoding="utf-8").read()
    check("AUTO-CHECKPOINT: 1 file(s)" in led and led.count("already checkpointed") == 2,
          "ledger carries every run")

    # 5. unpushed commit only, no day file for today -> file created + index line
    open(os.path.join(work, "c.txt"), "w").write("three\n")
    git(["add", "-A"], work)
    git(["commit", "-q", "-m", "local only"], work)
    os.rename(day, day + ".moved")
    v = auto_checkpoint(work, "WS1", "other", None, now, do_backup=False)
    check("1 unpushed commit(s)" in v, "an unpushed commit counts as unbanked")
    check(os.path.isfile(day), "today's day file created when missing")
    idx = open(os.path.join(work, "docs", "history", "days_index.txt"), encoding="utf-8").read()
    check("days/2026-09-20-WS1.md" in idx, "days_index.txt gained its line")
    check(git(["rev-parse", "HEAD"], work).stdout.strip() ==
          git(["rev-parse", "main"], origin).stdout.strip(), "the local-only commit reached origin")

    print("session_end selftest: %d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()

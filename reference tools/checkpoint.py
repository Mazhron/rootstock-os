"""THE CHECKPOINT COUNTER (the CEO approved 2026-09-02: warn at 8 tasks,
DIRE at 15 with the offer to compress or clear).

THE TICK IS AUTOMATIC (2026-09-06, THE HOOKS): the harness's Stop hook
(tools/hooks/stop_tick.py) runs after every manager reply and ticks when
work_fingerprint() says something changed since the last reply (HEAD moved
or the working tree's status changed, bookkeeping files excluded). The old
honesty note ("no background process can watch the conversation") is
retired: a hook can. Manual `--tick` still exists for a hookless machine
but DOUBLE-COUNTS next to the hook - never tick by hand where the hook
runs. `--reset` is run ONLY as the LAST step of a full checkpoint (work
pushed, day file's WHERE-WE-LEFT-OFF refreshed, tree clean) - it also
stores the fingerprint, so the checkpoint commit itself is not a task.

Usage:
  python tools/checkpoint.py --tick     # +1 task (hookless machines only)
  python tools/checkpoint.py --status   # just look
  python tools/checkpoint.py --reset    # checkpoint done - count to zero

Thresholds: >=8 CHECKPOINT ADVISED; >=15 CHECKPOINT URGENT (dire).

THE CONTEXT GAUGE (the CEO's rule 2026-09-04: "regardless of the tasks
3/8, 5/8, if the remaining % before auto compact hits 80% remaining,
suggest a checkpoint and clear"): task count says how much WORK is
unbanked; context says how much the session COSTS. Every tick/status
also probes the newest harness transcript for this project - the last
API record's usage (input + cache_read + cache_creation) IS the live
context load - and warns once less than 80% of the auto-compact budget
remains (urgent under 30%). Calibration 2026-09-04: the CEO's UI read
"44% remaining" at a measured 518k context -> a ~1.0M window with
auto-compact near 925k; override per-machine with PROJECT_CTX_COMPACT
(tokens) if the plan/window differs. Probe failure is SILENT (headless
runs, WS2 paths) - the task counter never depends on it.

Search keys: checkpoint counter, task count, clear warning, context budget,
context gauge, auto compact.
See also: TOKEN_IDEAS.md 9b (the protocol); tools/standup.py (resumption);
docs/history/days/ (the day files that make /clear lossless).
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "docs", "history", "checkpoint_state.txt")


def which_ws():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def load():
    counts = {}
    if os.path.isfile(STATE):
        for ln in open(STATE, encoding="utf-8"):
            m = re.match(r"(WS\S*) \| (\d+) \| (.+)", ln.strip())
            if m:
                counts[m.group(1)] = (int(m.group(2)), m.group(3))
    return counts


def save(counts):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as fh:
        fh.write("# CHECKPOINT STATE (per WS: tasks since last checkpoint).\n")
        for ws, (n, when) in sorted(counts.items()):
            fh.write("%s | %d | %s\n" % (ws, n, when))


COMPACT_BUDGET = int(os.environ.get("PROJECT_CTX_COMPACT", "925000"))

# THE WORK FINGERPRINT (the Stop hook's "did anything change?" test).
HOOK_STATE = os.path.join(ROOT, ".claude", "hooks_state.json")  # gitignored
FP_IGNORE = ("checkpoint_state.txt", "hooks_state.json", "compact_runs.txt")


def work_fingerprint():
    """HEAD + the working tree's porcelain status, bookkeeping files
    excluded, hashed. Equal fingerprints across two Stops = no work."""
    import hashlib
    import subprocess

    def git(*a):
        try:
            return subprocess.run(["git"] + list(a), cwd=ROOT,
                                  capture_output=True, text=True,
                                  timeout=20).stdout
        except Exception:
            return ""
    head = git("rev-parse", "HEAD").strip()
    status = "\n".join(ln for ln in git("status", "--porcelain").splitlines()
                       if not any(x in ln for x in FP_IGNORE))
    return hashlib.md5((head + "\n" + status).encode("utf-8", "replace")).hexdigest()


def load_hook_state():
    try:
        return json.load(open(HOOK_STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_hook_state(state):
    os.makedirs(os.path.dirname(HOOK_STATE), exist_ok=True)
    with open(HOOK_STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)


def _transcript_files():
    """This project's session transcripts, newest first. Same matching as
    standup.py: the repo-root slug, its PARENT's slug (Claude Code may be
    launched from either), or any project folder containing the repo name."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(base):
        return []
    def slug(p):
        return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(p)).lower()
    wanted = {slug(ROOT), slug(os.path.dirname(ROOT))}
    repo_slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.basename(ROOT)).lower()
    files = []
    for d in os.listdir(base):
        full = os.path.join(base, d)
        dl = d.lower()
        if os.path.isdir(full) and (dl in wanted or repo_slug in dl):
            files += glob.glob(os.path.join(full, "*.jsonl"))
    return sorted(files, key=os.path.getmtime, reverse=True)


def context_load():
    """Live context tokens of the CURRENT session: the newest transcript's
    last usage record (input + cache_read + cache_creation). None if no
    transcript or no usage is readable - callers stay silent then."""
    files = _transcript_files()
    if not files:
        return None
    try:
        with open(files[0], encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return None
    for ln in reversed(lines[-400:]):
        try:
            u = (json.loads(ln).get("message") or {}).get("usage")
        except Exception:
            continue
        if not u:
            continue
        total = (int(u.get("input_tokens") or 0)
                 + int(u.get("cache_read_input_tokens") or 0)
                 + int(u.get("cache_creation_input_tokens") or 0))
        if total > 0:
            return total
    return None


def report_context():
    load_ = context_load()
    if load_ is None:
        return
    remaining = max(0.0, 1.0 - load_ / float(COMPACT_BUDGET))
    line = ("context gauge: ~%dk of ~%dk auto-compact budget used "
            "(%d%% remaining)" % (load_ // 1000, COMPACT_BUDGET // 1000,
                                  round(remaining * 100)))
    if remaining < 0.30:
        print("!!!!! CHECKPOINT URGENT (CONTEXT: %d%% remaining) !!!!!"
              % round(remaining * 100))
        print(line)
        print("Auto-compact is close. Checkpoint + /clear NOW - a compact is")
        print("a lossy summary; the day file + standup are lossless.")
    elif remaining < 0.80:
        print("~~ CHECKPOINT ADVISED (CONTEXT: %d%% remaining; the CEO's "
              "80%% rule) ~~" % round(remaining * 100))
        print(line)
        print("Suggest checkpoint + /clear at the next arc boundary - every")
        print("turn re-reads this whole session.")
    else:
        print(line)


def report(n):
    if n >= 15:
        print("!!!!! CHECKPOINT URGENT (%d tasks since last checkpoint) !!!!!" % n)
        print("The session is heavy. the CEO: I recommend /compact or /clear NOW.")
        print("Manager: push, refresh the day file's WHERE WE LEFT OFF, run --reset,")
        print("and emit the checkpoint marker BEFORE taking new work.")
    elif n >= 8:
        print("~~ CHECKPOINT ADVISED (%d tasks since last checkpoint) ~~" % n)
        print("Finish the current arc, then checkpoint (push + day file + marker).")
    else:
        print("checkpoint counter: %d task(s) since last checkpoint (warns at 8, dire at 15)" % n)


def main():
    ap = argparse.ArgumentParser(description="Checkpoint task counter")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tick", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    ws = which_ws()
    counts = load()
    n = counts.get(ws, (0, ""))[0]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if args.tick:
        n += 1
        counts[ws] = (n, now)
        save(counts)
        state = load_hook_state()
        state[ws] = {"fp": work_fingerprint(), "at": now}
        save_hook_state(state)
    elif args.reset:
        n = 0
        counts[ws] = (0, now + " (checkpoint)")
        save(counts)
        state = load_hook_state()
        state[ws] = {"fp": work_fingerprint(), "at": now + " (checkpoint)"}
        save_hook_state(state)
        print("checkpoint counter reset - marker may be emitted.")
        return
    report(n)
    report_context()
    sys.exit(0)


if __name__ == "__main__":
    main()

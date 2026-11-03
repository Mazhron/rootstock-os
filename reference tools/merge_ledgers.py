"""Resolve the hook-ledger conflicts a cross-workstation pull leaves behind, by file class.

PURPOSE: after `git pull --rebase --autostash` (or a merge) conflicts on the
docs/history ledgers both machines appended, write every conflicted file
UNDER docs/history/ whole and stage it (any other conflicted path is listed
and skipped: a source file or a wiki page is a real conflict for a hand): APPEND-ONLY ledgers (*_runs.txt, digest_size.txt and
any other text ledger) union-merge, ours then theirs inside each hunk with
the markers dropped; GENERATED reports (core_diet, wiki_heat, usage_*,
intent_metrics.xlsx) take OUR side, index stage 2, and the next loop run
regenerates them; the STATE file ledger_heads.txt keeps one line per key,
the newest date wins. Nothing is deleted: both pre-merge sides stay in git
history and the autostash entry stays in place (the preserve guard refuses
its drop, rightly). LESSONS.md "Pull when both machines appended the same
generated ledgers"; WORKFLOWS.md "Pull when both machines appended the
ledgers".

INTENT: so two workstations can both append the hook ledgers and a pull
  never ends in a hand-resolved conflict or a lost line (NS-11, the two
  machines joining, 2026-11-03).

Usage: python tools/merge_ledgers.py            (resolves and stages)
       python tools/merge_ledgers.py --dry-run  (names the classes, writes nothing)

Search keys: merge ledgers, pull conflict, union merge, autostash, both appended,
ledger_heads, generated reports, cross-workstation sync.
See also: WORKFLOWS.md "Pull when both machines appended the ledgers";
LESSONS.md (the seeded pull entries); tools/_ledger.py.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = {"core_diet.txt", "wiki_heat.txt", "usage_by_arc.txt", "usage_daily.txt",
             "usage_metrics.txt", "usage_metrics.csv", "usage_employees.txt", "usage_metrics.xlsx",
             "intent_metrics.xlsx", "wiki_view.html"}
# checkpoint_state.txt has the same "KEY | n | date" shape (one line per
# workstation), so it joins the newest-per-key class (adopted 2026-11-03,
# the first two-machine collision, NS-11).
STATE = {"ledger_heads.txt", "checkpoint_state.txt"}


def stage(n, path):
    return subprocess.check_output(["git", "show", f":{n}:{path}"], cwd=ROOT)


def union(text):
    out, mode, ours, theirs = [], None, [], []
    for line in text.splitlines():
        if line.startswith("<<<<<<<"):
            mode, ours, theirs = "o", [], []
            continue
        if line.startswith("=======") and mode == "o":
            mode = "t"
            continue
        if line.startswith(">>>>>>>") and mode == "t":
            out += ours + [l for l in theirs if l not in ours]
            mode = None
            continue
        (out if mode is None else (ours if mode == "o" else theirs)).append(line)
    if mode is not None:
        raise ValueError("an unclosed conflict hunk")
    return "\n".join(out) + "\n"


def newest_per_key(ours, theirs):
    head = [l for l in ours.splitlines() if l.startswith("#")]
    rows = {}
    for l in ours.splitlines() + theirs.splitlines():
        if l.startswith("#") or not l.strip():
            continue
        key, ts = l.split(" | ")[0], l.rsplit(" | ", 1)[-1]
        if key not in rows or ts > rows[key].rsplit(" | ", 1)[-1]:
            rows[key] = l
    return "\n".join(head + sorted(rows.values())) + "\n"


def main(argv):
    dry = "--dry-run" in argv
    files = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=U"], cwd=ROOT, text=True).split()
    counts = {"union": 0, "generated": 0, "state": 0, "skipped": 0}
    for p in files:
        base = os.path.basename(p)
        if not p.replace("\\", "/").startswith("docs/history/"):
            # THE SCOPE (kit v1.58 audit): only the ledgers are merged by class;
            # a conflicted source file, wiki page or lessons book is a real
            # conflict, left for a hand, never union-merged and staged as done.
            counts["skipped"] += 1
            print(f"  skipped   {p} (outside docs/history/: resolve by hand)")
            continue
        full = os.path.join(ROOT, p)
        if base in GENERATED:
            kind, data = "generated", stage(2, p)
        elif base in STATE:
            kind = "state"
            data = newest_per_key(stage(2, p).decode("utf-8"), stage(3, p).decode("utf-8")).encode("utf-8")
        else:
            kind = "union"
            data = union(open(full, encoding="utf-8").read()).encode("utf-8")
        counts[kind] += 1
        print(f"  {kind:9} {p}")
        if not dry:
            with open(full, "wb") as f:
                f.write(data)
            subprocess.check_call(["git", "add", p], cwd=ROOT)
    print("merge_ledgers: union %(union)d | generated (ours) %(generated)d | state (newest per key) %(state)d | skipped (outside docs/history) %(skipped)d" % counts
          + (" | dry run" if dry else " | staged"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

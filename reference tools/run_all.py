"""THE PARENT LOOP (the CEO's ask 2026-09-02): one line runs whole groups of
the scripts we use every session, in order. Any script that becomes a
per-session habit gets ADDED to a group here - never chained by hand again.

Usage:
  python tools/run_all.py --list             # show the groups
  python tools/run_all.py check              # one group
  python tools/run_all.py regen check metrics  # several, in the order given
  python tools/run_all.py session            # the standard end-of-session chain
  python tools/run_all.py --stale            # last run + age (days) per group

THE LOOP LEDGER (the CEO's ruling 2026-09-14, "any script that should be run
multiple times must be called by the main looping script"): every group run
appends one line to docs/history/loop_runs.txt (date/ws/group/seconds/result)
so a stale habitual script shows up instead of silently drifting (metrics_
report.py's ledger once stalled at 09-03 while sibling scripts in the same
group ran by hand). tools/hooks/session_start.py reads this ledger's
`last_run("session")` to decide whether to run the session group itself.

Groups (edit GROUPS to add a script - the Script Rule applies to this file
too: changed only to add or fix):
  check    library/index sanity (check_claude_md) + the lesson lint (lesson_log --check)
  regen    every generated design artifact (sheets + all webs + wiki view)
  tests    the full sweepable test roster (run_tests --all; slow, ~25 min)
  metrics  the company scorecard (parses SUBAGENTS.md, appends its ledger)
           + the usage sheet (harness-metered tokens per model/tool/day)
  probes   the pacing + stability probes (progression 12 rebirths, 5-min soak)
  builds   export + zip both release builds (refuses same-version overwrite)
  session  = regen + check + metrics (the typical pre-push chain)

Each child script keeps its own ledger (REPORTING_METHOD.md); this runner
just chains them, prints each one's tail, and stops on the first failure.

PURPOSE: Chain habitual scripts by named group (check/regen/tests/metrics/
  probes/builds/session/standup) and ledger every group run so staleness is
  visible instead of silent.
INTENT: any script that should be run multiple times must be called by the
  main looping script - never chained by hand a second time.

Search keys: run all, parent script, session chain, script groups, loop
ledger, stale groups.
See also: REPORTING_METHOD.md; tools/run_tests.py; docs/systems/testing.md;
docs/history/loop_runs.txt; tools/hooks/session_start.py (THE LOOP).
"""
import datetime
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOOP_LEDGER = os.path.join(ROOT, "docs", "history", "loop_runs.txt")

GROUPS = {
    "check":   [["tools/core_diet.py", "--move"],   # THE CORE DIET (2026-09-14): moves cold/over-budget routed CLAUDE.md sections BEFORE the lint judges the size
                ["tools/check_claude_md.py"],
                ["tools/workstation_survey.py"],
                ["tools/check_wiki_links.py"],
                ["tools/readme_lint.py"],
                ["tools/format_lint.py", "--quiet"],
                ["tools/purpose_audit.py", "--pending"],
                ["tools/lesson_log.py", "--check"]],   # THE LESSON LOOP (2026-09-20): entry shape + advised/written counts
    "regen":   [["tools/export_upgrades.py"],
                ["tools/export_upgrade_web.py"],
                ["tools/export_species_web.py"],
                ["tools/export_cloud_web.py"],
                ["tools/export_tag_index.py"],
                ["tools/export_wiki_view.py"]],
    "tests":   [["tools/run_tests.py", "--all"]],
    "metrics": [["tools/metrics_report.py"],
                ["tools/usage_report.py"],
                ["tools/wiki_heat.py"],
                ["tools/big_reads.py"],
                ["tools/intent_report.py"]],
    "probes":  [["tools/progression_report.py", "-n", "12"],
                ["tools/soak_report.py", "-m", "5"]],
    "builds":  [["tools/make_builds.py"]],
    "standup": [["tools/standup.py"]],
}
GROUPS["session"] = GROUPS["regen"] + GROUPS["check"] + GROUPS["metrics"]
COMPOSITES = {"session": ("regen", "check", "metrics")}


def which_ws():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def _append_loop_line(group, seconds, failed_script=""):
    """One line per group run: date time | ws | group | seconds | result."""
    os.makedirs(os.path.dirname(LOOP_LEDGER), exist_ok=True)
    fresh = not os.path.isfile(LOOP_LEDGER)
    with open(LOOP_LEDGER, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write("# THE LOOP (append-only): one line per run_all group "
                      "run. date time | ws | group | seconds | result\n")
        result = "FAIL (%s)" % failed_script if failed_script else "ok"
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        fh.write("%s | %s | %s | %.1f | %s\n" % (
            stamp, which_ws(), group, seconds, result))
        # A composite group (session = regen + check + metrics) counts as a
        # run of each member, so --stale, standup and ledger_trends rule 13
        # never call a member stale that the composite just ran.
        for member in COMPOSITES.get(group, ()):
            fh.write("%s | %s | %s | %.1f | %s (in %s)\n" % (
                stamp, which_ws(), member, seconds, result, group))


def last_run(group):
    """The newest loop_runs.txt datetime for `group` (any workstation), or
    None if it has never been run. Used by session_start.py's loop check."""
    if not os.path.isfile(LOOP_LEDGER):
        return None
    newest = None
    for ln in open(LOOP_LEDGER, encoding="utf-8"):
        parts = [p.strip() for p in ln.strip().split("|")]
        if len(parts) < 5 or ln.startswith("#"):
            continue
        when, _ws, grp = parts[0], parts[1], parts[2]
        if grp != group:
            continue
        try:
            dt = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if newest is None or dt > newest:
            newest = dt
    return newest


def print_stale():
    now = datetime.datetime.now()
    for group in GROUPS:
        dt = last_run(group)
        if dt is None:
            print("%-8s never run" % group)
        else:
            age = (now - dt).total_seconds() / 86400.0
            print("%-8s last run %s (%.1f days ago)" % (
                group, dt.strftime("%Y-%m-%d %H:%M"), age))


def main():
    args = [a for a in sys.argv[1:]]
    if not args or "--list" in args:
        print(__doc__)
        return
    if "--stale" in args:
        print_stale()
        return
    for a in args:
        if a not in GROUPS:
            sys.exit("Unknown group '%s' (see --list)." % a)
    env = dict(os.environ)
    # node lives in the portable install on WS2; harmless elsewhere.
    env["PATH"] = env.get("PATH", "") + os.pathsep + \
        r"C:\Users\Travis\AppData\Local\Programs\node-portable\node-v22.14.0-win-x64"
    for group in args:
        t0 = time.time()
        failed_label = ""
        for step in GROUPS[group]:
            label = " ".join(step)
            print("== %s" % label)
            r = subprocess.run([PY] + [os.path.join(ROOT, step[0])] + step[1:],
                               cwd=ROOT, env=env, capture_output=True, text=True,
                               timeout=3600)
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            for ln in tail:
                print("   " + ln)
            if r.returncode != 0:
                failed_label = "%s (exit %d)" % (label, r.returncode)
                break
        _append_loop_line(group, time.time() - t0, failed_label)
        if failed_label:
            sys.exit("STOPPED: %s failed." % failed_label)
    print("\nALL GROUPS COMPLETE (%d)." % len(args))


if __name__ == "__main__":
    main()

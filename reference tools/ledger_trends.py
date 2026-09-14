"""Ledger trends -> PROPOSALS: the learning loop's closing step, read-only.

the CEO's ask 2026-09-10 ("Is Rootstock implementing learning loops?"):
the ledgers already MEASURE (usage, tests, links, heat, employees,
compactions); this script reads their tails, compares them with the
THRESHOLDS below and prints proposed rule changes for the owner. It never
applies anything - a proposal is a sentence at standup, and the owner
decides. Standup calls it after THE BUDGET; run it alone any time.

Proposals (each names its ledger and the number that crossed):
  usage_daily.txt   >= N CHECK verdicts in the last 7 lines -> the read
                    diet is slipping; a rising whole-file-read average
  test_runs.txt     >= N FAIL lines in the last 10 -> a flaky group
  wiki_link_runs.txt  dead links > 0 -> fix them (the list is in
                    wiki_links.txt)
  wiki_heat_runs.txt  ACTIVE-UNREAD cold sections >= N -> propose a heading
                      check (cold by read count alone is never a shelf
                      reason - the CEO 2026-09-10; see wiki_heat WHY COLD)
  usage_daily.txt     read-diet CHECKs and big reads point at
                      docs/history/big_reads.txt (per-file, with the fix)
                    (candidates in wiki_heat.txt; nothing moves without
                    the owner's word)
  SUBAGENTS.md ledger  a model's CORRECTED+FAILED share > 25% of its last
                    10 lines -> the escalation rule (SUBAGENTS rule 6)
  compact_runs.txt  >= N compactions in the last 7 days -> checkpoint
                    earlier
  readme_audit_runs.txt  >= N kit-folder commits or >= N days since the last
                    README audit -> run the four-employee cross-reference
                    (tools/readme_audit.py; the lint is the mechanical layer)
  delete_grants.txt / retired_files.txt  informational counts
  11. open_questions.txt  an OPEN question waited past open_question_days ->
                    ask the CEO or resolve it
  12. digest_size.txt   the newest standup digest exceeds digest_warn_bytes ->
                    trim a tail or split a block
  13. loop_runs.txt     a run_all group's last run is older than its entry
                    in loop_stale_days -> the loop law says the main loop
                    calls it; check the session_start hook
When the set of proposals differs from the last run's, one line goes to
docs/history/proposal_runs.txt so the loop has its own history.

THE THRESHOLDS FILE (the CEO's ruling 2026-09-14): these numbers are
proposal-only - nothing here refuses a tool call or protects anything, so
they are NOT safety wiring (unlike the diet guard's constants, which stay
in code). DEFAULTS below are the script's; the owner's tuned numbers live
in .claude/trend_limits.json (COMMITTED, mirrors .claude/fanout_limits.json),
read fresh on every call. `--limits` prints the effective value and its
source (default/json) for every key.

PURPOSE: Reads the tails of the project's history ledgers (usage, tests,
  wiki links, wiki heat, employee corrections, compactions, README audit,
  intent claims, corrections, systems audit, open questions, digest size,
  the run_all loop), compares them against tunable thresholds, and prints
  proposed rule changes; it applies nothing itself.
INTENT: the CEO's ask 2026-09-10: 'Is Rootstock implementing learning
  loops?' Extended 2026-09-14: open questions get a nudge past N days, and
  the thresholds move to a data file the owner tunes (security and cost/
  efficiency come first; these numbers carry neither, so they are safe to
  externalize).

Search keys: learning loop, proposals, ledger trends, thresholds, rule
change proposal, standup proposals, escalation, cold shelf sweep, open
questions nudge, digest size, loop staleness, trend limits.
See also: tools/standup.py (prints this block); docs/systems/tooling.md
(the learning loop); SUBAGENTS.md rule 6 (escalation); tools/wiki_heat.py;
tools/check_wiki_links.py; tools/usage_report.py; tools/open_questions.py;
.claude/trend_limits.json; .claude/fanout_limits.json (the sibling
pattern); WORKFLOWS.md "Track an open question to the CEO".
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "docs", "history")
RUNS = os.path.join(HIST, "proposal_runs.txt")
CONFIG = os.path.join(ROOT, ".claude", "trend_limits.json")  # COMMITTED: the owner's tuned numbers
DEFAULTS = {
    "usage_check_days": 3,      # CHECK verdicts among the last 7 daily lines
    "usage_big_reads": 8,       # avg "big" whole-file reads over the last 7 lines
    "test_fails": 2,            # FAIL lines among the last 10 test runs
    "cold_sections": 10,        # cold sections reported by wiki_heat
    "employee_correction_pct": 25,  # SUBAGENTS rule 6
    "compactions_7d": 2,        # compactions inside the last 7 days
    "readme_audit_kit_commits": 12,  # kit-folder commits since the last README audit
    "readme_audit_days": 30,         # days since the last README audit
    "intent_pending_days": 7,        # an intent claim left PENDING this long
    "corrections_7d": 3,             # corrections recorded inside the last 7 days
    "systems_audit_days": 30,        # days since the last systems audit
    "systems_audit_day_files": 10,   # day files written since the last systems audit
    "open_question_days": 7,         # an OPEN question waited this many days
    "digest_warn_bytes": 12000,      # the standup digest's byte size (24000 before THE DIGEST DIET, 2026-09-14: ~6-8k after it)
    "loop_stale_days": {             # per run_all group: days since last run
        "session": 2, "metrics": 2, "check": 2, "regen": 7, "probes": 14, "tests": 7,
    },
}
# THRESHOLDS kept as an alias: older code/callers importing THRESHOLDS still work,
# but it no longer reflects the owner's tuning - use load_limits() for that.
THRESHOLDS = DEFAULTS


def load_limits(path=CONFIG):
    """DEFAULTS overlaid with the owner's tuned numbers from trend_limits.json.
    A missing or broken file, an unknown key or a non-positive value falls
    back silently - this script must never crash standup over its own config."""
    limits = dict(DEFAULTS)
    limits["loop_stale_days"] = dict(DEFAULTS["loop_stale_days"])
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        for k, v in (raw or {}).items():
            if k == "_comment":
                continue
            if k == "loop_stale_days" and isinstance(v, dict):
                for gk, gv in v.items():
                    if gk in DEFAULTS["loop_stale_days"] and isinstance(gv, (int, float)) \
                            and not isinstance(gv, bool) and gv > 0:
                        limits["loop_stale_days"][gk] = int(gv)
            elif k in DEFAULTS and isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                limits[k] = int(v)
    except Exception:
        pass
    return limits


def limits_table():
    """The --limits printout: key, current, default, source (default/json)."""
    limits = load_limits()
    lines_out = ["ledger_trends limits (DEFAULTS in tools/ledger_trends.py, "
                 "owner tuning in .claude/trend_limits.json)"]
    lines_out.append("  %-30s %12s %12s  %s" % ("key", "current", "default", "source"))
    for k, dv in DEFAULTS.items():
        if k == "loop_stale_days":
            for gk, gdv in dv.items():
                cur = limits["loop_stale_days"][gk]
                src = "json" if cur != gdv else "default"
                lines_out.append("  %-30s %12s %12s  %s" % ("loop_stale_days.%s" % gk, cur, gdv, src))
            continue
        cur = limits[k]
        src = "json" if cur != dv else "default"
        lines_out.append("  %-30s %12s %12s  %s" % (k, cur, dv, src))
    return "\n".join(lines_out)


def data_lines(name):
    path = os.path.join(HIST, name)
    try:
        with open(path, encoding="utf-8") as fh:
            return [ln.rstrip() for ln in fh if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def proposals(th=None):
    th = th or load_limits()
    out = []
    # 1. usage_daily.txt
    # A CHECK is a diet signal only when its reasons name the diet (reads,
    # section share, cache misses); a spend-only CHECK is a busy day, not a
    # slipping habit (the 2026-09-10 echo: two old heavy days kept proposing
    # "the diet is slipping" while the last five days ran 90-100% sectioned).
    lines = data_lines("usage_daily.txt")[-7:]
    diet_re = re.compile(r"heavy whole-file reads|section-read share|cache misses")
    checks = [ln for ln in lines if "| CHECK" in ln and diet_re.search(ln)]
    if len(checks) >= th["usage_check_days"]:
        out.append("PROPOSE (usage_daily.txt): %d of the last %d days carry a READ-DIET "
                   "CHECK (heavy whole reads, low section share or cache misses). "
                   "The files: docs/history/big_reads.txt (`python tools/big_reads.py`) "
                   "- the manager sections or splits them on that report's word, no "
                   "approval needed (the CEO 2026-09-10); misses -> batch CLAUDE.md/"
                   "MEMORY edits at checkpoint." % (len(checks), len(lines)))
    # Big reads: judge the LAST THREE active days, not a 7-day mean that two
    # old heavy days can carry for a week after the habit is fixed.
    bigs = []
    for ln in lines:
        m = re.search(r"\|\s*\d+ \((\d+)\) / \d+,", ln)
        if m:
            bigs.append(int(m.group(1)))
    recent = bigs[-3:]
    if recent and sum(recent) / float(len(recent)) >= th["usage_big_reads"]:
        out.append("PROPOSE (usage_daily.txt): big whole-file reads average %.1f/day "
                   "over the last %d active days - the files and their fix are in "
                   "docs/history/big_reads.txt; section or split them (standing order, "
                   "no approval needed)." % (sum(recent) / float(len(recent)), len(recent)))
    # 2. test_runs.txt
    tests = data_lines("test_runs.txt")[-10:]
    fails = [ln for ln in tests if "FAIL" in ln]
    if len(fails) >= th["test_fails"]:
        groups = sorted({ln.split("|")[3].strip() for ln in fails if ln.count("|") >= 3})
        out.append("PROPOSE (test_runs.txt): %d FAIL lines in the last %d runs (%s) - "
                   "a flaky or broken group; fix or quarantine before the next ship."
                   % (len(fails), len(tests), ", ".join(groups) or "?"))
    # 3. wiki_link_runs.txt
    links = data_lines("wiki_link_runs.txt")
    if links:
        m = re.search(r"dead (\d+)", links[-1])
        if m and int(m.group(1)) > 0:
            out.append("PROPOSE (wiki_link_runs.txt): %s dead wiki link(s) - fix them "
                       "(the list: docs/history/wiki_links.txt)." % m.group(1))
    # 4. wiki_heat_runs.txt
    # Cold by read count alone is NOT a shelf reason in a game project
    # (the CEO 2026-09-10): a system doc goes unread while its system is not
    # being worked on, and the wiki is a human reference too. Only the
    # ACTIVE-UNREAD class (code moved, doc never opened) is worth a look.
    heat = data_lines("wiki_heat_runs.txt")
    if heat:
        m = re.search(r"active-unread (\d+)", heat[-1])
        if m and int(m.group(1)) >= th["cold_sections"]:
            out.append("PROPOSE (wiki_heat_runs.txt): %s cold sections sit in wiki files "
                       "whose CODE moved in the last 30 days but whose doc was never "
                       "opened (active-unread) - check those headings for search keys "
                       "or staleness (docs/history/wiki_heat.txt, WHY COLD). Dormant, "
                       "reference and archive cold is expected and never a shelf reason."
                       % m.group(1))
    # 5. SUBAGENTS.md ledger (rule 6)
    try:
        with open(os.path.join(ROOT, "SUBAGENTS.md"), encoding="utf-8") as fh:
            body = fh.read()
        led = body.split("## THE LEDGER", 1)[1] if "## THE LEDGER" in body else ""
        per = {}
        for ln in led.splitlines():
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) < 5 or not re.match(r"\d{4}-\d\d-\d\d", parts[0]):
                continue
            model = parts[2].split("/")[0].strip().lower()
            outcome = parts[4].split("-")[0].strip().upper()
            per.setdefault(model, []).append(outcome)
        for model, outs in sorted(per.items()):
            last = outs[-10:]
            bad = sum(1 for o in last if o.startswith(("CORRECTED", "FAILED")))
            pct = 100.0 * bad / len(last) if last else 0
            if len(last) >= 4 and pct > th["employee_correction_pct"]:
                out.append("PROPOSE (SUBAGENTS.md ledger): %s corrected/failed on %d of its "
                           "last %d tasks (%.0f%%) - rule 6 says bump the model a tier or "
                           "raise the effort in THE ASSIGNMENTS (dated, attributed)."
                           % (model, bad, len(last), pct))
    except OSError:
        pass
    # 6. compact_runs.txt
    week = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    comps = [ln for ln in data_lines("compact_runs.txt") if ln[:10] >= week
             and "pipe-test" not in ln]
    if len(comps) >= th["compactions_7d"]:
        out.append("PROPOSE (compact_runs.txt): %d compactions in the last 7 days - "
                   "sessions run past the gauge; checkpoint at the first ADVISED line."
                   % len(comps))
    # 7. readme_audit_runs.txt (the CEO 2026-09-13: the README's third layer)
    # The parity lint (tools/readme_lint.py) catches facts a script can
    # derive; only a four-employee audit catches an answer the wiki holds
    # that the README never says. Propose one when the kit has moved past
    # a commit count or an age since the last recorded audit.
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import readme_audit  # noqa: E402 - sibling script, same folder
        stamp, days, commits = readme_audit.status()
        if stamp is None:
            out.append("PROPOSE (readme_audit_runs.txt): no README audit on record - run the "
                       "four-employee cross-reference (WORKFLOWS.md 'Audit the public README') "
                       "and `python tools/readme_audit.py --record \"...\"`.")
        elif commits >= th["readme_audit_kit_commits"] or (days or 0) >= th["readme_audit_days"]:
            out.append("PROPOSE (readme_audit_runs.txt): %d kit-folder commit(s) and %s day(s) "
                       "since the last README audit (%s) - the lint keeps the counts honest, "
                       "an audit finds the answers the README never got; run the four-employee "
                       "cross-reference and `--record` it." % (commits, days, stamp))
    except Exception:  # noqa: BLE001 - a missing helper never breaks standup
        pass
    # 8-10. THE INTENT LOOP (the CEO 2026-09-13, INTENT.md "Intent tracking"):
    # the agreement trend, stale claims, clustered corrections, and the
    # systems-audit cadence. Real data, past vs present, improving or not.
    runs = data_lines("intent_runs.txt")
    if runs:
        last = runs[-1]
        if "DECLINING" in last:
            out.append("PROPOSE (intent_runs.txt): the 7-day intent agreement is DECLINING (%s) "
                       "- Claude's reading of asks is drifting from the CEO's; read the "
                       "DIFFERENT lines in docs/history/intent_log.txt and file the missing "
                       "INTENT.md sections (the why) before the next build." % last.split(" | ")[-1])
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import intent_log  # noqa: E402
        st, order = intent_log.state()
        cutoff = (datetime.datetime.now() - datetime.timedelta(
            days=th["intent_pending_days"])).strftime("%Y-%m-%d %H:%M")
        stale = [i for i in order if st[i]["verdict"] == "PENDING" and st[i]["when"] < cutoff]
        if stale:
            out.append("PROPOSE (intent_log.txt): %d intent claim(s) pending past %d days (%s) - "
                       "resolve each (`python tools/intent_log.py --resolve <id> ...`); an "
                       "unresolved claim is a comparison never made."
                       % (len(stale), th["intent_pending_days"], ", ".join(stale[:5])))
    except Exception:  # noqa: BLE001
        pass
    week = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    corr = [ln for ln in data_lines("corrections.txt") if ln.startswith("RECORD | ")
            and ln.split(" | ")[2][:10] >= week]
    if len(corr) >= th["corrections_7d"]:
        out.append("PROPOSE (corrections.txt): %d corrections in the last 7 days - a law or an "
                   "INTENT.md section is missing; read their 'what was wrong' words together "
                   "and name the pattern to the CEO." % len(corr))
    try:
        import systems_audit  # noqa: E402
        stamp, days, dfs, commits = systems_audit.status()
        if stamp is None:
            out.append("PROPOSE (systems_audit_runs.txt): no systems audit on record - run the "
                       "four-lane audit (WORKFLOWS.md 'Audit the operating system') and "
                       "`python tools/systems_audit.py --record \"...\"`.")
        elif (days or 0) >= th["systems_audit_days"] or dfs >= th["systems_audit_day_files"]:
            out.append("PROPOSE (systems_audit_runs.txt): %s day(s) and %d day file(s) since the "
                       "last systems audit (%s) - run the four-lane audit (tokens, process, "
                       "knowledge, features) and `--record` it; proposals only, the CEO decides."
                       % (days, dfs, stamp))
    except Exception:  # noqa: BLE001
        pass
    # 11. open_questions.txt (the CEO's ruling 2026-09-14): a question only
    # the owner can answer, waiting past open_question_days, is a nudge -
    # never a decision made for them.
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import open_questions  # noqa: E402
        stale = [(age, r) for age, r in open_questions.open_rows()
                 if age >= th["open_question_days"]]
        if stale:
            age, r = stale[0]  # sorted oldest-first by open_rows()
            extra = (" (also waiting: %s)" % ", ".join(a[1]["id"] for a in stale[1:5])) \
                if len(stale) > 1 else ""
            out.append("PROPOSE (open_questions.txt): %s has waited %d d - ask the CEO or "
                       "resolve it%s." % (r["id"], age, extra))
    except Exception:  # noqa: BLE001
        pass
    # 12. digest_size.txt: the standup digest itself costs a session-start
    # read every time - a growing digest is worth trimming or splitting.
    sizes = data_lines("digest_size.txt")
    if sizes:
        parts = [p.strip() for p in sizes[-1].split("|")]
        if len(parts) >= 4:
            m = re.search(r"(\d+)", parts[2])
            if m and int(m.group(1)) > th["digest_warn_bytes"]:
                out.append("PROPOSE (digest_size.txt): the standup digest is %s bytes (~%s "
                           "tokens) at every session start - trim a tail or split a block."
                           % (m.group(1), parts[3]))
    # 13. loop_runs.txt (THE LOOP LAW): a run_all group whose last run is
    # older than its loop_stale_days entry means the main loop isn't calling
    # it on the cadence the law expects.
    runs = data_lines("loop_runs.txt")
    latest = {}
    for ln in runs:
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) < 3:
            continue
        try:
            dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        group = parts[2]
        if group not in latest or dt > latest[group]:
            latest[group] = dt
    now = datetime.datetime.now()
    for group, max_days in th["loop_stale_days"].items():
        last = latest.get(group)
        if last is not None and (now - last).days > max_days:
            out.append("PROPOSE (loop_runs.txt): %s last ran %d d ago - the loop law says the "
                       "main loop calls it; check the session_start hook." % (group, (now - last).days))
    return out


def info_lines():
    out = []
    n = len(data_lines("delete_grants.txt"))
    if n:
        out.append("grants: %d double-acknowledged deletion(s) on record (delete_grants.txt)" % n)
    n = len(data_lines("retired_files.txt"))
    if n:
        out.append("retired: %d file(s) on the shelf (_retired/, retired_files.txt)" % n)
    return out


def record(props):
    """One ledger line when the proposal set changed since the last line."""
    key = " || ".join(p.split(":", 1)[0] + ":" + p.split(":", 1)[1][:60] for p in props)
    last = data_lines("proposal_runs.txt")
    if last and last[-1].split(" | ", 3)[-1] == (key or "none"):
        return
    new = not os.path.isfile(RUNS)
    with open(RUNS, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# PROPOSAL HISTORY (append-only; one line whenever the ledger trends "
                     "change what is proposed). Read the TAIL.\n"
                     "# date time | ws | count | proposals (truncated)\n")
        fh.write("%s | %s | %d | %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                          workstation(), len(props), key or "none"))


def main(argv):
    if "--limits" in argv:
        print(limits_table())
        return 0
    props = proposals(load_limits())
    print("== PROPOSALS (ledger trends vs thresholds; `python tools/ledger_trends.py "
          "--limits`; NOTHING is applied - the owner decides)")
    if props:
        for p in props:
            print("  " + p)
    else:
        print("  none - every ledger trend is inside its threshold")
    for ln in info_lines():
        print("  " + ln)
    if "--no-record" not in argv:
        record(props)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

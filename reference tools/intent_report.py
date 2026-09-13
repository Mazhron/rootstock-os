"""THE INTENT REPORT (Mazhron's ruling 2026-09-13: agreement between Claude's
intent and Mazhron's, "kept track of by day, week, month, like every other
ledger... in txt for you and your employees and a csv/xcl file for a human
to read... audited by script and compared as cheaply as possible").

    python tools/intent_report.py          # regenerate the three outputs + one ledger line

Reads docs/history/intent_log.txt (claims + resolutions, newest line per
id wins) and docs/history/corrections.txt (RECORD lines). Writes:
  docs/history/intent_metrics.txt   for Claude + employees: the SUMMARY block
                                    (all-time, last 7 days vs the 7 before,
                                    the TREND verdict), then day / week /
                                    month tables per actor
  docs/history/intent_metrics.csv   the same rows, one table, for a human
  docs/history/intent_metrics.xlsx  the spreadsheet (openpyxl; skipped
                                    quietly without it) - THE SPREADSHEET
                                    RULE: header frozen, TOTAL rows bold
  docs/history/intent_runs.txt      ONE line per run (append-only): claims,
                                    resolved, agreement %, different %,
                                    pending, corrections, the trend - what
                                    ledger_trends and standup read

THE NUMBERS. agreement = (SAME + SIMILAR) / resolved; different = DIFFERENT
/ resolved; both per period and per actor (fable = manager; an employee's
model name otherwise). THE TREND compares the last 7 days' agreement
against the previous 7 active days (and the last 30 vs the 30 before, as
a second reading): IMPROVING when it rose by TREND_POINTS or more, DECLINING
when it fell by that much, STEADY between, and "n/a (fewer than MIN_RESOLVED
resolved)" while the data is thin - a verdict on three lines is a coin
flip, and the whole point is REAL data. Every number is a count of
recorded verdicts, nothing estimated; "inferred" sources are counted
separately so a self-judged SAME never hides inside a stated one.

Why a script (INTENT.md "Intent tracking", Mazhron's words): it is the
same every time, it is cheap and costs no tokens, and it is structured
and triggers from the loop we already have - run_all's metrics group.

Search keys: intent metrics, agreement rate, same similar different,
intent trend, improving declining, intent spreadsheet, feedback loop.
See also: tools/intent_log.py; tools/correction_log.py; tools/ledger_trends.py
(rule 8 reads intent_runs.txt); INTENT.md; INTENT_METHOD.md (portable);
docs/systems/tooling.md "The intent loop".
"""
import csv
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "docs", "history")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import intent_log  # noqa: E402
import correction_log  # noqa: E402

TXT = os.path.join(HIST, "intent_metrics.txt")
CSV = os.path.join(HIST, "intent_metrics.csv")
XLSX = os.path.join(HIST, "intent_metrics.xlsx")
RUNS = os.path.join(HIST, "intent_runs.txt")
TREND_POINTS = 5      # percentage points of agreement that count as a move
MIN_RESOLVED = 5      # resolved verdicts a period needs before a trend is called
FIELDS = ["period_type", "period", "actor", "claims", "resolved", "same", "similar",
          "different", "pending", "agreement_pct", "different_pct", "stated", "correction",
          "inferred", "corrections"]


def period_keys(day):
    d = datetime.date.fromisoformat(day)
    iso = d.isocalendar()
    return {"day": day, "week": "%d-W%02d" % (iso[0], iso[1]), "month": day[:7]}


def bucket():
    """{(period_type, period, actor): counters}"""
    st, order = intent_log.state()
    rows = {}

    def get(pt, p, actor):
        return rows.setdefault((pt, p, actor), dict(claims=0, resolved=0, same=0, similar=0,
                                                    different=0, pending=0, stated=0,
                                                    correction=0, inferred=0, corrections=0))
    for i in order:
        r = st[i]
        day = r["when"][:10]
        if not day:
            continue
        for pt, p in period_keys(day).items():
            for actor in (r["actor"] or "?", "all"):
                c = get(pt, p, actor)
                c["claims"] += 1
                v = r["verdict"]
                if v == "PENDING":
                    c["pending"] += 1
                else:
                    c["resolved"] += 1
                    c[v.lower()] += 1
                    if r["source"] in ("stated", "correction", "inferred"):
                        c[r["source"]] += 1
    for r in correction_log.records():
        if r["kind"] != "RECORD" or not r["when"][:10]:
            continue
        for pt, p in period_keys(r["when"][:10]).items():
            for actor in (r["actor"] or "?", "all"):
                get(pt, p, actor)["corrections"] += 1
    return rows


def pct(n, d):
    return round(100.0 * n / d, 1) if d else ""


def table_rows(rows):
    out = []
    order = {"day": 0, "week": 1, "month": 2}
    for (pt, p, actor), c in sorted(rows.items(), key=lambda kv: (order[kv[0][0]], kv[0][1],
                                                                  kv[0][2] == "all", kv[0][2])):
        out.append([pt, p, "total" if actor == "all" else actor, c["claims"], c["resolved"],
                    c["same"], c["similar"], c["different"], c["pending"],
                    pct(c["same"] + c["similar"], c["resolved"]),
                    pct(c["different"], c["resolved"]), c["stated"], c["correction"],
                    c["inferred"], c["corrections"]])
    return out


def window(rows, days_back, days_len):
    """Agreement over the 'all' actor for day periods inside a window ending days_back
    days ago and spanning days_len days: (resolved, agreement_pct or None)."""
    today = datetime.date.today()
    end = today - datetime.timedelta(days=days_back)
    start = end - datetime.timedelta(days=days_len - 1)
    res = agree = 0
    for (pt, p, actor), c in rows.items():
        if pt != "day" or actor != "all":
            continue
        d = datetime.date.fromisoformat(p)
        if start <= d <= end:
            res += c["resolved"]
            agree += c["same"] + c["similar"]
    return res, (100.0 * agree / res if res else None)


def trend(rows, span):
    r1, a1 = window(rows, 0, span)
    r0, a0 = window(rows, span, span)
    if r1 < MIN_RESOLVED or r0 < MIN_RESOLVED or a1 is None or a0 is None:
        return "n/a (fewer than %d resolved in a %d-day window: %d now, %d before)" % (
            MIN_RESOLVED, span, r1, r0), a1, a0
    diff = a1 - a0
    verdict = "IMPROVING" if diff >= TREND_POINTS else ("DECLINING" if diff <= -TREND_POINTS
                                                         else "STEADY")
    return "%s (%.0f%% -> %.0f%%, %+.0f points)" % (verdict, a0, a1, diff), a1, a0


def write_txt(rows, tot, t7, t30):
    lines = ["== INTENT METRICS (regenerated by tools/intent_report.py; the log is "
             "docs/history/intent_log.txt, corrections in corrections.txt)",
             "== SUMMARY",
             "  all-time: %d claims | %d resolved | SAME %d SIMILAR %d DIFFERENT %d | "
             "agreement %s%% | different %s%% | pending %d | corrections %d | sources: "
             "stated %d correction %d inferred %d" % (
                 tot["claims"], tot["resolved"], tot["same"], tot["similar"], tot["different"],
                 pct(tot["same"] + tot["similar"], tot["resolved"]),
                 pct(tot["different"], tot["resolved"]), tot["pending"], tot["corrections"],
                 tot["stated"], tot["correction"], tot["inferred"]),
             "  TREND 7-day:  %s" % t7,
             "  TREND 30-day: %s" % t30,
             "  (agreement = SAME+SIMILAR over resolved; a trend needs %d resolved per window; "
             "moves of %d+ points count; 'inferred' = self-judged, never mistaken for stated)"
             % (MIN_RESOLVED, TREND_POINTS)]
    for pt in ("day", "week", "month"):
        lines.append("== BY %s (actor: total = every actor)" % pt.upper())
        lines.append("  " + " | ".join(FIELDS[1:]))
        for r in table_rows(rows):
            if r[0] == pt:
                lines.append("  " + " | ".join(str(x) for x in r[1:]))
    with open(TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_csv(rows):
    with open(CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for r in table_rows(rows):
            w.writerow(r)


def write_xlsx(rows, summary):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Border, Side, Alignment
    except ImportError:
        return False
    wb = Workbook()
    wb.remove(wb.active)
    bold = Font(bold=True)
    thick = Border(bottom=Side(style="thick"))
    ws = wb.create_sheet("summary")
    for ln in summary:
        ws.append([ln])
    ws.column_dimensions["A"].width = 120
    for pt in ("day", "week", "month"):
        s = wb.create_sheet(pt)
        s.append(FIELDS)
        for c in s[1]:
            c.font = bold
            c.alignment = Alignment(horizontal="center")
        s.freeze_panes = "A2"
        s.auto_filter.ref = "A1:%s1" % s.cell(row=1, column=len(FIELDS)).column_letter
        for r in table_rows(rows):
            if r[0] != pt:
                continue
            s.append(r)
            if r[2] == "total":
                for c in s[s.max_row]:
                    c.font = bold
                    c.border = thick
        for i, f in enumerate(FIELDS, 1):
            s.column_dimensions[s.cell(row=1, column=i).column_letter].width = 14
    wb.save(XLSX)
    return True


def ledger(tot, t7):
    new = not os.path.isfile(RUNS)
    with open(RUNS, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# INTENT RUNS (append-only; one line per intent_report run). Read the TAIL.\n"
                     "# date time | ws | claims | resolved | agreement % | different % | pending | "
                     "corrections | trend 7-day\n")
        fh.write("%s | %s | %d | %d | %s | %s | %d | %d | %s\n" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), intent_log.workstation(),
            tot["claims"], tot["resolved"], pct(tot["same"] + tot["similar"], tot["resolved"]) or 0,
            pct(tot["different"], tot["resolved"]) or 0, tot["pending"], tot["corrections"],
            t7.split(" (")[0]))


def main():
    rows = bucket()
    tot = dict(claims=0, resolved=0, same=0, similar=0, different=0, pending=0, stated=0,
               correction=0, inferred=0, corrections=0)
    for (pt, p, actor), c in rows.items():
        if pt == "day" and actor == "all":
            for k in tot:
                tot[k] += c[k]
    t7, _, _ = trend(rows, 7)
    t30, _, _ = trend(rows, 30)
    write_txt(rows, tot, t7, t30)
    write_csv(rows)
    summary = open(TXT, encoding="utf-8").read().split("== BY DAY")[0].splitlines()
    x = write_xlsx(rows, summary)
    ledger(tot, t7)
    print("INTENT REPORT: %d claims, %d resolved, agreement %s%%, different %s%%, pending %d, "
          "corrections %d | 7-day %s | 30-day %s | wrote intent_metrics.txt/.csv%s"
          % (tot["claims"], tot["resolved"], pct(tot["same"] + tot["similar"], tot["resolved"])
             or 0, pct(tot["different"], tot["resolved"]) or 0, tot["pending"],
             tot["corrections"], t7, t30, "/.xlsx" if x else " (no openpyxl: xlsx skipped)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# The Reporting Method (portable: scripted runs + history ledgers, for any project)

PORTABLE FILE: an architecture, not a project. Hand it to any Claude (or any
capable agent) at the start of any project alongside its siblings
(SUBAGENT_METHOD.md, WIKI_METHOD.md) and say "set this up". Nothing here
assumes a game, a language, or a test framework.

THE PROBLEM IT KILLS: ad-hoc runs are amnesia. A test typed by hand today and
retyped slightly differently tomorrow cannot be compared, cannot be delegated
cheaply, silently skips what someone forgot, and its results vanish into a
chat log nobody re-reads. Regressions then survive for WEEKS because nothing
ever says "this passed last Tuesday and fails today."

## The three rules

1. THE SCRIPT RULE. Anything repeatable - tests, builds, imports, exports,
   probes, reports, data regeneration - is a SCRIPT in the repo, and the
   script is the ONLY way that thing is ever run. Scripts are changed only to
   ADD a capability or FIX a defect; commands are never retyped in chat, in
   notes, or in a sub-agent's brief. If a human or an AI "just runs it by
   hand this once," that is the defect - script it.
2. THE LEDGER RULE. Every scripted run APPENDS exactly one labeled line to an
   append-only history file (a docs/history/ directory of plain .txt ledgers,
   one per kind of run). The line carries: date+time | which machine/agent |
   the project version | what ran | the result | failures if any. The files
   travel with the repo (version control), so every machine and every session
   shares one memory. READING RULE: read the TAIL, never the whole file -
   the ledger exists so nobody re-reads anything.
3. THE BASELINE RULE. The first act after building a runner is recording a
   FULL baseline. After any notable change, re-run what it could touch. A
   regression is then a visible line flip - "passed at vX, fails at vY" -
   and the guilty range is two adjacent ledger lines, not an archaeology dig.

## What a runner script must do

- Own the WHOLE inventory of what can run, grouped correctly: every isolation
  law ("A and B must never share a process"), every per-task environment
  requirement, every timing window lives IN the script. An illegal ad-hoc
  combination is REFUSED with the law quoted - never allowed to produce a
  mystery flake.
- Parse its own results (pass/fail per item), print a compact summary, exit
  nonzero on any failure - so it is automatable, chainable with other
  scripts, and delegable to the cheapest sub-agent as a ONE-LINE brief
  ("run <script> --all"). This is where the method compounds with
  SUBAGENT_METHOD.md: scripted work needs no context to delegate.
- Append its ledger line itself (rule 2) - reporting is not a separate step
  anyone can forget.
- Identify the machine/agent automatically where possible (hostname, user
  path) so multi-machine ledgers stay attributable with zero configuration.
- Long/expensive runs (soaks, benchmarks) are excluded from the default
  "--all" and run deliberately - but STILL through the script, STILL ledgered.

## What earns a ledger (not just tests)

Tests are the obvious case; the same shape pays for: progression/balance
probes (compare tuning across versions), benchmark numbers (compare perf
across optimizations), build/export runs, data-regeneration passes. One
ledger file per kind, same line discipline. When a number matters enough to
mention in a conversation, it matters enough to append.

## The usage sheet: mine the harness meter, never self-estimate

A model cannot see its own token meter - but the HARNESS can, and it writes
it down. Claude Code keeps full session transcripts under
~/.claude/projects/<project>/*.jsonl (sub-agent runs in
<session>/subagents/agent-*.jsonl): every assistant message carries the real
API usage (model, input/output/thinking tokens, cache reads/writes) and
every tool call is named. A miner script aggregates that into ONE derived
sheet - totals per day / week / month for each model and each tool, CSV for
humans + a TXT twin - replacing all self-estimated token figures with
metered truth. Dollars stay estimates (price tokens from a table in the
script); the billing dashboard is the only dollar truth. Two laws learned
building it: (a) the transcripts ARE the ledger, so the sheet REGENERATES
whole instead of appending; (b) key rows by machine/workstation - each
machine only sees its own transcripts, so a run must only rewrite its own
rows. Reference implementation: Everwood's tools/usage_report.py
(incremental byte-offset cache; a 274MB transcript parses once, reruns
read only new bytes).

## THE WEIGHTED COLUMN + THE COMPARISON RULE (the CEO's rulings 2026-09-10)
Tags: economy, lessons, process | Only budget-weighted tokens are the headline; a number without a comparison means nothing - every daily figure is judged against the previous seven days with the reason named

THE WEIGHTED COLUMN. The origin CEO, on seeing 200M cache-read tokens:
"The most important token counts are the ones that actually count against
a user's usage amount... my budget is only being hit by 5 million. That
should be the concept for any of the pillars." So every usage sheet
carries a WEIGHTED column beside the raw one and makes it the headline:
input x1, cache write x1.25 (x2 on a 1-hour cache), cache read x0.1 (x0.025
on the model that discounts it), output x5 - the API's own price ratios,
the best public model of an unpublished budget. The raw count stays as
trivia. The same weights drive every other meter in the project (the
fan-out guard's spend), so all numbers agree. Under those weights the
origin project's split was cache WRITES 43%, cache reads 40%, output 17%,
fresh input ~0 - which is why the sheet also counts CACHE MISSES (a
request after a session's first whose cache write is most of its prompt:
the cache expired or an early prefix byte changed) - 24% of the origin's
all-time budget was prefix rewrites nobody chose.

THE COMPARISON RULE. The CEO, on the read-diet metric: "there should be a
comparison between the previous several days' averages... A number
without comparison means nothing. Then you can also compare and let the
user know that something didn't work right, or you messed up in one way
or another and somehow token usage was high, or maybe it was low (which
is good)." So the sheet writes a DAILY LINE file - one line per active
day: weighted (raw) | vs the previous 7 active days | top pillar | cache
misses | reads whole (big) / section, share | VERDICT - and the verdict
names the reason: CHECK when spend is 30% over the prior average, or
misses / heavy whole-file reads run at twice it, or the section-read
share drops 20 points; LOW spend when 30% under (good); normal otherwise;
today's line marked partial. The standup digest prints the tail as THE
BUDGET block so the cost of a day is seen the next morning, and a CHECK
verdict is relayed to the CEO verbatim - it is the manager's own report
card. Reference: the kit's usage_report.py (weighted(), daily_lines(),
--quiet) and standup.py (print_budget); the checkpoint fingerprint
ignores the sheet's outputs so the refresh never counts as work.

See also: The usage sheet (above) | THE SPREADSHEET RULE (below) | WIKI_METHOD.md (the read diet + the output diet) | HOOKS_METHOD.md Tier 2c (the diet guard)

## THE SPREADSHEET RULE (Mazhron's ask 2026-09-10 - any sheet a human opens)
Tags: process, lessons | A CSV cannot carry formatting; a sheet meant for human eyes ships as .xlsx with frozen header, separators, bold ruled totals

The origin CEO opened the usage CSV in Excel and asked for four things that
no CSV can carry: the header row FROZEN so labels stay in view while
scrolling; every token/count column formatted as a Number with the
thousands separator (Format Cells > Number, 1000 separator); a TOTAL row
in line UNDER the last record of each period (day, week, month, all) with
the averages beside it in their own columns, the totals BOLD; and a THICK
bottom border under each total so the eye finds the split into the next
period. "I want future Rootstock users to have their Claude automatically
do this when their Claude builds it." So it is a rule: when a script
produces a sheet a person will open (usage, metrics, progression, any
ledger export), it ALSO writes an .xlsx twin with exactly that shape - the
CSV/TXT stay for grep and git diffs, the .xlsx is what the human opens.
Mechanics that worked (openpyxl, pip): `ws.freeze_panes = "A2"`;
`cell.number_format = "#,##0"` on every count column ("#,##0.00" for
money); the TOTAL row appended LAST in its period block, `Font(bold=True)`
on every cell of it and `Border(bottom=Side(style="thick"))`; per-row
totals + averages in the last two columns (total_tok / avg_tok) so a
model's or tool's average sits on its own line, not only in the totals;
an auto-filter on the header; the dependency recorded in the workstation
inventory + survey the same batch (THE WORKSTATION RULE). When the
library is missing the run must still write the CSV/TXT and SAY the
.xlsx was skipped - never crash a ledger run over formatting.
Reference: Everwood's tools/usage_report.py (write_xlsx / _xlsx_sheet).
See also: the usage sheet (section above); WORKSTATION_METHOD.md (the
dependency write-back); REPORTING_METHOD.md bootstrap step for the sheet.

## Evidence this pays (Everwood, the origin project, day one of the method)

The FIRST full baseline through the new runner caught, in one afternoon:
a live-gameplay regression that had silently shipped weeks earlier (half the
off-screen world's insect ecology frozen - found because a routine sweep
finally ran the right test), a parser defect in the runner itself, and a
test still calibrated to a design number the owner had changed versions ago.
Each fix is a readable flip in the ledger. None of it was findable from chat
history, because chat history is not a ledger.

## Bootstrap steps for a new project

1. Create the runner script the day the FIRST repeatable thing exists (one
   test is enough); create docs/history/ beside it.
2. Encode groups/laws in the runner as they are learned - a flake's
   post-mortem always ends with a new law line in the script.
3. Record the full baseline; commit ledger + runner together.
4. Wire every later probe/report script to append to its own ledger.
5. When delegating (SUBAGENT_METHOD.md), briefs for scripted work are one
   line; the employee runs the script and reports its output verbatim.
6. Never prune a ledger; if one grows huge, start a dated continuation file
   and leave a pointer - history is the product.

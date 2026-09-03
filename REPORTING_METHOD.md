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

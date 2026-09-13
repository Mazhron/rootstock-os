# The Intent Method (portable: the intent discipline, for any project)

PORTABLE FILE: an architecture, not a project. Hand it to any Claude (or any
capable agent) at the start of any project alongside its siblings
(WIKI_METHOD.md, SUBAGENT_METHOD.md, REPORTING_METHOD.md, WORKFLOW_METHOD.md)
and say "set this up". Nothing here assumes a game, a language, a team size,
or which model manages - never assume today's manager is tomorrow's; this
file speaks of "the manager" and "the owner" throughout, not any one name.

THE PROBLEM IT KILLS: a Claude that follows rules without knowing their WHY
re-derives the reasoning every time a new case doesn't quite match the old
one, and re-asks questions the owner already answered once. Ledgers
(REPORTING_METHOD.md) remember RESULTS; the registry (WORKFLOW_METHOD.md)
remembers ORDER; nothing remembered REASONS. This file is for the reasons,
and for measuring - honestly, with real data - whether Claude's reading of
what the owner wants is actually converging on it.

Search keys: intent, why, reasons, rationale, purpose, what did the owner
mean, agreement rate, correction ritual, feedback loop.
See also: INTENT.md (a project's instance - read it for the format);
tools/intent_log.py, tools/intent_report.py, tools/correction_log.py,
tools/systems_audit.py; REPORTING_METHOD.md (the ledger rules this method
reuses); SUBAGENT_METHOD.md (who states an intent and when); WORKFLOW_METHOD.md
(the registry that names where a rule lives).

## Why intent: knowing the reason beats knowing the rule
Tags: intent, design | Understanding why a rule exists lets Claude apply its reasoning to a new case; knowing only that a rule exists does not

The method exists because of one example the owner gave when asking for it:
"It's not as important that you know to make looping scripts because you
were told to, it's almost more important that you understand we make
looping scripts because 1.) It decreases your token usage, 2.) It's done
the same every time and very structured, 3.) It's something that triggers
without asking." A Claude that only knows THAT scripts get looped will
follow the letter of the rule and miss a new case that the same three
reasons plainly cover. A Claude that knows WHY can extend the rule itself,
correctly, without asking. That is the entire bet of this method: capture
reasons once, in the owner's own words, and every future reader - manager,
employee, or auditor - inherits the judgment, not just the instruction.

## The intent file: one project file, one section per ruling
Tags: intent, architecture | INTENT.md holds one section per ruling with fixed fields; it grows incrementally and a missing section is the question to ask

Each project keeps ONE file, INTENT.md, at its root. It holds one section
per ruling - a decision, a law, a standing instruction - and nothing else.
Each section carries four fields, in this order:

- ASKED: the owner's prompt, verbatim. Never paraphrased - the whole point
  of the file is the owner's actual words, not a manager's summary of them.
- WHY: the owner's reasons, verbatim where the owner numbered them. If the
  owner gave three numbered reasons, the section holds exactly those three,
  numbered the same way.
- GENERALIZES TO: the manager's own reading of what the reasons reach
  beyond the specific case that raised them, explicitly marked as the
  manager's reading (never blended with the owner's words above it).
- LIVES IN: the law, script, or file that actually carries the rule day to
  day - a pointer, not a duplicate, so the rule has one true home and
  INTENT.md carries only its reason.

The file follows the same wiki conventions as everything else (WIKI_METHOD.md):
searchable `## ` headings naming what a search would look for, a `Tags:`
line on hard-won sections, and `See also:` cross-references so a hop needs
no search. It GROWS INCREMENTALLY - a ruling's intent is captured the day
the ruling is made, or the day a correction reveals it - never a backfill
sweep of old decisions nobody asked to revisit. A brief for a delegated
task pastes the relevant section straight in, so an employee starts with
the reason already in hand. And the reverse holds too: a section that
DOES NOT EXIST YET, when a question like "what did the owner mean by this?"
fires, is itself the signal to stop guessing and ask the owner - the answer
then gets filed the same batch.

## The comparison ledger: claim, then verdict
Tags: intent, process | A claim records the manager's reading before building; a verdict records the owner's truth when it's known, naming its source so self-judged agreement never inflates the rate

Before building anything nontrivial, the manager logs its OWN reading of
the ask as a CLAIM (`tools/intent_log.py --claim --actor <name> --task
"<3-8 words>" --mine "<the reading>"`) - written down before the work,
so it can't be quietly rewritten after the fact to match what shipped.
An employee does the same in miniature: it states its own reading in its
delegation stamp as an `INTENT:` line, and the manager logs that claim
with the employee's model as the actor, never folding it into its own.

When the owner's actual intent becomes known - stated outright, revealed
by a correction, or judged by the manager from how the work landed - the
claim RESOLVES with a verdict:

- SAME: the reading matched; nothing was rebuilt or adjusted.
- SIMILAR: matched in substance; a detail differed and was adjusted
  without a rebuild.
- DIFFERENT: a correction or rebuild was needed.

Every resolution also names its SOURCE: `stated` (the owner said so
directly), `correction` (a `/correct` ritual revealed it), or `inferred`
(the manager judged it with no explicit words). Inferred verdicts are
counted separately in every report, on purpose - a Claude grading its own
homework must never be allowed to quietly inflate its own agreement rate.
The log (`docs/history/intent_log.txt`) is append-only: a resolve appends
a RESOLVED line that supersedes the claim's PENDING state, and the newest
line for a given id is the one that counts. Nothing is ever edited in place.

## The correction ritual: a fix plus the reason it was needed
Tags: intent, lessons | A correction records the owner's words verbatim, resolves the matching claim DIFFERENT by itself, then asks for the intent while the mismatch is still fresh

The owner described the ritual this way: "Lets pretend I ask you to do
something. You build it, and it's wrong. I send you a correction skill.
You then inquire: What about the last thing I did needs correcting? The
user explains. You mark that down and prepare to fix the thing that needs
correcting, then you would ask 'What was the intent?' firing off the intent
immediately after. These two create a feedback loop."

Mechanically: the `/correct` skill asks "What about the last thing I did
needs correcting?", records the answer verbatim with `tools/correction_log.py
--record` (never paraphrased - the owner's exact words are the evidence).
If the correction names the intent claim it falsifies, that call alone
resolves the claim DIFFERENT with source `correction` - the hardest
evidence the comparison ledger ever gets, and it is never left to be
remembered separately. Then, while the mismatch is still fresh, the
`/intent` skill asks "What was the intent?" and files the answer into
INTENT.md as a new or amended section. Only after both of those does the
fix ship, closed out with `tools/correction_log.py --fixed`. A correction
is never JUST a fix - it is evidence about a misread intent, logged before
the fix is allowed to erase the trail.

## The report: real data, on a cadence, from a script
Tags: intent, economy | The report exists for the same three reasons every looping script does - it is a scorecard the loop produces on its own, not a status the manager has to remember to give

The owner's reasons for wanting real numbers instead of a feeling: "we 1.)
Want to have real data, 2.) We want to compare past to present, 3.) We want
to know if we are improving, staying the same, or declining because each
one of those will tell us something about our feedback loop." And the
reasons this has to be a script, not a habit: "The Intent there is 1.) It's
the same every time, 2.) It's cheap and costs no tokens, 3.) it's
structured and we don't need to remember to call it by adding it to the
loop we already have."

`tools/intent_report.py` is that script. It reads the intent log and the
correction ledger and regenerates, whole, every run: a txt summary for
Claude and employees (all-time, the last window vs the window before, the
trend verdict, then day/week/month tables per actor), a csv for a human,
and an xlsx twin (THE SPREADSHEET RULE from REPORTING_METHOD.md - frozen
header, bold totals - skipped quietly, never fatally, when the library
isn't installed). It appends one line per run to a runs ledger so the
trend itself has history. It calls the trend IMPROVING, DECLINING, or
STEADY by comparing agreement across two windows, with a minimum-resolved
floor below which it says "n/a" rather than call a coin flip a trend. The
exact thresholds (points of movement, minimum resolved claims per window)
live in the script as constants - they are the owner's to tune, never the
manager's to loosen on its own judgment. The script runs from the same
metrics loop every other recurring report runs from, for the same reason
looping scripts exist at all: it costs no tokens, it is identical every
time, and it fires without anyone having to remember to ask for it.

## The systems audit: the loop measured, but never thought
Tags: intent, process | A ledgered, cadence-proposed audit in four read-only lanes returns proposals only; the owner decides what, if anything, changes

The owner's ask that started this: "Do we have anything in our loops that
audits our ledgers, new features, etc. and considers new options to
increase efficiency (without losing context), decrease token usage
(without losing efficiency or context), add txt data structures for
increased knowledge, etc?" The honest answer was no - every ledger measured
something, but nothing ever stepped back and asked whether the measuring
itself was still the right shape.

`tools/systems_audit.py` is that step-back, run as a handful of READ-ONLY
employees across four lanes: TOKENS (the usage sheet, big reads, the diet),
PROCESS (workflows, skills, hooks, what got done by hand instead of by
script), KNOWLEDGE (the wiki, the ledgers, what a new data structure would
capture), and FEATURES (what shipped since the last audit, and whether any
of it should have been a script, a hook, a data file, or a cheaper model).
Every lane returns PROPOSALS only - nothing is applied by the audit itself,
ever; the owner decides what, if anything, changes. A finished audit is
ledgered (`--record`), and a trend-watching script proposes the NEXT audit
once enough day files or enough elapsed time has piled up since the last
one - the audit is on a cadence, not a whim, but the cadence only proposes,
it never fires the audit unasked.

## The laws
Tags: intent, process, lessons | The discipline in seven short rules, none of them optional and none of them automatic

1. A claim is logged before building, not reconstructed afterward to match
   what shipped.
2. A verdict is recorded the moment truth is known, and it always names
   its source - stated, correction, or inferred - so a self-graded verdict
   never passes as owner-confirmed agreement.
3. A correction is evidence, never just a fix: it is recorded verbatim
   before the fix ships, and it resolves its claim by itself.
4. The report is a script living in the loop the project already runs -
   never a status a manager has to remember to compile by hand.
5. Nothing is ever applied by a script in this method. The systems audit
   proposes; the owner decides.
6. Growth is incremental. A ruling's intent is captured the day it is
   made, or the day a correction reveals it - never a backfill sweep.
7. A missing INTENT.md section is not a gap to route around; it is the
   question to ask the owner, on the spot.

## Bootstrap steps for a new project

1. Create INTENT.md the day the first ruling worth remembering is made -
   header (this file's purpose, the wiki-lookup convention) plus that
   first section, in the four-field format above.
2. Copy the four reference scripts (intent_log.py, intent_report.py,
   correction_log.py, systems_audit.py) and adapt their paths and any
   project-specific ledger locations; keep their docstrings as the
   canonical spec of the log format and the verdict definitions.
3. Add `intent_report.py` to the project's recurring metrics loop, and
   carry its three trend rules (a minimum-resolved floor, a two-window
   comparison, IMPROVING/STEADY/DECLINING) as tunable constants the owner
   can move, not the manager.
4. Add the `/intent` and `/correct` skills so the correction ritual runs
   the same way every time: what needs correcting, record, what was the
   intent, file it, fix, mark fixed.
5. Add the employee INTENT stamp line to the project's delegation rules
   (its SUBAGENT_METHOD.md instance) so every brief states a reading
   before it builds, the same as the manager does.
6. Add one index line for INTENT.md and one for this file to the
   project's core file, alongside the other portable-method index lines.

Search keys: intent method, intent discipline, why behind a rule, claim
and verdict, correction ritual, agreement rate, systems audit, feedback
loop.
See also: INTENT.md (a live instance of this method, read it for the exact
format); tools/intent_log.py; tools/intent_report.py; tools/correction_log.py;
tools/systems_audit.py; REPORTING_METHOD.md; SUBAGENT_METHOD.md;
WORKFLOW_METHOD.md.

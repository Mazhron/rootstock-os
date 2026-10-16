# One task, two users: a worked example of where the tokens go

PURPOSE: A step-by-step, modeled walk-through of one ordinary task done by
  a user without Rootstock and a user with it, every step priced in tool
  calls, tool results, output, cache reads and cache writes, so a person or
  a reading Claude can see WHICH piece of the kit saved WHICH tokens and
  why the saving compounds across turns and sessions.
INTENT: The owner's ask (2026-10-15): "I feel it's very important for people
  and even another AI to understand" how the processes save tokens, not
  only the ledgered totals; the receipts in the README say how much, this
  file says where and why, one step at a time.

Search keys: worked example, token example, where the tokens go, two users,
with and without rootstock, cache read, cache write, output cost, context
compounds, lesson saved, workflow saved, section read saved, trust the
ledger saved, digest saved, weighted tokens, price weights, modeled not
metered, token walkthrough, how rootstock saves tokens, for an AI reader.

See also: README.md "The seven ways it saves tokens" (the map this example
walks), "The receipts" (the metered numbers), "What it saves, concretely"
(the habit table); LESSONS.md (the lesson law); WORKFLOW_METHOD.md (the
process registry); WIKI_METHOD.md "Read cheap" and "Size before you read";
REPORTING_METHOD.md "Trust the ledger"; HOOKS_METHOD.md (the prompt hook
that names a matching lesson); the usage sheet in reference tools/
(usage_report.py, the weights this file prices with).

## What this is, and what it is not

This is a MODEL, not a meter. The metered numbers live in the README's
"The receipts" (44 days, 7,573 requests of the origin project). This file
takes one ordinary task and prices it twice, step by step, with:

- the origin project's measured averages for file sizes: a whole-file read
  averaged ~35k tokens before the wiki diet, a section read 1-2k after;
- the API's own price ratios, which the kit's usage sheet meters with:
  fresh input x1, cache write x1.25, cache read x0.1, output x5;
- one rule of the harness that explains everything else: EVERY turn
  re-reads its whole prefix (the conversation plus every tool result so
  far) from cache. Context size is therefore the number that matters, and
  anything that enters context is paid again on every later turn.

Within a session everything is cached (the five-minute cache), so the
fresh-input column rounds to zero and is left out.

## The task, the same for both users

Day two of a project. Add a headless self-test for a new Undo button and
get it passing. The trap, a real one from the origin project: a test that
clicks the screen fails headless and passes in a window; the fix is to go
through the test runner's own route instead of clicking. User B's project
has already recorded that as a LESSONS.md entry and a WORKFLOWS.md step,
because the lesson advisor hook forced the entry the first time it was
learned. User A's project has nothing recorded, because nothing forced it.

## User A: no kit

A 10k-token CLAUDE.md loads (the common shape: every convention, every
path, every rule, in one file), and the user types ~1.5k tokens of "where
we were yesterday" by hand. Context opens at 11k.

| Step | Tool calls | Results in | Output | Cache read | Context after |
|---|---|---|---|---|---|
| 1. Re-orient: scene script and test file read whole | 2 | 42.0k | 0.6k | 12k | 54k |
| 2. Write the test by copying an existing click test | 1 | 0.3k | 1.2k | 54k | 56k |
| 3. Run it by hand, Godot log comes back, FAIL | 1 | 4.0k | 0.5k | 56k | 60k |
| 4. Read the menu script whole to see how autostart works | 1 | 30.0k | 0.8k | 60k | 91k |
| 5. Tweak, run again, FAIL | 2 | 4.3k | 0.5k | 91k | 96k |
| 6. Read the runner script whole, find the test route | 1 | 15.0k | 0.6k | 96k | 111k |
| 7. Rewrite, run via the runner, PASS | 2 | 2.3k | 1.0k | 111k | 115k |
| 8. Re-run the whole green group "to be sure" | 1 | 12.0k | 0.3k | 115k | 127k |
| 9. Summary; nothing recorded | 0 | 0 | 0.8k | 127k | 128k |

Totals: 11 tool calls, 110k of tool results, 6.3k output, 721k cache read,
128k cache write. WEIGHTED: ~263k (writes 160k, reads 72k, output 32k).

## User B: Rootstock

A ~1k pointer core and a ~3k standup digest load. The digest carries both
sides of yesterday's last exchange verbatim, so nothing is retyped. The
prompt hook names the matching lesson before the first tool call. Context
opens at 4k.

| Step | Tool calls | Results in | Output | Cache read | Context after |
|---|---|---|---|---|---|
| 1. Grep WORKFLOWS and LESSONS headings, read one section of each | 4 | 3.3k | 0.5k | 4k | 8k |
| 2. Grep the test file's headings, read one existing test | 2 | 1.9k | 0.3k | 8k | 10k |
| 3. Write the test the lesson's way, first try | 1 | 0.3k | 1.2k | 10k | 12k |
| 4. Run one test group, PASS; the other groups are green in the ledger at this version and are not re-run | 1 | 1.5k | 0.3k | 12k | 13k |
| 5. Ship: commit, ledger line; the stop hook finds no trial and error to record | 2 | 0.4k | 0.6k | 13k | 14k |

Totals: 10 tool calls, 7k of tool results, 2.9k output, 47k cache read,
14k cache write. WEIGHTED: ~37k (writes 18k, reads 5k, output 14k).

The ratio on this one task is about 7x. The tool-call COUNT is nearly the
same (11 against 10): the saving is not fewer actions, it is smaller ones,
and smaller context under every one of them.

## Which piece of the kit took which share

- **The lesson** removed steps 3 to 6 entirely: two failed runs and 45k of
  whole-file reads that then rode on every later turn. The prompt hook put
  the lesson in front of the manager at zero tool cost; the lesson advisor
  is why it existed at all.
- **The workflow** removed the re-derivation of how to run a test: one
  section read of 1.5k instead of a 15k runner script.
- **Section reads** turned 42k of re-orientation into 5k, and because
  context compounds, the cache-read column is 721k against 47k.
- **The digest and the pointer core** replaced the typed re-explanation
  and the 10k CLAUDE.md, so the session opened at 4k instead of 11k and
  the user wrote nothing.
- **Trust the ledger** removed step 8, a 12k log that proved nothing new.
- **The output diet** halved generation, the most expensive column per
  token (x5).

## Where it compounds

- User A's NEXT session starts the same way, because nothing was recorded;
  the trap costs the same again the next time it is met.
- If user A keeps the session open instead of clearing, tomorrow's step 1
  starts at the 128k already there, and the whole cache-read column grows
  by 128k per step. This is the mechanism behind the origin's metered
  numbers: 810-898k tokens re-read PER REQUEST at the marathon peak,
  ~267k on the first cleared days (a 69% cut).
- User B's next session costs about the same 37k, and the lesson is now
  also in the kit for the project after this one.

Multiply the 7x by the number of times a trap recurs and by the number of
sessions that never clear, and the receipts follow. Different tasks give
different ratios; the direction does not change, because every column is
the same arithmetic: a smaller thing entering context, paid fewer times.

## For a reading Claude

If you are the manager of an installed project, this is what each law is
buying when you obey it: grep headings before a read, read the section not
the file, check LESSONS.md and WORKFLOWS.md before deriving, trust a green
ledger line, keep replies short, and checkpoint then clear instead of
compacting. None of these is etiquette. Each one is a column in the tables
above.

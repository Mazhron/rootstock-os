# LESSONS - the one-right-way book (judgment, not steps)

PURPOSE: One entry per task shape: THE ONE RIGHT WAY first, then what was
  tried, why it failed and what to do instead, then nuance headlines as they
  accumulate, so a future session does the correct thing first instead of
  repeating trial and error.
INTENT: Mazhron 2026-09-20: "so in the future you don't make the same
  mistakes and just do the one correct way first? Then, if that fails, add
  nuanced headlines to that to describe what you did to avoid similar
  pitfalls again and adapt what works for A to work for B" and "we want
  something to push you to write what you learned, as well as push you to
  add to the knowledge base, create new txt files, add to current ones ...
  we want to prevent re-inventing the wheel".

THE LESSON LAW (Mazhron 2026-09-20). WORKFLOWS.md is the steps; this file
is the judgment. Before any task, `Grep "^## " LESSONS.md` the way
WORKFLOWS.md is grepped, and read the entry whose shape matches (the
prompt hook names matching entries by itself when a prompt's words hit an
entry's Keys line). When the Stop hook says LESSON ADVISED, ADVISED MEANS
DO IT: before that turn ends, write or amend the entry for the task shape,
or put the fact in its topic file under a Tags line, or say in one line
why there is no lesson. A lesson is written the moment it is learned, in
the same batch, never in a later pass. Nothing here is deleted: a lesson
that stops being true is marked SUPERSEDED with the date and the reason.

ENTRY SHAPE (each `## ` heading is the task shape, in the words a prompt
would use):
- `Tags: lessons, <area> | <brief>` so KNOWLEDGE_INDEX.md lists it.
- `Keys: a, b c, d` - the terms the prompt hook matches against a prompt
  (a multi-word key hits only when all its words appear).
- THE ONE RIGHT WAY: the thing to do first, one to three lines.
- TRIED / FAILED BECAUSE / DO INSTEAD bullets, one per pitfall, dated.
- NUANCE lines ("when A differs from B") as they accumulate.
- See also: the topic file that holds the detail (one home per fact; the
  lesson is the judgment, the detail stays where it lives).

Lint + ledger: `python tools/lesson_log.py --check` (run_all check group;
docs/history/lesson_runs.txt); `--match "<prompt>"` shows what the prompt
hook would say; `--scan` shows the signals the Stop hook saw.

Search keys: lessons, the one right way, tried failed do instead, pitfalls,
lesson advised, trial and error, knowledge capture, judgment not steps.
See also: WORKFLOWS.md (the steps); docs/index/laws.md "The lesson law";
tools/lesson_log.py; tools/hooks/lesson_advisor.py (the Stop twin);
tools/hooks/prompt_gauge.py (the match line); KNOWLEDGE_INDEX.md.

## Brief a numbers or balance task (an envelope for an employee)
Tags: lessons, delegation, balance | Read the existing spread before briefing a numbers task and stay inside it; ask for the band when there is none
Keys: brief, employee, numbers, balance, envelope, lanes, stats, spread, retune, tune, species numbers, propose values, band

THE ONE RIGHT WAY: before writing the brief, read the existing spread of
the same stat on the species (or upgrades) that already carry it, state
that band in the brief as the envelope, and tell the employee to propose
inside it. If nothing carries the stat yet, ask Mazhron for the band
first, one question, before anyone proposes a number.

- TRIED (2026-09-20, T-0920-WET-1): the manager's brief gave a wide
  envelope (lid to 0.4, anchor to 0.5) for fourteen wetland species.
  FAILED BECAUSE: lid and anchor multiply, so one mature flower cut a
  5x5's evaporation by 63 percent; the grasses and plants already laned
  sat at a tenth of that. Mazhron read the table and pulled every number
  to the grass and plants spread (intent I0048, DIFFERENT, stated).
  DO INSTEAD: the envelope is the existing spread, not a round number;
  the band goes in the brief in the same sentence as the ask.
- NUANCE: a stat that multiplies with a sibling (lid x anchor, cost x
  count) is judged by the product on one cell, not by each value alone.

See also: docs/systems/flora.md "THE LANES SPREAD"; SUBAGENTS.md (the
brief shape); INTENT.md (I0048); WORKFLOWS.md "Delegate a task to an
employee".

## Write a guard that names forbidden verbs or calls
Tags: lessons, process | A guard that pattern-matches deletion verbs will refuse its own docstring and its own wiki row; write the prose first, then the pattern, and reword rather than route around
Keys: guard, hook, refuse, deny, forbidden, delete verbs, pattern, preserve guard, bash guard, write a hook

THE ONE RIGHT WAY: write the guard's docstring, its wiki table row and its
README paragraph BEFORE the pattern goes live, or exempt prose files
(.md .txt .rst .csv .html) from the content check in the same edit. When
the guard refuses its own author, reword the text or refine the pattern;
never bypass the guard to land the edit.

- TRIED (2026-09-10, preserve_guard.py): the deletion-call check went live
  with a docstring that named the call it bans. FAILED BECAUSE: the guard
  read its own docstring as a deletion call, twice (the docstring, then
  the tooling.md table row). DO INSTEAD: exempt prose files from content
  checks and describe the banned call in words ("the remove call"), not
  code, inside a script that the guard also reads.
- NUANCE: a PreToolUse guard fires on the settings.json edit that wires it
  (the live watcher), so pipe-test with synthesized stdin first, then
  wire, then trigger once for real.
- NUANCE (2026-09-20, session_end.py): a selftest that builds a sandbox
  repo and removes it afterwards is a script that deletes; the guard
  refused the Write. DO INSTEAD: build the sandbox with tempfile.mkdtemp,
  print its path, and leave it for the OS - a test never needs to clean
  up to be a test.

See also: docs/systems/tooling.md "The hooks"; WORKFLOWS.md "Add or
change a harness hook"; HOOKS_METHOD.md.

## Write an engine resource file (.tres, .tscn) from a script or shell
Tags: lessons, gotchas | A shell write puts a BOM or CRLF in a .tres and Godot's parser fails; write engine resources from Python with utf-8 and newline "\n", never from PowerShell redirection
Keys: tres, tscn, resource file, write species file, species files, data/species, powershell write, redirect, bom

THE ONE RIGHT WAY: edit or write a .tres/.tscn from Python (or the Edit
tool) with encoding utf-8 and newline "\n"; the shell guard refuses a
shell redirect into a .tres for this reason. A hand-written .tscn with a
typed node export needs the node_paths entry in its header or the export
silently stays null. Run `--import` headless after any new asset.

See also: docs/index/gotchas.md "Gotcha: writing .tres from PowerShell",
"Gotcha: hand-written .tscn node exports"; .claude/rules/game-code.md.

## Write a long file or script through the shell (heredocs on this Windows setup)
Tags: lessons, process | A long quoted heredoc through the Bash tool dies with "unexpected EOF while looking for matching quote" past roughly a hundred lines; write files with the Write tool and put edit scripts in the scratchpad, then run them
Keys: heredoc, bash tool, write file, long script, edit script, python script, shell write, cat eof, unexpected eof, scratchpad

THE ONE RIGHT WAY: a new file of any length goes through the Write tool;
a multi-file edit goes into a Python script written to the scratchpad
with the Write tool and run with one Bash call (assert each replacement
count is 1 so a missed target fails loudly). A heredoc is for ten lines
or fewer.

- TRIED (2026-09-20, building the lesson loop): a 330-line script and a
  70-line edit script as `python - <<'EOF'` heredocs. FAILED BECAUSE: the
  shell reported "unexpected EOF while looking for matching quote" at
  lines 148 and 73 both times; a 118-line markdown heredoc had worked
  minutes earlier, so the cliff is size plus content, not size alone.
  DO INSTEAD: Write tool for the file, scratchpad script for the edits;
  both landed first time.
- NUANCE: the shell guard refuses shell writes into settings.json in any
  case, so a settings edit is always the Edit tool after a Read.

See also: WORKFLOWS.md "Add or change a harness hook" (the settings.json
rule); tools/hooks/bash_guard.py (rule 5).

## Harden a guard against a public incident (audit a safeguard)
Tags: lessons, process | Write the incident's exact shapes as probe cases before reading the guard; a selftest only proves the shapes its author imagined
Keys: guard, hook, harden, audit, safeguard, incident, catastrophe, deletion, robust, preserve guard, prevent this, pitfall

THE ONE RIGHT WAY: take the incident apart into the literal commands and
files it used (what wrote the deleter, what ran it, what it walked, what
it touched), write each as a pipe-test case BEFORE reading the guard's
code, run them all, and only then read the guard to see why each ALLOW
happened. Fix by shape, add every probe to the selftest, and write the
guard's prose (docstring, wiki row, kit tier text) with the verbs split
or reworded so the guard never refuses its own author.

- TRIED (2026-09-20, preserve_guard): trusted the 35-check selftest as
  proof of coverage. FAILED BECAUSE: every check was a shape the author
  had imagined; the incident's shape (a remover written to Temp through
  a heredoc, run in a LATER command) sat in the one exemption the guard
  had - a cat heredoc body - and in the one thing it never looked at -
  a script file being executed. Fourteen of twenty-nine probes passed
  straight through. DO INSTEAD: probe with the incident first; the
  selftest is the floor, not the ceiling.
- TRIED (2026-09-20): scanning every script a command NAMES. FAILED
  BECAUSE: grep, cat and diff name scripts too; reading is not running.
  DO INSTEAD: scan a script only when it starts its command segment or
  a runner word (python, pwsh, bash, node, &, timeout ...) precedes it.
- TRIED (2026-09-20): scanning a tracked script whole. FAILED BECAUSE:
  three committed exporters unlink their own temp file, so every run of
  them would have needed a grant. DO INSTEAD: a tracked script is judged
  on its uncommitted ADDED lines only; an untracked one on its whole
  body.
- NUANCE: a guard that scans scripts scans ITSELF while it is modified
  and uncommitted; two-letter helper names in its selftest (the verb
  aliases) and regex sources that contain their own verbs read as
  deletion shapes. Name helpers with four letters, write verbs in
  pattern sources as r[m] / r[i] so the source never matches itself,
  and split string literals ("rm " + "-rf").
- NUANCE: a guard must never crash the turn, but "never crash" was
  implemented as "allow on exception" - fail open. A crude substring
  fallback that refuses on the obvious verbs keeps both.
- NUANCE (Windows): os.walk(followlinks=False) and os.path.islink() do
  NOT stop at a directory junction; a walker deletes through it into
  the target. No script deletes here, so the guard, not the walker, is
  the defence; a script that only walks is fine.

See also: tools/hooks/preserve_guard.py (docstring: HARDENED
2026-09-20); docs/systems/tooling.md "The hooks"; WORKFLOWS.md "Delete
something"; HOOKS_METHOD.md Tier 2d.

## Cut and wire new art from a sheet
Tags: lessons, art | Montage the slices and look at the picture before wiring a single species; some sheets interleave stages and a bad grid is only visible as an image
Keys: slice, sheet, sprite, art, cut, wire art, montage, growth stages, sprites, spritesheet, animal art, plant art

THE ONE RIGHT WAY: slice, then build one montage of every cut cell and
read it as an image, then wire. A grid cut that looks right in numbers
can interleave stages or catch a black border; the montage shows it in
one glance and the wiring is not redone.

See also: ART_METHOD.md; docs/systems/art-pipeline.md "Gemini growth
sheets"; WORKFLOWS.md "Cut and wire new creature or plant art".

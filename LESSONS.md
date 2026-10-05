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
brief shape); INTENT.md "A new stat band starts inside the existing
spread" (I0048); WORKFLOWS.md "Delegate a task to an
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
Keys: tres, tscn, resource file, write species file, species files, data/species, powershell write, redirect, bom, project.godot, comments stripped, editor rewrote

THE ONE RIGHT WAY: edit or write a .tres/.tscn from Python (or the Edit
tool) with encoding utf-8 and newline "\n"; the shell guard refuses a
shell redirect into a .tres for this reason. A hand-written .tscn with a
typed node export needs the node_paths entry in its header or the export
silently stays null. Run `--import` headless after any new asset.

- NUANCE (2026-09-21, project.godot): the Godot editor rewrites
  project.godot whenever it saves settings (Mazhron playing in the
  editor is enough): every `;` comment is stripped, sections are
  reordered, and lines equal to the engine default are dropped
  (renderer/rendering_method went, then came back on restore). A
  comment there is a note that lives until the next editor save. Its
  durable home is the topic file (the FRAME LAW in GODOT_FIELD_NOTES.md,
  testing.md and ui.md; the no-physics law in lag-and-latency.md);
  project.godot carries the values. When the editor has rewritten it: `git show
  <last-good>:project.godot` with the version line carried forward,
  never a hand re-type, and commit it as its own batch so the diff
  shows only the restore. The editor keeps its in-memory copy, so a
  version bump written while it is open shows only after a restart.

See also: docs/index/gotchas.md "Gotcha: writing .tres from PowerShell",
"Gotcha: hand-written .tscn node exports"; .claude/rules/game-code.md.

## Write a long file or script through the shell (heredocs on this Windows setup)
Tags: lessons, process | A long quoted heredoc through the Bash tool dies with "unexpected EOF while looking for matching quote" past roughly a hundred lines; write files with the Write tool and put edit scripts in the scratchpad, then run them
Keys: heredoc, bash tool, write file, long script, edit script, python script, shell write, cat eof, unexpected eof, scratchpad, powershell syntax, wrong shell, exit 2, select-object, call operator

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
- NUANCE (2026-09-30, the same family the other way around): PowerShell
  syntax sent to the Bash tool (`& "exe"`, `Select-Object`) dies with
  exit 2 just as a bashism would in PowerShell; the two shell tools each
  take only their own syntax, so match the tool to the syntax BEFORE
  writing the command, and on an exit-2 with no useful output reread the
  command for the other shell's idioms first.
  DO INSTEAD: Write tool for the file, scratchpad script for the edits;
  both landed first time.
- NUANCE: the shell guard refuses shell writes into settings.json in any
  case, so a settings edit is always the Edit tool after a Read.
- NUANCE (2026-09-20 evening, a 180-line heredoc died the same way with
  "here-document delimited by end-of-file"): reading this file's INDEX
  at session start did not stop the repeat; the entry applies at the
  moment of writing. The rule is mechanical: an edit script over ten
  lines is the Write tool + scratchpad, before the first attempt, never
  as the fallback after the heredoc fails. (Python parses the whole
  script first, so the failed heredoc applied nothing - check with
  `git status` before rerunning, then rerun the scratchpad script.)
- NUANCE (2026-09-21, the line-gate road): a SHORT heredoc is not safe
  either when the text carries a backslash at a line's end (GDScript
  line continuations). The Bash tool's own layer turns the doubled
  backslash into one before Python sees it, so backslash-newline inside
  the Python string becomes a line join: the OLD text never matches
  (count 0) and a NEW text that lands writes the two lines as one, a
  silent parse error in the .gd file. The Write tool passes the script
  verbatim, so any edit whose old or new text holds a backslash goes
  through a scratchpad script, whatever its length. Add to the same
  rule: the .gd files here carry mixed CRLF and LF, so an edit script
  reads with newline="" and normalises CRLF to LF before matching
  (git stores LF; the working copy's CRs are noise).

- TRIED (2026-09-21, the C0001 doc edits): a 120-line Python edit script
  in a quoted heredoc followed by a second command on the same line whose
  arguments carried apostrophes ("it's", "Classic's"). FAILED BECAUSE:
  bash reported "unexpected EOF while looking for matching `'" and ran
  nothing, so no edit landed and the failure had to be diagnosed twice.
  DO INSTEAD: a multi-line edit script is a .py file in the scratchpad,
  written with the Write tool and run by path; commands with quoted
  prose go in their own call, never after a heredoc.
- NUANCE (2026-09-30, the README audit's four lane briefs): an EMPLOYEE
  BRIEF is never a file at all. Four ~60-line briefs went into a heredoc
  Python script meant to write them to the scratchpad, and died on an
  apostrophe inside a quoted question ("Does it check the app I build?")
  plus a stray `$VAR` on the same line. FAILED BECAUSE: the detour added
  a shell layer and a file layer to text whose only reader is the Agent
  tool's prompt field. DO INSTEAD: compose the brief in the Agent call
  itself (the shared preamble pasted into each of the four prompts);
  the scratchpad is for scripts that run, not for prose that is read
  once. Same rule for a note to the other workstation or a lesson: the
  Write or Edit tool, never a shell write.
- TRIED (2026-09-21 evening, the records script): the same 120-line
  quoted heredoc ALONE in its call, with only `echo written` after it,
  written under the auto-mode instruction to prefer Bash. FAILED
  BECAUSE: bash still reported "unexpected EOF while looking for
  matching `'" at the heredoc's last line; the body carried apostrophes
  in prose and a `%s`-formatted string, and the Bash tool's layer does
  not deliver a long quoted heredoc intact whatever follows it. DO
  INSTEAD: the auto-mode "prefer Bash" instruction does not cover this
  case; a scratchpad script is the Write tool, full stop, and the first
  attempt is the Write tool. Two identical failures a day apart is the
  proof.

See also: WORKFLOWS.md "Add or change a harness hook" (the settings.json
rule); tools/hooks/bash_guard.py (rule 5).

## Write a self-test for a shop purchase (a FAIL that was the test's own assumption)
Tags: lessons, testing | A test that buys one level compares against the level BEFORE the buy, never against 1: profiles carry meta start levels, and the same process may run another test's fixture first; GDScript maxi/mini take exactly two arguments
Keys: self-test, MEMTEST, REBIRTHTEST, level_of, meta floor, start level, buy one level, maxi, mini, too many arguments, parse error, FAIL then PASS, test assumption

THE ONE RIGHT WAY: read the level first (`var lv0 := level_of(id)`), buy,
then assert `level_of(id) == lv0 + 1`; pick the fixture line by its data
shape (gated, no requires, a biomass category), never by a name whose
start level you assume. A compound assertion that fails gets split into
named parts with one detail print before the second run, not guessed at.
maxi / mini are two-argument: nest them.

- TRIED (2026-09-21, the line-gate road): asserted the gated line ended at
  level 1 after one buy. FAILED BECAUSE: the fixture (bushes_broad_leaves)
  carries a meta start level of 3 in the test profile, so the buy landed
  on 4; every other part of the step was true. DO INSTEAD: lv0 + 1, and
  the split-and-print step the first time a compound assertion fails.
- TRIED (same batch): `maxi(a, b, 0)` in UpgradeData. FAILED BECAUSE: the
  parse error broke the whole resource script, so MEMTEST read MISSING and
  a REBIRTHTEST check that only touches UpgradeData read false, a failure
  two tests away from its cause. DO INSTEAD: `--verbose` on the first
  MISSING (the parse error is the first SCRIPT ERROR line); nest maxi.

See also: docs/systems/testing.md (the roster); WORKFLOWS.md "Run tests
or probes".

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
Keys: slice, sheet, sprite, art, cut, wire art, montage, growth stages, sprites, spritesheet, animal art, plant art, resolution, lower resolution, pixelated, blurry, art_scale, chunky

THE ONE RIGHT WAY: slice, then build one montage of every cut cell and
read it as an image, then wire. A grid cut that looks right in numbers
can interleave stages or catch a black border; the montage shows it in
one glance and the wiring is not redone. Pick the sliced mature height
FROM the on-screen size, not from one flat number: source height x
art_scale x zoom_max must not exceed the source height (nearest filter),
and the cut height should be the same multiple of art_scale as the
category it sits beside.

- TRIED (2026-09-20, the 24-flower batch): every category cut to
  TARGET_MATURE_H 72, then flowers wired at art_scale 0.75 beside
  plants at 0.5 and grass at 0.3. FAILED BECAUSE: the same 72 px were
  stretched 1.5x to 2.5x further on screen than the neighbours', past
  native at zoom 3.0, and 0.75 under a nearest filter drops one pixel
  in four (ragged petal edges) where 0.5 drops every other one cleanly;
  Mazhron saw the flowers as "lower resolution than the small plants
  and grass". Ten times the detail had been in the 800 px panels. DO
  INSTEAD: a per-category mature height in extract_gemini_sheets.py
  (FLOWER_MATURE_H 108 beside TARGET_MATURE_H 72; `--only <category>`
  re-cuts one family), art_scale set so every category lands at the
  same rendered height per source pixel, and the montage compared at
  in-game scale (resize NEAREST by art_scale, then magnify) before
  wiring. Landed 2026-09-21 as v0.99.24: flowers 108 px at 0.5, same
  screen size, montage clean, flora green, build soak PASS.
- NUANCE: 0.5 is the clean factor under the nearest filter (every other
  pixel); a category that must render bigger gets a taller CUT, never
  a bigger art_scale.
- NUANCE (2026-09-26, the flair sheets): joining the PARTS of one decal
  (a flower head above its stem) is a PIXEL-distance question, never a
  bounding-box one. Merging boxes that overlap or sit near each other
  chains transitively - one dense row of a scatter sheet collapsed into
  a single 24-item mega-piece the montage caught in one glance. DO:
  dilate the alpha mask by half the join gap (MaxFilter) and label the
  DILATED mask, then crop each ORIGINAL component group; the gap that
  joins a stem (8 px) never reaches the neighbouring tuft (30+ px).
- NUANCE (2026-09-25, the wood planks): read the montage for the FILL
  art as hard as for the sprites. The Cherry and Dark Oak plank tiles
  showed a thin white stripe at their edges in the montage; wired as
  they were, drawn dimmed under a window, the stripe was a grey band
  beside the frame that Mazhron had to point at. A generated background
  can carry a white margin: tools/cut_ui_borders.py now trims it
  (trim_white) - a stripe in a montage is never "just the tile edge".
- NUANCE (2026-09-29, the nineteen bushes): a new sheet family breaks
  the slicer in ways only the montage and the blob list show, three in
  one batch. TRIED: the existing reading-order pass. FAILED BECAUSE: (1)
  rows by CENTROID misplace a tall mature plant set beside two stacked
  stages (its centre sits between their rows); (2) the grey-junk filter
  meant for grid lines dropped Brittlebush's silver sprout ("only 6
  blobs"); (3) choosing the N largest blobs BEFORE joining parts let half
  of Scarlet Quince's two-piece twig outrank the sprout, and the sprout,
  now a "fragment", welded onto a later stage (taller than the mature).
  DO INSTEAD: rows by BASELINE (bottom edge); join a plant's parts by
  pixel distance (MaxFilter) FIRST and only then pick the N plants;
  strip thin border rules before dilating; fragments to the nearest BOX;
  and SWEEP the join size across every sheet (5..11 all clean, 13 welded
  two Buttonbush panels) and take the middle. When a count fails, dump
  the blob list (area + bbox) before touching a threshold: it names the
  cause in one read. Landed as panels_from_sheet's baseline_gap mode.
- NUANCE (2026-10-02, the twenty-five trees): the join size is a per-FAMILY
  number, not a slicer constant. The bushes' 9 welded two tree crowns
  that touch (American Beech, Umbrella Thorn Acacia: "only 5 blobs");
  the sweep on just those two sheets took seconds (crop to the opaque
  bbox first) and 1..5 cut them, 7 welded. DO: sweep the new family's
  worst sheet before touching the shared constant; give the family its
  own join (TREE_JOIN_PX). A species drawn across TWO sheets (the
  Redwood) has no shared pixel scale between them: scale the earlier
  sheet from the later one's first stage (TREE_SPLIT_RATIO), never from
  its own mature. And read docs/species_edits.json's mtime before an
  art batch: Mazhron had banked the eighteen new trees the evening
  before, three under ids that did not match the sheet names.

See also: ART_METHOD.md; docs/systems/art-pipeline.md "Gemini growth
sheets"; WORKFLOWS.md "Cut and wire new creature or plant art".

## Apply an audit's findings with a batch edit script (anchors quoted from a report)
Tags: lessons, process | An employee quotes a README sentence on one line but the file wraps it; grep every anchor before the script runs and make each replacement skip itself when its new text is already present, so a mid-way failure resumes instead of forcing a split
Keys: batch edit, edit script, anchor, assert count, wrapped line, audit findings, apply findings, readme audit, rep(), resumable, idempotent, backslash, line continuation, multi-line anchor, heredoc assert, one file per script

THE ONE RIGHT WAY: before writing the edit script, `grep -n` every anchor
in the target file as it is wrapped on disk (an employee's quote joins
lines); write the replacement helper so a call whose NEW text is already
present is skipped, not asserted; then a failed assert halfway costs one
rerun of the same script, not a hand-split second script.

- TRIED (2026-09-20, the second README audit): forty replacements in one
  scratchpad script, each asserting its anchor count. FAILED BECAUSE: one
  anchor ("No hook has state that survives being unwired.") was quoted by
  the employee on one line and wrapped across two in the README; the
  assert stopped the script with half the edits applied, and the same
  script could not rerun because the applied anchors now counted zero.
  DO INSTEAD: grep the anchors first; skip-if-done in the helper.
- NUANCE (the same evening, session_end.py): a live pipe-test of a hook
  that ACTS on unbanked work fires for real - the kit sync had restamped
  FLAGS.md after the commit, so the "clear" test made an auto commit.
  Pipe-test such a hook last, after every companion script has run and
  `git status` outside docs/history/ is empty, or feed it a sandbox root.
- NUANCE (2026-09-28, the WOODTEST `travel` check): a multi-line anchor
  that contains a GDScript line continuation (`\` at the end of a line)
  failed its assert through the Bash heredoc even though the file matched
  by eye, and the FIRST two files in the same script were already written
  when it stopped. DO INSTEAD: one short single-line anchor per
  replacement (`var all_ok := tooltip_ok and drops_ok and`, `drops=%s)"`,
  `drops_ok])`), never a block with a backslash in it; and one file per
  script run, so a stop leaves nothing half-applied. Also: a grep across
  several files prints the FILE before its hits - `@export var pause_menu`
  was run_controller.gd's, not main.gd's, so the check reaches it as
  `$RunController.pause_menu`.
- NUANCE (2026-09-30, the fourth README audit, 22 replacements): the
  anchors were composed from `sed -n` output read minutes earlier, not
  grepped, and the script stopped twice before landing: once on an
  anchor that began at a line's start ("  fix a forbidden") where the
  file's line began mid-sentence ("  section, fix a forbidden"), once on
  a numbered-list continuation indented THREE spaces where the bullets
  above it use two. Nothing was half-applied (the write is per file,
  after its edits), so the cost was two reruns, not a split. DO INSTEAD:
  the script gets a `--check` pass that prints every anchor's count and
  writes nothing, run first and always; and an anchor starts at a word
  that begins its line in the file, or mid-line with no leading spaces,
  never at a guessed indentation.

See also: LESSONS.md "Write a long file or script through the shell";
WORKFLOWS.md "Audit the public README (Rootstock)" and "Add or change a
harness hook"; tools/hooks/session_end.py.

## Read a failing probe or a frame-cost spike (a soak, a ledger FAIL, "transient spikes")
Tags: lessons, testing | A ledger's FAIL with the final figure at baseline is not "transient" until the per-sample series is seen; run the probe short with the machine idle, make it NAME the eater, and fix the eater - never loosen the check to pass it
Keys: soak, soak fail, spike, spikes, transient, window cost, frame cost, probe fail, ledger fail, culprit, slow window, performance, perf

THE ONE RIGHT WAY: a probe that fails on cost is rerun SHORT (2 min)
with nothing else running, and its output must name the system that ate
the time (SpikeTracer's probe ledger; every system reports cost()). Read
the per-sample series, not the ledger's final figure. Fix the named
eater; leave the rule that caught it alone.

- TRIED (2026-09-20, three builds of soak FAILs): read the ledger tails -
  "1, 3, 2 violations, final window at baseline" - and called it
  transient spikes three times, with "one more build's eye" as the plan
  and "flag sustained degradation only" as the proposed fix. FAILED
  BECAUSE: the ledger line carries only the LAST window and a count; the
  violations were a plateau (windows at 4x for 3-6 samples in a row)
  that had drained by the run's end, and the proposed rule change would
  have hidden a real 10 ms/frame cost in play. DO INSTEAD: the culprit
  line (testing.md) - a slow window prints its three biggest eaters;
  the first run with it named water_tiles in every slow window and the
  fix took one @export (perf.md "The water redraw cadence").
- NUANCE: a heartbeat every 20 samples hides a 3-sample plateau; the
  heartbeat now carries winmax= (the slowest of its 20) for exactly this.
- NUANCE: the eater need not be in the sim - here it was a CanvasItem
  _draw that no tick owned, invisible until it reported cost() itself.
  A system missing from the culprit line is the first suspect when the
  named ones do not add up to the window.
- NUANCE (2026-09-21, the .25 build soak): a FAIL whose EVERY window sits
  at ~4x with a tiny board (plants 5, window 2012 ms, clouds the eater)
  while `tasklist | grep -i godot` shows the editor open is the machine,
  not the build: Mazhron's editor instance shares the GPU. Two idle
  reruns at the same version read the old baseline (473 / 498 ms). The
  tell is the shape: a real eater plateaus in some windows; contention
  lifts all of them. Rerun idle before reading anything else.
- NUANCE (2026-10-02, the .51 build soak): the same reading holds when
  only the LAST windows fail (22 violations, all inside a Hurricane
  wipeout at 4.2 min, every earlier window at the 340-500 ms baseline)
  and the sharer is not Godot: `tasklist | grep -i "godot\|gimp"` showed
  GIMP at 923 MB with the 200 MB tree palette open. The idle rerun
  passed at 380 ms. Widen the tasklist to whatever Mazhron edits art
  with; the hurricane's clouds are the costliest window the game has and
  the first to show a shared GPU.

See also: docs/systems/testing.md "The long-soak stability probe";
docs/systems/perf.md "The water redraw cadence"; tools/soak_report.py;
scripts/core/spike_tracer.gd.

---
## Give a system a second face the player can switch back to (keep the old system as an option)
Tags: lessons, design | A second presentation of the same progression is a VIEW over the one data set, never a generated copy; then the switch is free, the save needs no mapping, and a retune of the original moves both faces
Keys: second system, switch back, keep the current, option to swap, new system, two systems, classic, alternate shop, alternate mode, view not copy, memories

THE ONE RIGHT WAY: when Mazhron wants the current system kept as an
option beside a new one built "on the same concepts", find the one
statement of the data both must share (the upgrade levels, the cost
curve) and build the new face as functions over it: new fields on the
same resource for what the new face adds, a Settings switch that only
changes presentation and gates, and per-run state kept beside the shared
save. Never generate a second data folder from the first.

- TRIED (2026-09-21, the Memories shop): the first plan was a generator
  writing chain .tres files into a second folder chosen by the setting.
  FAILED BECAUSE: Mazhron's aside ("if I change the costs of the original
  upgrade in the chain, the others should adjust") cannot hold for
  copies, the save would need a level mapping at every switch, and two
  folders drift. DO INSTEAD: chains as a view over one UpgradeData
  (chain_of(level), the same cost_at), three fields on the resource, the
  gates in UpgradeManager reading Settings, Classic answering "usable"
  for every chain so the old shop is byte for byte the old shop. Three of
  Mazhron's questions (curve continuity, level equivalence, seamless
  switch) answered themselves.
- NUANCE: a rule priced off one example (10,000 for a 127-vitality
  chain) must be checked across the whole table before baking: the
  linear 80x gave a 3.7 billion price on the dearest line; a sub-linear
  power (264 x total^0.75) kept the example and the median sane. Print
  the min / median / max before writing a single .tres.

See also: docs/systems/meta.md "The Memories shop"; NEXT_STEPS.md
"[NS-2]"; tools/memory_chains.py; WORKFLOWS.md "Retune the Memories
chains".

---
## Add a new kind of element to a shared canvas (a second layer on a generated web page)
Tags: lessons, tooling | A canvas that several render functions share is cleared by each one's own selector list; a new element class must join EVERY clear list the same edit, and a headless probe that switches views both ways is the check
Keys: shared canvas, new layer, render path, leftover elements, clear list, querySelectorAll remove, generated page, upgrade web, species web, second view, toggle view, probe both ways

THE ONE RIGHT WAY: when a generated page gains a new kind of element
(a band, a cluster, a chain box) on a canvas that other render functions
also draw on, grep every `querySelectorAll(...).forEach(e => e.remove())`
on that canvas and add the new class to each in the same edit; then the
headless probe switches INTO the new view and BACK OUT and counts the new
class after the switch back (expected 0), not only inside the new view.

- TRIED (2026-09-21, the Memories layer on the upgrade web's tree): the
  layer cleared ".tbox, .gate, .cluster, .clustertitle, .memband" for
  itself and the first probe read 44 boxes and 10 bands, all correct.
  FAILED BECAUSE: the Classic tree and View All kept their own older
  clear lists, so switching back left the ten Rebirth bands drawn under
  the Classic boxes; only the probe's "switch back and count" line saw
  it. DO INSTEAD: one grep for the clear lists before adding the class,
  and the probe's round trip as a standing line (probe_species_web.py's
  shape: the page plus a probe script in headless Chrome, out[] to the
  title).
- NUANCE: node --check proves nothing here; the bug is a missing string
  in a selector, visible only by rendering.

See also: tools/probe_species_web.py; tools/export_upgrade_web.py "THE
MEMORIES LAYER"; docs/systems/tooling.md "The Memories chain table".

---
## Some of the chips are cut off, I need the ability to scroll more to the right (a generated page's canvas clipped at the window edge)
Tags: lessons, tooling | A scroller inside a flex wrapper needs min-width:0 on the wrapper or the wrapper grows to the content and the body clips it; a probe measures geometry only after render() in the view that shows it, since a hidden element reads 0 for every offset
Keys: cut off, clipped, cannot scroll right, horizontal scroll, flex item min-width auto, overflow auto, treewrap, scrollWidth clientWidth, offsetTop 0, display none, hidden view, render vs renderTree, probe geometry, upgrade web, species web

THE ONE RIGHT WAY: when a generated page clips content at the window edge,
measure in headless Chrome first (scroller clientWidth vs scrollWidth,
the wrapper's width vs its parent's): a wrapper equal to the content and
wider than its parent is the flex min-width:auto trap, fixed by
`min-width:0` on the wrapper, never by resizing the content. Any probe
that reads offsets or scroll ranges switches views with the page's own
render() (the function that flips display), then measures, and asserts
the wrapper is no wider than its parent.

- TRIED (2026-09-21, the Memories layer's right edge): assumed the canvas
  width was short and looked for a missing +margin. FAILED BECAUSE: the
  canvas and scroller were sized right (2593 of 2593); #treewrap, a flex
  item of #main with min-width:auto, had grown to 2758px in a 764px window
  and body overflow:hidden clipped it - no scrollbar could exist. DO
  INSTEAD: measure wrapper vs parent before touching sizes; one line of
  CSS (`min-width:0`) was the whole fix.
- TRIED (same day, the probe's four new geometry lines): called
  renderTree() after the card-editor step and every reading was 0
  (treewrap 0, chain 2 moved 0). FAILED BECAUSE: the previous step had
  left state.view on cards, so the tree was display:none and hidden
  elements read 0 for offsetTop, clientWidth and scrollWidth. DO INSTEAD:
  switch with render() (it flips the display) and keep the "wrapper <=
  parent" line as a standing check so a regression reads ERR, not 0.

See also: LESSONS.md "Add a new kind of element to a shared canvas";
WORKFLOWS.md "Probe the upgrade web page after regenerating it";
tools/probe_upgrade_web.py.

---
## A ruling about the parts is not a ruling about the whole (widening a chain ruling to the line gate)
Tags: lessons, design, intent | When a ruling names the parts of a thing (the chains), do not extend it to the thing itself (the line's gate) without asking; state the widening as an assumption in the reply and let the owner rule
Keys: widen a ruling, generalize a ruling, the parts and the whole, chain ruling, line gate, over-read, contradiction rule, memories gate, from the start, rebirth gate

THE ONE RIGHT WAY: when a ruling is phrased about the parts ("the chain
keeps the gates of rebirths"), build exactly that and name any wider
reading as an assumption in the reply: "I read this as also covering the
line's own gate; say if not." The owner answers in a line and the build
is right the first time. If the wider reading changes what a player sees
(a line moving from "from the start" to a gate line), it is a ruling of
its own and waits for a yes under THE CONTRADICTION RULE.

- TRIED (2026-09-21, v0.99.31): read "the chain keeps the gates of
  rebirths (permanent) OR the memory unlock" as covering the LINE's
  requires_rebirths too, and put chain 1 of every gated line behind its
  Classic gate under Memories. FAILED BECAUSE: the ruling was about the
  chains; the line gate is the price of taking the line whole, and a
  split line is not taken whole. Tilling Grasp jumped from "from the
  start" to the 10-rebirth band and Mazhron caught it in the web the same
  afternoon (correction C0001). DO INSTEAD: keep the ruling's scope, and
  where a line is ONE chain (a tool, a Will) it IS the whole, so the
  chain ruling and the line gate coincide there without any widening.

See also: INTENT.md "The split line starts from the beginning";
docs/systems/meta.md "The Memories shop" (THE SPLIT LINE paragraph);
LESSONS.md "Give a system a second face"; docs/index/laws.md "The
contradiction rule".

## Read the screenshot against the data before asking the owner to export (an arrow's target)
Tags: lessons, tooling, web | When a screenshot shows a number the data seems to lack, find which link on disk carries that number before calling it a browser-only edit; a labelled arrow's target is easy to misread in a crowded layer
Keys: screenshot, arrow, export, browser edit, browser-only edit, requires_levels, link label, upgrade web, misread, prerequisite, threshold

THE ONE RIGHT WAY: when the owner's screenshot shows a value the data
"does not have", grep the data for that value first (requires_levels,
thresholds, gates) and name the link that carries it; only when nothing
on disk carries it ask for an export. Say which link you read the arrow
as, so the owner can correct the reading in a line.

- TRIED (2026-09-21, v0.99.31 to .32): read the ">=10" arrow leaving
  Stronger Pulse in the web's Memories layer as the Tilling Grasp link,
  found no threshold on that link, and asked Mazhron at two checkpoints
  to export a browser edit. FAILED BECAUSE: the ">=10" was the Auto
  Click link (click_auto requires_levels = [10], on disk since the gating
  build); the Tilling Grasp link has no threshold on purpose, it opens
  once Stronger Pulse has any level. The owner spent a turn explaining
  data that was already right. DO INSTEAD: `grep -rn "requires_levels"
  data/upgrades/` before the reply; when the value exists on disk, the
  arrow is that link.

See also: docs/systems/tooling.md "The Memories chain table";
WORKFLOWS.md "Probe the upgrade web page after regenerating it";
LESSONS.md "A ruling about the parts is not a ruling about the whole".

## Pull when both machines appended the same generated ledgers (a merge under the preservation law)
Tags: lessons, process, gotchas | Commit the local hook-written ledgers BEFORE pulling, and resolve a generated-file conflict by writing theirs and re-running the generator - never `git checkout --theirs` (the preserve guard refuses the discard verb, and rightly: the write path loses nothing)
Keys: pull, merge conflict, usage ledgers, checkpoint_state, generated files, checkout --theirs, preserve guard refusal, keep_other_ws, regenerate, cross-workstation sync, xlsx binary conflict

THE ONE RIGHT WAY: (1) commit the locally modified hook ledgers first (the
pull aborts on them otherwise), then `git pull --no-rebase`. (2)
checkpoint_state.txt resolves by hand: each WS keeps its own newest line.
(3) Every generated usage file (usage_daily/metrics/employees + the xlsx)
resolves by WRITING the remote side (`git show <merge-head>:<path> >
<path>`, binary-safe from Bash) and then `python tools/usage_report.py` -
the generator rebuilds this machine's rows from its own transcripts and
`keep_other_ws` preserves the other's, so the merged files are correct by
construction. Both pre-merge sides live in git history; nothing is lost.

- TRIED (2026-09-22, the eleven-day catch-up pull): `git checkout
  --theirs <ledgers>` to take WS1's side. FAILED BECAUSE: the preserve
  guard refuses checkout-of-a-path as a discard verb, and a hand-union
  would have duplicated WS1's rows once the generator re-read them.
  DO INSTEAD: the write-then-regenerate path above - it is not a
  workaround of the guard, it is the shape the guard wants: a write that
  discards nothing, then the sanctioned script.
- NUANCE (2026-09-25, the wood-UI pull): three file classes resolve
  differently. APPEND-ONLY ledgers (*_runs.txt, days_index, digest_size)
  union-merge: keep ours then theirs inside each conflict hunk, markers
  dropped - a small Python pass over the markers does 27 files at once.
  GENERATED reports (usage_* + xlsx, wiki_view.html) take theirs or ours
  and let the next loop regenerate. STATE files rewritten in place
  (ledger_heads, checkpoint_state) keep one line per key, newest wins.
  For binary or single-side files, `git show :2:<path>` (ours) /
  `:3:<path>` (theirs) written from Python is the guard-compliant read -
  byte-safe where a PowerShell redirect corrupts and checkout is refused.

See also: WORKFLOWS.md "Leave a note for the other workstation";
docs/index/laws.md (the preservation law); tools/usage_report.py
(keep_other_ws).

## Leave the cross-workstation note the moment the need is spoken (never wait to be told)
Tags: lessons, process, cross-workstation | The instant the manager knows the OTHER machine must do or know something, the note goes in docs/index/notes.md in the SAME batch; telling the owner about the need without writing the note is the failure
Keys: leave a note, WS1, WS2, other workstation, relay, handoff, notes.md, proactive note, unprompted note, next tasks, courier

THE ONE RIGHT WAY: the test lives in the reply itself: any sentence
shaped "WS1 will need to...", "remember for the other machine...", "ask
the manager there to..." is a note that ALREADY EXISTS in
docs/index/notes.md before that reply is sent, committed and pushed with
the batch. The owner never couriers a message between machines and never
has to say "leave a note" - the relay is the manager's own memory across
machines, and standup reads it out on the other side.

- TRIED (2026-09-22, the memory trim): shipped the kit v1.29 batch and
  ended the reply with "ask the manager there to run the trim" - handing
  Mazhron the job of carrying the task to WS1. Mazhron had to say "leave
  a note" as a separate instruction, then ruled: "I shouldn't have to
  tell you to leave a note for WS1 ... If you know WS1 needs to do
  something, you should leave the note for yourself. If WS1 needs to
  know something, you should make the note yourself." FAILED BECAUSE:
  the manager treated the relay as the owner's channel instead of its
  own cross-machine memory. DO INSTEAD: write the note in the same batch
  that created the need; the reply then says "noted for WS1" instead of
  assigning the owner homework.

See also: docs/index/notes.md (the relay); WORKFLOWS.md "Leave a note
for the other workstation"; docs/index/laws.md (the workflow rule).

## Keep track of real time between saves (a telemetry clock that spans sessions)
Tags: lessons, telemetry, persistence | A persisted log's real-time deltas come from its own play clock, never from wall-clock stamps; the log flushes at the world save, not at the window-close notification
Keys: telemetry, real seconds, real_s, wall-clock, unix, play clock, quit, save and exit, resume, next day, several days, flush, WM_CLOSE_REQUEST, get_tree().quit, balance log, run spans sessions

THE ONE RIGHT WAY: when a log measures "real time" between events and
its baseline is persisted, the time source is a counter the log owns
and saves (ticks only while recording is enabled), never a unix stamp
in the baseline. And the log banks itself inside the same function the
world save goes through, because a menu quit calls the engine quit
directly and the window-close notification never fires.

- TRIED (2026-08-24 to 2026-09-24): BalanceLog stamped unix time into
  each segment's baseline and measured the next event from it; the
  flush hung on NOTIFICATION_WM_CLOSE_REQUEST.
  FAILED BECAUSE: a run played over several days put the whole night
  into the first event after the resume (only the day baseline was
  rebased on arrival, not the unix one), and Save & Exit quits through
  get_tree().quit(), which sends no close notification, so the last
  minute of the zone ledger was dropped. Found when Mazhron asked
  whether a run could be played across days (2026-09-24).
  DO INSTEAD: a play clock on the log (Time.get_ticks_msec deltas while
  enabled, baseline dropped when disabled, saved in the log JSON) feeds
  the real_s delta; SaveManager.save_campaign calls BalanceLog.flush()
  so every save path banks the log. Prove it with a save + reload check
  in the self-test.
- NUANCE: any other counter the deltas read must live in the world
  save (RunStats, lifetime vitality and biomass, the day clock do), or
  a reload reads it as fresh from zero.
- RULED (Q0005, Mazhron 2026-09-24): the log LIVES AND DIES WITH THE
  WORLD SAVE. Its only disk write is flush() from save_campaign; no
  per-event, timer or close-notification writes; load_log always reads
  the disk on every world load. A quit without a save then reverts the
  log to the same moment the world reverts to, and the stretch since is
  nixed. Test both halves: resume (flush, reload, next delta) and
  discard (event, no flush, reload, event gone).

See also: docs/systems/meta.md "THE PLAY CLOCK"; scripts/core/balance_log.gd;
docs/history/open_questions.txt (Q0005); WORKFLOWS.md "Track an open
question to Mazhron".

## Anything that can be pressed should wear the new frames (style every Button, or every control of one type, at once)
Tags: lessons, ui, godot | Fill the PROJECT theme at boot; a root-window theme stops at a CanvasLayer and a per-script override is one place per button forever
Keys: theme, Button, stylebox, every button, all buttons, CanvasLayer, project theme, wood_theme.tres, ThemeDB, install_theme, press feedback, pressed, hover, disabled, rebuild, in place, queue_free, canvas item, badge, footer, changing constantly, flicker

THE ONE RIGHT WAY: project.godot names an empty Theme .tres
(gui/theme/custom = assets/ui/wood_theme.tres, written with the Write
tool, never a shell redirect) and one static installer (WoodBox.
install_theme, from Settings._ready before any scene builds) fills its
Button styleboxes for normal / hover / pressed / hover_pressed / disabled
/ focus. Every Button in the game changes at once, CheckBox and the touch
keys inherit the Button type, and a control's own override (map tiles)
still wins. Press feedback is three tints and a 1 px content-margin sink
on the pressed box, not per-button code. Probe the lookup headless first
(a SceneTree script under --script: add a Button under a CanvasLayer and
compare get_theme_stylebox to the box you set) - it takes ten seconds and
settles the question before any wiring.

- TRIED (2026-09-25, the wood buttons): `get_tree().root.theme = theme`
  on the root Window. FAILED BECAUSE: theme lookup walks parent Controls
  and Windows only - it stops at a CanvasLayer - and the HUD, the badges
  and the footer all live under one, so the probe printed false; and
  ThemeDB has no set_project_theme to fall back on at runtime. DO
  INSTEAD: the empty project-theme .tres named in project.godot, filled at
  boot through ThemeDB.get_project_theme() - the probe printed true under
  the CanvasLayer, true for CheckBox, and the override still won.
- NUANCE: one shared StyleBox instance serves every button, so a Random
  wood must roll PER CONTROL (seed = the canvas item id + a generation
  counter), or hover and press would each re-roll the frame under the
  mouse.
- TRIED (2026-09-25 evening, Mazhron: "they shouldn't be changing
  constantly"): leaving the badge strips and the footer as they were -
  queue_free every Button and make new ones on the half-second poll and
  on every tool switch. FAILED BECAUSE: a re-made Button is a NEW canvas
  item, and the per-control seed IS the canvas item; the roll held per
  control exactly as designed while the controls were replaced under it,
  so the HUD wore new woods twice a second. DO INSTEAD: a HUD control that
  lives the whole run updates its Buttons IN PLACE - one Button per key,
  hidden when not shown, text/tip/icon/visibility refreshed - and only a
  window that opens and closes may rebuild, because that is the moment a
  fresh wood is wanted. WOODTEST's `held` check compares the Buttons'
  instance ids across a refresh. The general form: any "seeded by the
  node" look breaks the moment a refresh path re-creates the node.
- NUANCE (the cut, same day): a hollow frame taken apart by geometry
  measures its border as the MEDIAN opaque run across hollow rows, never
  the max (a bark nub at an inner corner read as a border half the frame
  wide) and never a fixed middle band (the bar's underside is thicker
  than its top); see art-pipeline.md "The wood UI frames".
- TRIED (2026-09-26, the dresser clicks: "the new buttons randomize
  everything every time"): detecting "this window just reopened" as
  frames-since-last-draw inside StyleBox._draw (REROLL_GAP 3): a big gap
  meant hidden, so the next draw re-rolled woods and dealt fresh flair.
  FAILED BECAUSE: retained-mode canvas items only redraw when DIRTIED -
  a visible window sitting STILL also stops drawing, so the first
  dresser click after 3 quiet frames (its own emit_changed!) read as a
  reopen and rolled the player's pick away; picking Birch randomized,
  Randomize flair re-rolled the woods too. DO INSTEAD: wire the real
  signal - WoodBox.wear(host, pad) connects the host Control's
  visibility_changed AND its enclosing CanvasLayer's (the big menus
  toggle the LAYER's visible, which a child Control's signal never
  fires for), and the draw never guesses state. The general form: "time
  since last draw" measures DIRTINESS, not visibility; never infer
  hidden/shown from it in a retained-mode renderer.
- NUANCE (2026-09-26, the offline card): "every window" means every
  PanelContainer in the GAME, not every file in scripts/ui/ - the
  while-you-were-away card is built inline in main.gd and kept its old
  StyleBoxFlat through the whole NS-30 sweep until Mazhron saw it. When
  restyling a control type, `Grep "StyleBoxFlat" scripts/` finds the
  inline stragglers the folder sweep misses; each converted window gets
  a self-test flag that its stylebox IS the new kind (OFFLINETEST's
  `card` check is the pattern).

See also: docs/systems/ui.md "The wood frames" (THE BUTTONS AND THE BAR);
docs/systems/art-pipeline.md "The wood UI frames"; WORKFLOWS.md "Cut and
wire the wood UI frames"; scripts/ui/wood_box.gd (install_theme).

## A test that clicks the screen fails headless and passes in a window (FOOTERTEST through --test, 2026-09-25)
Tags: lessons, testing, godot | A synthesized mouse click has nowhere to land without a window; the runner must know which tests are windowed-only, not the person typing the command
Keys: headless, windowed, --windowed, WINDOWED_ONLY, FOOTERTEST, parse_input_event, mouse click, synthesized click, probe FAIL, run_tests, adhoc, --test, capture, _SHOT

THE ONE RIGHT WAY: a test that drives the game through real input (a
synthesized InputEventMouseButton, a screenshot capture, a tutorial
highlight) is listed in tools/run_tests.py WINDOWED_ONLY, and the runner
drops --headless by itself for any batch that holds one; `--windowed`
forces a window for anything else. testing.md names the test as windowed
next to its command. A FAIL line that came from a headless run of a
windowed test stays in the ledger - the fix line follows it.

- TRIED (2026-09-25, after the footer refactor): `python tools/run_tests.py
  --test FOOTERTEST`, trusting that any test the runner lists can run the
  way the groups run. FAILED BECAUSE: the runner passed --headless as it
  does for every group, testing.md called the test "windowed" in prose
  only, and the click on the Upgrades button landed nowhere: "window
  open=false". Nothing in the footer was wrong. DO INSTEAD: put the
  knowledge in the runner (WINDOWED_ONLY), not in prose - the hook forbids
  setting EVERWOOD_*TEST by hand, so the runner is the only door and must
  know the shape of every test it can open.
- NUANCE: a FAIL right after a code change is not evidence against the
  change until the test has run the way it was designed to run. Read
  the FAIL text for what it actually measured (here: the window state,
  not the button) before touching the code.

See also: docs/systems/testing.md (the probes paragraph); tools/run_tests.py
(WINDOWED_ONLY); LESSONS.md "Read a failing probe or a frame-cost spike".

## An append-only tracker is read at its tail, not its first matching line (Q0005 reported open after it was ruled, 2026-09-25)
Tags: lessons, ledgers, reporting | In a ledger where "a resolution is a new line, never an edit", an id's earlier lines are history; only the LAST line for that id is its state - a diff or grep that surfaces the OPEN line proves nothing about today
Keys: open questions, Q0005, append-only, tail, RESOLVED, OPEN, tracker state, last line, diff --check, pull summary, misreport, open_questions.txt

THE ONE RIGHT WAY: before telling the owner a tracked item is waiting
on him (a question, a claim, a flag), read the tracker for EVERY line
carrying that id and report the last one's status. After a pull, the
diff shows lines in whatever order the file holds them - an added OPEN
line in a diff hunk is where the item STARTED, not where it stands.
One grep answers it: `Grep "Q0005" docs/history/open_questions.txt`,
state = the final match.

- TRIED (2026-09-25, the WS1 merge): summarized the pull for Mazhron
  and listed Q0005 as "waiting on you", quoting the OPEN line that had
  scrolled past in a `git diff --check` result. FAILED BECAUSE: the
  tracker is append-only by its own header line; WS1 had ruled and
  logged Q0005 RESOLVED the day it was raised (2026-09-24, the answer
  verbatim, the fix built and self-tested in v0.99.35) - the OPEN line
  I quoted was simply the older sibling of the RESOLVED line two rows
  down. The owner had to point out he had already answered. DO
  INSTEAD: never report an append-only ledger's state from a diff
  fragment; grep the id in the file and read the tail before naming
  anything "open" in a summary.

See also: docs/history/open_questions.txt (the header is the law);
WORKFLOWS.md "Track an open question to Mazhron"; LESSONS.md "Pull when
both machines appended the same generated ledgers".

## I don't understand what the issue is with git and rootstock (a harness block explained as if it were a repo problem, 2026-09-26)
Tags: lessons, harness, kit | When the harness's permission layer blocks a sanctioned action, say plainly "the repo is fine; I was not allowed to press the button" and hand the owner the smallest way to unblock; an explanation that mixes the git state with the permission block reads as if something broke
Keys: rootstock-os, permission classifier, blocked push, kit repo, out of scope, settings.local.json, additionalDirectories, harness block, denied, explanation, correction

THE ONE RIGHT WAY: the kit repo lives OUTSIDE the project working
directory, so on a machine without an allow rule the harness may block
git commands aimed at it. Two separate reports, never blended: (1) the
repo's own state (merged? clean? what commit waits?) and (2) the
harness block ("the command was refused by my permission layer; the
repo is healthy"). Both workstations work in both Everwood and
rootstock-os including push and pull (Mazhron's ruling 2026-09-26), so
the standing fix is an owner-added allow rule in the machine's
.claude/settings.local.json (gitignored, per-machine paths) - Claude
cannot write its own permission rules; that self-granting block is a
security boundary, so hand the owner the exact rule text or /permissions
step and stop.

- TRIED (2026-09-26): explained a blocked rootstock-os push by
  narrating the merge, the sync script's "nothing to push", and the
  classifier denial in one breath. FAILED BECAUSE: the owner could not
  tell whether git was broken, the merge had failed, or something
  needed fixing - the answer was "nothing is wrong; one push needs a
  hand". A second, two-part explanation (ordinary git, then the
  permission block) resolved it in one read. DO INSTEAD: separate "what
  the repos look like" from "what I was allowed to do", and end a
  permission report with the one action that unblocks it.

See also: WORKFLOWS.md "Edit the future-project kit (Rootstock)";
LESSONS.md "Pull when both machines appended the same generated
ledgers".

## Never set EVERWOOD_*TEST by hand, even though CLAUDE.md's verify snippet showed how (the runner is the only door, 2026-09-26)
Tags: lessons, testing, process | A doc snippet that demonstrates a pattern a guard forbids is a stale doc, not a permission; the guard's message names the one right way and the doc is fixed in the same batch
Keys: EVERWOOD_WOODTEST, EVERWOOD_*TEST, run_tests.py, --group, --list, script rule, hook block, verify snippet, CLAUDE.md Verifying changes, stale doc, env var by hand

THE ONE RIGHT WAY: tests run through `python tools/run_tests.py --group
<group>` (`--list` shows the groups) - the groups, the don't-combine laws
and the ledger append live there. The import line (`--headless --path .
--import`) is still run directly; it is not a test. When a guard blocks a
command, the block text IS the instruction - follow it, and if a doc
taught the blocked pattern, fix that doc in the same batch (the workflow
rule: a stale entry is a bug).

- TRIED (2026-09-26, verifying the flair density change): set
  `$env:EVERWOOD_WOODTEST = "1"` and launched Godot by hand, copying
  CLAUDE.md's "Verifying changes" snippet verbatim. FAILED BECAUSE: the
  script-rule hook forbids hand-set EVERWOOD_*TEST - running outside the
  runner skips the group laws and the test_runs.txt append - and the
  CLAUDE.md snippet predated the guard. DO INSTEAD: `python
  tools/run_tests.py --group ui` (WOODTEST's group) on the first try;
  the snippet in CLAUDE.md now points at the runner.

See also: docs/systems/testing.md (the full roster); WORKFLOWS.md "Run
tests or probes"; LESSONS.md "A test that clicks the screen fails
headless and passes in a window".

## Adding several safety hooks at once: the SAFETY table bites every in-between state (the delegation truth set, 2026-09-26)
Tags: lessons, hooks, kit | A guard that checks a file's WHOLE resulting state refuses any edit sequence whose intermediate states are illegal, even when the end state is what the guard wants; the counts lint reads prose numbers as claims
Keys: SAFETY table, format_guard, settings.json, safety wiring, atomic write, intermediate state, Edit refused, whole-file Write, readme_lint, count claim, three hooks, hook count

THE ONE RIGHT WAY: when a batch adds N hooks to format_lint.py's SAFETY
table, land each settings file's N wirings in ONE call - a whole-file
Write (or one Edit whose new_string carries all N entries) - because
format_guard validates the RESULTING file against the FULL table, and
after the table gains its rows, every partial wiring is a refusable
state. Order inside the batch: SAFETY rows first is fine, but from that
moment the settings edit must be atomic. And when the public README
gains prose about the new set, spell numbers that are not the total
carefully: readme_lint reads "<number> hooks" as a count claim against
the real script count ("three hooks" FAILED against truth 15; "a trio"
passed).

- TRIED (2026-09-26, wiring brief_guard + delegation_auditor +
  verify_advisor into the kit template): three sequential Edits, one
  per hook. FAILED BECAUSE: each single edit produced a file where the
  OTHER two SAFETY hooks were "not wired", and the format guard refuses
  any edit that leaves a settings file short of the full table - the
  guard judges states, not intentions. DO INSTEAD: one Write with all
  three entries; the guard passed it first try. The refusals were the
  law working (they proved the new rows enforce), never a bug to route
  around.
- NUANCE: a guard the manager writes WILL fire on the manager's own
  next steps (the preserve guard's author history says the same). Plan
  the batch so the guard lands in its final shape and the guarded files
  change atomically after it.

See also: HOOKS_METHOD.md (Tier 4a + the v1.30 change-log line);
tools/format_lint.py (SAFETY); tools/readme_lint.py (the counts);
LESSONS.md "Harden a guard against a public incident (audit a
safeguard)".

## A test-runs PROPOSE means read the ledger tail first (the FAIL may already carry its fix, 2026-09-26)
Tags: lessons, testing, process | The trends proposal counts FAIL lines in a lagging 10-line window; a fix that landed minutes after the failures still trips it at the next standup, so the ledger tail - not the proposal text - says whether anything is broken now
Keys: test_runs, PROPOSE, FAIL lines, flaky group, quarantine, ledger_trends, lagging window, tail -15, WOODTEST, fix line follows, age out

THE ONE RIGHT WAY: on a "PROPOSE (test_runs.txt): N FAIL lines in the
last 10 runs" line, `tail -15 docs/history/test_runs.txt` BEFORE hunting
a flaky group. If every FAIL is followed by a PASS of the same test at
the same or a later version, the fix already happened (the FAIL lines
stay in the ledger by law - the fix line follows them) and the proposal
is the window lagging, not a live problem. The honest close is one
legitimate run if one is owed - the group at the CURRENT version when
the version moved past the last green line - never green runs fired to
flush the window ("never re-run a green group at an unchanged version").
Only a FAIL with no following PASS is the flaky-or-broken case the
proposal's "fix or quarantine" words are for.

- TRIED (2026-09-26, standup carried "4 FAIL lines in the last 10 runs
  (adhoc)"): the tail showed all four were WOODTEST at 10:30 the prior
  day - dev-loop iterations while WOODTEST gained the layout round-trip
  flag - with 2/2 PASS at 10:31 and ui 7/7 PASS the same afternoon.
  Nothing was flaky; ui at the new version (0.99.46, a UI change) was
  the one run owed, and it passed 7/7.

See also: tools/ledger_trends.py (rule 2, test_fails threshold);
WORKFLOWS.md "Run tests or probes"; docs/systems/testing.md;
LESSONS.md "A test that clicks the screen fails headless and passes in
a window (FOOTERTEST through --test, 2026-09-25)".

## If the hook says checkpoint advised, I shouldn't have to type /checkpoint (the ADVISED line is a step in the reply, not a line to relay)
Tags: lessons, process, checkpoint | The closing check of every reply: did any hook say ADVISED this turn? Each one is work done before the reply ends
Keys: checkpoint advised, ADVISED MEANS DO IT, hook line, relay verbatim, closing check, end of reply, safe to clear, context gauge, 80% rule, C0002, C0003, kit unsynced, lesson advised, changelog unexported, hook warning, warning means do it, the hook law, repeated warning

THE ONE RIGHT WAY: before sending any reply, run the closing check: (1)
is the tree committed and pushed, (2) did a hook this turn say ADVISED -
CHECKPOINT ADVISED, LESSON ADVISED, KIT UNSYNCED - and is the arc closed?
Each ADVISED is an instruction: the checkpoint sequence (session loop,
push, WHERE WE LEFT OFF with both sides verbatim, commit, push, reset,
marker) runs INSIDE that reply, the lesson is written INSIDE that reply,
the kit is synced INSIDE that reply. Relaying the hook line verbatim is
part of the reply, never a substitute for the step. Mazhron then simply
/clears; he never types /checkpoint.

- TRIED (2026-09-28, after shipping v0.99.47): the prompt hook had said
  KIT UNSYNCED and the context gauge had crossed the 80% line; the reply
  synced the kit, reported the ship in full and ended. FAILED BECAUSE:
  the law's text ("ADVISED MEANS DO IT", laws.md since 2026-09-10) lived
  in a file, not in the reply's closing check - the ship report felt like
  the end of the work, and the checkpoint was left as something Mazhron
  would ask for. He had to ask (correction C0002). DO INSTEAD: the
  closing check above, every reply; when in doubt whether the arc is
  closed, it is - ship the step, then checkpoint. A checkpoint costs one
  commit; a missed one costs Mazhron a prompt and a rule restated.
- NUANCE: mid-arc (uncommitted work, an employee running) the checkpoint
  waits for the step to ship - but the reply says so in one line and
  names when it will run, so the advice is answered, not dropped.
- TRIED (2026-09-28 afternoon, the same day): the Stop hook printed
  CHANGELOG UNEXPORTED after three docs-only commits; the replies
  relayed the line and ended, three times, until Mazhron asked "Why am I
  told about the changelog being uncommitted? Should you not just run
  the script?" FAILED BECAUSE: the closing check above listed three
  ADVISED names and this line was a fourth; a warn-only line read as
  information. Half the warnings were also spurious: the hook counted
  the export's own commit, so every export left "1 commit" behind it.
  DO INSTEAD (correction C0003, his words: "A Warning from the hook
  means do it, not relay the message for the user to do"): the closing
  check is "did ANY hook line name work this turn?" - not a list of
  names; each one runs inside the reply (the export is one command and a
  push). A hook's wording is an order to the manager ("MANAGER: run
  ..."), never a note for him. And a warning seen twice for the same
  thing is the failure, not the warning itself.
- TRIED (2026-09-28 evening, the same day again): after the route line
  batch the reply ended "the checkpoint counter has ticked through a full
  arc tonight, so a checkpoint and clear is the natural next step
  whenever you want to stop." FAILED BECAUSE: the closing check asked
  "did a HOOK name work?" and no hook had; the manager's own sentence
  named the checkpoint as due and was treated as advice to the owner.
  DO INSTEAD (correction C0004, his words: "If this is the case, you
  should have just done a checkpoint. Any reference to a checkpoint from
  any valid source should prompt you to do it."): the closing check is
  "does ANYTHING in this turn - a hook, my own reply, the counter - name
  a checkpoint as due?" If the sentence "a checkpoint is the next step"
  is true, the checkpoint runs before the sentence is sent, and the
  reply ends with the marker instead. stop_tick.py now refuses once per
  prompt when a reply names a checkpoint as due without the marker
  (CHECKPOINT NAMED), so the sentence cannot be sent unmade.

See also: docs/index/laws.md "The checkpoint protocol" (REAFFIRMED AS A
CORE LAW, BROADENED TO EVERY HOOK LINE); CLAUDE.md "The hook law"; .claude/skills/checkpoint;
docs/history/corrections.txt (C0002); LESSONS.md "Anything that can be
pressed should wear the new frames" (the same evening's ADVISED lesson,
written on the hook's word).

## Apply a long batch of file edits from the shell (the heredoc that fails to parse, 2026-09-28 and twice 2026-09-29; the sed that eats backslashes)
Tags: lessons, tooling, harness | A Python edit script longer than about ninety lines inside a Bash heredoc fails to parse in this harness's Git Bash, and ANY edit whose text carries a backslash (a regex) loses it through sed or a heredoc; write the script to the scratchpad and run it by path, then run the file's selftest before any ledger line
Keys: heredoc, unexpected EOF, matching quote, bash parse, long script, scratchpad, edit script, batch edit, route_docs, python - <<, Write tool, run by path, backslash, sed -i, regex edit, \b, chr(92), selftest before ledger, false measure

THE ONE RIGHT WAY: a multi-file edit that needs more than a screen of
Python goes into the scratchpad as a .py file through the Write tool,
then `python <scratchpad>/<name>.py` runs it. Short heredocs (a few
dozen lines) are fine. A new tool or hook is written with the Write
tool too, never through a heredoc, because a docstring carries triple
quotes and apostrophes that a shell will parse before Python sees them.

- TRIED (2026-09-28, the route line batch): `python - <<'EOF' ... EOF`
  with a 106-line tool body, then again with a 110-line edit script.
  FAILED BECAUSE: both died with "unexpected EOF while looking for
  matching `''" at the line just past the heredoc's end; the shell never
  saw the terminator, nothing ran, and the second failure cost the whole
  batch of doc edits a rerun. Two shorter heredocs the same hour (about
  ninety lines) parsed and ran. DO INSTEAD: Write the script as a file,
  run it by path; the file is also re-runnable and readable if it asserts.
- TRIED (2026-09-29, the fifth digest trim): a ONE-line regex edit in
  tools/standup.py, first through `python - <<'EOF'` with `\\b` in the
  match string (the pattern never matched: assertion, nothing written),
  then through `sed -i '326s/.*/.../'` (the replacement landed with every
  `\b` turned into `b`; the selftest went 8 FAILED and the digest measured
  1,300 bytes short because no verdict matched). FAILED BECAUSE: the
  shell and sed each consume one layer of backslashes before Python or
  the file sees them, and a regex is nothing but backslashes. Worse,
  the ledger line was appended between the two tries, so for two
  minutes digest_size.txt carried a measurement of a broken tool. DO
  INSTEAD: length is not the test; the CONTENT is. Any edit carrying a
  backslash, a regex, a docstring or mixed quotes goes to a scratchpad
  .py file, built with chr(92) or a raw string, run by path. And the
  order is fixed: edit, selftest, THEN measure and ledger; a ledger
  line written before the selftest is a guess with a timestamp.
- TRIED (2026-09-29, the security audit batch, the third time the same
  day): a 13 KB method file with apostrophes, double quotes and
  backticks, wrapped in a Python raw string, sent through a quoted
  heredoc anyway because the session's auto-mode note prefers Bash.
  FAILED BECAUSE: the same "unexpected EOF while looking for matching
  `''" as 09-28; the shell parsed the body before Python saw it. The
  Write tool wrote the same script to the scratchpad and it ran by
  path on the first try. DO INSTEAD: a harness preference for Bash is
  not a reason; this lesson is the reason. Any file of prose or code
  longer than a screen, or carrying mixed quotes, is a Write-tool
  script run by path, and the heredoc is never the first try.
- NUANCE: the diet guard's OUTPUT DIET line on a command that mentions
  glob or a listing is advice about limiters, not a failure; the parse
  error came from the shell, and the fix is the file, not shorter output.
- TRIED (2026-10-01, the stop-time cross-check, twice in ten minutes):
  a short heredoc Python script whose replacement text held `\n` inside
  a triple-quoted block, then a one-line fix-up script with `\\n`.
  FAILED BECAUSE: the Bash tool's own layer halved the backslashes both
  times, so the file got a real newline inside a string literal and the
  selftest died on "unterminated string literal"; the second try had
  "fixed 3" printed and changed nothing, since `\\n` had become `\n`
  before Python ran. DO INSTEAD: the length test is a trap when the
  script is SHORT: any text with a backslash in it goes through the
  Edit tool (its old/new strings pass verbatim) or a Write-tool
  scratchpad script, even when it is three lines.

See also: WORKFLOWS.md "Section or split a file the big-reads ledger
names" (the batch-edit lesson nuance: one anchor per replacement, one
file per script run); tools/route_index.py (the tool born in this batch);
docs/systems/self-audit.md "The route line".

## A standup proposal is this reply's work (the PROPOSE line is an order, not a menu, 2026-09-29)
Tags: lessons, process, learning loop | A [DO] proposal at standup (an audit, a trim, a loop run) is done in the first reply by a script or an employee; only an [ASK] line is a question for Mazhron
Keys: proposal, PROPOSE, standup proposals, what to work on, learning loop, owner decides, systems audit overdue, digest trim, do it, permission, ask permission, proposal named, DO ASK, C0005, four corrections, name the pattern

THE ONE RIGHT WAY: the first reply after standup relays the digest, then
DOES every PROPOSE [DO] line in that same reply: the systems audit is four
read-only employees plus --record, the digest trim is the loss test plus
a measurement, a stale loop group is one run_all call, dead links are
fixed, an unwritten lesson is written, a stale claim is resolved, a
corrections pattern is named and its law drafted. Only the [ASK] lines
(an open question, a shelf, a declining agreement rate, a game number)
are put to Mazhron, and the reply ends with what was done, not with a
menu. "The owner decides" names the ASK class, never the mechanics.

- TRIED (2026-09-29, the first reply after /clear): the digest carried
  four PROPOSE lines; the reply summarized them under "Proposals" and
  closed with "What do you want to work on: NS-30's flat surfaces, the
  overdue systems audit, the corrections pattern, the core diet, or one
  of the open questions?" FAILED BECAUSE: the learning-loop law's closing
  words, "Mazhron decides", were read as "every proposal is a question";
  an audit an employee runs and a trim a loss test governs carry no
  decision, only work, so offering them was the fourth relay of the week
  (C0002, C0003, C0004 were the same shape with a hook line or the
  manager's own sentence as the source). Mazhron: "If an audit is
  required, and it can be done with a sub-agent, or a script, it doesn't
  need my permission. Just do it." DO INSTEAD: the way above; the tags
  now say which is which, and the Stop hook refuses a reply that names a
  [DO] proposal its ledger still raises (PROPOSAL NAMED).
- NUANCE: an audit's own proposals follow the same split: its DO items
  the manager does in the batch (or briefs next), its ASK items are
  relayed verbatim; an employee still applies nothing.
- NUANCE (the guard's probe case, 2026-09-29): the incident reply was
  written into stop_tick's selftest BEFORE the pattern, per "Harden a
  guard against a public incident", and it failed first: the sentence
  span `[^.
]{0,80}` stopped at the "3.2k" in "about 3.2k tokens and
  wants a trim". A sentence span in a guard regex must not treat every
  full stop as a sentence end; `[^
;]{0,100}` passed. The probe case
  earned its keep in the first minute.

See also: INTENT.md "The proposal law"; "If the hook says checkpoint
advised, I shouldn't have to type /checkpoint" (the same law, the hook
and the reply as sources); tools/ledger_trends.py (ACTION); tools/hooks/
stop_tick.py (PROPOSAL NAMED); WORKFLOWS.md "Audit the operating system".

## An ask is a question with a recommended answer (a statement never asks, 2026-09-29)
Tags: lessons, process, communication | Every [ASK] line put to Mazhron ends with a question mark, carries the manager's recommended answer first, and never shares a list with statements; a reply of "agreed" or "you decide" on any line must be enough
Keys: ask, ASK items, ruling, rulings, are you asking me, statement or question, summaries, can't tell, recommended answer, relay ASK, what do you want, question mark, decision list

THE ONE RIGHT WAY: when a reply puts something to Mazhron, each item is
one numbered line shaped "<the thing in a sentence>. <The question>?
Recommended: <the answer and why in a clause>." Asks and statements never
share a list: findings go in prose or their own list, asks in the ASK
list, and the list is introduced as asks ("These need your ruling").
Any item where the manager's recommendation is good enough says so, so
"you decide" is a valid reply. A relayed audit ASK item is rewritten into
this shape by the manager, never pasted as the auditor's finding.

- TRIED (2026-09-29, the first reply after /clear): the systems audit's
  seven ASK items were relayed as findings ("The between-session cache
  gap past the one-hour TTL is the residual miss cause. No script fixes
  a cadence.") under a heading that said ASK. Mazhron: "Are you asking
  me to make rulings here or are these statements? Sometimes when you
  respond to me and give me summaries, I can't tell if you are asking me
  for something or telling me something." DO INSTEAD: the shape above;
  a finding without a question is a statement however it is labelled,
  and a question without a recommendation makes the owner do the
  manager's thinking.

See also: "A standup proposal is this reply's work" (the DO / ASK split
this entry gives its voice to); INTENT.md "The proposal law"; the
WHERE WE LEFT OFF ASK list in the day file, which follows the same shape.

## Widen a proxy after its first real run (the named corpus, and the selftest that pins a phrase, 2026-09-29)
Tags: lessons, process, learning loop, ledgers | A rule's script proxy must count every home the rule already has, and a verdict phrase changed in the script is changed in its selftest in the same edit
Keys: law_gaps, workflow gap, proxy, named corpus, first real run, false positives, hooks flagged, run_all scripts flagged, selftest FAIL after edit, verdict wording, pinned phrase, employee script widened

THE ONE RIGHT WAY: when a script stands in for a law (a proxy), list every
place the law is already satisfied BEFORE the spec is written, and make the
proxy read all of them: a tool is "named" not only by a WORKFLOWS.md entry
but by tools/run_all.py (the loop is a loop script's workflow), by
.claude/settings.json (a hook's wiring) and by any skill. Then run it once
for real and read the list it produces: every false positive on that first
run is a home the spec forgot. When the widening changes a verdict's
wording, grep the selftest for the old phrase in the same edit, because an
employee's selftest pins the exact string it was told to print.

- TRIED (2026-09-29, tools/law_gaps.py by sonnet, spec by the manager):
  the workflow-rule proxy was specified as "a changed tool that
  WORKFLOWS.md does not name". Its first real run listed 17 gaps, and
  twelve of them were hooks and run_all exporters, which the workflow rule
  already covers by their wiring. FAILED BECAUSE: the spec named one home
  for the rule when the rule has four. DO INSTEAD: the corpus above; the
  list fell to 5, all real.
- TRIED (the same patch): the verdict text gained ", run_all group, hook
  setting or skill" in the script alone; the selftest failed once on the
  old phrase, then passed after the second edit. DO INSTEAD: change the
  script and its selftest in one edit script, grepping the old phrase
  first (the "Apply an audit's findings with a batch edit script" entry's
  anchor rule applies to verdict strings too).

See also: INTENT.md "Everything that can be measured is measured"; tools/
law_gaps.py (the named corpus comment); "Apply an audit's findings with a
batch edit script (anchors quoted from a report)".

## Edit the kit's original, never its grab-copy (refresh_kit reverts the copy silently, 2026-09-29)
Tags: lessons, process, kit, rootstock | A method file exists three times (repo root, the kit folder, the public mirror); only the repo-root original holds an edit, because refresh_kit copies it over the other two on every run
Keys: kit copy reverted, refresh_kit pairs, Future Project MDs, WIKI_METHOD edit lost, sync_kit_repo, grab-copy, original vs copy, method file fix, README audit fix in a method file

THE ONE RIGHT WAY: before a batch edit touches any file under "Future
Project MDs/", ask refresh_kit which original owns it (`python -c "import
sys; sys.path.insert(0,'tools'); import refresh_kit as r; print(r.pairs())"`
or WORKFLOWS "Edit the future-project kit" step 1) and point the edit at
THAT path: the repo-root METHOD.md, tools/<script>.py, .claude/skills/,
.claude/rules/. Then `python tools/refresh_kit.py` carries it to the kit
folder and `python tools/sync_kit_repo.py` to the mirror. A file with no
original (UPGRADES.md, the domain notes, the public README) is edited where
it lives. Check the edit landed with a grep of the ORIGINAL after the
refresh, not of the copy before it.

- TRIED (2026-09-29, the README audit's WARN_TOKENS catch): the batch edit
  script pointed at "Future Project MDs/WIKI_METHOD.md", printed "wrote",
  and the next refresh_kit run copied the untouched repo-root original
  back over it; the sync pushed a mirror without the fix. FAILED BECAUSE:
  the kit folder is a grab-copy, not a home; refresh_kit says nothing
  when it overwrites. DO INSTEAD: the path rule above; the second pass
  edited WIKI_METHOD.md at the repo root and both copies followed.

See also: WORKFLOWS.md "Edit the future-project kit (Rootstock)";
tools/refresh_kit.py (pairs); "Apply an audit's findings with a batch edit
script" above (the anchor rule; add the path rule to it).

## Close a proposal with the number its rule reads (the measure line by the proposal's own formula, 2026-09-29)
Tags: lessons, process, proposals, ledgers | A "done" the ledger cannot see is not done: the closing measurement is taken exactly the way the trend rule measures, or the proposal fires again
Keys: proposal still raises, PROPOSAL NAMED, measure line, digest_size, digest_warn_bytes, wc -c, like-for-like, closing a DO proposal, ledger_trends formula, HOW line

THE ONE RIGHT WAY: before appending the line that closes a [DO] proposal,
read the rule in tools/ledger_trends.py (or the HOW line the digest prints
for that ledger) for WHAT it measures and HOW, and record that exact
measurement as the closing line; a second line with a richer like-for-like
number is welcome but is never the closer. Verify with `python
tools/ledger_trends.py | grep <ledger>` printing nothing before the reply
ends.

- TRIED (2026-09-29, the fourth digest trim): the trim was real (14562 ->
  13415 bytes like-for-like, the injected text with the hook preamble) and
  the measure line recorded 13415; the rule reads bytes > 12000 on the
  newest line, so the Stop hook fired PROPOSAL NAMED at the reply's end.
  FAILED BECAUSE: the number recorded was a different measurement from the
  one the rule reads (the HOW line says `standup.py | wc -c`, the script's
  own output). DO INSTEAD: the way above; the second line (10855) closed it
  and both lines say what they measure.

See also: tools/ledger_trends.py (the HOW line under digest_size.txt);
docs/systems/self-audit.md "The digest size ledger"; "Apply a long
batch of file edits from the shell" below (the fifth trim's order:
edit, selftest, then measure and ledger).

## Trim every auto-memory store, not just the one that loads (the harness keys a store by the folder a session opens in, 2026-09-29)
Tags: lessons, memory, workstations | One machine can hold several auto-memory stores for one project; a trim that reads only the loaded MEMORY.md misses the others
Keys: auto-memory, memory trim, memory store, MEMORY.md, second store, parent folder, current-state-and-next-steps, banked memory, stub superseded

THE ONE RIGHT WAY: before a memory trim (or any claim about what
auto-memory holds), list every store for the project:
`ls ~/.claude/projects/ | grep -i everwood`, then each one's memory/
folder. A session opened at the repo folder and one opened at its parent
folder read different stores. Bank and stub each store the same way
(WORKFLOWS.md "Reference or restore a banked auto-memory"; WIKI_METHOD.md
"The harness memory").

- TRIED (2026-09-22 to 09-29): WS1's trim task sat open for a week while
  the loaded store (the repo folder's) already looked trimmed: two small
  entries. FAILED BECAUSE: the 14 untrimmed memories, including the
  current-state-and-next-steps.md the 09-29 systems audit named, lived in
  the parent-folder store (slug ...Everwood---Idle-Clicker, no repo
  suffix), which no repo session loads. DO INSTEAD: the listing above; the
  2026-09-29 trim banked all 14 plus the index into docs/systems/
  memory-bank.md.

See also: docs/systems/memory-bank.md "What stayed in auto-memory";
WORKFLOWS.md "Reference or restore a banked auto-memory"; docs/index/
notes.md (WS2's task to check its own stores).

## Copy a hook's stated line shape exactly (a RESOLVED line with a date prefix is invisible to verify_advisor, 2026-09-30)
Tags: lessons, hooks, delegation | When a hook prints the line it wants appended, that text is its parser's grammar; any prefix or reordering makes the line unread and the hook advises the same set forever
Keys: verify_advisor, delegation_pending, RESOLVED line, LEDGER ADVISED, hook parser, line format, append-only, date prefix

THE ONE RIGHT WAY: when a hook says "append `RESOLVED | <id> | OK/CORRECTED
- <words>`", append exactly that: first field the literal word, second the
id, nothing before it. The ledger's other lines carry dates; the RESOLVED
line does not, because tools/hooks/verify_advisor.py reads
`parts[0].startswith("RESOLVED")`. If a set keeps coming back ADVISED after
you resolved it, grep the hook for its parse before resolving it again.

- TRIED (2026-09-29 01:38): the four README-audit lanes were resolved as
  `2026-09-29 01:38 | WS1 | RESOLVED | D10e3e1 | ...`, matching the
  PENDING lines' shape. FAILED BECAUSE: the hook only clears a PENDING
  when a LATER line's FIRST field starts with RESOLVED; the dated lines
  never matched, so the set stayed ADVISED into 2026-09-30. DO INSTEAD:
  the exact shape; a wrong past line is never edited (append-only), a
  correct line is appended after it, naming the original.
See also: tools/hooks/verify_advisor.py; .claude/skills/brief/SKILL.md
"AFTER THE EMPLOYEE RETURNS"; SUBAGENTS.md rule 5.

## Exclude the generated wiki view from any grep over docs (one hit in wiki_view.html is the whole wiki, 2026-09-30)
Tags: lessons, tokens, tooling | docs/wiki_view.html holds every wiki file as one JavaScript line, so a recursive grep that matches it returns megabytes and the tool result is spilled to disk
Keys: wiki_view.html, grep docs, output flood, persisted output, --include=*.md, export_wiki_view, big read

THE ONE RIGHT WAY: a recursive grep over docs/ or the repo root always
narrows to markdown (`--include=*.md`, or the Grep tool's `glob`) or
excludes the view (`--exclude=wiki_view.html`). The view is regenerated by
tools/export_wiki_view.py from the .md files, so it never holds a fact the
markdown does not; matching it adds nothing and costs the whole output.

- TRIED (2026-09-30, the contradiction sweep's verify step): `grep -rn
  "placeholder until" docs *.md` to find a quote. FAILED BECAUSE: the third
  hit was docs/wiki_view.html's DATA line, 1.3 MB, and the harness spilled
  the result to a file; the two lines I wanted were at the top and the
  lint verdicts I also needed were at the bottom, both unread until a
  second call tailed the spill. DO INSTEAD: the include flag; when a
  result does spill, `tail -c` the saved file rather than re-running.
See also: tools/export_wiki_view.py; docs/systems/tooling.md; LESSONS.md
"Copy a hook's stated line shape exactly" (the same batch).

## Walk the transcript tree, never list it (employee sessions live in <session>/subagents/, 2026-09-30)
Tags: lessons, tooling, tokens | A miner of the harness transcripts that lists only the project's top-level folder sees the manager's sessions and none of the employees', which is where most guard denials and most spend happen
Keys: transcripts, subagents folder, os.walk, listdir, guard_replay, usage_window, usage_report, transcript miner, employee transcripts

THE ONE RIGHT WAY: any script that reads ~/.claude/projects/<slug>/ walks it
recursively (os.walk or rglob) and takes every *.jsonl it finds; the
employees' transcripts sit one level down in <session-id>/subagents/. Before
trusting a miner's first table, count the files it opened against
`find <slug> -name "*.jsonl" -mtime -7 | wc -l`.

- TRIED (2026-09-30, guard_replay.py's first real run): collect_calls()
  used os.listdir on the top level, replayed 889 calls, and reported that
  every guard matched its live behaviour exactly. FAILED BECAUSE: 17 of
  the 31 recent transcripts were employee files under subagents/, holding
  five of the six live INDEX FIRST denials; the table was drawn from
  two thirds of the traffic. DO INSTEAD: os.walk (the fix, one hunk); the
  true table was 1261 calls, INDEX FIRST 9 would / 10 live / 1 lost.
See also: tools/guard_replay.py; tools/usage_window.py; tools/usage_report.py
(transcript_dirs, which already walks); LESSONS.md "Widen a proxy after
its first real run".

## Unset ELECTRON_RUN_AS_NODE before any Electron app's CLI from a Claude Code shell (Unity Hub ran as bare Node, 2026-10-05)
Tags: lessons, tooling, workstation | VS Code's Claude Code shell exports ELECTRON_RUN_AS_NODE=1, so an Electron binary launched from it (Unity Hub, any Electron CLI) starts as plain Node and fails "Cannot find module '--headless'"
Keys: Unity Hub, headless, ELECTRON_RUN_AS_NODE, MODULE_NOT_FOUND, Electron CLI, env -u, install editor, Art of War

THE ONE RIGHT WAY: launch an Electron app's command line with the variable
removed: `env -u ELECTRON_RUN_AS_NODE "C:/Program Files/Unity Hub/Unity Hub.exe" -- --headless editors -i`.
The same flag is why `code`, Discord or any Electron tool misbehaves from
this shell; check for it before blaming the tool. A Hub catalogue query
(`editors -r`) can hang on the network; the install needs only the
version and changeset from ProjectSettings/ProjectVersion.txt, so skip the
query and install directly.

- TRIED (2026-10-05, installing Unity 6000.6.4f1 for The Art of War): ran
  the Hub's documented `-- --headless editors -i` from the repo folder,
  then from the Hub folder. FAILED BECAUSE: both printed Node's
  MODULE_NOT_FOUND for '--headless' - the process was Node, not the Hub,
  because the inherited environment carried ELECTRON_RUN_AS_NODE=1.
  DO INSTEAD: `env -u ELECTRON_RUN_AS_NODE` in front; the listing and the
  install then worked first time (editor + three modules in one call).
See also: WORKSTATION_METHOD.md (the kit); docs/systems/mods.md; the Art of War handoff (the local Claude notes at the root of the TheArtOfWar clone under Desktop, Unity).

## Never put a Windows path inside a Python heredoc's string literal (a `\U` in `Desktop\Unity` is a unicode escape, 2026-10-05)
Tags: lessons, tooling, workstation | A backslash-U or backslash-x in a normal Python string is an escape, so a one-off edit script carrying `C:\Users` or `Desktop\Unity` dies with "truncated \UXXXXXXXX escape" before it runs
Keys: unicodeescape, truncated UXXXXXXXX, heredoc, python - <<, Windows path, backslash, raw string, Edit tool

THE ONE RIGHT WAY: an edit that carries a Windows path uses the Edit tool,
or a raw string (r"...") in the script, or forward slashes. A `python -
<<'EOF'` one-off is for text without backslashes; the moment the
replacement text names a folder, switch tools.

- TRIED (2026-10-05, twice in one day: the mods.md See also, then the
  LESSONS See also): wrote the replacement text as a normal "..." literal
  with `Desktop\Unity` inside. FAILED BECAUSE: Python read `\U` as the
  start of a 32-bit unicode escape and refused the whole script with a
  SyntaxError; nothing was written. DO INSTEAD: the Edit tool for that
  line (it worked first time), or r"..." when a script must carry it.
See also: LESSONS "Unset ELECTRON_RUN_AS_NODE before any Electron app's CLI" above (the same day's other workstation trap); WORKSTATION_METHOD.md.

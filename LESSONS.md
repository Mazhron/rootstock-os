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

See also: ART_METHOD.md; docs/systems/art-pipeline.md "Gemini growth
sheets"; WORKFLOWS.md "Cut and wire new creature or plant art".

## Apply an audit's findings with a batch edit script (anchors quoted from a report)
Tags: lessons, process | An employee quotes a README sentence on one line but the file wraps it; grep every anchor before the script runs and make each replacement skip itself when its new text is already present, so a mid-way failure resumes instead of forcing a split
Keys: batch edit, edit script, anchor, assert count, wrapped line, audit findings, apply findings, readme audit, rep(), resumable, idempotent

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

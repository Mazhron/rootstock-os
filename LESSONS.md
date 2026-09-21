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

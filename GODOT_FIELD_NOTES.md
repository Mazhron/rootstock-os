# Godot Field Notes

Hard-won engine knowledge from building Everwood (Godot 4.4). Everything in
here was LEARNED THE EXPENSIVE WAY - measured, debugged, or shipped around -
so future work (this game or the next one) never pays for it twice. Portable
by design: nothing below depends on Everwood's code.

---

## Rendering and the 2D performance model
Tags: performance, gotchas | Renderer choice and per-item costs matter more than texture packing alone

- **GL Compatibility barely batches across canvas items.** Measured
  directly: forcing ONE texture onto ~5,700 sprites still produced ~2,400
  draw calls (~3 sprites per batch). A texture atlas bought only ~17% there.
  **Forward+ (Vulkan) has real 2D batching** - the same board dropped to
  ~520 calls, and the atlas multiplied its effect (3.7x under Forward+).
  If a 2D game has thousands of sprites, the renderer choice matters more
  than any texture arrangement.
- **You can split renderers per platform in one project:**
  `renderer/rendering_method="forward_plus"` with
  `renderer/rendering_method.web="gl_compatibility"` (and `.mobile`).
  Desktop gets Vulkan, the web export automatically keeps GL. Keep
  `config/features` renderer tag in sync.
- **Draw-call submission cost hides INSIDE TIME_PROCESS.** GL renders on
  the main thread within the process step, so no GDScript profiler line
  ever owns it. If your instrumented script costs sum to 15ms but
  TIME_PROCESS reads 50ms, the missing ~35ms is the renderer/driver.
- **Canvas item COUNT is its own cost, independent of batching**: roughly
  ~3us of main-thread processing per visible item per frame. 11,000 items
  on screen = ~30ms before a single pixel draws. Levers: cull sub-pixel
  decorations at far zoom, bake static content into chunk textures (see
  the soil pattern below), or MultiMesh.
- **Property setters are NOT free, even for unchanged values.** In Godot 4,
  `Sprite2D.flip_h`, `modulate`, and `z_index` setters trigger canvas
  redraws / RenderingServer calls without equality checks. A herd of 180
  idle creatures rewriting identical values 60x/s was a measured cost.
  On hot paths, guard every visual property write with `if new != old`.
- **`Label.text = same_string` still re-shapes the font.** Pooled floating
  text re-setting an identical string ~450x/s was a measured storm. Skip
  the assignment when the pooled node already wears that exact text.
- **CANVAS_ITEM_Z_MAX is 4096, and relative z STACKS.** A child at z 4090
  under a parent with any z silently overflows - the engine spams an error
  you only see on stderr. Leave generous headroom (we cap decor at ~3900).
- **Runtime texture atlas is easy and pipeline-free**: at load, collect
  every unique Texture2D (including procedurally generated ones a build-time
  packer could never see), shelf-pack into big `Image`s (2px padding,
  4096 max width for old web GPUs), `ImageTexture.create_from_image`, and
  swap each source for an `AtlasTexture` region. AtlasTexture is a drop-in
  Texture2D (get_width/height return the region), with ONE trap:
  **`AtlasTexture.get_image()` returns the WHOLE sheet**, so image-reading
  tools need a bypass lever.
- **Group atlases along the draw order.** Batches break when the texture
  changes along the z-sorted draw sequence - pack categories that draw
  adjacently into the same sheet, never split a category across sheets.

## Simulation architecture (the patterns that scaled)
Tags: architecture, performance | Pool objects, tick centrally in buckets, and let the grid be the spatial hash

- **Pool everything; never instantiate/queue_free during gameplay.** Pooled
  scenes implement pool_activate()/pool_reset(). Corollary trap:
  `is_instance_valid()` is TRUE for a pooled-and-recycled node - a stale
  reference points at a reused object. Guard cross-references with state
  flags, never validity alone.
- **No per-entity Timer or _process.** One central system ticks entities at
  a fixed rate split into buckets (each entity ticks every Nth tick with
  Nx dt). Smooth per-frame motion stays per-frame; hunger/growth/decay ride
  the slow tick.
- **Fixed-timestep accumulators NEED a catch-up cap** (`while accum >=
  interval` is a death spiral: a slow frame banks ticks, repaying them makes
  the next frame slower - we caught 28 ticks running in one frame). Cap at
  ~3 ticks/frame and DROP the remainder (`accum = fmod(accum, interval)`) -
  sim time stretches gracefully under load instead of killing the frame
  rate. **Scale the cap by Engine.time_scale** or your fast-forward setting
  silently under-delivers at low fps.
- **Stagger everything.** (1) Give each system's accumulator a different
  initial offset so they don't all fire the same frame. (2) If off-screen
  entities tick at half rate, alternate by ENTITY PARITY, not a global
  phase flag - a global flag makes every off-screen entity tick on the same
  cycle, producing a visible multi-second fps sawtooth (heavy cycle, light
  cycle). Even/odd stagger = same cadence per entity, flat load.
- **The grid IS the spatial hash.** A game on a cell grid needs no Area2D
  and no physics queries - "what am I standing on" is integer math, radius
  queries walk cells. We render 6,000+ interactive plants with zero physics.
- **Bake state into one texture** (the soil pattern): a whole 560x11 grid is
  ONE Image/ImageTexture (1px per cell, nearest filter, scaled up), painted
  per-cell only when a cell changes, uploaded per-row only when dirty. One
  draw call for the entire floor. The same idea extends to static flora
  chunks ("chunk baking") when item count becomes the ceiling.
- **Cache expensive AI scans WITH their misses.** The worst pathology was a
  starving animal rescanning a 441-cell radius every tick and finding
  nothing, forever. A short TTL memory (hit OR miss, ~2 ticks; shorter for
  chasers; cleared on panic) removed the cost without changing behavior.
  Likewise, an O(N^2) "is a predator near me" scan became O(N + K) by
  collecting the few predator positions once per tick.
- **Vision cones cost one dot product.** Directional senses (prey sees
  ~300 degrees, hunters ~200) add rich behavior for essentially free -
  cost lives in scan COUNT, not scan quality.
- **Engine.time_scale scales _process delta and timers** - a free sim-speed
  lever, with the catch-up-cap interaction above as its one trap.
- **No physics used? Drop `physics/common/physics_ticks_per_second` to 10.**
  Harmless. But do NOT trust `TIME_PHYSICS_PROCESS` to confirm anything -
  we measured ~11ms there with ZERO physics nodes, unmoved by the tick
  rate; the monitor apparently misattributes frame-pacing time.

## GDScript and API gotchas
Tags: gotchas | Godot 4 language and API traps that silently break code or drop behavior

- `-1 << 30` is a PARSE ERROR (negative shift operand). Use a plain literal
  sentinel.
- `var x := dict.get(...)` (inferred Variant) is a parse error in strict
  projects - write `var x: Variant = ...`.
- **Never call `Input.parse_input_event()` from inside input handling**
  (a pressed callback etc.) - the synthesized event is silently dropped.
  `call_deferred` it.
- **CanvasLayer is not a CanvasItem** - generic code reading `visible`
  across mixed node types should use `node.get("visible")`.
- **`load()` caches resources.** Mutating a loaded Image/Texture mutates it
  for EVERY user - a shared folder sprite resized "for one species" shrinks
  for all of them. `duplicate()` before editing.
- **Static vars survive scene reloads.** Any static flag a catastrophe or
  mode sets must be reset in the owning system's `_ready()`.
- **Autoloads process before the current scene** (tree order); among
  autoloads, project.godot order rules. Matters for anything that
  accumulates per-frame data across systems.
- Integer division truncates (`level / 4` on ints) - handy for banded
  curves, a bug when a refactor makes one side float.
- **Enum-typed exports serialize as text defaults in .tres parsing tools**:
  a .tres omits fields at default value, so external tools reading tres
  files must also parse the script's defaults - and an enum default reads
  as `Op.ADD`, not a number. Write explicit values in generated tres files.

## Files, editor, and project plumbing
Tags: gotchas, process | Editor, export, and tooling traps that cause silent failures

- **Hand-written .tscn typed node exports need the header attribute** or the
  export silently stays null:
  `[node ... node_paths=PackedStringArray("soil")]` + `soil = NodePath(...)`.
- **PowerShell `Set-Content`/redirects write a BOM** that Godot's .tres
  parser rejects (`Parse Error: Expected '['`). Worse, a BOM once entered
  project.godot as a garbage duplicate key and survived for weeks. Write
  engine files from tools that emit clean UTF-8.
- **New asset FOLDERS require a `--headless --import` pass** - the silent
  failure is flat colors and no .import files beside the PNGs.
- **Export presets are addressed BY NAME**: `--export-release "Web"` fails
  informatively only if you read stderr; check `export_presets.cfg` for the
  actual names.
- **`--quit-after N` counts FRAMES, not milliseconds** - and headless
  `--fixed-fps` runs as fast as the CPU allows, so N frames of simulated
  time can pass in seconds (or a "25 minute" mistake).

## Debugging and measurement (the toolkit that cracked the case)
Tags: process, performance | Instrument every frame and measure windowed, not just headless, to find real costs

- **Read stderr.** `2>$null` hid SCRIPT ERRORs for days: a totally silent
  test run almost always means a parse error upstream, not a hung test.
  Engine error spam (like the z overflow) is stderr-only.
- **A frame-time watchdog beats guessing**: an autoload that logs any frame
  over threshold with `Performance` monitors (draw calls, objects, nodes,
  orphans, memory) plus game context. Orphan/node growth = leak;
  draw-call explosion = render burst; high process with low draws = script.
- **A cost ledger names the culprit**: wrap every per-frame `_process` with
  usec timing reported to the watchdog (`rename body to _frame(), add a
  4-line wrapper`), print the top costs on each spike line, and compute
  `unaccounted = frame - process - physics` (that remainder is render).
  When everything is instrumented, whichever key dominates IS the answer.
- **Per-second RHYTHM lines catch what spike lines cannot**: one compact
  line per second (fps, worst frame, the second's summed top costs) makes
  multi-second waves - like the off-phase sawtooth - readable at a glance.
- **Measure draw calls in-game, windowed**
  (`Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`), and bisect by hiding
  layers (plants off, fx off, one-texture-for-everything...). The
  one-texture experiment is what proved the GL batching truth in minutes
  after days of atlas theory.
- **Headless benches cannot see the render side.** A sim that benches at
  1.5ms/frame can still play at 15fps - always pair a bench with a
  windowed measurement before concluding anything about frames.
- **Prove time-scaling claims with a truth test** (count real frames to a
  sim event at 1x vs 3x). Ours read ratio 2.98 and turned a "bug report"
  into two real findings elsewhere.
- **Visual regressions: capture a screenshot from the game itself**
  (`get_viewport().get_texture().get_image().save_png(...)`) behind an env
  var, and compare before/after. Cheap, scriptable, decisive (verified the
  atlas and the Forward+ switch render identically).

## Process habits that repeatedly paid off
Tags: process, lessons | Self-test everything, data-drive every number, and trust player reports

- Self-test everything behind env vars with one PASS/FAIL line; run tests
  headless before every commit. A parse error that reaches main costs more
  than every test run combined.
- Data-drive every number (resources, not code constants). Twice we had to
  migrate hardcoded systems (perm costs, then the whole eternal shop) into
  resources so tools could edit them - starting data-driven is free.
- Guard generated patches: bash heredocs collapse backslash-newline
  sequences inside embedded code, producing joined lines that sometimes
  still parse (worse than failing). Literal-string edit tools for any
  continuation-bearing code.
- Filter test output by the string the test ACTUALLY prints ("TOOLTEST
  water:" does not contain "TEST:").
- When a player reports something impossible ("hidden animals are not
  behind the brush"), believe them: the per-frame row sort was clobbering
  the z shift every frame. The report was exactly right.

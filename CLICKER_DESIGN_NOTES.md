# Clicker / Idle Design Notes

Genre knowledge earned building Everwood, written PORTABLY: what carries to
the next clicker/idle game, with Everwood only as the worked example. The
three-layer rule: engine facts live in GODOT_FIELD_NOTES.md, genre patterns
live HERE, game-specific detail lives in that game's own docs.

---

## Cost curves (the shapes, and when each feels right)

The full toolkit, all worth exposing as data on every upgrade:

- **Plain exponential** `base x growth^level` (growth ~1.1-1.7): the
  workhorse for in-run upgrades. Low growth = long satisfying chains.
- **Tier bands**: every N levels stacks another multiplier on top of the
  smooth curve. Long (50+) chains get harder in VISIBLE STEPS instead of
  one smooth wall - players see the band boundary coming and push for it.
- **Smooth ramp**: the multiplier itself grows each level
  (`growth + ramp x levels_owned`, e.g. x2, x2.5, x3...). Super-exponential;
  ends a chain fast. Good for "few, weighty" purchases - dangerous as a
  default (see the parity lesson).
- **Banded meta curve** `base x growth^floor(level / band)`: flat stretches
  then jumps. This is how a 500-level prestige upgrade stays reachable
  without a hyper-exponential chain making level 40 the real cap.
- **Dual-currency prices** (two banks, optionally separate growths per
  currency) make one purchase pull on two economies at once.

**THE PARITY LESSON (learned the hard way):** always compare CUMULATIVE
curves across currencies the player can substitute. Everwood's permanent
upgrades hit 3.3M meta-currency by level 16 while the ENTIRE 50-level
in-run chain cost 3M run-currency - so no rational player would ever buy
permanent. If a permanent and a run version scale identically, permanent is
strictly better (pay once, own forever) - so perm should be consciously
steeper or higher-based, by a chosen margin, not by accident of formula.

**Coupled knobs bite.** When two systems read a min/max of two tunables
(Everwood: natural sprouts charge `min(sprout_cost, fertile_threshold)`),
retuning one silently drags the other. Document every coupling next to the
knobs, and retune them together.

**Everything data-driven from day one.** Twice we had to migrate hardcoded
cost systems into resources so tools could edit them. Starting data-driven
is free; migrating later costs a day each time.

## Clicking and auto-clicking

- **The taught verb is CLICK.** Holding/auto-fire is an UPGRADE the player
  earns - never teach "hold" first, or the upgrade means nothing.
- **Batch the RATE, never the footprint.** An auto-clicker at 16/s with a
  visual cap draws 4 pulses/s, each carrying 4 clicks' worth of power by
  math - totals identical, draw cost quartered. But every target the pulse
  touches still shows ITS OWN number with the batch folded in: players
  notice missing feedback immediately (a real report). Manual clicks are
  never batched.
- **AOE clicks earn on the whole footprint**, so a wider-reach upgrade
  visibly increases income per click, not just coverage.
- **Bank clicks on slow targets.** Progress-toward-a-thing (clicks toward a
  free birth, vitality toward a sprout) should be MONOTONIC and shown on
  the target - a click that visibly banked is never a wasted click.

## Progression, gating, and discovery

- **Mystery rows** ("??? - unlocks after N Rebirths") pace discovery across
  prestiges; never show the name or effect early. In-shop chains
  (requires / requires-N-levels / requires-MAXED) sequence within a run.
- **Locked things say HOW to unlock, inline** ("locked - requires 1 level of
  Stronger Pulse"). A lock without a path is just frustration.
- **Shelf order: buyable first, mysteries soonest-first.** The next goal is
  always visible at the top of the fog.
- **Playtest mode bypasses every gate**, and tests get their own bypass
  lever - both standing, or gates make iteration miserable.
- **Every number is a baseline, not a constant**: meta progression retunes
  run numbers at run start, so nothing balance-relevant is inlined in logic.

## The prestige economy

- **Two currencies from two DIFFERENT sources** keeps prestige interesting:
  one from lifetime accumulation (a % of everything earned - note: ALL
  earned, not unspent, so spending during a run is never punished at the
  payout), one from a CENSUS of what is alive/standing at the moment of
  prestige - rewarding a built ecosystem, not just a big number.
- **Weight value at EARN TIME, not payout time.** Bank earnings into
  buckets stamped with the difficulty active when earned; the payout sums
  buckets x their own multipliers. This kills the classic exploit of
  flipping to max difficulty right before prestiging.
- **Snapshot on disaster.** When a catastrophe strikes, bank the payout the
  player COULD have taken that morning - they can always prestige on their
  pre-disaster peak. Removes the "lost everything" sting without removing
  the loss.
- **First-arrival bonuses** (a grant the first time each species/feature
  appears in a run) reward breadth, not just depth.
- **Permanently owned = owned.** A meta-bought starting level grants its
  unlocks (tools, modes) at run start exactly like an in-run purchase; the
  run's shop continues from that level at that level's price.
- **Measure the loop, don't guess it.** Scripted probes told us: first
  prestige ~x1.8 power and -44% clicks to the same milestone; by prestige
  #3 a single upgrade line plateaus (~x9.7) because one basket saturates -
  later prestiges need the SHOP'S BREADTH to keep compounding. Design meta
  shops so depth hands off to breadth.
- Keep a capped **prestige history ledger** from day one - the stats page
  and the balance passes both want it.

## Offline progress

The shape that worked: while away, earn a FRACTION of the run's recent
income PACE - a slow EMA sampled during play and saved with the campaign -
at base X% per real hour, +Y% per meta level, with an HOURS CAP (base ~8h,
extendable by its own upgrade) so a months-old save cannot detonate the
economy, a minimum-gap so relaunch-spam earns nothing, and a "while you
were away" report card on return. Pace-based (not state-simulated) offline
is cheap, exploit-resistant, and reads fair.

## Feedback economics (numbers the player can trust)

- **Ship the whole suffix ladder** (k, M, B, T, Qa, Qi, Sx, Sp, Oc, No,
  Dc...) from the start - idle games reach big numbers faster than you
  think, and "1e15" mid-game reads as a bug.
- **Floating numbers are an economy of their own**: pooled, SMALL font
  (dozens fly at once; big text becomes an unreadable wall), a minimum
  threshold so wide AOE never sprays "+0.01" a dozen times, and a static
  "left until the next thing" progress number ON the target so mass
  clicking reads as banking, not noise.
- **Every visual firehose gets a Graphics dial** (On / Intermittent / Off):
  click flash, gain numbers, progress numbers, visual rate caps. Players
  on weak machines will thank you; the tracer will too.
- **Per-source breakdowns build trust.** Showing income split by faucet
  (clicks, growth, creatures, rain...) - with a reconciliation row so the
  table ALWAYS sums to the total - turns "is this broken?" into "oh, THAT's
  where it comes from."

## Balance instrumentation (the telemetry that answers "where do they stall")

Build a local, opt-in, per-event progression log:

- An EVENT is an upgrade purchase; purchases within ~20s coalesce into one
  spree (players buy in bursts - per-purchase rows are noise).
- Between events record: real seconds, in-game days, clicks, every gain by
  SOURCE, every currency by branch, populations born/died/alive, soil/world
  milestones.
- A prestige CLOSES the segment list and starts a new one, stamped with the
  permanent purchases made at the seam.
- Export TXT (readable) + CSV (spreadsheet) per session.

This answers empirically what no amount of playtesting-by-feel answers:
time-between-upgrades curves, dead stretches, which faucet actually funds
each era. Pair it with a frame-time tracer (see GODOT_FIELD_NOTES.md) so
balance sessions double as performance sessions.

## The tooling workflow ("nothing lives only in code")

The single highest-leverage decision of the project:

- **Design webs**: self-contained HTML editors GENERATED from the real game
  data - every upgrade/species as an editable card, field definitions
  PARSED from the data script itself so new fields need zero tool changes.
  Edits live in browser localStorage; Export writes a JSON; an apply script
  patches the real resources; regenerate and reset.
- **Compare tables** (one category side by side, one column per stat, every
  cell editable, arrow keys walk columns) with COMPUTED columns - total
  cost of the whole chain, effect at max - because cumulative numbers, not
  per-level numbers, are what decide balance.
- **Tree views** with requirement edges and draggable gate lines are the
  design conversation; the exported JSON is the spec.
- **The iron rule**: if a designer cannot edit a number in the tool, that is
  a bug. Every cost, curve, gate, max level and effect belongs on data the
  tool can reach - the moment something "lives in code," tooling rots
  around it.
- Commit subjects are the changelog (player-readable, exported by script);
  ship builds every batch; never delete old build zips - before/after
  captures need them.

## Living-ecosystem idle (the sub-genre lessons)

If the idle economy is an ECOSYSTEM (creatures, food chains) rather than
pure numbers:

- **The land decides the herd**: food supply sets a target population;
  breeding fills TOWARD the target and never past it; arrivals trickle.
  Without the gate, two well-fed founders max out any population cap.
- **Render caps fold into multipliers**: population beyond the sprite
  budget lives as a "community" stat on the drawn entities (bigger appetite,
  bigger yield) - the ecosystem keeps growing without more nodes.
- **Sense gates must match eat gates.** Everwood's grazers could neither
  see nor eat plants below stage 2 - and grazing knocks plants DOWN stages,
  so cropped meadows became invisible food and animals starved amid plenty.
  Any "minimum quality" threshold on food must apply to sensing and eating
  identically, and consumption must not push food below its own floor.
- **Starvation drains a bank, not a switch**: hunger empties a belly, then
  emptiness drains stored vitality/HP - a well-fed life buys a long grace.
  And only TRUE empty should drain: early-bleed thresholds compound with
  every other pressure (hiding prey nearly wiped the predators).
- **Prey/predator behavior is cheap richness**: stop-to-eat, storm shelter,
  hiding with a visible tell, vision cones (one dot product), corpses that
  persist and feed - each was a few constants and a state flag, and
  together they read as "alive" to players.

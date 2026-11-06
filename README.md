# Rootstock

### A project operating system for Claude Code

**Keep the context small, make clearing the chat lossless, let cheap
sub-agents do the reading.**

Kit version: **v1.60** (2026-11-06). The graft log `UPGRADES.md` is the
single source of truth; this line is checked against it on every sync.

Rootstock is a folder of method files, scripts, skills and hooks you hand
to Claude Code inside your own repo. It is for anyone running a real
software project with Claude over weeks, not hours: the kind where the
sixth hour of a session costs several times its first, where the chat
gets cleared and the thread is lost, and where "did it actually run the
tests" is a fair question. It grew inside one shipped project (Everwood,
an idle game) and every rule in it was paid for there. This page is the
short form; [README_FULL.md](README_FULL.md) is the long one, with the
receipts, every pillar and the questions people ask.

## What changes: the context, before and after

The bill is the context. The whole conversation plus every file ever read
rides along with EVERY request, so Rootstock has one idea: keep the
manager's context small and let disposable contexts do the reading.

```
A LONG SESSION WITHOUT THE KIT                  THE SAME WORK WITH THE KIT
+------------------------------------------+    +------------------------------------------+
| CLAUDE.md grown to ~10k tokens, loaded   |    | CLAUDE.md a pointer core, ~900 tokens;   |
|   every turn                             |    |   a lint fails it past its budget        |
| whole files read, ~35k tokens per Read,  |    | headings grepped, one section read:      |
|   re-read by every later turn            |    |   ~10k per Read once the habit lands     |
| the conversation never cleared:          |    | /clear after a checkpoint; the next      |
|   810-898k tokens re-read PER REQUEST    |    |   session resumes from a 3-4k digest:    |
|   at the peak                            |    |   ~267k per request for the same work    |
| sub-agents inherit the manager's model;  |    | employees pinned to the cheap tier; the  |
|   their search results land in the       |    |   manager gets a stamped, metered report |
|   manager's context                      |    |   and never the files                    |
+------------------------------------------+    +------------------------------------------+
```

Every number is the origin project's own meter from the harness
transcripts, before and after each habit changed (README_FULL.md "The
receipts"). One project's honest metering, not a controlled benchmark; the
mechanism is arithmetic.

**What it costs you back.** The kit's own hooks put text into the context
too, and the usage sheet prints that beside the savings every run. Metered
on the origin since 2026-10-02: ~61k tokens over 272 injections, 1.0% of
the new context written in the same window (the prompt gauge ~280 tokens a
prompt, the standup digest ~600 a session as the harness delivers it, a
guard's note under 130).

## Three ways in (pick a level)

| Level | Time | What lands | Hooks |
|---|---|---|---|
| **Lean** | an afternoon | a CLAUDE.md pointer core with a token-budget lint, a master index, one path-scoped rule, a day file, and the checkpoint and standup skills: `/checkpoint` writes the day file so /clear loses nothing, `/standup` reads it back | none; `hooks/settings.lean.json` is a deny list only |
| **Standard** | a day | lean + the reporting runner and ledgers, the delegation company (employees on the cheap tier, stamped briefs, verified reports), the skills shelf | `hooks/settings.standard.json`: the session loop, the three safety guards (shell, preserve, diet), the delegation pair; eleven entries |
| **Full** | a long session | everything, including the loops that measure the loop: the lesson loop, the intent loop, the format law and the purpose audit | `hooks/settings.json`: all eighteen entries |

Moving up is merging the next file's entries and running the front-door
steps it adds; nothing is reinstalled. The install stamp in your CLAUDE.md
records the level.

## Quick start (three commands)

```
git clone https://github.com/Mazhron/rootstock-os
cd your-project && claude
> read "../rootstock-os/0 - READ ME FIRST.md" and install the kit at the standard level
```

Claude asks the STEP 0 questions (project, engine, who manages, which
models are employees, your update policy, the level), builds the operating
system in order, and finishes with a definition of done you can check
yourself: the standup script runs clean, the core lint passes, every hook
answers its `--selftest`, the first commit is in. The front door is read
once (~2k tokens); it is not a CLAUDE.md and never loads per session.
Installing into an existing project? Claude inventories what you have,
proposes a mapping, and touches nothing without your yes.

You need **git**, **Python 3** and **Claude Code**. Missing one is fine:
the front door skips what it cannot do and records the skip.

## The four pillars, one line each

1. **The knowledge wiki** ([WIKI_METHOD.md](WIKI_METHOD.md)): CLAUDE.md
   points, the master index lists, topic files hold; a file's headings
   are grepped and one section is read.
2. **The reporting discipline** ([REPORTING_METHOD.md](REPORTING_METHOD.md)):
   every repeatable check is a script, every result a ledger line, and
   the standup relays yesterday's verdicts.
3. **The delegation company** ([SUBAGENT_METHOD.md](SUBAGENT_METHOD.md)):
   seven laws; employees on the cheap tier read and search, the manager
   gets a stamped, metered report and verifies it against the diff.
4. **Lossless sessions** ([SKILLS.md](SKILLS.md)): nine skills; a
   checkpoint writes both sides of the last exchange to the day file, the
   standup reads it back after /clear.

The harness enforces the laws itself: sixteen hooks
([HOOKS_METHOD.md](HOOKS_METHOD.md)) that refuse a destructive shell verb,
refuse the first whole read of a file past ~10k tokens, refuse an
unstamped brief, hold the manager to a checkpoint it named, and say when
the context is 80% spent.

## Glossary (the private words, linked)

- **CEO / manager / employee**: you, the Claude in your chat, the
  sub-agents it spawns ([SUBAGENT_METHOD.md](SUBAGENT_METHOD.md)).
- **The pointer core**: a CLAUDE.md that points instead of restating,
  under 200 lines and a token budget ([WIKI_METHOD.md](WIKI_METHOD.md)).
- **Checkpoint, standup, day file**: the clear-and-resume ritual and the
  file it writes ([SKILLS.md](SKILLS.md), [REPORTING_METHOD.md](REPORTING_METHOD.md)).
- **The diet**: read a section, not a file; say less; one script, not
  many calls ([WIKI_METHOD.md](WIKI_METHOD.md) "The read diet").
- **Graft**: how an update lands on an installed project, by concept,
  never by overwriting your files ([UPGRADES.md](UPGRADES.md)).
- **The one right way**: a lessons book read before the first try
  ([LESSONS.md](LESSONS.md)).
- **Ledger**: an append-only file one script writes and another reads
  ([REPORTING_METHOD.md](REPORTING_METHOD.md)).
- **Flag**: a read-only audit of a kit thing, green, yellow or red
  ([CONTRIBUTING.md](CONTRIBUTING.md), [FLAGS.md](FLAGS.md)).
- **The loss test**: a digest trim is kept only if the resumed session
  lost nothing it needed (README_FULL.md "Lossless sessions").

## What is in the box

| File | What it is |
|---|---|
| `0 - READ ME FIRST.md` | The front door: an install runbook read once (STEP 0 questions, the level, the install order as pointers, the definition of done); not a CLAUDE.md |
| `WIKI_METHOD.md` | The knowledge wiki: the token mechanics, the pointer core, the read diet, bootstrap |
| `LESSONS.md` | The one-right-way book's law and entry shape, plus a pointer index to every entry's home under `knowledge/` |
| `knowledge/` | The knowledge tree: `MANIFEST.md` (one row per file: kind, domain, size, one sentence) and `lessons/<domain>.md`, the origin's lessons by domain |
| `REPORTING_METHOD.md` | Scripts + ledgers: the three rules, the runner, bootstrap |
| `SUBAGENT_METHOD.md` | The delegation company: org chart, seven laws, assignments, scorecard, bootstrap |
| `SKILLS.md` | The skills shelf: what each ritual does and the skills rule |
| `skills/` | The nine skills, ready to drop into `.claude/skills/`: `/brief`, `/checkpoint`, `/correct`, `/flag`, `/intent`, `/preserve`, `/runaway`, `/ship`, `/standup` |
| `agents/` | Two agent files pinned to the cheapest tier, `explore.md` and `lookup.md`, for `.claude/agents/` |
| `rules/` | The first path-scoped rule, `wiki.md`, for `.claude/rules/`; it loads only when Claude reads a markdown file |
| `HOOKS_METHOD.md` | The hooks: the contract, the sixteen kit hooks by tier, the modes file, bootstrap |
| `hooks/` | The sixteen hook scripts and `_hooklib.py`, the library they share (copy to `tools/hooks/`); `README.txt` with the per-hook setup steps; three settings files, one per level (merge into `.claude/settings.json`; each carries a permissions.deny block for destructive shell shapes and secret files); `rootstock_modes.json`, the switches between each newer behaviour and the way it replaced |
| `WORKFLOW_METHOD.md` | The process registry: one runbook entry per repeatable task |
| `WORKSTATION_METHOD.md` | The machine inventory: the document, the survey script, the new-machine runbook |
| `INTENT_METHOD.md` | The intent loop: the why file in the owner's words, the claim-and-verdict ledger, the correction ritual |
| `SECURITY.md` | The security policy: what pulling the repo runs (nothing), what the community gate refuses, the private door for reporting |
| `SECURITY_METHOD.md` | The pre-production security audit: the gate before anything with a backend, a key or user data goes public |
| `reference tools/` | 43 working scripts to adapt, not rewrite: standup, checkpoint, the core lint, the usage sheet (with the overhead block), the runner, the update check, and the rest of the loops (README_FULL.md lists every one) |
| `UPGRADES.md` | The graft log: the kit version and how each update lands on an installed project |
| `CONTRIBUTING.md` | The format law and the purpose audit: the header every thing carries, the read-only flag ritual |
| `FLAGS.md` | The flag ledger: every kit thing's latest green, yellow or red, tallied, append-only |
| `GODOT_FIELD_NOTES.md` | Domain example: Godot engine lessons (skip if not Godot) |
| `CLICKER_DESIGN_NOTES.md` | Domain example: idle/clicker genre lessons (skip if not that genre) |
| `WORKED_EXAMPLE.md` | One task priced twice, step by step, with and without the kit |

The two domain files double as templates for what your own engine-notes
and genre-notes files grow into.

## Updating, taking part, origin

Updates are grafts, never file copies: `UPGRADES.md` lists each newer
concept and how it lands on your own files; the update checker pins to a
signed tag and verifies `SHA256SUMS` first. Contributions go through
`community/` (see `CONTRIBUTING.md`); nothing leaves your machine without
your yes. The kit was grown by **Mazhron (Travis Rhoda)** with Claude in
[Everwood](https://github.com/Mazhron/Everwood); a developer's own review
of this repo shaped v1.60 (the levels, this page, the overhead figure).

## License

MIT. Take it, graft it, grow something.

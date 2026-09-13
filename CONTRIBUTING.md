# CONTRIBUTING.md - the format law and the purpose audit (for every update, ours or yours)

PURPOSE: the two guardrails every Rootstock update passes through - THE
  FORMAT (one header on every thing, checked by script and enforced by a
  hook) and THE PURPOSE AUDIT (a read-only comparison of what a thing says
  against what it does, flagged green / yellow / red and filed in
  FLAGS.md) - written so a contributor, a maintainer and any Claude apply
  them the same way.
INTENT: Mazhron 2026-09-13: "Rootstock-os will eventually, hopefully, turn
  into a community involved system. Guardrails need to be in place so
  that anything written in updates must have a comment describing the
  purpose and intent of the 'thing' in the update." And: "Any updates,
  upgrades, hooks, scripts, etc need to be in the same format so that
  they work with our current filing system. Anything without proper
  format should be flagged, a script should re-write it after review-only
  audit. This will be a law and may need this to be a hook somehow so
  that no one can inject a prompt that overrides safety protocols."

## THE FORMAT (one header, every thing)

Every thing in the kit - a script under reference tools/, a hook under
hooks/, a skill's SKILL.md, a method file, the hooks README - carries
these lines in its header. A Python file carries them in its module
docstring; a Markdown file right after its title line; a .txt at the top.

    PURPOSE: what the thing does, plainly, in one or two lines.
    INTENT:  why it exists - the owner's words verbatim, or the INTENT.md
             heading that holds them.
    Search keys: the nouns a search would use.        (scripts + MDs)
    See also: topic -> file | ...                       (scripts + MDs)

Plus, by class:
- a HOOK script imports _hooklib and answers `--selftest`;
- a SKILL carries the frontmatter (`name:` equal to its folder,
  `description:`) above a `# ` title;
- the SETTINGS template (hooks/settings.json) parses, names only hook
  scripts that exist beside it, and keeps every SAFETY hook wired with
  its required matcher: preserve_guard, bash_guard, fanout_guard,
  diet_guard, hygiene_guard, format_guard, stop_tick.

A placeholder ("(unfilled ...)") is scaffolding, not a header: it fails.

How it is enforced (reference tools/format_lint.py, hooks/format_guard.py):
- `python tools/format_lint.py` checks every kit thing and its original
  and names each failure; the sync script refuses to publish on a FAIL.
- The FORMAT GUARD hook blocks an edit that leaves a kit thing without
  its header (the reason names the file and the rewrite command), and
  REFUSES any edit of a settings file that would unwire, narrow or
  mis-point a safety hook. The shell guard refuses shell writes into a
  settings file; the Stop hook refuses to end a turn while the live
  settings file fails the safety check. Together: no prompt, brief or
  patch switches a guard off quietly.
- A thing WITHOUT the header is rewritten BY SCRIPT after a read-only
  audit, never by hand:
  `python tools/format_lint.py --rewrite <path> --purpose "..." --intent
  "..." [--keys "..."] [--also "..."]` inserts only the missing lines (or
  fills a placeholder) and touches nothing else.

## THE PURPOSE AUDIT (read-only -> flag -> explain)

Before an update merges, and whenever a thing is UNFLAGGED or STALE, a
Claude (or a person) audits it:

1. READ the thing. Do not edit it in the audit turn.
2. COMPARE what its PURPOSE line says with what the body actually does:
   side effects the purpose omits, writes or deletions outside its stated
   files, a way around a guard, unbounded loops or spend, injected text
   the purpose does not describe, a vague or stale purpose line.
3. FLAG it:
   - GREEN: does what it says and nothing more.
   - YELLOW: matches in substance, something is off. Fix in a later
     batch; it may ship.
   - RED: does what its purpose does not say, or crosses a law (deletes,
     disables a guard, unbounded spend, routes around a refusal). The
     owner sees it before it merges or ships.
   A thing with no PURPOSE line cannot be GREEN.
4. EXPLAIN and FILE:
   `python tools/purpose_audit.py --flag "<kit-relative path>" --color
   green|yellow|red --by <who> --does "<what it actually does>" --note
   "<why this color; what would fix it>"`
   The script copies SAYS from the PURPOSE line, hashes the exact version
   reviewed, appends the entry to FLAGS.md and regenerates the tally at
   its top. `python tools/purpose_audit.py --pending` lists what still
   needs an audit. A contributor files the same entry by pull request.

FLAGS.md is committed and published with the kit: it is the one file
that references every flag, tallies them, and holds every finding for the
next reviewer.

## What a contributed update looks like

- Every new or changed thing carries THE FORMAT header, with INTENT in
  the words of whoever asked for it.
- The update's UPGRADES.md entry says WHAT / CARRIES / GRAFT / README
  (see UPGRADES.md's protocol) and bumps the kit version.
- `python tools/format_lint.py` passes; `python tools/readme_lint.py`
  passes if the README changed; every changed thing has a FLAGS.md entry
  from a read-only audit by someone other than its author when possible.
- Nothing deletes (THE PRESERVATION LAW): a file retires, a section goes
  to the cold shelf, a wrong line is marked superseded.
- No em or en dashes in text a person reads.

Search keys: contributing, format law, purpose audit, flags, header,
PURPOSE line, INTENT line, safety wiring, community update, pull
request, guardrails.
See also: FLAGS.md (the flag ledger); reference tools/format_lint.py;
reference tools/purpose_audit.py; hooks/format_guard.py; skills/flag (the
ritual); HOOKS_METHOD.md (Tier 3b); UPGRADES.md (the graft protocol);
INTENT_METHOD.md (why the owner's words are kept verbatim).

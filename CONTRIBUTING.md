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
hooks/, a skill's SKILL.md, a method file, the hooks README, the front door - carries
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
  diet_guard, hygiene_guard, format_guard, brief_guard,
  delegation_auditor, verify_advisor, stop_tick, session_end (the SAFETY
  table in format_lint.py is the list; this prose follows it).

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

## The community path (kit v1.49, NS-38 phase 1)

Two doors, by what you bring:
- TEXT (a lesson, a gotcha, a page of field notes, design notes, a
  graphics note): one markdown file in `community/inbox/` of the public
  repo, named `YYYY-MM-DD-<name>-<slug>.md`, stamped on line two
  `Contributed by: <name> | <YYYY-MM-DD HH:MM> | <kind> | <domain>`, by
  pull request. The contribution lint (reference
  tools/contribution_lint.py) runs on the pull request and refuses a
  file outside the inbox, a non-markdown file, a shell line or block, an
  install, a fetch, a deletion verb, an off-allowlist URL and an
  instruction aimed at a reading Claude. The owner reviews and merges;
  the file stays in the inbox for good and is grafted into its knowledge
  file in a later kit batch with the stamp kept (community/README.md).
- CODE (a hook, a tool, a skill, a change to a kit file): a PROPOSAL in
  the "Code proposal" issue form, with HOW IT WORKS, WHY IT WORKS, WHAT
  IT MIGHT HURT and a LEDGER (before and after). The owner builds it
  inside the laws above and credits the proposer in UPGRADES.md. A pull
  request carrying code is refused by the lint, by design: nothing a
  stranger pulls from the kit may be able to run on their machine.
The owner's own batches arrive by the sync script and pass the lint
untouched; their gates are the format lint, the README lint and the
purpose audit below. Main takes pull requests only, reviewed by the
owner, no force pushes, signed commits.
See also: community/README.md and community/TEMPLATE.md (kit repo only);
reference tools/contribution_lint.py; SECURITY.md; .github/ISSUE_TEMPLATE/
(the five forms); 0 - READ ME FIRST.md STEP 0 item 6 (the opt-in).

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
request, guardrails, community inbox, code proposal, contribution lint.
See also: FLAGS.md (the flag ledger); reference tools/format_lint.py;
reference tools/purpose_audit.py; hooks/format_guard.py; skills/flag (the
ritual); HOOKS_METHOD.md (Tier 3b); UPGRADES.md (the graft protocol);
INTENT_METHOD.md (why the owner's words are kept verbatim).

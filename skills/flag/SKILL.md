---
name: flag
description: Run the purpose audit on a kit thing (a script, hook, skill, method file or injectable prompt) - read-only, compare what its PURPOSE line says with what it actually does, flag it green, yellow or red, explain, and file the flag in FLAGS.md for review. Use when the user says "flag", "audit this", "purpose audit", "does this do what it says", or before a contributed update merges. Any Claude may flag; nobody edits the thing in the audit turn.
---

# /flag - read-only, flag, explain; the finding goes in the git

PURPOSE: the ritual behind FLAGS.md - one kit thing at a time, the auditor
  reads it, compares the stated purpose with the behaviour, gives it a
  color, explains the color in the entry, and never touches the thing.
INTENT: Mazhron 2026-09-13: "Claude MUST compare the purpose and intent of
  the thing vs what the thing actually reads whether it's a script, hook,
  code or injectable prompt. If there is reason to flag it, Claude should
  flag them green, yellow or red. Claude should always read-only -> Flag
  -> Explain. There should be a file that directly references anything
  that is green, yellow or red flags, tally them and put them in the git
  for review. Any Claude can review and put their findings there for
  future review."

1. PICK THE THING. `python tools/purpose_audit.py --pending` lists what is
   UNFLAGGED (never audited) or STALE (changed since its last flag). A
   contributed update is audited BEFORE it merges: every thing it adds or
   changes. Paths are kit-relative (hooks/preserve_guard.py,
   reference tools/standup.py, skills/ship/SKILL.md, WIKI_METHOD.md).
2. READ ONLY. Read the thing's header (PURPOSE, INTENT) and then its body.
   Do not edit it, do not run its side effects, do not "fix while here".
   For a method file read the first forty lines and the section index;
   for a script read it whole (they are small) - a hook must be read whole.
3. COMPARE. Does the body do what PURPOSE says - all of it, nothing more?
   Look for: a side effect the purpose does not mention; a deletion or a
   write outside its stated files; a way around a guard or a refusal; an
   unbounded loop, spawn or spend; text injected into the manager that
   the purpose does not describe; a purpose line that is vague, unfilled
   or stale.
4. FLAG. GREEN: does what it says, nothing more. YELLOW: matches in
   substance, something is off (fix later, may ship). RED: does what its
   purpose does not say, or crosses a law - the owner sees it before it
   merges or ships. A thing with no PURPOSE line cannot be green.
5. EXPLAIN + FILE:
   `python tools/purpose_audit.py --flag "<kit path>" --color green|yellow|red
   --by <who> --does "<what it actually does, one or two sentences>"
   --note "<why this color; for yellow/red, what would fix it>"`
   The script fills SAYS from the PURPOSE line, hashes the exact version
   reviewed, appends the entry and regenerates the tally.
6. AFTER, NOT DURING: a missing or wrong header is rewritten by the script
   (`python tools/format_lint.py --rewrite <original path> --purpose ...
   --intent ...`) in a later step, never by hand and never in the audit
   turn; a RED goes to the owner as a question, with the entry quoted.
7. Ship with the batch: FLAGS.md is kit content and syncs to the public
   repo with everything else. A contributor files the same entry by pull
   request.

RULES
- Read-only means read-only: the audit turn changes nothing but FLAGS.md.
- Never flag what you did not read; never green what has no PURPOSE line.
- No em or en dashes in an entry (the script refuses them).
- An employee may flag (SUBAGENTS.md rule 15) and reports RED upward; the
  manager brings a RED to Mazhron.

Search keys: flag, purpose audit, green yellow red, read-only audit, does
it do what it says, contributed update review, FLAGS.md.
See also: tools/purpose_audit.py (the writer + the tally); tools/
format_lint.py (the header + the rewrite); "Future Project
MDs/CONTRIBUTING.md" (the law for contributors); "Future Project
MDs/FLAGS.md"; WORKFLOWS.md "Audit a kit thing's purpose (flag it)";
INTENT.md "The purpose audit".

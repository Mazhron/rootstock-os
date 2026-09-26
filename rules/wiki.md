---
paths:
  - "**/*.md"
---
<!--
PURPOSE: path-scoped rule carrying the wiki convention at the moment a markdown file is read: headings are search keys, every section ends with See also, the core stays a pointer file, nothing is deleted
INTENT: Mazhron 2026-09-14: CLAUDE.md should simply point to everything else; the wiki hygiene rule belongs where wiki files are edited, not in the always-loaded core
Search keys: wiki rule, headings, see also, tags line, grow the wiki, read cheap, pointer core, preservation, cold shelf
See also: WIKI_METHOD.md; docs/index/MASTER_INDEX.md; WORKFLOWS.md "Diet the core"; tools/check_wiki_links.py; tools/hooks/hygiene_guard.py (SEE-ALSO)
(this comment is stripped before the rule enters context)
-->
# Wiki rules (loaded because a markdown file is open)

- READ CHEAP: `Grep "^## " <file>` first (the section index), then Read
  ONLY the section. Never a topic file whole unless doing a full pass.
- HEADINGS ARE SEARCH KEYS; every `## ` section ends `See also: topic -> file`;
  a hard-won section carries `Tags: t1, t2 | brief`.
- GROW THE WIKI: a subject that outgrows its home gets a topic file in
  docs/systems/ and ONE line in docs/index/MASTER_INDEX.md. New always-true
  knowledge goes to a sub-index or a path-scoped rule, never into CLAUDE.md
  (the lint fails past its budgets; WORKFLOWS.md "Diet the core").
- EVERY FILE TOUCHED gets headings + See-also then and there, no
  stop-the-world passes.
- NOTHING IS DELETED: retire, cold-shelve (docs/cold/INDEX.md) or mark
  superseded; a wiki section moves verbatim with a provenance comment.
- FEATURE RULINGS LIVE WITH THE FEATURE (Mazhron 2026-09-26: per-feature
  knowledge accumulates where the feature lives): a ruling about one
  feature lands in that feature's docs/systems/ topic file under
  `## Rulings` (date + his verbatim words, newest first); the WHY behind
  a project-wide or subtle ruling goes to INTENT.md, cross-linked both
  ways. Before building on a feature, read its Rulings section.
- Internal docs may use dashes; player-facing text may not (player-text.md).

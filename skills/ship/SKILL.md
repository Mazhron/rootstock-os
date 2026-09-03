---
name: ship
description: Ship a completed batch - commit with a player-readable subject, push, and (in projects with builds) refresh build zips without deleting old ones. Use after every completed work batch, unprompted.
---

# /ship - the per-batch ship ritual

Run after EVERY completed batch of work; the user should never have to ask.

1. Sanity: tests/checks relevant to the batch are green (trust the ledger -
   do not re-run identical green runs).
2. Version: bump if the batch warrants it (MINOR for a notable batch, MAJOR
   for a core-pillar milestone) in the project's single version source.
3. Commit: subject = one-line player-readable hook (it becomes the public
   changelog); body = player-readable detail bullets, same voice. Follow the
   project's text doctrines (in Everwood: no em/en dashes in player-facing
   text, including commit subjects).
4. Push.
5. Builds (projects that ship binaries): run the build script
   (`python tools/make_builds.py` in Everwood). NEVER delete older build
   zips - old versions are the "before" side of dev-log comparisons.
6. Tick the checkpoint counter (`python tools/checkpoint.py --tick`) and
   relay any warning.

Changelog EXPORT (publishing) stays a user-triggered step
(`python tools/export_changelog.py`) - do not run it unprompted.

Search keys: ship, commit ritual, batch end, build zips, changelog voice.
See also: checkpoint skill (arc-level close); REPORTING_METHOD.md (ledgers).

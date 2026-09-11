---
name: preserve
description: Retire a file, shelve a wiki section, or walk the twice-acknowledged delete grant - THE PRESERVATION LAW's conversational front. Use when the user says "preserve", "retire", "shelve", "cold shelf", "delete", "remove", "get rid of", "clean up", or when a task would otherwise delete anything. Never invoked by an employee; never used to route around the preserve guard.
---

# /preserve - move it, shelve it, or ask twice; never just delete

THE PRESERVATION LAW (the owner's ruling, 2026-09-10): neither the manager
nor any employee deletes a file, record or tree without the owner's
express permission given TWICE, and no script is written that deletes.
Knowledge is hard-won and never lost. The preserve guard
(tools/hooks/preserve_guard.py) refuses delete verbs, work-discarding git
verbs and deletion calls in new code; this skill is how the lawful moves
happen. The three moves are offered IN THIS ORDER; a later one is taken
only when the earlier ones cannot do the job.

1. NAME THE TARGET. Say exactly what would go and why (path, size, what
   references it). If the invocation carried a path (`/preserve
   scripts/old_thing.gd`), use it; otherwise ask. A wildcard, a folder
   the owner did not name, or "everything under X" is never a target.
2. RETIRE (files and folders inside the repo):
   `python tools/retire.py <path> [...] --reason "..."` - moves to
   _retired/<same relative path> (Godot resource types get a .retired
   suffix; the folder carries .gdignore; collisions get a numeric suffix,
   nothing overwritten) and appends docs/history/retired_files.txt.
   `--dry-run` previews; `--list` reads the ledger. If the target was
   referenced (a scene, an autoload, an index line, a See-also), fix the
   references in the same batch. Done: commit with a player-readable
   subject; no build unless game content moved.
3. SHELVE (a rarely-read wiki section that thins a hot file):
   `python tools/cold_shelf.py --move <file.md> "<## heading>" --reason
   "..."` - the section goes VERBATIM to docs/cold/<file>, a two-line stub
   stays under the hot heading, docs/cold/INDEX.md gains a line.
   `--dry-run` first; `--check` verifies every stub; `--restore` reverses.
   Cold by read count is NEVER a shelf reason on its own (the owner,
   2026-09-10) - only the owner picks what shelves, usually from
   wiki_heat.txt's ACTIVE-UNREAD list or by hand.
4. DELETE GRANT (rare by design - a branch, a stash, a generated tree, a
   file the owner wants GONE, when a move truly is not the answer):
   a. Ask, naming the EXACT target and size: "This will delete X (n
      files, y KB). Do you approve?" Wait for a yes.
   b. Restate and ask again: "To confirm: delete X and nothing else?"
      Wait for the second yes.
   c. Record all four texts verbatim:
      `python tools/delete_grant.py --target "<path>" --ask "<q>"
      --ack1 "<yes 1>" --ack2 "<yes 2>"` (single use, 15 minutes,
      ledgered in docs/history/delete_grants.txt; drive roots, the home
      folder and the repo root are refused here and by the guard).
   d. Run the ONE deleting command that names the target. The guard lets
      it through once and marks the grant used.
   e. `python tools/delete_grant.py --status` says USED; report the
      ledger line. Nothing else is gone.
5. Ship the batch per /ship (the retired_files / delete_grants ledger
   lines ride with it).

RULES
- The order is the law: retire before shelve before delete. Offer the
  cheaper move first even when the owner said "delete".
- Only the manager runs this, at the owner's word. An employee that needs
  a deletion STOPS and reports (SUBAGENTS.md rule 13 / the brief's
  preservation line).
- A refusal from the preserve guard is the owner's standing decision:
  never reword a command to slip past it, never write a script that
  deletes. Move the thing, or ask twice.
- A wrong memory or a wrong wiki fact is marked superseded in place, not
  removed.

IF A SCRIPT IS MISSING (new project): retire.py, cold_shelf.py and
delete_grant.py live in the kit's "reference tools/" (HOOKS_METHOD.md
Tier 2d bootstrap). Ask the owner for their future-project kit before
improvising a move.

Search keys: preserve, retire, cold shelf, shelve, delete grant, delete
something, remove a file, preservation law, never delete.
See also: WORKFLOWS.md "Delete something (the grant ritual)" + "Retire a
file or move a wiki section to the cold shelf"; HOOKS_METHOD.md (Tier
2d, the preserve guard); WIKI_METHOD.md (the cold shelf); SKILLS.md (the
shelf); SUBAGENTS.md rule 13.

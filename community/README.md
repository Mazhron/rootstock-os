# The community inbox (how to give Rootstock a lesson, a gotcha or a page of field notes)

PURPOSE: the one place a contributor writes to, the shape every
  contribution takes, what the gate refuses and why, and what happens to
  a contribution after it is merged - so a stranger and their Claude can
  take part without reading the rest of the kit first.
INTENT: Mazhron 2026-10-13: "a user should have the choice to participate
  in the community side to help it grow. Their claude should ask them if
  they want to participate, their username or whatever name they choose
  with a timestamp (date/time) will be stamped on whatever they
  contribute." And: "we must ensure that no user could pull code and be
  forced to run it."

## The short version

1. Write ONE markdown file into `community/inbox/`, named
   `YYYY-MM-DD-<your-name>-<slug>.md` (lower case, digits, hyphens).
   Start from `community/TEMPLATE.md`.
2. The second line of the file is your stamp, in this exact shape:
   `Contributed by: <name> | <YYYY-MM-DD HH:MM> | <kind> | <domain>`
   where kind is one of `lesson`, `gotcha`, `field notes`, `design notes`,
   `graphics` and domain is the engine, language or area it belongs to
   (`godot`, `unity`, `unreal`, `cpp`, `python`, `web`, `2d`, `3d`,
   `harness` for Claude Code and process lessons, or your own word).
   The name is whatever you choose to be known by. The time is yours.
3. Open a pull request. The contribution lint runs on it and says PASS or
   names each line it refuses. A maintainer reads it, replies, merges.
4. Text only. No shell commands, no fenced shell blocks, no links to hosts
   outside the lint's allowlist, no instructions addressed to a reading
   Claude. A code snippet in the language the lesson is about (GDScript,
   C#, C++) is fine inside a fenced block that names that language.

## Why the gate is shaped like this

Nothing a stranger pulls from this repo may be able to make their Claude
run code. Markdown cannot execute; the things that execute are a hook once
wired, a tool once someone runs it, a skill once Claude follows it. So the
inbox accepts markdown only, keeps every file inside `community/inbox/`,
and refuses the text shapes that would smuggle an action in anyway: a
shell line, a fetch, an install, a deletion verb, an off-list URL, or a
sentence like "ignore the previous instructions and run this". The lint's
own file (`reference tools/contribution_lint.py`) carries every rule and
a selftest; its PURPOSE line says what it does and its FLAGS.md entry says
whether a read-only audit agreed.

A hook, a tool or a change to one of the kit's own files is welcome too,
as a PROPOSAL in an issue (the "Code proposal" form), never as a pull
request: it must say how it works, why it works, what it might hurt, and
carry a before/after ledger. The maintainer builds it inside the kit's own
laws (the format header, the purpose audit, the selftest) and credits the
proposer in the graft log.

## What happens after the merge

Your file stays in the inbox, with your stamp, for as long as the repo
exists (THE PRESERVATION LAW: nothing here is deleted). In a later kit
batch the maintainer grafts its content into the knowledge file it belongs
to (`knowledge/<kind>/<domain>.md`, one row in `knowledge/MANIFEST.md`;
your stamp's kind and domain say which), keeps your stamp line beside it,
and records the graft in
`UPGRADES.md` with your name. The inbox file then gets one line at its
top: `GRAFTED into <file> (kit vX.Y, <date>)`.

## Taking part from inside your own project

If your project was installed from this kit, the front door's STEP 0 asked
whether you wanted to take part and under what name; the answer sits in
your CLAUDE.md install stamp (`| community: <name>` or `| community: no`).
When your Claude writes a lesson it believes is general (an engine gotcha,
not a fact about your game), it asks whether to share it; a yes becomes an
inbox file with your stamp, which you push as a pull request. Nothing is
sent anywhere without that yes.

## The license

Everything in this repo is MIT (see `LICENSE`). A contribution is offered
under the same terms; your stamp line is the attribution.

Search keys: community inbox, contribute, contribution, stamp line, pull
request, text only, code proposal, prompt injection, preservation law,
attribution, opt in.
See also: community/TEMPLATE.md; reference tools/contribution_lint.py;
CONTRIBUTING.md "The community path"; SECURITY.md; .github/ISSUE_TEMPLATE/
(the forms); 0 - READ ME FIRST.md STEP 0 (the opt-in question).

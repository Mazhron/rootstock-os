# SECURITY.md - what runs, what never runs, and where to report (kit v1.51)

PURPOSE: the kit's security policy for readers and contributors - which
  parts of Rootstock execute on a machine and only after whose yes, which
  parts can never execute, what the community gate refuses, and the
  private door for reporting a problem - so nobody has to guess whether
  pulling this repo is safe.
INTENT: Mazhron 2026-10-13: "Anything pushed would need to come with
  whatever is needed to authenticate that the code is not malicious, we
  must ensure that no user could pull code and be forced to run it."

## What pulling this repo runs

Nothing. A clone or a download executes no file. The things in the kit
that CAN run are, by class:
- `hooks/*.py`: run by Claude Code only once wired into a project's
  `.claude/settings.json`. The install runbook makes the owner approve
  that wiring by hand (front door STEP 4); the settings template is
  merged, never auto-installed; every hook answers `--selftest` first.
- `reference tools/*.py`: run only when someone runs them. They are
  meant to be adapted; their docstrings say what each reads and writes.
  Two can make a network call: `rootstock_update_check.py` does a
  read-only GET of this repo (or reads a local clone, which it pulls
  first) and sends nothing; since v1.51 it pins to the release tag for
  the kit version, fetches `SHA256SUMS` and `UPGRADES.md` at that tag and
  verifies the checksum before it reports a single graft; it does not
  check the tag's signature, you do (see "Verifying a release");
  `security_audit.py` makes plain requests to YOUR deployment, only when
  you pass `--url`. No other kit script touches the network.
- `skills/*/SKILL.md`: prompt text Claude follows when the owner types
  the slash command; a skill can ask Claude to run a kit script, never
  anything outside the project.
- Every markdown file: text. It cannot execute. The risk in text is an
  instruction aimed at a reading Claude, which is what the contribution
  gate below refuses and what the owner's own laws (the bash guard, the
  preserve guard, the format guard) refuse on the receiving side.

## What a contributor can change

Two lanes, and nothing else. Text goes in `community/inbox/*.md`
(markdown only; community/README.md). Python goes in one folder under
`community/code/<YYYY-MM-DD-name-slug>/` (kit v1.51; one or more .py
files and an optional README.md; community/code/README.md). The
contribution lint (`reference tools/contribution_lint.py`) runs on every
pull request and refuses a file outside those two lanes (hooks/,
settings.json, reference tools/ and .github/ stay refused from a
non-owner), a binary file, a shell line or shell block, a package
install, a web fetch, a deletion verb, a URL whose host is not on its
allowlist, and an instruction addressed to a reading Claude. In the code
lane it also refuses a .py without the four header lines (PURPOSE, INTENT,
Search keys, See also) in its docstring, without the stamp line
`Contributed by: <name> | <YYYY-MM-DD HH:MM> | code | <domain>`, or
without `--selftest`; a .py that imports a network module (urllib,
requests, socket, http.client and the like); and a .py that calls eval,
exec, compile, __import__, os.system, os.popen, shell=True, ctypes,
marshal or pickle.loads.

Two more checks run on the pull request, on GitHub's runner: a replay of
the kit's own bash guard and preserve guard over each contributed file
(`reference tools/guard_replay.py`; a deletion call or a shell-shaped line
is a refusal), and the file's own `--selftest` under a 60 second timeout.
The selftest never runs on a reader's machine, only on GitHub's.

A merged file is never wired. It sits in `community/code/` with its stamp,
does nothing, and is not part of any install. A different Claude audits
its purpose read-only (the flag skill) and files a `FLAGS.md` entry; only
after that may the owner graft it into reference tools/ or hooks/ in a
later kit batch, crediting the stamp in `UPGRADES.md`. A change to an
existing kit file is still a proposal in the "Code proposal" issue form,
built by the maintainer inside the kit's laws: the format header, a
selftest, a read-only purpose audit filed in `FLAGS.md`.

The main branch takes pull requests only, each reviewed by the owner;
force pushes are refused; the owner's commits are signed.

The pull request check runs from the pull request's own checkout, so a
pull request that edits the lint, the guard replay or the workflow file
is judged by its own copy. The backstops are branch protection (the
check is required and the owner reviews every merge) and the owner's
read-only purpose audit of every changed thing before the merge; a
change to any of those three files from a non-owner is refused by the
lint's own path rule in the first place.

## Verifying a release

Every release is checkable (kit v1.51). The repo root carries `SHA256SUMS`,
one hash line for every file except `.git` and build junk, written by the
sync script before each commit. From v1.51 on each kit version is also one
SIGNED annotated tag, `v<kit version>`, created and pushed by the sync
script after the push; an unsigned tag is never made, and a machine
without the signing key prints a refusal instead. To check a release by
hand, compare the hash of each file you pulled against its line in
`SHA256SUMS`, and confirm the tag's signature shows as verified in the
repo's tags view on GitHub. The update checker
(`reference tools/rootstock_update_check.py`) does the checksum half of
that before it lists grafts: it fetches `SHA256SUMS` and `UPGRADES.md` at the tag, and
prints `VERIFIED v1.51 (checksum matches)` or, on a mismatch, `UNVERIFIED`
and no grafts. An UNVERIFIED line means stop and tell the kit's owner.

## Reporting a problem

If you find a way for something pulled from this repo to run without the
reader's approval, or a text shape the lint lets through that should not
pass, report it privately through GitHub's "Report a vulnerability" on
the repo's Security tab (private vulnerability reporting is on). Do not
open a public issue for it. You will get a reply from the owner; the fix
ships as a kit version with a graft entry naming the class of problem,
never the exploit path, and you are credited if you want to be.

## What the origin project does about its own security

The kit carries `SECURITY_METHOD.md`: the pre-production audit a project
runs before anything with a backend, a key, an env file or user data goes
public, with `reference tools/security_audit.py` and a ledger line. The
origin project (a static game export, no backend) wrote its exemption
and re-audits the day a leaderboard, an account or a key arrives.

Search keys: security policy, what runs, hooks wiring, network calls,
contribution gate, private vulnerability reporting, signed commits,
branch protection, text only, code lane, community/code, never wired,
guard replay, SHA256SUMS, signed tag, verified release.
See also: community/README.md (the inbox rules, kit repo only); reference
tools/contribution_lint.py; CONTRIBUTING.md; HOOKS_METHOD.md
"Bootstrap"; SECURITY_METHOD.md; 0 - READ ME FIRST.md STEP 4.

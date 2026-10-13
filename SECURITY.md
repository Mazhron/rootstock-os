# SECURITY.md - what runs, what never runs, and where to report (kit v1.49)

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
  Two can make a network call: `rootstock_update_check.py` fetches this
  repo's `UPGRADES.md` over HTTPS (or reads a local clone) and sends
  nothing; `security_audit.py` makes plain requests to YOUR deployment,
  only when you pass `--url`. No other kit script touches the network.
- `skills/*/SKILL.md`: prompt text Claude follows when the owner types
  the slash command; a skill can ask Claude to run a kit script, never
  anything outside the project.
- Every markdown file: text. It cannot execute. The risk in text is an
  instruction aimed at a reading Claude, which is what the contribution
  gate below refuses and what the owner's own laws (the bash guard, the
  preserve guard, the format guard) refuse on the receiving side.

## What a contributor can change

Only `community/inbox/*.md`, and only text (community/README.md). The
contribution lint (`reference tools/contribution_lint.py`) runs on every
pull request and refuses a file outside the inbox, a non-markdown or
binary file, a shell line or shell block, a package install, a web fetch,
a deletion verb, a URL whose host is not on its allowlist, and an
instruction addressed to a reading Claude. Code arrives as a proposal in
an issue and is built by the maintainer inside the kit's laws: the format
header, a selftest, a read-only purpose audit filed in `FLAGS.md`.

The main branch takes pull requests only, each reviewed by the owner;
force pushes are refused; the owner's commits are signed.

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
branch protection, text only.
See also: community/README.md (the inbox rules, kit repo only); reference
tools/contribution_lint.py; CONTRIBUTING.md; HOOKS_METHOD.md
"Bootstrap"; SECURITY_METHOD.md; 0 - READ ME FIRST.md STEP 4.

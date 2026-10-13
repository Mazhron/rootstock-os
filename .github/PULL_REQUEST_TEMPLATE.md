<!-- A pull request to Rootstock carries text into community/inbox/ or one Python folder under community/code/. A change to an existing kit file (a hook, a tool, a setting) is a proposal: use the "Code proposal" issue form. -->

**My stamp:** `<name> | YYYY-MM-DD HH:MM`

**What this adds:** one line.

**Checklist** (the contribution lint checks the first four; a maintainer reads the rest)
- [ ] one file per contribution, in `community/inbox/`, named `YYYY-MM-DD-<name>-<slug>.md`
- [ ] line two is the stamp: `Contributed by: <name> | <YYYY-MM-DD HH:MM> | <kind> | <domain>`
- [ ] a `Tags:` line, a PURPOSE and an INTENT line (see `community/TEMPLATE.md`)
- [ ] text only: no shell commands or shell blocks, no links outside the allowlist, no instructions addressed to a reading Claude
- [ ] code only: one folder under `community/code/<YYYY-MM-DD-name-slug>/`, every .py carries the four header lines and the stamp with kind `code`, answers `--selftest`, imports no network module and calls nothing that executes text or a shell
- [ ] it is general (an engine, language or process fact), not a fact about my own project
- [ ] I offer it under the repo's MIT license; the stamp line is my attribution

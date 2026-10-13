# The code lane (community/code/)

PURPOSE: Say how a stranger contributes a Python script to the kit, what the pull request check refuses, and why a merged script is never run by anyone's machine until the owner grafts it in by hand.
INTENT: Mazhron 2026-10-13: "Anything pushed would need to come with whatever is needed to authenticate that the code is not malicious, we must ensure that no user could pull code and be forced to run it."
Search keys: code lane, community code, contributed script, selftest, guard replay, network module, graft, stamp line.
See also: community/README.md; CONTRIBUTING.md "The community path"; SECURITY.md; reference tools/contribution_lint.py; reference tools/guard_replay.py.

## The short version

One folder per contribution: community/code/YYYY-MM-DD-name-slug/ (lower case, digits and hyphens). Inside it go one or more .py files (names are lower case letters, digits and underscores) and an optional README.md that follows the same rules as an inbox note.

Every .py carries, in its module docstring, the four header lines of THE FORMAT (PURPOSE:, INTENT:, Search keys:, See also:) and a stamp line:

Contributed by: <name> | <YYYY-MM-DD HH:MM> | code | <domain>

Every .py answers a selftest flag and prints PASS or FAIL. It imports no network module and calls no eval, exec, system or shell.

When you open the pull request, three checks run on GitHub's runner: the lint reads the file as text, the kit's own bash and preserve guards are replayed over the file, and the selftest is run with a 60 second limit. Nothing runs on anyone else's machine.

## What the gate refuses

- Any file outside community/inbox/ and community/code/, and any file in the code lane that is not a .py or a README.md.
- A folder or file name in the wrong shape, or a folder nested deeper than one level.
- A script missing any of the four header lines, or the stamp line with the kind code.
- A script with no selftest flag and no selftest function.
- Any network module: urllib, requests, http.client, httpx, aiohttp, socket, ftplib, smtplib, websocket, websockets, telnetlib, xmlrpc. No kit tool reaches the network except the owner's update checker.
- Dynamic execution or a shell: eval, exec, compile, the import builtin, system or popen calls, shell=True, ctypes, marshal, pickle loads, importlib import_module.
- A line that the kit's guards would refuse (a deletion call, a fetch verb, a force push and so on).
- An instruction aimed at a reading Claude, or a link to a host that is not on the allowlist.
- Warnings only: an em or en dash, or a file over about 4k tokens.

## What happens after the merge

The file stays in community/code/ for good, with its stamp. The merge never wires it into hooks/ or settings.json, so it is only ever text sitting in a folder.

A maintainer and a different Claude audit its purpose read-only, comparing what the PURPOSE line says with what the code does, and file an entry in FLAGS.md.

If it earns a place, the owner grafts it into reference tools/ or hooks/ by hand in a later kit batch and credits the stamp in UPGRADES.md. Until then nobody's machine runs it unless they choose to run it by hand.

---
name: standup
description: Open a session - print the standup digest and hand back the last exchange (prompt + response) and project state before anything else. Use at session start, after /clear, or whenever the user says "standup".
---

# /standup - the session opener

1. Run `python tools/standup.py` from the repo root.
2. Relay the WHERE WE LEFT OFF block FIRST and faithfully: the user's last
   prompt AND the manager's last response (both sides of the final exchange),
   then state and next-likely. After a /clear the user has nothing - give it
   back unprompted.
3. Then summarize the rest of the digest briefly: version, open roadmap
   items, ledger tails worth noting, anything blocked.
4. End by asking what to work on, or naming the next-likely step.

RULES
- Never re-read notes/day files wholesale when the digest covers them;
  open a full file only where the digest points.
- Never re-run green tests at an unchanged version (trust the ledger).

IF THE SCRIPT IS MISSING (new project): this project lacks the reporting
kit. Ask the user for their future-project kit (SKILLS.md + REPORTING_METHOD.md
carry the bootstrap) before improvising a summary.

Search keys: session start, standup, resume after clear, where we left off.
See also: checkpoint skill (the other end of the loop); REPORTING_METHOD.md.

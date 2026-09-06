"""SessionStart hook: run the standup digest and inject it (Tier 1, #1).

Fires on startup, resume, /clear and after a compaction. This is the end
of "after /clear the CEO has nothing": the digest (THE LAST EXCHANGE mined
from the harness transcript + state + roadmap + ledger tails) arrives in
the manager's context without anyone typing "standup".

Search keys: session start hook, auto standup, resume after clear, compact.
See also: tools/standup.py (the digest); .claude/skills/standup (the ritual
this automates); tools/hooks/_hooklib.py.
"""
import os
import subprocess
import sys

from _hooklib import ROOT, TOOLS, context, read_input

data = read_input()
source = data.get("source", "?")
env = dict(os.environ, PYTHONIOENCODING="utf-8")
try:
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "standup.py")],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=100)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        out = "(standup.py failed rc=%s)\n%s" % (r.returncode, r.stderr[-800:])
except Exception as exc:  # never break a session over the digest
    out = "(standup.py could not run: %s)" % exc

header = ("[HOOK session_start | trigger: %s] The standup digest below was "
          "injected automatically by .claude/settings.json - the /standup "
          "ritual already ran; do NOT run standup.py again. Manager: on a "
          "fresh session or after /clear, relay THE LAST EXCHANGE block "
          "FIRST and VERBATIM (both sides, in quote blocks), then state + "
          "next-likely, then a brief digest summary, then ask what to work "
          "on. After a compaction, use it to re-anchor silently unless "
          "something in it contradicts the summary." % source)
context("SessionStart", header + "\n\n" + out)

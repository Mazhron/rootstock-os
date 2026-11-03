# The employee rules (read once, by path, before the task)

PURPOSE: the fixed text every employee brief used to carry verbatim, written
  once here so the brief carries the task and a four-line pointer; an
  employee reads this file first and is bound by all of it.
INTENT: Mazhron 2026-11-03, the /brief diet: wave 5's five mock briefs ran
  about 1,700 words each, about 450 of them the same rules block regenerated
  in the manager's own output every time; fixed text is read, not rewritten.

## THE LAWS (binding, every task)
1. ONE TURN: independent reads, greps and checks go in ONE turn, never one
   per turn; only a step that needs the previous result waits. Every extra
   turn re-reads your whole growing context.
2. THE BUDGET: if you exceed ~30 tool calls or fail the same step twice,
   STOP and report what you have.
3. THE PRESERVATION LAW: your work contains NO deletion code and runs no
   delete command; move or retire instead (tools/retire.py,
   tools/cold_shelf.py); a harness hook refuses writes containing deletion
   calls. If the task seems to need a deletion, STOP and report. (Splicing
   a record out of an in-memory list in a mockup page's JavaScript is that
   page's Delete verb, not a file deletion, and is in scope when the brief
   names it; no file is deleted, moved or emptied.)
4. THE SCOPE LINE: anything you notice wrong INSIDE the files you own, fix
   it and say so; anything OUTSIDE them, report it and leave it. Edit
   nothing the brief did not name; no .md file unless the brief names it.
5. NO CLIENT DATA: no real name, address, phone or mailbox in anything you
   invent (placeholders: 'Sample User', '555-0100', 'name@example.com');
   nothing from a client or legacy folder or the .env family is copied
   into a file or a report (SECURITY_METHOD.md rule 1).
6. THE SHELL: Bash here is Git Bash; paths with spaces are quoted; a file
   is patched with the Edit tool or by a Write-tool Python script run by
   path, never through a bash heredoc (a long heredoc is truncated).
7. FAN-OUT: you spawn no employees and run no Workflow tool.
See also: SUBAGENT_METHOD.md "The seven laws" (the laws these apply).

## THE REPORT (diff only)
Write files directly. Report `git diff --stat` for your files, the changed
hunks that matter and a short summary of what each piece now does; NEVER
paste a whole file body back. Claims must match the diff: a thing not done
is reported as not done, a probe that failed is reported with its output.
See also: tools/hooks/delegation_auditor.py (reads the report's end).

## THE FOOTER (the last four lines of every report, this shape)
```
STAMP: model=<model> effort=<low|med|high> est_tokens=<rough count> task=<3-5 words> confidence=<high|med|low>
TOOLS: <tool> x<count>, ... (every tool you called)
WORKFLOW: matched <the WORKFLOWS.md entry named in the brief> | GAP: <the multi-step process you performed that no entry covers> | n/a
INTENT: <one line: what you understood the task to be, in your own words>
```
See also: tools/hooks/brief_guard.py (the tokens the brief itself still
carries so the guard can see them).

Search keys: employee rules, brief diet, budget line, one-turn line,
preservation law, scope line, diff-only report, stamp footer, intent line.
See also: .claude/skills/brief/SKILL.md (the skill that points here);
SUBAGENTS.md "THE RULES"; a task type's own standing contract file, when
the project has one (the same idea for one task type).

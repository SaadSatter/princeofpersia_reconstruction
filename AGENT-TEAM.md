# Agent Team Log

> **Template.** Saad writes this page in his own voice. The rubric (5b)
> treats an agent-voiced log as missing authorship. The implementation agent
> only created the headings and the "how to run" notes; it must not fill in
> recommendations, decisions, reflections, or evidence links.

## Team configuration

| Agent | Artifact | Allowed to see | Allowed to do | Not allowed |
| --- | --- | --- | --- | --- |
| Implementation agent | `CLAUDE.md` | whole project folder, original source (read-only reference) | edit code/tests/docs, run tests | approve own work, write this log, run live trials without the student, commit secrets |
| Reusable skill: `game-rules-audit` | `.claude/skills/game-rules-audit/SKILL.md` | spec, map, checklist, interface/runner/agent code, tests | read, run deterministic tests, write `docs/audits/AUDIT-*.md` | edit code or tests |
| Independent reviewer: `rules-reviewer` | `.claude/agents/rules-reviewer.md` | same as skill, read-only | Read, Grep, Glob | edit, run commands, approve |
| Game-playing agent (model player) | `agents/model_player.py` | observations, legal actions, bounded history | submit one action per call | files, repo, engine state, evaluator |

## How to run the sessions (procedure, not evidence)

1. **Implementation session(s).** Start Claude Code in the project folder;
   it loads `CLAUDE.md`. Save the session link.
2. **Audit session A.** Start a *new* Claude Code session in the project
   folder. Run `/game-rules-audit`. The skill writes
   `docs/audits/AUDIT-<date>-A.md`. Save the session link.
3. **Audit session B.** Later, after changes, start another *new* session
   and run `/game-rules-audit` again → `AUDIT-<date>-B.md`. Two separate
   invocations satisfy "invoked in at least two sessions."
4. **Independent review.** Start a *new* session that did not build the
   code. Ask: "Use the rules-reviewer agent to review the project." Commit
   its output verbatim as `review.md`, with date and commit hash.
5. Record each session link in the evidence table below.

## Evidence (Saad fills in)

| Agent | Session / PR link | Date | What it recommended | What I decided and why |
| --- | --- | --- | --- | --- |
| Implementation | | | | |
| game-rules-audit (session A) | | | | |
| game-rules-audit (session B) | | | | |
| rules-reviewer | | | | |

## My decisions (Saad writes)

<!-- Scope, action vocabulary, level-data publication, baseline design,
memory/history choice, which findings I accepted or rejected. -->

## What I'd change next time (Saad writes)

<!-- -->

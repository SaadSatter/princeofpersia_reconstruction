# SMOKE-01: verify that the orchestration docs name only paths that exist

Handoff id: HO-SMOKE-01-orchestrator
Assigned agent: tech-lead (procedure: agents/tech-lead.md), read-only check; then qa (agents/qa.md)
Requested by: Saad, 2026-11-24: "Orchestration smoke test, task id SMOKE-01. It is a documentation-verification task: check that every repository path named in the Files table of docs/final/orchestration/README.md and in the 'Roles and configuration' table of CLAUDE.md exists on main at the current HEAD, and that each .claude/agents/*.md native definition points to a procedure file that exists. Run it through the normal chain [...] Gate 2 does not apply (no AI or boundary change)."
Requirements: orchestration integrity (`HANDOFF_PROTOCOL.md`, `README.md` "Files", `COURSE_ROLE_MAP.md`). No gameplay checklist row.
Decisions in force: #11 (orchestration records are committed to `main`).

## Context and dependencies

This smoke test exercises the native chain (orchestrator → tech-lead → qa →
orchestrator) with file-based handoffs. It changes no project file. No
dependency on any open task or WIP branch.

## Base

`main` at the **coordination commit** named in your prompt (the commit that
adds this brief; its parent is `2d40972`). "Current HEAD" in Saad's request
means that commit. Check paths against that commit's tree
(`git ls-tree -r --name-only <sha>`, `git cat-file -e <sha>:<path>`), not
against the working tree of any checkout.

## What to check

1. **README Files table.** Every path in the "Files" table of
   `docs/final/orchestration/README.md`. Paths there are relative to
   `docs/final/orchestration/`.
   - Literal paths (e.g. `HANDOFF_PROTOCOL.md`, `tasks/_EXEC_COMMON.md`)
     must exist.
   - Placeholder or pattern rows (`agents/<role>.md`, `tasks/<TASK-ID>.md`,
     `reports/<TASK-ID>-<role>.md`, `PLAN-YYYY-MM-DD*.md`,
     `DECISIONS-YYYY-MM-DD.md`, `handoff-drafts/`): count as present when at
     least one file matches. For `agents/<role>.md`, check each role the row
     names (orchestrator and the four workers: tech-lead, qa,
     evaluation-specialist, requirements-auditor) individually.
2. **CLAUDE.md "Roles and configuration" table.** Every path in both the
   "Native definition" and "Procedure" columns, including the Skills row
   (`.claude/skills/game-rules-audit/`, and `session-evidence/` and
   `evaluate-rival/` read as siblings under `.claude/skills/`, each with a
   `SKILL.md`) and the AI rival row (`agents/rl/`, `docs/final/RL_POLICY.md`).
   "itself" means the native definition file is its own procedure.
3. **Native definitions.** For each `.claude/agents/*.md` at the base commit,
   the procedure file its body tells the agent to read (e.g.
   `docs/final/orchestration/agents/<role>.md`) exists. A definition that is
   its own procedure (`rules-reviewer`) counts as pointing to itself; say so.
   Also report any `.claude/agents/*.md` that matches neither table.

Report each path with the result `present` / `MISSING` and how you checked
it. A missing path is a **finding**, not something to fix: do not create,
move or edit any file other than your report.

## Branches and permitted write paths

| Worker | Branch (created from) | May write |
| --- | --- | --- |
| tech-lead | `task/SMOKE-01` (from the coordination commit) | `docs/final/orchestration/reports/SMOKE-01-tech-lead.md` only |
| qa | `gate/SMOKE-01-qa` (from the tech-lead's report commit) | `docs/final/orchestration/reports/SMOKE-01-qa.md` only. No new tests are needed for this read-only task; put any proposed check in the report |

## Acceptance criteria

1. The tech-lead report lists every path from the README Files table, with
   `present`/`MISSING` and the command used.
2. The tech-lead report lists every path from the CLAUDE.md "Roles and
   configuration" table, with `present`/`MISSING` and the command used.
3. The tech-lead report lists every `.claude/agents/*.md` at the base commit,
   the procedure path it points to (quoted from the definition), and whether
   that path exists.
4. The tech-lead commit changes only its report
   (`git diff --name-only <coordination-sha>..<report-sha>`).
5. QA reads the tech-lead report at its commit, names it under `consumed:`,
   re-derives the path lists independently from the two tables and
   `.claude/agents/`, re-checks every path at the base commit, and states
   whether the tech-lead report is complete and correct.
6. The QA commit changes only its report.

## Required tests

`uv run pytest -q` once per worker on its branch (sanity: a docs-only check
must not disturb the suite). Paste the real result line.

## Required gates

Gate 1 QA: yes. Gate 2 Evaluation: **no** (Saad: "Gate 2 does not apply (no
AI or boundary change)"). Gate 3: orchestrator.

## Required evidence

The two reports, committed on their branches, with the commands and output.

## Approval needed before

Nothing. Do not push, merge, or edit any file outside the permitted paths.

---
handoff_id: HO-T21-tech-lead
task_id: T21
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T21.md@60f4805
source_branch: task/T21
source_commit: 2081398f6e6f9043adec1adad22844d9c5de6579
reviewed_commit: n/a
verdict: n/a
---

# T21: tech-lead report

Status: done

## Work completed
Added the `telemetry-analyst` worker (decision #69): native definition, procedure, a row in every role table, and a dry-run report on the T20 fixture. No code changed. The five role-table files differ between `main` and `orch/reviewed` (three are absent on `orch/reviewed`), so I checked them out from `main` (60f4805) and edited that text, so the PR does not revert orchestration records.

## Paths
- New: `.claude/agents/telemetry-analyst.md`, `docs/final/orchestration/agents/telemetry-analyst.md`, `docs/agent-sessions/T21-telemetry-analyst.md`, `docs/final/orchestration/reports/T21-dryrun-telemetry-analyst.md`, this report.
- From `main` plus my rows: `CLAUDE.md`, `docs/final/orchestration/README.md`, `docs/final/orchestration/agents/orchestrator.md` (worker table, routing row, branch table, "Analyst findings" paragraph in section 5), `.claude/agents/orchestrator.md` (description, `Agent(...)` list, spawnable list), `docs/final/orchestration/COURSE_ROLE_MAP.md`.
- Check with `git diff main -- <those five files>`: only my rows differ. Against `orch/reviewed` the diff of `.claude/agents/orchestrator.md` and `COURSE_ROLE_MAP.md` and `agents/orchestrator.md` shows whole files, because they are new there.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Definition loads: valid frontmatter, name `telemetry-analyst`, model pinned | yes (frontmatter parsed; not loaded by a live agent here) | `name`, `model: claude-sonnet-5-5`, tools `Read, Grep, Glob, Bash, Write`, no Agent. It spawns only after a session restart |
| 2 | Write permission is its own report only | yes | stated in both the definition and procedure section 4 and 5. Note: `Write` and `Bash` are tools, so the limit is by instruction, not by the tool list |
| 3 | All role tables agree | yes | CLAUDE.md (two tables), README agents table, orchestrator procedure (worker table, route, branches), `.claude/agents/orchestrator.md` (3 places), COURSE_ROLE_MAP (row, `team-` note) |
| 4 | Suite green, real line | yes | below |

Also: procedure carries the four T20-fix2 reading notes (flip, zero-gap DRAW/SHEATHE, no pooling of pre-fix2 logs, AI duels human-seat only); orchestrator procedure has the "not confirmed" rule.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1952 passed, 11 skipped, 5 xfailed, 2 warnings in 441.37s (0:07:21)
```
A first run with the work staged but uncommitted gave `3 failed, 1949 passed` (tests/test_qa_T08_probes.py ledger tests: "a real held-out run needs a clean tree"). Committing the work cleared it. The bare `uv run pytest -q` without extras fails at collection (13 errors, missing extras), as on earlier tasks.

## Findings
None. Scope check `git diff --name-only 72066f1..2081398`: the nine paths above (before this report), all permitted. One judgement: the brief's permitted list does not name the dry-run report path; I wrote it as `reports/T21-dryrun-telemetry-analyst.md` because item 4 requires it. Say if QA or the orchestrator wants it elsewhere.

## Known limitations
The dry run was written by me following the procedure, not by a spawned analyst (the agent type does not exist until restart). The fixtures are schema 1, hand-built, with no real players. A real first run of the agent is the true test of its definition.

## Unresolved findings
None.

## Requested next action
Commit to review: 2081398 on task/T21 (the report commit is on top of it)
What changed: a new read-only-on-logs worker, its procedure, and role-table rows. No game or AI code.
How to check it: `git diff main -- CLAUDE.md docs/final/orchestration/README.md docs/final/orchestration/agents/orchestrator.md .claude/agents/orchestrator.md docs/final/orchestration/COURSE_ROLE_MAP.md`; read the two telemetry-analyst files; recompute the dry run with `python3 tools/telemetry/summarize.py tests/data/t20_telemetry --out <dir>` and check each cited line.
What I am unsure about: whether `Write` and `Bash` can be confined to one path (they cannot by tool list; the limit is instructional, and QA should say if that is enough); the dry-run report path; whether a restarted session accepts the `Agent(...)` entry.
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
None.

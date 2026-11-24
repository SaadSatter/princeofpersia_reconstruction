---
handoff_id: HO-SMOKE-01-tech-lead
task_id: SMOKE-01
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/SMOKE-01.md@58ea6e7
source_branch: task/SMOKE-01
source_commit: see "Commit to review" below (the commit that adds this report)
reviewed_commit: n/a
verdict: n/a
---

# SMOKE-01: tech-lead report

Status: done (one finding: two paths named in CLAUDE.md are MISSING)

## Work completed
Created `task/SMOKE-01` from coordination commit `58ea6e7` (parent `2d40972`).
Dumped that commit's tree once (`git ls-tree -r --name-only 58ea6e7 > /tmp/smoke01_tree.txt`,
286 paths) and checked every path with an exact-line match
(`grep -qxF <path> /tmp/smoke01_tree.txt`). The worktree was clean at 58ea6e7,
so the filesystem agrees. No file other than this report was touched.

## Paths
`docs/final/orchestration/reports/SMOKE-01-tech-lead.md` (this file).

## 1. README "Files" table (paths relative to `docs/final/orchestration/`)
| Path | Result | How checked |
| --- | --- | --- |
| `agents/orchestrator.md` | present | exact match in tree |
| `agents/tech-lead.md` | present | exact match |
| `agents/qa.md` | present | exact match |
| `agents/evaluation-specialist.md` | present | exact match |
| `agents/requirements-auditor.md` | present | exact match |
| `HANDOFF_PROTOCOL.md` | present | exact match |
| `COURSE_ROLE_MAP.md` | present | exact match |
| `tasks/<TASK-ID>.md` | present (pattern) | `grep -c '^docs/final/orchestration/tasks/'` = 33 files; e.g. `tasks/SMOKE-01.md` |
| `tasks/_EXEC_COMMON.md` | present | exact match |
| `reports/<TASK-ID>-<role>.md` | present (pattern) | 20 files under `reports/`, e.g. `T01-tech-lead.md`, `T02-qa.md` |
| `reports/_TEMPLATE.md` | present | exact match |
| `STATUS.md` | present | exact match |
| `REVIEW_LOG.md` | present | exact match |
| `PLAN-YYYY-MM-DD*.md` | present (pattern) | `PLAN-2026-11-23.md`, `-v2.md`, `-v3-delta.md` |
| `DECISIONS-YYYY-MM-DD.md` | present (pattern) | `DECISIONS-2026-11-23.md` |
| `handoff-drafts/` | present (directory) | 1 file: `handoff-drafts/2026-11-24-qa-to-tech.md` |
| `inputs/FINAL_REQUIREMENTS.md` | present | exact match |

All 17 rows present.

## 2. CLAUDE.md "Roles and configuration" table
| Path | Result | How checked |
| --- | --- | --- |
| `.claude/agents/orchestrator.md` | present | exact match |
| `docs/final/orchestration/agents/orchestrator.md` | present | exact match |
| `.claude/agents/tech-lead.md` | present | exact match |
| `docs/final/orchestration/agents/tech-lead.md` | present | exact match |
| `.claude/agents/qa.md` | present | exact match |
| `docs/final/orchestration/agents/qa.md` | present | exact match |
| `.claude/agents/evaluation-specialist.md` | present | exact match |
| `docs/final/orchestration/agents/evaluation-specialist.md` | present | exact match |
| `.claude/agents/requirements-auditor.md` | present | exact match |
| `docs/final/orchestration/agents/requirements-auditor.md` | present | exact match |
| `.claude/agents/rules-reviewer.md` (procedure "itself") | present | exact match; its own procedure |
| `.codex/agents/pop-rule-reviewer.toml` (procedure "itself") | present | exact match; its own procedure |
| `.claude/skills/game-rules-audit/` | present | `.claude/skills/game-rules-audit/SKILL.md` exact match |
| `.claude/skills/session-evidence/` | present | `SKILL.md` exact match |
| `.claude/skills/evaluate-rival/` | present | `SKILL.md` exact match |
| `agents/rl/` | **MISSING** | `grep -c '^agents/rl/'` = 0; no `agents/rl*` path in the tree |
| `docs/final/RL_POLICY.md` | **MISSING** | exact match fails; `docs/final/` holds ART_PROVENANCE, CONFIGURATION, ENGINE_DECISION, EVIDENCE_INDEX, GDD, PROJECT_PLAN, README, REQUIREMENTS_CHECKLIST, VERSUS_SPEC and `orchestration/` |

## 3. Native definitions at 58ea6e7
`.claude/agents/` holds exactly six files. Procedure line quoted from each body:
| Definition | Procedure it points to | Exists? |
| --- | --- | --- |
| `orchestrator.md` (line 14) | "Your complete procedure is `docs/final/orchestration/agents/orchestrator.md`." | present |
| `tech-lead.md` (line 18) | `git show <coordination-sha>:docs/final/orchestration/agents/tech-lead.md` | present |
| `qa.md` (line 18) | `git show <coordination-sha>:docs/final/orchestration/agents/qa.md` | present |
| `evaluation-specialist.md` (line 18) | `git show <coordination-sha>:docs/final/orchestration/agents/evaluation-specialist.md` | present |
| `requirements-auditor.md` (line 17) | `git show <coordination-sha>:docs/final/orchestration/agents/requirements-auditor.md` | present |
| `rules-reviewer.md` | none: it is its own procedure (README row and CLAUDE.md say "itself"). Its line 16 reads `docs/final/orchestration/agents/tech-lead.md` only as the builder's limits, and that file is present | self |

Every definition matches a row in both tables; none is unlisted. Side note:
`evaluation-specialist.md` line 22 also names the `evaluate-rival` skill, which is present.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | README table fully listed | yes | section 1 |
| 2 | CLAUDE.md table fully listed | yes | section 2 |
| 3 | `.claude/agents/*.md` listed with procedure and existence | yes | section 3 |
| 4 | Commit changes only the report | to verify | `git diff --name-only 58ea6e7..HEAD` (see scope check below) |
| 5-6 | QA criteria | n/a | QA's job |

## Tests run
```
uv run pytest -q
435 passed, 12 skipped in 3.06s
```
Scope check: `git diff --name-only 58ea6e7..HEAD` lists only
`docs/final/orchestration/reports/SMOKE-01-tech-lead.md`.

## Findings
- [minor] `CLAUDE.md` "Roles and configuration" (AI rival row) names
  `agents/rl/` and `docs/final/RL_POLICY.md`; neither exists at `58ea6e7`.
  Not fixed, per the brief. Likely cause (unverified): the PPO work (T-tasks) is on
  a WIP branch, not on `main` yet; `tech-lead.md` section 5 says some paths exist
  only on `orch/preview` or a WIP branch. Reproduce: `git cat-file -e 58ea6e7:docs/final/RL_POLICY.md`.
- No other findings: all other paths are present.

## Known limitations
Pattern rows were counted present on at least one match, as the brief says. I
did not verify the content of any file, only existence. I did not check other
branches for the two missing paths.

## Unresolved findings
The two MISSING paths above, for the orchestrator to route.

## Requested next action
Commit to review: the commit adding this file on task/SMOKE-01 (qa: `git log -1 task/SMOKE-01`)
What changed: nothing in the project; only this report was added.
How to check it: re-derive both tables and `.claude/agents/`, then `git cat-file -e 58ea6e7:<path>` for each path.
What I am unsure about: whether `agents/rl/` and `RL_POLICY.md` should count as expected-missing until the PPO task lands.
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
none

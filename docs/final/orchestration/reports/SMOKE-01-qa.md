---
handoff_id: HO-SMOKE-01-qa
task_id: SMOKE-01
date: 2026-11-24
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/SMOKE-01-tech-lead.md@fc16525
source_branch: gate/SMOKE-01-qa
source_commit: the commit adding this file (git log -1 gate/SMOKE-01-qa)
reviewed_commit: fc16525
verdict: ACCEPT WITH NOTES
---

# SMOKE-01: QA report

## Method
Branch `gate/SMOKE-01-qa` created from fc16525 (`git rev-parse HEAD` = fc1652510a9b...).
I re-derived the lists from `git show 58ea6e7:docs/final/orchestration/README.md`
(Files table, lines 101-117) and `git show 58ea6e7:CLAUDE.md` (lines 64-76), plus
`git ls-tree 58ea6e7 .claude/agents/`, without using the Tech Lead's lists.
Dumped `git ls-tree -r --name-only 58ea6e7` (286 paths, same count as the Tech
Lead) and checked each path with `grep -qxF`. Pattern rows were counted with
`grep -c '^<prefix>'`.

## Independent results at 58ea6e7
- README Files table: 17 rows. All 5 role files, HANDOFF_PROTOCOL, COURSE_ROLE_MAP,
  tasks/_EXEC_COMMON, reports/_TEMPLATE, STATUS, REVIEW_LOG, inputs/FINAL_REQUIREMENTS:
  present. Patterns: tasks/ 33 files, reports/ 20 files, PLAN-* 3 files
  (`PLAN-2026-11-23.md`, `-v2`, `-v3-delta`), DECISIONS-* 1 file
  (`DECISIONS-2026-11-23.md`), handoff-drafts/ 1 file: present. Matches TL section 1.
- CLAUDE.md table: the 5 native + 5 procedure paths, `rules-reviewer.md`,
  `.codex/agents/pop-rule-reviewer.toml`, and the three `SKILL.md` files: present.
  `docs/final/RL_POLICY.md`: **MISSING** (`docs/final/` has no such file).
  `agents/rl/`: **MISSING** (`agents/` holds only `__init__.py`, `baseline.py`,
  `model_player.py`, `providers.py`; `grep -c '^agents/rl'` = 0). Matches TL section 2.
- `.claude/agents/`: exactly six files; procedure lines quoted by the TL match
  mine (orchestrator.md:14, tech-lead.md:18, qa.md:18, evaluation-specialist.md:18,
  requirements-auditor.md:17); `rules-reviewer.md` is its own procedure (line 16 only
  reads AGENTS.md, CLAUDE.md and tech-lead.md for builder limits; all exist). No
  definition is unlisted.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | TL lists every README path with result and command | met | TL section 1 equals my 17 rows |
| 2 | TL lists every CLAUDE.md path | met | TL section 2, 17 entries, same MISSING pair as mine |
| 3 | TL lists each agent definition, quoted procedure, existence | met | TL section 3 equals my grep output |
| 4 | TL commit changes only its report | met | `git diff --name-only 58ea6e7..fc16525` = `docs/final/orchestration/reports/SMOKE-01-tech-lead.md` |
| 5 | QA consumed, re-derived, re-checked, states correctness | met | this report |
| 6 | QA commit changes only its report | met | verify with `git diff --name-only fc16525..HEAD` |

## Is the Tech Lead report complete and correct?
Yes. No omissions or false results found. Minor wording note: the TL cites
"exact-line match" for directory rows, and its section 2 lists the skills as
directories, then confirms via SKILL.md; fine.

## Findings
- [minor, reproduced] `CLAUDE.md:76` (AI rival row) names `agents/rl/` and
  `docs/final/RL_POLICY.md`, neither present at 58ea6e7.
  Repro: `git ls-tree -r --name-only 58ea6e7 | grep -E '^agents/rl|RL_POLICY'` prints nothing.
  Expected: paths exist, or the row marks them as planned. Cause (unverified):
  PPO work is not on main. Not fixed, per the brief. Orchestrator to route.

## Tests run
`uv run pytest -q` on the gate branch: `435 passed, 12 skipped in 3.02s`.

## Not checked
Content of any file beyond the quoted lines; other branches for the two missing
paths; whether the README/CLAUDE.md wording ("each SKILL.md") is intended
to be literal. No tests added (the brief says none are needed).

## Touches the knowledge boundary or AI seat
no. Gate 2 does not apply.

## Student decision required
none

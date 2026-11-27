---
handoff_id: HO-T31-tech-lead
task_id: T31
date: 2026-11-27
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T31.md@acfc462
source_branch: task/T31
source_commit: acfc4627af07da86a94a060b0d21d46b9778e572
reviewed_commit: n/a
verdict: n/a
---

# T31: tech-lead report

Status: done (official CI run still queued)

## Work completed
In a fresh clone of the official repository, `g23-migration` (base f306dbc), I replaced the "Your tests" pytest line with a fast subset and added one README line. Pushed `g23-migration` only: head **92705af4ec311b8b48b1a6b59fe6a6f2fc011590**. `task/T31` here holds only this report (base acfc462).

## Paths
Official repo: `.github/workflows/final.yml` (only the pytest line inside "Your tests", plus one comment line; `uv sync --frozen --extra train --extra online` kept; `timeout-minutes: 10`, `permissions: contents: read`, no secrets, runner expression untouched), `README.md` (one paragraph under the run commands). This repo: this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Subset includes headless, observation/interface hidden-info, online boundary, midterm regression | Met | `test_architecture` (engine never imports pygame); `test_interface`, `test_leakage`, `test_seats`, `test_traps_leaks`, `test_disguise`, `test_gate_t01/t04_eval_boundary`, `test_eval_T22/T25/t18/T22fix2/T24fix1` boundary files; `test_online_boundary`, `test_server_*`, `test_t22_server`, `test_gate_t13_qa_online`, `test_gate_t14_*`, `test_web_bridge`, `test_online_rooms`; `test_regressions`, `test_rules`, `test_level1*`, `test_levelfile`, `test_frozen_suite`, `test_situations`, guards, traps, swordplay, versus |
| 2 | Deterministic, no network, no new native extras | Met | same extras as before (`train`, `online`); no `play` |
| 3 | Under 4 minutes including `uv sync` | Met | 1:52 wall, with `.venv` deleted first (uv download cache warm, so a cold runner adds download time) |
| 4 | Passes locally | Met | below |
| 5 | Only permitted paths, protected settings unchanged | Met | `git diff --name-only f306dbc..92705af`: the two files |
| 6 | Official CI state | Queued | run 46046347788 on 92705af is `queued` (self-hosted runner). The f306dbc run 46044541653 was cancelled (superseded). Not waited |

## Tests run
```
cd game; rm -rf .venv; uv sync --frozen --extra train --extra online; uv run --frozen --extra train --extra online pytest -q <the 36 files listed in final.yml>
574 passed, 8 skipped, 1 xfailed in 110.54s (0:01:50)     (wall 1:52 including uv sync)
```
Exact command is the "Your tests" step in `.github/workflows/final.yml@92705af`. Full suite in this repository (main base, only a report added): `uv run --extra train --extra online pytest -q` gave `2299 passed, 48 skipped, 5 xfailed, 2 warnings in 524.75s (0:08:44)`. Plain `uv run pytest -q` without extras fails at collection (13 errors, numpy/websockets absent), as expected.

## Findings
No findings. Notes carried from T03 QA: N1 (setup-uv step) unchanged and still needs Saad's knowing acceptance. N2 (timeout risk) is addressed by the subset; the real CI time is unverified until the run starts. The subset's 8 skips are pygame-dependent tests (no `play` extra), the same as in CI before.

## Known limitations
- The subset covers about a quarter of the tests (574 of roughly 2,350); other eval, RL training and art tests run only in `SaadSatter/shadow_masque` CI.
- Time measured on a local Mac, not the course runner.

## Unresolved findings
Official CI result.

## Requested next action
Commit to review: 92705af4ec311b8b48b1a6b59fe6a6f2fc011590 on official `g23-migration` (report on task/T31)
What changed: "Your tests" now runs 36 named test files instead of the whole suite; README explains it and points to the full suite in `SaadSatter/shadow_masque` CI.
How to check it: `git diff f306dbc 92705af`; from `game/`: `rm -rf .venv` then the step's commands; `gh run list -R columbia-university-ai-games/final-saadsatter -b g23-migration`.
What I am unsure about: whether the course runner finishes within 10 minutes (including checkout, team steps and a cold uv cache); whether the chosen subset is the coverage Saad wants.
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply).

## Student decision required
none

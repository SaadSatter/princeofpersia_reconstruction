---
handoff_id: HO-T29-tech-lead
task_id: T29
date: 2026-11-26
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T28.md@b4aa069 (id renumbered to T29 by the orchestrator mid-task; T29.md not read)
source_branch: task/T29
source_commit: eee55b937c218e1f4fb2f2f0b05cfe5054d9d1dd
reviewed_commit: n/a
verdict: n/a
---

# T29: tech-lead report

Status: done (GitHub Actions result not obtained; nothing pushed)

## Work completed
Changed `.github/workflows/ci.yml` so the install step is `uv sync --frozen --extra train --extra online` and the test step is `uv run --frozen --extra train --extra online pytest -q`. This installs `websockets` for `tests/test_online_boundary.py`. `--frozen` kept; `uv.lock` and `pyproject.toml` untouched. Branch was first created as task/T28 and renamed to task/T29 before any push.

## Paths
`.github/workflows/ci.yml`; this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Install and test use `--extra train --extra online`, keep `--frozen` | yes | commit eee55b9 |
| 2 | Local suite green with those flags | yes | below |
| 3 | Push and report Actions result | no | I did not push (the procedure forbids it for workers); no Actions run exists |

## Tests run
```
uv run --frozen --extra train --extra online pytest -q   (clean tree, at eee55b9)
2265 passed, 45 skipped, 5 xfailed, 2 warnings in 471.46s (0:07:51)
```
An earlier run with the workflow edit uncommitted gave 2 failed, 2263 passed: `tests/test_qa_T08_probes.py` two held-out ledger tests refuse a dirty tree (decision #64). They pass on a clean tree, as the run above shows.

## Findings
No findings. Base: the brief names dfe2d90; local `orch/reviewed` was stale (1a515ca), so I branched from dfe2d90, which equals `origin/orch/reviewed`.

## Known limitations
Fix not verified on GitHub Actions (3.11 and 3.12 matrix). Local Python version was not matched to the matrix. The workflow still triggers only on push to main, PRs and manual dispatch, so a push of task/T29 alone will not start it; a PR or `workflow_dispatch` is needed.

## Unresolved findings
None.

## Requested next action
Commit to review: eee55b937c218e1f4fb2f2f0b05cfe5054d9d1dd on task/T29
What changed: CI installs and runs tests with the `online` extra as well as `train`.
How to check it: `git diff dfe2d90..task/T29 -- .github/workflows/ci.yml`; run the suite command above on a clean tree; open a PR to see the Actions run.
What I am unsure about: whether Actions goes green on both Python versions, untested.
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
none

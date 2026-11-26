---
handoff_id: HO-T29-qa
task_id: T29
date: 2026-11-26
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T29-tech-lead.md@baa2ec6
reviewed_commit: baa2ec617cfdfdb7946a1b9791cafb7e376147a2
source_commit: see branch gate/T29-qa head
verdict: ACCEPT
---

# T29: QA report

Verdict: ACCEPT

## Scope
`git diff --name-only dfe2d90..baa2ec6`: `.github/workflows/ci.yml` and the Tech Lead report only. Within the brief's permitted paths. `pyproject.toml` and `uv.lock` untouched; `online = ["websockets>=13,<16"]` already exists. The diff changes exactly two lines: install is `uv sync --frozen --extra train --extra online`, test is `uv run --frozen --extra train --extra online pytest -q`. `--frozen` kept. `ci/midterm-saadsatter.yml` (course copy) is unchanged and out of scope.

## Acceptance criteria to evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | Install and test steps use `--extra train --extra online`, keep `--frozen` | yes | diff above |
| 2 | `uv run --frozen --extra train --extra online pytest -q` green locally | yes | my run at baa2ec6, clean tree: `2265 passed, 45 skipped, 5 xfailed, 2 warnings in 706.74s` (matches the Tech Lead's counts) |
| 3 | Push `task/T29`, report the Actions result | yes | `task/T29` is on origin at baa2ec6. Run 45768522109 (`ci.yml`, workflow_dispatch, headSha baa2ec6): conclusion success. Python 3.12: `2262 passed, 48 skipped, 5 xfailed, 2 warnings in 442.63s`. Python 3.11: `2262 passed, 48 skipped, 5 xfailed in 587.69s`. The install log shows `uv sync --frozen --extra train --extra online`. |

The Tech Lead's report says nothing was pushed and no run existed. That was true when written. The branch is now on origin and the orchestrator dispatched the run, so criterion 3 is met.

## Findings
None (no blocker, major, minor or cosmetic).

Notes, not defects:
- CI skips 48 tests against 45 locally. These are environment-dependent skips (for example optional tools or assets). I did not itemise them.
- The workflow still triggers only on push to main, PRs and manual dispatch. A push of `task/T29` alone does not start it, as the Tech Lead said.
- The first CI failure (run 45764999518, `No module named 'websockets'`) is no longer reproduced in the new run.

## Not checked
- I wrote no new tests. The change is CI config only, and the Actions run is its test.
- I did not itemise the 48 CI skips.
- Gate 2 does not apply (no AI, observation or boundary change).

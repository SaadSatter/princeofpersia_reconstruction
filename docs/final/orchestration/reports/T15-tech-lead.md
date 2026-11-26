---
handoff_id: HO-T15-tech-lead
task_id: T15
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T15.md@1a5840a
source_branch: task/T15
source_commit: faf7e8d4ab670dfad9ffa2c0c108c3c3b5961336
reviewed_commit: n/a
verdict: n/a
---

# T15: tech-lead report

Status: done

## Work completed
Added `train = ["numpy>=2,<3"]` to `[project.optional-dependencies]`, ran `uv lock`, and switched `ci.yml` to `uv sync --frozen --extra train` and `uv run --frozen --extra train pytest -q`. No test, `dependencies` or `dev` group was touched.

## Paths
`pyproject.toml` (1 line), `uv.lock`, `.github/workflows/ci.yml`, this report. No session file was added (small change).

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | `--extra train` run passes numpy probe | yes | 867 passed, 12 skipped, 4 xfailed |
| 2 | no-extra result and failing tests named | yes | see below; 1 failed |
| 3 | no numpy import in pop/agents/render/web/play.py | yes | grep of working tree (identical to base for these paths) is empty; `web/` does not exist on this base |
| 4 | scope | yes | only permitted paths (checked below) |
| 5 | uv.lock adds numpy only | yes, with one note | no existing package changed. Added: two numpy entries (2.4.6 for Python <3.12, 2.5.5 for >=3.12, both inside `>=2,<3`), the `train` extra metadata, and a top-level `resolution-markers` block that uv adds whenever a package resolves differently per Python version. |

## Tests run
```
uv run --extra train pytest -q
867 passed, 12 skipped, 4 xfailed in 79.58s (0:01:19)

uv run --exact pytest -q     (--exact removes numpy; plain `uv run` keeps it once installed)
1 failed, 866 passed, 12 skipped, 4 xfailed in 78.98s (0:01:18)
FAILED tests/test_gate_t04fix1_qa_probes.py::test_numpy_str_answer_still_works
```
On this base only that one test needs numpy. `test_gate_w2_qa_probes.py` and `tests/test_rl_*.py` are not on `orch/reviewed`.

## Findings
No findings. Two numpy versions in the lock follow from `requires-python` allowing 3.11 (numpy 2.5 needs >=3.12). CI matrix is 3.11 and 3.12, so both are exercised.

## Known limitations
`uv run` without `--exact` reuses an env that already has numpy, so a no-extra check must use `--exact` or a fresh venv. CI itself was not run (no push).

## Unresolved findings
None.

## Requested next action
Commit to review: faf7e8d4ab670dfad9ffa2c0c108c3c3b5961336 on task/T15
What changed: numpy becomes an optional `train` extra, locked; CI installs the extra so numpy tests run. Base install stays numpy-free.
How to check it: `git diff --name-only 2180fea..HEAD`; `uv run --extra train pytest -q`; `uv run --exact pytest -q`; `git diff 2180fea -- uv.lock`.
What I am unsure about: whether the extra `resolution-markers` header and dual numpy pins in the lock are acceptable (they are uv's normal output).
Touches the knowledge boundary or AI seat: no   (Gate 2 does not apply)

## Student decision required
none

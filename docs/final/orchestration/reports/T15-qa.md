---
handoff_id: HO-T15-qa
task_id: T15
date: 2026-11-24
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
consumed: docs/final/orchestration/reports/T15-tech-lead.md@44a5ded
source_branch: gate/T15-qa
source_commit: see branch head
reviewed_commit: faf7e8d4ab670dfad9ffa2c0c108c3c3b5961336 (checked out at 44a5ded, report-only on top)
verdict: ACCEPT
---

# T15 QA report

Verdict: ACCEPT. No findings. No tests added (packaging change, no gap found).

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | `--extra train` passes numpy probe | met | `uv run --frozen --extra train pytest -q`: 867 passed, 12 skipped, 4 xfailed in 79.24s |
| 2 | no-extra result, failures named | met | `uv run --frozen --exact pytest -q`: 1 failed, 866 passed, 12 skipped, 4 xfailed; only `tests/test_gate_t04fix1_qa_probes.py::test_numpy_str_answer_still_works` fails |
| 3 | no numpy import in pop/agents/render/web/play.py | met | `git grep "import numpy\|from numpy" HEAD -- pop agents render web play.py` empty |
| 4 | scope | met | `git diff --name-only 2180fea..HEAD`: ci.yml, T15-tech-lead.md, pyproject.toml, uv.lock |
| 5 | uv.lock adds numpy only | met | diff has no removed lines except `provides-extras` (gains "train"). Added: two numpy entries, `train` extra metadata, top-level `resolution-markers`. No other package changed |

## Extra checks requested
- pyproject diff: exactly one line (`train = ["numpy>=2,<3"]`); `dependencies` and `dev` untouched.
- `uv lock --check` succeeded ("Resolved 26 packages"); `uv sync --frozen --extra train` succeeded.
- numpy python requirement: 2.4.6 is pinned for Python <3.12 and has cp311 wheels (11 in lock); 2.5.5 is pinned for >=3.12 and has none for cp311. This matches `requires-python = ">=3.11"`, and the marker split is consistent. I did not read numpy's metadata directly, only the lock's wheel tags. Python 3.11 is not installed here, so I did not install on 3.11.
- ci.yml: parses as valid YAML; the diff shows only the install step name/command and the pytest command changed. Other steps untouched.

## Not checked
- CI itself (not pushed, by instruction).
- A real Python 3.11 install (interpreter unavailable); lock wheel tags only.
- A fresh-venv no-extra run; `--exact` was used instead, as the tech lead advised.

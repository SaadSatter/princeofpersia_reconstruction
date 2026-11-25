---
handoff_id: HO-T17-tech-lead
task_id: T17
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T17.md@63ff5ea
source_branch: task/T17
source_commit: 54308c0e4c84f19f00ad4d28eeff663c71ca2c0f
reviewed_commit: n/a
verdict: n/a
---

# T17: tech-lead report

Status: partial (one superseded existing test fails; needs an orchestrator or Saad ruling, see Findings)

## Work completed
Failing tests first (3 tests, all failed on the base), then `tools/rl/train.py`: when `final_check` counts a policy error, `weights.json` is renamed `weights.failed.json`. `summary.json` gains `weights_file` and `weights_failed`, and `weights_sha256` is the hash of the failed file. `stopped` and exit status 2 are unchanged. A clean run is unchanged apart from the two new summary keys. One paragraph added to `docs/final/RL_POLICY.md`. No full training run.

## Paths
`tools/rl/train.py`, `docs/final/RL_POLICY.md`, `tests/test_rl_t17_withhold.py` (new), `docs/agent-sessions/19-T17-withhold-failed-weights.md` (new), this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Injected final_check error: no weights.json, weights.failed.json exists, summary names it with its sha256 and a failed label, exit 2 | Yes | `test_a_failed_final_check_renames_...`, `test_the_command_line_exits_2_...` |
| 2 | Clean smoke run writes weights.json, exits 0 | Yes | `test_a_clean_run_still_writes_weights_json_and_exits_0` |
| 3 | Suite green | No, 1 failure | below |

## Tests run
```
uv run --frozen --extra play --extra train pytest -q
1 failed, 1189 passed, 12 skipped, 2 xfailed, 2 warnings in 173.27s (0:02:53)
```
The failure is `tests/test_gate_T16_qa.py::test_final_check_error_keeps_weights_marks_summary_and_main_exits_2`, line 63: `assert (tmp_path / "weights.json").exists()  # fact: weights are still written`. That test pins the behaviour decision #50 replaces. The brief forbids other test edits, so I left it. It needs the one-line change to assert `weights.failed.json` exists and `weights.json` does not. Everything else in that test (stopped, error counts, exit 2) still passes.

## Findings
- [major] tests/test_gate_T16_qa.py:63 contradicts decision #50 (above). Not reproduced as a code bug. Needs a permitted edit by whoever owns that test.

## Known limitations
New summary keys `weights_file` and `weights_failed` are absent from the `policy_error` early-stop summary (it has no weights; `weights_sha256` is null there).

## Unresolved findings
The test conflict above.

## Requested next action
Commit to review: 54308c0e4c84f19f00ad4d28eeff663c71ca2c0f on task/T17
What changed: a failed final check no longer leaves a file named weights.json; it is renamed weights.failed.json and the summary says so.
How to check it: `uv run --frozen --extra play --extra train pytest -q tests/test_rl_t17_withhold.py`, then the full suite.
What I am unsure about: whether the orchestrator wants the stale T16 QA test edited on this branch (needs permission) and whether the extra summary key names are acceptable.
Touches the knowledge boundary or AI seat: no for observations, actions and hidden information; it does change training output of the AI rival's weights file, so Gate 2 applies per the brief.

## Student decision required
none

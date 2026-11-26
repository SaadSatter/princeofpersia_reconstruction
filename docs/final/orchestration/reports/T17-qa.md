---
handoff_id: HO-T17-qa
task_id: T17
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T17-tech-lead.md@bb773ea
source_branch: gate/T17-qa
source_commit: the head of gate/T17-qa (this report's own commit is not recorded here)
reviewed_commit: 54308c0e4c84f19f00ad4d28eeff663c71ca2c0f
verdict: ACCEPT WITH NOTES
---

# T17: QA report

Status: done

## Work completed
Checked out bb773ea (the reviewed code is 54308c0; bb773ea only adds the TL report). Read the train.py diff and ran the TL's tests. Updated the stale T16 probe to decision #50. Added probes for the summary keys and the clean path. Ran the full suite. Scope: the diff 2835928..54308c0 touches only permitted paths (tools/rl/train.py, RL_POLICY.md, tests/test_rl_t17_withhold.py, one agent-session file, the TL report). No CI files changed.

## Paths
- `tests/test_gate_T16_qa.py` (edited by me as the owning QA role, per the orchestrator's instruction): `test_final_check_error_keeps_weights_marks_summary_and_main_exits_2` is renamed `test_final_check_error_withholds_weights_marks_summary_and_main_exits_2`. Line 63 now asserts `weights.failed.json` exists and `weights.json` does not. `stopped`, error counts and exit 2 are untouched. Nothing else in the file changed.
- `tests/test_gate_T17_qa.py` (new, 7 probes).
- this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Injected final_check error: no weights.json; weights.failed.json exists; summary names it, has sha256 of the failed file, labelled failed; exit 2 | Met | tests/test_rl_t17_withhold.py (2 tests); my `test_failed_summary_names_a_file_that_exists_and_hash_matches_it` (summary on disk equals the returned one; named file exists; its sha equals `weights_sha256`); updated T16 probe (exit 2 via `main`) |
| 2 | Clean smoke run writes weights.json, exits 0 | Met | `test_a_clean_run_still_writes_weights_json_and_exits_0`; my `test_clean_run_keys_are_the_old_keys_plus_two` (keys are the old keys plus `weights_file`, `weights_failed`; sha matches weights.json); `final_eval_seeds=0` also still ships weights.json |
| 3 | Suite green, real line | Met | below |

## Tests run
```
uv run --frozen --extra play --extra train pytest -q
1197 passed, 12 skipped, 2 xfailed, 2 warnings in 188.81s (0:03:08)
```
Targeted: `pytest -q tests/test_gate_T17_qa.py tests/test_gate_T16_qa.py tests/test_rl_t17_withhold.py` gave 15 passed. The skips and xfails match the base (12 skipped, 2 xfailed).

## Summary-key review (can they mislead a script?)
- Consistent: `weights_failed` is true exactly when `stopped == "final_check_policy_error"` (probe). `weights_file` always names a file that exists after a finished run, and `weights_sha256` always hashes that file (the rename keeps content).
- A script that opens `weights.json` after a failed run now gets file-not-found instead of shipping bad weights. That is the intent of #50. A script that trusts `weights_sha256` alone, ignoring `weights_failed` and `stopped`, could not tell failed weights from good ones. Not a defect; the keys are there.
- Clean run: only the two additive keys differ.

## Findings
No blocker or major. Reproduced observations (the probes pass and pin the behaviour):
- [minor] tools/rl/train.py, the `policy_error` summary (about lines 232-237): it lacks `weights_file` and `weights_failed`. A script doing `s["weights_failed"]` raises KeyError on the worst failure. Judgement on the TL's question: the meaning is consistent (no weights exist, `weights_sha256` is null, TrainingError, exit 2) but the schema is not. Recommended, not required: add `"weights_file": null, "weights_failed": false` there so every summary has one key set. Pinned by `test_in_training_policy_error_summary_has_no_weights_and_lacks_the_new_keys`; if the keys are added, QA updates that probe.
- [cosmetic] Re-running into the same `--out` after a failed run leaves the old `weights.failed.json` beside a new clean `weights.json`; the summary correctly points at weights.json. The reverse order (clean, then failed) removes the old shipping name, because the export overwrites it before the rename. Probes: `test_clean_rerun_after_a_failed_run_reports_weights_json`, `test_failed_run_after_a_clean_run_removes_the_old_shipping_name`.

## Known limitations
The #50 behaviour lives only in `train()`. A grep of non-test py/yml/toml found no other reader of the out-dir `weights.json`, so no consumer was found that could break.

## Unresolved findings
None blocking. The minor schema note awaits an orchestrator choice.

## Not checked
Full training run (forbidden). A crash between export and rename (not cheaply injectable; `Path.replace` is atomic on one filesystem). The RL_POLICY.md paragraph was only skimmed; Gate 2 covers it.

## Requested next action
Evaluation Specialist (Gate 2): read this report and branch `gate/T17-qa`. Orchestrator: decide whether the TL adds the two keys to the `policy_error` summary.

## Student decision required
none

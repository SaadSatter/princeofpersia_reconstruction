---
handoff_id: HO-T08-fix2-fix1-tech-lead
task_id: T08-fix2-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T08-fix2-fix1.md@96d990d; reports/T08-fix2-qa.md@114c3f6; reports/T08-fix2-evaluation-specialist.md@71a6ed0
source_branch: task/T08-fix2-fix1
source_commit: 114f9e6
reviewed_commit: n/a
verdict: n/a
---

# T08-fix2-fix1: tech-lead report

Status: done

## Work completed
Failing tests first (c35d4e9: 4 of 6 fail), then the fix (114f9e6). `evaluation/analysis.py` no longer prints an
unrecorded policy-error count as 0. No policy run, no H6, nothing under `agents/`, `pop/`, `tools/rl/`,
`evaluation/heldout/**`, `evaluation/results/**`; committed T09 `analysis.txt` untouched.

- `_seat_errors`: a count is recorded only if it is an int. Field absent (old row) is not recorded; field `null` on a
  seat whose `controllers.<seat>.kind` is `policy` is not recorded (QA N2); `null` on a scripted/fallback seat is
  skipped (not a policy seat). A row with no `controllers` info and no field defaults to policy, as before.
- `policy_error_totals`: sums recorded rows only. No recorded policy seat gives `policy_errors: None`,
  `rows_with_errors: None`; `not_recorded: n` (rows with an unrecorded policy seat) is added whenever n > 0.
  A condition with no policy seat (SvS) has `None` and no `not_recorded` key. A fully recorded condition returns
  the same dict as before (existing exact-equality test still passes).
- `policy_error_lines`: cells print `not recorded`, `S (n not recorded)` for mixed, `n/a` for no policy seat. The
  footnote ("zero cannot be assumed") is kept.
- PROTOCOL.md section 5: one sentence in the Row fields item (runner `seats.*.errors` excludes swallowed policy
  errors; `policy_errors` carries them; missing prints "not recorded", never 0).

## Paths
`evaluation/analysis.py`; `docs/final/evaluation/PROTOCOL.md`; new `tests/test_eval_t08fix2fix1_not_recorded.py`;
`docs/agent-sessions/T08-fix2-fix1-not-recorded.md`; the two authorised test edits below; this report.

## Authorised test edits (the only two)
1. `tests/test_eval_t08fix2_policy_errors.py::test_old_rows_without_the_field_are_read_as_not_recorded`
   - old: `assert analysis.policy_error_totals([old])[0]["policy_errors"] == 0`
   - new: `assert analysis.policy_error_totals([old])[0]["policy_errors"] is None`
2. `tests/test_qa_T08fix2_policy_errors_cli.py::test_old_rows_are_not_printed_as_zero_in_the_totals_table`
   - removed the line `@pytest.mark.xfail(strict=True, reason="F1: totals table prints 0 for unrecorded old rows")`; the test now passes.

## Acceptance criteria to evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Totals: None / not_recorded for unrecorded | Met | `test_a_condition_of_only_old_rows_...`, `test_a_mixed_condition_...` |
| 2 | Printed "not recorded", "S (n not recorded)", "n/a", footnote kept | Met | `..._prints_na`, `..._mixed_...`, `test_the_footnote_is_kept` |
| 3 | Null policy-kind seat is not recorded (N2) | Met | `test_a_policy_seat_with_a_null_counter_...` |
| 4 | PROTOCOL sentence | Met | PROTOCOL.md section 5, Row fields |
| 5 | Recorded zero still prints 0 | Met | `test_recorded_zero_still_prints_zero` |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree, 114f9e6)
1785 passed, 12 skipped, 5 xfailed, 2 warnings in 281.75s (0:04:41)
```
(Eval's 1778/12/6 plus 6 new tests, plus the QA probe now passing instead of xfail: 1778+6+1 = 1785; xfail 6 to 5.)

## Findings
No findings. Checks not done: I did not re-run `analyze_results.py` on the committed T09 `results.json` (it is not on
this branch); QA should re-run that read-only check. Expected: the T09 table reads "not recorded" in every MvS/SvM/MvM
cell and "n/a" for SvS, where the old output printed 0 for all sixteen conditions (the SvS rows have no policy seat).

## Known limitations
A row with no `controllers` block and a `null` field is skipped, not flagged (the kind is unknown); real rows always carry `controllers`.
Runner `seats.*.errors` is still 0 for swallowed errors (Eval N1: owner call, outside these paths).

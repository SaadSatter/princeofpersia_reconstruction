# T08-fix2-fix1 session (tech-lead worker)

Base `71a6ed0` (`gate/T08-fix2-eval`), branch `task/T08-fix2-fix1`. Closes T08-fix2 QA F1 and N2 and Eval F1:
the per-condition policy-error table no longer prints 0 for rows that never recorded the count.
Failing tests first (`tests/test_eval_t08fix2fix1_not_recorded.py`, commit `c35d4e9`, 4 of 6 failing), then
`evaluation/analysis.py` and one PROTOCOL section 5 sentence. No policy run, no H6, no paid call, no training,
no change to committed T09 evidence. Details and the result line are in
`docs/final/orchestration/reports/T08-fix2-fix1-tech-lead.md`.

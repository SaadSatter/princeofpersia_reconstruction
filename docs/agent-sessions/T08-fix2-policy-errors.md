# T08-fix2 session (tech-lead worker)

Base `0ea8d73` (`orch/reviewed`), branch `task/T08-fix2`. Decision #84: the PPO rival swallows inference errors
into WAIT and counts them (`policy_errors()`), but no result row carried the count (T09 review finding 1).
Tests first (`tests/test_eval_t08fix2_policy_errors.py`, 6 failing), then `evaluation/controllers.py`
(`policy_errors_of`), `evaluation/suite.py` (`seats.A/B.policy_errors` in every row), `evaluation/analysis.py`
(per-condition sum and an "Odd rows" list; a held-out row with a non-zero count is labelled a harness error and
does not abort) and one line in `docs/final/evaluation/PROTOCOL.md` section 5. No policy run, no H6 access, no paid
calls, no training. Details and the suite line: `docs/final/orchestration/reports/T08-fix2-tech-lead.md`.

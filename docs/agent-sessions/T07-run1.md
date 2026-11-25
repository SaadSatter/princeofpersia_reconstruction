# T07-run1 session: commit the run-1 weights and evidence (tech-lead worker, claude-sonnet-5-5)

Task brief: `docs/final/orchestration/tasks/T07-run1.md@ef621a5`. Base `f08c1a8`, branch `task/T07-run1`.

* Read: the brief, the tech-lead procedure, `agents/rl/policy.py`, `docs/final/RL_POLICY.md`,
  `tests/test_rl_policy.py`, `tools/rl/train.py` (`final_check`), the run folder (read-only).
* Order: failing tests (`tests/test_rl_run1_shipped.py`), then the copies (checked with `cmp`
  and `shasum -a 256`), two constants in `policy.py`, `RL_POLICY.md`, then the report.
* No training, no `--live`, no H6 run, no push of anything but the branch. `play.py`, `web/`,
  `server/` untouched.
* Report: `docs/final/orchestration/reports/T07-run1-tech-lead.md`.

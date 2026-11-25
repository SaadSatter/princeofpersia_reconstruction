# T08 session (tech-lead worker)

Base `fc02687` (`orch/reviewed`), branch `task/T08`. Versus evaluation suite: scenario registry (tuning split D1, B2, I3,
F5; frozen held-out H6 with a SHA-256 check and a run-once ledger), success monitors (decisions #9, #58, #59), the runner
CLI `tools/eval/run_versus_suite.py` (SvS, MvS, SvM, MvM test only; secret `secrets.token_bytes(32)` seed key; fresh
controllers; busy controller = harness error; two-seat traces and `--replay`), the analysis (`tools/eval/analyze_results.py`:
Wilson intervals, distinct outcomes per condition, mirror matches as one trial) and `docs/final/evaluation/PROTOCOL.md`.
Failing tests were committed first. The shipped PPO policy was run only on the tuning split in tests, with a 120-frame
cap; it was never run on H6 (decision #61). No paid calls, no training, no `--live`. `pop/`, `agents/`, `tools/rl/`,
`play.py`, `render/`, `web/`, `server/` and existing tests are untouched. Reused from the unreviewed `orch/wip-T08`
snapshot (25e4587): the module layout and the monitor, analysis and CLI ideas, rewritten and tested here; the tuning and
H6 start lists were re-derived (see PROTOCOL.md section 3). Result line and details are in
`docs/final/orchestration/reports/T08-tech-lead.md`.

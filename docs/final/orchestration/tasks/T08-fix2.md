# T08-fix2: record PPO inference errors in every evaluation row (decision #84)

Handoff id: HO-T08-fix2-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3.
Source: `reports/T09-rules-reviewer.md` finding 1; T07-fix1's open note ("the in-play counter still has to be written into game results by whoever runs the seat"). `agents/rl/policy.py` already counts swallowed inference errors (`policy_errors()`); `evaluation/` and `tools/eval/` never read them.
Base: `orch/reviewed` 0ea8d73. `git switch -c task/T08-fix2 0ea8d73`.

1. Failing test first: an M seat whose network raises inside `choose` gives a row with `policy_errors > 0` for that seat (today the row shows nothing).
2. Every result row records, per seat, `policy_errors` (an integer for a policy seat, `null` for other kinds), and `tools/eval/analyze_results.py` reports their sum per condition and lists any row with a non-zero count under the odd rows.
3. A policy seat with any `policy_errors` in a held-out run is reported in the analysis as a harness error (counted, not hidden); it does not abort the run (#24's abort rules stay as they are).
4. Update PROTOCOL.md §5 (result fields) with one line. Do not change H6, the ledger, the bar, or the committed T09 evidence. No policy run on H6.

Permitted writes: `evaluation/**` (not `evaluation/heldout/**` or `evaluation/results/**`), `tools/eval/**`, new tests `tests/test_eval_t08fix2_*.py`, `docs/final/evaluation/PROTOCOL.md` (the §5 line), `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T08-fix2-tech-lead.md`. Not `agents/`, `pop/`, `tools/rl/`, existing tests.
Suite: `uv run --frozen --extra play --extra train --extra online pytest -q` on a clean tree; paste the real line.

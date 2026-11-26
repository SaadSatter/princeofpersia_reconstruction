# T08-fix2-fix1: never print an unrecorded policy-error count as 0 (T08-fix2 QA F1, N2)

Handoff id: HO-T08-fix2-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3. Corrective attempt 1 of 2 for T08-fix2.
Read first: `tasks/T08-fix2.md`@c325f9e; `reports/T08-fix2-qa.md`@114c3f6 (F1, N1–N3); `reports/T08-fix2-evaluation-specialist.md`@71a6ed0 (the F1 ruling and the exact fix); decision #84.
Base: `gate/T08-fix2-eval` 71a6ed0. `git switch -c task/T08-fix2-fix1 71a6ed0`.

Fix (in `evaluation/analysis.py`), failing test first:
1. `policy_error_totals`: count recorded and unrecorded rows per condition. A condition with no recorded policy seat gives `policy_errors: None` and `rows_with_errors: None`; a mixed one sums the recorded rows and adds `not_recorded: n`.
2. `policy_error_lines`: print "not recorded" for those cells, "S (n not recorded)" for a mixed condition, and "n/a" for a condition with no policy seat (e.g. SvS). Keep the footnote.
3. `_seat_errors` (QA N2): a policy-kind seat whose field is `null` counts as not recorded, never as 0.
4. PROTOCOL.md §5: one sentence that the runner's `seats.*.errors` excludes errors swallowed inside the policy controller; `policy_errors` carries them (Eval N1 ruling).

Tests you may change (the orchestrator authorises these two edits only, as part of this corrective chain):
- your own `tests/test_eval_t08fix2_*.py` test `test_old_rows_without_the_field_are_read_as_not_recorded`, which asserts 0 and so encodes the defect: change only that assertion to the not-recorded result;
- `tests/test_qa_T08fix2_policy_errors_cli.py`: remove only the strict `xfail` marker of `test_old_rows_are_not_printed_as_zero_in_the_totals_table` once it passes.
No other existing-test edit. Do not regenerate or edit the committed T09 `analysis.txt`, `evaluation/heldout/**` or `evaluation/results/**`. No policy run on H6. Not `agents/`, `pop/`, `tools/rl/`.

Permitted writes: `evaluation/analysis.py`, `tools/eval/**` (only if needed), the two test edits above, new tests `tests/test_eval_t08fix2fix1_*.py`, `docs/final/evaluation/PROTOCOL.md` (the §5 sentence), `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T08-fix2-fix1-tech-lead.md`.
Suite on a clean tree: `uv run --frozen --extra play --extra train --extra online pytest -q`; paste the real line.
Gates: QA (`gate/T08-fix2-fix1-qa`), Eval (`gate/T08-fix2-fix1-eval`), Gate 3.

---
handoff_id: HO-T08-fix2-qa
task_id: T08-fix2
from: qa
to: evaluation-specialist
consumed: docs/final/orchestration/reports/T08-fix2-tech-lead.md@8e60513
reviewed_commit: 8e60513abb92a7b70e90b4e81c3d8978917739f5
source_branch: gate/T08-fix2-qa
verdict: ACCEPT WITH NOTES
---

# T08-fix2: QA (Gate 1)

Verdict: ACCEPT WITH NOTES (one minor finding, F1; no blocker or major).

## Suite
`uv run --frozen --extra play --extra train --extra online pytest -q` on the clean gate tree (8e60513 plus my probe file):
```
1777 passed, 12 skipped, 6 xfailed, 2 warnings in 285.00s (0:04:44)
```
(Tech Lead's line was 1773/11/5; the difference is my probes: 4 passed, 1 skip, 1 strict xfail F1. The skip is the T09 re-analysis probe, because `evaluation/results/T09` is not on this branch.)

## Acceptance criteria to evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | Failing test first; network raising in `choose` gives `policy_errors > 0` | Met | With `evaluation/` reverted to 0ea8d73, all 6 Tech Lead tests fail (and 5 of my 6 probes); at 8e60513 they pass. Test commit f0f06f0 precedes work 3f1e3da. |
| 2 | Every row has per-seat `policy_errors` (int or null); analysis sums per condition and lists non-zero rows under odd rows | Met | CLI probe `test_cli_injected_failure_...`: `run_versus_suite.main` (tuning, dry run, temp dir, `make_shipped_policy` patched to a raising net) writes MvS seat A and SvM seat B `> 0`, the other seat and all SvS seats `null`; `analyze_results.main` output lists exactly the MvS and SvM rows under "Odd rows" and not SvS. `test_wait_seat_is_null_through_the_cli` (held-out dry run, WAIT seats) all `null`. |
| 3 | Held-out policy errors reported as harness error, no abort | Met | `test_heldout_harness_error_label_and_tuning_has_none` (constructed rows, no policy run): held-out row gets "(harness error)" and the "run was not aborted" note; a tuning row lists the count without the label. Diff does not touch `aborted`, `harness_error` or abort rules. |
| 4 | PROTOCOL section 5 one line only; no change to H6, ledger, bar, T09 evidence | Met | `git diff --name-only 0ea8d73..8e60513`: session note, PROTOCOL.md (one added item in Row fields), the TL report, `evaluation/{analysis,controllers,suite}.py`, the new test file. All permitted; nothing under `evaluation/heldout`, `evaluation/results`, `agents/`, `pop/`, `tools/rl/`, existing tests. |

Old rows: I re-analysed the committed T09 `results.json` (read from 874c5e0 into a scratch dir, read-only) with `tools/eval/analyze_results.py`. The output differs from the committed `analysis.txt` only by an appended section (diff lines 42-68): all 16 conditions, "Odd rows: None.", and "Policy errors not recorded (rows from before T08-fix2): 48 rows, so zero cannot be assumed." Everything before it is byte-identical.

## Findings
- **F1 (minor, reproduced)** `evaluation/analysis.py` `policy_error_totals` / `policy_error_lines` (about line 195-215): for rows that carry no field, the per-condition table prints `policy errors = 0` and `rows with errors = 0`. The "not recorded" sentence appears only as a footnote. The brief says old rows must read as "not recorded" and not 0. A reader of the T09 table sees sixteen zeros. Repro: `uv run python tools/eval/analyze_results.py <T09 results.json>` (lines "| H6 | H6-1 | MvS | 0 | 0 |"), or probe `test_old_rows_are_not_printed_as_zero_in_the_totals_table` (strict xfail "F1"). Expected: "n/r" (or similar) in the cell for a condition with no recorded rows. The Tech Lead's own test `test_old_rows_without_the_field_are_read_as_not_recorded` asserts the sum is `0`, so it encodes this. Suggested handling: fix in a small follow-up, or accept given the footnote; the Evaluation Specialist should say which.
- **N1 (note, as the brief asked)** The runner's own `seats.*.errors` still reads 0 for a swallowed inference error (my CLI probe asserts it). This is the T09 observation, now covered by `policy_errors` in every row. A follow-up in `pop/runner.py` or `agents/` (outside this task's paths) would be needed to make `errors` truthful; I do not think it is needed for the evaluation, but it is an owner/orchestrator call. Anyone reading `errors` alone is still misled.
- **N2 (note)** A policy-kind seat that exposes no `policy_errors` callable records `null`, and the analysis then treats the field as present (`null` summed as 0, not flagged "not recorded"). The shipped `make_rl_rival` always has the counter, so this is theoretical.
- **N3 (note)** The "harness error" label is by `split == "heldout"` only; a held-out dry run (WAIT seats) never produces one.

## Not checked
No real shipped-weights policy run and no H6 run (forbidden). The CLI injection patches `evaluation.controllers.make_shipped_policy`; the real `make_rl_rival` counter wiring (`agents/rl/policy.py:144`) was read, not exercised with real weights. T09 results are not on this branch, so the committed-results probe skips here and was done by hand as above.

## Probes
`tests/test_qa_T08fix2_policy_errors_cli.py` (6 tests: 4 pass, 1 strict xfail F1, 1 skip when T09 results are absent).

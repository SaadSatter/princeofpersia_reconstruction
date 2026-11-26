---
handoff_id: HO-T08-fix2-tech-lead
task_id: T08-fix2
date: 2026-11-25 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T08-fix2.md@c325f9e; DECISIONS-2026-11-24.md@c325f9e (row #84); reports/T09-rules-reviewer.md@c325f9e (finding 1)
source_branch: task/T08-fix2
source_commit: 3f1e3da0cfec4ba9df3fd17b5ff37c02169178a0
reviewed_commit: n/a
verdict: n/a
---

# T08-fix2: tech-lead report

Status: done

## Work completed
Failing tests first (commit `f0f06f0`), then the change (`3f1e3da`), then the change. Every result row now has
`seats.A.policy_errors` and `seats.B.policy_errors`: an integer for a policy seat (read from `ctrl.policy_errors()`
after the trial), `null` for scripted, WAIT, decoy and random seats, and `null` for a policy seat that exposes no
counter (so a missing counter is never read as zero). `analysis.render` gains a section with the sum per condition
and an "Odd rows" list of every row with a non-zero count. A held-out row with a non-zero count is labelled
"(harness error)" with a note that the run was not aborted. Rows from before this change have no field; for a policy
seat they are reported as "not recorded", not as zero. The runner's abort rules, `harness_error` and `aborted` are
unchanged. No policy run on H6.

## Paths
- `tests/test_eval_t08fix2_policy_errors.py` (new, 6 tests; committed first, all 6 failing on the base).
- `evaluation/controllers.py` (`policy_errors_of`), `evaluation/suite.py` (one row field), `evaluation/analysis.py`
  (`policy_error_totals`, `policy_error_lines`, called from `render`).
- `docs/final/evaluation/PROTOCOL.md` section 5, "Row fields": one added item.
- `docs/agent-sessions/T08-fix2-policy-errors.md`.
- Not touched: `evaluation/heldout/**`, `evaluation/results/**`, `evaluation/runs/**`, `agents/`, `pop/`, `tools/rl/`,
  existing tests, `tools/eval/` (its analyzer prints `analysis.render`, so no edit was needed).

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Failing test first: M seat whose network raises gives `policy_errors > 0` | Yes | `test_a_policy_seat_whose_network_raises_shows_policy_errors` (real runner, `BrokenNet`); test commit precedes the change |
| 2 | Every row has per-seat `policy_errors` (int or null); analysis sums per condition and lists non-zero rows under odd rows | Yes | `test_non_policy_seats_record_null`, `test_the_analysis_sums_per_condition_and_lists_odd_rows`, `test_the_section_names_odd_rows` |
| 3 | Held-out policy errors reported as a harness error, no abort | Yes | same test asserts "harness error"; `aborted` and `harness_error` row fields untouched (the suite's busy-controller tests still pass) |
| 4 | PROTOCOL section 5 one line; H6, ledger, bar and T09 evidence unchanged | Yes | `git diff 0ea8d73 --stat` |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1773 passed, 11 skipped, 5 xfailed, 2 warnings in 292.74s (0:04:52)
```
Run on the clean committed tree at `3f1e3da`. This report and the session note were added afterwards (docs only).

## Findings
No findings. Concerns for QA:
- A policy seat that raises in `choose` inside the runner still shows up only via this counter; the runner's own
  `seats.*.errors` stays 0, as T09 found. I did not change the runner.
- `policy_errors_of` returns `null` for a policy-kind controller without a `policy_errors` attribute (for example the
  `Slow` stand-in in existing tests). The shipped `make_rl_rival` always has one.
- The "harness error" label is applied only where `row["split"] == "heldout"`; tuning rows list the count without it.
- The 5 xfailed and 11 skipped are as on the base (not investigated here).

## Known limitations
The H6 rows already committed carry no field, so they show "not recorded" if re-analysed; the T09 evidence is unchanged
(decision #84: T09-fix1 states this in words).

## Unresolved findings
None.

## Requested next action
QA Gate 1 on `task/T08-fix2` at the sha above (`gate/T08-fix2-qa`). Evaluation Specialist Gate 2 applies (evaluation and
result-row change).

## Student decision required
None.

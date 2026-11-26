---
handoff_id: HO-T08-fix2-fix1-eval
task_id: T08-fix2-fix1
from: evaluation-specialist
to: orchestrator
consumed: docs/final/orchestration/reports/T08-fix2-fix1-qa.md@28a2442; reports/T08-fix2-fix1-tech-lead.md@adcbc33; tasks/T08-fix2-fix1.md@96d990d; reports/T08-fix2-evaluation-specialist.md@71a6ed0
reviewed_commit: 28a2442 (code under review: 114f9e6)
source_branch: gate/T08-fix2-fix1-eval
verdict: ACCEPT
---

# T08-fix2-fix1: Evaluation Specialist (Gate 2)

Verdict: **ACCEPT.** My F1 ruling (steps 1 to 6) is met exactly, and the intent of #84 holds end to end. No findings.

## F1 ruling, step by step
| Step | Met? | Evidence |
| --- | --- | --- |
| 1 totals: None when no recorded policy seat; sum of recorded rows plus `not_recorded: n` when mixed | Met | `policy_error_totals` in `evaluation/analysis.py`; `not_recorded` only when n > 0; fully recorded dict unchanged |
| 2 printing: "not recorded", "S (n not recorded)", "n/a" (SvS), footnote kept | Met | `_cells`; footnote line intact; QA probes cover all three |
| 3 `_seat_errors`: null on a policy-kind seat is not recorded; only ints count as recorded | Met | code read; null on scripted/fallback seat is skipped, not a policy seat |
| 4 old-row test changed to the not-recorded result | Met | one assertion `== 0` to `is None` (QA diff) |
| 5 xfail marker removed from QA probe | Met | one line removed; test passes |
| 6 T09 `analysis.txt` untouched | Met | no `evaluation/results/**` or `heldout/**` change |

Also: PROTOCOL section 5 sentence added (Eval N1). Scope has no `agents/`, `pop/`, `tools/rl/`.

## End-to-end path (rows to analysis to printed table)
Only consumers of the field: `evaluation/suite.py:210` (writes int or null) and `evaluation/analysis.py` (reads). `analyze_results --json` does not emit policy errors, so there is no second printing path. Every printed cell passes through `_cells`; the "Odd rows" list only prints non-zero values; the missing-rows footnote uses the same `_seat_errors` flag.

New test `tests/test_eval_t08fix2fix1_end_to_end.py`: real shipped weights, tuning split, dry run, temp dir, then the real `analyze_results` CLI. Results: SvS prints `n/a`, MvS and SvM print `0 | 0` (recorded zeros stay 0). The same rows with the field stripped, and with it nulled on policy seats, print `not recorded` for MvS and SvM, SvS stays `n/a`, and the "zero cannot be assumed" footnote appears.

## T09 re-analysis (read-only, from 5518f54, scratch dir)
`results.json` and `analysis.txt` extracted from `origin/orch/reviewed` 5518f54 into the scratch dir and analysed. `diff` against the committed `analysis.txt` shows only an appended section: 16 conditions (MvS and SvM, H6-1 to H6-8), every one `not recorded | not recorded`; zero cells printing 0; "Odd rows: None."; footnote "48 rows, so zero cannot be assumed". The re-analysis is honest: it neither claims zero errors nor invents a count. No policy run, no H6 run.

## Gate 2 checks
Environment, observation and action boundary, baseline fairness, reward and training method, checkpoint: untouched (no `agents/`, `pop/`, `tools/rl/` change). Train and held-out separation: nothing under `evaluation/heldout/**` or `evaluation/results/**` written; my scratch files are outside the repo. Evaluation validity and abort rules: unchanged (held-out non-zero count still labelled harness error, no abort). Fallback labelling: unchanged. Latency, replay fidelity: not affected, not re-measured.

## Tests
Added `tests/test_eval_t08fix2fix1_end_to_end.py` (1 test, commit on this branch).
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean tree, branch gate/T08-fix2-fix1-eval)
1793 passed, 12 skipped, 5 xfailed, 2 warnings in 282.58s (0:04:42)
```
(QA 1792 plus my one test.)

## Findings
None. Notes carried from QA (not blocking): a bool counts as an int (the runner never writes one); a row with no `controllers` block and a null field is skipped (real rows always have `controllers`). N1 (runner `seats.*.errors` excludes swallowed policy errors) remains an owner call outside the evaluation paths; PROTOCOL now says so.

## Requested next action
Orchestrator: Gate 3 for T08-fix2-fix1, then T08-fix2. No Student decision required.

---
handoff_id: HO-T08-fix2-eval
task_id: T08-fix2
from: evaluation-specialist
to: orchestrator
consumed: docs/final/orchestration/reports/T08-fix2-qa.md@114c3f6; docs/final/orchestration/reports/T08-fix2-tech-lead.md@8e60513; tasks/T08-fix2.md and DECISIONS-2026-11-24.md (#84) and reports/T09-rules-reviewer.md (finding 1) @c325f9e
reviewed_commit: 114c3f6 (code under review: 8e60513)
source_branch: gate/T08-fix2-eval
verdict: ACCEPT WITH NOTES, conditional on one small fix-up (F1) before Gate 3
---

# T08-fix2: Evaluation Specialist (Gate 2)

Verdict: **ACCEPT WITH NOTES.** The mechanism is correct and the boundaries hold. F1 should be fixed in a
T08-fix2-fix1 before Gate 3 (small, evaluation-only).

## Gate 2 checks
- **Environment, observation and action boundary:** untouched. `git diff 0ea8d73..8e60513` has no file under
  `agents/`, `pop/`, `tools/rl/`; the new code reads `ctrl.policy_errors()` after the trial, never at inference.
- **Baseline fairness, reward and training method, checkpoint:** untouched. The shipped weights load by the
  existing SHA-256 check (`make_shipped_policy`), as the smoke below shows.
- **Train/held-out separation:** no change under `evaluation/heldout/**`, `evaluation/results/**` or `tools/rl/`.
  No policy run on H6 (none made by me, none by QA).
- **Evaluation validity and abort rules (#24):** `aborted`, `harness_error` and abort logic untouched. A non-zero
  count on a held-out row is labelled "(harness error)" and the analysis says the run was not aborted (QA probe
  `test_heldout_harness_error_label_and_tuning_has_none`).
- **Fallback labelling:** untouched; fallback seats are still labelled by kind and record `policy_errors: null`.
- **Latency, replay fidelity:** not affected (a counter read per trial). Not re-measured.
- **Honest reporting of failed trials:** improved: swallowed inference errors are now in every row. The T09
  committed evidence is unchanged (re-analysis by QA only appends a section).

## Shipped-weights tuning smoke (no H6)
`tools/eval/run_versus_suite.py --split tuning --dry-run --configs SvS,MvS,SvM,MvM --trials 1 --max-frames 400`
into a scratch dir (real `make_rl_rival` through `make_shipped_policy`): 48 rows (35 hit the frame cap, expected at
400 frames). Seat tally: policy seats 26, all `policy_errors == 0`; scripted 38 and fallback 32, all `null`.
The analyzer prints the totals table with 0 and "Odd rows: None." Consistent with the design. Committed as
`tests/test_eval_T08fix2_shipped_smoke.py` (D1, SvS/MvS/SvM, 300 frames, temp dir).

## Rulings
- **F1: must be fixed before Gate 3.** Decision #84 and the brief exist so that a silent zero is never read as
  "no errors"; the table printing 0 for 48 unrecorded T09 rows reproduces that misreading in the very table a
  reader looks at, and the footnote is easy to miss. The fix is small. Exact fix for a T08-fix2-fix1 Tech Lead
  task (paths: `evaluation/analysis.py`, `tests/test_eval_t08fix2_policy_errors.py`, and the QA probe marker):
  1. `policy_error_totals`: per condition, count rows whose policy seats are all recorded versus not. If no row
     in the condition has a recorded policy seat, return `policy_errors: None` and `rows_with_errors: None`; if
     some do, keep the sum over recorded rows and add `not_recorded: n`.
  2. `policy_error_lines`: print `not recorded` in those cells (and `S (n not recorded)` for a mixed condition);
     conditions with no policy seat at all (SvS) print `n/a`, not 0. Keep the footnote.
  3. `_seat_errors`: treat a policy-kind seat whose field is `null` (counter missing, N2) as not recorded, not as
     a zero.
  4. Update `test_old_rows_without_the_field_are_read_as_not_recorded`, which asserts 0 and encodes the defect.
     Remove the strict `xfail` marker from QA's probe `test_old_rows_are_not_printed_as_zero_in_the_totals_table`
     (it will XPASS and, being strict, fail otherwise); QA owns that file, so the orchestrator should authorise
     the one-line marker edit or have QA do it.
  Do not regenerate or edit the committed T09 `analysis.txt`.
- **N1: no follow-up needed for evaluation; one optional follow-up, not blocking.** `seats.*.errors` stays 0
  because `PolicyMacro` swallows the exception inside `choose` and the runner never sees it. `policy_errors` now
  covers this in every row, and PROTOCOL section 5 names it. A truthful runner counter would need a change in
  `agents/rl/policy.py` (re-raise or flag to the seat) or `pop/seats.py`, outside the evaluation paths, and it
  would alter in-play behaviour; that is an owner call. Recommend only a one-line note in PROTOCOL section 5
  that `errors` does not include swallowed policy errors (evaluation path, can ride with fix1).
- **N2: fold into F1 fix** (step 3). Theoretical for the shipped rival, but a null read as zero is the defect class
  this task closes.
- **N3: accept.** Label by `split == "heldout"` is the right test; a dry run has no policy seat to err.

## Findings
| id | severity | finding |
| --- | --- | --- |
| F1 | minor, fix before Gate 3 | totals table prints 0 for unrecorded rows (as QA F1) |
| N2 | note | policy seat with null counter is summed as 0; fold into F1 |
| N1 | note | runner `errors` still 0 for swallowed errors; optional PROTOCOL sentence, runtime change is Saad's call |
| N4 | note | the controller kind labels in rows include `fallback` for the scripted seats in the smoke; they carry `null`, matching the brief |

## Tests
New: `tests/test_eval_T08fix2_shipped_smoke.py` (1 test).
`uv run --frozen --extra play --extra train --extra online pytest -q` at the smoke-test commit (tree clean apart from this untracked report):
```
1778 passed, 12 skipped, 6 xfailed, 2 warnings in 283.93s (0:04:43)
```
(QA: 1777/12/6 including its probes; the extra pass is my smoke test.)

## Requested next action
Orchestrator: open T08-fix2-fix1 for Tech Lead with the F1 fix above, then QA re-check, Gate 3. No Student decision
required.

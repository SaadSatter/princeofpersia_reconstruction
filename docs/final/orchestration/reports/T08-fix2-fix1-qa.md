---
handoff_id: HO-T08-fix2-fix1-qa
task_id: T08-fix2-fix1
from: qa
to: evaluation-specialist
consumed: docs/final/orchestration/reports/T08-fix2-fix1-tech-lead.md@adcbc33; tasks/T08-fix2-fix1.md@96d990d; reports/T08-fix2-qa.md@114c3f6; reports/T08-fix2-evaluation-specialist.md@71a6ed0
reviewed_commit: adcbc33 (code at 114f9e6; adcbc33 adds only the tech-lead report)
source_branch: gate/T08-fix2-fix1-qa
verdict: ACCEPT
---

# T08-fix2-fix1: QA (Gate 1)

Verdict: **ACCEPT.** No findings. Two notes.

## Acceptance table
| Check | Met? | Evidence |
| --- | --- | --- |
| New tests fail on 71a6ed0 | Met | With `evaluation/analysis.py` from 71a6ed0 (restored afterwards), the three test files gave 6 failed: 4 new `test_eval_t08fix2fix1_*`, the edited `test_old_rows_...not_recorded` and the un-xfailed QA probe. |
| Two authorised test edits only | Met | `git diff 71a6ed0..adcbc33 -- tests`: one assertion `== 0` to `is None` in `test_eval_t08fix2_policy_errors.py`; one removed `xfail` line in `test_qa_T08fix2_policy_errors_cli.py`; plus the new file `test_eval_t08fix2fix1_not_recorded.py`. Nothing else changed. |
| Scope | Met | `git diff --name-only 71a6ed0..adcbc33` is 7 files: `evaluation/analysis.py`, PROTOCOL.md, the three tests above, one `docs/agent-sessions/` file, the tech-lead report. No `agents/`, `pop/`, `tools/rl/`, `evaluation/heldout/**`, `evaluation/results/**`, no committed T09 `analysis.txt`. |
| T09 re-analysis (read-only) | Met | `results.json` copied from 5518f54 to scratch; `tools/eval/analyze_results.py` run on it; `diff` against committed `analysis.txt`: the only difference is the appended section "PPO inference errors", all 16 conditions (MvS and SvM) read `not recorded | not recorded`, odd rows "None.", footnote "48 rows, so zero cannot be assumed". Every other line is identical. T09 has no SvS rows, so `n/a` is covered by probe, not by T09. |
| Mixed prints "S (n not recorded)" | Met | probe `test_mixed_and_fully_recorded_conditions`: `2 (1 not recorded) | 1 (1 not recorded)`. |
| Fully recorded unchanged | Met | probe: dict equals the old shape (no `not_recorded` key), prints `2 | 1`; recorded zero prints 0. |
| PROTOCOL section 5 | Met | Diff is one sentence added inside the existing `seats.A/B.policy_errors` item (runner `seats.*.errors` excludes swallowed errors; analysis prints "not recorded", never 0). Nothing else changed. |
| Edge: no `controllers` and null field | Acceptable | Skipped (prints `n/a`), probe `test_edge_no_controllers_...`. Real rows always carry `controllers` (runner output); a policy seat in a real row with null is "not recorded". |

## Findings
None.

Notes:
- N1: a bool counts as an int in `_seat_errors` (`isinstance(True, int)`); the runner never writes one. Not worth a fix.
- N2: the reviewed commit is adcbc33 but the handoff's `source_commit` is 114f9e6; the only difference is the report file, so the review covers both.

## Tests
Added `tests/test_qa_T08fix2fix1_not_recorded.py` (7 probes: all cell kinds, mixed, fully recorded, recorded zero, MvM with one seat unrecorded, null on scripted vs policy seat, edge case, non-integer value). All pass.

Full suite on a clean tree (gate branch with my probe committed):
```
uv run --frozen --extra play --extra train --extra online pytest -q
1792 passed, 12 skipped, 5 xfailed, 2 warnings in 280.88s (0:04:40)
```
(1785 from the tech lead plus 7 probes.) No policy run, no H6 run, nothing written under `evaluation/heldout/**` or `evaluation/results/**`.

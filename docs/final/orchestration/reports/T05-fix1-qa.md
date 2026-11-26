---
handoff_id: HO-T05-fix1-qa
task_id: T05-fix1
date: 2026-11-24 ET
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T05-fix1-tech-lead.md@161a841
source_branch: gate/T05-fix1-qa
source_commit: see git log (head of gate/T05-fix1-qa)
reviewed_commit: ce8c8c07f1d77e2f800f331f6716b1fed5862f25
verdict: ACCEPT WITH NOTES
---

# T05-fix1: QA report (Gate 1)

Branch `gate/T05-fix1-qa` created from 161a841 (report travels with it).

## Results
- Full suite: `1 failed, 860 passed, 12 skipped, 3 xfailed in 66.17s` (`uv run pytest -q`). The one failure is `test_gate_t04fix1_qa_probes.py::test_numpy_str_answer_still_works` (ModuleNotFoundError numpy).
- Claim "fails at base too": VERIFIED. At 0846a16 (clean worktree) `tests/test_gate_t04fix1_qa_probes.py` gives the same failure, same line 89. Environment issue, not this change.
- With my probe file: 4 passed, 1 xfailed (strict) in that file.
- Scope: `git diff --name-only 6692771..161a841` lists only agents/macros.py, agents/versus_baseline.py, MACROS.md, the session record, the report and the four permitted test files. No `pop/` change. CI files untouched.

## The six rewritten assertions (drive -> drive_one)
Checked in `git diff 0846a16 ce8c8c0 -- tests/test_macros.py`. Not weakened. Same starts, same macros, same expected end state (room, row, hearts). The old test asserted `executor.state == "done"` (or `reason == "left_room"`) after a run during which the Fixed policy re-asks the macro; the new one asserts the first macro event is `macro_done` with a specific reason (`dropped`, `new_room`, `left_room`), which is stricter on cause. Row/room/hearts asserts are kept (the drop test now ticks 30 frames to let the fall settle). The change is justified: the old end-state could be a later macro's state. Minor remark: `drive_one` stops at the first event, so a macro that wrongly succeeds early with the right reason would pass, but the position asserts guard that. Gate 2 probe tests (eval baseline) lost only their xfail marks.

## Independent sweep (my sampler, not the tech lead's)
Sampler in `tests/test_gate_t05_fix1_qa_probes.py::_sweep`: seed 20261124, two distinct rooms from 1..6, random floor cell (row 2, chars `_` or `P`) and facing each, baseline vs opponent, seats swapped on odd k, 3600 frames, seed k.
- vs WAIT, 30 duels: 29 W, 1 L, 0 T.
- vs Random, 30 duels: 28 W, 2 L, 0 T.
- Fallbacks of the baseline over 12 duels (seed 20261125): 0.
- Default arena start vs WAIT, seeds 4,5,6 both seat orders: 6/6 wins.
- Baseline vs baseline, random starts, sampler seed 77, 24 duels: 12 won:A, 11 won:B, 1 draw:time_up.
Compared with the earlier gate sweep (22 W, 8 L, 10 T), QA-2 and QA-3 are resolved on an independent sample. The tech lead's numbers are in line with mine.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Default start reaches rooms 4 and 5, uniform most seeds | yes (indirect) | default start vs WAIT 6/6 wins (new seeds 4-6); tech lead's room/uniform counts not re-measured by me |
| 2 | Finds a WAIT rival in rooms 4-6 | yes | Gate 2 probe `finds_a_passive_rival_on_the_lower_floor` (3 cases) passes without xfail; sweep 29/30 |
| 3 | Does not die to a lone guard | yes | `survives_a_guard_room_start` rooms 4,5 pass; QA-2 probes pass |
| 4 | Inputs legal, determinism | yes | existing QA probes (36 random-room duels, 0 fallbacks; replay; identical fresh baselines) pass; my fallbacks 0 |
| 5 | Competence table on tuning and frozen held-out | yes | `LOWER_HELD_OUT_STARTS` unchanged vs 0846a16 (diff shows no start-list edits); tests pass |
| 6 | Baseline vs baseline not 10/10 draws, 12 swapped duels | yes, with a note | QA-1 probes pass (xfail removed); mine: 1 draw in 24. See N1 |
| 7 | Memory disclosed in MACROS.md; decision #31 recorded confirmed | yes | `docs/final/MACROS.md` edited in the diff (read, not re-audited line by line) |
| 8 | xfails removed only for fixed findings | yes | qa-1..3, eval-1..2 removed, each now passing; no unfixed finding hidden |
| 9 | Suite green | yes except environment | 1 pre-existing numpy failure, same at base |

## Findings
- **N1 (minor, reproduced, design note)**: the mirror match is "fixed" by seat-order asymmetry, not by better play. The tech lead's 12 duels are one identical trace and seat B always wins. Passes the brief's letter ("not 10/10 no-hit draw"), but a seat's win rate in baseline-vs-baseline depends on seat. Repro: `uv run pytest -q -s tests/test_versus_baseline.py -k mirror`. Gate 2 should judge whether that is acceptable.
- **F1 (minor, reproduced)**: baseline loses to a motionless WAIT seat in 78 frames from start A=(5,2,0,-1), B=(6,2,0,1), seed 17, `swap_seats=True`. Cause not diagnosed (not checked whether hazard or guard). Repro: `uv run pytest -q tests/test_gate_t05_fix1_qa_probes.py` (xfail strict `QA-F1`). Expected: baseline wins; actual: WAIT seat wins. Two further losses to Random in the sweep: k=27 (6,2,1,+1) vs (5,2,8,-1) and k=29 (1,2,3,+1) vs (3,2,7,+1), both swapped; unverified cause.
- **N2 (note)**: all three sweep losses are swapped-seat games (baseline in seat B). Unverified whether this is chance (n=3) or a seat-B effect; Gate 2 may want a larger swap-balanced sweep.
- No blocker or major found.

## Not checked
- Browser/Playwright (not part of this change).
- The tech lead's per-seed room-4/5/uniform counts and rule-5 threshold sensitivity (it admits the thresholds were tuned on the failing duels; only the old top-row held-out set is unseen). I did not do a threshold sweep.
- Hidden-information review beyond existing probes (the changes read only the seat's own observation and `last_result`; I did not trace each line of macros.py for leaks, and the existing boundary probes pass).
- `numpy`-dependent test (environment).

## Requested next action
Gate 2 (evaluation-specialist) on ce8c8c0: judge N1 (seat-order win), the seat-B pattern in N2, and the rule 5 thresholds. Tests: `tests/test_gate_t05_fix1_qa_probes.py`.

## Student decision required
none

---
handoff_id: HO-T08-fix1-tech-lead
task_id: T08-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T08-fix1.md@18a169f (decisions #58-#61, #64-#66, #74-#77 in DECISIONS-2026-11-24.md@18a169f); reports/T08-tech-lead.md@deb8718; reports/T08-qa.md@cf43ba1; reports/T08-evaluation-specialist.md@059aea5
source_branch: task/T08-fix1
source_commit: 212cd37d6c6c9107f4ed45d071d772d5b113e2d8
reviewed_commit: n/a
verdict: n/a
---

# T08-fix1: tech-lead report

Status: done, with six existing tests red that the brief does not let me edit (listed under Findings; one-line patches given).

## Work completed
Base `059aea5`. Every fix-list item built, each with a failing test committed first (`4b08daa`; the H6 selection rule
itself was committed before that and before any start was added, `1f6fe1e`). No policy (PPO or baseline) ran on H6, the
real ledger was never written, no result was consulted for any new start, no training, no `--live`. Nothing under `pop/`,
`agents/`, `tools/rl/`, `play.py`, `render/`, `web/`, `server/` was touched.

| Item | Commit | What |
| --- | --- | --- |
| 6 (rule first) | `1f6fe1e` | PROTOCOL.md 3.1: the written selection rule for H6-5 to H6-8 |
| tests first | `4b08daa` | five new test files, all failing at that commit |
| 1, 2, 3, 4, 5 | `25475a3` | ledger key and clean-tree check, D1 attribution, seat-B starts and per-seat analysis, F-2, F-4, B2 disguise; F-1/F-2/F-4 xfail marks removed |
| 6 (starts) | `632fc95` | H6-5 to H6-8 from `tools/eval/select_heldout_starts.py`, H6 re-frozen |
| 7, 8 | `681ac3a` | PROTOCOL.md and H6 README wording, pre-registered bar, `tools/eval/exposure_table.py` |
| session | `212cd37` | `docs/agent-sessions/T08-fix1-evaluation-corrections.md` |

**New H6 SHA-256: `d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266`** (recorded in
`evaluation/manifest.py`, `evaluation/heldout/README.md`, `docs/final/evaluation/PROTOCOL.md`; the superseded first freeze
`44da40ec...0847` is named as superseded). H6-1 to H6-4 are byte-identical to the first freeze (the diff of `H6.json` is only
additions; a test rebuilds the old hash from the first four starts).

### What each item does
1. **#64 key.** `manifest.claim_heldout_run` refuses a second claim for the same (policy key, `info["commit"]`); the same
   weights on a new commit are allowed and both lines stay (each line has `status: claimed`). `manifest.require_known_clean_tree`
   refuses an unknown commit or `dirty` not False. `suite.git_state` now counts untracked files under `evaluation/` and
   `tools/eval/` (not the two ledger files) and tracked changes anywhere; outside a repository it returns commit `unknown`,
   `dirty` None. Every refusal is appended to `evaluation/heldout/refusals.jsonl` beside the ledger (`status: refused`,
   reason, commit); it claims nothing, so a later clean run still works. The refusals go to a separate file because the QA
   probe asserts the ledger has exactly one line after four refused runs.
2. **F-1.** D1 credits a guard only if the agent was in the guard's room on the first frame the guard was knocked down or
   downed; the uniform must come from a credited guard. New metric `credited_guards`.
3. **#65.** `Start` gained `subject` and `forced_seat`; the monitor, `subject_seat` and `result_subject` follow the start.
   `tuning.json` holds 11 mirrored starts `<id>-B` (D1, B2, I3 all three, F5-a, F5-b): rivals, hearts, disguise swapped, guards
   kept, seat A forced to the same stand-in. A mirrored start runs SvS and SvM (the forced seat's letter must be S).
   `analysis.success_by_scenario` groups by subject seat and labels the subject's own controller; the table has a
   "subject seat" column. Tuning split only; H6 has no mirrors.
4. **F-2.** `duel_results` lists a row with `controllers: {}` as an aborted trial of "none built" (it sits in the
   denominator, and `render` already lists it under "Aborted rounds"). **F-4.** `--replay` reads `split` from `meta.json`
   (fallback `--split`), and refuses an unknown split with exit 2.
5. **#76 / #66.** B2 also needs the subject disguised on the last frame (reason `disguise_lost`); the threshold stays a named
   parameter (50); `success_active` is reported only when the flag is true and is never scored.
6. **#74.** Rule in PROTOCOL.md 3.1; implemented in `tools/eval/select_heldout_starts.py` (candidates ordered by a SHA-256 of
   their coordinates; the module reads no policy, baseline or run data, and a test greps its source for that). Result:
   H6-5 A (2,2,3) B (6,2,0); H6-6 A (6,2,9) B (2,2,8); H6-7 A (6,2,5) B (2,2,0); H6-8 A (5,2,2) B (4,2,3); two guards per
   start in two rooms. Tests: 8 starts, disjoint from the 8 `TUNING_STARTS`, every tuning scenario (mirrors included),
   `arena.STARTS`, H6-1 to H6-4 and each other; post tuples disjoint from tuning and default posts; rivals in different
   rooms and outside their own start's patrols; no training or tuning configuration repeated; the rule regenerates the
   frozen starts.
7. **Docs (#75, #77, E-6).** PROTOCOL.md section 3 and the H6 README: "unseen start pairs and guard layouts", start cells and
   post tuples disjoint, patrol ranges not, each start reported and the most training-like labelled; H-b says trained for
   duels only, so skill scenarios are "a result, not a defect"; the pre-registered bar (at least 14 of the 16 held-out
   duels, no aborted duel, else "not supported" with the full numbers); Wilson lower bounds computed for the new sizes
   (16/16 0.81, 14/16 0.64, 12/16 0.51; 6 of 6 starts 0.61; 3 of 3 0.44).
8. **Exposure table.** `tools/eval/exposure_table.py` generates it from the frozen file: of the 16 posts, 5 lie entirely
   inside a default patrol, 1 partly, 10 not at all; H6-1 is training-like, H6-3, H6-6, H6-7, H6-8 partly, H6-2, H6-4, H6-5
   unseen layouts. For the first four starts it gives the Gate 2 numbers (2, 1, 5).

## Paths
Changed: `evaluation/{analysis,manifest,monitors,spec,suite}.py`, `evaluation/scenarios/tuning.json`,
`evaluation/heldout/{H6.json,README.md}`, `tools/eval/run_versus_suite.py`, `docs/final/evaluation/PROTOCOL.md`,
`tests/test_qa_T08_probes.py` (three xfail decorators removed, nothing else). New: `tools/eval/select_heldout_starts.py`,
`tools/eval/exposure_table.py`, `tests/test_eval_t08fix1_{ledger,monitors,seatb,h6,docs}.py`,
`docs/agent-sessions/T08-fix1-evaluation-corrections.md`, this report. Scope check
`git diff --name-only 059aea5..HEAD` (before this report): all paths inside the brief's permitted list.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | #64 key, refusals, recorded runs | met | `tests/test_eval_t08fix1_ledger.py` |
| 2 | F-1 before #65 | met | `test_eval_t08fix1_monitors.py`; the QA F-1 probe now passes un-marked |
| 3 | #65 seat-B starts, per-seat analysis | met | `test_eval_t08fix1_seatb.py` |
| 4 | F-2, F-4 | met | same file; QA probes un-marked |
| 5 | #76, #66 | met | `test_eval_t08fix1_monitors.py` |
| 6 | #74 rule first, 8 starts, new hash in three places | met | `1f6fe1e` precedes `632fc95`; `test_eval_t08fix1_h6.py` |
| 7 | #75, #77, E-6 docs | met | `test_eval_t08fix1_docs.py` |
| 8 | exposure script (optional) | met | `tools/eval/exposure_table.py` |

## Tests run
Base suite line: not re-run by me. The Gate 2 report's line for the base lineage (`gate/T08-eval`, cf43ba1 plus its own
file) is `1479 passed, 11 skipped, 8 xfailed, 2 warnings in 379.84s`.

```
uv run --frozen --extra play --extra train --extra online pytest -q      (on 212cd37)
6 failed, 1569 passed, 11 skipped, 5 xfailed, 2 warnings in 393.18s (0:06:33)
```
The 5 xfailed are the 4 pre-existing repository ones plus the QA F-3 probe (strict xfail, still true: H6 patrol cells still
overlap tuning and default cells). The 11 skips are the same count as the base.

## Findings
**The six failing tests are all existing tests that the new H6 or the mirrored starts invalidate. None is a regression in
behaviour. I did not edit them (the brief allows only the QA probe marks); each needs a one-line update by its owner.**

| Test | Why it fails | Needed change |
| --- | --- | --- |
| `tests/test_eval_T08_gate2.py::test_f3_exposure_of_h6_guard_posts_to_training` | pins `(2, 1, 5)` over `_h6_starts()`, which now has 8 starts (16 posts: 5, 1, 10) | slice `[:4]`, or pin `(5, 1, 10)` |
| `tests/test_eval_T08_gate2.py::test_h6_has_four_starts_and_two_seat_orders_give_eight_outcomes` | `len(_h6_starts()) == 4` | now 8 starts and 16 duels |
| `tests/test_eval_registry.py::test_heldout_split_is_one_full_duel_scenario_h6_with_four_starts` | start ids pinned to H6-1..H6-4 | H6-1..H6-8 |
| `tests/test_eval_suite.py::test_heldout_dry_run_uses_wait_seats_checks_the_hash_and_claims_nothing` | start ids pinned to H6-1..H6-4 | H6-1..H6-8 |
| `tests/test_eval_suite.py::test_dry_run_writes_one_complete_row_for_every_start_of_every_scenario` | asserts seat A is `scripted` on every row; a mirrored start forces seat A to WAIT (kind `fallback`), as seat B was forced before | assert the controller kind of the non-forced seat, or use `forced_controllers` |
| `tests/test_qa_T08_probes.py::test_a_one_byte_change_is_refused_and_the_real_file_hash_is_the_recorded_one` | hard-codes the old hash prefix `44da40ec` and suffix `0847` | new hash `d013152a` / `5266`. (The brief says change nothing else in this file; the re-freeze makes this assertion false.) |

The other new Gate-2 assertions (`test_no_h6_start_reproduces_a_training_configuration`, `test_power_of_an_eight_outcome_heldout_run`,
`test_training_only_ever_had_guards_in_rooms_4_and_5`) still pass.

Not a defect, a property to know: the real held-out tests in `tests/test_eval_suite.py` and `tests/test_qa_T08_probes.py`
run the CLI with the real `git_state`, so since #64 they pass only on a clean tree with known commit. They passed in my full
run (everything committed, only this report untracked outside `evaluation/` and `tools/eval/`). In a checkout with
uncommitted tracked changes or new files under `evaluation/` or `tools/eval/`, they fail with "needs a clean tree". That
follows from the brief (item 1) and I could not add a conftest fixture without an unpermitted path.

## Known limitations
- H6 start choice: with the rule's inputs only 13 floor cells of the corridor row were free; rooms 2 and 6 hold 9 of them,
  so the new starts lean on those rooms (rooms 4 and 5 contribute one rival cell each). Selection is by the rule, not tuned.
  The new rival cells are 3 in room 2, 3 in room 6 and one each in rooms 4 and 5; none in rooms 1 or 3.
- Patrol ranges still overlap training patrols (#75, documented). The QA F-3 probe stays a strict xfail.
- The claim is a ledger convention: a deleted `ledger.jsonl` resets it, `HELDOUT_SHA256` is a source constant (unchanged
  from T08, noted by QA). `refusals.jsonl` and `ledger.jsonl` are not gitignored.
- Mirrored starts keep the original guards and cells, so a mirrored start repeats geometry; they add the seat, not new layouts.
  Seat-B rows run SvS and SvM only (MvS would repeat SvS with the stand-in forced).
- Wilson table in PROTOCOL.md is for 16 independent duels. The two seat orders of one start share geometry (Gate 2 noted the
  effective n may be between 8 and 16); the bar of 14 of 16 is Saad's and is not changed.
- The ledger check is still check-then-append with no lock (unchanged).

## Unresolved findings
None of the gate findings is left open in code. Open for others: the six test updates above (QA/Eval owners at their
gates); QA F-3 is accepted and documented (#75).

## Requested next action
Commit to review: 212cd37d6c6c9107f4ed45d071d772d5b113e2d8 on task/T08-fix1 (plus the commit that adds this report)
What changed: the held-out run-once key is (weights, engine commit) with clean-tree and unknown-commit refusals and a
refusals file; D1 credits only the agent's own kills; the tuning split has mirrored seat-B starts with per-seat analysis; the
analysis tolerates rows with no controllers; `--replay` reads the split from the trace; B2 needs the disguise at the end;
H6 has eight starts chosen by a rule committed first, re-frozen at d013152a...5266; the protocol states the claim, the
bar and the intervals.
How to check it:
- `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t08fix1_*.py tests/test_qa_T08_probes.py`
- the rule first: `git log --oneline 059aea5..task/T08-fix1` (`1f6fe1e` before `632fc95`); `git diff 059aea5..HEAD -- evaluation/heldout/H6.json` shows additions only
- reproduce the starts: `python3 tools/eval/select_heldout_starts.py` and compare with H6-5..8; `python3 tools/eval/exposure_table.py`
- schema only, no policy: `python3 tools/eval/run_versus_suite.py --dry-run --split heldout --trials 1 --max-frames 30 --out <tmp>`
- adversarial: try to claim twice for one (weights, commit) with a different seed key, scenario subset or trial count; run a real held-out
  command with `--out` somewhere and a dirty tree (it must refuse and write only `refusals.jsonl`); never use the real ledger path with a policy.
What I am unsure about:
- the rule's choices (spans of 2 to 4 columns, facing toward the room's middle, a SHA-256 order): all are mine, written before use;
  Gate 2 should say whether any needs Saad.
- the D1 "struck" reading is approximated by the agent's room at the first knocked-down or downed frame; the state has no striker field.
- whether QA wants `refusals.jsonl` ignored by git or committed (it is neither today).
- the six red tests above.
Touches the knowledge boundary or AI seat: yes (scenarios, baseline/PPO comparison data, held-out set and ledger: Gate 2 applies)

## Student decision required
none

## Addendum: decision #78 test updates (pinned values only)
| Test | Old assertion | New assertion |
| --- | --- | --- |
| `tests/test_eval_registry.py::test_heldout_split_is_one_full_duel_scenario_h6_with_four_starts` | start ids `== ["H6-1", "H6-2", "H6-3", "H6-4"]` | `== [f"H6-{i}" for i in range(1, 9)]` |
| `tests/test_eval_suite.py::test_heldout_dry_run_uses_wait_seats_checks_the_hash_and_claims_nothing` | row start ids `== ["H6-1", "H6-2", "H6-3", "H6-4"]` | `== [f"H6-{i}" for i in range(1, 9)]` |
| `tests/test_eval_suite.py::test_dry_run_writes_one_complete_row_for_every_start_of_every_scenario` | seat A is `scripted`, name `versus-baseline*`, version `source:*` on every row | normal starts: unchanged for seat A. Mirrored `-B` starts: `subject_seat == "B"`, seat A is the forced stand-in recorded in `forced_controllers["A"]` (`wait` gives kind `fallback`, `decoy` gives `scripted`, name equal to the stand-in), and the subject seat B is the scripted `versus-baseline`. Every row's subject seat is scripted baseline |
Not touched: the QA hash probe and `tests/test_eval_T08_gate2.py`.

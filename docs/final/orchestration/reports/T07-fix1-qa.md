---
handoff_id: HO-T07-fix1-qa
task_id: T07-fix1
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T07-fix1-tech-lead.md@2c9915f (task brief docs/final/orchestration/tasks/T07-fix1.md@e51dd12)
source_branch: gate/T07-fix1-qa
source_commit: bc3480e
reviewed_commit: 2c9915f (code and tests fa0c840; failing-tests commit 23be879)
verdict: ACCEPT WITH NOTES
---

# T07-fix1: QA report

Status: done

## Work completed
Checked out 2c9915f, ran the full suite, read the whole diff against base ae90c8c, and added independent tests. Checked the two edits to existing tests (#42, #44), the stop-on-error rule through a real subprocess, start disjointness, the overlap with candidate H6, and the evaluation coverage question. No blocker or major finding. One minor reproduced finding (xfail), two documentation inaccuracies, one finding for T08.

## Paths
- `tests/test_gate_T07fix1_qa.py` (7 pass, 1 `xfail(strict)`), commit bc3480e.
- Scope: `git diff --name-only ae90c8c..fa0c840` is agents/rl/policy.py, tools/rl/env.py, tools/rl/train.py, tests/test_rl_policy.py, tests/test_rl_train.py, tests/test_rl_fix1_errors.py, tests/test_rl_fix1_starts.py, docs/final/RL_POLICY.md, docs/agent-sessions/{16,17}. All inside the brief's permitted paths. No pop/, evaluation/, macros.py or versus_baseline.py change. No CI change. Session numbers 16 and 17 are free on this base, on main and on orch/wip-T08.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Parity over >= 200 observations, several seeds | Met | `_record_duels()` over seeds 0-5, fresh `Encoder` per duel, `assert n >= 200`, tolerance still `1e-9`, assertion unchanged in strength. Passes in the full suite. |
| 2 | Injected error counted; in log.jsonl, summary.json, smoke output; stops the run | Met | tech lead's 5 tests pass; mine: subprocess run with `Encoder.features` broken exits **2**, stderr starts `TRAINING STOPPED: policy or encoder error ...`, no `weights.json`, `summary.json` has `stopped: policy_error`, `weights_sha256: null`, `policy_errors > 0`, log row has `policy_errors` and `stopped`. A single late error (7th call) is also caught. A clean subprocess run exits 0 with `policy_errors: 0`. |
| 3 | About 8 starts incl. lower floors, disjointness test | Met | 8 starts, 6 new in rooms 1-6 incl. 4, 5, 6. My test checks the 12 new cells against `HELD_OUT_STARTS`, `LOWER_HELD_OUT_STARTS`, `LOWER_TUNING_STARTS`, the midterm two and candidate H6: disjoint, no cell reused inside the six, all on row 2, cols 0-9. |
| 4 | RL_POLICY.md states #43, new starts, labelled numbers | Met, with one wrong sentence | #43 stated plainly (lines 54-57). Speed labelled estimate. Lines 124-125 are wrong about `final_check` (see N2). |
| 5 | Smoke run < 60 s, deterministic | Met | `test_smoke_training_...` and `test_training_is_reproducible_...` pass in the suite. |
| 6 | Full suite | Met | below |
| 7 | No full training run | Met | none started; my CLI runs were 2 updates, 200 frames. |

## Tests run
```
uv run --frozen --extra play --extra train pytest -q      (at 2c9915f, before my tests)
1120 passed, 11 skipped, 2 xfailed in 167.45s (0:02:47)
uv run --frozen --extra play --extra train pytest -q tests/test_gate_T07fix1_qa.py
7 passed, 1 xfailed in 0.99s
```

## Checks you asked for
**Edit to `tests/test_rl_train.py` (#44).** The diff is one test: renamed `..._are_only_the_two_midterm_tuning_starts` to `..._begin_with_the_two_midterm_tuning_starts`, `== 2` to `== 8`, and a comment. The second assertion (`a[0] != b[0]`, different rooms) is untouched and still holds for all 8. Decision #44 adds six starts, so `== 2` cannot hold: the edit is forced. Nothing else in the file changed. One consequence: the renamed test no longer checks that the first two are the midterm starts; the tech lead's new test `test_there_are_about_eight_tuning_starts_with_the_midterm_two_first` does, so no coverage was lost.

**Edit to `_record` (#42).** The old `_record(n)` is replaced by `_record_duels()` and a new `_record(n)` that concatenates six seeds. The test now asserts `n >= 200`, keeps `worst < 1e-9`, and builds a fresh `Encoder` per duel. Not weakened. Mild point: `_record` is no longer used by the parity test (it uses `_record_duels`); check that other callers of `_record` still pass (they did, suite green).

**Midterm start vs candidate H6-4.** Confirmed from `git show 25e4587:evaluation/heldout/H6.json`: H6-4 is A `(3,2,5,-1)`, B `(1,2,3,+1)`. The midterm tuning start `(1,2,3,+1)`, the first element of the second tuning pair `((1,2,3,+1),(3,2,6,-1))`, equals H6-4's **B** rival, not its A rival (the brief says "A cell"; it is the tuning pair's A slot and H6-4's B slot). It is the only shared cell between the 8 tuning starts and the four H6 starts (my test `test_finding_midterm_tuning_start_equals_a_candidate_h6_4_cell`). It is also the A start of `LOWER_TUNING_STARTS[0]` in `tests/test_versus_baseline.py`. **Finding for T08 (not decided here): either H6-4 changes, or the midterm start `(1,2,3,+1)` leaves `TUNING_STARTS`.** The new starts avoid every H6 cell.

**Per-update evaluation and `final_check` (assessment).**
- The per-update evaluation draws `_combo(k)` for `k < eval_episodes` (default 8), so it covers only start pairs 0 and 1 (the midterm two). Reproduced: `{train._combo(k)[0] for k in range(8)} == set(TUNING_STARTS[:2])`.
- **`final_check` is not limited to the first 8.** It loops `for i in range(len(env.COMBOS))`, which is 32 combinations, so all 8 starts are checked, 4 seeds each (128 pure-Python duels with the default). The tech lead's report and `RL_POLICY.md` lines 124-125 say otherwise; that is a documentation error that understates coverage (N2). Consequence for cost: `final_check` is about 128 duels, not 32; the Evaluation Specialist should budget for it.
- Assessment: the in-loop win-rate curve measures progress on 2 of 8 start pairs, all of them on rooms 1-3. The 3 lower-room pairs are trained on but invisible to the per-update numbers. This is a blind spot in the monitoring, not a correctness failure, and the end-of-run check does cover all 8. It matters for T08: a regression in lower rooms would not show until the end. Suggest (not required) `eval_episodes` of 32, or rotating the eval combos, at roughly 4x the in-loop evaluation cost.

**Stop-on-first-policy-error (proposal awaiting Saad).** Works as described. Subprocess run with an encoder that raises: exit status 2, `TRAINING STOPPED: ...` on stderr, no `weights.json`, `summary.json` written with `stopped: policy_error` and `weights_sha256: null`, `log.jsonl` has the stopping row. `fail_on_policy_error=False` is the diagnosis switch (see M1). Behaviour of note: the training run stops at the first update in which any episode reports an error, and that update is not trained on. Errors in the baseline opponent are not counted (not a `PolicyMacro`); learner runner fallbacks stay in `fallbacks`, a separate field. I did not find a path where an encoder error in the learner is silent.

## Findings
- **M1 (minor, reproduced, xfail strict `T07-fix1-QA-1`)** `tools/rl/train.py:88` (`_batch`) — with `fail_on_policy_error=False` and every episode empty (every decision errors), `np.concatenate([])` raises `ValueError`. Repro: `uv run --frozen --extra play --extra train pytest -q tests/test_gate_T07fix1_qa.py::test_fail_on_policy_error_false_keeps_running_but_still_counts` (xfail). Expected: diagnosis mode keeps running and counts errors; actual: crashes. Only the non-default diagnosis switch; no impact on the real run.
- **N1 (note, for T08)** The midterm start `(1,2,3,+1)` equals H6-4's B cell in candidate H6 @ 25e4587. Either H6 changes or the start goes. Not decided here.
- **N2 (note, documentation)** `docs/final/RL_POLICY.md:124-125` says `final_check` "does the same" (covers only the two midterm starts). In the code it covers all 32 combinations. Also `tools/rl/env.py:46` comment says "8 (start pair, ...)" for `COMBOS`, which has 32 entries.
- **N3 (note)** In-loop evaluation covers 2 of 8 start pairs (see above).
- **N4 (note)** The disjointness test copies the H6 cells as facts; if T08 freezes a different H6, the test still passes against stale data. The doc says so; T08 must re-check.
- Unverified: whether `--workers 2` (fork pool) propagates a worker-side counted error identically; the counts travel in the returned episode dict, so I expect yes, but I only ran `workers=1`.

## Not checked
No full training run (brief item 7). No browser, no live call. Balance or difficulty of the six starts, and whether the starts are reachable by the baseline in a useful way, are left to Gate 2. The 8-versus-32 combination cost of `final_check` was read from the code, not timed. Rules reviewer checklist not applied: no rule, observation or player-interface change in this diff (the controller gained attributes `policy_macro` and `policy_errors`, which are runner-side, not seat-visible).

## Known limitations
My CLI tests start fresh subprocesses and take about 1 s in total at 200 frames.

## Unresolved findings
M1 (minor), N1 to N4.

## Requested next action
Commit to review: bc3480e on gate/T07-fix1-qa (report one commit above).
What changed: added `tests/test_gate_T07fix1_qa.py`; no production file touched.
How to check it: `uv run --frozen --extra play --extra train pytest -q tests/test_gate_T07fix1_qa.py`
What I am unsure about: multi-worker error propagation; coverage choice for in-loop evaluation.
Touches the knowledge boundary or AI seat: yes (training starts and AI-seat error accounting); Gate 2 applies.

## Student decision required
None from QA. The proposed stop-on-first-error rule still awaits Saad; it behaves as described.

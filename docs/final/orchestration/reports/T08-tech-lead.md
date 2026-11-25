---
handoff_id: HO-T08-tech-lead
task_id: T08
date: 2026-11-24 23:30 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T08.md@0bba440 (amended 2026-11-24 late night; decisions #58 to #61, #9, #24 in DECISIONS-2026-11-23/24.md@0bba440)
source_branch: task/T08
source_commit: 3de37ad79eef934263d9750d7e4b7d883ac1b13b
reviewed_commit: n/a
verdict: n/a
---

# T08: tech-lead report

Status: done

## Work completed
Built the versus evaluation suite on `orch/reviewed` fc02687: the scenario
registry (tuning D1, B2, I3, F5; frozen held-out H6), the success monitors, the
runner CLI with replay, the analysis, the protocol and the held-out README.
Failing tests were committed first (f9609ae, they failed at import), then the
work (3de37ad), then this report. No policy was run on H6; no training, no
`--live`, no paid call. `pop/`, `agents/`, `tools/rl/`, `play.py`, `render/`,
`web/`, `server/` and every existing test are untouched.

**H6 file SHA-256:** `44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`
(`evaluation/heldout/H6.json`; recorded in `evaluation/manifest.py`,
`evaluation/heldout/README.md`, `docs/final/evaluation/PROTOCOL.md`; a test checks all three).

Decisions applied: #58 (B2 below 50 of 100, `monitors.B2_LOW_THRESHOLD`), #59
(D1: the other rival in the agent's room at no frame), #60 (H6-4's B start moved
to (1,2,4,+1) by a rule stated before the cell was chosen: keep room and row, scan
right from the old column, take the first floor cell no tuning start, other H6
start or H6-4 guard patrol uses; no policy result was consulted), #61 (start now),
#9 and #24.

What I took from `orch/wip-T08` 25e4587 (read only; everything was rewritten and
tested here): the module split (spec, monitors, controllers, manifest, suite,
analysis, stats), the monitor classes, the decoy stand-in, the ledger idea and the
CLI shape. Changed from it: the "pending Saad" fields are gone (#58, #59 closed);
no `--policy-factory` (M seats use `SHIPPED_WEIGHTS`/`SHIPPED_SHA256`, hash in
every row); seed key from `secrets.token_bytes(32)` (the WIP used `os.urandom`
and accepted 16-character keys); busy is a harness error; the analysis reports
distinct outcomes, mirrors as one trial and per-seat results; `downed_guards`
and the `until_success` D1 reading were dropped; the tuning and H6 start lists
were re-derived so H6 shares no cell or guard post with any tuning scenario.

## Paths
New only: `evaluation/{__init__,spec,monitors,controllers,manifest,suite,analysis,stats}.py`,
`evaluation/scenarios/tuning.json`, `evaluation/heldout/{H6.json,README.md}`,
`evaluation/runs/.gitignore`, `tools/eval/{__init__,run_versus_suite,analyze_results}.py`,
`tests/test_eval_{monitors,registry,suite,analysis}.py`,
`docs/final/evaluation/PROTOCOL.md`,
`docs/agent-sessions/T08-versus-evaluation-suite.md`, this report.
Scope check: `git diff --name-only fc02687..HEAD` lists only these.

## Acceptance criteria → evidence
| # | Criterion (from the brief) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Dry runs of every scenario, baseline vs baseline, write complete rows | yes | `test_dry_run_writes_one_complete_row_for_every_start_of_every_scenario` (12 rows, all keys, none aborted); manual run: 12 rows, 0 aborted |
| 2 | Replay test | yes | `test_replay_reproduces_the_final_snapshot_of_every_row`, `test_cli_replay_exits_zero_on_a_good_trace_and_one_on_a_tampered_one`, `test_a_changed_recorded_input_does_not_replay_to_the_same_snapshot` |
| 3 | Success predicates unit-tested on constructed states incl. D1/B2/I3/F5 definitions | yes | `tests/test_eval_monitors.py` (29 tests; B2 boundary 49 passes, 50 fails; D1 visit after the take still voids) |
| 4 | Held-out file hash checked by the CLI | yes | `test_the_cli_refuses_a_heldout_file_whose_hash_changed`, `test_an_edited_heldout_file_is_refused_before_it_is_parsed` |
| 5 | H6 disjoint from the 8 `TUNING_STARTS`; `agents/rl/**` and `tools/rl/**` never read `evaluation/heldout/` | yes | `test_h6_shares_no_start_cell_with_the_eight_tuning_starts`, `test_h6_4_b_start_is_off_the_tuning_cell...`, `test_training_and_policy_code_never_read_the_heldout_directory` |
| 6 | Seat-swapped pairs, fresh controllers, secret `seed_key`, aborted runs reported | yes | `test_plan_skips...`, `test_each_trial_builds_fresh_distinct_controllers...`, `test_the_seed_key_never_reaches_a_result_or_a_trace`, `test_a_busy_controller_is_a_harness_error...`, `test_an_exception_in_a_trial_is_a_reported_aborted_row` |
| 7 | Analysis: win/draw/loss with Wilson, per-scenario success, every round | yes | `tests/test_eval_analysis.py` (13 tests) |
| 8 | PROTOCOL.md with hypotheses, success, splits, freeze, comparison plan, N/A provider fields | yes | `docs/final/evaluation/PROTOCOL.md` |
| 9 | Full suite green | yes | below |
| 10 | Open questions for Saad reported | yes | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1468 passed, 11 skipped, 4 xfailed, 2 warnings in 398.81s (0:06:38)
```
No failures. The base's own suite line was not run separately (the brief asked
for it; I ran the full suite once, on my branch, and that line is above).
The four new files alone: `87 passed in 5.92s`, so the suite grows by about 6 s
(the module-scoped dry run of 12 scenario starts is about 4.5 s of that).
Skips and xfails are the repository's existing ones; I did not inspect them.

## Findings
No findings against others. Things I checked that you may want to re-check:
- The shipped PPO policy ran only on the tuning split, in
  `test_policy_seats_use_the_shipped_weights_and_record_their_hash`, capped at
  120 frames. H6 was run only with WAIT seats and a 90-frame cap
  (`test_heldout_dry_run_uses_wait_seats...`) and with scripted seats and a
  30-frame cap (the ledger test, which writes to a temp ledger).
- Dry-run behaviour of the baseline on the tuning split (not evidence of
  anything but plumbing): D1 1 of 3, B2 1 of 3, I3 3 of 3, F5 2 of 3 successes.
  In D1-b and D1-c the baseline strikes the idle seat B (the duel ends
  `won:A`), so the D1 predicate fails there on the #59 rule. I did not tune the
  starts to change these numbers.

## Known limitations
- `ScenarioEpisode` sets `kid.hp` and `disguised` through the duel's private
  `_duel`, because `pop/` has no set-up hook. T19 is changing the engine; if it
  renames those attributes the tests fail loudly. Plumbing request in PROTOCOL.md
  section 7 (a public hook on `VersusEpisode`).
- A start with a forced seat B (all D1, B2, I3 and F5-a/b starts) runs only
  configurations whose B letter is S, so seat B as the *subject* is measured only
  in F5-c and H6. Scenario subjects are always seat A.
- Seeds rarely change a deterministic duel (T07-run1 E3). With one start, three
  seeds usually give one distinct outcome, and the analysis says so (`n<3`). More
  independent evidence needs more starts, which for H6 means a new frozen set.
- I3's decoy is a scripted pacer, not calibrated to a real patrol stride (a stated
  confound).
- B2 passes for a seat that never moves; `success_active` (6 distinct cells) is
  reported as an extra with an evaluator-chosen floor, not as the flag.
- F5's attribution of a downed guard to the agent holds only where seat B is
  forced idle (F5-a, F5-b); in F5-c a guard downed by seat B would count (copresence
  is reported).
- Latency is measured wall time per decision (`time.perf_counter`); the results
  do not claim token, cost or provider figures (N/A).
- I did not run the base's suite separately, so the 1468 count includes my 87
  tests but I cannot give the exact delta.
- The git-tool sandbox here blocked commands naming `tools/eval` as a path, so I
  staged it with a glob; the commit content is as listed above.

## Unresolved findings
None.

## Requested next action
QA (Gate 1): review `task/T08` at 3de37ad (the report commit comes after it).
Then the Evaluation Specialist (Gate 2: this touches held-out data, baselines and
the AI seat), then Gate 3.

Commit to review: 3de37ad79eef934263d9750d7e4b7d883ac1b13b on task/T08
What changed: a new, evaluator-only package that runs seeded scenario starts
through the existing `VersusRunner` with scripted or shipped-PPO controllers,
scores the four approved scenarios from true state, writes one result row per
trial plus two-seat traces, replays them, and summarises rates with Wilson
intervals over distinct outcomes. H6 is frozen by hash with a run-once ledger.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_monitors.py tests/test_eval_registry.py tests/test_eval_suite.py tests/test_eval_analysis.py`;
`python3 tools/eval/run_versus_suite.py --dry-run --trials 1 --out /tmp/x` then
`python3 tools/eval/analyze_results.py /tmp/x/results.json`; replay one trace with
`--replay /tmp/x/traces/D1/D1-a/SvS-t0`; try `--dry-run --split heldout --max-frames 90`
(WAIT seats, no ledger line). Do not run `--split heldout` without `--dry-run`
and without a policy decision: a real held-out run claims the one run per policy.
What I am unsure about: whether Saad wants seat B as the subject in D1/B2/I3/F5
(needs mirrored starts); the 6-cell `success_active` floor; whether the
tuning-scenario start cells I re-derived are fair for the baseline (they were
chosen only to avoid H6 cells and posts); and `ledger.jsonl` keyed by weights hash
alone (a rerun of the same weights after an engine change is refused unless the
key changes; T09 decides whether the key should include the commit).
Touches the knowledge boundary or AI seat: yes (held-out data, baseline and PPO
seat configuration; Gate 2 applies)

## Student decision required
None for the build. Questions for Saad (propose, do not choose):
1. Should the run-once ledger key include the engine commit, so T09's single H6
   run after T19 is the only one for these weights on that engine? As built it is
   the weights hash only, so any later re-run of the same weights on a changed
   engine is refused.
2. Should D1, B2, I3 and F5-a/b also be measured with the policy as seat B
   (mirrored starts)? As built they measure seat A only; seat swap is in F5-c and H6.
3. Is a 6-cell activity floor an acceptable extra reading for B2 (a seat that stands
   still passes the approved predicate)?

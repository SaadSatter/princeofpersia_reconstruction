---
handoff_id: HO-T04-fix3-eval
task_id: T04-fix3
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T04-fix3-qa.md@ab7fcba (which consumed T04-fix3-tech-lead.md@6830232); brief docs/final/orchestration/tasks/T04-fix3.md@fccabb5
source_branch: gate/T04-fix3-eval
source_commit: ab7fcba (base; this branch adds tests/test_gate_t04fix3_eval_probes.py and this report)
reviewed_commit: 60ef7d54a478143b54b26ddd6335e9a26278bab8
verdict: ACCEPT WITH NOTES
---

# T04-fix3: evaluation specialist report (Gate 2)

Status: done

## Work completed
Read the diff 7fe2e9c..ab7fcba (`pop/versus_runner.py`, VERSUS_RUNNER.md, tests), the QA report, and the brief with its decision #33 amendment. Probed seat isolation (ValueError, `busy`), the keyed seed, the shared-controller effect in both modes, and stress-ran the timing-based probes under load. No training run, no paid call, no held-out file touched (the change is runner-only).

## Paths
Added `tests/test_gate_t04fix3_eval_probes.py` (10 test cases, all pass) and this report. No production code, existing test or evaluation scenario edited.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | One controller in both seats refused with ValueError (QA-5, #24, #33) | yes | `__init__` identity check; message is fixed text and names no hidden fact (`test_the_shared_controller_value_error_names_no_hidden_fact`) |
| 2 | `seed_key` opt-in; evaluation must pass one; keyed seed unrecoverable | yes | existing keyed/unkeyed tests pass; my probe shows the key is absent from the result JSON, seeds differ per seat and per key, and 5000 enumerated episode seeds x 2 seats do not match the keyed seed |
| 3 | No controller ever called concurrently; `busy` fallback | yes | `max_active == 1` in both threaded modes with an event-forced overlap (my Gate controller) |
| 4 | Seat isolation survives the change | yes | see Leak findings |
| 5 | Full suite | yes | below |

## Tests run
```
uv run --with numpy python -m pytest -q
863 passed, 12 skipped, 1 xfailed in 23.76s
```
Note: `uv run --with numpy pytest -q` does not make numpy visible to pytest (it still gave the 2 known numpy failures); `uv run --with numpy python -m pytest` does. Without numpy the result is 2 failed (the two `test_numpy_str_answer*` tests, T15) and 851 passed. The one xfail is the pre-existing GATE-T01-QA2 residual, unrelated.

Load stress (my script, scratchpad, not committed): the concurrency, busy, late, timeout, reset and recover tests of the runner, both w2 probe files, t04fix1 eval probes and both T04-fix3 probe files (43 tests per run), run as whole-process pytest runs in parallel with CPU burners on a 10-core machine: 60 runs (8 parallel, 16 burners) and 100 runs (14 parallel, 40 burners). 160 of 160 passed. Before that, 3 of ~40 runs failed, all my own new probe (see "Own probe flake" below), none of the older ones.

## Leak findings
none found. Probed:
- **`busy` fallback and the other seat.** While runner 1 holds a shared controller inside `decide`, runner 2 (same controller in seat A) gets `busy`. The controller is never entered a second time; none of its observations or legal lists contain "busy" or the error text; seat B's trace in the busy run equals seat B's trace in a run where seat A just waits (ignoring latency); the final snapshot hash is equal; seat B's busy count is 0. `busy` is a harness-side label in the result and trace, never passed to a controller (`test_busy_fallback_reveals_nothing_...`).
- **ValueError.** Fixed text, raised in `__init__`, before any observation exists.
- **`seed_key`.** Not present in result or traces (str or hex form); per-seat seeds differ; not recoverable by enumeration with a proper key.
- Not re-probed: observation contents (unchanged by this diff; QA confirmed no field added).

Findings (reproduced, both minor, neither blocks):
1. [minor] `pop/seats.py` `controller_seed`: `bytes(key)` accepts an int and the empty key. `seed_key=5` becomes five NUL bytes and `seed_key=b""` is a valid HMAC key, and in both cases the seed is recoverable by enumeration (`test_finding_degenerate_seed_keys_are_accepted_silently`). A harness that passes such a value believes the run is keyed. Request for the Tech Lead: reject non-bytes and keys under 16 bytes, or have T08 generate the key with `secrets.token_bytes(32)` and say so in its brief.
2. [minor, design limit] The ValueError tests object identity only. Two different instances sharing a mutable (a module global, a shared list or file) are still a seat channel (`test_finding_two_instances_sharing_state_are_not_detected`). This cannot be fixed in the runner. It belongs in the evaluation rules (below).

## Judgement on the facts in the prompt
**QA's one unexplained failure.** I could not reproduce it: 160 of 160 under heavy parallel load (see above), on top of QA's 155. The change itself is event-based and was not the cause of any failure I saw. The older probes are timing-based by construction and have thin margins that a loaded machine can break: `test_busy_clears_after_the_call_returns...` and `test_busy_registry_is_not_left...` rely on `sleep(0.3)` outliving a 0.1 s or 0.05 s late call; `test_busy_recovers_after_late_call_returns` and `test_busy_state_is_shared_across_runner_instances` rely on the run being long or short compared with a 0.12 s or 0.3 s call; and several use `timeout_s` of 0.02 to 0.03 s with a thread that must overrun it. So yes, a timing probe can flake under load, in principle, and a parallel harness is the case that would show it. I cannot name which one failed, and I do not claim any did. A 60-run failure rate of 1 (about 1.7 percent per run of the whole set, so under 0.05 percent per test) is consistent with a thin-margin test, a collision between QA's two loops (both write `__pycache__`, pytest tmp dirs) or something else. Recommendation, for the Tech Lead only if it recurs: replace the sleeps with events, as the new overlap test does. The evaluation itself does not use these tests, so a flake here cannot change a result. A **real** evaluation does depend on the same wall-clock effect, and it is already documented: a trace that contains a real timeout or `busy` is not reproducible (VERSUS_RUNNER.md, "What this means for evaluation").

**Shared controller across worker threads (T08).** Confirmed for both `threaded=True` and `threaded=False`: the second worker gets `busy`, counted in `busy` and `fallbacks` (`test_a_controller_shared_across_worker_threads_...`); one controller per worker never sees `busy` (`test_one_controller_per_worker_...`). Yes, the evaluation rules need a note. Decision #24 aborts a run over its fallback limit and always reports it, so a harness with a shared controller would fill the report with `aborted` runs that look like policy failures but are harness misuse. The rule I propose for the T08 brief and for `docs/final/evaluation/` (not edited by me, since the success criteria are not mine; it is a wording request): "Build a fresh controller for each worker and each seat (the policy and the scripted baseline too). A `busy` fallback in an evaluation run is a harness error, not a policy result: report it as such, with the run, and do not count it as a policy fallback. Never share one controller, or one piece of mutable state, between workers or seats." The inability of the runner to tell harness-caused `busy` from a real late call (both are `busy`) means the harness should assert `busy == 0 and timeouts == 0` per seat in evaluation and list any other run as aborted.

**Seat isolation.** Holds (Leak findings above).

## Own probe flake (disclosed)
My first version of the isolation probe compared whole seat-B traces, which include `latency_ms`, so it failed in 3 of the first ~40 loaded runs. I removed `latency_ms` from the comparison, a test fix, and it then passed 160 of 160. It was never a runner behaviour.

## PPO and evaluation checks (scope)
This task changes only the runner's concurrency bookkeeping and the QA-5 and eval-1 items. Nothing in `agents/rl/`, the encoder, the baseline, reward, training, scenarios or held-out set changes, and none were re-reviewed here.
Baseline fairness: not in scope (unchanged).
Reward and training method: not in scope (unchanged).
Checkpoint reproducibility: not in scope (unchanged).
Train / held-out separation: not in scope; I did not read, run or tune against `evaluation/heldout/`.
Evaluation validity and confounds: the change helps: evaluation runs must pass `seed_key` (#24), and the two-seat ValueError removes a seat channel. Confounds that stay: a run with a real timeout or `busy` cannot be reproduced; `seed_key` strength depends on the caller (finding 1).
Local inference performance: not measured (no inference path touched).
Replay and fallback: the `busy` fallback is still labelled `"source": "fallback"`, `"fallback_reason": "busy"`, counted per seat; replay of a busy trace stays exact (existing test `test_busy_trace_is_wallclock_dependent_but_replay_is_exact` passes). A run over its fallback limit is `aborted` and reported as before.
Training-run readiness: not affected by this task (no training path touched). Separate approval and the T08 harness are still needed.

## Known limitations
- Real-timeout and `busy` traces are not reproducible (documented, unchanged).
- Identity-only check for the two seats (finding 2).
- I could not reproduce QA's flake and cannot say which test it was.

## Unresolved findings
Finding 1 and 2 above (minor). Neither blocks closing T04-fix3.

## Requested next action
Orchestrator, Gate 3, on 60ef7d5 / 6830232, with my probes from this branch. Carry two notes into the T08 brief: (a) one fresh controller per worker and seat, and treat any `busy` or timeout in an evaluation run as a harness error that aborts and is reported; (b) generate the `seed_key` with `secrets.token_bytes(32)`. Tech Lead (optional, a later fix): validate `seed_key` in `controller_seed` or the runner (bytes, at least 16).

## Student decision required
none

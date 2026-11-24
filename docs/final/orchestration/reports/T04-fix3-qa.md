---
handoff_id: HO-T04-fix3-qa
task_id: T04-fix3
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T04-fix3-tech-lead.md@6830232
source_branch: gate/T04-fix3-qa
source_commit: see the branch head (tests and this report)
reviewed_commit: 60ef7d54a478143b54b26ddd6335e9a26278bab8 (checked out as 6830232, which adds only the report)
verdict: ACCEPT WITH NOTES
---

# T04-fix3: QA report (Gate 1)

Status: done

## Work completed
Checked out 6830232 on `gate/T04-fix3-qa`. Read the diff against 7fe2e9c, re-ran the suite, re-ran the concurrency and busy tests many times, ran the new overlap test against the 7fe2e9c runner (reverted `pop/versus_runner.py` only, then restored it), checked the session-note bullet against wave2-batch.md, searched for consumers of the runner, and added a small probe file.

## Paths
Added `tests/test_gate_t04fix3_qa_probes.py` (5 tests, all pass). Production code and existing tests untouched. Scope of the reviewed change (`git diff --name-only cd5c4aa 6830232`): the four gate files plus `tests/test_gate_t04fix1_eval_probes.py` (decision #33), `tests/test_versus_runner.py`, `pop/versus_runner.py`, VERSUS_RUNNER.md, two session notes and the tech-lead report. All inside the brief's permitted paths after the #33 amendment.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | QA-5: same controller in both seats raises ValueError, xfail removed | yes | `versus_runner.py` `__init__` checks `controllers["A"] is controllers["B"]`; `test_qa5_one_instance_cannot_play_both_seats` passes; fails on 7fe2e9c runner |
| 1b | Decision #33 flip | yes | `test_same_instance_in_both_seats_is_refused` passes (fails on the 7fe2e9c runner); only that test changed in the file |
| 2 | Eval-1: seed_key opt-in, doc says evaluation runs must pass one, keyed test passes, unkeyed documented | yes | tests in `test_gate_t04_eval_boundary.py` pass; doc diff present; no code change needed |
| 3 | In-flight mark at call start under the registry lock; concurrent runners never call one controller together; busy fallback; both w2 xfails removed | yes | `_claim` checks and marks under one `_LATE_LOCK` hold; with the 7fe2e9c runner these fail: the new overlap test, GATE-w2-QA-1 (`..._started_concurrently`), GATE-w2-eval-1 (`..._at_the_same_time_in_threads`); all pass on the reviewed code |
| 3b | New test deterministic (events, no sleeps), repeated >= 50 | yes with a note | see "Repeat runs" |
| 4 | Session wording "R-V26, QA3 and L2" | yes | wave2-batch.md line 7 asks for exactly this wording. The base had no sentence to correct, so the bullet is new, but it is accurate: R-V26, QA3 and L2 are the three changes that move traces or the hash, and the "before T01-fix1" framing matches wave2-batch.md ("Eval differential 83127cf to cd5c4aa: changes explained by R-V26 and QA3", "L2 also changes the hash"). Minor: it does not mention QA1, which wave2-batch.md lists as a fixed finding but not as a hash cause. Not a defect |
| 5 | Full suite green, Handoff block | yes except known numpy | below |

## Tests run
```
uv run pytest -q   (at 6830232)
2 failed, 846 passed, 12 skipped, 1 xfailed in 22.81s
```
Failures: `test_numpy_str_answer_still_works` and `test_numpy_str_answers_still_work`, both `ModuleNotFoundError: numpy` (`uv run python -c "import numpy"` fails). Not counted (T15, #34). Verified at 7fe2e9c: the w2 numpy test fails there too (the run of five files at 7fe2e9c showed it). The t04fix1 one is not in that run, but it is the same bare `import numpy`, so I treat it as the same cause.

With my probe file added: `tests/test_gate_t04fix3_qa_probes.py` 5 passed.

Revert experiment (runner at 7fe2e9c, tests at 6830232), five relevant files: `6 failed, 205 passed`. The six: the new overlap test, GATE-w2-QA-1, GATE-w2-eval-1, QA-5, the #33 test, plus the numpy one. So each fix is covered by a test that fails without it.

### Repeat runs
Set: `tests/test_versus_runner.py`, both w2 probe files and `test_gate_t04fix1_eval_probes.py`, selected by `-k "busy or concurrent or late or same_instance"` (the concurrency and busy tests, a superset of the tech-lead's 7).
- Sequential: 60 runs, 59 passed, 1 failed. The failing run overlapped in time with a second copy of my loop that I had started and then killed, and I did not capture its output, so the cause is not known.
- Sequential again, nothing else running: 55 of 55 passed.
- Four loops in parallel (heavy load), 25 runs each: 100 of 100 passed.
Total on the reviewed code: 214 of 215 passed, with one undiagnosed failure under unintended load. I could not reproduce it in 155 further runs, 100 of them under deliberate load. Recorded as an unverified concern (below), not a reproduced finding.

## Findings
Reproduced: none.

Unverified concerns:
- [minor, unverified] One failure in 60 sequential runs of the concurrency/busy set (see Repeat runs), not reproduced in 155 runs. Some of the w2 tests (`Slow(0.25)`, `time.sleep(0.3)`, timeouts of 0.02 s) are timing-based; the new overlap test is event-based. If this recurs, look at those older probes first. Not a defect of the change.

## Judgement on the flagged side effect (inline mode now gets `busy`)
Correct, with a caveat. The mark is set for every call, so two threads that share a controller in `threaded=False` mode now get a `busy` fallback for the second caller instead of a concurrent call. That is the same guarantee as threaded mode and the decision's intent: no controller is ever entered twice at once. Nothing in the repository relies on the old behaviour: `VersusRunner` is imported only by `pop/seats.py` (docs/strings) and tests; there is no evaluation harness (T08), web bridge, or baseline sweep using it yet (`grep` over non-test `*.py` files). Caveat for the Evaluation Specialist and for T08/T13: a harness that runs several workers in threads with one shared controller object, expecting them to serialise by luck, will now see `busy` fallbacks, which count against that controller's stats (`busy`, `fallbacks`). Such a harness must build one controller per worker (the fix already forces separate instances per seat). Sequential reuse across runners is unaffected (new probe `test_sequential_reuse_of_one_controller_across_runners_is_never_busy`).

Other checks, all clean: the claim is released after a controller raises, in both modes, and after normal runs (the registry is empty afterwards; probes added); the late-thread path still keeps the id marked until the thread dies (existing busy tests). `_claim` replaces a dead late thread entry correctly. Reading the diff I found no way for the sentinel to leak, since `_call` releases it in a `finally`.

## Known limitations
Real-timeout traces remain non-reproducible (documented, unchanged).

## Not checked
No browser build or Playwright (the change is runner-only). No CI file review beyond confirming the diff touches neither `.github/workflows/` nor `ci/`. Hidden-state leak review: the change adds no field to observations, results or traces, so I did not re-run the hidden-fact probes beyond the existing suite passing; Gate 2 owns that. Did not run the t04fix1 numpy test at 7fe2e9c separately.

## Student decision required
none

## Requested next action
Gate 2 (evaluation-specialist) on 60ef7d5 / 6830232, plus my probe file. Then Gate 3.

---
handoff_id: HO-T05-fix1-evaluation-specialist
task_id: T05-fix1
date: 2026-11-24 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T05-fix1-qa.md@12c11bd (which consumed T05-fix1-tech-lead.md@161a841); brief docs/final/orchestration/tasks/T05-fix1.md@38aca15; earlier findings reports/GATE-T05-eval.md@38aca15
source_branch: gate/T05-fix1-eval
source_commit: 12c11bd (base; the commit holding my probes is the head of gate/T05-fix1-eval)
reviewed_commit: ce8c8c07f1d77e2f800f331f6716b1fed5862f25
verdict: ACCEPT WITH NOTES
---

# T05-fix1: evaluation-specialist report (Gate 2)

Status: done

## Work completed
Read the QA and tech-lead reports, then read `agents/versus_baseline.py` in full and the diff of `agents/macros.py` for every observation input. Ran a key-access boundary probe over full duels, a larger swap-balanced sweep (my own sampler, fresh seeds), a threshold-sensitivity sweep for the rule-5 constants, and the mirror match per seat. No training run, no paid call, no code outside my permitted paths changed. Only the baseline and macro layer changed in this task: there is no `agents/rl/` or `tools/rl/` on this base, so PPO-specific checks (checkpoint, reward, latency, training separation) are out of scope and listed as "not applicable here".

## Paths
- `tests/test_gate_t05_fix1_eval_probes.py` (new, 2 tests, pass)
- this report
- Scratch scripts (not committed): sampler and sensitivity scripts in the session scratchpad, quoted below with seeds so they can be rerun.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Every baseline input is something a human seat could see | yes | key-access probe and line reading, see Leak findings |
| 2 | Memory asymmetry with PPO disclosed in MACROS.md | yes | `docs/final/MACROS.md` "What the baseline remembers" lists each kept item and lifetime, and says the PPO rival keeps none unless its encoder is given it |
| 3 | N1 judged | yes, see Findings | |
| 4 | N2 judged with a larger swap-balanced sweep | yes, no seat effect | 1,040 duels below |
| 5 | Held-out claims judged | yes, partly invalid | see Train / held-out separation |

## Leak findings
none found. Probed:
- `tests/test_gate_t05_fix1_eval_probes.py::..reads_only_visible_fields_over_full_duels`: key-logging wrapper around the observation, full 3,600-frame duels from the default start, baseline in each seat, seeds 0 to 2, against WAIT. Top-level keys read are inside `room, edges, tiles, state, kid, me, figures, suspicion, last_result`; figure keys inside `kind,row,col,facing,posture,stance,armed,motion`. It never reads `minutes_left`, `swords`, `task`, `actions_left`, seed or episode. A source scan shows the only use of `last_result` in `agents/` (excluding the legacy model player) is `.get("effect")`, and R-V26 gives `no_uniform` to the acting seat only. In these duels the `last_result` branch is not reached (duels end quickly); that branch is covered by the source scan, not by the runtime log.
- The T05 boundary probe (`test_gate_t05_eval_baseline_reads_only_this_seats_visible_fields`) still passes.
- `FigureTracker` and the guard/rival split read `kind`, a label the observation gives every seat (a disguised rival is labelled `guard`, R-V18), so it cannot tell a disguised rival from a guard except by behaviour (the tells in the module docstring), which a human can also see.
- Planning through unseen pits: `FieldView._fall_from` treats a pit in the bottom row as `leave_down` and assumes a floor at the top of the room below ("blind cost"). This is a guess, not a read of hidden state: the observation shows nothing below, and the code never looks at the layout of other rooms. It does encode prior knowledge of the arena (that a bottom-row pit leads to a room with floor under it). In the shipped arena no bottom-row pit exists in rooms 4 to 6 (which have no room below), so the guess is never wrong there, but it would be wrong in a layout where a pit opens onto another pit. A human seat sees the same screen and would learn it the same way, so this is not a leak. Disclose it as prior knowledge in MACROS.md (see Findings F-E3).
- Memory (`SEARCH` visited-room table, danger memory, tried shaft columns) keys on the room label the observation gives the seat. Own history only.

## Baseline fairness
- Same observation, legal list and macro vocabulary as the PPO rival (#23). Competent: it reaches rooms 4 and 5, takes a uniform, finds a WAIT rival in rooms 4 to 6 and avoids a lone guard, measured below.
- Asymmetry: the baseline has memory (tracks, rooms visited, fled-from rooms with 120-decision lifetime, shaft columns tried, stripped bodies, failed macros) and a hand-written planner (`RoomView` search with the engine's fall rules). The PPO rival has neither unless its encoder adds it. This is disclosed in MACROS.md, as required. The comparison is therefore "PPO vs a scripted player with memory and a planner", not like for like; reports must say so.
- The baseline also uses the published fall rule (one row safe, two cost a heart, three kill) and the R-V14 sight range 5 as constants. Both are published rules a player learns. The PPO rival must learn them from reward.

## Reward and training method
Not applicable here: no PPO code on this base.

## Checkpoint reproducibility
Not applicable here.

## Train / held-out separation
- The baseline is scripted, so "training" means the author tuning constants and rules. Brief and tech lead agree: rule-5 thresholds (`ENGAGED 2`, `DANGER_RANGE 3`, `WAIT_FOR_BACK 40`, danger memory 120) were set while looking at failing duels. At `0846a16` the failing tests included the new competence tests, so I treat `LOWER_HELD_OUT_STARTS` as contaminated for threshold tuning, even though the start list itself is unchanged (checked: no start list changed between 0846a16 and ce8c8c0). Their 28/28 and 27/28 are therefore not unseen evidence.
- The old top-row `HELD_OUT_STARTS` (16/16, 16/16) is unseen for the new rule, but the top row has no guard and no descent, so it is a weak test of rule 5.
- Replacement unseen evidence: my own samplers with seeds the tech lead and QA did not use (31001, 31002, 41001, 41002, 51001), random start cell and facing in random pairs of arena rooms. These were run once each, after the code was frozen, and I changed nothing in response. The two QA and tech-lead sweeps (seeds 20261124, 99, 7, 5, 77) are of the same family, so the family as a whole is the better "held out" claim: random starts are not the tuning starts.
- The sensitivity sweep (below) shows the result does not rest on a fine-tuned constant except `ENGAGED`.
- Verdict on the claim: "held-out" may be said of the old top-row set and of the random-start samplers; it should not be said of `LOWER_HELD_OUT_STARTS`. Ask the orchestrator to label it "frozen before implementation, not unseen" in MACROS.md Results.

## Evaluation validity and confounds
Baseline vs scripted opponents (WAIT, Random), 3,600-frame duels, fresh controllers, seats alternated, seed = duel index, `VersusRunner`, offline. Wins are by the baseline.

| Sampler seed | Opponent | Duels | Seat A wins | Seat B wins | Losses | Timeouts |
| --- | --- | --- | --- | --- | --- | --- |
| 31001 | WAIT | 120 | 60/60 | 59/60 | 0 | 1 |
| 41001 | WAIT | 400 | 196/200 | 198/200 | 1 | 5 |
| 31002 | Random | 120 | 59/60 | 59/60 | 2 | 0 |
| 41002 | Random | 400 | 192/200 | 192/200 | 16 | 0 |

Total: vs WAIT 513/520 wins (98.7%, 1 loss, 6 timeouts; Wilson 95% about 97.3% to 99.3%); vs Random 502/520 (96.5%, 18 losses; Wilson 95% about 94.5% to 97.8%). Seat A 251/260 and seat B 251/260 against Random; WAIT 256/260 vs 257/260.

- N2 (seat-B effect): none. Win rates are equal by seat at n = 260 per seat per opponent. QA's three losses in seat B were chance at n = 30. Losses and timeouts are reported, not dropped.
- Threshold sensitivity (sweep seed 51001, 100 duels per cell, vs WAIT and vs Random): base 99 and 96 wins; `ENGAGED=3` 99 and 98; `DANGER_RANGE` 2 or 4: 99 or 100 and 96; `WAIT_FOR_BACK` 20 or 80: 99 and 96. Only `ENGAGED=1` degrades (91 and 88). So the competence does not depend on a knife-edge, and `ENGAGED` is the one rule that matters (fleeing from a guard at distance 2 costs hearts).
- The 6 timeouts vs WAIT (one example start (2,2,3,-1) vs (4,2,8,1), seed 111 in sweep 31001) are the shaft-up search or a rival unreachable in 3,600 frames; not diagnosed.
- Mirror match (N1): from the default start, baseline vs baseline is one trace; the seed does not change it; seat B wins every time because seat A resolves first (test `..mirror_match_is_one_trace_decided_by_seat_order`). On random starts QA found 12 A, 11 B, 1 draw (24 duels), so the seat-order effect is specific to the symmetric default start.
  - Acceptable for evaluation? Yes, with conditions. The baseline is never compared with itself in the hypothesis test; it is the opponent for PPO. A deterministic mirror is a degenerate pairing and must not be used as evidence of anything about baseline strength. The brief's requirement (not 10/10 draws) is met.
  - Per-seat reporting: every comparison must report results per seat (A, B), and a mirror result must be reported as "decided by seat order, one trace, n = 1 distinct duel" and counted as 1 trial, not 12. Any PPO-vs-baseline table must show A-seat and B-seat wins separately. I did not add symmetry-breaking, since that would need a seed or identity read, which the brief forbids.
- Confounds to name: random starts sample cells in `_` and `P` tiles of row 2 only; WAIT and Random are weak opponents (no baseline-vs-PPO result exists yet); nearest-figure targeting; the guard patrols are deterministic; the baseline keeps memory and PPO does not; two tuning starts were seen by the author while fixing.
- No scenario of D1, B2, I3, F5, H6 (decision #9) was run; this task does not claim them. Scenario freezing for the comparative evaluation is a later task.

## Local inference performance
Not measured and not applicable here (the baseline has no network or model; there is no PPO policy on this base). Timing for scale only: 400 baseline-vs-WAIT duels took 70 s and 400 vs Random 24 s wall, on the development laptop (measured, includes the engine).

## Replay and fallback
Existing QA probes (replay, identical fresh baselines, 0 fallbacks) pass in the full suite. My runs used `VersusRunner`'s default fallback accounting; QA's report shows 0 baseline fallbacks over 12 duels. I did not count fallbacks in my 1,040 duels (the sampler only read `winner_slot`). The `decide` crash on a `None` or malformed tuple is now a reported failure (tech lead); labelled fallback behaviour is unchanged.

## Training-run readiness
not applicable to this task (no PPO code on this base). Readiness of the baseline as the opponent: ready, subject to the notes below.

## Tests run
```
uv run pytest -q tests/test_gate_t05_fix1_eval_probes.py
2 passed in 2.46s
uv run pytest -q
1 failed, 866 passed, 12 skipped, 4 xfailed in 77.45s (0:01:17)
```
The one failure is `tests/test_gate_t04fix1_qa_probes.py::test_numpy_str_answer_still_works` (`ModuleNotFoundError: numpy`), the same environment failure QA reported at the base. The 4 xfails are other tasks' (QA's strict `QA-F1` plus three older).

## Findings
- [minor, reproduced] **F-E1 (N1):** mirror match is decided by seat order. Accepted with per-seat reporting, as above. No code change requested.
- [note, resolved] **F-E2 (N2):** no seat-B effect, 520 swap-balanced duels per opponent.
- [minor] **F-E3:** MACROS.md should say that the baseline's planner assumes a floor at the top of the room below a bottom-row pit (prior knowledge of the arena, not a hidden read), and that it is wrong for any arena layout that breaks it. Request for the Tech Lead; I did not edit it (not my path).
- [minor] **F-E4:** `LOWER_HELD_OUT_STARTS` is labelled held out but the thresholds were tuned while failing duels were in view. Relabel "frozen before implementation, not unseen". The honest unseen evidence is the random-start samplers above.
- [minor, QA F1, carried] the baseline can lose to a motionless WAIT seat (QA-F1, start A=(5,2,0,-1), B=(6,2,0,1), seed 17, swapped). In my 520 vs-WAIT duels there was 1 loss and 6 timeouts; cause not diagnosed. Not blocking, since WAIT is not an opponent in the hypothesis.
- No blocker, no major.

## Known limitations
- No PPO policy was available, so nothing about the rival was evaluated. The baseline's strength against WAIT and Random does not say it is a good opponent for a trained policy that learns to exploit it.
- One sampler family; start cells are floor tiles in the bottom row only; opponents are WAIT and Random only.
- Fallback count not re-measured by me.

## Unresolved findings
F-E3 and F-E4 (documentation only), the QA-F1 loss, the 6 vs-WAIT timeouts.

## Requested next action
Orchestrator Gate 3 on ce8c8c0 with this report and the QA report. Ask the Tech Lead for a small MACROS.md edit (F-E3, F-E4) and require per-seat reporting for any later comparison that uses the baseline in both seats. Read `docs/final/orchestration/reports/T05-fix1-evaluation-specialist.md` and `tests/test_gate_t05_fix1_eval_probes.py` on `gate/T05-fix1-eval`.

## Student decision required
none

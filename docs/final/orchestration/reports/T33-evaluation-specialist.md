---
handoff_id: HO-T33-eval-evaluation-specialist
task_id: T33-eval
date: 2026-11-27 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T33.md@ab395fc (stage 1); docs/final/orchestration/inputs/G23_PRESENTATION_REQUEST.md@ab395fc (slides 3 and 6)
source_branch: gate/T33-eval
source_commit: ab395fc (base; this report's own commit follows)
reviewed_commit: n/a (a fact check of records at ab395fc; no code under review)
verdict: ACCEPT WITH NOTES
---

# T33-eval: evaluation-specialist fact sheet for slides 3 and 6

Status: done. Report only. No training, no held-out run (H6 was read as a committed result, never re-run), no `--live` call, no code or test edited. Every path below is `path@ab395fc`; the blob of each result file was last changed at the commit named beside it.

Verdict: **ACCEPT WITH NOTES.** Every number in Saad's slide 3 text (16 trials, 13 W, 2 D, 1 L, bar 14, NOT SUPPORTED) matches the record. The notes (N1 to N7 below) are wording limits the deck must respect.

## 1. Slide 3: the T09 held-out result (verified)

I recomputed from the 48 raw rows, not from the prose.

| Item | Value | Source |
| --- | --- | --- |
| Set | H6, 8 starts x 2 seat orders (MvS = PPO seat A, SvM = PPO seat B) = **16 duels**; 3 trials per duel = 48 rows | `evaluation/results/T09/results.json` (48 rows, @874c5e0) |
| PPO result | **13 W, 2 D, 1 L of 16** (seat A 7W 1D 0L; seat B 6W 1D 1L) | `evaluation/results/T09/analysis.txt` "Duels: win / draw / loss"; `docs/final/evaluation/RESULTS-T09.md` (@fbce328) |
| Pre-registered bar | at least **14 of 16** wins and no aborted duel (decision #77) | `docs/final/orchestration/DECISIONS-2026-11-24.md` row 77; `docs/final/evaluation/PROTOCOL.md` |
| Verdict | **NOT SUPPORTED** (13 < 14). Aborted: 0 | `RESULTS-T09.md` line 1; `analysis.txt` "Rows: 48; aborted: 0" |
| Reading of the verdict | "Not supported" means the improvement over the baseline was not shown at this bar. It does not mean the rival is worse. | `RESULTS-T09.md` line 1 |
| Recount from rows | termination counts over 48 rows: 24 `won:A`, 18 `won:B`, 6 `draw:time_up` = 16 cells x 3; each cell's 3 trials agree | my recount of `results.json` |
| Frozen inputs | `evaluation/heldout/H6.json` SHA-256 `d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266` (I re-hashed it: match); `agents/rl/weights/ppo-run-1.json` SHA-256 `80e4a110...ba4c` (re-hashed: match); ledger has one row, status `claimed`, no refusals | `evaluation/heldout/ledger.jsonl`; shell `sha256sum` |
| Run identity | run id `20261125T085558Z`, engine commit `77bc2f7d506d5cb774287065ea2d62501343e72c`, clean tree, one invocation | `results.json` rows; `RESULTS-T09.md` |

**The identical-trials caveat (must be on the slide or in the notes).** The three trials of every duel were identical (one distinct outcome per cell; `analysis.txt` "Distinct outcomes per condition" shows `distinct = 1` in all 16 rows). So "16 trials" is 16 duels, and the effective sample is nearer 8 starts (two seat orders share a layout). Saying "48 trials" would be wrong. The Wilson interval printed (0.57 to 0.93 on the win rate) is optimistic for that reason; if shown, say so, or leave it out.

Other limits to state, each in `RESULTS-T09.md` "Confounds and limits":
- Starts: H6-1 is training-like; H6-3, 6, 7, 8 partly training-like; H6-2, 4, 5 unseen layouts. The claim is "unseen start pairs and guard layouts", not an unseen map.
- Seat order is confounded with start position, so 7W/1D/0L vs 6W/1D/1L is not evidence of a seat effect.
- The three non-wins: H6-1 MvS draw (3600 frames, 3 hearts each), H6-2 SvM draw (PPO 3 hearts, baseline 2), H6-8 SvM loss (baseline won at frame 519, PPO 0 hearts, baseline 1). Causes of the draws were not analysed. Stale inputs do not explain them (none on either seat in those three cells).
- Stale inputs (queued moves no longer legal): PPO seat 21, baseline 18, over the 48 rows. I recomputed both. PROTOCOL H-c ("0 stale on both seats") is not met as written on H6; decision #80 relaxed it for the step-1 health check only. Reported, not hidden.
- Pre-T09 and later engine changes: the T09 run is on 77bc2f7. Later commits on `main` (T22 to T25) changed game modes, kneel-takes-uniform and hang-wins; the T24-fix1 Gate 2 report found macro-rival behaviour bit-identical (0 changed duels in 256 per row on tuning starts), so the T09 evidence stands but was not re-run on today's `main`. Source: `docs/final/orchestration/reports/T24-fix1-evaluation-specialist.md` "Evidence affected?".

Suggested wording (facts only): "Held-out H6: 16 duels, PPO 13 wins, 2 draws, 1 loss. Bar set in advance: 14 wins. Not supported. The three trials of each duel were identical, so effective n is about 8 starts."

## 2. The tuning-start final check (120/8/0) and how it differs

| | Tuning-start final check | Held-out T09 |
| --- | --- | --- |
| Result | **120 W, 8 D, 0 L of 128** (win rate 0.9375), 0 policy errors | **13 W, 2 D, 1 L of 16** |
| Starts | the 8 tuning starts the policy was trained on (32 start pairs x 4 seeds, seat-swapped) | 8 frozen H6 starts, never used by training |
| What it is | in-distribution smoke check, run by the trainer at the end of training | the one pre-registered comparison, run once |
| Claim allowed | none about strength ("not a strength claim", `RL_POLICY.md`) | NOT SUPPORTED at the bar |
| Independence | the 8 draws are 2 start-pair combos (9 and 11) giving the same stalemate on all 4 seeds each, so 32 distinct scenarios, not 128 | effective n near 8 |
| Source | `tools/rl/runs/run-1/summary.json` (`final_check_vs_baseline_tuning_pure_python`, commit f08c1a8); `docs/final/RL_POLICY.md` "Results" | `RESULTS-T09.md` |

I did not rerun it. The Evaluation report that did rerun it (identical 120/8/0 through the pure-Python path, 11 s) is `docs/final/orchestration/reports/T07-run1-evaluation-specialist.md` section 1. The two numbers must never share one headline ("120 of 128 versus 13 of 16 is the same claim" would be false). Show 120/8/0 only labelled "tuning starts, trained on, not held-out".

Held-out separation (checked here): `tools/rl/` and `agents/rl/` contain no reference to `evaluation/heldout/` or H6 except one comment (`tools/rl/env.py:15`); the committed hash matches the ledger. No checkpoint was chosen by score (`summary.json`: `checkpoint_chosen_by_score: false`; last weights exported).

## 3. Training runtime and compute (all local, $0 in API terms)

| Item | Value | Source |
| --- | --- | --- |
| Where | Saad's Mac, local CPU, 2 worker processes, numpy `train` extra | `tools/rl/runs/run-1/config.json` (`workers: 2`); `RL_POLICY.md` "Results"; decision #51 |
| Wall time | **4812.6 s (80.2 min)**; cap `--seconds 4800`; `stopped: time_cap`, exit 0; 2026-11-24 20:40:05 to 22:00:26 EST | `tools/rl/runs/run-1/summary.json`, `run-1.meta` |
| Amount trained | 1568 updates, 25,088 episodes, 1,487,955 environment steps | `summary.json` |
| Policy | MLP, hidden 64 x 64, 251 input features, 9 macro slots (RIG_TRAP always masked); seed 0 | `config.json`; `RL_POLICY.md` "What the rival sees" |
| Approval | decision #51, "Go, 4,800 s cap" | `DECISIONS-2026-11-24.md` row 51 |
| Training errors | `policy_errors: 0`, `weights_failed: false`, run stopped on the first error by design (#47); none occurred | `summary.json` |
| Hardware detail | "Saad's Mac": no chip or core count is recorded in the run files. Do not state one | `run-1.meta` has none |

Slide wording that is safe: "Trained locally on CPU in about 80 minutes (4,813 s, 1.49 M steps). No API, no GPU recorded, no paid call."

## 4. Paid live-model spend for the PPO line

Confirmed from the records, not assumed:
- **PPO training, evaluation and in-game inference: $0, no provider call.** Every T09 row has `provider: N/A, tokens: N/A, cost_usd: N/A` for the PPO controller and for the scripted baseline (`results.json`, all 48 rows; checked in code). `docs/final/CONFIGURATION.md` lines 26, 43, 83 and `docs/final/GDD.md` line 68 say the PPO rival makes no paid call.
- **Decision #8 smoke budget (under $1, "Try less than $1 for a smoke test") was not spent in the final project.** The final-project records show no `--live` run: no `traces/live` file was added after 2026-10-26 (`git log --since=2026-11-01 -- traces/live`: none), and no post-2026-11-23 report records a live call.
- **Caveat, and a conflict to avoid.** `GDD.md:68` says "No paid run has been made". That is not true of the repository as a whole. The **midterm** left three live traces from 2026-10-26 (before decision #8, and for the legacy LLM model player, not PPO): two real trials (`claude-haiku-4-5-20251001`, S1 seed 0, 4 calls each, 0 failed, both `died:spikes`, 8,970 in / 1,896 out tokens, estimated **$0.0185** in all) and one failed attempt (40 calls, no credential, 0 tokens, $0). Source: `EVALUATION.md` "Live development trials" and "Failed live attempt"; `traces/live/README.md`. These are midterm development trials on the tuning suite, an estimate from token counts, not a final-project spend, and not PPO. If the slide shows a cost line, write: "PPO rival: $0 (local training and inference). Final-project paid LLM calls: none. Decision #8 smoke budget (under $1): unspent. Midterm LLM dev trials (Oct 2026): about $0.02 estimated, not part of this evaluation." Do not write "no paid call has ever been made".

## 5. Policy errors and fallbacks

| Where | Fallbacks | Policy errors | Source |
| --- | --- | --- | --- |
| T09 held-out, 48 rows, both seats | **0** (fallbacks, refused, errors, timeouts, busy all 0 over 14,907 decisions I summed; invalid inputs 0) | **not recorded in these rows** (PPO inference errors are caught inside the controller and answered with WAIT; T08-fix2 records them for later runs; decision #84) | `results.json` per-row `seats`; `RESULTS-T09.md` "The odd rows" |
| Training run 1 | n/a | 0 | `summary.json` |
| Tuning final check | 0 | 0 | `summary.json`; T07-run1 Eval report |
| Playtest XGJT (online, trained rival) | 0 (`fallbacks: []` in the trace; "0 fallbacks" in the telemetry README) | not logged separately | `docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json`; `.../README.md` |
| Aborted duels | 0 of 16 on H6 | | `analysis.txt` |

So the honest sentence is "0 aborted, 0 runner-level fallbacks or refusals; the PPO policy's own inference errors were not recorded in the held-out rows". Do not write "0 policy errors on the held-out run".

Latency (measured, per decision, PPO seat, 7500 decisions, the stdlib policy on the evaluation machine): mean 0.27 ms, max 10.8 ms (my recompute: mean 0.2686 ms). Runner cadence is 6 frames (100 ms at 60 fps); the online AI answer budget is 0.04 s (`RL_POLICY.md`). The machine is not recorded in the rows. Not measured in the browser build in this task.

## 6. What the learned rival contributes versus the scripted baseline

### Observed (records)
1. **Head to head, held-out H6:** PPO 13 W / 2 D / 1 L against the scripted baseline's 1 W / 2 D / 13 L (the baseline line is the complement, not independent evidence). `analysis.txt` "Duels" rows. Both controllers get the same observation and macro vocabulary (`RL_POLICY.md`; `docs/final/MACROS.md`); the baseline is also one of the opponents the policy trained against (opponent mix: scripted baseline and policy snapshots; `config.json`). It is the only comparison in the record that puts the learned rival against the scripted one with a pre-registered bar.
2. **Tuning starts, for context only** (T24-fix1 Eval, 256 episodes per row, seat-swapped, not held-out): PPO vs scripted baseline 240 / 16 / 0; baseline vs baseline 128 / 0 / 128; PPO vs a random-input seat 254 / 0 / 2. `reports/T24-fix1-evaluation-specialist.md` table. Use at most as "the learned rival does not lose to the baseline on starts it was trained on".
3. **One trace to show.** Recommended: H6-6 MvS in `evaluation/results/T09/traces/` (PPO win at frame 274 with 2 hearts, baseline 0; table row H6-6, `RESULTS-T09.md`), or the loss H6-8 SvM (baseline wins at frame 519) to show a failure honestly. Whichever is shown, label it "one duel from the held-out set; the three trials were identical". Replay of trial 0 of all 16 cells reproduced the traces (`RESULTS-T09.md`); a replay is not new evidence.
4. **What the rival cannot do** (state it): it never sets traps (decision #43, `RIG_TRAP` masked); the target is the nearest figure; it was trained for duels only on 8 starts.

### Hypotheses, not observed (label them)
- H1: "Players misidentify the disguised policy rival more often than the disguised scripted rival." H2: "rate rounds against the policy rival as more tense than against the scripted rival." (`docs/final/playtest/LOG.md` section 1, drafts for Saad.)
- **Neither H1 nor H2 has been tested.** They need Session B (policy against scripted, same player, sealed condition codes). Session B has not been run; LOG sections 5 and 8 are empty. The one external session was Human vs the trained rival only (A1). There is no record of any human playing the scripted baseline in a comparison.
- Therefore **"what the player would lose if the scripted baseline replaced the rival" has no observed answer**. The only supportable statements are the head-to-head result above (observed) and the player-experience hypotheses H1, H2 (untested). The slide must not claim the baseline would feel worse, easier, or less deceptive.

## 7. The external playtest, only as it bears on slides 3 and 4 (full replay audit is the Tech Lead's stage 2)

I replayed the XGJT trace read-only on `ab395fc` (not committed). Because Gate 2 may be asked to check the replay claim later, the facts I saw:

- `server.trace.replay` on `online/duel-XGJT-001-seed0.json` gives `won:B`, 465 frames, and state hash `5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910`, equal to the hash recorded in the file. Inputs counted in the file: seat A (human) 115, seat B (AI) 78; 0 invalid; 0 fallbacks.
- LOG.md section 3: room XGJT, duel 1, A1 Human vs AI, P01, external yes, notes publishable yes, consent option (b) (decision #130), recording "no".
- Per-frame engine state in my replay: the human (seat A) lost hearts 3 to 2 at frame 417, 2 to 1 at frame 441, 1 to 0 at frame 465 (three hits in 48 frames, matching three `hit`/`heart_lost` events in `playtest/2026-11-27-XGJT-001-A.jsonl`); the AI (seat B) lost 1 heart at frame 456 and won with 2 of 3; both in room 5 from frame 246 on. A guard (`pit_hall`) was knocked down at frame 327; the telemetry has no event for it and the file does not say which seat did it.
- **Observation-to-evidence gaps the deck must respect** (these concern Saad's LOG wording, which is quoted, not edited):
  - "Disarming": the only `sword_drop` in the telemetry is seat A's, cause `thrown`, at frame 465, two frames after seat A's own `THROW` input (frame 463), on the same frame as the fatal third hit. In my replay seat A's sword is `drawn` until frame 465 and `none` from 465. No event shows the AI knocking a sword away. The telemetry cannot support "the AI disarmed the human"; it shows the human threw its own sword in the last frames.
  - "Consecutive attacks": supported in a weak sense: three hits on the human at frames 417, 441, 465 (24-frame spacing). Seat B issued 9 LUNGE and 2 SWEEP inputs.
  - "Effective at defeating scripted guards": the telemetry has no guard event and the AI seat is not logged; the replay shows one guard downed at frame 327, with unknown attribution. Treat as not supported by telemetry.
  - "The human could identify the AI" and "the AI located the human": not measurable from telemetry (no identification event; both rivals were in room 5 from frame 246, which is consistent with the AI finding the human but does not show who found whom).
  - "The human struggled to stop or counter the AI": consistent with the result (human lost 0 to 3 hearts, AI lost 1) and 63 of the human's 115 inputs being replaced (`replaced_inputs: {A: 63, B: 7}`); a struggle is an observer judgement, not a measurement.
  - One duel, one external player. Saad's interpretation (combat imbalance) is a hypothesis for further playtests; the sample cannot support it as a finding.
- Online-play limits for slide 6: the telemetry is host-side; XGJT is the only human-versus-AI duel; XUKM (6 duels) is human versus human; AI seats are not logged. The records I read do not show how many machines or players took part beyond one external player P01 in XGJT; I did not verify the two-machine status (STATUS "Waiting on Saad"). The slide should say the online evidence is one human-vs-AI duel and six human-vs-human duels from one 2026-11-27 session.

## 8. Slide 6 items inside my remit

| Claim | Record | Status |
| --- | --- | --- |
| Evaluation threshold not met | T09 above | verified |
| 0 aborted, deterministic, replayable | `analysis.txt`; replay of all 16 cells "ok" in `RESULTS-T09.md` | verified from the record; I replayed one XGJT trace myself, not H6 |
| No paid evaluation, $0 for PPO | section 4 | verified; midterm LLM caveat |
| Local inference | section 5 | measured (mean 0.27 ms, max 10.8 ms) |
| Test counts, green CI, official CI queued | not mine (QA stage). Latest counts I saw: `2373 passed, 14 skipped, 5 xfailed` in REVIEW_LOG; the official CI push run was "queued on the course runner" at merge (REVIEW_LOG, T03 + T03-fix1 row, 2026-11-27) | **not verified by me**; QA must rerun and re-read the official run's status |

## Paths
Created: `docs/final/orchestration/reports/T33-evaluation-specialist.md` (this file). Nothing else changed. Scratch scripts (outside the repository): the session scratchpad.

## Acceptance criteria → evidence
| # | Criterion (T33 stage 1) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | T09: trials, W/D/L, bar, verdict, identical-trials caveat | Met | section 1 |
| 2 | Tuning-start check 120/8/0 and how it differs | Met | section 2 |
| 3 | Training runtime and compute (local CPU, $0) | Met | section 3 |
| 4 | Paid live spend for PPO line, confirmed not assumed | Met, with the midterm caveat | section 4 |
| 5 | Policy errors and fallbacks | Met | section 5 |
| 6 | Observed contribution versus hypotheses H1/H2, one trace or result | Met; H1/H2 untested, said plainly | section 6 |
| 7 | Every number cites path@commit | Met | tables |

## Tests run
```
python3 (recount of evaluation/results/T09/results.json): 48 rows; won:A 24, won:B 18, draw:time_up 6; stale PPO 21, baseline 18; fallbacks/refused/errors/timeouts/busy 0
sha256sum evaluation/heldout/H6.json agents/rl/weights/ppo-run-1.json -> both match the recorded hashes
python3 -c "from server.trace import replay ..." (XGJT-001) -> won:B, 465 frames, state hash equal to the recorded hash
```
No `pytest` run (report only; no code changed). I did not rerun any evaluation or training.

## Findings
- [minor] N1: "16 trials" is 16 duels; the three trials per duel are identical, so effective n is near 8. Say so (section 1).
- [minor] N2: show 120/8/0 only as "tuning starts, trained on, not held-out" (section 2).
- [minor] N3: "0 errors" on H6 is runner-level only; PPO inference errors were not recorded in those rows (section 5).
- [minor] N4: the GDD line "No paid run has been made" (`docs/final/GDD.md:68`) is true for the final project but not for the repository: midterm LLM trials cost about $0.0185 (estimate). Slide wording in section 4. The GDD is not mine to edit.
- [minor] N5: `docs/final/RL_POLICY.md` lines 3 to 8 ("Not yet wired into play.py ... no held-out (H6) result exists yet") are stale against its own Results section and T09. Do not cite that status paragraph. Request for the Tech Lead; not edited here.
- [major for slide 4, not for slide 3] N6: the telemetry does not support "the AI disarmed the human", "defeated scripted guards" or "identified/located" (section 7). The deck can quote Saad's observation verbatim as his entry, but a caption or voice-over that says the video shows a disarm would be wrong for XGJT-001. The Tech Lead's replay check must report this per event.
- [minor] N7: no hardware spec exists for the training or latency machine; do not state a chip or core count.

## Known limitations
I did not open `evaluation/heldout/H6.json` content beyond hashing it. I did not check slide layout, the video, test counts or CI status. The replay in section 7 is a spot check, not the stage 2 audit. The playtest was a single duel.

## Unresolved findings
N4, N5 (wording in documents I may not edit), N6 (for the Tech Lead's stage 2 and QA).

## Requested next action
Tech Lead (T33 stage 2 to 4): use sections 1 to 6 for slides 3 and 6 at this report's commit; use section 7 for the video caption (no "disarm" or "guard kill" claim unless the replay shows it per frame, with attribution). QA: independently rerun the test suite and read the official CI run status for slide 6. Orchestrator: record N4 and N5 as follow-ups.

## Student decision required
none. (Saad may wish to decide whether slide 4 quotes his LOG entry verbatim next to the telemetry gaps in N6; I do not answer that here.)

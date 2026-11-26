---
handoff_id: HO-T20-evaluation-specialist
task_id: T20
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-qa.md@8139bae (reviewed implementation c1be053; also tasks/T20.md@88589af, decisions #67, #68)
source_branch: gate/T20-eval
source_commit: 8139bae (base; the probe test file and this report are committed on top)
reviewed_commit: c1be053 (as carried by 8139bae)
verdict: ACCEPT WITH NOTES
---

# T20: evaluation specialist report (Gate 2)

Status: done

Verdict: **ACCEPT WITH NOTES** at Gate 2 (knowledge boundary and determinism hold). This does not lift QA's REJECT: F1 and F2 still go to T20-fix1. Section "What T20-fix1 must also cover" lists what that fix needs beyond QA's two findings.

## Work completed
Read QA's report, the brief, decisions #67 and #68, `server/telemetry.py`, the `Match` hooks, `play.py`, `tools/telemetry/summarize.py` and `TELEMETRY.md`. Probed the knowledge boundary by non-interference (seat A's log identical whatever seat B hides), determinism with and without the logger over 8 seed and rival combinations, the recorder's source for step/tick/RNG/clock calls, what F2's grace detection can read, and what the summarizer's stall, quit and mechanic counts measure on scripted play. Did not re-litigate F1 or F2.

## Paths
`tests/test_eval_t20_probes.py` (new; 12 pass, 1 strict xfail). No production, trainer, encoder or existing test file touched. Scratch scripts were kept outside the repository.

## Acceptance criteria -> evidence (Gate 2 scope)
| # | Gate 2 scope item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Seat log knowledge boundary | yes | `test_a_log_is_identical_whatever_b_hides`: A's log byte-identical when B is idle versus B disguised, owning a trap and acting (140 ticks). Source reading below. |
| 2 | Host summary and header | yes, with notes | below |
| 3 | Trace and state hash identical with and without logging | yes | 4 seeds x (two humans, AI seat), 900 ticks: trace, `state_hash` and every client message equal |
| 4 | No client message change | yes | same test compares every drained message |
| 5 | AI seat gets no log | acceptable, with a disclosure | below |
| 6 | F2 grace detection from host-side state | not from the public surface | below |
| 7 | Summarizer definitions for T21 | partly | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1582 passed, 12 skipped, 7 xfailed, 2 warnings in 281.43s (0:04:41)
```
The 7 xfails are 4 earlier ones, QA's strict F1 and F2, and my strict `EVAL-T20-E1`. All fail as expected, none unexpectedly pass. Run alone: `tests/test_eval_t20_probes.py` 12 passed, 1 xfailed.

## Leak findings
None found. What was probed:
- **Non-interference.** Same inputs for A; B idle versus B disguised, rigged trap, TAKE/RIG/stance/walk keys. A's file is byte-identical (the clock is fake and deterministic). No `disguise_*` or `trap_*` event, no "disguise" text.
- **Source read of every field.** `_view` reads `obs["me"]`, `obs["my_traps"]` (the engine already limits it to the seat's own unsprung traps in its room, R-V34), `obs["figures"]`, `obs["swords"]`, `obs["room"]` and `obs["last_result"]`. A disguised rival is `kind: "guard"` in `figures` (R-V18), so nothing it does reaches the log under its own name. Other rooms, the other seat's hearts and `minutes_left` are never read.
- **`hit` and `heart_lost` cause heuristic.** The cause is a function of the seat's own view: `fall` from its own `last_result`, `strike` if any figure or flying sword is in its room, else `hazard`. It cannot name the other rival or a trap owner. It can be wrong in measurement (a rival's trap that hurts A while a guard stands in the room reads as `strike`; spikes read as `hazard`), but a wrong label is not a leak, because A's own screen is equally ambiguous. Noted for the T21 analyst.
- **Room events.** `room` is the seat's own opaque label. `trap_rigged` and `trap_sprung` are only emitted while the room is unchanged, and `my_traps` is own-room only, so a trap sprung out of sight is not logged.
- **`duel_end.reason`** is the engine string the bridge shows the client (`won:X`, `draw:both_died`, `draw:time_up`, plus the forfeit texts). Nothing hidden.
- **`pause`, `disconnect`, `forfeit by me/rival`** are the same statuses each client is shown.

## Host summary and header
- The per-seat header carries `seed`, `commit`, `build`, `versions`, `rival` and no name, address, user agent or token (QA also grepped all three files of a full lifecycle). That is what the brief asks, and it is host-only: the traces directory is not under the served site directory (`OnlineServer(site_dir=<temp build>)`), and the hosted page logs nothing. Note: the seed sits in each per-seat file, so a seat's file must never be handed back to a participant. TELEMETRY.md says the files stay on the host; it should also say not to share a seat's file with its player.
- The host JSON holds `seed`, `engine_reason`, `forfeit_seat` and per-seat event counts. TELEMETRY.md says "counts only, no ownership", but the per-seat counts include `trap_rigged` and `disguise_on` per seat, which is ownership by count. Host-only and allowed by the brief (item 3), so a wording fix, not a leak.
- `summarize.py` reads only `*.jsonl`, so the host JSON (seed) never enters the analyst's summary. Good.

## Determinism
- Equal trace, `state_hash` and client messages over seeds 1, 7, 4242, 99, each with two humans and with the baseline AI seat (900 ticks of random key sets, including refused keys and shift). The tech-lead's tests cover one seed; this widens it.
- The recorder's source (checked through `ast`, so docstrings do not count) calls none of `step`, `tick`, `reset`, `rematch`, `press`, reads no `_duel` or `rivals`, and imports neither `random` nor `time`. `Match._note_refused` reads `legal_actions` and `observe` only.
- Cost: measured on this machine (macOS, Python 3.13) 0.206 ms per tick without and 0.245 ms with the recorder, against the 83.3 ms tick. About 1,600 lines and 160 kB for a 74-second, two-seat duel. Residual risk, not reproduced: the AI seat's `TimeLimitedRival` has a wall-clock budget, so in principle added CPU could change when it falls back. At 0.04 ms per tick the margin is large, but a duel against the AI with `--playtest` is "same input, same trace" only while the AI answers within budget, as it is without the flag.
- `play.py --versus --playtest` was not run under a display (as QA). Its code path calls the same recorder and adds no engine call; its tests ran in the suite.

## No client message changes
Equal, message by message, in the test above, human and AI modes. The only server-side additions are reads before and after `game.tick()`.

## The AI seat gets no log: acceptable
Yes, for T20's purpose, with two disclosures:
1. Decision #67 and the brief speak of the human playtest; the human's own log shows everything the human saw, and every seat's accepted inputs, AI included, are already in the duel trace (`traces/online`), which `_ticks` records for both seats. So the AI's behaviour is recoverable and a second log would add nothing the trace lacks.
2. For the T21 analyst: in a duel against the baseline rival the summary has one seat only. "Mechanics never used" and quits describe humans only, and an AI-duel `no_rematch` is the human's. The AI seat's fallback count is in the trace, not in telemetry. The only AI today is the scripted baseline; when the PPO policy joins the server it will need no telemetry change for this purpose.

## F2: can grace be detected host-side without leaking into a seat's log?
Yes in principle, no from today's public read surface, and no retroactively.
- The resolved action is not public. I ran grace (`d` then `d`+`w` one tick later) against a plain jump: `ep.log` holds `RUN_JUMP_RIGHT` (the submitted action) while the engine runs `JUMP_RIGHT`; `observe(seat)["me"]["motion"]["effect"]` is `"flipped"` in both cases. Only `Duel._move_action[seat]` (private) differs. `test_grace_resolved_action_is_not_in_the_public_read_surface` pins this.
- No leak risk in logging it. The resolved action and a `grace` marker are the seat's own input, resolved by the engine's own rule; no other seat, disguise or trap information is involved. A host-side read of `ep._duel._move_action` would therefore be safe for the knowledge boundary, but it breaks the recorder's current "public reads only" contract, and the recorder test I added would need to allow exactly that one read.
- Better options, for the orchestrator to choose (a `pop/` read is outside the brief's permitted paths without an explicit decision): (a) a small public read-only accessor on the episode, for example the resolved action of the last accepted input per seat, requested from the Tech Lead; (b) infer grace from the log itself (a direction accepted at t, a jump in the same direction at t+1 or t+2, no direction accepted at t-1), which copies engine logic into a second source of truth and approximates `_fresh`, so it is not recommended.
- Append-only files cannot "drop" a RIGHT already written one tick earlier. The fix must either emit a `grace` marker event on the jump tick and have the summarizer discount the superseded direction, or hold direction events back two ticks before writing. QA's xfail asserts the log shows the jump only, which only the second approach meets. The first is simpler and keeps tick order; the orchestrator should say which one the acceptance wording means.

## Summarizer definitions, for the T21 analyst
- **Idle** is "no accepted action for 3 s, in ticks". Because a held key is accepted every tick, a player walking into a wall or mashing a refused key is not idle. It measures no input, not no progress. Pauses do not count (ticks), good.
- **Refused runs.** REFUSED_RUN_MIN=3 ticks (0.25 s) flags ordinary play. In scripted walking, jumping and climbing for two seats, over three seeds, 21 refused runs appeared and every one was exactly 3 ticks long, a fixed engine window in which the held key is not yet legal, not a confused player. As defined, this stall signal fires on normal play and will drown real stalls. Suggest a threshold in seconds (for example 12 ticks, 1 s) or runs longer than the engine window; it is Saad's threshold, so reported as a proposal to revisit, not changed.
- **Time stuck in a room** (60 s, `STUCK_ROOM_S`) counts time between `room` events. The arena has six rooms and a duel is at most 300 s, so a long fight or ambush in one room is normal; "stuck" here means "stayed", not "could not leave".
- **Quits.** Disconnect, forfeit, no rematch (every `rematch` event false, none true) and abandoned duel (`duel_end.reason` in `abandoned` or `room_failed`) match the brief. `no_duel_end` covers a killed server. QA's F3 (no `pause` end on forfeit) does not affect them.
- **Mechanics never used or used once.** "Never used" is right. "Used once" and the totals are wrong because of F1, and F1 is wider than QA's repro (below).
- **`accepted` is not "executed".** In 1,200 ticks of random two-seat play, 496 inputs were accepted and the engine dropped 13 of them unstarted (`Duel.stale`: A 9, B 4), about 2.6 percent. Small, but it means accepted counts are an upper bound.

## What T20-fix1 must also cover
1. **F1 is wider than the held key.** `flip` is counted from any accepted action whose `effect` is `flipped`, and `effect` is `motion["effect"] or last_result["effect"]`, so any key queued while a flip runs inherits "flipped". Repro: `d`+`w` for one tick then `a` for three ticks gives `flip: 4` (one jump, three LEFT). Strict xfail `tests/test_eval_t20_probes.py::test_a_queued_direction_is_not_credited_with_the_running_flip` (expected 1, actual 4; run with `--runxfail`). The fix has to count a use at the move's start (rising edge, or when the resolved move changes), not at every accepted tick, and must not read the effect of the move in progress as the effect of the newly queued action. The same applies to the `effect` field on every `action` row: it describes the move running, not the action just accepted. The T21 analyst reading `effect` per row would be misled; document it or fix it.
2. **F2 is one case of a wider gap: accepted is not resolved.** Besides R-V35, `Duel` also rewrites inputs for R-V10 (a kick replaces the rest of a jump) and R-V22 (a direction turns a hop into a flip), and drops stale queued inputs. Any "resolved action" column the fix adds should come from one place for all of these, not a special case for grace. I reproduced only R-V35 (the R-V22 probe I tried climbed instead of hopping, so it proves nothing).
3. **Keep the knowledge boundary through the fix.** If the fix reads `_move_action` or a new accessor, the recorder's contract text, the module docstring and my `test_recorder_source_only_reads` need to name that one read, and the non-interference test above must still pass (it will, as the value is the seat's own).
4. **Re-run determinism** (the 8-combination test above and the tech-lead's two) after the change; an accessor that caches would break it.
5. **Doc fixes** in TELEMETRY.md: do not hand a seat's file to its player (the seed is in it); the host JSON counts are per seat, not "no ownership"; `action.effect` describes the running move; the refused-run threshold note above.
6. **QA's F3** (no `pause` end when a paused duel ends by forfeit) is cheap to fix in the same pass.

## Baseline fairness, reward and training, checkpoint, held-out
Not touched by T20 (telemetry only, no training, no baseline, no held-out set). `tools/rl/` and `evaluation/heldout/` are not in the diff `bdc3c76..8139bae`. Not assessed.

Baseline fairness: not applicable (no AI or baseline change).
Reward and training method: not applicable.
Checkpoint reproducibility: not applicable.
Train / held-out separation: not applicable; no held-out file read or tuned against.
Evaluation validity and confounds: not applicable; telemetry is an observation instrument for T21, not a comparison. For T21: seats are human, the two starts are mirror images, and the thresholds above are proposals.
Local inference performance: measured, recorder overhead only: 0.04 ms per tick on this machine (macOS, Python 3.13), 0.05 percent of the 83.3 ms tick. No inference was measured (no model in scope).
Replay and fallback: the trace and state hash are unchanged by logging (tested, human and AI seat). The fallback count lives in the trace, not in telemetry; the AI seat's `"source": "fallback"` labelling is untouched.
Training-run readiness: not applicable to T20.

## Known limitations
No real browser or WebSocket client, no `play.py --versus --playtest` under a display, no two-machine run. The refused-run histogram comes from one scripted player (three game seeds), so it shows a pattern, not a rate for real players. The R-V22 probe was inconclusive.

## Unresolved findings
New, for T20-fix1: the F1 widening and the wider-than-grace resolved-action gap above (major, both on the summarizer's numbers). Not new: F1, F2, F3. Refused-run threshold calibration (minor, Saad's number).

## Requested next action
Orchestrator: send QA's F1 and F2 plus section "What T20-fix1 must also cover" to the Tech Lead, decide whether F2 may add a `pop/` read accessor or read the private `_move_action`, and decide whether the grace log is a marker plus summarizer discount or a two-tick hold-back. Then re-run Gate 1 and, for the changed recorder, a short Gate 2 re-check (the three tests named above are the checks). Saad: the refused-run threshold and the CONSENT draft remain his.

Commit to review: the head of `gate/T20-eval` (this report and `tests/test_eval_t20_probes.py`).
What changed: one test file and this report.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t20_probes.py` (12 passed, 1 xfailed).
What I am unsure about: whether the brief's "resolved action" means grace-resolved only or every engine rewrite; whether 3 ticks was meant as the refused-run threshold.
Touches the knowledge boundary or AI seat: yes (read-only probe; no gameplay code touched)

## Student decision required
None.

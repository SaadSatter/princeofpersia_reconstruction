**Pre-registered verdict (decision #77): NOT SUPPORTED.** The PPO rival won 13 of the 16 held-out duels; the bar was at least 14 of 16 with no aborted duel. "Not supported" means the improvement over the scripted baseline was not shown at this bar. It does not mean the rival is worse.

# T09: the one held-out comparison (H6), PPO rival against the scripted baseline

- Run id `20261125T085558Z`, engine commit `77bc2f7d506d5cb774287065ea2d62501343e72c` (code identical to `orch/reviewed` 0ea8d73; the only later commits on `eval/T09` are the evaluation report), clean tree, one invocation (decisions #79, #77, #74, #75, #64, #61, #24, #80).
- Weights `agents/rl/weights/ppo-run-1.json`, SHA-256 `80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c`. H6.json SHA-256 `d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266`. Ledger: one row, status `claimed`, `evaluation/heldout/ledger.jsonl`. No refusals.
- Command, as briefed: `run_versus_suite.py --split heldout --configs MvS,SvM --trials 3 --seed-key-file <outside the repo> --out evaluation/results/T09`. Exit 0, 48 rows, 0 aborted.
- Evidence: `evaluation/results/T09/results.json`, `analysis.json`, `analysis.txt`, `traces/`.
- Counting rule (brief step 4): a duel is one (start, seat order) cell, 16 in all; a cell is a win only if all 3 trials win. In every cell the 3 trials agreed on outcome (one distinct outcome per cell, so the 3 trials are one deterministic trial, not 3 samples; effective n is 16 cells and nearer 8 starts). The conservative rule changed nothing.
- Pending Saad confirmation, as always: the B2 "low" threshold and D1 "on screen" are not part of H6.

## Overall

| line | W | D | L | n | 95% Wilson on the win rate (optimistic, see below) |
| --- | --- | --- | --- | --- | --- |
| PPO rival, all 16 duels | 13 | 2 | 1 | 16 | 0.57 to 0.93 |
| PPO as seat A (MvS) / seat B (SvM) | 7W 1D 0L / 6W 1D 1L | | | 8 / 8 | |
| Robustness, descriptive only, without H6-1 (the training-like start) | 12 | 1 | 1 | 14 | 0.60 to 0.96 |

The intervals treat 16 duels as independent. They are not: the controllers are deterministic, the three trials of a cell are identical, and the two seat orders of a start share a layout, so the effective n is nearer 8 (G-4) and the true interval is wider. Starts won in both seat orders (sweeps): 5 of 8 (H6-3, 4, 5, 6, 7). Not swept: H6-1 (draw, then win), H6-2 (win, then draw), H6-8 (win, then loss).

## Per start (PPO result; hearts at the end PPO/baseline)

PPO is seat A in MvS and seat B in SvM. Start positions are fixed by seat (A and B), so seat order also changes who stands where. Rooms are the two rivals' start rooms (A, B). Exposure labels from `tools/eval/exposure_table.py`.

| start | exposure | rooms A,B | hazard ahead | MvS: result, termination, hearts | SvM: result, termination, hearts | sweep |
| --- | --- | --- | --- | --- | --- | --- |
| H6-1 | training-like | 4, 5 | no | D, time_up (3600), 3/3 | W, won:B (1485), 2/0 | no |
| H6-2 | unseen layout | 1, 4 | no | W, won:A (477), 3/0 | D, time_up (3600), 3/2 | no |
| H6-3 | partly training-like | 5, 3 | no | W, won:A (373), 3/0 | W, won:B (1479), 2/0 | yes |
| H6-4 | unseen layout | 3, 1 | no | W, won:A (1611), 2/0 | W, won:B (1635), 3/0 | yes |
| H6-5 | unseen layout | 2, 6 | yes | W, won:A (459), 2/0 | W, won:B (295), 3/0 | yes |
| H6-6 | partly training-like | 6, 2 | yes | W, won:A (274), 2/0 | W, won:B (357), 3/0 | yes |
| H6-7 | partly training-like | 6, 2 | no | W, won:A (299), 2/0 | W, won:B (1689), 3/0 | yes |
| H6-8 | partly training-like | 5, 4 | yes | W, won:A (633), 1/0 | **L, won:A (519), 0/1** | no |

## The odd rows, in full

- **H6-8 SvM, the one loss.** The scripted baseline (seat A) won at frame 519 with 1 heart left against the PPO rival at 0. Hazard-ahead start; by entry into the falling posture, the PPO seat entered 3 falls and the baseline 3 (trial 0 replay). Same start, other order: the PPO rival won with 1 heart left (frame 633).
- **H6-1 MvS, draw (training-like start).** 3600 frames, 3 hearts each, no hit decided. Stalemate; cause not analysed. The same start, other order, was a PPO win at 1485 frames.
- **H6-2 SvM, draw.** 3600 frames, PPO 3 hearts, baseline 2. Stalemate; cause not analysed.
- No aborted duel, no fallback, no refused, errored, timed-out or busy decision, 0 invalid inputs on either seat (all 48 rows, both seats). These "0 errors" are runner-level only: PPO inference errors (caught inside the controller and answered with WAIT) were not recorded in the held-out rows; T08-fix2 adds them for future runs (decision #84).

## Stale inputs and falls (decision #80: reported per duel as a confound)

The PPO seat did **not** stay at 0 stale on H6. PROTOCOL H-c ("0 stale for both seats") is therefore not met as written on H6 (PPO 21, baseline 18); decision #80 relaxed it for the step-1 health check only, and on H6 the counts are reported, as here. Per trial (the three trials of a cell are identical; totals over 48 rows are 21 PPO and 18 baseline):

| cell | PPO-seat stale per trial | baseline stale per trial |
| --- | --- | --- |
| H6-2 MvS | 1 | 0 |
| H6-4 MvS | 0 | 1 |
| H6-4 SvM | 0 | 1 |
| H6-5 MvS | 1 | 0 |
| H6-5 SvM | 0 | 1 |
| H6-6 MvS | 0 | 1 |
| H6-6 SvM | 3 | 0 |
| H6-7 MvS | 0 | 2 |
| H6-7 SvM | 2 | 0 |
| every other cell | 0 | 0 |

A stale input is a queued move that was no longer legal when the previous move ended (the tuning diagnostic found it comes with a move ending in a fall, where only WAIT is legal), so the drop costs nothing extra. This mechanism is shown for the baseline on the tuning split; it is not verified for the PPO seat (H6-2 MvS, H6-5 MvS, H6-6 SvM, H6-7 SvM). The run is not repeated (brief step 3, decision #80). Falls (not independently reproduced: the replay script is not committed, and the per-cell numbers were only re-summed, not re-derived), counted as entries into the posture `falling` by replaying trial 0 of each cell (descriptive; includes ordinary drops, not only damage), per cell PPO/baseline: H6-1 MvS 1/1, SvM 0/0; H6-2 2/1, 0/4; H6-3 1/3, 2/4; H6-4 2/2, 0/1; H6-5 2/1, 2/4; H6-6 0/2, 4/3; H6-7 2/5, 3/1; H6-8 1/2, 3/3 (the one loss, H6-8 SvM, had 3 falls on each seat, so falls do not explain it). Totals 25 PPO, 37 baseline: the baseline entered the falling posture about 1.5 times as often, which may favour the PPO rival and is not the same as falling damage (not measured here). None of the three non-wins (H6-1 MvS, H6-2 SvM, H6-8 SvM) has a stale input on either seat, so stale inputs do not explain the shortfall. The claim stays "not shown"; it is not "would have reached 14".

## Status of H-a and the intervals

PROTOCOL H-a ("wins more than it loses") is not the pre-registered criterion; the bar of decision #77 is. No strength claim is made. The Wilson interval (lower bound 0.57, above 0.5) is optimistic because the effective n is near 8, and the baseline line in `analysis.txt` (1W 2D 13L) is the complement of the PPO line, not independent evidence.

## Confounds and limits

- The rival's targeting is the nearest figure; the baseline's uses the same observation and macros. H6 has one distinct outcome per condition (deterministic, G-4), not 3 independent trials.
- Guard patrols overlap with training for H6-1 (full), and partly for H6-3, 6, 7, 8 (#75); H6-2, 4, 5 are unseen layouts. The claim is "unseen start pairs and guard layouts", not an unseen map.
- No guard in room 2 (G-3). Hazard-ahead starts H6-5, 6, 8.
- The PPO rival was trained for duels only. The baseline stale inputs and falls above. The start positions are fixed by seat, so seat order is confounded with position: the 7W 1D 0L (seat A) against 6W 1D 1L (seat B) split, with 8 duels each, is not evidence of a seat effect either way.
- Latency (measured, per decision, PPO seat, 7500 decisions): mean 0.27 ms, max 10.8 ms (H6-3 SvM t2).
- Replay: `--replay` of trial 0 of all 16 cells reproduced the traces (all `ok`). A replay is not new evidence.
- Effective n near 8: the reported intervals are optimistic.

## No tuning

Nothing was tuned, re-seeded, or chosen after the result: the weights, H6, the bar and the starts are as pre-registered.

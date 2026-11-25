# PPO rival: encoder, trainer, inference (task T07)

Status: **built and tested; full training run NOT started** (waiting for the
macro fix `T05-fix1`: GATE-T05-eval found that the vocabulary cannot take a
seat down a floor, so a policy trained now would learn on a broken action
set). No weights are committed yet; the hash table below is empty until the
full run. Awaiting QA (Gate 1) and the Evaluation Specialist (Gate 2).

Decisions followed: DECISIONS #3 (small PPO policy we train, PR #64 pattern),
#23 (macro vocabulary), #24 (6-frame cadence, labelled `WAIT` fallback);
PLAN v2 (numpy for training only, stdlib inference, no game dependency);
GATE-T01-eval (no `minutes_left`, no `outcome()` in features); GATE-T04-fix1
(fast path, fresh controllers per trial); GATE-T14-eval (inference stdlib-only,
weights a plain JSON list, loadable in the browser build).

Code: `agents/rl/encoder.py`, `agents/rl/policy.py` (shipped, stdlib only);
`tools/rl/env.py`, `tools/rl/ppo.py`, `tools/rl/train.py` (training only).
Tests: `tests/test_rl_encoder.py`, `tests/test_rl_policy.py`,
`tests/test_rl_train.py`.

## What the rival sees

The encoder (`Encoder`) turns **one seat's observation** into 251 floats. It
keeps its own history (below). It reads only: room tiles, edges, `me`,
`figures`, `swords`, `suspicion`, and the controller's own `status` (last macro
and its state). It never reads `minutes_left`, the task text, `last_result`,
`outcome()`, an id, or the seed (tests: key-access spy, source scan, and a
changed `minutes_left` leaves the vector unchanged). Elapsed time is also not
a feature: the history counters are capped and per room, so the policy cannot
count the duel clock. A disguised rival and a real guard with the same observed
fields give identical features (test over a real engine, step by step).

| Group | Count | Features |
| --- | --- | --- |
| Room tiles | 150 | for each of 3x10 cells: wall, air, spikes, loose tile, special (gate, plate, exit) |
| Edges | 2 | an exit left, an exit right |
| Me | 19 | row, column, facing, posture (standing, hanging, falling, other), hearts / max, one heart left, stance (none, low, mid, high), sword drawn, disguised, knocked-down timer, moving, leaping |
| Suspicion | 2 | highest meter on screen, meter of the nearest guard |
| Swords on the floor | 4 | nearest: present, dx, dy; count |
| Figures | 3 x 20 | the K=3 nearest by distance, ties broken by observed fields (never list order): present, dx, dy, same row, ahead of me, faces me, label "rival", posture (standing, downed, knocked down, other), sword, stance (4), moving, has leapt/run unarmed, frames motionless (cap 48), frames in my sight line without reacting (cap 24) |
| History | 15 | last macro (9 slots + none), last macro running / done / failed, distinct rooms seen (cap 6), decisions in this room (cap 60) |

The two per-figure counters and the leap flag are kept by the encoder from
what it has seen at each decision (tracks matched by place, no ids). They are
the raw tells the scripted baseline thresholds; the policy learns its own
thresholds.

## Actions

The nine macro slots of `agents/macros.py`: `BLEND, DISGUISE, WAIT, FOLLOW,
STRIKE, FLEE, CLIMB, SEARCH, RIG_TRAP` (unchanged; `RIG_TRAP` keeps its slot and
is always masked).

**The PPO rival does not set traps in G2/G3.** Traps are human-only, by Saad's
decision #43 ("Train without traps", 2026-11-24). `RIG_TRAP` stays reserved and
masked, so the rival never rigs; it can still be hurt by a human's trap. Say so
wherever the rival is described to players or in results. Mask (`macro_mask`): `WAIT`, `SEARCH`,
`BLEND`, `CLIMB` always; `FOLLOW`, `STRIKE`, `FLEE` need a figure that is not
downed; `DISGUISE` needs a downed figure and no disguise; with no legal input
only `WAIT`. The mask is a cheap necessary condition; the executor can still
fail a macro, and reports it in the next decision's `status`.

Cadence: the runner asks at 6-frame decisions. The policy picks a macro when
the last one is no longer running, or every `MACRO_EVERY = 4` decisions (2 s),
otherwise the running macro continues. **Target rule:** the macro's target is
the nearest figure that is not downed (fixed rule on observed positions);
the learned part is when to strike, follow, flee or blend. This is a known
limit: the policy cannot choose a farther figure.

Fallbacks: an inference error returns `WAIT` and is counted
(`PolicyMacro.errors`); a runner-level failure is the runner's labelled `WAIT`
fallback, counted per seat.

## Reward

Terminal: +1 win, -1 loss, 0 draw (also a time-up draw). Shaping
(`RewardConfig`, default on, `--no-shaping` turns it off): +0.1 per heart the
opponent loses, -0.1 per heart I lose, +0.05 when I become disguised; at most
a few tenths against the +-1 terminal. Shaping is read from the runner's
`on_frame` view (training only); the policy never sees hearts of the other
seat.

## Trainer

PPO in numpy (`tools/rl/ppo.py`): actor and critic MLPs 2x64 tanh, masked
softmax, GAE (gamma 0.995, lambda 0.95), clip 0.2, Adam lr 5e-4, 4 epochs,
minibatch 256, value coef 0.5, entropy 0.01, gradient norm 0.5. Per update: 16
episodes on 2 forked worker processes. Opponents: the scripted baseline, or
(50%, once a snapshot exists) one of the last 6 snapshots of the learner,
snapshotted every 5 updates. The learner's seat, start pair and which of the
pair's two starts it takes cycle through all 8 combinations every episode
(seats swapped every episode). Rollouts use `copy_mode="json"`,
`threaded=False` and a fresh controller per episode. All seeds are fixed
(`--seed`); two runs with one seed give the same weights (tested with one
worker; ordering is fixed with two).

**Held-out starts and tuning starts.** Training uses **only the eight tuning
starts** in `tools/rl/env.py: TUNING_STARTS`: the two the midterm `MACROS.md`
records, and six added in T07-fix1 by Saad's decision #44 (2026-11-24), recorded
here **before any training run**. The held-out H6 starts belong to the Evaluation
Specialist (T08); training does not read them.

The six added starts (A start, B start; room, row, col, facing; row 2 is the bottom walkable floor row):

| # | A | B | Lower rooms (4, 5, 6) |
| --- | --- | --- | --- |
| 3 | (1, 2, 8, -1) | (4, 2, 4, +1) | B in 4 |
| 4 | (2, 2, 6, -1) | (5, 2, 4, +1) | B in 5 |
| 5 | (3, 2, 1, +1) | (6, 2, 6, -1) | B in 6 |
| 6 | (4, 2, 9, -1) | (2, 2, 1, +1) | A in 4 |
| 7 | (5, 2, 5, -1) | (1, 2, 9, -1) | A in 5 |
| 8 | (6, 2, 3, +1) | (3, 2, 0, +1) | A in 6 |

How they were picked: by hand, from floor cells on row 2 (not holes, spikes,
plates, gates or posts), with the rule that no start **cell** (room, row,
column, ignoring facing) equals a cell used by any held-out list on this base
(`HELD_OUT_STARTS` and `LOWER_HELD_OUT_STARTS` in `tests/test_versus_baseline.py`)
or by the candidate H6 in the unreviewed WIP `orch/wip-T08` @ 25e4587. Each pair
is in two different rooms, three pairs put a rival in each lower room, and no
new pair or cell repeats another. `tests/test_rl_fix1_starts.py` checks
disjointness from the lists on the base, and from the candidate H6 cells written
into the test as facts. **T08 must re-check against the H6 it actually freezes.**
Training cycles through the 8 starts x 2 seats x 2 orders = 32 combinations. The
per-update evaluation uses the first 8 combinations (`_combo(0..7)`,
`tools/rl/train.py`), so the in-loop curve covers start pairs 0 and 1 only, the two
midterm starts. `final_check` loops over **all 32 combinations**
(`for i in range(len(env.COMBOS))`), 128 pure-Python duels with the default 4 seeds,
so it covers all eight starts. Eight starts are still few:
expect some over-fitting, and report tuning-start numbers as such, not as
general strength.

Note for T08 (not changed here): the existing midterm tuning start
`(1, 2, 3, +1)` equals the **B** slot of candidate H6-4 as a cell.

**Logging and stopping.** One JSON line per update in `<out>/log.jsonl` (steps,
episodes, mean return, mean terminal reward, win rate vs the baseline on
tuning starts from 8 greedy episodes, training win rate, opponent mix,
fallbacks, losses, elapsed seconds). Training stops at the time cap (default
5,100 s, cap 90 min) or `max_iters`. The **last** weights are exported;
no checkpoint is chosen by score. `summary.json` records the commit, seed,
steps, wall time, the weights hash, and a final check of the exported file
through the pure-Python rival against the baseline.

Command (to run later, as a background process, polled):
`python -m tools.rl.train --out tools/rl/logs/run-0 --seed 0 --seconds 5100`

Speed (estimate, not a measurement of the full run): Gate 2 measured 8 untrained,
early-ending duels in 2.7 s on an Apple M4 (about 0.34 s per duel). The earlier
sandbox figure of about 6 s per update (2 cores, 16 training plus 8 evaluation
episodes) is superseded. Full 5-minute duels and a trained policy will differ, so
treat any total as an estimate until the run's `summary.json` reports wall time.

**Errors are visible and fatal (T07-E4).** `TrainPolicy` counts any exception in
`choose` (it answers WAIT and carries on for that episode), a snapshot opponent's
`PolicyMacro.errors` is added, and `play_episode` returns `policy_errors`. Each
`log.jsonl` row and `summary.json` carry `policy_errors`. **Decided (#47, Saad):**
the run stops on the first update with any such error, writes no weights, and
`python -m tools.rl.train` exits with status 2 and a message on stderr
(`TrainConfig.fail_on_policy_error`, default true). The shipped rival's
controller exposes `policy_errors()` (the count of swallowed inference errors).
The per-update greedy evaluation episodes are counted too: each row has
`eval_policy_errors`, included in `policy_errors`, and with the switch on an error
there stops the run as well. `final_check` reads `policy_errors()` of the exported
policy on every duel and writes `policy_errors` and `failed` into the
`final_check_vs_baseline_tuning_pure_python` block of `summary.json`; a count above 0
sets `stopped` to `final_check_policy_error` and the command exits with status 2.
**Decided (#50, Saad):** in that case the exported file is renamed `weights.failed.json`, so
no `weights.json` exists; `summary.json` carries `weights_file`, `weights_failed` (true) and
the `weights_sha256` of the failed file. A clean run still writes `weights.json`.
With `fail_on_policy_error` off (diagnosis only) an update whose episodes are all
empty skips the PPO update instead of crashing.

## Weights and inference

`agents/rl/policy.py`: `load_net(path, sha256)` refuses a missing or wrong
SHA-256 of the file; the format is `sm-ppo-mlp-1`, plain JSON lists of floats
(`sizes`, `macros`, per-layer `w` as rows of inputs and `b`). Inference is pure
Python, argmax over allowed macros by default (lowest slot wins a tie), no
numpy, no pygame. `make_rl_rival(path, sha256)` returns a `MacroController`
labelled `kind: "policy"`. Parity test: the pure-Python logits equal the numpy
forward pass to 1e-9 on 200 recorded observations.

| Weights file | SHA-256 | Commit | Steps | Wall time |
| --- | --- | --- | --- | --- |
| (none yet: waiting for Saad's go-ahead) | | | | |

## Results

Full training run: **not started, waiting for Saad's go-ahead.** The smoke runs in
`tests/test_rl_train.py` (under 60 s, 900-frame duels) only check that the
loop runs, logs, exports and reloads; they say nothing about strength.

## Open items for Saad

- Approval of the feature set, the macro cadence of 4 decisions, and the
  nearest-figure target rule (CQ-1).
- Decided: eight tuning starts (#44), train without traps (#43). T08 must confirm
  the frozen H6 shares no start cell with the eight.
- Decided (#47): the full run stops on the first policy or encoder error (above).
- Whether training may randomise the duel limit (the encoder already has no
  clock, so this is not needed for the leak rule).

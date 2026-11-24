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
is always masked until traps exist). Mask (`macro_mask`): `WAIT`, `SEARCH`,
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

**Held-out starts.** Training uses **only the two tuning starts**
(`tools/rl/env.py: TUNING_STARTS`, the ones `MACROS.md` records). The held-out
H6 starts belong to the Evaluation Specialist (T08); they are not available to
this task and not used. The two starts are few: expect over-fitting to them.
The numbers below are tuning-start numbers, not evidence of general strength.

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

Measured throughput (this sandbox, 2 cores, early-ending untrained duels):
about 6 s per update of 16 episodes plus 8 evaluation episodes.

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
| (none yet: waiting for T05-fix1) | | | | |

## Results

Full training run: **not started, waiting for T05-fix1.** The smoke runs in
`tests/test_rl_train.py` (under 60 s, 900-frame duels) only check that the
loop runs, logs, exports and reloads; they say nothing about strength.

## Open items for Saad

- Approval of the feature set, the macro cadence of 4 decisions, and the
  nearest-figure target rule (CQ-1).
- Whether training should use more than two tuning starts (needs T08 to
  confirm they do not overlap the H6 starts).
- Whether training may randomise the duel limit (the encoder already has no
  clock, so this is not needed for the leak rule).

# Versus evaluation protocol (task T08)

Status: built on `orch/reviewed` fc02687 by the Tech Lead (T08), through Gate 1
(QA) and Gate 2 (Evaluation Specialist) with notes, then corrected by T08-fix1
(decisions #64, #65, #74 to #77 and the gate findings); T08-fix1 is waiting for
its own gates. No held-out result exists. T09 runs H6 once, after T08-fix1 and
T19, on the post-T19 engine.

Code: `evaluation/` (scenarios, monitors, controllers, freeze check, analysis)
and `tools/eval/` (`run_versus_suite.py`, `analyze_results.py`). Tests:
`tests/test_eval_*.py`.

## 1. What is compared, and the hypotheses

The AI rival is the PPO policy (`agents/rl/`, shipped weights
`agents/rl/weights/ppo-run-1.json`, SHA-256 in `agents/rl/policy.py`
`SHIPPED_SHA256`). The comparison is against the scripted baseline
(`agents/versus_baseline.py`), on the same controller interface, labelled
`scripted`. The PPO rival has no provider, token or cost: those fields are
**N/A** in every row (as in PR #64).

Hypotheses (stated before any held-out run; they are claims to test, not
results):

| # | Hypothesis | Measured by |
| --- | --- | --- |
| H-a | In full duels from the held-out starts the PPO rival wins more often than it loses against the scripted baseline, in both seats | H6, win/draw/loss per controller and per seat, Wilson intervals |
| H-b | The PPO rival does not do worse than the baseline on the four approved scenarios (D1, B2, I3, F5) | tuning split, per-scenario success rates, M against S as the subject, per seat (decision #65) |
| H-c | Neither rival is pushed to its fallback: fallbacks, invalid inputs and stale inputs stay at 0 for both | the rows' `seats.*.fallbacks`, `invalid_inputs`, `stale_inputs` |

H-a is the headline. A draw (time up) is not a win; an aborted round is not a
win. If the intervals overlap the report says so and makes no strength claim.
The bar for H-a is pre-registered in section 6 ("The pre-registered T09 bar").

**H-b and what it can show.** The PPO rival was trained for duels only (T07:
disguise appears only as a 0.05 shaping term, and no scenario skill was a
training target). A loss against the baseline on D1, B2 or I3 is therefore
expected and is **a result, not a defect**: it says the skills were not trained
for, not that the rival failed. H-b is reported as found, per scenario and per
seat, with no tuning toward it.

## 2. What counts as success (Saad's words, decisions #9, #58, #59)

Computed from the true state after every frame (the runner's `on_frame`
view), never shown to a controller. Subject = seat A.

| Id | Saad's words (decision #9) | Reading in force | Predicate |
| --- | --- | --- | --- |
| D1 | "Success if the agent kills a guard and picks up the disguise when no other player is on screen." | #59: "on screen" = the other rival is in the agent's room at **no frame** of the scenario | a guard is downed, its uniform is taken by the agent, and the other rival shares the agent's room at no frame. A guard counts as the agent's only if the agent struck it, or was in the guard's room when it was first knocked down or downed (QA F-1): a guard the other rival downed while the agent was elsewhere does not. The other seat is forced to WAIT |
| B2 | "Blend if another guard doesn't notice it or keeps low suspicion." | #58: "low" = suspicion **below 50 of 100** for the whole scenario (`monitors.B2_LOW_THRESHOLD`, a named parameter); #76: the disguise must last | the disguised agent is never targeted by a guard, its suspicion meter stays below 50 at every frame, **and it is still disguised at the end** (a mid-way loss made good by the end is recorded, the end state decides). The row also stores `success_active` (at least 6 distinct cells visited while succeeding) because a seat that stands still is never noticed; per #66 that is reported and **never scored** |
| I3 | "Identify if the agent can distinguish between player guard and real guard." | no reading was open | the first thing the agent strikes is the disguised rival (its hearts drop), not a real guard (downed or knocked down); a same-frame strike on both is not a success. The other seat is a scripted `decoy` that paces like a patrol (stated confound: its stride is not calibrated to a real patrol) |
| F5 | "Fight or retreat if it wins a duel against a player or guard." | no reading was open | the agent is alive when a guard is downed, or when the other rival dies (`win_against: either`). F5-a, F5-b: guard with seat B idle in another room; F5-c: rival against rival |
| H6 | (decision #9: held out) | not applicable | full duel, 3,600 frames (5 minutes, decision #5); **no success flag**: the outcome by controller slot is the measurement |

Retreating is not scored separately: "fight or retreat" succeeds when the duel
is won, however it was won.

**Seat B as the subject (decision #65).** Every tuning start of D1, B2, I3, F5-a
and F5-b has a mirrored start `<id>-B`: the two rivals swap cell, facing, hearts
and disguise, the guards stay, the subject is seat B and the forced stand-in
(WAIT or decoy) plays seat A. Rows carry `subject_seat`, the monitors watch the
subject's seat, and the analysis reports each subject seat as its own line, never
pooled. A mirrored start runs the configurations whose seat-A letter is S (SvS
for the baseline, SvM for the PPO rival). F5-c is rival against rival and needs no
mirror: SvM covers seat B. Mirrors exist on the tuning split only; H6 is full
duels with both seat orders.

## 3. Splits

| Split | File | Contents | Who may read it |
| --- | --- | --- | --- |
| tuning | `evaluation/scenarios/tuning.json` | D1, B2, I3, F5: three starts each, plus a mirrored seat-B start for D1, B2, I3, F5-a and F5-b (23 starts) | anyone; used for dry runs, tuning and tests |
| held-out | `evaluation/heldout/H6.json` | H6: eight full-duel starts (H6-1 to H6-8), sixteen guard posts | **only the CLI, through the hash check.** OFF LIMITS to training, tuning, reward and prompt design |

Frozen file: `evaluation/heldout/H6.json`, SHA-256
`d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266`
(T08-fix1, decision #74). The first freeze, four starts, was
`44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`; it is
superseded. It never ran, so no held-out result is voided. H6-1 to H6-4 are the
first freeze unchanged.

**What "held out" means here (decision #75).** The claim is
"unseen start pairs and guard layouts", not "unseen cells". In short: start cells and guard post tuples are disjoint from
everything else; **patrol ranges are not**. A patrol is a stretch
of a ten-column corridor, and the default training patrols span columns 1 to 8 of
rooms 4 and 5, so some H6 patrols cover cells that training guards also covered.
No H6 configuration (both rival starts plus the guard layout) equals a training or
tuning configuration. Training used only the default arena guards, which sit in
rooms 4 and 5. The exposure of each H6 post to those training patrols is
generated by `tools/eval/exposure_table.py`, not written by hand: for the first
four starts, 5 of 8 posts are in rooms that had no guard in training, 2 lie
entirely inside a default patrol and 1 partly; H6-1 is the most training-like
start. For all eight starts the script gives: of 16 posts, 5 lie entirely inside
a default patrol, 1 partly and 10 not at all; H6-1 is training-like (both posts
full), H6-3, H6-6, H6-7 and H6-8 are partly training-like, H6-2, H6-4 and H6-5 are
unseen layouts. T09 reports the result **per start** and labels the most training-like
starts, so a reader can see whether a result rests on them.

Disjointness, enforced by tests (`tests/test_eval_registry.py`,
`tests/test_eval_t08fix1_h6.py`):

- no H6 start cell (room, row, column, any seat) is a start cell of the eight
  `TUNING_STARTS` in `tools/rl/env.py`, of any tuning scenario (mirrors
  included), or of the default arena starts;
- no H6 guard post tuple is a tuning-scenario post or a default arena post
  (the tuple, not the cells it covers);
- no H6 rival starts inside the patrol of a guard of its own start;
- the two rivals of an H6 start are in different rooms;
- `agents/rl/**` and `tools/rl/**` never mention `heldout` or `evaluation/` and
  never import `evaluation`; neither do `pop/`, `agents/`, `render/`, `server/`.

**H6-4's B start (decision #60).** The candidate in `orch/wip-T08` put B at
(1,2,3,+1), which is the A start of tuning pair 2. The rule, written before the
cell was chosen and independent of any policy result: keep B's room and row,
scan right from the old column, and take the first floor cell that no tuning
start, no other H6 start and no H6-4 guard patrol uses. Column 3 is a tuning
cell; column 4 is free, so B starts at (1,2,4,+1). The tuning scenarios'
cells were chosen the same way against the H6 cells.

### 3.1 Selection rule for H6-5 to H6-8 (decision #74, T08-fix1)

Saad (decision #74) chose to extend H6 from 4 to 8 starts (16 duels with seats
swapped) before the one held-out run. H6 has never been run, so the new hash
voids no result. **This rule was committed before any new start was added.**
It uses only the arena map and the lists of cells already in use. It never
reads a policy, a baseline, a result row or a checkpoint, and no new start may
be chosen, kept or dropped because of how any controller plays it.

Inputs: rooms 1 to 6 of arena A; the eight `TUNING_STARTS`; every start cell
and guard post of every tuning scenario (seat-B mirrors included); the arena's
default `STARTS` and `GUARD_POSTS`; and H6-1 to H6-4 exactly as frozen at
SHA-256 `44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`.

Definitions. `H(s)` is the lowercase hexadecimal SHA-256 of the ASCII string
`s`; candidates are ordered by `H` ascending (string comparison). A *floor
cell* is a cell of row 2 (the corridor row, where every existing start is)
that `evaluation.spec` accepts as walkable. Used cells `U` are the rival
start cells of all inputs above; used posts `P` are their guard-post tuples
`(room, row, (first col, last col))`.

1. Rival cell candidates: every floor cell of rooms 1 to 6 not in `U`, ordered
   by `H("h6x|cell|<room>|<row>|<col>")`.
2. For k = 5, 6, 7, 8 in turn: seat A takes the first candidate not yet taken;
   seat B takes the first candidate not yet taken **in a different room**.
   (Both rivals start in different rooms, GDD 5.3.) Both cells then count as
   used. Facing is toward the middle of the room: +1 if the column is 4 or
   less, otherwise -1. Hearts 3, no disguise, no forced seat.
3. Guard post candidates: room 1 to 6, row 2, a span of 2 to 4 columns
   `(c0, c1)` with every cell a floor cell, whose tuple is not in `P` and which
   contains neither rival cell of this start. Ordered by
   `H("h6x|post|<room>|<c0>|<c1>")`. Guard 1 takes the first candidate; guard 2
   takes the first candidate in a **different room**; both tuples then join `P`
   (so later starts cannot reuse them). Facing is +1 if the first byte of
   `H("h6x|face|<room>|<c0>|<c1>")` is even, else -1. Names are `h6<k>-g1` and
   `h6<k>-g2`.
4. Check, and fail the build rather than adjust: every new rival cell is
   outside `U`; no new post tuple is in `P`; no new start repeats a training or
   tuning configuration (both starts plus guard layout).

The rule is implemented in `tools/eval/select_heldout_starts.py` and tested in
`tests/test_eval_t08fix1_h6.py`, which regenerates H6-5 to H6-8 from H6-1 to
H6-4 and the lists above and compares them with the frozen file.

## 4. Freeze rule

1. `H6.json` is committed once and never edited. The CLI recomputes its
   SHA-256 and refuses to run on any difference (a missing file also refuses).
2. A change needs a new hash, a new commit and a note here, and voids every
   earlier held-out result.
3. **Run once per (weights, engine commit) (decision #64).** A real held-out run
   first appends a line to `evaluation/heldout/ledger.jsonl` (status `claimed`;
   keyed by the weights SHA-256, or by the scripted source hash for scripted-only
   runs, together with the engine commit), then runs. A second run for the same
   pair is refused. The same weights on a new engine commit are allowed: a re-run
   after a rule change is possible but visible, because both lines stay in the
   ledger and are reported. An aborted run still used its claim. A real run is
   also refused on an **unknown commit** or a **dirty tree** (any tracked change,
   or an untracked file under `evaluation/` or `tools/eval/`; the ledger files
   themselves do not count), so the commit in the key names the code that ran.
   Every refused attempt is recorded in `evaluation/heldout/refusals.jsonl`
   (status `refused`, the reason, the commit); a refusal claims nothing.
4. A held-out dry run (`--dry-run --split heldout`) uses WAIT seats on both
   seats, writes no ledger line and refuses any policy configuration.
5. MvM is test only and is refused on the held-out split.
6. T08 and T08-fix1 ran no policy on H6 (WAIT or scripted seats with a frame cap
   and a temporary ledger, for schema tests only). T09 runs it once, after
   T08-fix1 and T19.

## 5. Runner policy (decision #24) and result rows

- **Fresh controllers per trial**, built for that trial only. One controller
  per worker and seat; seats never share an instance (the runner refuses it).
  A controller reported busy (an earlier call timed out and has not returned)
  makes the row a **harness error**: `harness_error: true`, `aborted: true`,
  `abort_reason: "harness_error:busy"`. It is not a quiet result.
- **Secret `seed_key`**: `--make-seed-key PATH` writes
  `secrets.token_bytes(32)` as 64 hex characters, mode 0600, never overwrites.
  A real run needs `--seed-key-file`; keys under 32 bytes are refused. The key
  is never written to a result or trace, only a short id. A dry run uses a
  public key and says so (`seed_key_id: dry-run-public`).
- **Aborted runs are reported**, never dropped: a runner cap (`max_frames`,
  `max_fallbacks`), a harness error or an exception each give a row with
  `aborted: true` and the reason. They count in the denominator as "not a
  success, not a win".
- **Row fields**: scenario, start id, seed, commit (and `dirty`), controller
  names, versions and weights hash, seat (`controllers.A/B`, `subject_seat`,
  `outcome.result_A/B`, `outcome.result_subject`),
  outcome, termination, success flag and reason, metrics, invalid, stale,
  replaced and fallback/busy/timeout counts, decisions, measured latency
  (`time.perf_counter`), trace paths, forced stand-ins, `seed_key_id`.
- **Two-seat traces**: `traces/<scenario>/<start>/<config>-t<n>/` holds
  `seat-A.jsonl`, `seat-B.jsonl` (one line per decision, with the seat's
  observation and legal-list hashes) and `meta.json`. `--replay DIR` re-feeds
  the recorded inputs and compares the final snapshot hash with the trace and
  the meta file (exit 0 equal, 1 different). The split to replay against is read
  from `meta.json`, so a held-out trace needs no `--split` flag.

### Configurations and seat swap

A configuration names the seat A and seat B controllers: SvS, MvS, SvM, MvM
(S scripted baseline, M PPO). MvS against SvM is the seat swap for a duel.
A scenario start that forces the other seat to a stand-in (`wait`, `decoy`) runs
only configurations whose letter for the forced seat is S. With the subject in
seat A that is SvS and MvS (SvM would repeat SvS and MvM would repeat MvS
exactly), so "M against S" means the PPO rival as the subject (MvS) against the
baseline as the subject (SvS), each against the same stand-in. With the subject
in seat B (the mirrored starts, decision #65) it is SvS and SvM. Seat B is also
covered in the rival-against-rival starts (F5-c and H6).

## 6. Comparison plan

1. Tuning dry run: `--dry-run`, SvS, every scenario. Plumbing only; the rows are
   labelled and are not evidence of play strength.
2. Tuning comparison: MvS and SvS on D1, B2, I3, F5 with the subject in seat A,
   SvM and SvS with the subject in seat B (the mirrored starts); F5-c also SvM.
   At least 3 trials per start and configuration.
3. Held-out (T09, once): `--split heldout --configs MvS,SvM`, seed key from
   `--make-seed-key`, at least 3 trials per start and configuration.
4. Analysis: `tools/eval/analyze_results.py results.json`.

### The pre-registered T09 bar (decision #77)

Written here before the held-out run. The PPO rival is called better than the
scripted baseline on H6 **only if it wins at least 14 of the 16 held-out duels
(7 of 8 per 4 starts) and there is no aborted duel.** The 16 duels are the 8 starts
with the seats swapped (MvS and SvM). A draw (time up) is not a win and an
aborted duel is not a win. Anything below the bar is reported as
**"not supported"**, with the full numbers: wins, draws, losses and aborted duels per
start, per seat and overall, with the Wilson intervals, and the most
training-like starts labelled. No other reading of H6 is a strength claim, and
the bar is not moved after the run.

### How much each size can show (95 % Wilson lower bounds, computed)

| Sample | Best case | Next |
| --- | --- | --- |
| 16 held-out duels (8 starts, seats swapped) | 16 of 16: 0.81 | 14 of 16: 0.64, 13 of 16: 0.57, 12 of 16: 0.51, 11 of 16: 0.44 |
| 8 outcomes (the superseded 4-start H6) | 8 of 8: 0.68 | 7 of 8: 0.53 |
| D1, B2, I3 scenario with 6 starts (3 plus 3 mirrored) | 6 of 6: 0.61 | 5 of 6: 0.44 |
| any scenario with 3 starts of one seat | 3 of 3: 0.44 | 2 of 3: 0.21 |

So three starts alone can never put a scenario's interval above 0.44, and
six starts not above 0.61; scenario rates are descriptive. The bar of 14 of 16
is stricter than the point where the lower bound first clears 0.5 (12 of 16);
that is the approved bar and it stays.

### Seeds are not independent trials

T07-run1 Evaluation E3 found that duels of one start pair gave identical results
across seeds: the baseline and the argmax policy are deterministic, and the
engine's RNG is rarely consulted. The analysis therefore reports, per condition
(scenario, start, configuration), the **rows run** and the **distinct final
snapshots**, and computes its rates and intervals over the distinct outcomes
(`n`), not over the rows (`n_rows`). Three trials of one start with one final
state are one trial. Independent evidence comes from distinct starts and the two
seats, not from seed repeats. With fewer than 3 distinct outcomes an interval is
printed but flagged `n<3`. A study that wants more independent trials adds
starts, which for H6 means a new frozen set.

### Win, draw, loss and mirrors

Win/draw/loss are reported per controller (M or S) over both seats, with the
split by seat A and seat B, 95 % Wilson intervals, and aborted rounds in the
denominator. A mirror match (the same kind of controller in both seats: SvS,
MvM) is **one trial**, reported as seat A wins, seat B wins and draws, never as
two controllers.

## 7. Plumbing requests (not done here; `pop/` is not ours to edit)

1. `ScenarioEpisode` (`evaluation/spec.py`) sets `kid.hp` and `disguised` on the
   duel's private rivals after every `reset`, and reads `_duel`. A public set-up
   hook on `VersusEpisode` (hearts, disguise, no change of rules) would remove
   that. T19 changes the engine now; the tests in `tests/test_eval_*.py` fail
   loudly if it moves.
2. `pop.versus_runner.snapshot` reads `_duel.snapshot()` when the episode has no
   public `snapshot`; the same request.

## 8. Not in this protocol

Playtests, reflections, balance numbers and any Student decision are Saad's.
This document changes no rule, number or approved criterion.

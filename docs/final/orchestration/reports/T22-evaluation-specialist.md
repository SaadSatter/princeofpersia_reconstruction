---
handoff_id: HO-T22-evaluation-specialist
task_id: T22
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-qa.md@2477843 (and docs/final/orchestration/reports/T22-tech-lead.md@73e6531; brief docs/final/orchestration/tasks/T22.md@9305b3e; decisions #87-#92, #24, #41, #43, #45, #46, #49, #55, #88 at 8892b7f)
source_branch: gate/T22-eval
source_commit: see the branch head (test commit 13fd62e; this report is committed after it)
reviewed_commit: 73e6531 (with QA's probes at 2477843)
verdict: ACCEPT WITH NOTES
---

# T22: Evaluation Specialist report (Gate 2)

Status: done. No training, no `--live`, no H6 run. Nothing under `agents/`, `pop/`, `server/`, `web/`, `tools/rl/` or `evaluation/` edited.

## Verdict
**ACCEPT WITH NOTES.** No leak reproduced; the knowledge boundary holds in all three front ends and in the
server payload; the weights are loaded by hash everywhere; honest labels hold except on the one legacy path
(#91, already decided). One **major** finding (EVAL-T22-1): the in-game seat hook drops the policy's `WAIT`
instead of submitting it, so the shipped rival does not play in the game exactly as it played in evaluation.
It is a small fix and must be in T22-fix1 before Gate 3. It does not change the headline (see impact below), so
it is not a REJECT.

## Work completed
Read the brief, decisions, TL and QA reports; read `agents/modes.py`, the `play.py`, `server/` and `web/bridge.py`
hooks, `server/rival.py`, `agents/rl/policy.py`, `pop/versus_runner.py`. Built the web bundle and inspected it.
Ran the AI seat through the runner and through the game hook and compared them. Measured latency and weight-load
time. Ran `play.py --mode ai` under the dummy driver and a server `Match` AI room for 1,200 ticks.

## Paths
New: `tests/test_eval_T22_parity.py` (2 pass, 2 strict xfail = EVAL-T22-1), this report. Scratch scripts are
outside the repository.

## Findings

### EVAL-T22-1 [major] The game drops `WAIT`; the evaluated rival submits it
`web/bridge.py` `SeatControllerRival.__call__` returns `None` for a controller answer of `WAIT` ("no input"), and
`agents/modes.py` `ModeRival` inherits that. `pop/versus_runner.py` instead submits the answer: `ep.step(seat, "WAIT")`.
In the engine these are different: `WAIT` is a legal action that stops what the seat was doing, while no input
leaves the previous input in force. Reproduction (`wait_probe`, in this report's session): an episode with one
`RIGHT` then a `WAIT` step every 6 frames ends in a different snapshot from the same episode without the `WAIT`
steps.
Consequence: the same weights, encoder, 6-frame cadence and macro expansion, against the same scripted seat A and
seed, give the same inputs up to the first `WAIT` and then diverge (first divergence at frame 30 in the raw list,
at frame 240 once `WAIT`s are filtered). Forwarding `WAIT` on the game's cadence reproduces the runner's final
snapshot exactly (`test_cause_is_wait_mapped_to_no_input`, seeds 0 and 3, passes), so the cadence, encoder,
macro expansion and weights are the same and `WAIT` mapping is the single cause. The strict xfail
`test_game_path_matches_runner_path_for_the_shipped_rival` will XPASS when it is fixed.
Impact measured: over 24 seeds the shipped rival beats the scripted baseline 24/24 on both paths
(`won:B` x24 each; the baseline in the game path is also affected by the same mapping, so this is a smoke
comparison, not a strength claim). So the effect is behavioural fidelity ("the rival you play is the rival we
evaluated"), not a visible collapse. Against a human, who moves differently, it is unmeasured.
The same mapping is old in the hosted bridge (T04), so it also affects the baseline in the hosted page; it was
never a problem before because the baseline was not what the evaluation reported.
Fix (for the Tech Lead, in `agents/modes.py`; no change to `agents/rl/`, `pop/` or the baseline): make `ModeRival`
return `"WAIT"` on a decision tick when the controller answers `WAIT` (and `None` between decisions), so the game
submits what the runner submits. Keep the failed-or-illegal answer path as "no input" plus a fallback record
(the runner substitutes `WAIT` there too, labelled; do the same and keep the label). Then drop the xfail.
Server `TimeLimitedRival` and the `Match` fallback counters need no change (a slow answer stays `None` and is
logged, #45, #49).

### EVAL-T22-2 [minor] Hosted page and pygame keep fallbacks only in memory / stdout
`ModeRival.fallback_log` is read by pygame (one stdout line at exit) and online (trace and server log, #49).
On the hosted page (Pyodide) nothing reads it, so a policy error there is counted but invisible. The labelled
`"source": "fallback"` entries exist; surfacing is the open question. Suggest: log to the browser console on the
page, nothing on screen (no decision needed). Also `ModeRival.reset` does not clear `fallback_log`; a pygame `R`
restart carries the previous duel's entries into the exit line. Cosmetic.

### EVAL-T22-3 [minor] Weights parsed per room inside the asyncio loop
Creating an AI room parses and hash-checks the 430 KB weights on the event loop. Measured here: 8.9 ms first,
6.2 to 6.4 ms after (QA saw ~40 ms cold). A burst of AI rooms delays other rooms' 12 Hz tick by at most about
half a tick; the cap is 50 rooms. Suggest caching the loaded `Net` (immutable) once per process after the hash
check, and `PolicyMacro`/`MacroController` per room as now. Not a blocker.

### EVAL-T22-4 [minor, observation] The pygame AI seat has no time budget
Decision #45 names the live server only. Measured per-decision latency of the shipped rival: median 0.04 ms,
p99 1.2 ms, max 1.3 ms over 200 decisions (1,200 ticks, ARENA, this Mac, **measured**) against 40 ms on the
server and 83 ms per tick. A budget in pygame is not needed for the shipped rival and would add a thread
and non-determinism to a local, scripted-input-reproducible path. Recommendation: no budget in pygame or the
page; keep the synchronous call and say so in `GAME_MODES.md` (it is already described in the TL report). The
Pyodide inference time is **not measured** (no browser here); the pure-Python MLP is CPython-in-WASM, perhaps
5 to 20 times slower than here (estimated, not measured), which would still be under one tick.

### EVAL-T22-5 [minor, observation] The start the player meets is a training start
The game plays `arena_episode`, which is `TUNING_STARTS[0]`, with the human in seat A and the rival in B. That
is in-distribution for the policy (trained on seat B in this start), so the game does not exercise a start the
policy never saw. Against human opponents the policy is out of distribution (trained against the scripted
baseline and its own mix); say so if the page or the report claims strength. The end screen and the docs make
no strength claim (checked).

## Judged against the brief's questions

**Knowledge boundary, every front end.** Holds. pygame: `modes.step_ai_seat` gives the rival
`ep.observe("B")` and `ep.legal_actions("B")` only; the human seat gets nothing from the rival. The rival
call receives fresh copies: I scribbled over the returned observation and legal list and the engine snapshot
was unchanged. Hosted page: the rival lives in the browser's CPython beside the full `Episode` (as in T04's
local mode); it is handed the same two arguments. That the page's Python process holds the episode is the
existing local-mode design, not new, and the page never shows the rival's identity or traps. Server: spy
tests (TL, QA) show the AI seat's input is exactly its own seat's observation and legal tuple. The observation
carries `minutes_left` among its keys; the encoder does not read it (T07/T08 gates, `RL_POLICY.md`), and the
shipped path uses the same `Encoder` as training. No seed, identity of the other rival, trap ownership, or
`GameState` reaches the policy: the only arguments are the observation and the legal tuple.

**Web bundle.** Built and listed (`tools/web/build.py`, 34 zip members). It carries `agents/{__init__,baseline,
macros,modes,versus_baseline}.py`, `agents/rl/` (stdlib policy, encoder, the weights file `ppo-run-1.json` whose
SHA-256 equals `SHIPPED_SHA256` and `manifest.weights_sha256`), `pop/` engine and `web/bridge.py`. It carries no
`tools/rl`, `evaluation/` (so no held-out file), `server/`, tests, docs or traces. `seed_key` appears only as a
parameter name in `pop/seats.py` and `pop/versus_runner.py`; no key value ships. Weights are public by design.

**Server-to-client boundary (`mode`, AI rooms).** The only new client-to-server field is the creator's `mode`,
validated against the shared list (`bad_mode` otherwise); extra create fields are ignored (QA probes). State
messages in an AI room hold exactly `draw hud outcome rival seat seat_view type` (TL, real sockets) and QA found
no seed, token, snapshot, owner, fallback, source, weights, hash or policy text in any server message. The rival
label is now sent on purpose (#88). Seat B's payload queue does not exist in an AI room.

**Fallback labelling and destination (#49).** Slow answer (`TimeLimitedRival.slow`), failed or illegal answer
(`SeatControllerRival.fallbacks`) and policy error (`policy_errors`) are three counters, logged server-side as
`{"source": "fallback", "seat": "B", "reason": ...}` and in the trace, never to client A, and a duel never
aborts on them (#49). Evaluation keeps #24's abort rule (the runner is untouched).

**0.04 s budget (#45).** `DEFAULT_BUDGET_S = 0.04`. Measured 1.3 ms worst per decision; a 1,200-tick server
`Match` AI duel gave 0 slow answers, 0 fallbacks. QA injected a 0.30 s policy: the 12 Hz loop was not stalled,
the answer was replaced by `WAIT`, and the fallback was logged, not sent. The worker is a daemon thread per
room and `close()` is called on `Match.close` and when a room is reaped.

**Weights inside the asyncio loop.** See EVAL-T22-3. The server also refuses to start on a wrong or missing hash
(`verify_shipped`), and a room cannot be made with a different file.

**Same behaviour in the game as in evaluation.** Same factory (`make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256)`),
same encoder, `decision_every` 6 (runner `frame % 6 == 0`; the hook's `tick % 6 == 0` from `reset`; they align
because both start at 0, and pygame `R` and the server rematch reset both), same macro expansion (the
`MacroController`), argmax inference. Same SHA `80e4a110...ba4c`. One difference: EVAL-T22-1 (`WAIT`).
Also: the runner seeds the controller with `controller_seed(seed, seat, seed_key)`; the policy ignores the seed
(`PolicyMacro.reset(seed)` takes none into account), so this has no effect.

**Honest labels (#88).** "AI Model (trained)" and "Baseline (scripted)" on the menu, HUD and end screen in
pygame, the page and rooms made with a mode. The one gap is the legacy `--rival baseline` default room
("AI rival: ..."): QA-T22-2, decided as #91, fix in T22-fix1. `--neutral` stays an opt-in. Pygame prints
the label next to the hearts and in the end line (read in code; the TL's screenshot shows it).

**Local run.** `SDL_VIDEODRIVER=dummy python play.py --mode ai --seed 3 --keys A:RIGHT,A:RIGHT,A:DRAW
--screenshot ...` exit 0. A `Match(rival="ai")` through the server's own `make_match` ran 1,200 ticks with
no slow answer and no fallback. Not run: a real window, a browser, Pyodide, two human clients.

## Eval-specific headings (role file)
Leak findings: none found. Probed: spy on the AI seat's arguments (pygame, bridge, `Match`); mutation of the
returned observation and legal list; the bundle's file list and text for seed, held-out, `tools/rl`,
`evaluation`, `server`; the server's state and status message keys and forbidden-key walk (QA, real sockets);
extra create-message fields; a second client claiming seat B; the `mode` value against the list.
Baseline fairness: unchanged by T22 (same `make_baseline`, same observation and legal tuple). The in-game
baseline is affected by EVAL-T22-1 in the same way.
Reward and training method: not touched; no training run was started; `agents/rl/` and `tools/rl/` are unchanged
by T22 (`git diff 74975e1..73e6531` lists neither).
Checkpoint reproducibility: the weights load only with the recorded SHA-256 in every front end, and a wrong or
missing file is an error everywhere (TL tests, QA probes, my bundle check).
Train / held-out separation: unchanged; the bundle holds no `evaluation/` and the game never reads it. The game
start equals `TUNING_STARTS[0]`; nothing was tuned against held-out data.
Evaluation validity and confounds: T22 produces no comparative evidence and none should be quoted from the
game. My 24-seed comparison is a smoke check on one start, seats not swapped, not a result.
Local inference performance: measured on this Mac (Darwin 25.5, CPython 3.13): decision median 0.04 ms, p99
1.2 ms, max 1.3 ms; weight load 6 to 9 ms warm (QA: ~40 ms cold). Pyodide: not measured.
Replay and fallback: the game's input stream is deterministic (TL: same seed and inputs give the same hash).
Replays of server traces use the inputs actually applied, so a dropped `WAIT` is replayed as dropped; after the
EVAL-T22-1 fix, traces will record `WAIT` inputs and must still replay (add a replay test in T22-fix1).
Fallbacks are labelled and counted (see above).
Training-run readiness: not applicable to T22 (no training requested).

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_T22_parity.py
2 passed, 2 xfailed in 1.15s

uv run --frozen --extra play --extra train --extra online pytest -q          (clean tree, 13fd62e)
1901 passed, 11 skipped, 8 xfailed, 2 warnings in 467.57s (0:07:47)
```
Relative to QA's run at 2477843 (1856 passed + QA's 43, 5 + 1 xfailed): +2 passed and +2 xfailed from my file;
1856 + 43 + 2 = 1901, 5 + 1 + 2 = 8. The 8 xfails are the 5 older ones, QA-T22-1 and my two EVAL-T22-1 cases.

## Proposed T22-fix1 list
1. #91: delete `legacy` in `server/__main__.py` `make_match`; update the one T13 test assertion to
   "Baseline (scripted)" (QA-T22-2).
2. #92: menu by default for a bare `python play.py`; the hosted page opens on a mode chooser; update the web
   smoke path (`tools/web/smoke.cjs`, `.github/workflows/web-smoke.yml`). Keep the old single-player reachable.
3. QA-T22-1: generate the `--mode` help text from `modes.MODES` (the strict xfail will XPASS; remove the marker).
4. **EVAL-T22-1 (required):** `ModeRival` submits `WAIT` as the runner does; remove the xfail in
   `tests/test_eval_T22_parity.py` (this is my file, so I will remove it in a re-review; or the Tech Lead may
   flip the marker, since it must XPASS). Add a test that a server trace with `WAIT` inputs replays to the
   same snapshot.
5. EVAL-T22-3 (optional, small): load and hash-check the weights once per process and share the immutable `Net`.
6. EVAL-T22-2 (optional): hosted page logs `fallback_log` to the console; `ModeRival.reset` clears the log.
7. When #92 changes the bare `play.py` and the page, keep the label and the "no strength claim" wording; do not
   add a win-rate figure to the menu or the end screen.
8. Docs: one sentence in `GAME_MODES.md` that the pygame and hosted AI seats call the rival synchronously
   (no time budget) and only the server has the 0.04 s limit, plus that the policy was trained against
   scripted rivals, so "AI Model (trained)" is a label, not a strength claim.

## Known limitations
No browser, window or two-human session. Pyodide latency not measured. The impact of EVAL-T22-1 against human
play is unmeasured. My comparison is 24 seeds on one start.

## Unresolved findings
EVAL-T22-1 (major, to T22-fix1); EVAL-T22-2 to 5 (minor); QA-T22-1 and QA-T22-2 carried over.

## Requested next action
Orchestrator: dispatch T22-fix1 with the list above (items 1 to 4 required), then a short Gate 1 and Gate 2
re-check (my parity file should go green), then Gate 3.

## Student decision required
none

---
handoff_id: HO-T22-fix1-evaluation-specialist
task_id: T22-fix1
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-fix1-qa.md@5ebf909 (and docs/final/orchestration/reports/T22-fix1-tech-lead.md@19dc355; brief docs/final/orchestration/tasks/T22-fix1.md@7bf5bef; my T22 report@0ff9d4a)
source_branch: gate/T22-fix1-eval
source_commit: see the branch head (test commit 60d9141; this report is committed after it)
reviewed_commit: 19dc355 (with QA's probes at 5ebf909)
verdict: ACCEPT
---

# T22-fix1: Evaluation Specialist report (Gate 2)

Status: done. No training, no `--live`, no H6 run. Only `tests/test_eval_T22_parity.py` (my own file) and this report were written.

## Verdict
**ACCEPT.** EVAL-T22-1 is closed: the in-game rival equals the evaluated rival, on the game hook and on the
server path. EVAL-T22-2 and -3 work. The two QA minors need no Gate 2 action; they may go to a T22-fix2
(contents at the end) and nothing in them blocks Gate 3. No leak, no boundary change, no strength claim.

## My test fix (author edit)
File: `tests/test_eval_T22_parity.py`, `test_game_path_matches_runner_path_for_the_shipped_rival[0,3]`.
Old:
```python
@pytest.mark.xfail(strict=True, reason="EVAL-T22-1: ...")
...
runner_b = [(r["frame"], r["input"]) for r in res["traces"]["B"]
            if r["input"] not in (None, "WAIT")]   # the game sends WAIT as "no input"
assert runner_b, "the rival never acted: the comparison would be vacuous"
assert runner_b == game_b
assert res["final_snapshot"] == snapshot(ep)
```
Why it could not pass: it filtered WAIT from the runner's list only. The game now (correctly) submits WAIT, so the
lists differ at the first WAIT (frame 30). I wrote it for the old behaviour. A WAIT-inclusive list comparison is
also not meaningful: the runner skips a seat with no legal action on a decision tick (no trace row), where the game
submits WAIT. The whole final snapshot is what proves the WAITs equal.
New (strict kept, xfail marker removed):
```python
runner_b = [(frame, input) for ... if input not in (None, "WAIT")]
game_acts = [(f, a) for f, a in game_b if a != "WAIT"]       # WAIT filtered from BOTH sides
assert runner_b, "the rival never acted: the comparison would be vacuous"
assert any(a == "WAIT" for _, a in game_b), "the game must submit WAIT (EVAL-T22-1)"   # new, anti-vacuity
assert runner_b == game_acts
assert res["final_snapshot"] == snapshot(ep)                 # unchanged
assert b.policy_errors == 0 and b.fallback_log == []         # unchanged
```
Result: 4 passed (2 cause tests, 2 parity). No other existing test edited.

## Findings and judgement

**EVAL-T22-1 closed: yes.** `ModeRival._answer` keeps `SeatControllerRival`'s cadence and checks and returns
`"WAIT"` on a decision tick and `None` between decisions. Measured (scratch script outside the repository; shipped
weights; 720 frames; ARENA; seat A the scripted baseline, seat B the shipped rival):
- game hook (`step_ai_seat`) against `VersusRunner`: final snapshot equal on **16 of 16 seeds** (0 to 15), 0 fallbacks.
- server path: `Match(rival="ai")` made through `server.modes.make_match`, one human joined and idle, 720 `_tick()`s
  with a 5 s budget: final snapshot equals the game hook with an idle A on **16 of 16 seeds**; fallback counters
  `(0, 0, 0)`. The server drives the rival through the same hook, so by transitivity it equals the runner. (A direct
  server-versus-runner comparison with an idle A written as a `WAIT` controller differs on every seed, because a
  `WAIT` step on the idle seat A is exactly what the engine treats differently from no input; it says nothing about B.)
- QA's probes (seeds 1, 2, 5), the TL's (0, 3) and the replay test with WAIT inputs also pass.

**The remaining difference (failed or illegal answer).** Game and server: no input plus a labelled fallback.
Runner: `WAIT`, and in evaluation the run aborts (#24). Does it matter? For the shipped rival, no. It happened on 0
of 16 seeds on the game path and 0 on the server path. The policy's own inference error is answered `WAIT` by the
policy itself, and that now goes through as `WAIT`. The difference exists only when the controller raises or answers
something illegal, which an evaluation aborts on anyway, so no evaluated number can depend on it. Aligned? **No change
needed.** "No input" lets a held input stay in force for up to 6 frames until the next answer, while `WAIT` stops it;
neither is the evaluated behaviour on an error, because the evaluation has none. The server's late answer is the
same class (`TimeLimitedRival` returns `None`; its comment says "WAIT", stale wording, harmless). If Saad prefers one
rule, "errors and late answers are WAIT, still labelled" is a small change, but it is a live-play design choice, so
I leave it to him. `GAME_MODES.md` already states the present rule.

**EVAL-T22-3 (cache) works.** `_shared_net` loads and hash-checks once per process; each room gets its own
`PolicyMacro` and controller. A wrong hash raises cold and warm and is not cached (QA probes; TL test of one
`load_net` for three controllers). `load_net` measured 6.5 ms here, now paid once.

**EVAL-T22-2 works.** `reset` clears `fallback_log` and counters (tested). `web/main.js` `reportFallbacks` writes only
`console.warn("AI seat fallback (source: fallback)", entry)`, through a guarded Python helper. It never writes to
the page text, the draw list or the server payload (`tick_json` and server messages carry no fallback field, tested).
Not run in a browser (no Pyodide here), so the console line and `smoke.cjs` are unverified at runtime; the code is
read and the Node harness passes.

**QA-T22fix1-1 (cache key): no fix needed for Gate 3.** A same-size edit with the mtime restored is served from the
cache without a new hash check. That needs a writer on the process's file system after start; `verify_shipped()`
already hashed the file at server start; the shipped file is read-only in the build; the policy is not secret. The
weights are still loaded only with their recorded SHA-256, at load time. If a cheap fix is wanted anyway: read the
bytes and compare their SHA-256 on every call (0.32 ms measured, against 6.5 ms for the parse) and use the digest, not
mtime and size, as the cache key. That makes QA's strict xfail probe pass, and QA then drops the marker.

**QA-T22fix1-2 (stale docs row): confirmed, documentation only.** `docs/final/WEB_BUILD.md`, the `?mode=ai` row, still
says the baseline is labelled "AI rival: versus-baseline (scripted)". The page passes `honest=true`, so it shows
"Baseline (scripted)".

**Boundaries unchanged.** `git diff 0ff9d4a..5ebf909` touches nothing in `pop/`, `agents/rl/`,
`agents/versus_baseline.py`, `web/bridge.py`, `tools/rl/` or `evaluation/`. The AI seat still gets only
`observe(seat)` and `legal_actions(seat)` (spy tests pass); the new code reads no seed, identity, snapshot or
held-out data. The shared `Net` is not mutated by `Net.logits` or `Net.act` (read; QA: 240 ticks leave it unchanged).
Server to client: `server/match.py` had a comment edited; `server/__main__.py` only lost the `legacy` branch; the
state message keys are unchanged (QA, real sockets). The chooser adds no message field; it navigates with
`?play=<id>`. The console log is the page's own local process and carries the AI seat's own labelled entries only.

**Strength claims.** None. A search for win rate, stronger, beats and unbeaten across `render/`, `web/main.js`,
`web/bridge.py`, `agents/modes.py`, `play.py` and `GAME_MODES.md` finds only the sentence that says no win rate
appears and that the T09 comparison was not supported. "AI Model (trained)" is a label.

## Eval-specific headings
Leak findings: none. Probed: trace and snapshot parity on the game and server paths; the payload for fallback fields;
the seat's arguments (TL and QA spies).
Baseline fairness: unchanged. The in-game baseline now also submits WAIT as the runner does (the old mapping affected it too).
Reward, training, reproducibility, held-out separation: untouched (nothing under `agents/rl/`, `tools/rl/`,
`evaluation/` changed; the weights hash `80e4a110...ba4c` is unchanged and still checked).
Evaluation validity: no comparative evidence produced; my 16-seed check is equality of traces, not strength.
Local inference latency: not re-measured (median 0.04 ms, p99 1.2 ms in my T22 report). Pyodide: not measured.
Replay fidelity: a server trace with WAIT inputs replays to the same snapshot (TL test, passes).
Fallback: labelled `"source": "fallback"`, counted, never sent to the other seat, console-only on the page.
Training-run readiness: not applicable.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_T22_parity.py
4 passed in 1.09s

uv run --frozen --extra play --extra train --extra online pytest -q -p no:cacheprovider    (clean tree, 60d9141)
1998 passed, 11 skipped, 7 xfailed, 2 warnings in 430.07s (0:07:10)
```
Against QA's 1996 passed, 9 xfailed: +2 passed and -2 xfailed (my two parity cases). The 7 xfails are the 5 older
ones and QA's two strict findings (QA-T22fix1-1, -2).

## Proposed T22-fix2 (small; none of it blocks Gate 3)
1. Doc: `docs/final/WEB_BUILD.md` `?mode=ai` row: "Baseline (scripted)" instead of "AI rival: versus-baseline (scripted)". QA's strict xfail then passes; QA removes the marker.
2. Optional: `agents/modes.py:_shared_net` keyed on the SHA-256 of the file bytes (read and hash per call). QA removes its marker.
3. Optional: the `# WAIT` comment in `server/rival.py` (it returns `None`).
If the orchestrator would rather not open a fix2, record QA-T22fix1-1 and -2 as accepted notes and go to Gate 3.

## Known limitations
No browser, window, Pyodide or two-human session; the hosted chooser, `smoke.cjs` and the console log are untested at
runtime. Parity is on one start (ARENA, `TUNING_STARTS[0]`), seats not swapped, 720 frames.

## Unresolved findings
QA-T22fix1-1 and -2 (minor). Nothing else.

## Requested next action
Orchestrator: Gate 3 (after T20 closes), or the small T22-fix2 above first.

## Student decision required
none

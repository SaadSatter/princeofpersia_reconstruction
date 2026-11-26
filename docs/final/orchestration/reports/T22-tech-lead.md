---
handoff_id: HO-T22-tech-lead
task_id: T22
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T22.md@9305b3e
source_branch: task/T22
source_commit: 2c70380
reviewed_commit: n/a
verdict: n/a
---

# T22: tech-lead report

Status: done (one flagged deviation, below: the `--rival baseline` default room keeps its old label)

## Work completed
One mode list (`agents/modes.py`: `ai` "AI Model (trained)", `baseline` "Baseline (scripted)", `human`
"Human vs Human") is read by all three front ends. pygame: `--menu` (start menu) and `--mode ai|baseline|human`.
Hosted page: three mode buttons built from `manifest.json`, the stdlib policy and shipped weights in `game.zip`.
Online server: the room creator picks the mode; `--rival ai` added. Tests first (commit `a07ca95`), then the
implementation (`2c70380`), then this report.

## Paths
New: `agents/modes.py`, `render/menu.py`, `server/modes.py`, `tests/test_t22_{modes,pygame,server}.py`,
`docs/final/GAME_MODES.md`, `docs/agent-sessions/T22-game-modes.md`.
Hooks: `play.py` (`menu_entries`, `ai_key_names`, `versus_main(args, rival)`, `mode_main`, three flags),
`web/bridge.py` (`make_game(..., honest)`, `rival="ai"`, `rival_label`), `web/{keys,main,online}.js`,
`web/{index,online}.html`, `server/{app,match,__main__}.py`, `tools/web/build.py`.
Docs: `RL_POLICY.md` ("In the game"), `ONLINE_PLAY.md`, `WEB_BUILD.md`.
No existing test was edited. `pop/`, `agents/rl/`, `tools/rl/`, `pyproject.toml`, `uv.lock`, `README.md` untouched.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Same three modes and labels in all front ends, one source | yes | `test_t22_modes.py` (list, manifest `modes`, pages read `manifest.modes` and hold no label text), `test_t22_pygame.py::test_the_menu_offers_the_one_mode_list_in_order`, `test_t22_server.py::test_the_server_accepts_exactly_the_shared_mode_list` |
| 2 | AI mode loads shipped weights by hash, refuses a wrong hash, no silent baseline | yes | `test_ai_mode_loads_...`, `..._refuses_a_wrong_hash_...`, `..._missing_weights_...`, bridge and pygame (`rc == 2`, no screenshot) and server start (`SystemExit`) variants, bundle variant (unpacked `game.zip` refuses a patched hash) |
| 3 | AI seat gets only its own observation and legal tuple (spy); fallback labelled | yes | `Spy` test for `ai` and `baseline` (`obs == ep.observe("B")`, legal tuple equal); `fallback_log` entries `{"source":"fallback","seat":"B"}` for a failed answer and for a policy error |
| 4 | Online AI room sends only the seat's payload; budget or logged fallback | yes | `test_an_ai_room_sends_nothing_beyond_its_own_seat_payload` (allowed-key set, forbidden-key walk, no seat-B queue); budget constant 0.04 asserted; slow-controller and policy-error tests end in trace fallbacks `"source":"fallback"` never sent to A |
| 5 | pygame `--mode` starts the right controllers; menu uses the game palette | yes | `made` spy: `ai` -> `["ai"]`, `baseline` -> `["baseline"]`, `human` -> `[]`; menu keys choose the same; pixel set of the menu subset of `render.menu.PALETTE` which is a subset of `render/draw.py` constants |
| 6 | Web: bundle has weights with right hash; bridge picks controller per mode | yes | `test_the_bundle_holds_the_weights_...` (zip member hash == `SHIPPED_SHA256`, `manifest.weights_sha256`), bridge label/controller kind per mode, unpacked bundle plays 120 ticks in a clean interpreter |
| 7 | Deterministic AI-mode duel with scripted input | yes | `_duel` twice, same final `state_hash` and input counts, for `ai` and `baseline`; bridge duel; pygame `--keys` run twice gives byte-identical screenshots |
| 8 | Suite green; `uv lock --check` | yes | below; `uv lock --check`: "Resolved 27 packages" (no change) |
| 9 | Manual run | partly | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1856 passed, 11 skipped, 5 xfailed, 2 warnings in 401.08s (0:06:41)
```
Base `74975e1` (same command, run in this worktree before any T22 test or code):
`1805 passed, 11 skipped, 5 xfailed, 2 warnings in 306.17s`. +51 passed = the new T22 tests; no failure, no new skip.
An earlier run with an uncommitted tree showed 7 failures (3 are the "real held-out run needs a clean tree"
guards; the others were mine and are fixed, see Findings); the last run is on a clean tree at `2c70380`.

Run by hand (all under `SDL_VIDEODRIVER=dummy` or on localhost, nothing left running):
- `play.py --mode ai --seed 3 --keys A:RIGHT,A:RIGHT,A:DRAW --screenshot ...`: exit 0; I looked at the screenshot:
  one panel, hearts, line "you (A) vs AI Model (trained)   hearts 3".
- `play.py --menu --menu-keys down,return`: exit 0 (starts Baseline). Rendered the menu to a PNG and looked: gold title,
  three stone rows, selected row lighter, hint line.
- `python -m server --host 127.0.0.1 --port 8791`, one scripted websocket client per mode with `create` + `mode`:
  `ai` -> state label "AI Model (trained)", 74 states in 6 s, status `playing`; `baseline` -> "Baseline (scripted)";
  `human` -> `waiting`, no rival field; `bogus` -> `bad_mode` error. State message keys were exactly
  `draw hud outcome rival seat seat_view type`.
- Policy latency over 600 ticks of an arena duel: max 1.2 ms, p99 0.9 ms (budget 40 ms). Seat B decides once per 6 ticks.

Could not run: a real window (pygame on a display), a real browser (index.html with Pyodide and Phaser, online.html
lobby buttons, the new JS in a browser; Node unit tests and the main.js harness pass, `tools/web/smoke.cjs` not run),
`--live`, training, the H6 run, two concurrent human clients.

## Findings
- [needs a decision] `server/__main__.py`: `--rival baseline` with no creator-chosen mode keeps the T13 label
  "AI rival: ..." because `tests/test_gate_t13_qa_online.py::test_cli_process_two_scripted_clients_real_clock_and_trace_dir[baseline]`
  asserts it, and I may not edit an existing test. Everything else is honest (#88): rooms with a chosen mode, `--rival ai`,
  the hosted page, pygame. To finish #88 for that path: delete the `legacy` variable in `make_match` and update that one
  test. Not done here on purpose.
- [fixed in my own tests] first drafts broke `tests/test_frontend.py::test_render_reads_observations_only` (render/ must not
  import `agents`, so `render/menu.py` takes entries from the caller), `test_main_js_reads_only_what_the_payload_has`
  (main.js harness has no `createElement`, so the mode links are one `innerHTML` string and tolerate a missing element or list),
  and `test_the_page_cannot_choose_or_learn_the_rival_kind` (no `agents/` text in `online.js`).

## Known limitations
- The menu is reached with `play.py --menu`; plain `python play.py` still starts the single-prince S3 as before.
  `--mode`/`--menu` always play the ARENA (they set the situation).
- The bare hosted page is Baseline (scripted), as before (so `tools/web/smoke.cjs` is unaffected); AI Model is `?play=ai`.
- `ModeRival` is a subclass built inside `agents.modes._rival_class()` (lazy import of `web.bridge` so `agents` does not
  import `web` at load). `agents/modes.py` imports `web.bridge` at call time; that direction is unusual but the zip ships both.
- Online: the creator's `mode` is the only new client-to-server field; the AI seat's kind is now shown by label (#88), not hidden.
  Docs say so (the old "cannot learn the AI seat's kind" sentence is replaced).
- pygame AI seat is called synchronously (inference about 1 ms); the 0.04 s `TimeLimitedRival` is the server's only.
- The hosted bundle grows by the 430 KB weights file; PPO weights are loaded in the browser by CPython-in-Pyodide
  (pure-Python MLP, 251-64-64-9); load time in Pyodide not measured.
- Human vs Human on the hosted page links `online.html`, which exists only on a server run with `python -m server`.

## Unresolved findings
The one deviation above.

## Requested next action
Commit to review: 2c70380 on task/T22 (this report is committed after it)
What changed: three modes from one list in pygame (menu, `--mode`), the hosted page (buttons, trained rival in the bundle)
and the online server (creator picks, `--rival ai`); honest labels; human seat reads both key sets against an AI; docs.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t22_modes.py
tests/test_t22_pygame.py tests/test_t22_server.py`; `play.py --mode ai` / `--menu`; `python -m server --rival ai`;
read `agents/modes.py` first, then the hooks in `play.py` (`versus_main`, `mode_main`), `web/bridge.py`, `server/match.py`.
What I am unsure about: the `legacy` label deviation; Pyodide load time and the browser path (never run in a browser);
whether the menu should also appear for a bare `play.py` (a choice for Saad); the `Match.honest` flag kept so old tests
still pass (an alternative is to make honest the only behaviour and update the two old label tests); the pygame
screenshot determinism test compares PNG bytes (stable here, same machine).
Touches the knowledge boundary or AI seat: yes (Gate 2 applies: AI seat in three front ends, server-to-client payload, fallbacks)
Merge note: `play.py` hooks are one block in `versus_main` plus `mode_main` and three flags; `server/` hooks are in `app.py`
(`_create`), `match.py` (rival values, third fallback counter), `__main__.py` (`make_match`). Expect conflicts with T20 only
if it edits those lines.

## Student decision required
none

---
handoff_id: HO-T22-fix1-tech-lead
task_id: T22-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T22-fix1.md@7bf5bef
source_branch: task/T22-fix1
source_commit: e494c7a
reviewed_commit: n/a
verdict: n/a
---

# T22-fix1: tech-lead report

Status: partial. Every fix is in. One existing test I may not edit fails because of #91 (details below, needs an authorisation), and the two Eval parity cases cannot lose their xfail with a marker-only edit.

## Work completed
Base `0ff9d4a` (`gate/T22-eval`). Failing tests first (`c3d41ec`), fixes (`e494c7a`), this report. The base's suite line is the Evaluation Specialist's at 13fd62e (the base adds only its report): `1901 passed, 11 skipped, 8 xfailed, 2 warnings in 467.57s`. I did not re-run the base.
1. EVAL-T22-1: `ModeRival` (`agents/modes.py`) submits the controller's `WAIT` as `"WAIT"` on a decision tick and `None` between; failed or illegal answers stay `None` plus a `"source": "fallback"` entry. `agents/rl/`, `pop/`, the baseline untouched. A server trace with WAIT inputs replays to the same hash. Game path vs runner path for the shipped rival: same non-WAIT inputs and the same final snapshot, seeds 0 and 3.
2. #91 / QA-T22-2: the `legacy` variable and `honest=not legacy` are gone from `server/__main__.py`; `--rival baseline` shows "Baseline (scripted)".
3. #92: bare `python play.py` opens the menu. `play.py S3` (a named situation) and the new `--classic` flag keep the single-prince level; `--versus`, `--watch`, `--replay`, and scripted `--keys`/`--screenshot` without `--menu-keys` also keep the old behaviour. Hosted page: `SMKeys.needsChooser(search)` (true unless `play=`, `mode=` or `rival=` is present); `main.js` then shows the three mode buttons, starts neither Pyodide nor Phaser, and marks no mode as current. `tools/web/smoke.cjs` now waits for the chooser, checks it lists 3 modes, clicks Baseline, then runs its old checks. `.github/workflows/web-smoke.yml` unchanged (not needed).
4. QA-T22-1: the `--mode` help is built from `modes.MODES`; I also removed label text from a `server/match.py` comment and my own docstrings, so no file but `agents/modes.py` spells a label.
5. EVAL-T22-3: `agents.modes._shared_net` caches the loaded, hash-checked `Net` per process, key = (resolved path, sha, mtime_ns, size); a different path, hash or changed file is checked again. Each room still gets its own `PolicyMacro` and controller. The controller is built as `policy.make_rl_rival` builds it (same classes, name, kind, cadence); the parity test shows an identical result.
6. EVAL-T22-2: `ModeRival.reset` clears `fallback_log`. `web/main.js` reads `game.rival.fallback_log` (through a small guarded Python helper, so a stub or older build reports nothing) every 12 frames and `console.warn`s new entries, labelled "AI seat fallback (source: fallback)". Never in the page text or to the other seat; `web/bridge.py` untouched.
7. Docs: `docs/final/GAME_MODES.md` (synchronous AI seat with no budget except the server's 0.04 s, "AI Model (trained)" is a label not a strength claim, no win rate anywhere, WAIT, fallbacks, weights cache, menu by default, chooser), plus one sentence each in `ONLINE_PLAY.md` (label) and `WEB_BUILD.md` (bare page).

## Paths
Changed: `agents/modes.py`, `play.py`, `server/__main__.py`, `server/match.py` (one comment), `web/keys.js`, `web/main.js`, `tools/web/smoke.cjs`, `docs/final/{GAME_MODES,ONLINE_PLAY,WEB_BUILD}.md`. New: `tests/test_t22fix1_modes.py`, `tests/test_t22fix1_server_play.py`, `docs/agent-sessions/T22-fix1.md`, this report. Existing tests edited: below. Not touched: `pop/`, `agents/rl/**`, `agents/versus_baseline.py`, `tools/rl/**`, `evaluation/**`, `web/bridge.py`, `.github/`, `pyproject.toml`, `uv.lock`.

## Existing tests edited (authorised ones only)
| Test | Old | New |
| --- | --- | --- |
| `tests/test_gate_t13_qa_online.py` (CLI two clients, `[baseline]` case, one line) | `assert any("AI rival" in str(m.get("rival")) for m in states)` | `assert any("Baseline (scripted)" in str(m.get("rival")) for m in states)` |
| `tests/test_qa_T22_probes.py::test_no_file_but_agents_modes_spells_a_mode_label` | `@pytest.mark.xfail(strict=True, reason="QA-T22-1 ...")` | marker removed; it passes |
| `tests/test_eval_T22_parity.py` | strict xfail on `test_game_path_matches_runner_path_for_the_shipped_rival[0,3]` | not edited (see Findings) |

The web smoke test is `tools/web/smoke.cjs` (a path the brief permits), described in item 3.

## Acceptance criteria -> evidence
| # | Item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | EVAL-T22-1 | yes | `test_t22fix1_modes.py`: decision-tick WAIT, failure and illegal answers, a policy WAIT is not a fallback, server-trace replay with WAIT (asserts WAIT is present), parity with the runner for seeds 0 and 3 (inputs and whole snapshot) |
| 2 | #91 | yes | `test_the_server_cli_has_no_legacy_label_path`; the edited T13 `[baseline]` CLI test passes against a real subprocess |
| 3 | #92 | yes (Python and Node side) | bare-menu tests (Esc quits; Down+Enter starts baseline), `--classic` gives the same screenshot bytes as `S3`, `needsChooser` on 11 query strings in Node, chooser and smoke static checks, the T14 main.js Node harness unchanged and green |
| 4 | QA-T22-1 | yes | the probe, no longer xfail, passes |
| 5 | EVAL-T22-3 | yes | one `load_net` call for three controllers; a wrong hash still raises after the cache is warm |
| 6 | EVAL-T22-2 | yes | `reset` clears the log; main.js static check; the payload carries no `fallback_log` |
| 7 | Docs | yes | `GAME_MODES.md`, section "What the AI seat is, and what it is not" |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q -p no:cacheprovider
FAILED tests/test_qa_T22_probes.py::test_label_honesty_is_missing_only_on_the_legacy_default_room_path
1 failed, 1933 passed, 11 skipped, 7 xfailed, 2 warnings in 411.62s (0:06:51)
```
Run on the tree at `e494c7a` (the only later changes are this report and the agent-session note, both docs). The 7 xfails are the 5 older ones and the 2 Eval parity cases; QA-T22-1 is no longer one (8 to 7).

## Findings
- [needs an authorisation] `tests/test_qa_T22_probes.py::test_label_honesty_is_missing_only_on_the_legacy_default_room_path` asserts that the source line `legacy = mode is None and args.rival == "baseline"` is in `server/__main__.py`. Deleting `legacy` (#91) makes it fail by design. It is not in the authorised list, so I did not edit it, and I did not keep dead code to satisfy it. Suggested edit (QA owns the file): replace that `src` assertion with `assert "legacy" not in src`; the `make_game(..., "baseline").rival_label is None` class-default line is still true.
- [needs a decision] `tests/test_eval_T22_parity.py::test_game_path_matches_runner_path_for_the_shipped_rival` cannot XPASS with a marker-only edit. It filters WAIT out of the runner's list (`not in (None, "WAIT")`) but not out of the game's, and the game now correctly includes WAIT, so its list comparison fails at frame 30. I left the strict xfail in place so the suite stays honest. The same comparison (WAIT filtered from both sides, plus the whole final snapshot, plus "the game submitted WAIT") passes in `test_t22fix1_modes.py::test_game_path_equals_runner_path_for_the_shipped_rival_wait_included`. The runner's trace does not list every frame (on seed 0 it skips frames 444 and 450, where the game submits WAIT), so a WAIT-inclusive list comparison is not meaningful. Eval owns that file: filter both sides, drop the marker.
- [observation] A failed or illegal answer is still `None` plus a labelled fallback, as the brief says. The runner substitutes WAIT there (and aborts in evaluation, #24). The game does not abort. This is the only remaining difference between the paths and applies only to errors.
- [observation] A bare `play.py` with `--screenshot` or `--keys` (and no `--menu-keys`) keeps the single-player level, so old scripted checks do not wait on a menu.

## Run by hand / could not run
Run: the bare menu and `--classic` through `play.main` under the dummy driver (in the tests); a real `python -m server` subprocess with two scripted clients (the T13 `[baseline]` test); the main.js Node harness; the weights cache; the shipped policy through the runner and through the game for 720 frames on two seeds. Could not run: a real window, a real browser (Pyodide, Phaser, the chooser click flow in `smoke.cjs`, the console log of fallbacks), `--live`, training, the H6 run, two human clients. `smoke.cjs` was not run against a page.

## Known limitations
- The chooser, the smoke change and the console fallback log are untested in a browser. The `fallback_json` helper runs only in Pyodide.
- The loaded network is shared by reference. `Net.logits` and `Net.act` do not mutate it (read from the code), but nothing enforces that.

## Unresolved findings
The two items under Findings that need an authorisation or an Eval edit.

## Requested next action
Commit to review: e494c7a on task/T22-fix1 (this report and `docs/agent-sessions/T22-fix1.md` are committed after it)
What changed: WAIT submitted as in the runner; honest server label; menu by default; hosted chooser; shared net; fallback log reset and console; help text from the list; docs.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t22fix1_modes.py tests/test_t22fix1_server_play.py tests/test_qa_T22_probes.py tests/test_eval_T22_parity.py tests/test_gate_t13_qa_online.py`; `python play.py` (menu), `python play.py --classic`; `node tools/web/smoke.cjs` against a built `web/dist` (needs Playwright; not run).
What I am unsure about: the browser path end to end; the two test edits above; whether `needsChooser` should also treat `seed=` or `seat=` as a choice (I chose no, they pick no mode); the mtime-keyed cache (a file edited within the same ns and size would be missed).
Touches the knowledge boundary or AI seat: yes (Gate 2 applies: WAIT submission by the AI seat, weights cache, fallback surfacing)

## Student decision required
none

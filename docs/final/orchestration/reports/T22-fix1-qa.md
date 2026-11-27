---
handoff_id: HO-T22-fix1-qa
task_id: T22-fix1
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-fix1-tech-lead.md@19dc355 (brief docs/final/orchestration/tasks/T22-fix1.md@7bf5bef)
source_branch: gate/T22-fix1-qa
source_commit: see the branch head (tests tests/test_qa_T22fix1_probes.py, probe update in tests/test_qa_T22_probes.py; this report is committed after them)
reviewed_commit: 19dc355
verdict: ACCEPT WITH NOTES
---

# T22-fix1: QA report (Gate 1)

Status: done. Verdict: ACCEPT WITH NOTES. No blocker or major finding. Two minor findings, both with strict xfail probes.

## Suite (clean committed tree at cd6f7fc = 19dc355 plus my two test files)
```
uv run --frozen --extra play --extra train --extra online pytest -q -p no:cacheprovider
1996 passed, 11 skipped, 9 xfailed, 2 warnings in 413.07s (0:06:53)
```
The 9 xfails: 5 older ones, the 2 Eval-owned `tests/test_eval_T22_parity.py::test_game_path_matches_runner_path_for_the_shipped_rival[0,3]` (strict, waiting for Eval's fix at Gate 2), and my 2 findings below. 11 skips are the usual ones. Real browser, Playwright and the smoke script were not run.

## Probe update (author edit, authorised)
`tests/test_qa_T22_probes.py`, renamed `test_label_honesty_is_missing_only_on_the_legacy_default_room_path` to `test_legacy_label_path_is_gone_and_default_baseline_room_is_honest`.
- Old: `assert 'legacy = mode is None and args.rival == "baseline"' in src`, with the docstring saying the legacy path still says "AI rival: ...".
- New: `assert "legacy" not in src and "honest=not" not in src` and `assert modes.label("baseline") == "Baseline (scripted)"`. The `make_game(..., honest=True)` label checks and `smodes.make_match("baseline").honest is True` are kept. The class-default line (`make_game(..., "baseline").rival_label is None`) stays, labelled "class default only".
`tests/test_eval_T22_parity.py` not touched.

## Existing-test edits: exactly as authorised
`git diff 0ff9d4a..19dc355 -- tests/` touches only: `test_gate_t13_qa_online.py` (one line: `"AI rival"` becomes `"Baseline (scripted)"` in the `[baseline]` assertion), `test_qa_T22_probes.py` (only the strict xfail marker of the QA-T22-1 case removed), and two new files `test_t22fix1_*.py`. The web smoke edit is `tools/web/smoke.cjs`. `test_eval_T22_parity.py` is unchanged. Met.

## Scope
`git diff --name-only 0ff9d4a..19dc355`: `agents/modes.py`, `play.py`, `server/__main__.py`, `server/match.py` (one comment), `web/keys.js`, `web/main.js`, `tools/web/smoke.cjs`, `docs/final/{GAME_MODES,ONLINE_PLAY,WEB_BUILD}.md`, `docs/agent-sessions/T22-fix1.md`, the TL report, 4 test files. Nothing in `pop/`, `agents/rl/`, `agents/versus_baseline.py`, `tools/rl/`, `evaluation/`, `web/bridge.py`, `.github/`, `pyproject.toml`, `uv.lock`. All permitted. Pinned by `test_no_forbidden_path_is_touched`. Met.

## Acceptance criteria -> evidence
| # | Item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | WAIT forwarded as the runner does; failed or illegal is a labelled fallback | yes | `ModeRival._answer` returns `WAIT` on the decision tick and `None` between. My probes: game path vs runner path on seeds 1, 2, 5 (non-WAIT inputs equal, whole final snapshot equal, empty fallback log); near-miss answers ("wait", " WAIT", "", bytes, list, 0, False) are `None` plus `source: fallback`; exception, WAIT, legal sequence keeps cadence and log; reset restarts cadence |
| 2 | #91 label on every path | yes | `server/__main__.py` has no `legacy`, `honest=not` or "AI rival". `make_match` defaults `honest=True`; ai and baseline rooms show the honest labels; `--neutral` never shows the old label; the T13 `[baseline]` real-subprocess test passes |
| 3 | #92 bare `play.py` shows the menu; old level kept | yes | with `mode_main`, `versus_main` and `pygame.init` stubbed: `[]`, `--seed 3`, `--placeholder`, `--menu-keys ... --screenshot` give the menu; `--classic`, `S1`, `S3`, `S2 --seed 4`, `--keys`, `--screenshot`, `--watch baseline` give the classic path; `S2 --classic` keeps S2; `ARENA --versus` and `--mode ai` dispatch; `--versus` alone is still a usage error; `--replay` without a file does not open the menu |
| 3b | hosted chooser | yes (static and Node only) | `needsChooser` on 13 more query strings incl. `seed=`/`seat=`/`label=` alone (chooser), `play=`, `mode=`, `rival=` with empty or bogus values (no chooser), no argument (chooser); main.js returns before `startPython`; no mode marked current on the chooser; `online.js` untouched; `keys.test.js`, `ui.test.js`, `node --check` pass; `smoke.cjs` picks a mode and checks 3 buttons before waiting for ready. Not run in a browser |
| 4 | `--mode` help from the mode list | yes | `--help` contains `id = label` for every entry of `modes.MODES`; no hand-written label in play.py |
| 5 | weights cache | yes, one minor | wrong hash refused cold and warm and a failure is not cached; another (broken or missing) path is not served from the cache; same content at another path is loaded and checked again; size change and mtime change at same size are re-checked; each room has its own `PolicyMacro` and controller over one net; 240 AI ticks do not change the net. Weak point: QA-T22fix1-1 |
| 6 | fallback log cleared on reset, console only | yes | reset clears list and counters; `tick_json` and the server payload carry no `fallback`; `reportFallbacks` uses only `console.warn`; `loggedFallbacks` reset on rematch |
| 7 | docs | yes, one minor | GAME_MODES.md has the synchronous/no budget/0.04 s, label-not-claim, no win rate, T09 not supported, `--classic`; ONLINE_PLAY.md and WEB_BUILD.md sentences present; no win-rate text in `render/`, `web/main.js`, `web/bridge.py`, `agents/modes.py`. Stale row: QA-T22fix1-2 |
| 8 | authorised test edits exactly as listed; scope | yes | sections above |

## Findings
Reproduced:
- **QA-T22fix1-1 (minor)** `agents/modes.py:_shared_net`. Cache key `(path, sha, mtime_ns, size)`: a same-size edit with the mtime restored is served from the cache without a new hash check. Repro: warm the cache from a copy of the weights, flip one byte, `os.utime(..., ns=(atime, old_mtime_ns))`, call `make_controller("ai", weights=copy)`. Expected `WeightsError`; actual a controller. Needs a local attacker inside the running process or filesystem, and the shipped path is read-only in the build, so low risk. Probe `test_cache_rechecks_a_same_size_edit_with_the_mtime_restored` (strict xfail). Fix, if wanted: key on the file's sha256 of the bytes (reading 1 file once per room is cheap) or accept and document.
- **QA-T22fix1-2 (minor, docs)** `docs/final/WEB_BUILD.md`, the `?mode=ai` row still says the baseline is labelled "AI rival: versus-baseline (scripted)". The page passes `honest=true` (`web/main.js`), so it shows "Baseline (scripted)". Pre-existing text that #91 and #88 make stale. Probe `test_web_build_mode_ai_row_names_the_label_the_page_shows` (strict xfail).
Unverified or by design (no action required):
- A chooser click goes to `?play=<id>` and drops `seed=`, `seat=` and `label=neutral`. Seed and seat were never set from the chooser; a blind playtest must open `?play=...&label=neutral` directly.
- `?play=bogus` skips the chooser and plays the baseline. Same as before.
- The runner substitutes WAIT for a failed answer; the game submits nothing. The TL recorded this; it changes only error ticks and the game labels each one.
- GAME_MODES.md quotes decision timings (median 0.04 ms, p99 1.2 ms) that I did not reproduce.
- For Gate 2: `tests/test_eval_T22_parity.py::test_game_path_matches_runner_path_for_the_shipped_rival[0,3]` stays strict xfail; its comparison must filter WAIT from the game side as well. My probes on seeds 1, 2, 5 use the filtered comparison plus the whole final snapshot, and pass.

## Not checked
A real window, a real browser (Pyodide, Phaser, chooser click flow, console warnings, `smoke.cjs`, the Playwright CI job), two human clients, `--live`, training, H6.

## Requested next action
Gate 2 (evaluation-specialist): fix `tests/test_eval_T22_parity.py` and review WAIT forwarding by the AI seat, the weights cache and the console-only fallback log. Then Gate 3.

## Student decision required
none

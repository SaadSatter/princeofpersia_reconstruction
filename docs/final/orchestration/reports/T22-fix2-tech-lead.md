---
handoff_id: HO-T22-fix2-tech-lead
task_id: T22-fix2
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T22-fix2.md@d35fe93
source_branch: task/T22-fix2
source_commit: 3cbffa02c801030003d43dd7c7e8c0575eb31c8d
reviewed_commit: n/a
verdict: n/a
---

# T22-fix2: tech-lead report

Status: done

## Work completed
Branched from 967db26, merged `origin/orch/reviewed` 1a515ca (merge commit 451f923), resolved four conflicts so the T22 modes and T20 telemetry both work, then did items 2 to 5 and added overlap tests (3cbffa0).

## Conflicts and resolutions
1. `play.py` (4 hunks).
   - Helpers: kept T22's `menu_entries`/`ai_key_names` and T20's `new_recorder`/`restart_recorder`/`record_tick`. `new_recorder(args, ep, seats, kind)` now takes the logged seats and the mode id. It stores them on `args`, so the R restart reuses them. The log header says `"rival": <mode id>`.
   - `versus_main(args, rival=None)`: T22 signature kept. The recorder is created with `shown_seats` (`("A",)` against an AI, both seats in `human`), so an AI seat never gets a log.
   - R key: with `--playtest` the recorder restarts, then the AI rival is reset (#41), otherwise the plain reset.
   - Input loop: T22's `shown_seats` loop kept, with T20's `logged_before` snapshot. The recorder filters by its own seats, so the AI's accepted inputs are never logged.
   - `main`: T22's menu-by-default (#92) and `mode_main` dispatch kept. The T20 check now reads "`--playtest` needs `--versus`, `--mode` or `--menu`", placed before `mode_main`. `play.py S3 --playtest` still errors (T20 test unchanged and passing).
2. `server/__main__.py` (2 hunks). Both imports kept (`room_modes`, `Telemetry`/`_today`). `make_match(code, mode)` builds a `Telemetry` when `--playtest` is set and passes `telemetry=` through `room_modes.make_match`, so the home room and every created room (ai, baseline, human) get telemetry. The `--rival ai` choice, the weights check at start and the `--playtest` flags are all kept.
3. `server/match.py`: constructor takes both `honest` (T22) and `telemetry` (T20). The rival check stays `None|baseline|ai`. Telemetry already used `self.human_seats` and `self.rival`, so an AI room logs only seat A with no further change.
4. `docs/final/ONLINE_PLAY.md`: options paragraph merged (`--rival ai` plus `--playtest`/`--telemetry-dir`). It says that in an AI room only seat A is logged.

Behaviour both briefs imply. An AI room or `play.py --mode ai|baseline --playtest` logs only the human seat A, from its own observation and inputs. There is no file for the AI seat. Fallbacks stay in the server trace and stdout (`source: fallback`) and never reach a log. Telemetry reads only, so the trace and state hash are unchanged.

No change to `tools/telemetry/**`, `server/telemetry.py` or `pop/`. `TELEMETRY.md` already says the AI seat has no log. I did not edit it (not a permitted path), so it does not yet mention `--mode ... --playtest`. See the concerns.

## Items 2 to 5
2. `docs/final/WEB_BUILD.md` `?mode=ai` row now says labelled "Baseline (scripted)" (honest names, #88).
3. `agents/modes.py` `_shared_net` hashes the file bytes on every call. The cache key is `(resolved path, SHA-256 digest)`. I kept the path in the key because the existing `test_same_content_other_path_is_checked_again` requires it. A wrong hash goes to `load_net` and raises `WeightsError`.
4. `server/rival.py`: the comment on the late-answer path now says it returns no input (counted in `slow`, labelled fallback) and drops the late answer.
5. Removed the strict xfail markers from `test_cache_rechecks_a_same_size_edit_with_the_mtime_restored` (QA-T22fix1-1) and `test_web_build_mode_ai_row_names_the_label_the_page_shows` (QA-T22fix1-2). Both now pass.

## Paths
Merge (451f923): `play.py`, `server/__main__.py`, `server/match.py`, `docs/final/ONLINE_PLAY.md`, plus T20/T21 files brought in unchanged.
3cbffa0: `agents/modes.py`, `server/rival.py`, `docs/final/WEB_BUILD.md`, `tests/test_qa_T22fix1_probes.py`, new `tests/test_t22fix2_overlap.py` (15 tests). This report.

## Acceptance criteria to evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Both features work in full | yes | T20 and T22 suites pass unchanged on the merge; overlap tests |
| 2 | AI room logs only seat A, nothing of the AI or fallbacks | yes | `test_ai_room_*`, `test_play_mode_ai_playtest_logs_only_seat_a` |
| 3 | Telemetry never touches the duel in AI modes | yes | `test_telemetry_leaves_the_ai_duel_and_every_message_unchanged`, `test_play_playtest_does_not_change_an_ai_run` |
| 4 | Server wires telemetry into every room mode | yes | `test_server_wires_playtest_into_every_room_mode` |
| 5 | Items 2 to 5 | yes | see above |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree, 3cbffa0)
2161 passed, 11 skipped, 5 xfailed, 2 warnings in 467.19s (0:07:47)
```
No T20/T21 test contradicted a T22 test. The one existing test that constrained the item 3 design (path in the cache key) was satisfied, not edited. The overlap tests were written after the resolution and passed on first run, so I did not see them fail first. They exercise paths that did not exist before the merge.

Manual checks (headless / local):
- `play.py --mode ai --playtest --telemetry-dir ... --keys A:RIGHT,A:RIGHT,A:DRAW` under the dummy video driver. It wrote only `...-LOCAL-001-A.jsonl` and a host json that lists only seat A, with header `"rival":"ai"`. `tools/telemetry/summarize.py` ran on it and wrote `summary.json` and `summary.md`.
- `python -m server --rival ai --playtest --port 8791` started, printed the "Playtest telemetry ON" line and the URLs, and I stopped it. No real browser or WebSocket client was run.

## Findings
No findings in my own work beyond the concerns below.

## Known limitations
- Not run: a real browser or two live clients, `--live`, training, and H6.
- The R-key restart with `--playtest` in an AI mode is covered by code reading only, not by a test. The headless `--keys` path has no R key.
- `docs/final/playtest/TELEMETRY.md` still shows only `play.py ARENA --versus --playtest`. A one-line mention of `--mode ... --playtest` would help, and it needs a permitted path or a separate task.

## Unresolved findings
None.

## Requested next action
QA: Gate 1 on `task/T22-fix2` 3cbffa0 (both features, the overlap, scope). Then Eval (AI seat and telemetry boundary in AI rooms, parity). Gate 3 is then a fast-forward of `orch/reviewed`.

## Student decision required
None.

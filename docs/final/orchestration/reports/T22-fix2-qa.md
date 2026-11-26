---
handoff_id: HO-T22-fix2-qa
task_id: T22-fix2
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-fix2-tech-lead.md@9b59677
source_branch: gate/T22-fix2-qa
source_commit: see the branch head (tests commit on top of 9b59677; this report is added in a following commit)
reviewed_commit: 9b59677dd07ea1882114a4484be924fd023a5fc1
verdict: ACCEPT WITH NOTES
---

# T22-fix2: QA report (Gate 1)

Status: done

## Work completed
Reviewed 9b59677 (merge 451f923 of 1a515ca into 967db26, then items in 3cbffa0). Diffed each conflicted file against both parents, checked both suites, probed the overlap (`--playtest` with `--mode ai|baseline|human`, the menu, and the R restart), and judged items 2 to 5. Added `tests/test_qa_T22fix2_probes.py` (12 tests, all pass). No blocker or major finding.

## Paths
- `tests/test_qa_T22fix2_probes.py` (new)
- this report

## Acceptance criteria to evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Merge loses no line of either feature | yes | `git diff 1a515ca 451f923 -- play.py server/__main__.py server/match.py`: every removed T20 line is replaced by its T22-extended form (`new_recorder(args, ep, seats, kind)`, `make_match(code, mode)` with `telemetry=`, `_seen_fallbacks` becomes a 3-tuple incl. `policy_errors`, rival check widened to `ai`). `git diff 967db26 451f923`: the only removed T22 lines are `ep.reset(args.seed)` (moved under `else` of the `--playtest` branch), `self.game.press(keys)` (now `held = ...press(keys)`), and the `_ticks.append(...)` line (now built from `accepted`). All T20 additions present: `_tele(...)`, `_note_refused`, `after_tick`, `self._now`. |
| 2 | Both suites pass unchanged; only the two xfail removals in existing tests | yes | `git diff 967db26 9b59677 -- tests` shows removed lines are only the two `xfail(strict=True, ...)` decorators in `tests/test_qa_T22fix1_probes.py` (QA-T22fix1-1, -2). T20/T21 test files are byte-identical to 1a515ca (no `tests/test_t20*`/`t21*` in `git diff 1a515ca 9b59677 --name-only`). Other changed test files differ from 1a515ca because T22 tests are new there. |
| 3 | AI room / `--mode ai\|baseline` with `--playtest` logs only the human seat A | yes | probes: `test_r_restart_with_playtest_...[ai,baseline]` (no `-B.jsonl`), `test_menu_with_playtest_logs_the_chosen_mode_and_only_seat_a`, `test_ai_log_never_names_the_ai_seat_or_fallbacks` (no "fallback", "policy", seat B). TL's `test_ai_room_*` also pass. |
| 4 | Human rooms still log both seats | yes | probe `[human]` of the R test writes A and B logs for duels 001 and 002. |
| 5 | Telemetry never changes the duel | yes | `test_playtest_does_not_change_a_local_run[ai,baseline,human]`: screenshot bytes identical with and without `--playtest`; TL's `test_telemetry_leaves_the_ai_duel_and_every_message_unchanged` passes. |
| 6 | R restart with `--playtest` (untested by TL) | yes | probes inject a real K_r KEYDOWN. Result: duel 001 closes (`abandoned`/`restart`), duel 002 opens with its own header (`rival` = mode) and `duel_start`, no duel 003, the AI rival is reset exactly once more (`test_r_restart_resets_the_ai_rival_once_more`), and without `--playtest` nothing is written. |
| 7 | Item 2, WEB_BUILD `?mode=ai` row | yes | row says labelled "Baseline (scripted)"; the formerly xfailed probe passes. |
| 8 | Item 3, weights cache keyed on digest | yes, with a note | see "Judgement" below. Probe `test_weights_cache_recovers_when_the_file_is_restored` (edit with mtime restored is refused, restore is accepted, the net object is reused) passes. |
| 9 | Item 4, `rival.py` comment | yes | now reads "no input this tick (counted in `slow`, labelled fallback); the late answer is dropped". Matches the code (`return None`, `self.slow += 1`). One line, over 100 columns (cosmetic). |
| 10 | Item 5, only the two xfail markers removed | yes | see criterion 2. Both tests pass. |
| 11 | Scope | yes | `git diff --name-only 1a515ca..9b59677`: no `tools/telemetry/**`, no `server/telemetry.py`, no `pop/`, no `agents/rl/**`, no `.github/`/`ci/`. (`967db26..9b59677` lists `pop/versus.py`, `server/telemetry.py`, `tools/telemetry/summarize.py` only because the merge brings in T20/T21 unchanged from 1a515ca.) Changed paths vs 1a515ca are all T22 files plus the resolution files. |

## Judgement of item 3 (cache keyed on (path, digest))
Sound. The file is read and hashed on every call. If the digest differs from the expected hash the call goes straight to `policy.load_net`, which raises `WeightsError`, so a wrong file is never served from cache whatever its size or mtime (the QA-T22fix1-1 hole). A cache hit therefore only happens for a file whose bytes match the expected hash right now. Keeping the path in the key is harmless and satisfies the existing `test_same_content_other_path_is_checked_again`. The cost is one file read plus SHA-256 per room creation (about 0.3 ms per Eval, not re-measured here). On a miss the file is read twice (a theoretical TOCTOU between the two reads; `load_net` re-checks the hash, so the result is still safe). Departure accepted.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_qa_T22fix2_probes.py
12 passed in 3.56s

uv run --frozen --extra play --extra train --extra online pytest -q          (clean committed tree, run 1)
FAILED tests/test_qa_T22_probes.py::test_server_ai_seat_gets_only_seat_b_and_a_slow_policy_is_a_logged_fallback_never_sent[baseline]
1 failed, 2172 passed, 11 skipped, 5 xfailed, 2 warnings in 504.63s (0:08:24)

(run 2, same tree)
FAILED tests/test_qa_T22_probes.py::test_server_ai_seat_gets_only_seat_b_and_a_slow_policy_is_a_logged_fallback_never_sent[ai]
1 failed, 2172 passed, 11 skipped, 5 xfailed, 2 warnings in 520.77s (0:08:40)

tests/test_[a-q]*.py (includes that file), run 3:   1275 passed, 10 skipped, 5 xfailed, 6 warnings in 338.10s
test_qa_T22_probes.py alone:                        44 passed in 6.63s
the named test alone, three times:                  2 passed each
```
The Tech Lead's run of 3cbffa0 reported 2161 passed, 0 failed (before my 12 probes).

## Findings
Reproduced:
- [minor, flaky test, not a product defect] `tests/test_qa_T22_probes.py:308` — `assert worst < 0.04 + 0.05` is a wall-clock bound on one `m.advance` call. In two full-suite runs on this machine it failed once for `[baseline]` and once for `[ai]` (different parameter each time, so it is not tied to a mode), yet it passes alone, in its file, and in a 1275-test subset including it. Likely CPU load or GC late in a long run (the run also hosts leftover threads from slow-rival tests). The test is a T22 test unchanged by fix2, so this is not caused by the merge or items 2 to 5, but a Gate 3 trial on a loaded machine may see it. Suggest the Tech Lead widen the margin or the orchestrator rerun in isolation. I did not capture the failing `worst` value (the full run takes 8 minutes); unverified beyond that.

Notes (not blocking):
- [note] `docs/final/playtest/TELEMETRY.md:10` still lists only `play.py ARENA --versus --playtest`; it does not mention `--mode ai|baseline|human --playtest`, `--menu --playtest`, or the AI-room rule (only seat A logged, header `rival` = mode id). Not a permitted path for the Tech Lead; needs a one-line follow-up task.
- [cosmetic] `agents/modes.py` new comment line and `server/rival.py` comment exceed about 100 columns.
- [note] `play.py --mode human --playtest` writes `"rival": "human"` in the header, where T20 used `"human"` too (kind), so the summarizer is unaffected. Both seats are logged as before.

Unverified concerns: no real browser or WebSocket client was run (the TL did not either); the online server's telemetry for AI rooms rests on the TL's `test_server_wires_playtest_into_every_room_mode`, the `test_ai_room_*` tests and my read of `server/match.py` (telemetry uses `human_seats`, and the AI seat's fallbacks go only to `_fallbacks`).

## Known limitations / Not checked
- Playwright browser smoke and screenshots: not run (no web change in fix2 beyond a doc row; web files are unchanged against 967db26).
- `--live`, training, H6: not run, as instructed.
- The T20 manual check was covered through probes with `--mode ai` (headless), not by hand.
- Speed claim (about 0.3 ms) taken from Eval, not re-measured.

## Unresolved findings
The flaky timing test above (minor). Nothing else.

## Requested next action
Evaluation Specialist: Gate 2 on `gate/T22-fix2-qa` / 9b59677. Focus on the AI seat and telemetry boundary in AI rooms (server `Telemetry` with `rival=ai`, fallbacks and `policy_errors` never in a log or client message), parity still holding after the merge, and the log header's `rival` field. Orchestrator: decide on the flaky timing test and the TELEMETRY.md note.

## Student decision required
None.

## Addendum: flaky timing probe made robust (orchestrator request)
`tests/test_qa_T22_probes.py` (my own T22 probe), the one assertion changed:
- Old: `assert worst < 0.04 + 0.05, worst`
- New: `assert worst < delay["s"] / 2, f"worst advance() took {worst:.3f}s (injected delay {delay['s']}s)"` (bound 0.15 s; the injected delay is 0.30 s)
- It still proves what it proved: a slow policy becomes a logged `"source": "fallback"` that never reaches the client (the later asserts are untouched), and `advance` is bounded by the rival budget (about 0.04 s) plus noise, not by the 0.30 s delay (a stalled loop would show at least 0.30 s, twice the new bound).
- `worst` on an idle machine: 0.0455 s (`[ai]`) and 0.0459 s (`[baseline]`). The loaded-run failure values were not captured earlier; the failure message now prints them.
- Nothing else changed.

### Addendum: full-suite runs after the change (clean committed tree)
```
run A: FAILED tests/test_qa_T22_probes.py::test_server_ai_seat_gets_only_seat_b_and_a_slow_policy_is_a_logged_fallback_never_sent[ai]
       1 failed, 2172 passed, 11 skipped, 5 xfailed, 2 warnings in 667.67s (0:11:07)
run B: 2173 passed, 11 skipped, 5 xfailed, 2 warnings in 807.42s (0:13:27)
run C (extra): FAILED tests/test_rl_train.py::test_smoke_training_runs_logs_exports_and_loads_back
       (tests/test_rl_train.py:76  assert time.time() - t0 < 60)
       1 failed, 2172 passed, 11 skipped, 5 xfailed, 2 warnings in 787.82s (0:13:07)
```
- Run A: I had cut the output to the last 3 lines, so I did not see which assertion of the probe failed. I could not reproduce it: the probe passes alone, and 8 times in a row with 16 busy processes loading the CPU. It may be the warm-up check `fallbacks == []` (a normal tick exceeding the 0.04 s rival budget on a loaded machine), which I was told not to change. Unverified.
- Run C failed on a different wall-clock test (a 60 s smoke-training bound), not a T22 test. The suite took 11 to 13 minutes against 8 earlier, so the machine was loaded.
- So the suite is load-sensitive in at least two places, neither touched by fix2. Suggest Gate 3 runs it on an idle machine, and the Tech Lead hardens the `fallbacks == []` warm-up check if it is the cause.

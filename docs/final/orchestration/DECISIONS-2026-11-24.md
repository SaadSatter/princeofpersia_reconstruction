# Saad's decisions: 2026-11-24

Saad gave these in chat on Tue 2026-11-24, about 13:40 ET, after reading the
orchestration refactor report. His words are copied **verbatim**. Numbering
continues from `DECISIONS-2026-11-23.md`.

> "Push to github I agree with the smoke and origin main. You don't need approval for every push, for issues and PRs for handoffs you don't need approval. Allow to commit to main follow the new rules. Update the outdated docs."

| # | Topic | Saad's answer (verbatim excerpt) | Orchestrator's reading and effect |
|---|---|---|---|
| 26 | Publish the refactor | "Push to github I agree with the smoke and origin main" | Push `main` (including `inputs/FINAL_REQUIREMENTS.md`, which becomes public) and the SMOKE-01 branches `task/SMOKE-01` and `gate/SMOKE-01-qa` |
| 27 | Pushing | "You don't need approval for every push" | Standing approval: the orchestrator pushes branches without asking each time. Never force-push, never delete or rewrite a branch. Workers still do not push; the orchestrator does. `AGENTS.md` item 6 updated to match |
| 28 | GitHub handoffs | "for issues and PRs for handoffs you don't need approval" | The orchestrator opens issues and PRs, and posts reports as PR or issue comments, without asking (extends decision #14). **Merging** a PR is still Saad's |
| 29 | Committing to `main` | "Allow to commit to main follow the new rules" | The orchestrator commits to `main` under the new rules: orchestration records (`docs/final/orchestration/**`) directly; gameplay, engine, tests and other docs reach `main` only through a PR Saad merges |
| 30 | Outdated docs | "Update the outdated docs" | Task T10: bring `GDD.md`, `CONFIGURATION.md`, `REQUIREMENTS_CHECKLIST.md`, `PROJECT_PLAN.md` and `docs/final/README.md` in line with decisions #1 to #29, with dated "Changes since the last gate" sections and no rewritten history. It runs through the chain: Tech Lead, QA, Gate 3, then a PR |

## Addendum: Tue 2026-11-24, about 14:19 ET

Saad answered two questions put to him by the orchestrator session (AskUserQuestion) before T05-fix1 was dispatched again. His choices are quoted verbatim.

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 31 | CLIMB down (T05-fix1; was listed under "Waiting on Saad") | "CLIMB both ways (Recommended)" | `CLIMB` climbs up an edge, and also goes down safely: hang and drop, or a drop into a pit the engine lets you survive. `SEARCH` and `FLEE` may also use survivable drops. No new macro name (decision #23 stands). G1's "climb" is read as covering both directions. `MACROS.md` records it as confirmed by Saad, not pending |
| 32 | Parallel work alongside T05-fix1 | "T05-fix1 only (Recommended)" | Only one task chain runs at a time for now. T04-fix3 and GATE-wave3 wait until the T05-fix1 chain is finished |

## Addendum: Tue 2026-11-24, afternoon (T04-fix3, numpy, online play)

Saad asked in chat: "What do you mean the numpy isnt a declared dependecy? Just pipinstall it? Also is the online play ready for play testing between humans?" After the orchestrator's answer, he chose (AskUserQuestion, verbatim):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 33 | Stale gate probe `tests/test_gate_t04fix1_eval_probes.py::test_same_instance_in_both_seats_busy_blocks_both` (it contradicts #24) | "Flip to ValueError (Recommended)" | The probe asserts that `VersusRunner` raises `ValueError` when one controller object fills both seats. The T04-fix3 Tech Lead makes the change (brief amended); it is reviewed at Gates 1 and 2. This is the same kind of change as #21 |
| 34 | numpy | "Add a train extra (Recommended)" | `pyproject.toml` gets an optional extra `train = ["numpy>=2,<3"]`, and `uv.lock` is refreshed. RL tests run with `--extra train`. The base install stays numpy-free. New task **T15**, through the gates |
| 35 | Online human vs human | "Build it for G2/G3" | **Overturns the online-play deferral in #1** (and the "deferred" note in #12): T13 (online play, one authoritative server, one browser per rival) is in G2/G3 scope, due Sat 2026-11-28. Hosting (OQ-10), disconnect rule (OQ-13), the WebSocket dependency and the task order are asked separately before the T13 brief |
| 36 | OQ-10 hosting for T13 | "Your laptop, same LAN (Recommended)" | The authoritative server runs on Saad's Mac (`uv run python -m server`). Two computers on the same Wi-Fi open `http://<laptop-ip>:<port>`. No new service or account. OQ-10 closed for G2/G3 |
| 37 | WebSocket dependency | "websockets, online extra (Recommended)" | Optional extra `online = ["websockets>=13,<16"]` in `pyproject.toml`, and `uv.lock` refreshed. The base install is unchanged. Tests use no network beyond localhost |
| 38 | OQ-13 disconnect | "Pause 15 s, then forfeit (Recommended)" | On disconnect the duel pauses for both players. A reconnect within 15 s resumes it; otherwise the disconnected seat loses, and the end screen says why. OQ-13 closed |
| 39 | Task order (amends #32) | "T13 alongside reviews (Recommended)" | Finish T04-fix3 and T15, then run T13 (tech-lead) **at the same time as** GATE-wave3 (QA and Eval, tests and reports only; disjoint paths). Otherwise one chain at a time |

## Addendum: Tue 2026-11-24, evening (numpy scope, rematch)

Saad, in chat (verbatim): "add numpy as a train extra, also to call for a rematch, a button in the style of the game should popup for rematch"

| # | Topic | Saad's answer (verbatim excerpt) | Orchestrator's reading and effect |
|---|---|---|---|
| 40 | numpy also in the `dev` group? | "add numpy as a train extra" | numpy stays an optional `train` extra only, as built in T15 (closed, `orch/reviewed` 199f858). It is not added to the `dev` group. The full suite is run with `--extra train` |
| 41 | Rematch trigger (T13, and #25) | "to call for a rematch, a button in the style of the game should popup for rematch" | When a duel ends, a **Rematch** button pops up on each player's screen, drawn in the game's own pixel-art dungeon style (existing palette and art, no new generated asset). Pressing it requests a rematch; the duel restarts with the same seed (#25). Online, **both** players must press it, and the first to press sees "waiting for rival". The "both" part is the orchestrator's reading, flagged for Saad to confirm at review |

## Addendum: Tue 2026-11-24, night (after GATE-wave3)

Saad's choices (AskUserQuestion), quoted verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 42 | T07-fix1 edits T07's own parity test `tests/test_rl_policy.py` (not on `main`) | "Allow the fix (Recommended)" | T07-fix1 gathers the 200 parity observations over several seeds, with a fresh `Encoder` per duel. The check itself (pure-Python logits equal numpy to 1e-9) is unchanged |
| 43 | T07-E1: PPO and RIG_TRAP | "Train without traps" | RIG_TRAP stays reserved and masked for the PPO rival. Training does not wait for traps. G2/G3 documents "the AI rival does not set traps; traps are human-only" (`RL_POLICY.md`, Changes since G1). Rigging by the AI rival would need a new run, after G2/G3 |
| 44 | T07-E3: tuning starts | "Add tuning starts (Recommended)" | T07-fix1 adds about 6 tuning starts, including lower floors, disjoint from H6 by construction. T08 freezes H6 with a hash and proves the two sets disjoint before the full run |
| 45 | T13 live AI-seat budget | "Accept 0.04 s live (Recommended)" | On the live server the AI seat gets at most 0.04 s per decision, then a labelled, server-logged WAIT fallback. Evaluation and training keep the 5 s runner timeout (#24) |

Saad, in chat (verbatim): "Yes both press rematch, keep going through the gates"

| # | Topic | Saad's answer (verbatim excerpt) | Effect |
|---|---|---|---|
| 46 | #41 "both press" reading | "Yes both press rematch" | Confirmed. Online, the rematch starts only after both players have pressed the Rematch button. The flag on #41 is cleared |

Saad, in chat (verbatim): "Yes stop on first error, keep going through the gates"

| # | Topic | Saad's answer (verbatim excerpt) | Effect |
|---|---|---|---|
| 47 | T07-fix1 proposed fail-fast | "Yes stop on first error" | Training stops on the first update with any policy or encoder error, writes no weights, and exits with status 2 and a message on stderr (`TrainConfig.fail_on_policy_error`, on by default). The flag on this proposal is cleared |

## Addendum: Tue 2026-11-24, late night (T13-fix1, training run)

Saad's choices (AskUserQuestion), quoted verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 48 | T13 silent-drop detection (EVAL-3) | "Detect in ~6 s (Recommended)" | Server keepalive: ping every 3 s, 3 s timeout. A silent drop is noticed within about 6 s, the dropped seat's held keys are cleared at once, and then the 15 s pause (#38) starts |
| 49 | Online AI-seat fallbacks (EVAL-5) | "Log only, document (Recommended)" | A live human-vs-AI duel never aborts on fallbacks. Each fallback is logged server-side as `"source": "fallback"` and counted in the trace. `ONLINE_PLAY.md` says so. Evaluation keeps #24's abort rule |
| 50 | Weights after a failed `final_check` (T16 QA F1) | "Withhold (Recommended)" | On a `final_check` policy error, `weights.json` is renamed `weights.failed.json`, alongside the existing exit 2 and `stopped`. This is a small task (T17) through QA and Eval before the run |
| 51 | **Full PPO training run** | "Go, 4,800 s cap (Recommended)" | **Saad's go-ahead** for the full run from `orch/reviewed` 2835928 (plus T17 once closed), on Saad's Mac: 2 workers, the numpy `train` extra, `--seconds 4800`, the Mac kept awake. It starts after T17 passes Gate 3. It counts only with exit 0 and `stopped` in {`time_cap`, `max_iters`} |

## Addendum: Tue 2026-11-24, night (gameplay clean-up, T18 and T19)

Saad's request in chat (verbatim):

> "Another claude code session is working on the PPO and RL agent. I want this to clean up the game play.
> 1. When performing online play, let's use a room code,
> 2. Each player can use either control system (ASWD vs ARROWS)
> 3. let picking up dropped swords or disguises be a kneel animation
> 4. Debouncing, sometimes actions like (left -> jump, or jump -> left) sometimes has a time lag.
> 5. Flipping, let it be the default style of jump except when climbing. And Jumping then direction or direction then jumping both should cause flipping in that direction"

His choices (AskUserQuestion), quoted verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 52 | Online room code | "Many rooms, 4-letter code (Recommended)" | Player 1 creates a room and gets a 4-letter code; player 2 types it to join. One server holds several duels at once; a code expires when its room empties. Task T18 |
| 53 | Flip as the default jump | "Look and effect only (Recommended)" | Every directional jump, standing or running, in either input order, is a flip in that direction (motion and `last_result` effect `flipped`). Distances stay as now. `UP` under a ledge still climbs; `UP` on open floor with no direction is still a hop. Amends R-V22. Existing tests that encode the old "a standing jump flips only over someone" rule change only where they assert exactly that (the same kind of change as #21 and #33), each listed in the report. Task T19 |
| 54 | Input lag (left→jump, jump→left) | "2-tick grace window (Recommended)" | A direction and a jump pressed within 2 ticks (about 170 ms at 12 Hz) of each other, in either order, become one directional jump (a flip, #53); a press during a move's last frames is buffered. The same for every seat and every front end (pygame, hosted page, online server). Task T19 |
| 55 | Either control scheme | "Both schemes except local 2P (Recommended)" | Online and human-vs-AI: WASD + F/G/T/left Shift and arrows + `.` `/` `'` right Shift both drive the player's own seat. Local two-player on one keyboard keeps A = WASD, B = arrows. Task T19 |

Item 3 (a kneel when picking up a dropped sword or a uniform) needed no choice: it reuses the existing rig kneel pose, keeps the frame counts (`PICKUP_FRAMES` 6, `TAKE` 12) and keeps what the other seat is shown (R-V25). Task T19.

Order: decisions #32 and #39 allow one chain at a time, so T18 runs first and T19 follows it. The PPO run #51 is in its own worktree at f08c1a8 and is not affected. After T19 the PPO rival must be re-checked against the new jump rule (Gate 2 says how).

Saad's choices on the T18 tech-lead report (`reports/T18-tech-lead.md`@d643007), AskUserQuestion, verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 56 | Old CLI test pins the code-less single-duel lobby (`tests/test_gate_t13_qa_online.py::test_cli_process_two_scripted_clients_real_clock_and_trace_dir`) | "Keep a code-less default room" | The server keeps one default room that a code-less `{"type":"join"}` enters: first = seat A, second = seat B, third refused as full, exactly as the T13 lobby did, including its reset when empty. It never expires and counts toward no code. The old test stays unchanged and must pass. Coded rooms work as built. The page keeps Create and Join; it offers no code-less button unless Saad asks |
| 57 | T18 limits | "Accept all (Recommended)" | 10 failed joins per connection per minute; at most 50 rooms; a room expires 10 min after creation with no second player, or 15 s after both seats are gone. Per connection only (no per-IP limit) |

## Addendum: Tue 2026-11-24, late night (PPO line: T08 scenarios)

Recorded by the PPO-line orchestrator (session 8edb65a6), after T07-run1 closed. Saad's choices (AskUserQuestion), quoted verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 58 | B2 "Blend": what is "low suspicion" | "Below 50/100 (Recommended)" | B2 succeeds if the watching guard's suspicion stays below 50 of 100 for the whole scenario. A named parameter in the scenario registry. Closes the "pending Saad" note in `tasks/T08.md` |
| 59 | D1 "Disguise": what is "on screen" | "Same room (Recommended)" | D1 succeeds only if the other rival is never in the agent's room at any frame of the scenario (and the agent kills a guard and takes the uniform) |
| 60 | H6-4's B start equals tuning start (1,2,3,+1) (T07-fix1 Eval N1) | "Move the H6 cell (Recommended)" | Option A: T08 moves H6-4's B start to a cell no tuning start uses, chosen from the cell set and not from policy performance, then freezes H6 with a SHA-256 and a test proving it disjoint from the 8 `TUNING_STARTS`. Training data unchanged |
| 61 | Start T08 now, alongside T19 | "Start T08 now (Recommended)" | T08 starts now from `orch/reviewed` fc02687. It writes only new evaluation files. No PPO run on the held-out split: T09 runs H6 once, on the post-T19 engine (T07-run1 Eval E1) |

Saad, in chat after T18's Gate 3 (verbatim; numbered #62–#63 because a parallel session took #58–#61): "Its fine the way it is, let's add the server crash fix"

| # | Topic | Saad's answer (verbatim excerpt) | Effect |
|---|---|---|---|
| 62 | T18 minors: room cap 50 (measured safe about 40), creates not rate-limited, "full" vs "No room", the ligature QA-T18-1 | "Its fine the way it is" | All stay as built; QA-T18-1 stays a strict xfail |
| 63 | EVAL-T18-1: one room's `on_finish` error stops every room | "let's add the server crash fix" | Task T18-fix1: an error in one room's finish or trace write is logged and contained to that room; every other room keeps ticking; EVAL-T18-1's strict xfail then passes and its author removes the mark at Gate 2 |

## Addendum: Tue 2026-11-24, late night (PPO line: T08 tech-lead questions)

Saad's choices on `reports/T08-tech-lead.md`@deb8718 (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 64 | Held-out run-once key | "Weights + engine commit (Recommended)" | The run-once ledger allows one held-out (H6) run per (weights SHA-256, engine commit). Every run is still recorded and reported, so a re-run after a rule change is allowed but visible. T08-fix1 |
| 65 | Seat-B coverage of D1, B2, I3, F5-a/b | "Add mirrored seat-B starts (Recommended)" | Each tuning skill scenario also gets mirrored starts with the rival in seat B, so every scenario reports per-seat results. Tuning split only; H6 is not changed. T08-fix1 |
| 66 | B2 "active blend" reading | "Report it, don't score it (Recommended)" | B2 success stays as #58. `success_active` (at least 6 distinct cells while under 50) is reported beside it and is never scored. As built; documented in PROTOCOL.md |

## Addendum: playtest telemetry and a telemetry analyst (T20, T21)

Saad's request in chat (verbatim):

> "Add this telemetry for playtests and then make an agent a telemetry analyst. Your released build logs play events, and the agent reports where players stall, quit, or ignore a mechanic. You check its findings against your Playtest Log."

His choices (AskUserQuestion), verbatim. Numbered from #67 because a parallel session took #64–#66:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 67 | Which builds log | "Online server, behind a flag (Recommended)" | `python -m server --playtest` (off by default) writes one event log per room and seat; local pygame `--versus` gets the same flag. Only room code, seat and ticks identify a player; Saad maps seat to player code (P03) on his observation sheet. No names, IPs or browser data. Logs stay on the host and are never sent to a client. The hosted page logs nothing |
| 68 | Event set | "Default set (Recommended)" | Duel start and end; every resolved action (accepted or refused, with effect); room changes; disguise on and broken; sword drop and pickup; traps rigged and sprung; hits and hearts; idle spells; pause, disconnect, reconnect, forfeit; rematch pressed or not. Times in ticks plus seconds since duel start. No raw keys |
| 69 | Analyst as a course role | "Native helper now, decide later (Recommended)" | `telemetry-analyst` is a native worker, not a formal course production agent. It counts only if Saad later writes an origin note with two real, dated friction instances |
| 70 | Order | "T18-fix1 now, telemetry after T19 (Recommended)" | T18-fix1 (`server/app.py`) runs now alongside T19 (disjoint paths; amends #32/#39 for this pair). T20 (telemetry) starts after T19 closes; T21 (the analyst agent) after T20 |

The orchestrator checks every analyst finding against Saad's Playtest Log (`docs/final/playtest/LOG.md` and `sessions/`) before relaying it; a finding the log does not support is marked "not confirmed by the Playtest Log".

Saad's choices on the T19 tech-lead report (`reports/T19-tech-lead.md`@597e181), AskUserQuestion, verbatim:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 71 | A jump away from the facing: instant turn, or 4-tick turn first | "Keep instant turn (Recommended)" | `JUMP_*` faces and jumps at once (`Rival._directional`); runs and steps still turn first (R-D20). The QA probe `tests/test_gate_t05_qa_probes.py::test_qa_baseline_never_needs_a_fallback_over_randomised_duels_in_every_room` has its volume floor lowered by its author (QA) at Gate 1; the zero-fallback assertion stays. Gate 2 checks the macro planner (it still prices a turn) and the shipped PPO rival |
| 72 | `tests/test_server_ws.py::test_keys_move_your_own_rival_and_each_client_gets_only_its_own_payload` expects seat B's `a` to be ignored | "Update it to #55 (Recommended)" | Only that assertion changes: seat B's WASD keys move seat B, and never seat A. The T19 tech-lead makes the change |
| 73 | Kneel art | "Crouch is fine for now (Recommended)" | The crouch strip is drawn for sword pickup, uniform take and rigging. A dedicated kneel sprite is not planned |

## Addendum: Wed 2026-11-25, after midnight (PPO line: T08 Gate 2 items)

Numbered #74 to #77 (first committed as #67 to #70 in 5e6c757, which collided with the other session's #67 to #70; corrected in the next commit). Saad's choices on `reports/T08-evaluation-specialist.md`@059aea5 (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 74 | Held-out size | "Extend to 8 starts (Recommended)" | T08-fix1 adds 4 held-out starts (H6-5 to H6-8; 16 duels with seats swapped), chosen by a rule written down before any cell is picked and never from policy results, then re-freezes `H6.json` with a new SHA-256. H6 has never been run, so nothing is voided |
| 75 | QA F-3, guard patrols overlap | "Accept and document (Recommended)" | The held-out claim is "unseen start pairs and guard layouts", not "unseen cells". T09 reports each start and labels the most training-like starts |
| 76 | B2 and the disguise | "Yes, disguise must last (Recommended)" | Amends #58: B2 succeeds only if the rival is still disguised at the end and the guard's suspicion stayed below 50 throughout. `success_active` stays reported, not scored (#66) |
| 77 | Pre-registered T09 bar | "Approve the bar (Recommended)" | Written into PROTOCOL.md before the run: the rival is called better than the scripted baseline on H6 only with at least 14 wins of the 16 held-out duels (7 of 8 per 4 starts) and no aborted duel. Anything below is reported as "not supported", with the full numbers |

## Addendum: Wed 2026-11-25 (PPO line: T08-fix1 test edits)

Saad's choice on `reports/T08-fix1-tech-lead.md`@645707e (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 78 | Six T08 tests pin values that #74 and #65 changed (4 H6 starts, the old H6 hash, seat A always scripted) | "Allow, by each author (Recommended)" | Each test's author updates only the pinned values, listing old and new in its report: the Tech Lead now (`test_eval_registry.py::test_heldout_split_is_one_full_duel_scenario_h6_with_four_starts`, `test_eval_suite.py::test_heldout_dry_run_uses_wait_seats_checks_the_hash_and_claims_nothing`, `test_eval_suite.py::test_dry_run_writes_one_complete_row_for_every_start_of_every_scenario`); QA at Gate 1 (`test_qa_T08_probes.py::test_a_one_byte_change_is_refused_and_the_real_file_hash_is_the_recorded_one`); the Evaluation Specialist at Gate 2 (`test_eval_T08_gate2.py`, its two H6-size tests). Every other assertion stays |

## Addendum: Wed 2026-11-25 (PPO line: T09 go)

Saad's choice (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 79 | Run the one held-out comparison (T09) now | "Go, run it once (Recommended)" | The Evaluation Specialist first re-checks the shipped weights on the tuning starts on the post-T19 engine; only if that is clean, it runs H6 once on a clean committed tree from `orch/reviewed` 0ea8d73 and commits the results with the ledger. Then QA (Gate 1), an independent read by the rules reviewer, and Gate 3. Not repeated |

## Addendum: Wed 2026-11-25 (PPO line: T09 health criterion)

Saad's choice on `reports/T09-evaluation-specialist.md`@77bc2f7 (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 80 | T09 health check: stale inputs on the scripted seat (identical before and after T19; inputs stranded when a baseline jump ends in a fall) | "PPO seat 0 stale; report baseline (Recommended)" | The T09 health check passes with 0 aborted, 0 fallbacks, 0 invalid on both seats and 0 stale on the PPO seat. The baseline's stale inputs and its falls are reported per duel as a confound. T09 continues to steps 2 and 3 (H6 once). PROTOCOL H-c's "0 for both" is brought in line by a later docs task, not by T09 |

## Addendum: T20 Gate 2 choices (T20-fix1)

Saad's choices after the T20 Gate 1 REJECT (`reports/T20-qa.md`@8139bae) and Gate 2 (`reports/T20-evaluation-specialist.md`@a039283), AskUserQuestion, verbatim. Numbered from #81 because a parallel session took up to #80:

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 81 | How the logger learns what the engine actually did | "Small public read-only accessor (Recommended)" | One read-only method in `pop/` (the move a seat actually started this tick, after R-V10, R-V22 and R-V35 rewrites and stale drops), failing test first. It changes no rule and is never part of a seat's observation. The recorder's "resolved action" column comes only from it |
| 82 | How a grace-cancelled direction appears | "Marker + summary discounts it (Recommended)" | The log stays append-only and real-time. The direction row is written; the jump row carries `"grace": true`; the summarizer drops the superseded direction. QA updates its own F2 xfail to this form at Gate 1 |
| 83 | Summary thresholds | "Idle 3 s, refused 12 ticks, stuck 60 s (Recommended)" | `IDLE_THRESHOLD_S = 3`, `REFUSED_RUN_MIN = 12` (ticks), `STUCK_ROOM_S = 60`; named constants |
## Addendum: Wed 2026-11-25 (PPO line: T09 evidence gap)

Saad's choice on `reports/T09-rules-reviewer.md` finding 1 (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 84 | PPO inference errors (swallowed into WAIT, counted in `policy_errors()`) were not written into the H6 rows | "Reword only (Recommended)" | No policy runs on H6 again. T09-fix1 (docs only) states that the rival's own inference errors were not recorded in the held-out rows, alongside the other review wording fixes. A separate task (T08-fix2) writes `policy_errors` into every evaluation row for future runs |

Saad's choices on the T20-fix1 tech-lead report (`reports/T20-fix1-tech-lead.md`@394ca4f), AskUserQuestion, verbatim (numbered from #85; a parallel session took #84):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 85 | Existing T20 tests that assert the pre-#83 / pre-F3 behaviour | "Authors update them (Recommended)" | Only those assertions change, each listed old → new in its author's report. The Tech Lead updates `tests/test_t20_summarize.py::test_stalls` and `tests/test_t20_telemetry.py::test_connection_events_and_forfeit`. QA updates `tests/test_t20_qa_probes.py::test_real_scripted_duel_summarizes_deterministically`, its F1 xfail mark and its F2 test (to the #82 marker form). Eval removes its E1 xfail mark |
| 86 | Reporting-only engine label `_rewrite` (kick, grace, hop_turn) set in `Duel._start` | "Accept the label (Recommended)" | Kept. It is read only through `VersusEpisode.started_move`. No rule reads it. Gate 2 checks that it changes no trace, hash or observation and that no seat can see it |

## Addendum: Wed 2026-11-25 (PPO line: the trained rival in the game, three modes)

Saad's request in chat (verbatim): "Wire the trained rival into the game, keep going through the gates, make a game mode for the AI Model and a seperate one for the baseline and one for the human vs human"

His choices (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim) | Orchestrator's reading and effect |
|---|---|---|---|
| 87 | Where the three modes are offered | "All three front ends (Recommended)" | pygame `play.py`, the hosted web page and the online server each offer **AI Model**, **Baseline** and **Human vs Human**, from one shared mode list. Task T22 |
| 88 | On-screen names | "Honest names (Recommended)" | "AI Model (trained)" and "Baseline (scripted)" on the menu, the HUD and the end screen. Closes the open `--rival baseline` neutral-label question: honest labels by default (the existing `--neutral` flag may stay as an opt-in for blind tests) |
| 89 | Human seat in the AI modes | "Human players since they are using different machines, they can use either WASD or the arrows, both are valid" | Read with #55: in every mode where each human has their own machine (online, and human vs AI), the player's own seat accepts both WASD and the arrows. Local two-player on one keyboard keeps A = WASD, B = arrows (#55). The human plays seat A in the AI modes; no seat-swap option is added (not asked for) |
| 90 | Timing against T20 | "Start now, merge after T20 (Recommended)" | T22 starts now from `orch/reviewed` 74975e1, with mode code in new modules and thin hooks in `play.py`, `web/` and `server/`; overlap with T20 is resolved at Gate 3 after T20 lands |

## Addendum: Wed 2026-11-25 (PPO line: T22 tech-lead questions)

Saad's choices on `reports/T22-tech-lead.md`@73e6531 (AskUserQuestion), quoted verbatim. Recorded by the PPO-line orchestrator (session 8edb65a6):

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 91 | The legacy `--rival baseline` path (no creator-chosen mode) still shows "AI rival: …" because `tests/test_gate_t13_qa_online.py::test_cli_process_two_scripted_clients_real_clock_and_trace_dir[baseline]` pins it | "Update that test (Recommended)" | Finish #88 there: the legacy label code is removed and that one assertion changes to the honest label "Baseline (scripted)". No other existing-test edit. In T22-fix1 |
| 92 | Default start | "Menu by default (Recommended)" | A bare `python play.py` shows the three-mode menu (the old single-player level stays reachable with a flag and its situation argument), and the hosted page opens on a mode chooser. The web smoke test (`tools/web/smoke.cjs` / `.github/workflows/web-smoke.yml` path) is updated to pick a mode. If any other existing test breaks, stop and report. In T22-fix1 |

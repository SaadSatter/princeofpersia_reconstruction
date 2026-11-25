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

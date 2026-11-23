# AUDIT-A report (Tech Lead subagent, audit mode), 2026-11-23

Lightly condensed by the orchestrator from the subagent's final message (tables and findings kept; prose shortened). Key claims spot-checked by the orchestrator: linear branch chain (rev-list counts 0 on one side for all refs), no `server/` or `web/`, no versus references in `agents/` or `evaluate.py`, `419 passed, 12 skipped` on 13c7488.

Task ID / status: AUDIT-A (architecture, branches, integration). Done, read-only.

Summary:
- All six branches form one linear chain with no merges and no divergence. `final/versus-engine` @13c7488 contains every other branch, so in the dev repo nothing needs merging, only fast-forwarding.
- The versus engine (`pop/versus.py`, `pop/guards.py`) is real. It has two seats on 12 fps ticks, swordplay, 3 hearts, two scripted guards, disguise with suspicion, flips, and win/draw/time-up outcomes. It is tested and reaches terminal outcomes headless.
- Not built: rival-rigged traps with ownership, any AI or scripted seat for versus, the macro-action controller, a versus runner/evaluate/replay, and server/ and web/ (online). The only versus mode that runs is human vs human on one keyboard.
- Moving into the official repo is low-friction. Only 4 file paths collide, and the template's team tests pass alongside the game suite in a trial tree.

Files changed: none (scratch under /home/claude/sm/wt/AUDIT-A only). Commit or diff: none.

Tests executed (`python3 -m pytest -q -p no:cacheprovider`, Python 3.13, pygame and anthropic absent):
- main 0e5df5f -> 170 passed, 4 skipped
- origin/level1-reconstruction d5f6bda -> 192 passed, 4 skipped
- level1-reconstruction 2b5c909 (same tests tree as g1-shadow-masque and agent-setup-online) -> 272 passed, 10 skipped
- final/art-pixellab 3c0b0b4 -> 278 passed, 11 skipped
- final/versus-engine 13c7488 -> 419 passed, 12 skipped (skips: pygame 4, anthropic 1, original L1 file 6, original images 1)
- Smoke (auditor's own script, not in repo): 20 seeds, random legal inputs both seats, time_limit_frames=3600 -> {'won:B': 12, 'won:A': 8}, 0 invalid inputs.
- Trial tree (versus-engine + template team/, tests/, .github/) -> pytest 530 passed, 12 skipped; `unittest discover -p "test_team_*.py"` Ran 111 tests OK; `team validate`: "no agent-team/ yet; run python -m team init".

## 1. Branch ancestry
| Order | Ref | Ahead of previous | Unique content |
|---|---|---|---|
| 0 | main 0e5df5f | — | Midterm (graded record) |
| 1 | origin/level1-reconstruction d5f6bda | +2 | audit.py, Week-7 README, tests |
| 2 | level1-reconstruction 2b5c909 (local) | +10 | Original L1 as scenario (pop/levelfile.py, levels.py, tools/fetch_level1.py), frozen-suite test. Not pushed: remote is 10 behind |
| 3 | final/g1-shadow-masque 1b8d684 | +7 | Docs only: docs/final/ GDD, CONFIGURATION, PROJECT_PLAN, checklist |
| 4 | final/agent-setup-online dbb66ff | +3 | AGENTS.md, CLAUDE.md, Codex reviewer, session-evidence skill, tools/evidence/; online decision (docs) |
| 5 | final/art-pixellab 3c0b0b4 | +8 | assets/generated/ (PixelLab), render/dungeon.py, genart.py, pop/arena.py (6 rooms), approved VERSUS_SPEC |
| 6 | final/versus-engine 13c7488 | +13 (43 ahead of main) | pop/versus.py (1024 lines), pop/guards.py, render/versus_view.py, play.py --versus, 6 new test files, flip audit and review |
All final/* local refs equal their remote-tracking refs. PR state not verified.

## 2. Gameplay on versus-engine (code and tests)
| Feature | Status | Evidence |
|---|---|---|
| Two seats, real-time ticks (12/s) | Implemented | Duel.tick, VersusEpisode; tests/test_versus.py |
| Swordplay: stances, lunge, block, disarm, throw, dive kick, sweep | Implemented | R-V01–R-V12; tests/test_swordplay.py (22 tests) |
| Hearts (3) | Implemented | test_three_hits_kill_and_win_for_the_other_rival |
| Scripted guards: patrol, sight, attack, downed | Implemented, 2 guards | pop/guards.py, arena.GUARD_POSTS; tests/test_guards.py |
| Disguise + suspicion, breaks | Implemented | R-V17–R-V21; tests/test_disguise.py incl. field-for-field leak test |
| Flips | Implemented | R-V22/R-V23; test_flip.py, test_flip_review.py |
| Environmental traps (loose floors, 2 gate plates) hurting anyone | Implemented (inherited + arena) | arena PLATE_LINKS; test_a_falling_floor_downs_a_guard, test_a_plate_pressed_by_either_rival_slams_its_gate |
| Rival-rigged traps (RIG, 4/rival, ownership, leak test) | MISSING | No RIG in VERSUS_ACTIONS; not in VERSUS_SPEC; OQ-6 open |
| Arena | 6 rooms | pop/arena.py |
| Outcomes | Implemented | won:A/B, draw:both_died, draw:time_up; time limit defaults to inherited 60-min clock (OQ-3 open; GDD assumes 5 min) |
| Human controls, two seats | Local only | play.py ARENA --versus, one keyboard, two panels each from its seat's observe() |
| AI or scripted rival seat in versus | MISSING | agents/*, pop/runner.py, evaluate.py use only single-player Episode |
| Macro-action vocabulary + controller | MISSING | CQ-1 open (CONFIGURATION.md:35, :155) |
| Per-seat runner limits, timeouts, fallback, isolation | MISSING | checklist rows "not started" |
| Online server and browser client | MISSING | no server/ or web/ |
| Versus replay | PARTIAL | VersusEpisode.log + determinism test; no CLI or trace file |

## 3. Modes that run today
Human vs human local: runs (`uv run --extra play python play.py ARENA --versus`; not rendered here). Online, human vs AI, AI vs AI: not runnable. Midterm single-player modes still run.

## 4. Conflicts between docs and code
1. Online vs split screen: G1 had split screen in and online out; Saad's 2026-11-16 decision (dbb66ff; GDD.md:28, :49–50, :101) switched to online; what exists is local two-panel; server/web 0% built.
2. Gate date: PROJECT_PLAN/checklist say G2/G3 Mon 30 Nov; FINAL_REQUIREMENTS §6 says Sat Nov 28, 11:59 p.m.
3. Traps: GDD.md:25, :100 describe 2 rival-set types, 4 per rival; VERSUS_SPEC and code have none.
4. Stale text: pop/arena.py docstring says two-seat engine "not built yet"; EVIDENCE_INDEX arena row "planned CQ-1"; README.md is the midterm README; pyproject name pop-level1-reconstruction.
5. VERSUS_SPEC §10 implementation choices and `motion` field still marked for Saad's confirmation.
6. Art: no conflict; L1 fetch tooling is an IP/scope choice for the official repo.
7. Independence: VERSUS_SPEC §9 asks for an independent review after each stage; only the flip has one; stages 1–4 (499eb60..f083454) have none. The flip reviewer was a subagent of the session that then made the fixes (sm-untracked-13.md).
8. Observed, for B/C: a disguised rival's `posture` can be crouching/hanging/falling while real guards only report standing/downed/knocked_down — behavioural tell, not a hidden field.

## 5. Reusable
VersusEpisode five operations per seat; per-seat observe(); Duel.snapshot(); single-player runner (_call_with_timeout, late-reply discard, Limits, Decision, save_trace, cost/latency); agents/providers.py and model_player parsing/history; evaluate.py suite structure; render/versus_view.py helpers.

## 6. Missing for G2/G3 core loop
1. AI rival seat (vocabulary CQ-1, macro→tick controller, scripted baseline on same interface, per-seat runner with 5 s timeout and labelled WAIT fallback, fake-provider tests). 2. One rival-rigged trap with ownership leak test. 3. OQ-3 time limit. 4. Versus trace/replay command and scenario set. 5. Two-player play independent of online. 6. Independent review of stages 1–4.

## 7. Integration strategy
Dev repo: commit session-13 patch; PR versus-engine -> main (fast-forward); optionally push level1-reconstruction; tag main 0e5df5f as midterm record.
Official repo (template 32fa606): game at root; only .gitignore, AGENTS.md, CLAUDE.md, README.md collide. Recommended: branch in official repo, `git merge --allow-unrelated-histories` from dev tip (keeps history, no force push); resolve 4 files (template AGENTS.md + project rules appended; CLAUDE.md imports AGENTS.md; new README; .gitignore union); `python -m team init`, tailor tech/qa, render; final.yml "Your tests" -> `pip install "pytest>=8,<9" && python -m pytest -q`; PR to main, CI green before merge. Alternative: squashed snapshot (loses provenance). Excluding tools/fetch_level1.py / manifest is Saad's IP call.

## Recommended scope cuts
Keep duel and disguise; one rival-rigged trap type (loose floor; G1 cut 3), keep environmental gate plates; defer online past G2/G3, demo with local two-panel (note peeking limitation); AI vs AI test-only; keep 6 rooms and suspicion (already built).

## Plan (failing tests first, then QA gate)
P0 official-repo migration + team init + CI command (needs approval) | P1 macro vocabulary addendum to VERSUS_SPEC (Saad approves) | P2 controller + scripted versus baseline (dep P1) | P3 per-seat runner, cadence, 5 s timeout, WAIT fallback, isolated history, trace/replay (dep P2) | P4 play.py --rival baseline/model, AI vs AI headless (dep P2,P3) | P5 one rigged trap with ownership (dep addendum, OQ-6) | P6 OQ-3 + versus evaluate scenarios | P7 independent review of stages 1–4 and P2–P5.

## Decisions requiring Saad
1 Online defer/cut; 2 trap scope + OQ-6; 3 CQ-1 vocabulary + cadence; 4 OQ-3; 5 gate date correction; 6 migration method + L1/original-asset tooling exclusion; 7 VERSUS_SPEC §10 + motion field; 8 commit/push session-13 patch and level1-reconstruction, open PR; 9 live calls within $5.

Limitations: PR and Gate-decision issue state not verified; pygame not rendered; no live calls; knowledge-boundary depth and agent/tracker compliance left to B, C, D.

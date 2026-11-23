# AUDIT-C report (Evaluation Specialist, audit mode), 2026-11-23

Condensed by the orchestrator from the subagent's final message. Orchestrator checks: OpenAI adapter raises "not implemented" (agents/providers.py:162); `DEFAULT_CALL_TIMEOUT_S = 20.0` (pop/runner.py:37). **Reconciliation note:** this audit found "no leak at the observation level", but it did not probe WAIT; AUDIT-B's F1 (disguised WAIT shows `motion.effect: waited`) was reproduced by the orchestrator and stands. The `minutes_left` claim was not re-checked by the orchestrator.

Tests: full suite 419 passed, 12 skipped; `tests/test_disguise.py tests/test_leakage.py tests/test_flip_review.py` 54 passed.

## Findings
1. Interface: VersusEpisode has reset/observe/legal_actions/step/outcome + runner-only tick. No controller protocol or versus runner, so controllers cannot be swapped per seat; `_duel` is reachable in-process (isolation by convention only).
2. Model player: single-player only. Prompt is about escaping; on a versus observation `build_user_prompt` omits figures, stance, suspicion. No macro vocabulary, no tested per-seat history, no prompt/config version id. Runner blocks on thread.join with 20 s default (plan 5 s); game would stall. Present: cost accounting (unknown = None), late replies, --live gate, credential pre-check. Missing: cumulative budget cap; CLI dry run (`--provider` accepts only anthropic/vertex though FakeProvider exists). OpenAI adapter claimed in CLAUDE.md and CONFIG A3 but not implemented.
3. Baseline: midterm cautious explorer; G1 policy not implemented; RoomView/plan Dijkstra reusable. PROJECT_PLAN criterion "beats a do-nothing rival" is weaker than the G1 competent baseline.
4. Evaluation: evaluate.py runs midterm suites only; no SvS, MvS, SvM, MvM, seat swap; schema lacks seat, prompt version, per-seat termination. Seeds barely change duels (only disarm drop, pop/versus.py:694): held-out must vary starts/guard posts/seats.
5. Live evidence: 20261026T061626Z (06ff044, 4 calls, 3159 ms mean, $0.0093) and 20261026T180142Z (c23ebf7, 4 calls, 3010 ms mean, max 3526, $0.0092), claude-haiku-4-5-20251001, midterm single-player; 20261026T162629Z failed (40 auth failures, $0). G1 figures come from 4 calls; historical, not current build; per-duel figures are extrapolations. Model writes 180–280 tokens of prose before JSON.
6. Replay: in-memory log only; 20/20 random two-seat episodes replayed identically from log.
7. Boundary probes (standing, walking, turning, legal actions, step results, last_result): identical. Design tells: (a) a "guard" that sees you and doesn't attack is the rival; (b) postures guards never show; (c) 1-frame motion:null gap if a controller doesn't queue ahead. Minor: `minutes_left` computed from P.GAME_FRAMES not the duel limit (orchestrator did not re-check). Trap ownership N/A.
8. Spending: present --live, check_credentials, max_calls, tools/smoke_provider.py; missing run-level USD cap, ledger, fake dry-run CLI, per-seat limits.

## Must-build (G2 needs 1–7)
1 Seat-controller protocol + versus runner (copies only; ticks continue during calls; 5 s timeout; labelled fallback; per-seat call and USD caps; per-seat traces; seat swap). 2 Macro layer (BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB; RIG_TRAP later), re-validated each tick, queues ahead, targets by visible attributes only. 3 Versus scripted baseline on macros (same decisions if disguised rival swapped for real guard; never paths to unseen rival). 4 Versus model player, prompt version id, per-seat history; prompt contains no seat/disguise/other-room data. 5 Fallback decision + reconciled docs. 6 Harness: scenario registry, SvS/MvS/SvM (MvM test-only), result schema, --provider fake, --budget-usd. 7 Two-seat trace file, replay command, golden replay test. 8 Fix minutes_left, OpenAI claim, 5 s default. 9 Traps (T4 depends).

## Proposed scenarios (for Saad's approval)
| Id | Split | Initial conditions | Success (predeclared) | Metrics |
|---|---|---|---|---|
| D1 Disguise | tuning | AI undisguised 2 cells from downed uniformed guard; 1 patrolling guard; other rival idle elsewhere; 60 s | Disguised by 20 s and still disguised at 60 s | time to TAKE, peak suspicion, breaks, hearts, invalid, fallbacks |
| B2 Blend | tuning | AI disguised among 2 patrolling guards; scripted undisguised rival enters at 10 s; 60 s | Not struck and disguised at 60 s, or AI lands first strike | + hits taken, walking-only frame share |
| I3 Identify | tuning | AI undisguised, armed; 2 guards + disguised scripted rival; 60 s | First AI strike hits the rival | correct / false identification / missed rival / no encounter |
| T4 Trap | — | blocked until RIG exists | — | — |
| F5 Fight or retreat | tuning | AI 1 heart vs 3, both armed, 3 cells, exit behind AI; 30 s | survive 30 s or win | outcome, hearts, fight/flee |
| H6 Full duel | held-out | starts and guard posts never used in tuning; 5-min limit; model vs scripted both seat assignments | predeclared tally (model need not win) | W/D/L, termination, hearts, disguises, identification events, invalid, calls, latency, tokens, cost, fallbacks, traces, failed runs |

## Cost estimate (estimate, not measured)
~$0.0028–0.0045/call (2–3k in, 150–300 out tokens at $1/$5 per MTok) -> ~$0.21–0.34 per 5-min AI seat. Minimal suite ~661 calls ≈ $1.9–3.0; with 3 trials per tuning scenario ~780 calls ≈ $2.2–3.5. MvM excluded.

Decisions for Saad: CQ-1 vocabulary and figure targeting without ids; fallback WAIT vs baseline; 4 s cadence / 5 s timeout / non-blocking; scenario set and held-out starts; OQ-3 for evaluation; live experiment + hard USD cap; baseline details; which artifact is the [R] extension and manifest (CQ-7); doc fixes.

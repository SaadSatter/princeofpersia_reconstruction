# Final project evidence index

Maps each deliverable in [`REQUIREMENTS_CHECKLIST.md`](REQUIREMENTS_CHECKLIST.md)
to evidence that exists **now**. Session numbers such as `S10` refer to
`docs/agent-sessions/10-*.md`. Only existing evidence is listed; anything
planned is marked *planned*.

Updated 2026-11-16, branch `final/g1-shadow-masque`.

| Deliverable | Evidence that exists | Sessions | Missing |
| --- | --- | --- | --- |
| G1 recording and deck | External links in [`README.md`](README.md) (videos never committed) | — | — |
| G1 GDD | [`GDD.md`](GDD.md); Saad's confirmations: commits `ea7bdc0`, `5046762`, `526bfce` | not yet recorded | Session record for the G1 drafting session (*planned*, `session-evidence`) |
| G1 Configuration Document | [`CONFIGURATION.md`](CONFIGURATION.md) | not yet recorded | Same |
| G1 Project Plan and Risk Register | [`PROJECT_PLAN.md`](PROJECT_PLAN.md); gate dates commit `132f0b8` | not yet recorded | Asana project link (*planned*) |
| Silent-playtester notes | Commit `1b8d684` | — | Notes themselves are Saad's |
| Inherited engine (GDD 5.1) | `pop/`, `tests/` (deterministic suite), `docs/RULE_SOURCE_MAP.md`; midterm sessions S01–S10 | S01–S10 | — |
| Inherited model player and limits | `agents/model_player.py`, `agents/providers.py`, `pop/runner.py`; live run `traces/live/20261026T180142Z` (single player) | S02–S04 | Versus prompts, per-seat isolation (*planned*) |
| Agent configuration | `CLAUDE.md`, `AGENTS.md`, `.claude/agents/rules-reviewer.md`, `.codex/agents/pop-rule-reviewer.toml`, `.claude/skills/game-rules-audit/SKILL.md`, `.claude/skills/session-evidence/SKILL.md` | — | Invocations for the final project (*planned*) |
| Engine choice | [`ENGINE_DECISION.md`](ENGINE_DECISION.md) (recommendation) | — | Saad's decision |
| Art for the online build (OQ-8) | `assets/generated/` with `MANIFEST.tsv`; [`ART_PROVENANCE.md`](ART_PROVENANCE.md); `render/dungeon.py`, `render/genart.py`; `tests/test_generated_art.py`; branch `final/art-pixellab`, PR #1 | S12 | Saad's check of the macOS window |
| Arena (OQ-4) | `pop/arena.py`; `tests/test_arena.py`; full reachability `tools/check_arena.py` (run 2026-11-16: every row of all six rooms from both starts) | S12 | Two-seat starts and guard routes (*planned*, CQ-1) |
| Two-seat engine, swordplay, guards, disguise (VERSUS_SPEC stages 1-4) | `pop/versus.py`, `pop/guards.py`; tests `tests/test_versus.py`, `test_swordplay.py`, `test_guards.py`, `test_disguise.py`; rule map R-V00 to R-V23; flip (R-V22) and step-in-and-settle (R-V23): `tests/test_flip.py`, `tests/test_flip_review.py`; branch `final/versus-engine` | S13 (flip audit, review, fixes); builder sessions not yet recorded | Independent review of stages 1-4 (*planned*, separate session); the flip's audit and review are done (table below), and a re-review of the fixes is *planned* |
| Checkpoint: model call, isolation, timeout | — | — | *planned* |
| First playable, playtest log, scope lock | — | — | *planned* |

## Skill and reviewer invocations for the final project

| Date | Agent or skill | Session | Output | Independent of the builder? |
| --- | --- | --- | --- | --- |
| 2026-11-16 | `session-evidence` | S12 (`e2b80258`) | `docs/agent-sessions/12-pixellab-art-and-arena.md` | Records the builder's own session |
| 2026-11-25 | `session-evidence` | S20 (`a45fface`) | `docs/agent-sessions/20-orchestrator-gameplay-telemetry.md` | Records the orchestrator's own session |
| 2026-11-23 | `session-evidence` | S13 (`f4d83b8a`) | `docs/agent-sessions/13-flip-audit-review-fixes.md` | Records its own session (audit, review, then fixes) |
| 2026-11-18 | `game-rules-audit` | [S13](../agent-sessions/13-flip-audit-review-fixes.md) (`f4d83b8a`) | [`docs/audits/AUDIT-2026-11-18-flip-r-v22.md`](../audits/AUDIT-2026-11-18-flip-r-v22.md) (flip, commits `8c2d9bd`, `05fe136`) | Yes: run in a session other than the one that built the flip |
| 2026-11-18 | `rules-reviewer` agent | [S13](../agent-sessions/13-flip-audit-review-fixes.md) (`f4d83b8a`), subagent | [`docs/reviews/INDEPENDENT-REVIEW-flip-r-v22.md`](../reviews/INDEPENDENT-REVIEW-flip-r-v22.md) (unedited) | Yes from the builder; started from the audit session, and read the audit's findings after forming its own |

Add a row only when a transcript or committed report shows the invocation.
A subagent spawned by the implementing session is not an independent review.

## Art candidate download — 2026-11-16

[Session 11](../agent-sessions/11-free-dungeon-art-download.md) records SakPix free-demo acquisition and renderer fit constraints. Not integrated; redistribution unresolved; OQ-8 remains open. The session-evidence skill was read and applied in this Codex session; this is not an independent rules audit.

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
| Checkpoint: model call, isolation, timeout | — | — | *planned* |
| First playable, playtest log, scope lock | — | — | *planned* |

## Skill and reviewer invocations for the final project

| Date | Agent or skill | Session | Output | Independent of the builder? |
| --- | --- | --- | --- | --- |
| — | none yet | — | — | — |

Add a row only when a transcript or committed report shows the invocation.
A subagent spawned by the implementing session is not an independent review.

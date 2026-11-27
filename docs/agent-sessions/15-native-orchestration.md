# Session 15: native orchestration (Opus orchestrator, Sonnet workers, file-based handoffs)

| Field | Value |
| --- | --- |
| Tool / role | Claude Code (CLI) 2.1.331. The refactor session ran under the old `CLAUDE.md` (Tech Lead role), on Saad's explicit authorization to change the orchestration configuration. It started a headless child session that ran as the new Production Orchestrator |
| Session IDs / models | Refactor: `fb28fc89-cd66-4fc9-b8a9-688a47a62dad`, `claude-opus-5-5`. Probe: `197da38f-bc94-43b5-a5f7-6e359ba8c693`, main `claude-opus-5-5`, subagent `tech-lead` on `claude-sonnet-5-5`. Smoke test: `50115623-eb0d-4b3c-86b0-2c9326dbfa3d`, main `claude-opus-5-5`, subagents `tech-lead` and `qa` on `claude-sonnet-5-5`. All from transcript metadata (`tools/orchestration/verify_models.py`) |
| Date | 2026-11-24 (America/New_York) |
| Branch | `main` (orchestration records only, decision #11 and this request) |
| Independence | Builder session for the configuration. SMOKE-01's QA ran as a separate Sonnet subagent in its own worktree and read the Tech Lead's committed report. It is a configuration smoke test, not a review of gameplay |
| Session URL | None. Local session; no shareable URL was created. |
| Transcript | Local only, not committed |

## Saad's instructions (quoted, truncated)

- "Formalize the current Shadow Masque orchestration workflow into a reusable, repository-configured Claude Code agent hierarchy … every normal project request to first reach a central Production Orchestrator running Claude Opus 5.5 … delegate … to native Claude Code subagents running Claude Sonnet."
- "The agents must communicate through real, persistent, file-based handoffs tracked in GitHub."
- "I authorize changes to: CLAUDE.md, .claude/settings.json, .claude/agents/, Relevant .claude/skills/, Existing orchestration documentation. Agent configuration manifest. Supporting orchestration verification tests and documentation."
- "Commit the isolated orchestration changes to main, preserving unrelated work."

## What happened

- **Audited:** `main`, `orch/reviewed`, `orch/preview` and the three `orch/wip-*` snapshots (ancestry, commits). The official repository's `team/` scaffolding was read through `gh api`. Subagent and settings docs were read through a `web-fetch` subagent.
- **Verified capabilities by probe** (not only docs): the `agent` key in `.claude/settings.json` takes effect. `disallowedTools: Agent(...)` removes the whole Agent tool on 2.1.331, but a `tools: Agent(name, …)` allowlist works: `general-purpose` was refused and `tech-lead` ran on `claude-sonnet-5-5`.
- **Built:** the native orchestrator and four Sonnet workers, `rules-reviewer` pinned to Sonnet, a routing `CLAUDE.md`, the orchestrator procedure, `HANDOFF_PROTOCOL.md`, the report template, `COURSE_ROLE_MAP.md`, the `evaluate-rival` skill, `agent-config.json`, `verify_models.py` and its tests.
- **Imported** `docs/final/orchestration/**` from `orch/preview` 87606b9 unchanged. No other preview content.
- **Smoke test SMOKE-01:** a headless `claude -p` session under the committed settings committed a brief. It spawned `tech-lead`, which committed a report on `task/SMOKE-01`. It spawned `qa`, which read that report at fc16525 and committed its own on `gate/SMOKE-01-qa`. It then ran Gate 3 and committed the review log and status.
- **Fixed after the smoke test:** agent commit authorship, the `source_commit` wording, the QA minor finding in `CLAUDE.md`, and the documented worktree test counts.
- **Not done:** nothing was pushed. The `agent` setting was not verified in a Claude Code cloud session. No gameplay was changed. The `orch/wip-*` branches were not touched. `docs/agent-sessions/README.md` and `docs/final/EVIDENCE_INDEX.md` were not updated, because both have Saad's uncommitted edits.

## Commits (verified with `git log`)

| Commit | Author shown | Message |
| --- | --- | --- |
| 391089f | SaadSatter (refactor session) | docs: import orchestration records from orch/preview 87606b9, unchanged |
| 2d40972 | SaadSatter (refactor session) | orchestration: native Opus orchestrator and Sonnet workers with file-based handoffs |
| 58ea6e7 | SaadSatter (smoke orchestrator, Opus) | orchestration: SMOKE-01 brief |
| fc16525 | SaadSatter (tech-lead worker, Sonnet) on `task/SMOKE-01` | SMOKE-01: tech-lead report |
| 3bb36f5 | SaadSatter (qa worker, Sonnet) on `gate/SMOKE-01-qa` | qa: SMOKE-01 gate report |
| 44d02e2 | SaadSatter (smoke orchestrator, Opus) | orchestration: SMOKE-01 chain, Gate 3 closed, verified models |
| 2a76b0d | SaadSatter (refactor session) | orchestration: fixes exposed by the SMOKE-01 handoff chain |

All of them carry a `Co-Authored-By: Claude … 5.5` trailer. The "Author shown" column is why 2a76b0d now requires an explicit `--author` for agent commits.

## Tests

- `uv run pytest -q` in the main checkout: **459 passed, 1 skipped** (verified, this session, after 2a76b0d).
- SMOKE-01 Gate 3 in a worker worktree: 435 passed, 12 skipped (the orchestrator's report; the skip reasons were re-checked in this session: no gitignored data, no pygame).

# Change summary for the independent reviewer — session 02

For `.claude/agents/rules-reviewer.md`, run in a **separate** session that did
not write this code. Commits `8a1fbf0..` (see `docs/agent-sessions/02-agent-evaluation.md`).

## What changed

1. **Runner (R-D22)** — `pop/runner.py`: `Decision.fallback_reason`. A reply
   with no parseable action → `WAIT`, `source: "fallback"`, counted in
   `failed_calls` and `fallbacks`, metadata kept. Parseable illegal actions
   stay the model's and count as invalid. Episode `usage` and `latency_ms`
   summary added. Tests: `tests/test_runner.py` (last three tests).
2. **Baseline** — `agents/baseline.py`: visible-room Dijkstra planner with a
   hand-coded rules model plus room memory. No engine imports
   (`tests/test_architecture.py`). Tuned on S1–S3 only.
3. **Model player** — `agents/model_player.py`, `agents/providers.py`:
   one call per action, JSON reply, `history` (8 steps + seen rooms) and
   `obs-only` variants; Anthropic/Vertex adapters, SDK retries off, dated
   price table. Tests: `tests/test_model_player.py` (fake provider only).
4. **Evaluator** — `evaluate.py`: suites `tuning`/`final`, `--live` gate,
   held-out only in `final`, traces + results + table.
5. **CI** — `.github/workflows/ci.yml` (dev), `ci/midterm-saadsatter.yml`
   (course), `tests/test_ci_workflow.py`.

## Questions worth checking

- Does any part of the model prompt (`SYSTEM_PROMPT`) act as a hint beyond
  the published rules (e.g., "raised plate opens something, maybe in another room")?
- Is the baseline a fair competitor, given its rules model is code and its
  compute is unbounded? Is the ceiling effect (12/12) a problem for 4b?
- Does R-D22 risk hiding model failures (counting an unparseable reply as a
  fallback rather than an invalid action)?
- Self-audit findings F-1 (abandoned timeout thread) and unknown-cost
  flagging in `docs/audits/AUDIT-2026-10-26-session02-agents.md`.

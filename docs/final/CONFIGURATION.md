# Shadow Masque — Configuration Document

**Version:** Initial (G1), 2026-11-15
**Owner:** Saad Satter, as Tech Lead; approved as Creative Director
**Gate approver:** instructor
**Drafted by:** the implementation agent (Claude Code). Saad reviews and owns every decision in this file.

This document follows reader Section 5.2. It covers the **in-game agent** (the AI rival) and the **production agents** (the team that builds the game). The two are kept separate: production agents may read the repository; the in-game agent sees only one player's observation.

Labels:

- **[Implemented]**: exists from the midterm, with tests.
- **[Planned]**: designed, not built.
- **[Open]**: undecided, listed as `OQ-n` in the [GDD](GDD.md#open-questions) or `CQ-n` below.

---

## Part A — In-game agent: the AI rival

### A1. Purpose and bounded behaviour [Planned]

The AI rival fills one or both player seats. About every 4 seconds it reads its own player's observation and chooses one legal **macro-action**:

| Macro-action | Meaning |
|---|---|
| `BLEND` | Walk a guard route at guard pace |
| `DISGUISE` | Take the uniform of a downed guard in reach |
| `RIG_TRAP` | Rig a loose floor or gate plate in reach |
| `WAIT` | Stand still |
| `FOLLOW <figure>` | Shadow a visible figure |
| `STRIKE <figure>` | Attack a visible figure |
| `FLEE` | Leave the room by the nearest exit |
| `CLIMB` | Climb to the reachable ledge |

The engine expands each macro-action into per-frame inputs, so frame-level fencing stays scripted. The exact vocabulary is open (CQ-1).

### A2. Context sources and knowledge boundary

| Source | Given to the agent? |
|---|---|
| Its own player's observation: own room tiles, figures in view, own health, suspicion and disguise state | Yes |
| Its legal macro-actions | Yes |
| Its own last N actions and outcomes (bounded history) | Yes (N is CQ-2) |
| The other rival's identity when disguised | **No.** A disguised rival is a "guard" in the observation. |
| Which tiles are rigged, and by whom | **No**, except tiles it rigged itself |
| Other rooms, guard patrol scripts, RNG seed, `GameState` | **No** |
| Repository, files, rule map, evaluator | **No** |
| Anything a browser client could not see | **No.** Online, the AI seat runs on the server and gets exactly the per-seat observation a browser receives |

The midterm already enforces "players never get the engine": agents receive copies of the observation dict and the legal-action list, and the runner calls `step` ([Implemented]: `pop/interface.py`, `pop/observation.py`, `pop/runner.py`, hidden-information tests in `tests/`). The new hidden facts, disguise identity and trap ownership, need new leak tests ([Planned]).

### A3. Model and settings

| Setting | Value | Label |
|---|---|---|
| Provider | Anthropic by default; OpenAI and Vertex adapters exist | Implemented (`agents/providers.py`) |
| Model | `POP_MODEL` environment variable; default Claude Haiku 4.5 | Implemented |
| Credentials | `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / Vertex ADC from the environment only; never committed or logged | Implemented |
| Prompt / system instructions | `agents/model_player.py`, to be extended for versus play | Implemented (single player); Planned (versus) |
| Output | One action from the legal list, parsed and validated | Implemented |

### A4. Limits, timeout, retry, spending

| Limit | Value | Basis |
|---|---|---|
| Decision cadence | 1 call per ~4 s of game time per AI seat | Design estimate (CQ-3) |
| Call timeout | 5 s | Measured mean latency 3.0 s, max 3.5 s (run `traces/live/20261026T180142Z`) |
| Retries | 0; a failed call goes straight to fallback | Keeps the duel moving |
| Calls per duel | ≤ 100 per AI seat | 300 s ÷ 4 s = 75, plus margin |
| Cost per duel | ≤ $0.25 per AI seat (estimate: $0.17) | $0.009185 for 4 calls in the same run ≈ $0.0023 per call |
| Live budget before G2 | $5 total | Decision requested at G1 |

These are estimates from a single-player run. Versus prompts will be larger. They must be re-measured (CQ-4).

### A5. Failure modes and fallback

| Failure | Handling | Label |
|---|---|---|
| Timeout or provider error | Scripted-baseline action, logged with `"source": "fallback"` | Implemented (midterm runner) |
| Unparseable reply | Same fallback; counted as a failed call | Implemented |
| Illegal action | Refused, counted, no state change | Implemented |
| Leaks: acting on hidden information | Cannot happen by design (the agent never receives it); leak tests check the observation | Planned tests |
| Too slow to be fun | Shorter cadence or scripted rival only (cut order) | Open (OQ-9) |

### A6. Scripted baseline

Same observation and same actions. Policy: take the nearest available uniform, then walk the shortest path to the other rival and strike when adjacent. Built on `agents/baseline.py` ([Implemented] for single player; [Planned] for versus).

### A7. Evaluation

- **Deterministic (CI, no network, no keys):** rule invariants for sword, disguise and traps; hidden-information tests for disguise identity and trap ownership; a fake-provider test for timeouts and the call limit; same seed gives an identical trace.
- **Live (only with `--live`, never in CI):** AI vs scripted and AI vs AI duels on fixed seeds; record win/draw/loss, invalid actions, fallbacks, latency, tokens and cost.
- **Playtest question:** do players misidentify the disguised AI rival more often than the scripted one, and rate it more tense (1–7)?

### A8. Logging and human override

- Every call is logged by the runner: model id, latency, tokens, cost estimate, raw response, parsed action, fallback flag ([Implemented]).
- No player text and no credentials are stored.
- **Human override:** the human can quit, switch a seat to scripted, or switch to human vs human at any time ([Planned]).

### A9. Executable artifacts and commands

| Artifact | Path | Label |
|---|---|---|
| Player interface (five operations) | `pop/interface.py` | Implemented |
| Observation | `pop/observation.py` | Implemented |
| Runner (limits, timeouts, traces) | `pop/runner.py` | Implemented |
| Model player and provider adapters | `agents/model_player.py`, `agents/providers.py` | Implemented |
| Scripted baseline | `agents/baseline.py` | Implemented |
| Test command | `uv run pytest -q` | Implemented |
| CI workflow (development) | `.github/workflows/` | Implemented |
| CI workflow (course copy) | `ci/midterm-saadsatter.yml` | Implemented; a final-project copy is CQ-5 |
| Game server (online play; the AI seat runs here) | `server/` (proposed) | Planned |
| Browser client (draws one seat's observation) | `web/` (proposed) | Planned |

---

## Part B — Production agents and role coverage

The student remains Executive Producer and Creative Director. Agents recommend; Saad decides. The instructor approves gates.

### B1. Configured agents

| Agent | Executable artifact | Purpose | Context | Tools / permissions | Outputs → recipient | Evaluation | Human approval boundary |
|---|---|---|---|---|---|---|---|
| **Implementation agent** [Implemented] | `CLAUDE.md` | Build and change the game | Whole project folder; original source read-only | Edit code, tests and docs; run tests; no secrets, no merge | Branch, passing tests, change summary → rules-reviewer, then Saad | Tests green; reviewer findings | Saad merges; never approves its own work |
| **`game-rules-audit` skill** [Implemented] | `.claude/skills/game-rules-audit/SKILL.md` | Audit the player interface, hidden-state leaks, legal actions, limits | Spec, rule map, interface/runner/agent code, tests | Read, run deterministic tests, write `docs/audits/` | Dated audit report → Saad | Findings checked against code | Saad accepts or rejects findings |
| **`rules-reviewer`** [Implemented] | `.claude/agents/rules-reviewer.md` | Independent read-only review | Change summary, diff, rule map, code, tests | Read, Grep, Glob only | Findings `[blocking / should fix / note]` → Saad | Fresh context that did not write the change | Cannot approve or merge |
| **AI rival** (in-game) | `agents/model_player.py` | Play a seat (Part A) | One player's observation only | Submit one action per call | Action → runner | Section A7 | Live runs only when Saad passes `--live` |

### B2. Role coverage map (reader Section 3.3)

| Development role | Covered by | Coverage at G1 |
|---|---|---|
| **Producer** | Saad, with the implementation agent drafting plans | Planned: [`PROJECT_PLAN.md`](PROJECT_PLAN.md); moves to Asana after G1 |
| **Design Lead** | Saad; implementation agent drafts the GDD and rule-map rows | Planned: [`GDD.md`](GDD.md), `docs/RULE_SOURCE_MAP.md` |
| **Tech Lead** | Implementation agent | Implemented for the midterm engine; Planned for versus |
| **Art Lead** | Saad; placeholders drawn in code (`render/draw.py`) | Partial: no art agent; OQ-8 |
| **Narrative and Audio** | Not needed: no story beyond the premise, no sound | Excluded by scope |
| **QA** | `game-rules-audit` skill + `rules-reviewer` + CI tests | Implemented |
| **Business Intelligence** | `evaluate.py` result tables; Saad interprets playtests | Partial: playtest log format is CQ-6 |
| **Publishing and Release** | Saad; README run instructions; hosting the game server (GDD OQ-10) | Planned |

### B3. Handoffs

1. Saad (Design Lead) → implementation agent: a rule with its acceptance test, for example "a rigged floor drops whoever steps on it, including the rival who rigged it; the other rival's observation shows the tile as normal".
2. Implementation agent → rules-reviewer: change summary and diff.
3. Rules-reviewer → Saad: findings. Saad decides; blocking findings go back to the implementation agent.
4. The `game-rules-audit` skill runs after any change to `pop/interface.py`, `pop/observation.py` or `pop/runner.py`.

## Open configuration questions

| ID | Question | Needed by |
|---|---|---|
| CQ-1 | Final macro-action vocabulary for versus play | Rival-seat work |
| CQ-2 | History length N given to the AI rival | First live tuning run |
| CQ-3 | Decision cadence (4 s assumed) | First playtest |
| CQ-4 | Re-measured latency and cost with versus prompts | First live tuning run |
| CQ-5 | Course CI workflow path for the final project | Before transfer to the course repo |
| CQ-6 | Playtest log format (reader Section 5.9) | First playtest |
| CQ-7 | Whether to add a course `agent-config.json` manifest for the final project | Before G2 |
| CQ-8 | Where the AI seat's API key lives once the server is hosted (host secret store, never the browser) | Before hosting |

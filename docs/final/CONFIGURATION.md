# Shadow Masque — Configuration Document

**Version:** Initial (G1), 2026-11-15; "Changes since the last gate" added 2026-11-24 and refreshed 2026-11-26 (task T10b)
**Owner:** Saad Satter, as Tech Lead; approved as Creative Director
**Gate approver:** instructor
**Drafted by:** the implementation agent (Claude Code). Saad reviews and owns every decision in this file.

## Changes since the last gate (G1 → G2/G3, as of 2026-11-26)

Dated 2026-11-26 (task T10b). It covers Saad's decisions #31 to #118 and **supersedes the 2026-11-24 entry below wherever they differ**; that entry is kept as history. Sources: [`orchestration/DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md) (#1 to #25), [`orchestration/DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (#26 to #102, which also holds 2026-11-25 and 2026-11-26 entries), [`orchestration/DECISIONS-2026-11-26.md`](orchestration/DECISIONS-2026-11-26.md) (#103 to #118). `main` (PR #11, a93d36a) holds the rival, weights, macro layer, versus runner, evaluation suite, online server, web build and telemetry. The three-mode menu, kneel-takes-uniform and online polish (T22, T24, T25) are on `orch/reviewed` dfe2d90 (PR #12, open). Task state: [`TRACKER.md`](TRACKER.md), [`orchestration/STATUS.md`](orchestration/STATUS.md).

**2026-11-24 statements now superseded:** "no PPO weights exist" (they do: `agents/rl/weights/ppo-run-1.json`, SHA-256 `80e4a110...ba4c`); "the rival, macro layer, versus runner and web build are on `orch/preview` (in review)" and "the evaluation suite is on `orch/wip-T08`" (all closed at Gate 3 and on `main`); "online human vs human deferred" and "no game server for G2/G3" (reversed by #35 to #38; the server is built); "no PPO weights ... nothing verified by a playtest" (still no external playtest, but the held-out comparison T09 was run once, below).

| Area | Change | Source |
|---|---|---|
| In-game agent | Unchanged in kind: a small PPO policy, not the LLM. It is now trained and shipped. Weights `agents/rl/weights/ppo-run-1.json`, SHA-256 `80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c`, loaded only after the hash check; a wrong or missing file refuses to load, never a quiet switch to the baseline. Training: seed 0, 2 workers, numpy `train` extra, 4,800 s cap, 1,568 updates, 1,487,955 steps, 0 policy errors, one run | #3, #50, #51; `RL_POLICY.md` |
| Training rules | Stop on the first policy or encoder error, write no weights, exit 2 (#47). Withhold the file after a failed final check (`weights.failed.json`, #50). The AI rival does not rig traps; `RIG_TRAP` stays masked for it (#43). About 6 tuning starts were added, disjoint from H6 (#44) | #43, #44, #47, #50 |
| Macros | `CLIMB` goes up and down safely, no new macro name (#31). A jump away from the facing turns at once (#71). Macro cadence (4 decisions), nearest-figure targeting and reward defaults are still waiting on Saad | #31, #71 |
| Evaluation | Scenarios D1, B2, I3, F5 (tuning, with mirrored seat-B starts) and H6 (held-out: 8 starts, 16 duels, frozen by SHA-256). B2: the rival is still disguised and suspicion stayed below 50 of 100. D1: the other rival never in the agent's room. Run-once key: weights SHA-256 plus engine commit. Pre-registered bar: at least 14 of 16 wins, no aborted duel. **T09, the one held-out run: 13 W, 2 D, 1 L, bar not met, "NOT SUPPORTED".** The rival's own inference errors were not recorded in those rows (#84, wording only). Weights kept, no retraining | #58 to #66, #74 to #80, #84; `evaluation/RESULTS-T09.md` |
| Online server | `python -m server` (extra `online`, websockets): rooms with a 4-letter code, one authoritative `GameState` per room, only the seat's own view sent. The live AI seat gets at most 0.04 s per decision, then a labelled, server-logged `WAIT` fallback that never aborts a duel (evaluation keeps the 5 s runner timeout and the abort rule). Pause 15 s then forfeit; silent drop noticed in about 6 s; rematch only when both press the button. Limits: 10 failed joins per connection per minute, 50 rooms, rooms expire after 10 min with no second player or 15 s empty. AI and Baseline online are private one-click matches with no room code | #35 to #38, #41, #45, #46, #48, #49, #52, #56, #57, #95 to #97, #102; `ONLINE_PLAY.md` |
| Modes | AI Model (trained), Baseline (scripted), Human vs Human in pygame, the hosted page and the server, from one list; honest names on screen; `--neutral` stays an opt-in for blind tests | #87, #88, #91, #92; `GAME_MODES.md` |
| Telemetry | Optional host-side event log (`--playtest`, off by default), no player names; a summarizer with thresholds idle 3 s, refused run 12 ticks, stuck 60 s; read-only accessor for the move a seat started; a native `telemetry-analyst` that counts and never interprets | #67 to #69, #81 to #83, #85, #86; `playtest/TELEMETRY.md` |
| Dependencies | Optional extras `train` (numpy>=2,<3) and `online` (websockets>=13,<16). Neither is in `dev`. `ci.yml` did not install `online`, so CI was red on `main` on 2026-11-26; T29 fixes it | #34, #37, #40, #117 |
| Hosting | The G2/G3 server is Saad's laptop on a LAN (no new service or account). The static page (Pyodide 0.27.7, Phaser 3.88.2) is a second, human-vs-AI build; the GitHub Pages deploy returned 404 on 2026-11-26 and no page URL is recorded. No API key is held in any browser | #12, #13, #25, #36 |
| Production agents | Added the native `telemetry-analyst` (Sonnet): reads playtest logs, reports counted facts, writes its report only; not a formal course production agent (#69). Workers, gates and model verification are unchanged (B0) | #16, #69 |
| Spending | Unchanged: under $1 total, smoke only (#8). The PPO rival and its training make no paid call | #8 |
| Process | The official repository gets a copy of the game and gate files with its template kept (#104). The Student decision for the routed handoff (the T18 chain) is Saad's to write (#116). PR #6 is refreshed by T10b, not merged as it was (#117, amends #103). Gameplay is frozen after T23-fix1 (#118) | #103, #104, #116 to #118; `SCOPE_LOCK.md` (draft) |

**Not yet verified:** online play on two real machines, a hosted page URL, and any external playtest. Nothing here claims the game is fun or balanced.

### Changes since the last gate (as of 2026-11-24, kept as history; superseded in part by the entry above)

The G1 text below is kept. Superseded statements carry an inline marker. Sources: [`orchestration/DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md) (#1 to #25), [`orchestration/DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (#26 to #30), and the files named in each row. `main` holds the merged G1 engine and the orchestration records; the rival, macro layer, versus runner and web build are on `orch/preview` (in review) and the evaluation suite is on `orch/wip-T08` (unreviewed). Branch state: [`orchestration/STATUS.md`](orchestration/STATUS.md).

| Area | Change | Source |
|---|---|---|
| In-game agent | The AI rival is a **small PPO policy we train** (actor and critic MLP 2x64, masked softmax, stdlib inference), not the LLM. Claude Haiku 4.5 (`agents/model_player.py`) is the **legacy** midterm rival and is not the G2/G3 rival | #3; `agent-config.json` |
| Macro vocabulary | BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, SEARCH, plus RIG_TRAP once traps exist. CQ-1 closed | #23 |
| Cadence | Runner decisions every 6 frames (0.5 s); the policy picks a new macro at most every 4 decisions (2 s). Replaces "about every 4 s". The 4-decision value is still waiting on Saad | #24; `STATUS.md` "Waiting on Saad" |
| Timeout and fallback | 5 s controller timeout; failure gives a labelled `WAIT` fallback, counted per seat; a run over its fallback limit is "aborted", reported, never dropped | #24 |
| Evaluation | One controller object in both seats is refused; evaluation runs pass a secret `seed_key`. Scenarios D1, B2, I3, F5 (tuning) and H6 (held-out), success defined by Saad, frozen before any comparative run | #24, #9 |
| Duel limit | 5 minutes = 3,600 frames (OQ-3 closed) | #5 |
| Spending | Paid calls capped under $1 total, smoke test only; replaces the G1 $5 cap. The PPO rival needs no paid call | #8 |
| Rules the rival sees | R-V24 (+48 suspicion per hop), R-V25 (masking), R-V26 (`TAKE` always legal) | #18, #17, #15 |
| Hosting | Hosted static build: Pyodide 0.27.7 and Phaser 3.88.2; no game server and no API key in the browser for G2/G3. Online human vs human deferred | #1, #12, #13, #25 |
| Production agents | Replaced the G1 single implementation agent with a native orchestrator and named Sonnet workers and file-based handoffs. Manifest `agent-config.json` added (CQ-7) | #16, #27 to #29; commit 2d40972 |
| Tracker | In this repository for now; official-repository move due Sat 28 Nov, 11:59 p.m. This replaces "moves to Asana after G1" | #10, #6 |

Nothing in the rows above is verified by a playtest, and no PPO weights exist.

---

This document follows reader Section 5.2. It covers the **in-game agent** (the AI rival) and the **production agents** (the team that builds the game). The two are kept separate: production agents may read the repository; the in-game agent sees only one player's observation.

Labels:

- **[Implemented]**: exists from the midterm, with tests.
- **[Planned]**: designed, not built.
- **[Open]**: undecided, listed as `OQ-n` in the [GDD](GDD.md#open-questions) or `CQ-n` below.

---

## Part A — In-game agent: the AI rival

### A0. Current in-game agent, as of 2026-11-26: the PPO rival

This subsection supersedes A1 to A9 below (the G1 LLM rival, kept for the record) wherever they differ. Machine-readable form: [`agent-config.json`](../../agent-config.json) (on `main`, dated 2026-11-24; its `status_note` is stale and says no weights exist; refreshing it is outside T10b's write paths and is reported to the orchestrator).

Label key for this subsection (2026-11-26): **main** = on `main` (PR #11); **reviewed** = on `orch/reviewed` (PR #12, open), not yet on `main`; **Planned** = not built.

| Item | Current configuration | Source | Status |
|---|---|---|---|
| Purpose | Drive one rival seat in the duel: choose bounded macro-actions from that seat's own observation, compared against a scripted pathfinding baseline on the same interface | #3 | main |
| Model | Small PPO policy: actor and critic MLP 2x64 tanh, masked softmax over the macro slots; inference is pure Python (`agents/rl/policy.py`), argmax over allowed macros | #3; `RL_POLICY.md` | main; trained weights shipped (see Weights) |
| Training | `tools/rl/train.py` (numpy, fixed seeds). Default time cap 5,100 s. **Run once** (Saad's go-ahead, #51): seed 0, 2 workers, 4,800 s cap, 1,568 updates, 1,487,955 steps, 0 policy errors | #51; `RL_POLICY.md` | main |
| Macro vocabulary | BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, SEARCH, RIG_TRAP (`agents/macros.py`). The expander turns each macro into per-frame inputs, so fencing stays scripted. RIG_TRAP is masked for the PPO rival: the AI does not rig traps (#43). CLIMB goes up and down (#31) | #23, #31, #43 | main |
| Cadence | The runner asks every 6 frames; the policy picks a macro when the last one is no longer running, or every 4 decisions, otherwise the running macro continues. The 4-decision value is waiting on Saad | #24; `RL_POLICY.md` | main |
| Target rule | A macro's target is the nearest figure that is not downed (a fixed rule on observed positions); the policy learns when to strike, follow, flee or blend, not whom | `RL_POLICY.md` | main. Targeting still waiting on Saad |
| Knowledge boundary | The encoder turns one seat's observation into 251 features: room tiles (150), edges (2), the seat's own state (18), suspicion (2), swords on the floor (4), the 3 nearest figures (60), its own macro history (15). It reads only the observation and its own controller status, never `minutes_left`, `outcome()`, ids, the task text or the seed, and keeps no duel clock. A disguised rival and a guard with the same observed fields give the same features. The mask (`macro_mask`) is a necessary condition only | `RL_POLICY.md` "What the rival sees" | main |
| Weights | A plain JSON file, format `sm-ppo-mlp-1`, loaded only with its recorded SHA-256 (`load_net(path, sha256)` refuses a missing or wrong hash). Shipped: `agents/rl/weights/ppo-run-1.json`, SHA-256 `80e4a110...ba4c` | `RL_POLICY.md` | main |
| Limits | 3,600 frames per duel; decisions every 6 frames; controller timeout 5 s | #5, #24; `agent-config.json` | main |
| Fallback | An inference error returns `WAIT` and is counted; a runner failure is the runner's labelled `WAIT` fallback (`"source": "fallback"`), counted per seat; a run over its fallback limit is "aborted" and reported. Online, a live AI seat's fallback is logged and counted but never aborts the duel (#49), with a 0.04 s answer budget (#45) | #24, #45, #49 | main |
| Spending | Paid calls capped under $1 total, smoke test only. The PPO rival makes no provider call, so tokens and cost are N/A for it | #8 | unchanged; the PPO rival and its training make no paid call |
| Evaluation | Deterministic tests (`tests/test_rl_encoder.py`, `test_rl_policy.py`, `test_rl_train.py`, `test_versus_runner.py`, leak tests). Scenarios D1 (down a guard and take its uniform with the other rival never in the agent's room, #59), B2 (the rival is still disguised and the guard's suspicion stayed below 50 of 100, #58, #76), I3 (strike the disguised rival, not a real guard), F5 (win a duel against the rival or a guard) and held-out H6 (8 starts, 16 duels, frozen). Success criteria frozen before any comparative run. **T09 result: 13 W, 2 D, 1 L; bar 14 of 16 not met; "NOT SUPPORTED"** (`evaluation/RESULTS-T09.md`) | #9, #58, #59, #74 to #77; `agent-config.json` | main |
| Scripted baseline | `agents/versus_baseline.py`: pathfinding and visible tells, same controller interface, labelled `kind: scripted`. It is the competent comparison, and a selectable mode ("Baseline (scripted)") | #3, #87; `agent-config.json` | main |
| Legacy LLM rival | `agents/model_player.py`, Claude Haiku 4.5 via `POP_MODEL`; the midterm rival, kept working, not the G2/G3 rival. Any LLM use is slow-timescale only and out of G2/G3 scope | #3, #8 | main (single-player) |
| Known limits | Trained once, and the held-out comparison did not show an improvement over the baseline at the pre-registered bar, so there is no strength claim; target fixed to nearest figure; only a few tuning starts, so some over-fitting is expected; the rival never rigs traps. In the static web build the whole state lives in the browser, so devtools could read hidden state: acceptable for human vs AI, not for online human vs human | `agent-config.json` | — |

### G1 text (LLM rival), kept for the record

### A1. Purpose and bounded behaviour [Planned]

*[Superseded 2026-11-23, decisions #3, #23, #24: see A0. The rival is a PPO policy; CQ-1 is closed.]* The AI rival fills one or both player seats. About every 4 seconds it reads its own player's observation and chooses one legal **macro-action**:

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

*[Superseded 2026-11-23, decision #3: these rows describe the legacy LLM player. See A0.]*

| Setting | Value | Label |
|---|---|---|
| Provider | Anthropic by default; OpenAI and Vertex adapters exist | Implemented (`agents/providers.py`) |
| Model | `POP_MODEL` environment variable; default Claude Haiku 4.5 | Implemented |
| Credentials | `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / Vertex ADC from the environment only; never committed or logged | Implemented |
| Prompt / system instructions | `agents/model_player.py`, to be extended for versus play | Implemented (single player); Planned (versus) |
| Output | One action from the legal list, parsed and validated | Implemented |

### A4. Limits, timeout, retry, spending

*[Superseded 2026-11-23, decisions #3, #5, #8, #24: cadence, call counts and the $5 budget are replaced; see A0. The 5 s timeout is unchanged.]*

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

*[Fallback now a labelled `WAIT`, decision #24; see A0.]*

| Failure | Handling | Label |
|---|---|---|
| Timeout or provider error | Scripted-baseline action, logged with `"source": "fallback"` | Implemented (midterm runner) |
| Unparseable reply | Same fallback; counted as a failed call | Implemented |
| Illegal action | Refused, counted, no state change | Implemented |
| Leaks: acting on hidden information | Cannot happen by design (the agent never receives it); leak tests check the observation | Planned tests |
| Too slow to be fun | Shorter cadence or scripted rival only (cut order) | Open (OQ-9) |

### A6. Scripted baseline

Same observation and same actions. Policy: take the nearest available uniform, then walk the shortest path to the other rival and strike when adjacent. Built on `agents/baseline.py` ([Implemented] for single player; [Planned] for versus). *[2026-11-24: the versus baseline is `agents/versus_baseline.py` on `main`; see A0.]*

### A7. Evaluation

- **Deterministic (CI, no network, no keys):** rule invariants for sword, disguise and traps; hidden-information tests for disguise identity and trap ownership; a fake-provider test for timeouts and the call limit; same seed gives an identical trace.
- **Live (only with `--live`, never in CI):** AI vs scripted and AI vs AI duels on fixed seeds; record win/draw/loss, invalid actions, fallbacks, latency, tokens and cost. *[Superseded for the PPO rival by decisions #3, #8, #9: no live call is needed; scenarios D1, B2, I3, F5, H6 in A0.]*
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
| Game server (online play; the AI seat runs here) | `server/` | Implemented on `main` (T13, T18). *[Deferred 2026-11-23 (#1), restored 2026-11-24 (#35 to #38)]* |
| Browser client (draws one seat's observation) | `web/` | Implemented on `main` (T14, T13). Also the hosted Pyodide + Phaser page (#12); no live URL |

---

## Part B — Production agents and role coverage

The student remains Executive Producer and Creative Director. Agents recommend; Saad decides. The instructor approves gates.

### B0. Production agents as configured on 2026-11-26 (first written 2026-11-24)

Supersedes B1 below (the G1 single implementation agent) where they differ. Details: [`orchestration/README.md`](orchestration/README.md); the mapping to the course's formal roles: [`orchestration/COURSE_ROLE_MAP.md`](orchestration/COURSE_ROLE_MAP.md); handoff format: [`orchestration/HANDOFF_PROTOCOL.md`](orchestration/HANDOFF_PROTOCOL.md); manifest: [`agent-config.json`](../../agent-config.json).

| Agent | Native definition | Model | Purpose | Formal course role? |
|---|---|---|---|---|
| Production Orchestrator (the main session) | `.claude/agents/orchestrator.md` | `claude-opus-5-5` | Writes briefs, delegates, runs Gate 3, keeps `STATUS.md` and `REVIEW_LOG.md` | **No.** Execution architecture only |
| `tech-lead` | `.claude/agents/tech-lead.md` | `claude-sonnet-5-5` | Implements one approved task on `task/<ID>` in its own worktree | Yes, the course `tech` role once `agent-team/roles/tech.md` exists and is tailored |
| `qa` | `.claude/agents/qa.md` | `claude-sonnet-5-5` | Gate 1: fact-check and test of the Tech Lead's commit | Yes, the course `qa` role, same condition |
| `evaluation-specialist` | `.claude/agents/evaluation-specialist.md` | `claude-sonnet-5-5` | Gate 2 for AI, boundary and evaluation changes | **No**, unless Saad adds it with a dated origin note |
| `requirements-auditor` | `.claude/agents/requirements-auditor.md` | `claude-sonnet-5-5` | Read-only audit of the requirements | **No** (temporary worker) |
| `telemetry-analyst` | `.claude/agents/telemetry-analyst.md` (on `main`) | `claude-sonnet-5-5` | Counts playtest telemetry logs and reports facts; Saad interprets. Writes its report only | **No** (#69): it counts only if Saad later writes an origin note with real, dated friction |
| `rules-reviewer` | `.claude/agents/rules-reviewer.md` | `claude-sonnet-5-5` | Independent read-only rule review | Part of QA's rule-change check, not its own role |

Work passes between agents as committed report files, not chat. A feature closes only after an independent gate (Gate 1 QA, Gate 2 when the knowledge boundary or the AI changes, Gate 3 the orchestrator). Saad merges, decides, approves spending and writes every Student decision. Workers do not push; the orchestrator pushes branches without per-push approval and opens issues and PRs for handoffs (#27, #28), and commits orchestration records to `main` (#29). New workers run on Sonnet (#16). The course `agent-team/` folder does not exist yet; creating it is part of the official-repository move (#6), not started. The worker models were verified from session transcripts on 2026-11-24 (`orchestration/REVIEW_LOG.md`).

### B1. Configured agents (G1 text, kept)

### B1. Configured agents

| Agent | Executable artifact | Purpose | Context | Tools / permissions | Outputs → recipient | Evaluation | Human approval boundary |
|---|---|---|---|---|---|---|---|
| **Implementation agent** [Implemented] | `CLAUDE.md` | Build and change the game | Whole project folder; original source read-only | Edit code, tests and docs; run tests; no secrets, no merge | Branch, passing tests, change summary → rules-reviewer, then Saad | Tests green; reviewer findings | Saad merges; never approves its own work |
| **`game-rules-audit` skill** [Implemented] | `.claude/skills/game-rules-audit/SKILL.md` | Audit the player interface, hidden-state leaks, legal actions, limits | Spec, rule map, interface/runner/agent code, tests | Read, run deterministic tests, write `docs/audits/` | Dated audit report → Saad | Findings checked against code | Saad accepts or rejects findings |
| **`rules-reviewer`** [Implemented] | `.claude/agents/rules-reviewer.md` | Independent read-only review | Change summary, diff, rule map, code, tests | Read, Grep, Glob only | Findings `[blocking / should fix / note]` → Saad | Fresh context that did not write the change | Cannot approve or merge |
| **AI rival** (in-game) | `agents/model_player.py` | Play a seat (Part A) | One player's observation only | Submit one action per call | Action → runner | Section A7 | Live runs only when Saad passes `--live` |

### B2. Role coverage map (reader Section 3.3)

*G1 text. The formal course coverage map (every role one line) is not written yet; it is Saad's call and part of the official-repository move (`orchestration/COURSE_ROLE_MAP.md`).*

| Development role | Covered by | Coverage at G1 |
|---|---|---|
| **Producer** | Saad, with the implementation agent drafting plans | Planned: [`PROJECT_PLAN.md`](PROJECT_PLAN.md); moves to Asana after G1 *[Superseded 2026-11-23, decision #10: the tracker stays in this repository for now]* |
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

G1 "needed by" column (kept here): CQ-1 rival-seat work; CQ-2 and CQ-4 first live tuning run; CQ-3 first playtest; CQ-5 before transfer to the course repo; CQ-6 first playtest; CQ-7 before G2; CQ-8 before hosting. The status column is as of 2026-11-26.

| ID | Question | Status on 2026-11-26 (G1 "needed by" dates dropped) |
|---|---|---|
| CQ-1 | Final macro-action vocabulary for versus play | **Closed 2026-11-23 (#23):** BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, SEARCH, plus RIG_TRAP. CLIMB goes up and down (#31). RIG_TRAP exists but is masked for the PPO rival (#43) |
| CQ-2 | History length N given to the AI rival | Reframed: the PPO encoder keeps fixed capped counters and its last macro (A0), not N actions. N applies only to the legacy LLM player. The history features await Saad's approval of the feature set |
| CQ-3 | Decision cadence (4 s assumed) | **Partly closed (#24):** runner decisions every 6 frames. Open: a new macro at most every 4 decisions (waiting on Saad) |
| CQ-4 | Re-measured latency and cost with versus prompts | Not needed for the PPO rival (no provider call). Open only for the legacy LLM player, within the under-$1 smoke cap (#8) |
| CQ-5 | Course CI workflow path for the final project | Open; the move to the official repository is due Sat 28 Nov (#6) |
| CQ-6 | Playtest log format (reader Section 5.9) | Open |
| CQ-7 | Whether to add a course `agent-config.json` manifest for the final project | **Closed 2026-11-24:** [`agent-config.json`](../../agent-config.json) committed in 2d40972 (course-1 schema). No numbered Saad decision records it; Saad has not been recorded confirming its contents |
| CQ-8 | Where the AI seat's API key lives once the server is hosted (host secret store, never the browser) | Not applicable: the PPO rival, on the server and in the static page, needs no key and no browser holds one. Open only if an LLM component returns |

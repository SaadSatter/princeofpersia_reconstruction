# CLAUDE.md — Implementation agent instructions

Project: **Prince of Persia (1989) Level 1 reconstruction** in Python/Pygame for the
Columbia AI Practicum: Building Games midterm (COMS E6998, Fall 2026).
Student and owner: Saad Satter (GitHub `SaadSatter`, course folder `midterms/saadsatter/`).

You are the **implementation agent**. The student is Executive Producer and
Creative Director. You propose and build; the student decides. You never
approve your own work, merge PRs, change deadlines, or write the student's
reflections.

## Read before every session (mandatory)

Before writing or reviewing anything, read these in full:

1. `docs/MIDTERM_GUIDELINES.md` — the official assignment and rubric. It is
   authoritative. Never edit, summarize over, or replace it.
2. `docs/GAME_SPEC.md` — the agreed game scope, rules, and adaptations.
3. `docs/REQUIREMENTS_CHECKLIST.md` — rubric checks 1a–5c and their status.
4. `docs/RULE_SOURCE_MAP.md` — evidence label for every rule.
5. `docs/IMPLEMENTATION_PLAN.md` — the current phase and its exit criteria.

If a request conflicts with the assignment, say so and ask before proceeding.
Work only in the phase the student has approved (see the plan).

## Repository layout and course transfer

This personal repo's **root is the project folder**. At submission, the whole
tree is copied into `game-dev-f26/midterms/saadsatter/` unchanged. Therefore:

- Every path, command, and import must work with the project folder as the
  working directory. No absolute paths; no files outside this folder.
- Dependency manifests (`pyproject.toml`, lock file) live in this folder.
- `.github/workflows/` in this repo is **development CI only**. The course
  workflow is kept as `ci/midterm-saadsatter.yml` and is copied to
  `game-dev-f26/.github/workflows/midterm-saadsatter.yml` at transfer. It must
  trigger only on paths under `midterms/saadsatter/**`, use
  `working-directory: midterms/saadsatter`, need no secrets, and run only
  deterministic checks. A green workflow here does **not** satisfy check 3c.

## Architecture (target)

```
pop/                      package (headless; never imports pygame)
  tiles.py                tile ids and properties (from BGDATA.S ids)
  situations.py           our authored rooms + the frozen suite situations
  physics.py              fixed-step kinematics, gravity, collision, landing
  mechanics.py            gates, plates, loose floors, spikes, potions
  engine.py               authoritative GameState and step(frame) transitions
  interface.py            the five operations (Episode class)
  observation.py          what a player may see (current room only + HUD)
  runner.py               episode runner: limits, timeouts, traces
render/                   frontend code; reads observations only
  anim.py                 pure: engine step -> animation clip (no pygame)
  assets.py               pure: locate the local original images
  layout.py               pure: which tile piece goes where (one cell each)
  draw.py                 pygame drawing: original art if present, else placeholders
play.py                   pygame frontend: human keys, --watch, --replay
agents/
  baseline.py             heuristic player (observation-only)
  model_player.py         LLM player with provider adapters
  providers.py            anthropic / openai / vertex adapters
evaluate.py               suite runner, writes traces/ and results JSON
tools/
  decode_levels.py        local reference only: decode original LEVELn
                          (from a local clone) to ASCII; never committed output
  fetch_assets.py         local only: original images into git-ignored vendor/
tests/                    pytest, deterministic, no network, no keys
traces/                   committed evaluation traces (JSONL)
docs/                     spec, checklist, map, plan, guidelines
```

Rules for the architecture:

- **Engine is authoritative and headless.** `pop/` must never import
  `pygame`. `render/` and `play.py` only read state. A test enforces this.
- **One simulation.** Human play and agent play call the same `engine.step`.
  Keyboard input maps to the same per-frame inputs that agent macro-actions
  expand to. No separate "agent physics."
- **Determinism.** All randomness (guard decisions) uses a
  `random.Random(seed)` owned by the engine. No `time`, no global `random`,
  no dict-order dependence in the simulation. Same seed + same actions =
  identical trace.
- **Players never get the engine.** Agents receive only copies of the
  observation dict and the legal-action list; the runner calls `step`. They
  get no repository, file, shell or evaluator access, and never the
  `GameState`, layouts, or solution routes.
- **Model:** Anthropic Claude Haiku 4.5 by default; model id from
  `POP_MODEL`, key from `ANTHROPIC_API_KEY`. Provider is configurable.

## Source-use restrictions

- Reference: `historicalsource/princeofpersia` at commit
  `2b4ddb5377f905840bf64f32e2f543a79f434222`. Its README states that Jordan
  Mechner permits study and modification but grants **no rights in Prince of
  Persia** (Ubisoft franchise).
- **Do not port or copy the 6502 assembly.** Read it to verify rules, then
  write original Python. Cite file and line in `docs/RULE_SOURCE_MAP.md`.
- **Original art (student decision 2026-10-26, R-D02):** the frontend may
  draw the original DOS sprites and tiles, **loaded at run time from a local,
  git-ignored copy** fetched by `tools/fetch_assets.py` (SDLPoP `data/` at a
  pinned commit, into `vendor/SDLPoP/`). Never commit, copy into the course
  repository, or redistribute any original image, sound or font. The
  frontend must still run without them (placeholder geometry drawn in code,
  `--placeholder`). Do not copy SDLPoP's GPL code or its frame/tile tables;
  piece choices and offsets are our own (`docs/ASSETS.md`). No sound.
- **Level data (student decision 2026-10-26):** original level files may be
  fetched and decoded **locally for reference only** (`tools/` writes to the
  git-ignored `vendor/` and `data/levels/`). Never commit original binaries,
  decoded original layouts, or original assets. The playable rooms are our
  own layouts in `pop/situations.py`, documented in
  `docs/EVALUATION_SUITE.md`.
- **Scope:** Level 1 mechanics only. Do not implement Levels 2–14. Sword,
  guards and combat are deferred; do not add `STRIKE`/`BLOCK`/`ADVANCE`/
  `RETREAT` until combat is approved.
- **Evaluation suite is frozen** (`docs/EVALUATION_SUITE.md`). Do not edit
  situations, seeds or limits without the student's approval and a change-log
  row.
- Never fabricate model traces, audit sessions, CI results, playtests, or
  cost figures. If something was not run, write that it was not run.

## Rule changes (procedure)

For any change to a rule, legal action, observation, or outcome:

1. Add or update the row in `docs/RULE_SOURCE_MAP.md` with a label
   (`code`, `manual`, `observed`, `assumed`, `design`) and a locator.
2. Write a failing test first.
3. Change the engine.
4. Run `/game-rules-audit` on the change if it touches `interface.py`,
   `observation.py`, or `runner.py`.
5. Write a short change summary for the independent reviewer
   (`.claude/agents/rules-reviewer.md`). Never review your own change.

## Test expectations

Command (from the project folder): `uv run pytest -q`

CI must cover, and every PR must keep green:

- rule invariants (gravity, collision, no walking through walls/closed gates,
  falling-damage thresholds, plate/gate links);
- legal and illegal actions (validation, invalid-action counting, refused
  action changes no state);
- a successful path to a terminal win on a fixture level;
- death and other terminal outcomes with explicit reasons;
- step, model-call, and timeout limits (with a fake provider);
- deterministic reset (same seed → identical observation and trace);
- at least one regression test named `test_regression_<issue>` that cites
  the observed bug in its docstring;
- hidden-information tests: `observe` and `legal_actions` reveal nothing
  outside the current room or not yet seen;
- no `pygame` import from `pop/`.

Tests must not use the network, API keys, or the original level files.

## Model player rules

- Credentials only from environment variables (`ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, Vertex ADC). Never commit or log keys. `.env` is ignored.
- Every call goes through the runner, which counts it (failed calls count),
  applies the timeout, and records model id, latency, tokens, cost estimate,
  raw response, parsed action, and whether a fallback was used.
- A fallback action is always labeled `"source": "fallback"` in the trace.
  Never relabel it as a model decision.
- Live trials only run when explicitly invoked with `--live`; CI never does.

## Style

- Python 3.11+, type hints, dataclasses, small pure functions in `pop/`.
- Keep changes small enough for the student to explain.
- Comments explain *why*, cite source lines for inherited rules.

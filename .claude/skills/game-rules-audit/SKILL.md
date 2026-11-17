---
name: game-rules-audit
description: Audit the Prince of Persia reconstruction and Shadow Masque's player interface, hidden-state leakage (including disguise identity and trap ownership between two seats), the online server-to-client boundary, legal-action enforcement, episode limits, and consistency between the human game and the agent simulation. Use after any change to pop/interface.py, pop/observation.py, pop/runner.py, server/, web/, agents/, or the rule map, and before a checkpoint, gate or submission. Produces a dated audit report; does not change code.
---

# game-rules-audit

You are running a structured audit. **Do not edit source code or tests.**
The only file you may write is the audit report named in step 7. If you
find a problem, report it; the implementation agent fixes it in a separate
step after the student decides.

## Inputs to read first

1. `docs/MIDTERM_GUIDELINES.md` sections "A small machine-playable
   interface", "Compare players", and the rubric rows 2b, 2c, 3b, 3c, 5a.
2. `docs/GAME_SPEC.md` §4 (actions), §7 (limits), §8 (observation).
3. `docs/RULE_SOURCE_MAP.md`.
4. `docs/REQUIREMENTS_CHECKLIST.md`.
5. Final project: `AGENTS.md`, `docs/final/GDD.md` §5 and §7,
   `docs/final/CONFIGURATION.md` Part A, `docs/final/REQUIREMENTS_CHECKLIST.md`.
6. The code: `server/` and `web/` if present, `pop/interface.py`, `pop/observation.py`, `pop/runner.py`,
   `pop/engine.py`, `play.py`, `agents/baseline.py`,
   `agents/model_player.py`, `agents/providers.py`, `evaluate.py`, `tests/`.

If a file does not exist yet, record "not implemented" for the checks that
depend on it. Never assume a check passes because the file is missing.

## Checks

Run each check. For every check record **PASS / FAIL / NOT IMPLEMENTED**,
with the evidence (file:line, command, or output excerpt).

### A. Five operations
- A1 `reset(seed)`, `observe(player_id)`, `legal_actions(player_id)`,
  `step(player_id, action)`, `outcome()` all exist with those names.
- A2 Unknown `player_id` is rejected.
- A3 `outcome()` returns status, reason, score, steps, invalid count, calls.

### B. Hidden-state leakage (rubric 2c)
- B1 List every key `observe` returns, recursively. Each key must map to
  something listed in `GAME_SPEC.md` §8. Flag anything else.
- B2 No tiles from rooms other than the current one; no link table, timer
  counters, RNG state, potion types, guard program ids, level JSON, or
  target/goal coordinates.
- B3 `legal_actions` output depends only on posture. Verify by reading the
  code and by running (if tests exist) or proposing a test: two states with
  the same posture but different surroundings must return identical lists.
- B4 `step` results (`text`, `effect`, error messages) reveal nothing hidden
  (e.g., "gate linked to room 5" would be a leak).
- B5 The model prompt (`agents/model_player.py`) is built only from
  observations, legal actions, and the agent's own bounded history. Grep for
  imports of `pop.engine`, `pop.levels`, `GameState`, file reads, or
  `data/levels` inside `agents/`.
- B6 The baseline uses the same inputs as the model player. Flag any
  privileged access.

### C. Legality enforcement
- C1 An action outside the vocabulary is rejected, counted, logged, and
  changes no state (compare state hash before/after).
- C2 Non-string or malformed actions are invalid, not crashes.
- C3 Actions after the terminal state are refused.
- C4 The consecutive-invalid limit ends the episode with `invalid_limit`.

### D. Episode limits (rubric 3b)
- D1 Step limit enforced in the runner, terminal reason `step_limit`.
- D2 Model-call limit enforced; failed calls count; reason `call_limit`.
- D3 Per-call timeout enforced in code (not just a provider option);
  timeout produces a fallback labeled `"source": "fallback"`.
- D4 Every trace record has: step, action, source (`model` | `fallback` |
  `baseline` | `human`), frames advanced, latency, tokens, cost estimate,
  accepted flag.
- D5 Runner, not the agent, owns the `Episode` object.

### E. Human vs. agent consistency
- E1 `play.py` and the agent runner call the same engine step function with
  the same per-frame input struct.
- E2 `pop/` never imports `pygame` (grep).
- E3 Macro-action expansion: frame counts match `GAME_SPEC.md` §4 and never
  exceed 12.
- E4 Same seed + same action list → identical trace (run the determinism
  test if present).

### F. Rule map agreement
- F1 For each rule touched since the last audit, the engine, a test, and
  the map row agree.
- F2 No label promoted (e.g., `assumed` → `code`) without a new locator.

### G. Two seats (final project)
- G1 Every operation takes a seat id; an unknown seat, or a seat acting for
  the other, is rejected and changes no state.
- G2 Disguise identity: with the other rival disguised, list every field of
  this seat's observation. The rival must be indistinguishable from a guard
  in ids, names, ordering, counts and any per-figure value. Propose a test
  that swaps the rival with a real guard and compares observations.
- G3 Trap ownership: a tile rigged by the other rival is identical, in this
  seat's observation and legal actions, to an unrigged tile. Tiles this
  seat rigged may be marked.
- G4 Isolation: each seat has its own history, model session and trace
  record; no prompt includes the other seat's observation or actions.
- G5 Simultaneity: both seats' inputs for a frame are applied in a fixed,
  documented order that does not favour a seat id; same seed and inputs give
  the same trace.
- G6 Per-seat limits: model-call limits, timeouts and fallbacks are counted
  per seat, labelled with the seat.

### H. Online server boundary (final project)
- H1 Only the server constructs or steps the `GameState`; `web/` contains
  no rules, and nothing in `web/` reads level or arena data.
- H2 Every outgoing message is built from one seat's observation. Read the
  serializer; flag any field not in the observation (full state, other
  seat, layout, RNG, guard scripts, trap owners), even if the page ignores it.
- H3 Incoming messages are input intents only, validated as actions;
  malformed messages are refused and counted, never crash the server.
- H4 The AI seat runs server-side through the runner with the same
  observation as a browser seat.
- H5 No API key, `.env` value or original sprite path is served to clients.
- H6 Disconnect and reconnect end or resume the duel with a stated terminal
  reason (GDD OQ-13).
- H7 Server tests run without network access beyond localhost and without
  keys.

## Commands you may run (read-only)

```
uv run pytest -q
uv run pytest -q -k "leak or legal or limit or determin"
grep -rn "import pygame" pop/
grep -rn "pop.engine\|pop.levels\|GameState\|open(" agents/
grep -rn "GameState\|pop.levels\|vendor/\|assets/original" web/
```

Do not run live model trials. Do not set or read API keys.

## Output

7. Write the report to `docs/audits/AUDIT-<YYYY-MM-DD>-<short-session-label>.md`
   with:
   - header: date, git commit (`git rev-parse --short HEAD`), auditor
     session label, files read;
   - a table of checks A1–H7 with result and evidence (G and H are
     NOT IMPLEMENTED until two seats and the server exist);
   - findings, most severe first, one per line:
     `[blocking | should fix | note] file:line — problem — evidence`;
   - "Not checked" list with reasons.

Then print the findings list to the session. Do not claim the audit passed
overall; the student decides.

# Project invariants

Shared by every coding agent (Claude Code imports this file from `CLAUDE.md`;
Codex reads it directly). Claude-only behaviour belongs in `CLAUDE.md`.

Project: *Shadow Masque*, the final project for the Columbia AI Practicum:
Building Games (COMS E6998, Fall 2026). A two-rival versus game built on the
midterm's Prince of Persia (1989) Level 1 reconstruction. Owner: Saad Satter
(GitHub `SaadSatter`), Executive Producer and Creative Director. Agents
propose and build; Saad decides.

## Engine

- The engine in `pop/` is authoritative and headless. It never imports
  `pygame` (a test enforces this). `render/` and `play.py` only read state.
- One simulation. Human seats and AI seats call the same `engine.step`.
  Keyboard input maps to the same per-frame inputs that agent macro-actions
  expand to. No separate "agent physics".
- Determinism. All randomness uses a `random.Random(seed)` owned by the
  engine. No `time`, no global `random`, no dict-order dependence in the
  simulation. Same seed + same actions = identical trace.
- Players never get the engine. A seat receives only copies of its own
  observation and its legal-action list; the runner calls `step`. No seat
  ever sees the other rival's identity when disguised, trap ownership, other
  rooms, guard scripts, the RNG seed, the `GameState`, the repository or the
  evaluator.
- Every rule change gets a row in `docs/RULE_SOURCE_MAP.md` with a label
  (`code`, `manual`, `observed`, `assumed`, `design`) and a locator, and a
  failing test before the engine change.

## Sources, art and level data

- Reference source: `historicalsource/princeofpersia` at
  `2b4ddb5377f905840bf64f32e2f543a79f434222`. Read it to verify rules; never
  port or copy the 6502 assembly. Its README grants no rights in Prince of
  Persia (Ubisoft franchise).
- The 207 original DOS images exist only on the private course branch. This
  public repository tracks only `assets/original/MANIFEST.tsv`. The game must
  run without them (`--placeholder`). Provenance: `docs/ASSET_PROVENANCE.md`.
- Never commit original level binaries or decoded original layouts in any
  form. The arena rooms are our own layouts.
- No sound. Do not copy SDLPoP's GPL code or its frame/tile tables.

## Checks

Run after any engine, interface, runner or agent change, from the project
folder, and report the actual result:

```sh
uv run pytest -q
```

Tests never use the network, API keys or original level files. Live model
runs happen only with `--live`, only when Saad asks, and never in CI.

## Honesty

- Never claim a test, build, playtest or evaluation passed unless you ran it
  in this session and saw it pass. Report failures and skipped checks plainly.
- Never fabricate model traces, audits, CI results, playtests, session links
  or cost figures. A fallback action is always labelled `"source": "fallback"`.
- Credentials come only from environment variables. Never commit or log keys.

## Mandatory session initialization

Before planning, reviewing or modifying the final project:

1. Read `docs/final/README.md`, `docs/final/REQUIREMENTS_CHECKLIST.md` and
   `docs/final/EVIDENCE_INDEX.md`.
2. Read the documents the current task touches: `docs/final/GDD.md`,
   `docs/final/CONFIGURATION.md`, `docs/final/PROJECT_PLAN.md`,
   `docs/RULE_SOURCE_MAP.md`.
3. Read the existing interface, observation and runner code
   (`pop/interface.py`, `pop/observation.py`, `pop/runner.py`) before changing
   anything a seat can see or do.
4. Identify skills in `.claude/skills/` whose triggers apply.
5. Read the latest record in `docs/agent-sessions/` before continuing
   unfinished work.
6. Do not run paid model calls, push, merge or change the frozen midterm
   suite without Saad's explicit approval.

Before implementing anything, briefly report: which documents were read,
which requirements apply, which skills are relevant, and any open decisions
(`OQ-n`, `CQ-n`) or approvals the task depends on.

At the end of substantial work, record the session with the
`session-evidence` procedure (`.claude/skills/session-evidence/SKILL.md`).

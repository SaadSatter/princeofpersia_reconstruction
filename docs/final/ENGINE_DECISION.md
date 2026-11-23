# Engine decision: Python/Pygame or Godot

**Status:** recommendation by the implementation agent, 2026-11-16. Saad decides.
**Recommendation:** stay on the current Python engine (`pop/`) with the Pygame
frontend. Do not port to Godot for the final project.

## What exists now (measured 2026-11-16)

| Part | Size | Notes |
| --- | --- | --- |
| Headless engine `pop/` | ~1,670 lines | Deterministic, seeded, no `pygame` |
| Frontend `render/` + `play.py` | ~1,260 lines | Original art or placeholders |
| Agents + `evaluate.py` | ~940 lines | Model player, 3 providers, scripted baseline |
| Tests | ~2,570 lines; `uv run pytest -q`: 281 passed, 1 skipped (2026-11-16) | Leak, determinism, limits, regression, CI-workflow tests |

Godot is not installed on this machine.

## Comparison for *Shadow Masque*

| Need (GDD / Configuration) | Python + Pygame (current) | Godot 4 |
| --- | --- | --- |
| Movement, gates, plates, loose floors, landing damage | Built and tested | Rewrite in GDScript; re-derive every rule-map row |
| Determinism, same seed → same trace | Built; tests enforce it | Possible with a custom fixed-step loop, but Godot's physics and node-processing order are not designed for replayable traces; must be rebuilt and re-proven |
| Hidden-information boundary (disguise identity, trap ownership) | Extend `observation.py`; pytest leak tests | New observation layer; tests via GUT or a custom harness |
| AI rival calling Claude with timeout and fallback | Runner and adapters exist | `HTTPRequest` from GDScript, or a Python sidecar over a socket: two languages, two processes |
| CI with no secrets, deterministic | GitHub Actions + `uv run pytest` | Needs a headless Godot binary in CI and a GDScript test framework |
| Online play, one screen per rival (decided 2026-11-16) | Python WebSocket server around `pop/` + a thin browser client that only draws observations; new code on both sides | High-level multiplayer API and web export; the authoritative server would be a headless Godot build, and the AI seat's Claude calls still need building |
| Animation, tile editing, polish | Hand-written tables in `render/` | Editor, `AnimationPlayer`, `TileMap`: clearly better |
| Web or console export | Not available | Available |

## Why stay

1. **Schedule.** G2+G3 is Mon 30 Nov, two weeks away, and the checkpoint is
   Mon 23 Nov. A port would spend most of that time rebuilding what works,
   before any new mechanic (sword, disguise, traps) exists. The Timeline and
   Genre/Mechanics risks in `PROJECT_PLAN.md` are already High/Medium.
2. **The game's hard parts are rules and information, not rendering.** The
   new risks are disguise leaks, trap ownership, two-seat isolation and AI
   latency. These are exactly what the current headless engine and its tests
   are built to check.
3. **Evidence continuity.** The GDD, Configuration Document and rule map cite
   `pop/`, the runner and the existing tests as **[Implemented]**. A port turns
   them back into **[Planned]**.
4. **AI rival.** The runner already counts calls, enforces timeouts and labels
   fallbacks. In Godot this would be rebuilt or bridged to Python.

## What Godot would buy, and when to reconsider

Godot's real gains are an animation and tile editor, a built-in multiplayer
API, and a web build. Reconsider only if, at the scope
lock (Fri 27 Nov), the playtest says presentation, not rules, is what fails.
Even then, the cheaper path is to improve `render/` in Pygame.

A hybrid (Python engine authoritative, Godot as a renderer over a socket) is
not recommended: it keeps both toolchains and adds a network boundary to a
real-time sword fight.

## Update 2026-11-16: online play

Saad changed the play context from local split screen to online play, one
screen per rival. This makes Godot's web export and multiplayer API more
relevant, so the comparison was re-checked. The recommendation stands:

- **The server is the part that matters, and it is the Python engine.** The
  disguise only works if a client never receives what its player may not see.
  That needs one authoritative server sending per-seat observations, which is
  what `pop/interface.py` and `pop/observation.py` already produce. In Godot
  the server would be a headless Godot process with the rules rewritten.
- **The client can be thin.** A browser page that receives one seat's
  observation and draws it (HTML canvas, plain JavaScript; GDD OQ-11) holds no
  rules, so it is small to write in any technology. Godot would make the
  client nicer, not the game correct.
- **The AI seat stays where it is.** It runs on the server, behind the same
  runner, with the same per-seat observation as a browser.
- **The Pygame frontend is kept** for development, `--replay` and watching
  AI vs AI. It is not the online client.

Alternative considered: compiling the Pygame frontend to the browser
(pygbag/WebAssembly). It would reuse `render/`, but it is built to run the
whole game in the page; making it a network client that holds no game state
is more work than a small canvas page, and harder to test in CI.

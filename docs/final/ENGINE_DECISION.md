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
| Split screen, two keyboard layouts | Two room surfaces side by side; small amount of new code | Built in (`SubViewport`, input map) |
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

Godot's real gains are split screen out of the box, an animation and tile
editor, and a web build for showcase play. Reconsider only if, at the scope
lock (Fri 27 Nov), the playtest says presentation, not rules, is what fails.
Even then, the cheaper path is to improve `render/` in Pygame.

A hybrid (Python engine authoritative, Godot as a renderer over a socket) is
not recommended: it keeps both toolchains and adds a network boundary to a
real-time sword fight.

"""Screenshots for the deck from the real renderer (render/), generated art, scale 3.

    uv run --extra play python presentation/shots.py

Writes presentation/shots/:
  menu.jpg            the game's own start menu (render/menu.py), the title screen
  rehearsal-NNN.jpg   `--mode ai --seed 0` (the demo configuration): seat A is driven by a
                      scripted rehearsal bot (it walks to the Barracks, draws, strikes the
                      guard, takes the uniform), seat B is the shipped PPO policy loaded
                      by hash, exactly as `play.py ARENA --mode ai` does. These are rehearsal
                      frames, labelled as such on the slides; they are not the external playtest.
The external-playtest frames come from presentation/render_replay.py --png-dir.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
OUT = ROOT / "presentation/shots"
SCALE = 3


def main() -> int:
    import pygame
    from agents import modes
    from pop.versus import arena_episode
    from render import draw, menu, versus_view

    OUT.mkdir(parents=True, exist_ok=True)
    pygame.init()
    window = pygame.display.set_mode((draw.SCREEN_W * SCALE, draw.SCREEN_H * SCALE))
    surf = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
    menu.draw_menu(surf, 0, [(m.id, m.label) for m in modes.MODES])
    pygame.image.save(pygame.transform.scale(surf, window.get_size()), str(OUT / "menu.jpg"))

    renderer = draw.Renderer(original=False, art="generated")
    counts = {k: v["n"] for k, v in renderer.dungeon.meta["rival"].items()}
    gcounts = {k: v["n"] for k, v in renderer.dungeon.meta["guard"].items()}
    cache: dict = {}

    def shot(ep, tick, name):
        obs = ep.observe("A")
        panel = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
        renderer.draw_room(panel, obs, tick)
        for j, fig in enumerate(obs["figures"]):
            if fig["kind"] == "rival":
                spr = versus_view.sprite(fig, counts)
                if spr:
                    renderer.dungeon.blit_actor(panel, "rival", spr.strip, spr.index, spr.x, spr.y, spr.facing, "crimson")
                else:
                    renderer.dungeon.draw_kid(panel, versus_view.pose(fig, obs["room"], cache, ("f", j)), "crimson")
            else:
                spr = versus_view.guard_sprite(fig, gcounts)
                if spr:
                    renderer.dungeon.blit_actor(panel, "guard", spr.strip, spr.index, spr.x, spr.y, spr.facing)
                else:
                    renderer.dungeon.draw_kid(panel, versus_view.pose(fig, obs["room"], cache, ("g", j)), who="guard")
        me = obs["me"]
        if me["disguised"]:
            spr = versus_view.guard_sprite(me, gcounts)
            if spr:
                renderer.dungeon.blit_actor(panel, "guard", spr.strip, spr.index, spr.x, spr.y, spr.facing)
        else:
            spr = versus_view.sprite(me, counts)
            if spr:
                renderer.dungeon.blit_actor(panel, "rival", spr.strip, spr.index, spr.x, spr.y, spr.facing, "indigo")
            else:
                renderer.dungeon.draw_kid(panel, versus_view.pose(me, obs["room"], cache, "me"), "indigo")
        renderer.draw_hud(panel, obs)
        pygame.image.save(pygame.transform.scale(panel, window.get_size()), str(OUT / name))

    ep = arena_episode(0)
    rival = modes.make_seat_rival("ai")
    rival.reset(0)
    duel = ep._duel
    guard = duel.guards["barracks"]
    me = duel.rivals["A"]
    wanted = {1: "rehearsal-001.jpg"}
    taken = []
    for t in range(1, 420):
        leg = ep.legal_actions("A")
        if t <= 24:
            act = "RIGHT"
        elif guard.downed and not me.disguised:
            act = "TAKE" if "TAKE" in leg and abs(guard.col - me.kid.cell[2]) <= 1 else (
                "RIGHT" if guard.col > me.kid.cell[2] else "LEFT")
        elif me.disguised:
            act = None
        elif me.sword != "drawn":
            act = "DRAW" if "DRAW" in leg else None
        else:
            d = guard.col - me.kid.cell[2]
            act = "LUNGE" if abs(d) <= 2 and me.kid.cell[1] == guard.row else ("RIGHT" if d > 0 else "LEFT")
        if act and act in leg:
            ep.step("A", act)
        else:
            ep.release("A")
        modes.step_ai_seat(ep, rival)
        ep.tick()
        key = None
        if t == 40:
            key = "rehearsal-guard-room.jpg"
        elif guard.downed and "downed" not in taken:
            taken.append("downed")
            key = "rehearsal-guard-down.jpg"
        elif me.disguised and "disg" not in taken:
            taken.append("disg")
            key = "rehearsal-disguised.jpg"
        if key:
            shot(ep, t, key)
            print(t, key, ep.observe("A")["room"], me.kid.cell)
        if me.disguised and t > 200:
            break
    print("fallbacks:", len(rival.fallback_log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

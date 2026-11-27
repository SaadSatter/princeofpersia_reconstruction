"""Replay the external Human vs AI duel (room XGJT, duel 1) and render seat A's view.

Reads the server input trace (`duel-XGJT-001-seed0.json`), replays it through the real
engine (`pop.versus.arena_episode`, the same call `server/trace.py replay` makes), checks the
final outcome and state hash against the recorded ones, then draws each tick with the real
renderer (`render/draw.py`, `render/versus_view.py`, generated art) the way `play.py` does
for the human seat. Nothing is simulated that is not in the trace: every input, human and AI,
comes from the trace. Presentation tooling only; no rule or renderer code is changed.

Usage (from the repository root):

    uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py \
        --start 205 --end 465 --out presentation/out/xgjt-001-segment.mp4

    --png-dir DIR   also write one JPG (a tracked .png breaks tests/test_frontend.py) per rendered tick (for inspection)
    --verify-only   replay and check the hash, render nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

TRACE = ROOT / "docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json"
LABEL = "External playtest — reconstructed from telemetry"
COLOURS = {"A": "indigo", "B": "crimson"}
TPS = 12                                   # engine ticks per second (R-D26)
# Event captions: (first tick, last tick, text). Each is read off the replayed engine state and
# the recorded inputs/telemetry (tick numbers are the trace's), none is interpretation.
CAPTIONS = [
    (246, 275, "Tick 246: you enter the Pit Hall (telemetry room change)"),
    (325, 356, "Tick 327: the scripted guard goes down (engine state); you sent no input"),
    (409, 416, "Tick 409: rival B sweeps, you are knocked down for 10 frames"),
    (417, 432, "Tick 417: rival B's lunge hits, hearts 3 to 2 (telemetry)"),
    (433, 440, "Tick 433: rival B sweeps again"),
    (441, 455, "Tick 441: rival B's lunge hits, hearts 2 to 1 (telemetry)"),
    (456, 462, "Tick 456: rival B's hearts 3 to 2 (replay state; you sent LUNGE at 454, 456)"),
    (463, 465, "Tick 463: your THROW input. Tick 465: sword drop, hearts 0, rival B wins"),
]


def load_trace(path: Path = TRACE) -> dict:
    return json.loads(path.read_text())


def verify(trace: dict) -> tuple[bool, str]:
    """Replay with the repository's own function and compare to the recorded hash and outcome."""
    from server.trace import replay
    outcome, h = replay(trace)
    ok = h == trace["state_hash"] and outcome == trace["outcome"]
    return ok, h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=216, help="first tick to show (1-based)")
    ap.add_argument("--end", type=int, default=465, help="last tick to show")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "presentation/out/xgjt-001-segment.mp4"))
    ap.add_argument("--png-dir", help="write one JPG per tick here")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--hold-end", type=float, default=2.0, help="seconds to hold the last frame")
    args = ap.parse_args()

    trace = load_trace()
    ok, h = verify(trace)
    print(f"replay state hash {h}\nrecorded hash      {trace['state_hash']}\nmatch: {ok}")
    if not ok:
        print("REPLAY DOES NOT MATCH: not rendering", file=sys.stderr)
        return 2
    if args.verify_only:
        return 0

    import pygame
    import numpy as np
    import imageio_ffmpeg
    from pop.versus import arena_episode
    from render import draw, versus_view

    pygame.init()
    scale = args.scale
    pw, ph = draw.SCREEN_W * scale, draw.SCREEN_H * scale
    bar = 24 * scale                                   # caption strip under the panel
    window = pygame.display.set_mode((pw, ph + bar))
    renderer = draw.Renderer(original=False, art="generated")
    font = pygame.font.Font(None, 8 * scale)
    big = pygame.font.Font(None, 9 * scale)
    counts = {k: v["n"] for k, v in renderer.dungeon.meta["rival"].items()}
    guard_counts = {k: v["n"] for k, v in renderer.dungeon.meta["guard"].items()}
    cache: dict = {}

    def draw_actor(s, view, room, colour, key):
        spr = versus_view.sprite(view, counts)
        if spr is not None:
            renderer.dungeon.blit_actor(s, "rival", spr.strip, spr.index, spr.x, spr.y, spr.facing, colour)
            return
        renderer.dungeon.draw_kid(s, versus_view.pose(view, room, cache, key), colour)

    def draw_guard(s, view, room, key):
        spr = versus_view.guard_sprite(view, guard_counts)
        if spr is None:
            renderer.dungeon.draw_kid(s, versus_view.pose(view, room, cache, key), who="guard")
            return
        renderer.dungeon.blit_actor(s, "guard", spr.strip, spr.index, spr.x, spr.y, spr.facing)

    def draw_swords(s, swords):
        from render.anim import stand_point
        for sw in swords:
            x, y = stand_point(sw["row"], sw["col"])
            y = y - 18 if sw["flying"] else y - 1
            pygame.draw.line(s, (220, 231, 236), (x - 7, y), (x + 6, y))
            pygame.draw.line(s, (69, 78, 106), (x - 8, y - 1), (x - 8, y + 1))

    ep = arena_episode(trace["seed"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(out), (pw, ph + bar), fps=24, codec="libx264",
                                         pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         macro_block_size=2, quality=8)
    writer.send(None)
    if args.png_dir:
        Path(args.png_dir).mkdir(parents=True, exist_ok=True)
    last = None
    for tick, (inputs, released) in enumerate(zip(trace["ticks"], trace["releases"]), 1):
        for seat, act in inputs:
            ep.step(seat, act)
        for seat in released:
            ep.release(seat)
        ep.tick()
        if tick < args.start or tick > args.end:
            continue
        obs = ep.observe("A")
        panel = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
        renderer.draw_room(panel, obs, tick)
        draw_swords(panel, obs["swords"])
        for j, fig in enumerate(obs["figures"]):
            if fig["kind"] == "rival":
                draw_actor(panel, fig, obs["room"], COLOURS["B"], ("fig", j))
            else:
                draw_guard(panel, fig, obs["room"], ("guard", j))
        if obs["me"]["disguised"]:
            draw_guard(panel, obs["me"], obs["room"], "me")
        else:
            draw_actor(panel, obs["me"], obs["room"], COLOURS["A"], "me")
        renderer.draw_hud(panel, obs)
        window.fill((12, 12, 16))
        window.blit(pygame.transform.scale(panel, (pw, ph)), (0, 0))
        # Label, always on (small, top left, on a dark plate).
        lab = font.render(LABEL, True, (235, 225, 190))
        plate = pygame.Surface((lab.get_width() + 8 * scale // 2, lab.get_height() + 4))
        plate.set_alpha(190)
        plate.fill((10, 10, 14))
        window.blit(plate, (2 * scale, 2 * scale))
        window.blit(lab, (4 * scale, 2 * scale + 2))
        hp = obs["me"]["hp"]
        secs = tick / TPS
        cap = (f"you (seat A, indigo) vs trained PPO rival (seat B, crimson)    "
               f"duel time {secs:5.1f} s    your hearts {hp}")
        window.blit(big.render(cap, True, (200, 200, 205)), (4 * scale, ph + 3 * scale))
        for a, b, text in CAPTIONS:
            if a <= tick <= b:
                window.blit(big.render(text, True, (232, 196, 96)), (4 * scale, ph + 13 * scale))
        frame = np.transpose(pygame.surfarray.array3d(window), (1, 0, 2)).copy()
        last = frame
        for _ in range(2):                              # 12 ticks/s shown as 24 fps
            writer.send(frame)
        if args.png_dir:
            pygame.image.save(window, str(Path(args.png_dir) / f"t{tick:03d}.jpg"))
    for _ in range(int(args.hold_end * 24)):
        writer.send(last)
    writer.close()
    final = ep.outcome()
    print(f"wrote {out} (ticks {args.start}-{args.end}, {(args.end - args.start + 1) / TPS:.1f} s of play); "
          f"final outcome {final['reason']} at frame {final['frames']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

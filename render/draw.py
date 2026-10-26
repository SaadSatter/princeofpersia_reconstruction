"""Pygame drawing. Reads observation dicts and poses only (never the engine).

Original mode composes each tile from the DOS dungeon pieces the way the
original screen looks: a tile's own piece, the right-hand piece of the tile
to its left (floors and pillars reach into the next cell), and a 3-pixel
front edge. Piece choices and offsets are ours (docs/ASSETS.md).
Placeholder mode draws simple shapes and needs no files.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from pop import tiles as T

from . import anim, assets, layout
from .anim import COL_W, ROOM_H, ROOM_W, ROW_H, Pose

HUD_H = 8
SCREEN_W, SCREEN_H = ROOM_W, ROOM_H + HUD_H      # 320 x 200, as the original

# Placeholder palette
BG = (0, 0, 0)
STONE = (70, 88, 112)
STONE_LIGHT = (122, 142, 168)
STONE_DARK = (36, 46, 64)
WHITE = (236, 236, 236)
KID_BODY = (240, 236, 210)
KID_HAIR = (190, 140, 20)
RED = (220, 30, 30)
GOLD = (230, 180, 40)
TEAL = (40, 160, 160)



row_top = layout.row_top


class Renderer:
    def __init__(self, original: bool, root: Path | None = None):
        self.original = bool(original and (root or assets.asset_dir()))
        self.root = root or assets.asset_dir()
        self._img: dict[tuple[str, int, bool], pygame.Surface] = {}

    # --- images ------------------------------------------------------------
    def img(self, folder: str, n: int, flip: bool = False) -> pygame.Surface:
        key = (folder, n, flip)
        if key not in self._img:
            if flip:
                self._img[key] = pygame.transform.flip(self.img(folder, n), True, False)
            else:
                surf = pygame.image.load(str(self.root / folder / f"res{n}.png"))
                self._img[key] = surf.convert_alpha() if pygame.display.get_surface() else surf
        return self._img[key]

    def blit_bottom(self, s: pygame.Surface, folder: str, n: int, x: float, bottom: float) -> None:
        im = self.img(folder, n)
        s.blit(im, (round(x), round(bottom) - im.get_height()))

    # --- room --------------------------------------------------------------
    def draw_room(self, s: pygame.Surface, obs: dict, tick: int,
                  gate_pct: dict[tuple[int, int], float] | None = None) -> None:
        s.fill(BG, (0, 0, ROOM_W, ROOM_H))
        st = obs["state"]
        gates = {(g["row"], g["col"]): g["open_pct"] for g in st["gates"]}
        if gate_pct:
            gates.update(gate_pct)
        exits = {(e["row"], e["col"]): e["open_pct"] for e in st["exits"]}
        sprung = {tuple(x) for x in st["spikes_sprung"]}
        shaking = {tuple(x) for x in st["loose_shaking"]}
        pressed = {tuple(x) for x in st["plates_pressed"]}
        ctx = dict(room=obs["room"], tick=tick, gates=gates, exits=exits,
                   sprung=sprung, shaking=shaking, pressed=pressed)
        if self.original:
            self._room_original(s, obs["tiles"], ctx)
        else:
            self._room_placeholder(s, obs["tiles"], ctx)

    def _room_original(self, s, rows, ctx) -> None:
        for pc in layout.room_pieces(rows, ctx):
            if pc.name == "gate_bars":
                self._gate_bars(s, pc.x, pc.bottom, pc.value)
            elif pc.name == "exit":
                r, c = pc.cell
                self._exit_original(s, pc.x, row_top(r), pc.bottom, pc.value)
            else:
                self.blit_bottom(s, pc.folder, pc.number, pc.x, pc.bottom)

    def _gate_bars(self, s, x, top, open_pct: float) -> None:
        D = assets.DUNGEON
        full = 50                                    # closed: bars reach the floor
        length = max(4, round(full * (1 - open_pct / 100)))
        bars = self.img("VDUNGEON", D["gate_bars"])
        bot = self.img("VDUNGEON", D["gate_bottom"])
        clip = s.get_clip()
        s.set_clip(pygame.Rect(x, top, COL_W, length + 1))
        y = top + length - bot.get_height()
        s.blit(bot, (x, y))
        while y > top - bars.get_height():
            y -= bars.get_height()
            s.blit(bars, (x, y))
        s.set_clip(clip)

    def _exit_original(self, s, x, top, bottom, pct) -> None:
        D = assets.DUNGEON
        V = "VDUNGEON"
        self.blit_bottom(s, V, D["exit_left"], x, bottom)
        self.blit_bottom(s, V, D["exit_right"], x + COL_W, bottom + 2)
        self.blit_bottom(s, V, D["base"], x, bottom + 3)
        self.blit_bottom(s, V, D["base"], x + COL_W, bottom + 3)
        # Opening: from the left frame to the right frame, top to the floor.
        opening = pygame.Rect(x + 13, top + 4, 39, bottom - 9 - (top + 4))
        if pct > 0:
            clip = s.get_clip()
            s.set_clip(opening)
            self.blit_bottom(s, V, D["exit_stairs"], opening.x - 2, opening.bottom + 1)
            s.set_clip(clip)
        # The door panel slides up as it opens.
        panel_h = round(opening.h * (1 - pct / 100))
        if panel_h > 0:
            clip = s.get_clip()
            s.set_clip(pygame.Rect(opening.x, opening.y, opening.w, panel_h))
            strip = self.img(V, D["exit_panel"])
            y = opening.y + panel_h - strip.get_height()
            while y > opening.y - strip.get_height():
                s.blit(strip, (opening.x, y))
                s.blit(strip, (opening.x + 16, y))
                y -= strip.get_height()
            s.set_clip(clip)
        self.blit_bottom(s, V, D["exit_top_left"], x, top + 6)
        self.blit_bottom(s, V, D["exit_top_right"], x + COL_W, top + 6)

    def _room_placeholder(self, s, rows, ctx) -> None:
        for r, line in enumerate(rows):
            top = row_top(r)
            floor_y = top + 50
            for c, t in enumerate(line):
                x = c * COL_W
                if t == T.WALL:
                    pygame.draw.rect(s, STONE, (x, top, COL_W, ROW_H))
                    pygame.draw.rect(s, STONE_DARK, (x, top, COL_W, ROW_H), 1)
                    continue
                if t == T.SPACE:
                    continue
                slab = STONE_LIGHT
                if t == T.LOOSE:
                    slab = (150, 120, 90)
                    if (r, c) in ctx["shaking"] and ctx["tick"] % 2:
                        floor_y += 1
                pygame.draw.rect(s, slab, (x, floor_y, COL_W, 10))
                pygame.draw.rect(s, STONE_DARK, (x, floor_y + 10, COL_W, 3))
                if t == T.LOOSE:
                    pygame.draw.line(s, STONE_DARK, (x + 8, floor_y), (x + 14, floor_y + 9))
                    pygame.draw.line(s, STONE_DARK, (x + 22, floor_y), (x + 18, floor_y + 9))
                    floor_y = top + 50
                elif t == T.SPIKES:
                    h = 14 if (r, c) in ctx["sprung"] else 3
                    for k in range(4):
                        bx = x + 3 + k * 7
                        pygame.draw.polygon(s, WHITE, [(bx, floor_y), (bx + 5, floor_y),
                                                       (bx + 2, floor_y - h)])
                elif t == T.GATE:
                    pct = ctx["gates"].get((r, c), 0)
                    length = max(4, round(48 * (1 - pct / 100)))
                    for k in range(5):
                        pygame.draw.line(s, (180, 180, 190), (x + 4 + k * 5, top),
                                         (x + 4 + k * 5, top + length), 2)
                    pygame.draw.line(s, (180, 180, 190), (x + 2, top + length),
                                     (x + 26, top + length), 2)
                    pygame.draw.rect(s, STONE_DARK, (x + 27, top, 4, ROW_H - 13))
                elif t in T.PLATES:
                    up = t == T.RAISE_PLATE and (r, c) not in ctx["pressed"]
                    pygame.draw.rect(s, GOLD, (x + 4, floor_y - (3 if up else 0), 24, 3))
                elif t in T.EXITS:
                    if t == T.EXIT_LEFT:
                        pct = ctx["exits"].get((r, c), ctx["exits"].get((r, c + 1), 0))
                        door = pygame.Rect(x + 12, top + 6, 40, floor_y - top - 6)
                        pygame.draw.rect(s, (10, 10, 30), door)
                        for k in range(4):
                            pygame.draw.rect(s, STONE_LIGHT, (door.x + 4 + k * 8,
                                             door.bottom - 8 - k * 8, 36 - k * 8, 4))
                        panel = round(door.h * (1 - pct / 100))
                        pygame.draw.rect(s, STONE, (door.x, door.y, door.w, panel))
                        pygame.draw.rect(s, STONE_DARK, door, 2)
                elif t == T.POTION:
                    pygame.draw.circle(s, RED, (x + 16, floor_y - 5), 4)
                    pygame.draw.rect(s, WHITE, (x + 15, floor_y - 12, 3, 4))
                elif t == T.PILLAR:
                    pygame.draw.rect(s, STONE_LIGHT, (x + 10, top, 12, floor_y - top))
                elif t == T.TORCH:
                    pygame.draw.rect(s, STONE_DARK, (x + 15, top + 22, 3, 8))
                    flick = 2 if ctx["tick"] % 2 else 0
                    pygame.draw.polygon(s, GOLD, [(x + 12, top + 22), (x + 21, top + 22),
                                                  (x + 16 + flick, top + 10)])
                elif t == T.RUBBLE:
                    for k in range(5):
                        pygame.draw.rect(s, STONE_DARK, (x + 3 + k * 6, floor_y - 3, 4, 3))

    # --- kid ---------------------------------------------------------------
    def draw_kid(self, s: pygame.Surface, pose: Pose) -> None:
        if not pose.visible:
            return
        if self.original:
            im = self.img("KID", assets.image_for(pose.frame), flip=pose.facing > 0)
            s.blit(im, (round(pose.x - im.get_width() / 2), round(pose.y) - im.get_height()))
        else:
            self._kid_placeholder(s, pose)

    def _kid_placeholder(self, s, pose: Pose) -> None:
        x, y, f = round(pose.x), round(pose.y), pose.facing
        if pose.kind == "dead":
            pygame.draw.rect(s, KID_BODY, (x - 14, y - 6, 28, 6))
            pygame.draw.circle(s, KID_HAIR, (x + 14 * f, y - 4), 4)
            return
        h = {"crouch": 22, "hang": 40, "climb": 34, "fall": 40, "jump": 34}.get(pose.kind, 38)
        body = pygame.Rect(x - 4, y - h, 9, h - 6)
        pygame.draw.rect(s, KID_BODY, body)
        pygame.draw.circle(s, KID_HAIR, (x, y - h - 2), 4)
        pygame.draw.line(s, KID_BODY, (x - 2, y - 6), (x - 4 - (pose.frame % 3), y), 2)
        pygame.draw.line(s, KID_BODY, (x + 2, y - 6), (x + 4 + (pose.frame % 3), y), 2)
        if pose.kind in ("hang", "climb", "fall"):
            pygame.draw.line(s, KID_BODY, (x, y - h + 4), (x + 3 * f, y - h - 10), 2)
        else:
            pygame.draw.line(s, KID_BODY, (x, y - h + 6), (x + 7 * f, y - h + 14), 2)
        pygame.draw.circle(s, (20, 20, 20), (x + 2 * f, y - h - 2), 1)

    # --- hud ---------------------------------------------------------------
    def draw_hud(self, s: pygame.Surface, obs: dict) -> None:
        y0 = ROOM_H
        s.fill(BG, (0, y0, SCREEN_W, HUD_H))
        kid = obs["kid"]
        for i in range(kid["max_hp"]):
            full = i < kid["hp"]
            x = 2 + i * 7
            if self.original:
                n = assets.KID_HEARTS["full" if full else "empty"]
                self.blit_bottom(s, "KID", n, x, y0 + 7)
            else:
                pts = [(x, y0 + 1), (x + 5, y0 + 4), (x, y0 + 7)]
                pygame.draw.polygon(s, RED, pts, 0 if full else 1)

    def flash(self, s: pygame.Surface) -> None:
        over = pygame.Surface((ROOM_W, ROOM_H), pygame.SRCALPHA)
        over.fill((255, 0, 0, 90))
        s.blit(over, (0, 0))


def interp_gates(before: dict | None, after: dict, t: float) -> dict[tuple[int, int], float]:
    """Gate openings between two observations of the same room (display only)."""
    if before is None or before["room"] != after["room"]:
        return {}
    old = {(g["row"], g["col"]): g["open_pct"] for g in before["state"]["gates"]}
    out = {}
    for g in after["state"]["gates"]:
        key = (g["row"], g["col"])
        a = old.get(key, g["open_pct"])
        out[key] = a + (g["open_pct"] - a) * t
    return out


__all__ = ["Renderer", "SCREEN_W", "SCREEN_H", "interp_gates", "anim"]

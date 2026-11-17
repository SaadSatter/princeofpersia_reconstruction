"""Generated-art drawing (pygame): the medieval stone dungeon of Shadow Masque.

Reads only one room's tiles and display state (the same observation fields
draw.py uses) and poses. Geometry is render/anim.py's (COL_W 32, ROW_H 63,
TOP 3, FEET 55): the art follows the engine's grid, never the other way.

Layers, back to front: dark back wall, background props (pillars, torches,
exit door: behind ledges and the kid), gates (behind the floor lip), floor
slabs, floor details (loose tiles, plates, spikes, rubble, potion), the kid.

* Floors use a dual grid: the PixelLab tileset's corner tiles sit on cell
  centres and are drawn half a cell offset, so platform ends fall exactly on
  cell edges and a one-cell gap is one cell wide. A room's edge continues its
  own edge cell (the observation shows no neighbouring room).
* Loose tiles and plates are cut from the drawn slab itself, so they are the
  same stone in the same perspective; a rigged-looking tile never differs
  from a plain one except as the engine's state says (shaking, pressed).
* Gate and spikes are drawn here in the dungeon's iron colours: a frameless
  portcullis of two bar planes that slides up into the slab above, and iron
  spikes rising from a floor slot. Our own drawings.
"""

from __future__ import annotations

import colorsys
import json
from pathlib import Path

import pygame

from pop import tiles as T

from . import genart
from .anim import COL_W, FEET, HANG_DROP, ROOM_H, ROOM_W, ROW_H, TOP, Pose

IRON_DK, IRON, IRON_LT, IRON_HI = (20, 22, 30), (52, 57, 70), (100, 107, 122), (150, 157, 170)
RUST = (90, 66, 46)
SHADOW = (14, 15, 20)
WALL_TINT = (95, 95, 115)
PILLAR_TINT = (150, 150, 165)
HEART, HEART_DK = (200, 40, 40), (90, 20, 24)
SOLID = T.HAS_FLOOR | {T.WALL}


def ready(img: pygame.Surface) -> pygame.Surface:
    """Convert to the window's alpha format once a window exists, as draw.py does
    for the original images. Without this, under macOS's cocoa driver (whose
    plain surfaces carry an alpha byte) transparent pixels blitted onto the
    screen came out black: tests/test_generated_art.py
    test_regression_black_box_around_the_kid_on_macos."""
    return img.convert_alpha() if pygame.display.get_surface() else img


def surface_y(r: int) -> int:
    """The flagstone line of row r: where feet stand (anim.stand_point)."""
    return TOP + r * ROW_H + FEET


def slab_bottom(r: int) -> int:
    return TOP + (r + 1) * ROW_H + 3          # the floor edge shows 3 px into the row below


def tinted(img: pygame.Surface, rgb) -> pygame.Surface:
    img = img.copy()
    m = pygame.Surface(img.get_size())
    m.fill(rgb)
    img.blit(m, (0, 0), special_flags=pygame.BLEND_MULT)
    return img


def opaque_rows(img: pygame.Surface) -> tuple[int, int]:
    rows = [y for y in range(img.get_height())
            if any(img.get_at((x, y)).a for x in range(img.get_width()))]
    return rows[0], rows[-1]


def crimson(img: pygame.Surface) -> pygame.Surface:
    """The second rival: the same sprite with the indigo cloth turned crimson and
    the red sash turned gold, so both rivals share every frame and size."""
    out = img.copy()
    w, h = out.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = out.get_at((x, y))
            if not a:
                continue
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.55 <= hh <= 0.75 and ss > 0.25:          # indigo / navy cloth
                hh, ss, vv = 0.98, min(1.0, ss * 1.15), min(1.0, vv * 1.25)
            elif (hh <= 0.03 or hh >= 0.95) and ss > 0.55 and vv > 0.4:   # red sash
                hh, ss = 0.12, 0.75
            else:
                continue
            rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, vv)
            out.set_at((x, y), (round(rr * 255), round(gg * 255), round(bb * 255), a))
    return out


# ------------------------------------------------------------------ drawn pieces
def gate_image(h: int) -> pygame.Surface:
    """A full-height portcullis 12 px wide: a darker back plane of bars set up and
    right for depth, a front plane of 3 bars with cross-bars every 9 px, and
    pointed tips at the bottom."""
    s = pygame.Surface((12, h + 2), pygame.SRCALPHA)

    def plane(x0, y0, col, hi, dk, tips):
        for bx in (x0, x0 + 4, x0 + 8):
            if bx + 1 >= 12:
                continue
            pygame.draw.line(s, dk, (bx + 1, y0), (bx + 1, y0 + h - 1))
            pygame.draw.line(s, hi, (bx, y0), (bx, y0 + h - 1))
            if tips:
                s.set_at((bx, y0 + h), dk)
                s.set_at((bx + 1, y0 + h), dk)
                s.set_at((bx, y0 + h + 1), hi)
        for y in range(y0 + 3, y0 + h - 2, 9):
            pygame.draw.line(s, col, (x0, y), (min(11, x0 + 9), y))
            pygame.draw.line(s, dk, (x0, y + 1), (min(11, x0 + 9), y + 1))

    plane(2, 0, IRON_DK, IRON, SHADOW, False)
    plane(0, 1, IRON, IRON_HI, IRON_DK, True)
    for y in range(4, h, 13):
        s.set_at((4, y), RUST)
    return ready(s)


def spikes_image(state: int) -> pygame.Surface:
    """state 0: the slot only; 1: tips showing; 2: fully out. 32 x 14, base row 12."""
    s = pygame.Surface((32, 14), pygame.SRCALPHA)
    pygame.draw.line(s, SHADOW, (4, 12), (27, 12))
    heights = {0: (0, 0, 0, 0), 1: (4, 5, 4, 5), 2: (10, 12, 9, 11)}[state]
    for i, ht in enumerate(heights):
        if not ht:
            continue
        x = 5 + i * 6
        for k in range(ht):                       # 3 px at the base, tapering to a point
            y = 11 - k
            w = 3 if k < ht * 0.35 else 2 if k < ht * 0.75 else 1
            x0 = x if w >= 2 else x + 1
            s.set_at((x0, y), IRON_HI if w > 1 else IRON_LT)
            for j in range(1, w - 1):
                s.set_at((x0 + j, y), IRON_LT)
            if w > 1:
                s.set_at((x0 + w - 1, y), IRON_DK)
        s.set_at((x + 1, 12 - ht), IRON_HI)
        for j in range(3):
            s.set_at((x + j, 11), RUST)
    return ready(s)


# ------------------------------------------------------------------ the art
class DungeonArt:
    def __init__(self, root: Path):
        self.root = root
        load = lambda rel: ready(pygame.image.load(str(root / rel)))
        table = json.loads((root / "tiles" / "platform.json").read_text())
        sheet = load("tiles/platform.png")
        self.wang = {tuple(t["corners"]): sheet.subsurface((t["x"], t["y"], 32, 32)).copy()
                     for t in table["tiles"]}
        self.inner = self.wang[(True, True, True, True)]
        self.wall = tinted(self.inner, WALL_TINT)
        self.pillar, self.torch, self.door = (load(f"props/{n}.png") for n in ("pillar", "torch", "door"))
        self.cap_top = opaque_rows(self.wang[(False, False, True, True)])[0]
        self.base_bot = opaque_rows(self.wang[(True, True, False, False)])[1]
        self.meta = genart.sprites(root)
        self._strips = {who: {name: load(m["file"]) for name, m in d.items()}
                        for who, d in self.meta.items()}
        self.counts = {name: m["n"] for name, m in self.meta["rival"].items()}
        self._frames: dict[tuple, pygame.Surface] = {}
        self._gates: dict[int, pygame.Surface] = {}
        self._spikes = {k: spikes_image(k) for k in (0, 1, 2)}

    # --- sprites ------------------------------------------------------------
    def frame(self, who: str, strip: str, i: int, flip: bool, colour: str = "indigo") -> pygame.Surface:
        key = (who, strip, i, flip, colour)
        if key not in self._frames:
            m = self.meta[who][strip]
            im = self._strips[who][strip].subsurface((i * m["w"], 0, m["w"], m["h"])).copy()
            if colour == "crimson":
                im = ready(crimson(im))
            self._frames[key] = pygame.transform.flip(im, True, False) if flip else im
        return self._frames[key]

    def blit_actor(self, s, who: str, strip: str, i: int, x: float, y: float, facing: int,
                   colour: str = "indigo") -> None:
        """Feet-anchored strips put their anchor on (x, y); ledge-anchored ones put
        their ledge corner on (x, y)."""
        m = self.meta[who][strip]
        flip = facing < 0
        im = self.frame(who, strip, i, flip, colour)
        ax = m["x"]
        if flip:
            ax = m["w"] - ax if m["type"] == "ledge" else m["w"] - 1 - ax
        s.blit(im, (round(x - ax), round(y - m["y"])))

    def draw_kid(self, s, pose: Pose, colour: str = "indigo") -> None:
        if not pose.visible:
            return
        strip, i = genart.frame_for(pose.frame, self.counts)
        if self.meta["rival"][strip]["type"] == "ledge":
            lx, ly = pose.ledge if pose.ledge else (pose.x + 7 * pose.facing, pose.y - HANG_DROP)
            self.blit_actor(s, "rival", strip, i, lx, ly, pose.facing, colour)
        else:
            self.blit_actor(s, "rival", strip, i, pose.x, pose.y, pose.facing, colour)

    def draw_hearts(self, s, x0: int, y0: int, hp: int, max_hp: int) -> None:
        shape = (".##.##.", "#######", "#######", ".#####.", "..###..", "...#...")
        for k in range(max_hp):
            col = HEART if k < hp else HEART_DK
            for dy, row in enumerate(shape):
                for dx, ch in enumerate(row):
                    if ch == "#":
                        s.set_at((x0 + k * 9 + dx, y0 + dy), col)

    # --- room ---------------------------------------------------------------
    def draw_room(self, s, rows, ctx, object_shape=None) -> None:
        """rows: the room's 3 tile strings. ctx: tick, gates {(r,c): open %},
        exits {(r,c): open %}, sprung, shaking, pressed (sets of (r,c))."""
        for y in range(0, ROOM_H, 32):
            for x in range(0, ROOM_W, 32):
                s.blit(self.wall, (x, y))

        def solid(r, c):
            return rows[r][min(max(c, 0), 9)] in SOLID

        floor = ready(pygame.Surface((ROOM_W, ROOM_H), pygame.SRCALPHA))
        for r in range(3):
            for tx in range(-1, 10):
                a, b = solid(r, tx), solid(r, tx + 1)
                if not (a or b):
                    continue
                x = tx * COL_W + COL_W // 2
                y_lo = slab_bottom(r) - self.base_bot
                clip = surface_y(r) + 4 - y_lo          # the lower half never shows above the cap
                floor.blit(self.wang[(a, b, False, False)], (x, y_lo + clip),
                           area=pygame.Rect(0, clip, 32, 32 - clip))
                floor.blit(self.wang[(False, False, a, b)], (x, surface_y(r) - self.cap_top))

        def vis_bottom(r):
            """Lowest drawn slab pixel under row r (measured, not assumed)."""
            for c in range(10):
                if rows[r][c] in SOLID and rows[r][c] != T.WALL:
                    x = c * COL_W + COL_W // 2
                    ys = [y for y in range(surface_y(r), min(ROOM_H, surface_y(r) + 30))
                          if floor.get_at((x, y)).a]
                    if ys:
                        return max(ys)
            return slab_bottom(r)

        head = [0] + [vis_bottom(r - 1) + 1 for r in (1, 2)]   # underside of the slab above

        for r in range(3):                                      # solid wall blocks
            for c in range(10):
                if rows[r][c] != T.WALL:
                    continue
                rect = pygame.Rect(c * COL_W, head[r], COL_W, surface_y(r) - head[r] + 2)
                for y in range(rect.top, rect.bottom, 32):
                    s.blit(self.inner, (rect.x, y), area=pygame.Rect(0, 0, 32, min(32, rect.bottom - y)))
                if c > 0 and rows[r][c - 1] != T.WALL:
                    pygame.draw.line(s, SHADOW, rect.topleft, rect.bottomleft)
                if c < 9 and rows[r][c + 1] != T.WALL:
                    pygame.draw.line(s, SHADOW, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom))

        for r in range(3):                                      # background props
            for c in range(10):
                t = rows[r][c]
                if t == T.PILLAR:
                    h = surface_y(r) - head[r]
                    s.blit(tinted(pygame.transform.scale(self.pillar, (16, h)), PILLAR_TINT),
                           (c * COL_W + 8, head[r]))
                elif t == T.TORCH:
                    s.blit(pygame.transform.scale(self.torch, (16, 24)), (c * COL_W + 8, surface_y(r) - 40))
                elif t == T.EXIT_LEFT:
                    self._exit(s, r, c, head[r], ctx["exits"].get((r, c), ctx["exits"].get((r, c + 1), 0)))

        for r in range(3):                                      # gates, behind the floor lip
            for c in range(10):
                if rows[r][c] != T.GATE:
                    continue
                full = surface_y(r) + 2 - head[r]
                if full not in self._gates:
                    self._gates[full] = gate_image(full)
                g = self._gates[full]
                pct = ctx["gates"].get((r, c), 0)
                shown = max(6, round(full * (1 - pct / 100)))
                x = (c + 1) * COL_W - 14
                s.blit(g, (x, head[r]), area=pygame.Rect(0, g.get_height() - shown - 2, 12, shown + 2))
                pygame.draw.line(s, SHADOW, (x - 1, head[r]), (x + 12, head[r]))

        s.blit(floor, (0, 0))

        for r in range(3):                                      # floor details
            for c in range(10):
                t = rows[r][c]
                x0, y0 = c * COL_W, surface_y(r)
                if t in (T.LOOSE, T.RAISE_PLATE, T.DROP_PLATE):
                    R = pygame.Rect(x0, y0, COL_W, vis_bottom(r) - y0 + 1)
                    cell = s.subsurface(R).copy()
                    if t == T.LOOSE:
                        dy = 1 + (1 if (r, c) in ctx["shaking"] and ctx["tick"] % 2 else 0)
                        s.blit(self.wall.subsurface((0, 0, COL_W, dy)), (R.x, R.y))
                        s.blit(cell, (R.x, R.y + dy))
                        pygame.draw.line(s, SHADOW, (R.x, R.y), (R.x, R.bottom))
                        pygame.draw.line(s, SHADOW, (R.right - 1, R.y), (R.right - 1, R.bottom))
                        pygame.draw.lines(s, SHADOW, False, [(R.x + 8, R.y + dy), (R.x + 13, R.y + 2 + dy),
                                                             (R.x + 18, R.y + 1 + dy), (R.x + 22, R.y + 4 + dy)])
                    else:
                        sink = 1 if (t == T.DROP_PLATE or (r, c) in ctx["pressed"]) else 0
                        cap = tinted(cell.subsurface((5, 0, COL_W - 10, 4)).copy(), (150, 160, 190))
                        if sink:
                            s.blit(self.wall.subsurface((0, 0, COL_W - 10, 1)), (R.x + 5, R.y))
                        s.blit(cap, (R.x + 5, R.y + sink))
                        pygame.draw.line(s, SHADOW, (R.x + 4, R.y + sink), (R.x + 4, R.y + 3 + sink))
                        pygame.draw.line(s, SHADOW, (R.right - 6, R.y + sink), (R.right - 6, R.y + 3 + sink))
                elif t == T.SPIKES:
                    s.blit(self._spikes[2 if (r, c) in ctx["sprung"] else 0], (x0, y0 - 11))
                elif t == T.RUBBLE:
                    for dx, dy, w in ((6, -2, 4), (11, -3, 5), (17, -2, 3), (21, -1, 4)):
                        pygame.draw.rect(s, IRON_LT, (x0 + dx, y0 + dy, w, 2))
                        pygame.draw.line(s, SHADOW, (x0 + dx, y0 + dy + 2), (x0 + dx + w - 1, y0 + dy + 2))
                elif t == T.POTION:
                    pygame.draw.rect(s, SHADOW, (x0 + 13, y0 - 10, 6, 9))
                    pygame.draw.rect(s, HEART, (x0 + 14, y0 - 7, 4, 5))
                    pygame.draw.rect(s, IRON_HI, (x0 + 15, y0 - 10, 2, 3))
                elif t in (T.SWORD, T.BONES) and object_shape:
                    object_shape(s, "sword" if t == T.SWORD else "bones", x0, y0)

    def _exit(self, s, r, c, top, pct) -> None:
        """The oak door across cells c and c+1; it slides up as the exit opens."""
        d = self.door.subsurface(self.door.get_bounding_rect())
        dh = surface_y(r) - top - 2
        d = pygame.transform.scale(d, (round(d.get_width() * dh / d.get_height()), dh))
        x = c * COL_W + COL_W - d.get_width() // 2
        y = surface_y(r) - dh
        pygame.draw.rect(s, SHADOW, (x + 3, y + 3, d.get_width() - 6, dh - 3))       # the doorway
        shown = round(dh * (1 - pct / 100))
        if shown > 0:
            s.blit(d, (x, y), area=pygame.Rect(0, dh - shown, d.get_width(), shown))

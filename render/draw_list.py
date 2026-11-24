"""One seat's observation as a list of draws for the web client (pure Python, no pygame).

The browser page (web/main.js) only blits: every picture it shows comes from
this list, and every value in the list comes from the one observation passed
in (pop/versus.py `observe(seat)`), plus the display tick for flicker and the
art pack's measured sizes (render/webart.py `art_meta`). It mirrors what
`play.py --versus` draws for one panel with render/dungeon.py: the room, the
swords on the floor, each figure (guards and anything observed as a guard
with the guard strips, the other rival in its seat colour), the seat's own
rival, the suspicion meters this seat may see, and the hearts.

Draws, in drawing order (`layer` says which group a draw belongs to):

* image: {"layer", "img": sheet, "src": [sx, sy, sw, sh], "x", "y", "w", "h",
  "flip", "tint", "rot", "ox", "oy"}. (x, y) is the top-left corner of the
  unrotated picture, w x h its size on screen. `flip` mirrors the picture
  inside that box. `rot` degrees clockwise about (x + ox, y + oy).
* rect: {"layer", "rect": [x, y, w, h], "color"}.
* line: {"layer", "line": [x1, y1, x2, y2], "color"} (one pixel wide).

A figure's draws are a function of that figure's observed fields only, so a
disguised rival (observed as a guard, R-V18) gives exactly a guard's draws.
"""

from __future__ import annotations

from pop import tiles as T

from . import genart, versus_view
from .anim import COL_W, FEET, HANG_DROP, ROOM_H, ROOM_W, ROW_H, TOP, Pose, stand_point
from .webart import IRON, IRON_DK, IRON_HI, IRON_LT, RUST, SHADOW, SPIKE_H, SPIKE_W

HUD_H = 8                                   # render/draw.py HUD_H
SCREEN_W, SCREEN_H = ROOM_W, ROOM_H + HUD_H
WALL_TINT, PILLAR_TINT = (95, 95, 115), (150, 150, 165)
HEART, HEART_DK = (200, 40, 40), (90, 20, 24)
SOLID = T.HAS_FLOOR | {T.WALL}
SPIN_PIVOT = 16
COLOURS = {"A": "indigo", "B": "crimson"}   # play.py versus_main
SHEET_FOR = {"indigo": "rival", "crimson": "rival_crimson"}
LAYERS = ("back", "walls", "props", "gates", "floor", "details", "swords",
          "figures", "me", "meters", "hud")
L = {name: i for i, name in enumerate(LAYERS)}


def hexc(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


def surface_y(r: int) -> int:
    return TOP + r * ROW_H + FEET


def slab_bottom(r: int) -> int:
    return TOP + (r + 1) * ROW_H + 3


def _img(layer: str, sheet: str, src, x, y, w=None, h=None, flip=False, tint=None,
         rot=0.0, ox=0, oy=0) -> dict:
    return {"layer": L[layer], "img": sheet, "src": [int(v) for v in src],
            "x": round(x), "y": round(y), "w": int(src[2] if w is None else w),
            "h": int(src[3] if h is None else h), "flip": bool(flip),
            "tint": None if tint is None else hexc(tint),
            "rot": round(float(rot), 2), "ox": round(ox), "oy": round(oy)}


def _rect(layer: str, x, y, w, h, rgb) -> dict:
    return {"layer": L[layer], "rect": [round(x), round(y), round(w), round(h)],
            "color": hexc(rgb)}


def _line(layer: str, x1, y1, x2, y2, rgb) -> dict:
    return {"layer": L[layer], "line": [round(x1), round(y1), round(x2), round(y2)],
            "color": hexc(rgb)}


# --- the room (render/dungeon.py DungeonArt.draw_room) ----------------------
def room_context(obs: dict, tick: int) -> dict:
    st = obs["state"]
    return {"tick": tick,
            "gates": {(g["row"], g["col"]): g["open_pct"] for g in st["gates"]},
            "exits": {(e["row"], e["col"]): e["open_pct"] for e in st["exits"]},
            "sprung": {tuple(x) for x in st["spikes_sprung"]},
            "shaking": {tuple(x) for x in st["loose_shaking"]},
            "pressed": {tuple(x) for x in st["plates_pressed"]}}


def room_draws(rows: list[str], ctx: dict, art: dict) -> list[dict]:
    size = art["tile"]
    wang = art["wang"]
    out: list[dict] = []

    def tile(key):
        x, y = wang[key]
        return [x, y, size, size]

    for y in range(0, ROOM_H, size):                       # back wall
        for x in range(0, ROOM_W, size):
            out.append(_img("back", "tiles", tile("1111"), x, y, tint=WALL_TINT))

    def solid(r, c):
        return rows[r][min(max(c, 0), 9)] in SOLID

    floor: list[dict] = []
    covered: dict[tuple[int, int], set[int]] = {}           # column-0 floor pixels per (r, c)
    for r in range(3):
        for tx in range(-1, 10):
            a, b = solid(r, tx), solid(r, tx + 1)
            if not (a or b):
                continue
            x = tx * COL_W + COL_W // 2
            y_lo = slab_bottom(r) - art["base_bot"]
            clip = surface_y(r) + 4 - y_lo
            lo, cap = f"{int(a)}{int(b)}00", f"00{int(a)}{int(b)}"
            sx, sy = wang[lo]
            if clip < size:
                floor.append(_img("floor", "tiles", [sx, sy + clip, size, size - clip],
                                  x, y_lo + clip))
            floor.append(_img("floor", "tiles", tile(cap), x, surface_y(r) - art["cap_top"]))
            col = covered.setdefault((r, tx), set())   # column 0 sits on cell tx's middle
            col.update(y_lo + y for y in art["col0"][lo] if y >= clip)
            col.update(surface_y(r) - art["cap_top"] + y for y in art["col0"][cap])

    def vis_bottom(r):
        for c in range(10):
            if rows[r][c] in SOLID and rows[r][c] != T.WALL:
                ys = [y for y in covered.get((r, c), ())
                      if surface_y(r) <= y < min(ROOM_H, surface_y(r) + 30)]
                if ys:
                    return max(ys)
        return slab_bottom(r)

    head = [0] + [vis_bottom(r - 1) + 1 for r in (1, 2)]

    for r in range(3):                                      # solid wall blocks
        for c in range(10):
            if rows[r][c] != T.WALL:
                continue
            x0, top, bottom = c * COL_W, head[r], surface_y(r) + 2
            for y in range(top, bottom, size):
                hh = min(size, bottom - y)
                out.append(_img("walls", "tiles", [*wang["1111"], size, hh], x0, y))
            if c > 0 and rows[r][c - 1] != T.WALL:
                out.append(_line("walls", x0, top, x0, bottom, SHADOW))
            if c < 9 and rows[r][c + 1] != T.WALL:
                out.append(_line("walls", x0 + COL_W - 1, top, x0 + COL_W - 1, bottom, SHADOW))

    props = art["props"]
    for r in range(3):                                      # background props
        for c in range(10):
            t = rows[r][c]
            if t == T.PILLAR:
                p = props["pillar"]
                out.append(_img("props", "props/pillar", [0, 0, p["w"], p["h"]], c * COL_W + 8,
                                head[r], 16, surface_y(r) - head[r], tint=PILLAR_TINT))
            elif t == T.TORCH:
                p = props["torch"]
                out.append(_img("props", "props/torch", [0, 0, p["w"], p["h"]], c * COL_W + 8,
                                surface_y(r) - 40, 16, 24))
            elif t == T.EXIT_LEFT:
                pct = ctx["exits"].get((r, c), ctx["exits"].get((r, c + 1), 0))
                out.extend(_exit(r, c, head[r], pct, props["door"]))

    for r in range(3):                                      # gates, behind the floor lip
        for c in range(10):
            if rows[r][c] == T.GATE:
                out.extend(_gate(r, c, head[r], ctx["gates"].get((r, c), 0)))

    out.extend(floor)

    for r in range(3):                                      # floor details
        for c in range(10):
            out.extend(_detail(rows[r][c], r, c, vis_bottom(r), ctx))
    return out


def _exit(r: int, c: int, top: int, pct: float, door: dict) -> list[dict]:
    bx, by, bw, bh = door["bbox"]
    dh = surface_y(r) - top - 2
    dw = round(bw * dh / bh)
    x = c * COL_W + COL_W - dw // 2
    y = surface_y(r) - dh
    out = [_rect("props", x + 3, y + 3, dw - 6, dh - 3, SHADOW)]
    shown = round(dh * (1 - pct / 100))
    if shown > 0:
        # The door's bottom `shown` rows, drawn from the doorway's top (it slides up).
        src_h = max(1, round(bh * shown / dh))
        out.append(_img("props", "props/door", [bx, by + bh - src_h, bw, src_h], x, y, dw, shown))
    return out


def _gate(r: int, c: int, top: int, pct: float) -> list[dict]:
    """render/dungeon.py gate_image as bars: a back plane and a front plane of
    three bars, sliding up into the slab above as the gate opens."""
    full = surface_y(r) + 2 - top
    shown = max(6, round(full * (1 - pct / 100)))
    x = (c + 1) * COL_W - 14
    out = []
    for x0, y0, hi, dk in ((2, 0, IRON, SHADOW), (0, 1, IRON_HI, IRON_DK)):
        for bx in (x0, x0 + 4, x0 + 8):
            if bx + 1 >= 12:
                continue
            out.append(_rect("gates", x + bx + 1, top, 1, shown + y0, dk))
            out.append(_rect("gates", x + bx, top, 1, shown + y0, hi))
        for y in range(top + shown - 3, top, -9):
            out.append(_rect("gates", x + x0, y, 10, 1, IRON if y0 else IRON_DK))
    out.append(_rect("gates", x - 1, top, 14, 1, SHADOW))
    return out


def _detail(t: str, r: int, c: int, vb: int, ctx: dict) -> list[dict]:
    x0, y0 = c * COL_W, surface_y(r)
    out = []
    if t == T.LOOSE:
        dy = 1 + (1 if (r, c) in ctx["shaking"] and ctx["tick"] % 2 else 0)
        h = vb - y0 + 1
        out.append(_line("details", x0, y0 + dy, x0, y0 + h, SHADOW))
        out.append(_line("details", x0 + COL_W - 1, y0 + dy, x0 + COL_W - 1, y0 + h, SHADOW))
        pts = [(8, 0), (13, 2), (18, 1), (22, 4)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            out.append(_line("details", x0 + ax, y0 + ay + dy, x0 + bx, y0 + by + dy, SHADOW))
    elif t in (T.RAISE_PLATE, T.DROP_PLATE):
        sink = 1 if (t == T.DROP_PLATE or (r, c) in ctx["pressed"]) else 0
        out.append(_rect("details", x0 + 5, y0 + sink, COL_W - 10, 4, (120, 128, 150)))
        out.append(_line("details", x0 + 4, y0 + sink, x0 + 4, y0 + 3 + sink, SHADOW))
        out.append(_line("details", x0 + COL_W - 6, y0 + sink, x0 + COL_W - 6, y0 + 3 + sink,
                         SHADOW))
    elif t == T.SPIKES:
        state = 2 if (r, c) in ctx["sprung"] else 0
        out.append(_img("details", "spikes", [state * SPIKE_W, 0, SPIKE_W, SPIKE_H], x0, y0 - 11))
    elif t == T.RUBBLE:
        for dx, dy, w in ((6, -2, 4), (11, -3, 5), (17, -2, 3), (21, -1, 4)):
            out.append(_rect("details", x0 + dx, y0 + dy, w, 2, IRON_LT))
            out.append(_line("details", x0 + dx, y0 + dy + 2, x0 + dx + w - 1, y0 + dy + 2, SHADOW))
    elif t == T.POTION:
        out.append(_rect("details", x0 + 13, y0 - 10, 6, 9, SHADOW))
        out.append(_rect("details", x0 + 14, y0 - 7, 4, 5, HEART))
        out.append(_rect("details", x0 + 15, y0 - 10, 2, 3, IRON_HI))
    return out


# --- actors (render/dungeon.py blit_actor, draw_kid) --------------------------
def actor(layer: str, sheet: str, strip: str, i: int, x: float, y: float, facing: int,
          meta: dict, spin: float = 0.0) -> dict:
    m = meta[strip]
    flip = facing < 0
    ax = m["x"]
    if flip:
        ax = m["w"] - ax if m["type"] == "ledge" else m["w"] - 1 - ax
    left, top = round(x - ax), round(y - m["y"])
    src = [i * m["w"], 0, m["w"], m["h"]]
    if spin % 360 == 0:
        return _img(layer, f"{sheet}/{strip}", src, left, top, flip=flip)
    # Turned forward (clockwise when facing right) about the body's middle.
    return _img(layer, f"{sheet}/{strip}", src, left, top, flip=flip, rot=spin * facing,
                ox=ax, oy=m["y"] - SPIN_PIVOT)


def pose_draw(layer: str, sheet: str, who: str, pose: Pose, sprites: dict) -> list[dict]:
    if not pose.visible:
        return []
    counts = {k: v["n"] for k, v in sprites[who].items()}
    strip, i = genart.frame_for(pose.frame, counts)
    if sprites[who][strip]["type"] == "ledge":
        lx, ly = pose.ledge if pose.ledge else (pose.x + 7 * pose.facing, pose.y - HANG_DROP)
        return [actor(layer, sheet, strip, i, lx, ly, pose.facing, sprites[who])]
    return [actor(layer, sheet, strip, i, pose.x, pose.y, pose.facing, sprites[who], pose.spin)]


def guard_draws(layer: str, view: dict, room: str, sprites: dict, cache: dict | None,
                key: object) -> list[dict]:
    """Anything observed as a guard (play.py draw_guard). `key` only names the
    pose memo; the draws depend on `view` alone."""
    counts = {k: v["n"] for k, v in sprites["guard"].items()}
    spr = versus_view.guard_sprite(view, counts)
    if spr is None:
        return pose_draw(layer, "guard", "guard", versus_view.pose(view, room, cache, key), sprites)
    return [actor(layer, "guard", spr.strip, spr.index, spr.x, spr.y, spr.facing,
                  sprites["guard"])]


def rival_draws(layer: str, view: dict, room: str, colour: str, sprites: dict,
                cache: dict | None, key: object) -> list[dict]:
    """An undisguised rival in its seat colour (play.py draw_actor)."""
    sheet = SHEET_FOR[colour]
    counts = {k: v["n"] for k, v in sprites["rival"].items()}
    spr = versus_view.sprite(view, counts)
    if spr is not None:
        return [actor(layer, sheet, spr.strip, spr.index, spr.x, spr.y, spr.facing,
                      sprites["rival"])]
    return pose_draw(layer, sheet, "rival", versus_view.pose(view, room, cache, key), sprites)


def sword_draws(swords: list[dict]) -> list[dict]:
    out = []
    for sw in swords:
        x, y = stand_point(sw["row"], sw["col"])
        y = y - 18 if sw["flying"] else y - 1
        out.append(_line("swords", x - 7, y, x + 6, y, (220, 231, 236)))
        out.append(_line("swords", x - 8, y - 1, x - 8, y + 1, (69, 78, 106)))
    return out


EYE = ((-2, -4), (-1, -5), (0, -5), (1, -5), (2, -4), (-1, -3), (0, -3), (1, -3))


def meter_draws(entry: dict) -> list[dict]:
    """A guard's suspicion of this seat (play.py draw_meter)."""
    x, y = (round(v) for v in stand_point(entry["row"], entry["col"]))
    y -= 36
    col = (230, 170, 40) if entry["level"] < 70 else (220, 50, 40)
    out = [_rect("meters", x - 9, y - 1, 18, 5, SHADOW), _rect("meters", x - 8, y, 16, 3, (60, 60, 70)),
           _rect("meters", x - 8, y, round(16 * entry["level"] / 100), 3, col)]
    out += [_rect("meters", x + dx, y + dy, 1, 1, (235, 230, 215)) for dx, dy in EYE]
    out.append(_rect("meters", x, y - 4, 1, 1, SHADOW))
    return out


HEART_SHAPE = (".##.##.", "#######", "#######", ".#####.", "..###..", "...#...")


def heart_draws(hp: int, max_hp: int, x0: int = 2, y0: int = ROOM_H + 1) -> list[dict]:
    out = []
    for k in range(max_hp):
        col = HEART if k < hp else HEART_DK
        for dy, row in enumerate(HEART_SHAPE):
            start = None
            for dx, ch in enumerate(row + "."):
                if ch == "#" and start is None:
                    start = dx
                elif ch != "#" and start is not None:
                    out.append(_rect("hud", x0 + k * 9 + start, y0 + dy, dx - start, 1, col))
                    start = None
    return out


# --- one seat's payload ---------------------------------------------------------
def seat_draws(obs: dict, colour: str, other_colour: str, tick: int, art: dict,
               cache: dict | None = None) -> list[dict]:
    sprites = art["sprites"]
    room = obs["room"]
    out = [_rect("back", 0, 0, SCREEN_W, SCREEN_H, (0, 0, 0))]
    out += room_draws(obs["tiles"], room_context(obs, tick), art)
    out += sword_draws(obs["swords"])
    for j, fig in enumerate(obs["figures"]):
        if fig["kind"] == "rival":
            out += rival_draws("figures", fig, room, other_colour, sprites, cache, ("fig", j))
        else:
            out += guard_draws("figures", fig, room, sprites, cache, ("fig", j))
    me = obs["me"]
    if me["disguised"]:
        out += guard_draws("me", me, room, sprites, cache, "me")      # in uniform (R-V18)
    else:
        out += rival_draws("me", me, room, colour, sprites, cache, "me")
    for entry in obs["suspicion"]:
        out += meter_draws(entry)
    out += heart_draws(me["hp"], me["max_hp"])
    return out


def hud(obs: dict) -> dict:
    """Text the page shows beside the panel: all from this seat's own rival."""
    me = obs["me"]
    sword = f"sword drawn ({me['stance']})" if me["armed"] else "sword not drawn"
    parts = [f"hearts {me['hp']}/{me['max_hp']}", f"{obs['minutes_left']} min left", sword]
    if me["disguised"]:
        parts.append("in a guard's uniform")
    return {"hp": me["hp"], "max_hp": me["max_hp"], "minutes_left": obs["minutes_left"],
            "armed": me["armed"], "stance": me["stance"], "disguised": me["disguised"],
            "text": " · ".join(parts)}


def seat_payload(obs: dict, colour: str, other_colour: str, tick: int, art: dict,
                 cache: dict | None = None) -> dict:
    """{"seat_view", "draw", "hud"} for one seat: a function of `obs` (and the
    display tick and art sizes) only."""
    return {"seat_view": obs, "draw": seat_draws(obs, colour, other_colour, tick, art, cache),
            "hud": hud(obs)}

"""Which original pieces make up a room picture, and where (pure; no pygame).

Every piece belongs to one cell and is placed inside that cell's column,
so walls, holes, gates and spikes line up with the engine's cells. The one
exception is the floor surface's right-hand part: in the original's
perspective a floor's top surface leans right and its back edge reaches
into the next cell (`OVERHANG`). Its front edge, where the kid stands and
falls, still ends on the cell boundary.

Regression (session 06, student playtest): a wall's shaded side face was
drawn 25 px into the cell to its right and hid most of a one-cell pit, so
the kid seemed to fall into brickwork. Side faces are no longer drawn.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pop import tiles as T

from . import assets
from .anim import COL_W, ROW_H, TOP

V = "VDUNGEON"
P = "PRINCE"

# Floor-surface right-hand parts: the only pieces drawn in the next column.
OVERHANG = {"floor_right", "loose_right", "loose_right_shake", "rubble_right",
            "spike_floor_right", "pillar_right"}


@dataclass(frozen=True)
class Piece:
    name: str                  # key in assets.DUNGEON, or wall/decor/potion/flame/gate/exit
    folder: str
    number: int                # image number (0 for gate/exit, drawn specially)
    x: int                     # left edge, room pixels
    bottom: int                # bottom edge, room pixels
    cell: tuple[int, int]      # (row, col) the piece belongs to
    value: float = 0.0         # gate/exit open percentage


def row_top(r: int) -> int:
    return TOP + r * ROW_H


def variant(room: str, r: int, c: int, n: int) -> int:
    """A stable per-cell choice so walls and decor don't flicker or repeat evenly."""
    return hashlib.sha1(f"{room}:{r}:{c}".encode()).digest()[0] % n


def room_pieces(rows: list[str], ctx: dict) -> list[Piece]:
    """Pieces in drawing order. ctx: room, tick, gates, exits, sprung, shaking, pressed."""
    D = assets.DUNGEON
    out: list[Piece] = []
    for r, line in enumerate(rows):
        top = row_top(r)
        bottom = top + 60
        for c, t in enumerate(line):
            x = c * COL_W
            cell = (r, c)
            left = line[c - 1] if c > 0 else None
            if t == T.SPACE and variant(ctx["room"], r, c, 7) == 0:
                dec = D["decor"][variant(ctx["room"], r, c + 11, 4)]
                out.append(Piece("decor", V, dec, x + 2, top + 40, cell))
            # The back edge of the floor on the left leans into this cell.
            if (left is not None and left in T.HAS_FLOOR and t != T.WALL
                    and left not in (T.EXIT_LEFT, T.GATE)):
                name = {T.PILLAR: "pillar_right", T.RUBBLE: "rubble_right",
                        T.SPIKES: "spike_floor_right", T.LOOSE: "loose_right"}.get(left,
                                                                                "floor_right")
                if left == T.LOOSE and (r, c - 1) in ctx["shaking"] and ctx["tick"] % 2:
                    name = "loose_right_shake"
                out.append(Piece(name, V, D[name], x, top + 62, (r, c - 1)))
            elif left == T.GATE and t != T.WALL:
                out.append(Piece("floor_right", V, D["floor_right"], x, top + 62, (r, c - 1)))
            out.extend(_tile(t, r, c, x, top, bottom, ctx))
    return out


def _tile(t: str, r: int, c: int, x: int, top: int, bottom: int, ctx: dict) -> list[Piece]:
    D = assets.DUNGEON
    cell = (r, c)
    if t in (T.SPACE, T.EXIT_RIGHT):
        return []                                     # the exit draws both halves
    if t == T.WALL:
        face, base = assets.WALLS[variant(ctx["room"], r, c, len(assets.WALLS))]
        return [Piece("wall", V, face, x, bottom, cell), Piece("wall_base", V, base, x,
                                                              bottom + 3, cell)]
    if t == T.EXIT_LEFT:
        pct = ctx["exits"].get(cell, ctx["exits"].get((r, c + 1), 0))
        return [Piece("exit", V, 0, x, bottom, cell, pct)]
    main = {T.LOOSE: "loose", T.RUBBLE: "rubble", T.PILLAR: "pillar", T.GATE: "gate",
            T.SPIKES: "spike_floor"}.get(t, "floor")
    if t == T.LOOSE and cell in ctx["shaking"] and ctx["tick"] % 2:
        main = "loose_shake"
    if t in T.PLATES:
        main = ("plate_up" if t == T.RAISE_PLATE and cell not in ctx["pressed"]
                else "plate_down")
    base = "plate_base" if t in T.PLATES else "base"
    out = [Piece(main, V, D[main], x, bottom, cell), Piece(base, V, D[base], x, bottom + 3, cell)]
    if t == T.SPIKES:
        if cell in ctx["sprung"]:
            out.append(Piece("spikes_out", V, D["spikes_out"], x, bottom - 2, cell))
        else:
            out.append(Piece("spikes_low", V, D["spikes_low"], x + 2, bottom - 3, cell))
    elif t == T.GATE:
        out.append(Piece("gate_bars", V, 0, x, top, cell, ctx["gates"].get(cell, 0)))
    elif t == T.POTION:
        out.append(Piece("potion", P, assets.POTION, x + 12, bottom - 4, cell))
        b = assets.BUBBLES[ctx["tick"] % len(assets.BUBBLES)]
        out.append(Piece("bubbles", P, b, x + 15, bottom - 15, cell))
    elif t == T.TORCH:
        out.append(Piece("torch_bracket", V, D["torch_bracket"], x, top + 30, cell))
        fl = assets.FLAMES[(ctx["tick"] + c) % len(assets.FLAMES)]
        out.append(Piece("flame", P, fl, x + 16, top + 22, cell))
    return out

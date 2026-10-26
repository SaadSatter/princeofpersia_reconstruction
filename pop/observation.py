"""What a player may see: the current room as a human sees it (GAME_SPEC §8).

Nothing here reads plate links, internal timer counts, other rooms, the
situation id, or whether a situation is held out.
"""

from __future__ import annotations

import hashlib

from . import physics as P
from .engine import Game
from .mechanics import GATE_MAX

OBSERVATION_KEYS = {"room", "tiles", "state", "edges", "kid", "minutes_left",
                    "actions_left", "last_result", "task"}
STATE_KEYS = {"gates", "exits", "spikes_sprung", "loose_shaking", "plates_pressed"}
KID_KEYS = {"row", "col", "facing", "posture", "hp", "max_hp"}
RESULT_KEYS = {"effect", "frames", "fell_rows", "hp_change"}


def room_label(situation_id: str, room: int) -> str:
    """Opaque, stable name for a room (stands in for recognizing it on screen)."""
    digest = hashlib.sha1(f"{situation_id}:{room}".encode()).hexdigest()[:6]
    return f"room-{digest}"


def build(game: Game, actions_left: int | None, last_result: dict | None) -> dict:
    k = game.kid
    room = k.room
    in_room = lambda cell: cell[0] == room  # noqa: E731
    gates = [{"row": c[1], "col": c[2], "open_pct": round(100 * g.pos / GATE_MAX),
              "bars": g.bars}
             for c, g in sorted(game.mech.gates.items()) if in_room(c)]
    exits = [{"row": c[1], "col": c[2], "open_pct": round(100 * e.pos / GATE_MAX),
              "open": e.open}
             for c, e in sorted(game.mech.exits.items()) if in_room(c)]
    left, right, _up, _down = game.geom.links[room]
    return {
        "room": room_label(game.situation.id, room),
        "tiles": game.geom.rows(room),
        "state": {
            "gates": gates,
            "exits": exits,
            "spikes_sprung": [[c[1], c[2]] for c, t in sorted(game.mech.spikes.items())
                              if in_room(c) and t > 0],
            "loose_shaking": [[c[1], c[2]] for c in sorted(game.mech.loose) if in_room(c)],
            "plates_pressed": [[c[1], c[2]] for c, t in sorted(game.mech.plates.items())
                               if in_room(c) and t > 0],
        },
        # Up/down links are not shown: a pit looks the same whether or not a
        # room lies below it.
        "edges": {"left": bool(left), "right": bool(right)},
        "kid": {"row": k.row, "col": k.col,
                "facing": "right" if k.facing > 0 else "left",
                "posture": k.posture, "hp": k.hp, "max_hp": k.max_hp},
        "minutes_left": max(0, (P.GAME_FRAMES - game.frames) // (12 * 60)),
        "actions_left": actions_left,
        "last_result": None if last_result is None else
        {key: last_result[key] for key in RESULT_KEYS},
        "task": game.situation.task,
    }

"""Authoritative game state and transitions (headless, deterministic).

One `Game` holds the whole world. `perform(action)` runs one macro action
(at most MAX_FRAMES frames) by calling `_tick()` once per frame. Human play and
agent play both go through `perform` (R-D07).
"""

from __future__ import annotations

import copy
import random
from dataclasses import asdict, dataclass

from . import physics as P
from . import tiles as T
from .mechanics import Mechanics
from .physics import Cell, Geometry
from .situations import Situation

ACTIONS = (
    "WAIT", "LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT", "JUMP_LEFT", "JUMP_RIGHT",
    "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT", "UP", "DOWN",
)

LEGAL_BY_POSTURE = {
    "standing": ACTIONS,
    "hanging": ("WAIT", "UP", "DOWN"),
    "falling": ("WAIT",),
    "dead": (),
    "won": (),
}

DIRECTIONS = {"LEFT": -1, "RIGHT": +1}


@dataclass
class Kid:
    room: int
    row: int
    col: int
    facing: int
    posture: str = "standing"
    hp: int = 3                      # R-C19
    max_hp: int = 3
    hang_ledge: Cell | None = None
    fall_timer: int = 0
    fall_rows: int = 0
    fall_from_hang: bool = False

    @property
    def cell(self) -> Cell:
        return (self.room, self.row, self.col)


class Game:
    def __init__(self, situation: Situation, seed: int = 0):
        self.situation = situation
        self.seed = seed
        self.rng = random.Random(seed)  # unused until combat exists; kept for determinism
        self.geom = Geometry(situation.rooms, situation.links)
        self.mech = Mechanics(self.geom, situation.plate_links, situation.exits_open)
        room, row, col, facing = situation.start
        self.kid = Kid(room, row, col, facing)
        self.frames = 0
        self.terminal: str | None = None
        self._result: dict = {}

    # --- helpers -------------------------------------------------------
    def blocks(self, where: Cell | str) -> bool:
        """True if the kid cannot move horizontally into `where`."""
        if not isinstance(where, tuple):
            return where != P.BOTTOM
        return self.geom.tile(where) == T.WALL or self.mech.gate_bars(where)

    def ahead(self, n: int = 1) -> Cell | str:
        return self.geom.offset(self.kid.cell, 0, self.kid.facing * n)

    def _set_pos(self, cell: Cell) -> None:
        self.kid.room, self.kid.row, self.kid.col = cell

    def _die(self, reason: str) -> None:
        self.kid.posture = "dead"
        self.kid.hp = 0
        self.kid.hang_ledge = None
        self.terminal = reason
        self._result["effect"] = "died"

    def _near_cells(self) -> set[Cell]:
        near = set()
        for dc in (-1, 0, 1):
            c = self.geom.offset(self.kid.cell, 0, dc)
            if isinstance(c, tuple):
                near.add(c)
        return near

    def _pressing(self) -> Cell | None:
        k = self.kid
        if k.posture == "standing" and self.geom.tile(k.cell) in T.PLATES:
            return k.cell
        if k.posture == "hanging" and k.hang_ledge and self.geom.tile(k.hang_ledge) in T.PLATES:
            return k.hang_ledge
        return None

    # --- one frame -----------------------------------------------------
    def _tick(self) -> None:
        self.frames += 1
        k = self.kid
        alive = k.posture not in ("dead", "won")
        events = self.mech.tick(self._pressing() if alive else None,
                                self._near_cells() if alive else set())
        for _, loose_cell, landed in events:
            if not alive:
                break
            if k.posture == "standing" and k.cell == loose_cell:
                self._start_fall(from_hang=False)
            elif k.posture == "hanging" and k.hang_ledge == loose_cell:
                k.hang_ledge = None
                self._start_fall(from_hang=True)
            elif landed is not None and k.cell == landed and k.posture == "standing":
                self._hurt(1, "died:crushed")         # R-C14 crush
        if k.posture == "falling":
            k.fall_timer += 1
            if k.fall_timer >= P.FALL_PER_ROW:
                k.fall_timer = 0
                self._descend()
        if self.terminal is None and self.frames >= P.GAME_FRAMES:
            self.terminal = "time_up"

    def _hurt(self, amount: int, reason: str) -> None:
        self.kid.hp -= amount
        self._result["hp_change"] = self._result.get("hp_change", 0) - amount
        if self.kid.hp <= 0:
            self.kid.hp = 0
            self._die(reason)

    def _start_fall(self, from_hang: bool) -> None:
        k = self.kid
        k.posture, k.fall_timer, k.fall_rows, k.fall_from_hang = "falling", 0, 0, from_hang
        self._result["effect"] = "fell"

    def _descend(self) -> None:
        k = self.kid
        below = self.geom.offset(k.cell, 1, 0)
        if not isinstance(below, tuple):
            self._die("died:fall")                   # bottomless (R-D15)
            return
        self._set_pos(below)
        k.fall_rows += 1
        if self.geom.supported(below):
            self._land()

    def _land(self) -> None:
        k = self.kid
        rows = k.fall_rows - (1 if k.fall_from_hang else 0)   # R-D17
        self._result["fell_rows"] = k.fall_rows
        k.posture = "standing"
        if self.geom.tile(k.cell) == T.SPIKES:
            self._die("died:spikes")                 # R-C13 landing case
            return
        if rows >= 3:
            self._die("died:fall")                   # R-C10 via R-D03
            return
        if rows == 2:
            self._hurt(1, "died:fall")
            if self.terminal:
                return
            self._result["effect"] = "hurt"
        else:
            self._result["effect"] = "landed"
        self.mech.touch_loose(k.cell)

    def _enter(self, cell: Cell, how: str) -> None:
        """Kid arrives in `cell` by 'run', 'step', 'jump' or 'climb'."""
        self._set_pos(cell)
        tile = self.geom.tile(cell)
        if tile == T.SPIKES and how in ("run", "jump"):
            self._die("died:spikes")                 # R-C13
            return
        if not self.geom.supported(cell):
            self._start_fall(from_hang=False)
            return
        self.mech.touch_loose(cell)

    def _frames(self, n: int):
        for _ in range(n):
            self._tick()
            yield

    # --- macros --------------------------------------------------------
    def _directional(self, d: int, kind: str):
        k = self.kid
        if k.facing != d:                            # R-D20: reverse = turn only
            k.facing = d
            self._result["effect"] = "turned"
            yield from self._frames(P.TURN)
            return
        if kind == "run":
            yield from self._run()
        elif kind == "step":
            yield from self._step()
        elif kind == "jump":
            yield from self._jump(running=False)
        else:
            yield from self._jump(running=True)

    def _run(self):
        target = self.ahead()
        if self.blocks(target):
            self._result["effect"] = "bumped"
            yield from self._frames(P.BUMP)
            return
        self._result["effect"] = "moved"
        yield from self._frames(P.RUN)
        if self.terminal is None:
            self._enter(target, "run")

    def _step(self):
        target = self.ahead()
        if self.blocks(target):
            self._result["effect"] = "bumped"
            yield from self._frames(P.BUMP)
            return
        if not self.geom.supported(target):
            self._result["effect"] = "edge"           # careful steps never walk off
            yield from self._frames(P.BUMP)
            return
        self._result["effect"] = "moved"
        yield from self._frames(P.STEP)
        if self.terminal is None:
            self._enter(target, "step")

    def _jump(self, running: bool):
        k = self.kid
        span, flight = P.JUMP_SPAN, P.JUMP
        if running:
            first = self.ahead()
            if self.blocks(first) or not self.geom.supported(first):
                yield from self._run()               # no run-up: behaves as LEFT/RIGHT
                return
            yield from self._frames(P.RUN)
            if self.terminal is not None:
                return
            self._enter(first, "run")
            if k.posture != "standing" or self.terminal is not None:
                return
            span, flight = P.RUN_JUMP_SPAN, P.RUN_JUMP_FLIGHT
        target = None
        for i in range(1, span + 1):
            cell = self.ahead(i)
            if self.blocks(cell):
                break
            target = cell
        if target is None:
            self._result["effect"] = "bumped"
            yield from self._frames(P.JUMP_IN_PLACE)
            return
        self._result["effect"] = "jumped"
        yield from self._frames(flight)
        if self.terminal is None:
            self._enter(target, "jump")

    def _up(self):
        k = self.kid
        if k.posture == "hanging":
            self._result["effect"] = "climbed"
            yield from self._frames(P.HANG_UP)
            if self.terminal is None:
                ledge, k.hang_ledge, k.posture = k.hang_ledge, None, "standing"
                self._enter(ledge, "climb")
            return
        ex = self.mech.exit_for(k.cell)
        if ex is not None and ex.open:               # R-C17
            self._result["effect"] = "won"
            yield from self._frames(P.STAIRS)
            if self.terminal is None:
                k.posture = "won"
                self.terminal = "won"
            return
        above = self.geom.offset(k.cell, -1, 0)
        above_ahead = self.geom.offset(k.cell, -1, k.facing)
        if (isinstance(above, tuple) and self.geom.tile(above) == T.SPACE
                and isinstance(above_ahead, tuple) and not self.blocks(above_ahead)
                and self.geom.supported(above_ahead)):
            self._result["effect"] = "climbed"       # R-C12 (simplified)
            yield from self._frames(P.CLIMB_UP)
            if self.terminal is None:
                self._enter(above_ahead, "climb")
            return
        self._result["effect"] = "none"
        yield from self._frames(P.JUMP_IN_PLACE)

    def _down(self):
        k = self.kid
        if k.posture == "hanging":
            k.hang_ledge = None
            self._start_fall(from_hang=True)
            self._result["effect"] = "dropped"
            return
            yield  # pragma: no cover  (makes this a generator)
        if self.geom.tile(k.cell) == T.POTION:      # R-C16 type 1 (R-A03)
            self._result["effect"] = "drank"
            yield from self._frames(P.DRINK)
            if self.terminal is None:
                self.geom.set_tile(k.cell, T.FLOOR)
                if k.hp < k.max_hp:
                    k.hp += 1
                    self._result["hp_change"] = self._result.get("hp_change", 0) + 1
            return
        target = self.ahead()
        if (isinstance(target, tuple) and not self.blocks(target)
                and not self.geom.supported(target)):
            self._result["effect"] = "hanging"
            yield from self._frames(P.HANG_DOWN)
            if self.terminal is None:
                k.hang_ledge = k.cell
                self._set_pos(target)
                k.facing = -k.facing                 # turns to face the ledge
                k.posture = "hanging"
            return
        self._result["effect"] = "none"
        yield from self._frames(P.CROUCH)

    def _wait(self):
        self._result["effect"] = "waited"
        yield from self._frames(P.WAIT)

    # --- public --------------------------------------------------------
    def legal_actions(self) -> tuple[str, ...]:
        if self.terminal is not None:
            return ()
        return LEGAL_BY_POSTURE[self.kid.posture]

    def perform(self, action: str) -> dict:
        """Run one legal macro action. Caller must validate `action` first."""
        assert action in self.legal_actions(), action
        self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
        if action == "WAIT":
            gen = self._wait()
        elif action == "UP":
            gen = self._up()
        elif action == "DOWN":
            gen = self._down()
        else:
            parts = action.split("_")
            d = DIRECTIONS[parts[-1]]
            kind = {"LEFT": "run", "RIGHT": "run", "STEP": "step",
                    "JUMP": "jump", "RUN": "run_jump"}[parts[0]]
            gen = self._directional(d, kind)
        frames = 0
        # Run the macro to completion: code after its last frame (e.g. landing)
        # must execute. Every macro is at most MAX_FRAMES long by construction.
        for _ in gen:
            frames += 1
            if self.terminal is not None:
                break
        assert frames <= P.MAX_FRAMES, (action, frames)
        while (self.terminal is None and self.kid.posture == "falling"
               and frames < P.MAX_FRAMES):
            self._tick()
            frames += 1
        self._result["frames"] = frames
        return dict(self._result)

    def snapshot(self) -> dict:
        """Complete authoritative state (for tests and determinism checks)."""
        return copy.deepcopy({
            "kid": asdict(self.kid),
            "frames": self.frames,
            "terminal": self.terminal,
            "grid": {room: self.geom.rows(room) for room in sorted(self.geom.grid)},
            "mech": self.mech.snapshot(),
        })

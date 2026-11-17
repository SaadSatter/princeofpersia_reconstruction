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
    sword: bool = False              # Level 1 only (R-C21)
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
        self.mech = Mechanics(self.geom, situation.plate_links, situation.exits_open,
                              situation.gates_open)
        room, row, col, facing = situation.start
        self.kid = Kid(room, row, col, facing)
        self.frames = 0
        self.terminal: str | None = None
        self._result: dict = {}
        self._airborne = False        # kid has left his floor mid-move (see _phase)
        self.plan: dict | None = None  # the move in progress, for real-time display (_plan)
        self.intro: dict | None = None
        if situation.start_falling or situation.start_presses:
            self._intro()

    def _intro(self) -> None:
        """Level 1 entry (R-C30, Source/SUBS.S:1540-1550): plates pressed at load
        (slamming the gate behind the kid), then he drops in. The player has no
        control until he lands, so these frames pass before the first
        observation; they are reported in `intro` for the frontend."""
        self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
        for cell in self.situation.start_presses:
            self.mech.press_once(cell)
        frames = 0
        if self.situation.start_falling:
            self._start_fall(from_hang=False)
            while self.kid.posture == "falling" and self.terminal is None and frames < 48:
                self._tick()
                frames += 1
        self._result["frames"] = frames
        self.intro = dict(self._result)
        self._result = {}

    def rule(self, name: str) -> bool:
        return name in self.situation.rules

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
        self._react(events)
        if self.terminal is None and self.frames >= P.GAME_FRAMES:
            self.terminal = "time_up"

    def _react(self, events: list) -> None:
        """The kid's part of one frame: loose floors that fell this frame (`events`
        from Mechanics.tick), then his own fall. Split from `_tick` so a duel
        (pop/versus.py) can advance the shared world once per frame and let each
        rival react; single-player behaviour is unchanged."""
        k = self.kid
        alive = k.posture not in ("dead", "won")
        for _, loose_cell, landed in events:
            if not alive:
                break
            # A kid who has already left his floor mid-move (`_airborne`) is
            # no longer standing on it or under it (R-D33).
            if k.posture == "standing" and k.cell == loose_cell and not self._airborne:
                self._start_fall(from_hang=False)
            elif k.posture == "hanging" and k.hang_ledge == loose_cell:
                k.hang_ledge = None
                self._start_fall(from_hang=True)
            elif (landed is not None and k.cell == landed and k.posture == "standing"
                  and not self._airborne):
                self._hurt(1, "died:crushed")         # R-C14 crush
        if k.posture == "falling":
            k.fall_timer += 1
            if k.fall_timer >= P.FALL_PER_ROW:
                k.fall_timer = 0
                self._descend()

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

    def _phase(self, n: int, depart: int | None = None):
        """Run the `n` frames of a movement, then tell the caller whether it may
        complete (use as `ok = yield from self._phase(...)`).

        Shared resolution for every move that ends somewhere other than where
        it began (R-D33). The kid keeps his footing, or his hold on a ledge,
        until frame `depart` (None: throughout). If the world takes that
        support away first (a loose floor falls, R-C14) the move is
        interrupted: he is already falling from where he actually is, and the
        caller must not place him at the destination it planned. From
        `depart` on he is in motion, so the floor he left no longer affects
        him; the caller then places him and `_enter` checks support on
        arrival.

        Regression (session 10): the macros used to run their frames and then
        place the kid at the planned cell without this check, leaving him
        "falling" on solid ground or falling into a wall
        (tests/test_regressions.py, loose-floor movement tests)."""
        k = self.kid
        before = (k.posture, k.cell, k.hang_ledge)
        try:
            for i in range(n):
                if depart is not None and i == depart:
                    self._airborne = True
                self._tick()
                yield
                if self.terminal is not None:
                    return False
                if (k.posture, k.cell, k.hang_ledge) != before:
                    return False                     # interrupted: he is falling
            return True
        finally:
            self._airborne = False

    def _plan(self, effect: str, frames: int, to: Cell | None = None,
              posture: str = "standing", facing: int | None = None) -> None:
        """Record the move just decided: its effect, length in frames and where it
        should end. Display only (a real-time renderer animates the move while it
        runs; the macro places the kid only at its end). Never part of results,
        observations or traces."""
        k = self.kid
        self.plan = {"effect": effect, "frames": frames, "to": to or k.cell,
                     "posture": posture, "facing": k.facing if facing is None else facing}

    # --- macros --------------------------------------------------------
    def _directional(self, d: int, kind: str):
        k = self.kid
        if k.facing != d:                            # R-D20: reverse = turn only
            k.facing = d
            self._result["effect"] = "turned"
            self._plan("turned", P.TURN)
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
            self._plan("bumped", P.BUMP)
            yield from self._frames(P.BUMP)
            return
        self._result["effect"] = "moved"
        self._plan("moved", P.RUN, target if isinstance(target, tuple) else None)
        if (yield from self._phase(P.RUN, P.RUN_DEPART)):
            self._enter(target, "run")

    def _step(self):
        target = self.ahead()
        if self.blocks(target):
            self._result["effect"] = "bumped"
            self._plan("bumped", P.BUMP)
            yield from self._frames(P.BUMP)
            return
        if not self.geom.supported(target):
            self._result["effect"] = "edge"           # careful steps never walk off
            self._plan("edge", P.BUMP)
            yield from self._frames(P.BUMP)
            return
        self._result["effect"] = "moved"
        self._plan("moved", P.STEP, target)
        if (yield from self._phase(P.STEP, P.STEP_DEPART)):
            self._enter(target, "step")

    def _jump(self, running: bool):
        k = self.kid
        span, flight, depart = P.JUMP_SPAN, P.JUMP, P.JUMP_DEPART
        if running:
            first = self.ahead()
            if self.blocks(first) or not self.geom.supported(first):
                yield from self._run()               # no run-up: behaves as LEFT/RIGHT
                return
            self._plan("moved", P.RUN, first)
            if not (yield from self._phase(P.RUN, P.RUN_DEPART)):
                return
            self._enter(first, "run")
            if k.posture != "standing" or self.terminal is not None:
                return
            span, flight, depart = P.RUN_JUMP_SPAN, P.RUN_JUMP_FLIGHT, 0   # takes off running
        target = None
        for i in range(1, span + 1):
            cell = self.ahead(i)
            if self.blocks(cell):
                break
            target = cell
        if target is None:
            self._result["effect"] = "bumped"
            self._plan("bumped", P.JUMP_IN_PLACE)
            yield from self._frames(P.JUMP_IN_PLACE)
            return
        self._result["effect"] = "jumped"
        self._plan("jumped", flight, target)
        if (yield from self._phase(flight, depart)):
            self._enter(target, "jump")

    def _up(self):
        k = self.kid
        if k.posture == "hanging":
            self._result["effect"] = "climbed"
            self._plan("climbed", P.HANG_UP, k.hang_ledge)
            # Holds the ledge throughout: if it falls, he falls (R-C14).
            if (yield from self._phase(P.HANG_UP)):
                ledge, k.hang_ledge, k.posture = k.hang_ledge, None, "standing"
                self._enter(ledge, "climb")
            return
        ex = self.mech.exit_for(k.cell)
        if ex is not None and ex.open:               # R-C17
            self._result["effect"] = "won"
            self._plan("won", P.STAIRS, posture="won")
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
            self._plan("climbed", P.CLIMB_UP, above_ahead)
            if (yield from self._phase(P.CLIMB_UP, P.CLIMB_DEPART)):
                self._enter(above_ahead, "climb")
            return
        above_tile = self.geom.tile(above) if isinstance(above, tuple) else None
        if self.rule("ceiling_loose") and above_tile == T.LOOSE:
            # Hopping up touches the ceiling and knocks a loose floor down
            # (R-C31, Source/CTRL.S:2000-2005).
            self.mech.touch_loose(above)
            # Name the effect only if the floor is in view; a floor in the
            # room above is not on screen (audit 2026-10-26 session 08, F1).
            self._result["effect"] = "bumped_ceiling" if above[0] == k.room else "none"
        else:
            self._result["effect"] = "none"
        self._plan(self._result["effect"], P.JUMP_IN_PLACE)
        yield from self._frames(P.JUMP_IN_PLACE)

    def _down(self):
        k = self.kid
        if k.posture == "hanging":
            k.hang_ledge = None
            self._start_fall(from_hang=True)
            self._result["effect"] = "dropped"
            self._plan("dropped", 0, posture="falling")
            return
            yield  # pragma: no cover  (makes this a generator)
        if self.rule("sword") and self.geom.tile(k.cell) == T.SWORD:   # R-C21
            self._result["effect"] = "took_sword"
            self._plan("took_sword", P.PICKUP_SWORD)
            if (yield from self._phase(P.PICKUP_SWORD)):
                self.geom.set_tile(k.cell, T.FLOOR)
                k.sword = True
            return
        if self.geom.tile(k.cell) == T.POTION:      # R-C16 type 1 (R-A03)
            self._result["effect"] = "drank"
            self._plan("drank", P.DRINK)
            if (yield from self._phase(P.DRINK)):
                self.geom.set_tile(k.cell, T.FLOOR)
                if k.hp < k.max_hp:
                    k.hp += 1
                    self._result["hp_change"] = self._result.get("hp_change", 0) + 1
            return
        target = self.ahead()
        if (isinstance(target, tuple) and not self.blocks(target)
                and not self.geom.supported(target)):
            self._result["effect"] = "hanging"
            self._plan("hanging", P.HANG_DOWN, target, posture="hanging", facing=-k.facing)
            # Stands on the ledge throughout: if it falls, he falls (R-C14).
            if (yield from self._phase(P.HANG_DOWN)):
                k.hang_ledge = k.cell
                self._set_pos(target)
                k.facing = -k.facing                 # turns to face the ledge
                k.posture = "hanging"
            return
        self._result["effect"] = "none"
        self._plan("none", P.CROUCH)
        yield from self._frames(P.CROUCH)

    def _wait(self):
        self._result["effect"] = "waited"
        self._plan("waited", P.WAIT)
        yield from self._frames(P.WAIT)

    # --- public --------------------------------------------------------
    def legal_actions(self) -> tuple[str, ...]:
        if self.terminal is not None:
            return ()
        return LEGAL_BY_POSTURE[self.kid.posture]

    def _macro(self, action: str):
        """Start one legal macro: reset the result and return its per-frame
        generator (one `_tick` per yield). `perform` runs it to the end; a duel
        (pop/versus.py) advances it one frame per tick."""
        self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
        self.plan = None
        if action == "WAIT":
            return self._wait()
        if action == "UP":
            return self._up()
        if action == "DOWN":
            return self._down()
        parts = action.split("_")
        d = DIRECTIONS[parts[-1]]
        kind = {"LEFT": "run", "RIGHT": "run", "STEP": "step",
                "JUMP": "jump", "RUN": "run_jump"}[parts[0]]
        return self._directional(d, kind)

    def perform(self, action: str) -> dict:
        """Run one legal macro action. Caller must validate `action` first."""
        assert action in self.legal_actions(), action
        gen = self._macro(action)
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

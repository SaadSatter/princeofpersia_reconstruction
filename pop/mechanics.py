"""Per-frame gadgets: plates, gates, exits, spikes, loose floors."""

from __future__ import annotations

from dataclasses import dataclass

from . import tiles as T
from .physics import Cell, Geometry

GATE_MAX = 188          # gmaxval, BGDATA.S:194 (R-C08)
GATE_RISE = 4           # gateinc up, MOVER.S:89
GATE_LOWER = 1          # gateinc down, MOVER.S:89
GATE_HOLD = 50          # gatetimer = gmaxval + 50, MOVER.S:67
GATE_FAST = 63          # drop-plate slam; closes in 3 frames (design, cf. gatevel MOVER.S:56)
GATE_BARS_BELOW = 136   # pos/4 + 6 < 40 (COLL.S:1374-1381, R-C28; height 40 is R-A04)
EXIT_RISE = 4           # exitinc, MOVER.S:91
PLATE_POP = 5           # pptimer, MOVER.S:59
SPIKE_HOLD = 15         # spiketimer, MOVER.S:62
LOOSE_DELAY = 10        # loosetimer = Ffalling, MOVER.S:69, BGDATA.S:149


@dataclass
class Gate:
    pos: int = 0
    state: str = "idle"   # idle | rising | holding | lowering | fast
    hold: int = 0

    def raise_(self) -> None:
        if self.pos >= GATE_MAX:
            self.state, self.hold = "holding", GATE_HOLD  # restart hold (MOVER.S:469)
        else:
            self.state = "rising"

    def slam(self) -> None:
        if self.pos > 0:
            self.state = "fast"

    def tick(self) -> None:
        if self.state == "rising":
            self.pos = min(GATE_MAX, self.pos + GATE_RISE)
            if self.pos == GATE_MAX:
                self.state, self.hold = "holding", GATE_HOLD
        elif self.state == "holding":
            self.hold -= 1
            if self.hold <= 0:
                self.state = "lowering"
        elif self.state == "lowering":
            self.pos = max(0, self.pos - GATE_LOWER)
            if self.pos == 0:
                self.state = "idle"
        elif self.state == "fast":
            self.pos = max(0, self.pos - GATE_FAST)
            if self.pos == 0:
                self.state = "idle"

    @property
    def bars(self) -> bool:
        return self.pos < GATE_BARS_BELOW


@dataclass
class Exit:
    pos: int = 0
    opening: bool = False

    def tick(self) -> None:
        if self.opening and self.pos < GATE_MAX:
            self.pos = min(GATE_MAX, self.pos + EXIT_RISE)

    @property
    def open(self) -> bool:
        return self.pos >= GATE_MAX


class Mechanics:
    def __init__(self, geom: Geometry, plate_links: dict[Cell, tuple[Cell, ...]],
                 exits_open: bool):
        self.geom = geom
        self.links = dict(plate_links)
        self.gates: dict[Cell, Gate] = {}
        self.exits: dict[Cell, Exit] = {}
        self.plates: dict[Cell, int] = {}      # cell -> frames until it pops up
        self.spikes: dict[Cell, int] = {}      # cell -> frames until retract (0 = retracted)
        self.loose: dict[Cell, int] = {}       # cell -> frames since triggered
        for room, grid in geom.grid.items():
            for r, row in enumerate(grid):
                for c, sym in enumerate(row):
                    cell = (room, r, c)
                    if sym == T.GATE:
                        self.gates[cell] = Gate()
                    elif sym == T.EXIT_LEFT:
                        self.exits[cell] = Exit(pos=GATE_MAX if exits_open else 0,
                                                opening=exits_open)
                    elif sym in T.PLATES:
                        self.plates[cell] = 0
                    elif sym == T.SPIKES:
                        self.spikes[cell] = 0

    # --- queries -------------------------------------------------------
    def exit_for(self, cell: Cell) -> Exit | None:
        sym = self.geom.tile(cell)
        if sym == T.EXIT_LEFT:
            return self.exits.get(cell)
        if sym == T.EXIT_RIGHT:
            room, r, c = cell
            return self.exits.get((room, r, c - 1))
        return None

    def gate_bars(self, cell: Cell) -> bool:
        gate = self.gates.get(cell)
        return gate is not None and gate.bars

    # --- triggers ------------------------------------------------------
    def touch_loose(self, cell: Cell) -> None:
        if self.geom.tile(cell) == T.LOOSE and cell not in self.loose:
            self.loose[cell] = 0

    def _press(self, cell: Cell) -> None:
        self.plates[cell] = PLATE_POP
        kind = self.geom.tile(cell)
        for target in self.links.get(cell, ()):
            if target in self.gates:
                if kind == T.RAISE_PLATE:
                    self.gates[target].raise_()
                else:
                    self.gates[target].slam()
            elif target in self.exits and kind == T.RAISE_PLATE:
                self.exits[target].opening = True  # exits never close (MOVER.S:562-571)

    # --- per frame -----------------------------------------------------
    def tick(self, pressing: Cell | None, near: set[Cell]) -> list[tuple]:
        """Advance one frame. `pressing`: plate under the kid; `near`: cells within
        one block of the kid on his row. Returns loose-floor fall events."""
        if pressing in self.plates:
            self._press(pressing)
        for cell, t in self.plates.items():
            if cell != pressing and t > 0:
                self.plates[cell] = t - 1
        for gate in self.gates.values():
            gate.tick()
        for ex in self.exits.values():
            ex.tick()
        for cell in self.spikes:
            if cell in near:
                self.spikes[cell] = SPIKE_HOLD          # spring / stay sprung (R-D19)
            elif self.spikes[cell] > 0:
                self.spikes[cell] -= 1
        events = []
        for cell in list(self.loose):
            self.loose[cell] += 1
            if self.loose[cell] >= LOOSE_DELAY:
                del self.loose[cell]
                events.append(("loose_fell", cell, self._drop_loose(cell)))
        return events

    def _drop_loose(self, cell: Cell) -> Cell | None:
        """The floor piece falls and lands as rubble on the first support below (R-D14)."""
        self.geom.set_tile(cell, T.SPACE)
        below = self.geom.offset(cell, 1, 0)
        while isinstance(below, tuple):
            if self.geom.tile(below) == T.WALL:
                return None
            if self.geom.supported(below):
                if self.geom.tile(below) in (T.FLOOR, T.SPACE, T.TORCH, T.PILLAR):
                    self.geom.set_tile(below, T.RUBBLE)
                return below
            below = self.geom.offset(below, 1, 0)
        return None

    def snapshot(self) -> dict:
        return {
            "gates": {str(k): (g.pos, g.state, g.hold) for k, g in sorted(self.gates.items())},
            "exits": {str(k): (e.pos, e.opening) for k, e in sorted(self.exits.items())},
            "plates": {str(k): v for k, v in sorted(self.plates.items())},
            "spikes": {str(k): v for k, v in sorted(self.spikes.items())},
            "loose": {str(k): v for k, v in sorted(self.loose.items())},
        }

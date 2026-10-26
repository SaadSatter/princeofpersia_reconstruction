"""Heuristic baseline: a cautious explorer that plans inside the visible room.

What it uses (the same inputs as the model player):
  - the observation dict (current room's tiles and visible state, kid, HUD);
  - the legal-action list;
  - the published movement rules (docs/GAME_SPEC.md §4-5), hand-coded below as
    its own small predictive model. This is the "manual" a human would read.

What it keeps (disclosed in EVALUATION.md): its own memory of rooms it has
seen (by opaque room label), plates it has pressed, and the edges it has left by.

What it never gets: the engine, other rooms' tiles before visiting them,
plate links, pit destinations, timers, situation ids, or solution routes.

Policy per decision:
  1. falling -> WAIT; hanging -> UP (climb back).
  2. Standing on an open exit -> UP.
  3. Pick a goal: open exit in view > (closed exit in view) unpressed raise
     plate in view > exit that is opening > leave the room by the heading edge.
  4. Find the cheapest action sequence to the goal with Dijkstra over
     (row, col, facing, frames-on-loose-floor) using the predictive model;
     never choose a predicted death; avoid falls of 2 rows and sunken plates.
  5. If a barring gate blocks the goal: press a raise plate in this room, or
     wait beside the gate while it opens, or go back to look for a plate.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

COLS, ROWS = 10, 3

# Tile symbols as shown to players (README / prompt legend).
SPACE, FLOOR, WALL, SPIKES, LOOSE, GATE = ".", "_", "#", "^", "L", "G"
RAISE, SUNKEN, EXIT_L, EXIT_R, POTION = "u", "p", "E", "e", "f"
FLOORLESS = {SPACE, WALL}

# Frame costs from the published action table (GAME_SPEC §4).
F_RUN, F_STEP, F_TURN, F_JUMP, F_CLIMB, F_WAIT = 4, 8, 4, 12, 12, 6
LOOSE_FALLS_AFTER = 10          # GAME_SPEC §5: a loose floor falls 10 frames after it is stepped on

DEAD = "dead"
LEAVE = {-1: "leave_left", +1: "leave_right"}

# Cost weights: one unit is one action. Hurting falls and sunken plates are
# avoided unless they are the only way; risky edge jumps are a last resort.
HURT_COST, SUNKEN_COST, BLIND_JUMP_COST = 6, 8, 10


@dataclass(frozen=True)
class Pose:
    row: int
    col: int
    facing: int          # +1 right, -1 left
    loose: int = -1      # frames already spent on a loose floor, -1 if not on one


class RoomView:
    """The baseline's model of the visible room, built from one observation."""

    def __init__(self, obs: dict):
        self.tiles = [list(r) for r in obs["tiles"]]
        st = obs["state"]
        for r, c in st["loose_shaking"]:
            self.tiles[r][c] = SPACE               # about to fall: plan as if gone
        self.barring = {(g["row"], g["col"]) for g in st["gates"] if g["bars"]}
        self.gates = {(g["row"], g["col"]): g for g in st["gates"]}
        self.open_exit_cells = set()
        self.exits = st["exits"]
        for e in st["exits"]:
            if e["open"]:
                self.open_exit_cells |= {(e["row"], e["col"]), (e["row"], e["col"] + 1)}
        self.edges = {-1: obs["edges"]["left"], +1: obs["edges"]["right"]}
        self.hp = obs["kid"]["hp"]

    def tile(self, r: int, c: int) -> str:
        if r < 0:
            return WALL                            # rock / unknown above: treat as solid
        if r >= ROWS:
            return "below"                         # unknown: a pit may be bottomless
        if c < 0 or c >= COLS:
            return "edge" if self.edges[-1 if c < 0 else +1] else WALL
        return self.tiles[r][c]

    def blocks(self, r: int, c: int) -> bool:
        return self.tile(r, c) == WALL or (r, c) in self.barring

    def supported(self, r: int, c: int) -> bool:
        t = self.tile(r, c)
        if t in ("edge", "below", WALL):
            return False
        return t not in FLOORLESS or self.tile(r + 1, c) == WALL

    # --- predictive model: (pose, action) -> (pose | outcome, cost, frames) ---
    def predict(self, p: Pose, action: str):
        """Returns (result, extra_cost). result is a Pose, DEAD, 'win', a
        leave_* outcome, or None when the action achieves nothing."""
        if action == "UP":
            if (p.row, p.col) in self.open_exit_cells:
                return "win", 0
            if (self.tile(p.row - 1, p.col) == SPACE and not self.blocks(p.row - 1, p.col + p.facing)
                    and self.supported(p.row - 1, p.col + p.facing)):
                return self._after(p, F_CLIMB, lambda: self._enter(p.row - 1, p.col + p.facing,
                                                                     p.facing, "climb"))
            return None, 0
        d = -1 if action.endswith("LEFT") else +1
        if p.facing != d:                           # reverse = turn only
            return self._after(p, F_TURN, lambda: (Pose(p.row, p.col, d, p.loose), 0), stays=True)
        kind = action.rsplit("_", 1)[0]
        if kind in ("LEFT", "RIGHT"):
            return self._after(p, F_RUN, lambda: self._move(p, "run"))
        if kind == "STEP":
            return self._after(p, F_STEP, lambda: self._move(p, "step"))
        if kind == "JUMP":
            return self._after(p, F_JUMP, lambda: self._jump(p, p.row, p.col, 3))
        if kind == "RUN_JUMP":
            r, c = p.row, p.col + d
            if self.tile(r, c) == "edge" or self.blocks(r, c) or not self.supported(r, c):
                return self._after(p, F_RUN, lambda: self._move(p, "run"))
            if self.tile(r, c) == SPIKES:
                return DEAD, 0                      # the run-up lands on spikes
            return self._after(p, F_RUN, lambda: self._jump(p, r, c, 4))
        return None, 0

    def _after(self, p: Pose, frames: int, outcome, stays: bool = False):
        """Apply the loose-floor rule: standing on a loose floor too long drops you."""
        if p.loose >= 0 and p.loose + frames >= LOOSE_FALLS_AFTER:
            return self._fall(p.row, p.col, p.facing, from_cell_gone=True)
        result, cost = outcome()
        if stays and isinstance(result, Pose) and p.loose >= 0:
            result = Pose(result.row, result.col, result.facing, p.loose + frames)
        return result, cost

    def _move(self, p: Pose, how: str):
        r, c = p.row, p.col + p.facing
        t = self.tile(r, c)
        if t == "edge":
            return LEAVE[p.facing], 0
        if self.blocks(r, c):
            return None, 0
        if how == "step" and not self.supported(r, c):
            return None, 0                          # careful steps refuse edges
        return self._enter(r, c, p.facing, how)

    def _jump(self, p: Pose, r: int, c0: int, span: int):
        target = None
        for i in range(1, span + 1):
            c = c0 + p.facing * i
            if self.tile(r, c) == "edge":
                return LEAVE[p.facing], BLIND_JUMP_COST   # lands somewhere unseen
            if self.blocks(r, c):
                break
            target = c
        if target is None:
            return None, 0
        return self._enter(r, target, p.facing, "jump")

    def _enter(self, r: int, c: int, facing: int, how: str):
        t = self.tile(r, c)
        if t == SPIKES and how in ("run", "jump"):
            return DEAD, 0
        if not self.supported(r, c):
            return self._fall(r, c, facing)
        cost = SUNKEN_COST if t == SUNKEN else 0
        return Pose(r, c, facing, 0 if t == LOOSE else -1), cost

    def _fall(self, r: int, c: int, facing: int, from_cell_gone: bool = False):
        rows = 0
        while True:
            r += 1
            rows += 1
            t = self.tile(r, c)
            if t == "below":
                return DEAD, 0                      # unseen pit: assume bottomless
            if self.supported(r, c):
                break
        if self.tile(r, c) == SPIKES or rows >= 3:
            return DEAD, 0
        cost = 0
        if rows == 2:
            if self.hp <= 1:
                return DEAD, 0
            cost = HURT_COST
        cost += SUNKEN_COST if self.tile(r, c) == SUNKEN else 0
        return Pose(r, c, facing, 0 if self.tile(r, c) == LOOSE else -1), cost


PLAN_ACTIONS = ("LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT", "JUMP_LEFT", "JUMP_RIGHT",
                "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT", "UP")


def plan(view: RoomView, start: Pose, goal) -> list[str] | None:
    """Cheapest action list from start to a goal. `goal(result)` -> bool, where
    result is a Pose or an outcome string. Cost = actions + penalties."""
    frontier = [(0, 0, start, [])]
    best: dict[Pose, int] = {start: 0}
    tie = 0
    while frontier:
        cost, _, pose, path = heapq.heappop(frontier)
        if goal(pose):
            return path
        if len(path) >= 25:
            continue
        for action in PLAN_ACTIONS:
            result, extra = view.predict(pose, action)
            if result is None or result == DEAD:
                continue
            new_cost = cost + 1 + extra
            if not isinstance(result, Pose):
                if goal(result):
                    tie += 1
                    heapq.heappush(frontier, (new_cost, tie, result, path + [action]))
                continue
            if new_cost < best.get(result, 1 << 30):
                best[result] = new_cost
                tie += 1
                heapq.heappush(frontier, (new_cost, tie, result, path + [action]))
    return None


@dataclass
class RoomMemory:
    entered_from: int | None = None                 # -1 left edge, +1 right edge
    left_by: set = field(default_factory=set)
    pressed: set = field(default_factory=set)       # raise plates we stood on
    raise_plates: set = field(default_factory=set)


class BaselinePlayer:
    """Cautious explorer with a visible-room planner. Deterministic."""

    name = "baseline-explorer"
    source = "baseline"
    uses_model = False

    def __init__(self):
        self.rooms: dict[str, RoomMemory] = {}
        self.heading: int | None = None
        self.seek_plate = False                      # going back for a plate
        self.last_room: str | None = None
        self.last_dir = 0
        self.last_gate_pct: dict = {}
        self.visits: dict = {}
        self.exit_waits = 0                          # waits at a door showing 0 %

    # ------------------------------------------------------------------
    def decide(self, observation: dict, legal_actions: list[str]) -> str:
        action = self._decide(observation, legal_actions)
        if action not in legal_actions:
            action = "WAIT" if "WAIT" in legal_actions else legal_actions[0]
        if action.endswith("LEFT"):
            self.last_dir = -1
        elif action.endswith("RIGHT"):
            self.last_dir = +1
        return action

    def _decide(self, obs: dict, legal: list[str]) -> str:
        kid = obs["kid"]
        if kid["posture"] == "falling":
            return "WAIT"
        if kid["posture"] == "hanging":
            return "UP"
        label = obs["room"]
        mem = self._enter_room(label, obs)
        view = RoomView(obs)
        here = (kid["row"], kid["col"])
        facing = +1 if kid["facing"] == "right" else -1
        start = Pose(kid["row"], kid["col"], facing,
                     0 if view.tile(*here) == LOOSE else -1)
        key = (label, here, facing)
        self.visits[key] = self.visits.get(key, 0) + 1

        if view.tile(*here) == RAISE:
            mem.pressed.add(here)
            if self.seek_plate:
                self.seek_plate = False
                self.heading = -self.heading if self.heading else None
        if here in view.open_exit_cells:
            return "UP"

        # Goals in priority order.
        if view.open_exit_cells:
            path = plan(view, start, lambda r: r == "win")
            if path:
                return path[0]
        closed = [e for e in view.exits if not e["open"]]
        exit_cells = {(e["row"], e["col"] + i) for e in closed for i in (0, 1)}
        if closed and all(e["open_pct"] == 0 for e in closed):
            step = self._press_plate(view, start, mem)
            if step:
                return step
        # Go to a closed exit once it is rising, or after pressing every plate
        # in view (the plate may open it); give up if it stays shut.
        rising = any(e["open_pct"] > 0 for e in closed)
        if closed and (rising or self.exit_waits < 3):
            if here in exit_cells:
                self.exit_waits = 0 if rising else self.exit_waits + 1
                return "WAIT"
            path = plan(view, start, lambda r: isinstance(r, Pose) and (r.row, r.col) in exit_cells)
            if path:
                return path[0]

        if self.seek_plate:
            step = self._press_plate(view, start, mem)
            if step:
                return step
        return self._explore(view, start, mem, label, obs)

    # ------------------------------------------------------------------
    def _enter_room(self, label: str, obs: dict) -> RoomMemory:
        new = label not in self.rooms
        mem = self.rooms.setdefault(label, RoomMemory())
        if label != self.last_room:
            if self.last_room is not None:
                self.rooms[self.last_room].left_by.add(self.last_dir)
                if new:
                    mem.entered_from = -self.last_dir
            self.last_room = label
            self.last_gate_pct = {}
        for r, row in enumerate(obs["tiles"]):
            for c, sym in enumerate(row):
                if sym == RAISE:
                    mem.raise_plates.add((r, c))
        if self.heading is None:
            e = obs["edges"]
            if e["left"] != e["right"]:
                self.heading = -1 if e["left"] else +1
            else:
                self.heading = +1 if obs["kid"]["facing"] == "right" else -1
        return mem

    def _press_plate(self, view: RoomView, start: Pose, mem: RoomMemory) -> str | None:
        targets = mem.raise_plates - mem.pressed
        if not targets:
            return None
        path = plan(view, start, lambda r: isinstance(r, Pose) and (r.row, r.col) in targets)
        return path[0] if path else None

    def _explore(self, view: RoomView, start: Pose, mem: RoomMemory, label: str, obs: dict) -> str:
        sides = [s for s in (self.heading, -self.heading) if view.edges[s]]
        for side in sides:
            path = plan(view, start, lambda r, s=side: r == LEAVE[s])
            if path:
                if self.visits[(label, (start.row, start.col), start.facing)] > 6:
                    self.heading = -self.heading      # stuck in a loop: try the other way
                if side != self.heading:
                    self.heading = side               # dead end ahead: turn around
                return path[0]
            # A barring gate may be in the way.
            if view.barring:
                step = self._press_plate(view, start, mem)
                if step:
                    return step
                gate_now = {k: g["open_pct"] for k, g in view.gates.items()}
                opening = any(gate_now[k] > self.last_gate_pct.get(k, -1) for k in gate_now)
                self.last_gate_pct = gate_now
                if opening:
                    return self._approach_gate(view, start) or "WAIT"
                if not self.seek_plate:
                    # A closed gate and no plate here: go back and press one.
                    self.seek_plate = True
                    self.heading = -self.heading
                    return self._explore(view, start, mem, label, obs)
            if side == self.heading and len(sides) == 1:
                break
        return "WAIT"

    def _approach_gate(self, view: RoomView, start: Pose) -> str | None:
        gates = list(view.barring)

        def near(r):
            return isinstance(r, Pose) and any(r.row == gr and abs(r.col - gc) == 1
                                               for gr, gc in gates)
        if near(start):
            return "WAIT"
        path = plan(view, start, near)
        return path[0] if path else None

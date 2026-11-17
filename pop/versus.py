"""Two rivals in one game on real-time ticks (docs/final/VERSUS_SPEC.md, Section 2).

Saad's decisions, 2026-11-17: real-time ticks at 12 frames per second, both
rivals' moves overlapping frame by frame (CQ-1 timing); the spec was approved
as written the same day.

One `Duel` holds one geometry, one `Mechanics` and two `Rival`s (seats A and B).
Each rival runs the inherited movement macros (pop/engine.py), which are
already per-frame generators. `tick()` advances the shared world one frame
(gates, plates, loose floors), then each rival's move one frame, A then B.
Contacts that need symmetry are resolved on the frame's end state.

A seat's input starts a move only when its rival is free (no move in
progress); a seat holds one pending input and a newer one replaces it.

Timing detail: a macro places the kid at its destination in the code after
its last frame, so a move's arrival is applied when the duel next resumes it,
at the start of the following frame, just before that frame's next move
starts. Moves still chain without a gap (a run is 4 frames per cell) and the
lag is the same for both rivals. Changing it would change how the inherited
macros count frames, which single-player traces pin down.

Stage 1 (this file): movement only. Swordplay, guards and disguise follow
the spec's order of work (R-V01 to R-V21).
"""

from __future__ import annotations

import copy
import random

from . import observation
from . import physics as P
from .engine import ACTIONS, LEGAL_BY_POSTURE, Game, Kid
from .mechanics import Mechanics
from .physics import Cell, Geometry
from .situations import Situation

SEATS = ("A", "B")
TICKS_PER_SECOND = 12                 # R-D26 display rate; VERSUS_SPEC 2.1
TASK = ("Duel: bring the other rival's hearts to 0. Both rivals act at the same "
        "time; the duel ends on a death, a double death, or the time limit.")
OBSERVATION_KEYS = observation.OBSERVATION_KEYS | {"me", "figures", "swords", "suspicion"}
FIGURE_KEYS = {"kind", "row", "col", "facing", "posture", "stance", "armed", "motion"}
ME_EXTRA_KEYS = {"stance", "armed", "disguised", "knocked_down_frames", "motion"}

INVALID_SEAT = "unknown seat"
INVALID_NOT_TEXT = "action must be a string"
INVALID_UNKNOWN = "unknown action"
INVALID_NOT_NOW = "action not legal in the current posture"
DUEL_OVER = "duel is over"


class Rival(Game):
    """One rival's body in a duel: the inherited movement macros, acting on the
    duel's shared world. Never constructed outside a Duel."""

    def __init__(self, duel: "Duel", seat: str, start: tuple[int, int, int, int]):
        # Deliberately not Game.__init__: the world belongs to the duel.
        self.duel = duel
        self.seat = seat
        self.situation = duel.situation
        self.seed = duel.seed
        self.rng = duel.rng
        self.geom = duel.geom
        self.mech = duel.mech
        room, row, col, facing = start
        self.kid = Kid(room, row, col, facing)
        self.frames = 0
        self.terminal: str | None = None
        self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
        self._airborne = False
        self.plan: dict | None = None
        self.intro = None
        # Swordplay state (VERSUS_SPEC 3); Stage 1 keeps every rival sheathed.
        self.stance: str | None = None
        self.armed = False
        self.disguised = False
        self.knocked_down = 0

    def _tick(self) -> None:
        """This rival's part of the frame the duel has already advanced."""
        self.frames = self.duel.frames
        self._react(self.duel.events)

    def blocks(self, where: Cell | str) -> bool:
        """Walls and gates, as before, and the other rival standing there:
        rivals cannot pass through each other (VERSUS_SPEC 3)."""
        if super().blocks(where):
            return True
        return isinstance(where, tuple) and self.duel.standing_at(where, other_than=self.seat)

    @property
    def alive(self) -> bool:
        return self.kid.posture not in ("dead", "won")


class Duel:
    def __init__(self, situation: Situation, starts: dict[str, tuple[int, int, int, int]],
                 seed: int = 0, time_limit_frames: int = P.GAME_FRAMES):
        """time_limit_frames: OQ-3 (duel length) is open; the default is the
        inherited 60-minute clock (R-C24) until Saad sets it."""
        self.situation = situation
        self.seed = seed
        self.rng = random.Random(seed)
        self.geom = Geometry(situation.rooms, situation.links)
        self.mech = Mechanics(self.geom, situation.plate_links, situation.exits_open,
                              situation.gates_open)
        self.time_limit = time_limit_frames
        self.frames = 0
        self.events: list = []
        self.rivals = {seat: Rival(self, seat, starts[seat]) for seat in SEATS}
        self._moves: dict[str, object] = {seat: None for seat in SEATS}
        self._move_frame: dict[str, int] = {seat: 0 for seat in SEATS}
        self.pending: dict[str, str | None] = {seat: None for seat in SEATS}
        self.last_result: dict[str, dict | None] = {seat: None for seat in SEATS}
        self.terminal: str | None = None

    # --- queries ------------------------------------------------------
    def standing_at(self, cell: Cell, other_than: str) -> bool:
        return any(r.kid.cell == cell and r.kid.posture == "standing"
                   for seat, r in self.rivals.items() if seat != other_than)

    def busy(self, seat: str) -> bool:
        return self._moves[seat] is not None

    def motion(self, seat: str) -> dict | None:
        """The move in progress: effect, frames done, length, planned end."""
        r = self.rivals[seat]
        if not self.busy(seat) or r.plan is None:
            return None
        return {**r.plan, "frame": self._move_frame[seat]}

    def legal_actions(self, seat: str) -> tuple[str, ...]:
        if self.terminal is not None:
            return ()
        return LEGAL_BY_POSTURE[self.rivals[seat].kid.posture]

    # --- inputs and frames -------------------------------------------
    def submit(self, seat: str, action: str) -> None:
        """Queue a validated input; a newer input replaces an older one."""
        self.pending[seat] = action

    def tick(self) -> None:
        """One frame: the world once, then each rival's move one frame."""
        if self.terminal is not None:
            return
        self.frames += 1
        alive = [r for r in self.rivals.values() if r.alive]
        pressing = sorted({c for r in alive if (c := r._pressing()) is not None})
        near: set[Cell] = set()
        for r in alive:
            near |= r._near_cells()
        first = pressing[0] if pressing else None
        self.events = self.mech.tick(first, near, frozenset(pressing[1:]))
        before = {seat: r.kid.cell for seat, r in self.rivals.items()}
        for seat in SEATS:
            self._advance(seat)
        self._separate(before)
        self._check_end()

    def _advance(self, seat: str) -> None:
        r = self.rivals[seat]
        if not r.alive:
            return
        gen = self._moves[seat]
        if gen is not None:
            try:
                next(gen)
                self._move_frame[seat] += 1
                return
            except StopIteration:
                self._finish(seat)
        action = self.pending[seat]
        self.pending[seat] = None
        if action is not None and action in LEGAL_BY_POSTURE[r.kid.posture] \
                and r.terminal is None:
            gen = r._macro(action)
            self._moves[seat], self._move_frame[seat] = gen, 0
            try:
                next(gen)
                self._move_frame[seat] = 1
                return
            except StopIteration:            # a move with no frames (dropping from a hang)
                self._finish(seat)
        r._tick()                            # free this frame: the world still acts on it

    def _finish(self, seat: str) -> None:
        r = self.rivals[seat]
        r._result["frames"] = self._move_frame[seat]
        self.last_result[seat] = dict(r._result)
        self._moves[seat] = None
        self._move_frame[seat] = 0

    def _separate(self, before: dict[str, Cell]) -> None:
        """Two rivals that ended a frame standing in one cell both moved into it at
        once (a block is checked when a move starts). Whoever moved this frame
        goes back where it was, so neither passes through the other."""
        a, b = self.rivals["A"].kid, self.rivals["B"].kid
        if a.cell == b.cell and a.posture == b.posture == "standing":
            for seat in SEATS:
                k = self.rivals[seat].kid
                if k.cell != before[seat]:
                    k.room, k.row, k.col = before[seat]

    def _check_end(self) -> None:
        dead = [seat for seat, r in self.rivals.items() if r.kid.posture == "dead"]
        if len(dead) == 2:
            self.terminal = "draw:both_died"
        elif len(dead) == 1:
            self.terminal = "won:" + ("B" if dead[0] == "A" else "A")
        elif self.frames >= self.time_limit:
            self.terminal = "draw:time_up"

    def snapshot(self) -> dict:
        """The complete authoritative state (tests and traces; never sent to a seat)."""
        return copy.deepcopy({
            "frames": self.frames,
            "terminal": self.terminal,
            "rivals": {seat: {"kid": vars(r.kid), "terminal": r.terminal, "plan": r.plan,
                              "stance": r.stance, "armed": r.armed,
                              "busy": self.busy(seat), "move_frame": self._move_frame[seat]}
                       for seat, r in self.rivals.items()},
            "pending": dict(self.pending),
            "mech": self.mech.snapshot(),
            "tiles": {room: self.geom.rows(room) for room in sorted(self.geom.grid)},
        })


# --- what one seat sees (VERSUS_SPEC 6) ----------------------------------
def _motion_view(duel: Duel, seat: str, room: int) -> dict | None:
    """A move as it looks on screen: its effect, progress and, if it ends in this
    room, where. An end in another room is not shown (up/down links stay hidden)."""
    m = duel.motion(seat)
    if m is None:
        return None
    to = m["to"]
    return {"effect": m["effect"], "frame": m["frame"], "frames": m["frames"],
            "to": [to[1], to[2]] if to[0] == room else None,
            "to_posture": m["posture"],
            "to_facing": "right" if m["facing"] > 0 else "left"}


def observe(duel: Duel, seat: str) -> dict:
    me = duel.rivals[seat]
    room = me.kid.room
    obs = observation.build(me, None, duel.last_result[seat])
    obs["task"] = TASK
    obs["me"] = {**obs["kid"], "stance": me.stance, "armed": me.armed,
                 "disguised": me.disguised, "knocked_down_frames": me.knocked_down,
                 "motion": _motion_view(duel, seat, room)}
    figures = []
    for other, r in duel.rivals.items():
        if other == seat or r.kid.room != room:
            continue
        figures.append({"kind": "rival", "row": r.kid.row, "col": r.kid.col,
                        "facing": "right" if r.kid.facing > 0 else "left",
                        "posture": r.kid.posture, "stance": r.stance, "armed": r.armed,
                        "motion": _motion_view(duel, other, room)})
    obs["figures"] = sorted(figures, key=lambda f: (f["row"], f["col"], f["kind"]))
    obs["swords"] = []
    obs["suspicion"] = []
    return obs


class VersusEpisode:
    """The five operations per seat (VERSUS_SPEC 2.2), plus `tick` for the runner
    and server only. Seats never receive the Duel."""

    def __init__(self, situation: Situation, starts: dict[str, tuple[int, int, int, int]],
                 seed: int = 0, time_limit_frames: int = P.GAME_FRAMES):
        self._situation = situation
        self._starts = dict(starts)
        self._time_limit = time_limit_frames
        self.reset(seed)

    # 1
    def reset(self, seed: int) -> None:
        self.seed = seed
        self._duel = Duel(self._situation, self._starts, seed, self._time_limit)
        self.inputs = {seat: 0 for seat in SEATS}
        self.invalid = {seat: 0 for seat in SEATS}
        self.log: list[tuple[int, str, str]] = []      # (frame, seat, action): the trace

    # 2
    def observe(self, seat: str) -> dict:
        _check_seat(seat)
        return observe(self._duel, seat)

    # 3
    def legal_actions(self, seat: str) -> list[str]:
        _check_seat(seat)
        return list(self._duel.legal_actions(seat))

    # 4
    def step(self, seat: str, action: object) -> dict:
        _check_seat(seat)
        if self._duel.terminal is not None:
            return self._refuse(seat, DUEL_OVER, count=False)
        if not isinstance(action, str):
            return self._refuse(seat, INVALID_NOT_TEXT)
        name = action.strip().upper()
        if name not in ACTIONS:
            return self._refuse(seat, INVALID_UNKNOWN)
        if name not in self._duel.legal_actions(seat):
            return self._refuse(seat, INVALID_NOT_NOW)
        self.inputs[seat] += 1
        self._duel.submit(seat, name)
        self.log.append((self._duel.frames, seat, name))
        return {"accepted": True, "action": name, "queued_at_frame": self._duel.frames}

    # 5
    def outcome(self) -> dict:
        t = self._duel.terminal
        return {"status": "ongoing" if t is None else "terminal", "reason": t,
                "frames": self._duel.frames, "inputs": dict(self.inputs),
                "invalid_inputs": dict(self.invalid)}

    # runner and server only
    def tick(self) -> None:
        self._duel.tick()

    def _refuse(self, seat: str, error: str, count: bool = True) -> dict:
        if count:
            self.invalid[seat] += 1
        return {"accepted": False, "error": error}


def _check_seat(seat: str) -> None:
    if seat not in SEATS:
        raise ValueError(INVALID_SEAT)


def arena_episode(seed: int = 0, time_limit_frames: int = P.GAME_FRAMES) -> VersusEpisode:
    """The six-room arena (pop/arena.py) with both rivals at their starts."""
    from . import arena
    return VersusEpisode(arena.situation("A"), arena.STARTS, seed, time_limit_frames)

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

Stage 2 adds swordplay (R-V01 to R-V12): combat moves are per-frame
generators that set their phase (windup, active, recovery) each frame; the
duel resolves contacts (block, hit, disarm, kick, sweep) once per frame after
both rivals have moved, on that frame's end state, so a simultaneous exchange
does not depend on seat order. Stance changes run as a 2-frame timer beside
any move (VERSUS_SPEC 2.1, R-V03). Guards and disguise follow (R-V13 to R-V21).
"""

from __future__ import annotations

import copy
import json
import random

from . import observation
from . import physics as P
from . import tiles as T
from .engine import ACTIONS, LEGAL_BY_POSTURE, Game, Kid
from .guards import (ALERT_DRAW_FRAMES, CHASE_FRAMES, PATROL_FRAMES, SIGHT_CELLS, Guard,
                     blocked_between)
from .mechanics import Mechanics
from .physics import Cell, Geometry
from .situations import Situation

SEATS = ("A", "B")
TICKS_PER_SECOND = 12                 # R-D26 display rate; VERSUS_SPEC 2.1
DUEL_FRAMES = 5 * 60 * TICKS_PER_SECOND   # OQ-3, Saad 2026-11-23: "Make the duel time limit 5min"
TASK = ("Duel: bring the other rival's hearts to 0. Both rivals act at the same "
        "time; the duel ends on a death, a double death, or the time limit.")
OBSERVATION_KEYS = observation.OBSERVATION_KEYS | {"me", "figures", "swords", "suspicion", "my_traps"}
FIGURE_KEYS = {"kind", "row", "col", "facing", "posture", "stance", "armed", "motion"}
ME_EXTRA_KEYS = {"stance", "armed", "disguised", "knocked_down_frames", "motion", "traps_left"}

INVALID_SEAT = "unknown seat"
INVALID_NOT_TEXT = "action must be a string"
INVALID_UNKNOWN = "unknown action"
INVALID_NOT_NOW = "action not legal in the current posture"
DUEL_OVER = "duel is over"

# Swordplay numbers (VERSUS_SPEC 3, approved 2026-11-17). Frames at 12 per second.
STANCES = ("low", "mid", "high")
DRAW_FRAMES = 3                       # R-V02
SHEATHE_FRAMES = 3                    # implementation choice (= draw); listed for Saad in the PR
STANCE_FRAMES = 2                     # R-V03
LUNGE_WINDUP, LUNGE_ACTIVE, LUNGE_RECOVERY = 2, 2, 4          # R-V04
INVULNERABLE_FRAMES = 12              # R-V06
THROW_SPEED = 2                       # R-V08, cells per frame
THROW_FRAMES, THROW_RELEASE = 8, 3    # implementation choice: the blade leaves on frame 3
THROW_RECOVERY = THROW_FRAMES - THROW_RELEASE
PICKUP_FRAMES = 6                     # R-V09
KICK_FRAMES = 4                       # implementation choice: active on its last 2 frames (R-V10)
SWEEP_FRAMES = 6                      # R-V11; active on frames 3-4 (implementation choice)
KNOCKDOWN_FRAMES = 10                 # R-V10, R-V11
# Disguise and suspicion (VERSUS_SPEC 5, approved 2026-11-17).
TAKE_FRAMES = 12                      # R-V17
SUSPICION_MAX = 100                   # R-V19
SUSPICION_RUN, SUSPICION_LEAP, SUSPICION_LINGER = 4, 6, 1     # per frame, R-V19
LINGER_AFTER = 24                     # "over 2 s" within 1 cell, R-V19
SUSPICION_FALL = 2                    # per frame, R-V20
# Rigged traps (docs/final/TRAPS_SPEC.md, Saad's decision #22, 2026-11-23). The seat-facing
# `RIG` action is the engine half of the `RIG_TRAP` macro (CQ-1).
RIG_FRAMES = 12                       # R-V27: kneel as long as TAKE
TRAPS_PER_RIVAL = 4                   # R-V31: shared across trap types
SUSPICION_RIG = 3                     # R-V33: per frame of the kneel, in a guard's sight
RIG_KIND = "loose"                    # the only type built so far (gate plate is later)
LEAPS = ("jumped", "flipped", "climbed", "hanging", "dropped")  # jumping or climbing
JUMPS = ("jumped", "flipped")          # a flip is a jump over someone (R-V22)
VERSUS_ACTIONS = ("DRAW", "SHEATHE", "STANCE_UP", "STANCE_DOWN", "LUNGE", "THROW",
                  "KICK", "SWEEP", "TAKE", "RIG")
BREAKS_DISGUISE = ("DRAW", "LUNGE", "THROW", "KICK", "SWEEP")  # R-V21
DIRECTIONAL = {d: (d, "STEP_" + d, "JUMP_" + d, "RUN_JUMP_" + d) for d in ("LEFT", "RIGHT")}
HOPS = ("none", "bumped_ceiling")      # UP on open floor: a hop straight up (pop/engine.py _up)
HOP_FLIPS = {"_HOP_FLIP_LEFT": -1, "_HOP_FLIP_RIGHT": +1}       # R-V22, started by the duel
GRACE_TICKS = 2                       # R-V35, Saad #54 (2026-11-24): direction + jump window
# R-V18 (T01, AUDIT-B F1): every motion a guard can show (pop/guards.py Guard.motion),
# as (effect, frames). A disguised rival's move outside this set is shown to the
# other seat only if it raises suspicion by rule (Duel.suspicious_rise); any
# other move (a wait, a bump, a refused careful step, a crouch) is shown as
# standing still, the way a paused guard is observed.
GUARD_MOTIONS = frozenset({
    ("moved", PATROL_FRAMES), ("moved", CHASE_FRAMES), ("turned", P.TURN),
    ("drew", ALERT_DRAW_FRAMES), ("sheathed", ALERT_DRAW_FRAMES),
    ("lunge", LUNGE_WINDUP + LUNGE_ACTIVE + LUNGE_RECOVERY)})


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
        self.plan_from = 0                 # move frame the current plan started at
        self._hop_flip = False             # a hop being turned into a flip (R-V22)
        self.intro = None
        # Swordplay state (VERSUS_SPEC 3).
        self.sword = "sheathed"            # "drawn", "sheathed" or "none" (disarmed / thrown)
        self.stance: str | None = None     # set while drawn
        self.stance_change: tuple[str, int] | None = None   # (target, frames left), R-V03
        self.stance_landed = -1            # duel frame the last stance change took effect
        self.attack: dict | None = None    # the attack in progress and its phase this frame
        self.invulnerable = 0              # R-V06
        self.knocked_down = 0              # R-V12
        self.disguised = False             # R-V17 to R-V21
        self.still = 0                     # frames standing still (R-V19 lingering)
        self._trap_fall = False            # falling with a rigged floor (R-V28)

    def _tick(self) -> None:
        """This rival's part of the frame the duel has already advanced."""
        self.frames = self.duel.frames
        self._react(self.duel.events)

    def blocks(self, where: Cell | str) -> bool:
        """Walls and gates, as before; in this rival's own room, also the other
        rival standing there, a standing guard, and the other rival's landing
        cell: rivals cannot pass through either (VERSUS_SPEC 3); a downed guard
        can be crossed. R-V23 (Saad, 2026-11-23): a body or landing cell in
        another room is out of sight and never stops a move; a mover that
        arrives on someone settles beside them (Duel._settle_arrivals)."""
        if super().blocks(where):
            return True
        if not isinstance(where, tuple) or where[0] != self.kid.room:
            return False
        d = self.duel
        return (d.standing_at(where, other_than=self.seat) or d.guard_at(where) is not None
                or d.claimed(where, other_than=self.seat))

    def _can_vault(self, where: Cell | str) -> bool:
        """R-V22 (Saad, 2026-11-17): a jump flies over the other rival or a standing
        guard, never over a wall or closed gate. Only a body in this rival's own
        room: one in the next room is out of sight, and flipping over it would
        reveal it, so it still stops the jump as before."""
        return (isinstance(where, tuple) and where[0] == self.kid.room
                and not Game.blocks(self, where))

    def _jump_look(self, running: bool, vaulted: bool) -> str:
        """R-V22 (amended by Saad #53, 2026-11-24): every directional jump is a
        flip, standing or running, over someone or nobody. Where it lands is
        unchanged. (Before: only a jump over someone, a running jump or a hop
        turned into a jump flipped.)"""
        return "flipped"

    def _directional(self, d: int, kind: str):
        """A jump pointed the other way faces that way and jumps, with no separate
        4-frame turn first (Saad #53/#54: a direction and a jump are one flip in
        that direction). Runs and steps still turn first (R-D20)."""
        if kind == "jump":
            self.kid.facing = d
        yield from super()._directional(d, kind)

    def _flip_from_hop(self, d: int):
        """R-V22 (Saad, 2026-11-17): a direction pointed while hopping straight up
        turns the hop into a standing jump that way, always a flip. The rival
        faces the pointed way first (no separate turn)."""
        self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
        self.plan = None
        self.kid.facing = d
        self._hop_flip = True
        try:
            yield from self._jump(running=False)
        finally:
            self._hop_flip = False

    def _plan(self, *args, **kwargs) -> None:
        """Also note the move frame the plan starts at: a running jump plans its
        flight after the run-up, and the flight's motion counts from take-off."""
        super()._plan(*args, **kwargs)
        self.plan_from = self.duel._move_frame[self.seat]

    @property
    def alive(self) -> bool:
        return self.kid.posture not in ("dead", "won")

    @property
    def armed(self) -> bool:
        return self.sword == "drawn"

    def _hurt(self, amount: int, reason: str) -> None:
        super()._hurt(amount, reason)
        self.disguised = False                              # R-V21: losing a heart

    def _react(self, events: list) -> None:
        """Note a fall caused by a sprung rig before the inherited reaction starts it."""
        k = self.kid
        for _, cell, _ in events:
            if cell in self.duel.sprung and (
                    (k.posture == "standing" and k.cell == cell and not self._airborne)
                    or (k.posture == "hanging" and k.hang_ledge == cell)):
                self._trap_fall = True
        super()._react(events)

    def _land(self) -> None:
        """R-V28: a sprung trap costs 1 heart in all. A fall of 2 rows already costs
        one (R-V01), so only a shorter fall adds it; a deadly fall is left alone."""
        hp = self.kid.hp
        super()._land()
        if self._trap_fall:
            self._trap_fall = False
            if self.kid.posture == "standing" and self.kid.hp == hp:
                self._hurt(1, "died:trap")
                if self.alive:
                    self._result["effect"] = "hurt"

    def rig_target(self) -> Cell | None:
        """R-V27: the cell a RIG would rig, or None if RIG is not legal now. Reads
        only this seat's own state and what it sees in its own room: never the
        other seat's rigs (a refusal there would reveal them, TRAPS_SPEC 2), and
        never a link to a room below, which no observation shows (so the floor
        the tile falls to must lie in this room)."""
        d, k = self.duel, self.kid
        cell = self.ahead()
        if (not isinstance(cell, tuple) or cell[0] != k.room or k.posture != "standing"
                or d.traps_left[self.seat] <= 0 or self.seat in d.rigs.get(cell, {})
                or self.geom.tile(cell) != T.FLOOR or not self.geom.supported(cell)
                or d.body_in(cell) or d.claimed(cell, other_than=self.seat)
                or not d.floor_below_in_room(cell)):
            return None
        return cell

    def downed_guard_ahead(self):
        """A downed guard in this rival's own cell (standing over the body, facing
        either way) or in the cell ahead. The own cell was added after Saad's
        playtest of 2026-11-17: a downed guard can be walked onto, and T over the
        body did nothing."""
        here, ahead = self.kid.cell, self.ahead()
        for cell in (here, ahead):
            for g in self.duel.guards.values():
                if g.downed and g.cell == cell:
                    return g
        return None

    def uniform_ahead(self):
        """The downed guard in reach if its uniform is still there to take (R-V17)."""
        g = self.downed_guard_ahead()
        return g if g is not None and g.uniform else None
    # --- swordplay macros (per-frame generators, like the inherited ones) ---
    def _versus_macro(self, action: str):
        if action in HOP_FLIPS:                             # internal: never a seat's input
            return self._flip_from_hop(HOP_FLIPS[action])
        if action in VERSUS_ACTIONS or (action == "DOWN" and self._kneel_target() is not None):
            self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
            self.plan = None
            if action in BREAKS_DISGUISE:
                self.disguised = False                      # R-V21: drawing or any attack
            return {"DRAW": self._draw, "SHEATHE": self._sheathe, "LUNGE": self._lunge,
                    "THROW": self._throw, "KICK": self._kick, "SWEEP": self._sweep,
                    "DOWN": self._kneel, "TAKE": self._take, "RIG": self._rig}[action]()
        return self._macro(action)

    def _kneel_target(self) -> str | None:
        """What DOWN does here beyond the inherited crouch (R-V09, R-V17, Saad #94):
        pick up a dropped sword first, otherwise take a downed guard's uniform."""
        if self.sword == "none" and self.kid.cell in self.duel.swords:
            return "sword"
        if not self.disguised and self.uniform_ahead() is not None:
            return "uniform"
        return None

    def _kneel(self):
        return self._pickup() if self._kneel_target() == "sword" else self._take()

    def _draw(self):
        self._result["effect"] = "drew"
        self._plan("drew", DRAW_FRAMES)
        yield from self._frames(DRAW_FRAMES)
        self.sword, self.stance = "drawn", "mid"          # R-V02

    def _sheathe(self):
        self._result["effect"] = "sheathed"
        self._plan("sheathed", SHEATHE_FRAMES)
        self.stance_change = None
        yield from self._frames(SHEATHE_FRAMES)
        self.sword, self.stance = "sheathed", None

    def _timed_attack(self, kind: str, height: str | None, frames: int, active: range):
        """Run an attack's frames, publishing its phase for the duel's contacts."""
        self.attack = {"kind": kind, "height": height, "phase": "windup", "resolved": False}
        try:
            for i in range(frames):
                self.attack["phase"] = ("active" if i in active else
                                        "windup" if i < active.start else "recovery")
                yield from self._frames(1)
        finally:
            self.attack = None

    def _lunge(self):                                       # R-V04
        total = LUNGE_WINDUP + LUNGE_ACTIVE + LUNGE_RECOVERY
        self._result["effect"] = "lunged"
        self._plan("lunge", total)
        yield from self._timed_attack("lunge", self.stance, total,
                                      range(LUNGE_WINDUP, LUNGE_WINDUP + LUNGE_ACTIVE))

    def _sweep(self):                                       # R-V11
        self._result["effect"] = "swept"
        self._plan("sweep", SWEEP_FRAMES)
        yield from self._timed_attack("sweep", "low", SWEEP_FRAMES, range(2, 4))

    def _throw(self):                                       # R-V08
        height = self.stance
        self._result["effect"] = "threw"
        self._plan("throw", THROW_FRAMES)
        for i in range(THROW_FRAMES):
            if i == THROW_RELEASE - 1:
                self.duel.release_sword(self, height)
                self.sword, self.stance, self.stance_change = "none", None, None
            yield from self._frames(1)

    def _kick(self):                                        # R-V10
        land = self.ahead()
        if (not isinstance(land, tuple) or land[0] != self.kid.room or self.blocks(land)):
            land = self.kid.cell
        self._result["effect"] = "kicked"
        self._plan("dive_kick", KICK_FRAMES, land)
        self.attack = {"kind": "kick", "height": "high", "phase": "windup",
                       "resolved": False, "land": land}
        try:
            for i in range(KICK_FRAMES):
                self.attack["phase"] = "active" if i >= KICK_FRAMES - 2 else "windup"
                self._airborne = True
                yield from self._frames(1)
        finally:
            self.attack = None
            self._airborne = False
        self._enter(land, "jump")

    def _take(self):                                        # R-V17
        g = self.uniform_ahead()
        self._result["effect"] = "took_uniform"
        self._plan("took_uniform", TAKE_FRAMES)
        yield from self._frames(TAKE_FRAMES)
        if g is None or not (g.uniform and g.downed):
            # R-V26: nothing to take is a no-op the acting seat can read; the
            # other seat saw the same TAKE frames either way.
            self._result["effect"] = "no_uniform"
        else:
            g.uniform = False
            self.disguised = True
            if self.sword == "drawn":
                self.sword = "sheathed"                     # under the uniform
            self.stance, self.stance_change = None, None

    def _rig(self):                                         # R-V27
        target = self.rig_target()
        self._result["effect"] = "no_rig" if target is None else "rigged"
        self._plan("kneeled", RIG_FRAMES)
        if target is None:                                  # not reachable: RIG is only started when legal
            return
        self.duel.traps_left[self.seat] -= 1                # spent at the start, even if cancelled
        cell = self.kid.cell
        yield from self._frames(RIG_FRAMES)
        if not (self.kid.cell == cell and self.kid.posture == "standing"
                and self.duel.place_rig(self.seat, target)):
            self._result["effect"] = "no_rig"               # the floor changed under the kneel

    def _pickup(self):                                      # R-V09
        self._result["effect"] = "took_sword"
        self._plan("took_sword", PICKUP_FRAMES)
        yield from self._frames(PICKUP_FRAMES)
        if self.duel.take_sword(self.kid.cell):
            self.sword, self.stance = "drawn", "mid"


class Duel:
    def __init__(self, situation: Situation, starts: dict[str, tuple[int, int, int, int]],
                 seed: int = 0, time_limit_frames: int = DUEL_FRAMES,
                 guard_posts: dict | None = None):
        """time_limit_frames: the duel's length; 5 minutes by default (OQ-3, closed
        2026-11-23). The single-player 60-minute clock (R-C24) is unchanged.
        guard_posts: name -> (room, row, (c0, c1)[, facing]) (pop/arena.py)."""
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
        self._move_action: dict[str, str | None] = {seat: None for seat in SEATS}
        self._started: dict[str, int] = {seat: -1 for seat in SEATS}   # frame a move began
        # Reporting only (T20-fix1): which rewrite of an accepted input began the move.
        self._rewrite: dict[str, str | None] = {seat: None for seat in SEATS}
        # R-V35 (grace window): how the last move ended, and whether this one began a run.
        self._last_end: dict[str, tuple[str | None, str | None, int] | None] = {
            seat: None for seat in SEATS}                       # (action, effect, frame)
        self._fresh: dict[str, bool] = {seat: True for seat in SEATS}
        # While the rivals advance, each plans against the other as it was when the
        # frame began, so the seat id never decides where a move goes (R-V00).
        self._view: dict[str, dict] | None = None
        self.pending: dict[str, str | None] = {seat: None for seat in SEATS}
        # Reporting only (AUDIT-B F3): queued inputs that never started.
        self.replaced: dict[str, int] = {seat: 0 for seat in SEATS}
        self.stale: dict[str, int] = {seat: 0 for seat in SEATS}
        self.last_result: dict[str, dict | None] = {seat: None for seat in SEATS}
        self.terminal: str | None = None
        self.guards = {name: Guard.at_post(name, post)
                       for name, post in sorted((guard_posts or {}).items())}
        self.swords: list[Cell] = []            # dropped swords (R-V07, R-V08)
        self.suspicion: dict[tuple[str, str], int] = {}   # (guard, seat) -> 0..100
        self.flying: list[dict] = []            # thrown swords in flight (R-V08)
        # Rigged traps (R-V27 to R-V32): cell -> {seat: kind}. Only ever shown to the
        # owning seat (observe: my_traps). `sprung` marks floors that fell from a rig.
        self.rigs: dict[Cell, dict[str, str]] = {}
        self.traps_left: dict[str, int] = {seat: TRAPS_PER_RIVAL for seat in SEATS}
        self.sprung: set[Cell] = set()

    # --- queries ------------------------------------------------------
    def standing_at(self, cell: Cell, other_than: str) -> bool:
        if self._view is not None:                          # rivals advancing: frame start
            return any(v["cell"] == cell and v["posture"] == "standing"
                       for seat, v in self._view.items() if seat != other_than)
        return any(r.kid.cell == cell and r.kid.posture == "standing"
                   for seat, r in self.rivals.items() if seat != other_than)

    def body_in(self, cell: Cell) -> bool:
        """A living rival, or any guard (downed too), in `cell`."""
        return (any(r.alive and r.kid.cell == cell for r in self.rivals.values())
                or any(g.cell == cell for g in self.guards.values()))

    def floor_below_in_room(self, cell: Cell) -> bool:
        """The tile at `cell` would fall onto a floor in the same room (the landing
        `Mechanics._drop_loose` finds), judged from visible tiles only."""
        room, row, col = cell
        for r in range(row + 1, P.ROWS):
            below = (room, r, col)
            if self.geom.tile(below) == T.WALL:
                return False
            if self.geom.supported(below):
                return True
        return False

    def place_rig(self, seat: str, cell: Cell) -> bool:
        """Rig `cell` for `seat` (R-V28, R-V31): one rig per seat per cell, so a double
        rig is possible and a refusal never tells a seat about the other's rig."""
        if self.geom.tile(cell) != T.FLOOR or seat in self.rigs.get(cell, {}):
            return False
        self.rigs.setdefault(cell, {})[seat] = RIG_KIND
        return True

    def _standing_bodies(self) -> dict[str, Cell]:
        bodies = {seat: r.kid.cell for seat, r in self.rivals.items()
                  if r.alive and r.kid.posture == "standing"}
        bodies.update({"guard:" + n: g.cell for n, g in self.guards.items() if not g.downed})
        return bodies

    def _spring_rigs(self, before: dict[str, Cell]) -> None:
        """R-V28, R-V30, R-V32: a body that stepped onto a rigged cell this frame (any
        rival, owner included, or a guard) starts the floor shaking, and the rig is
        spent. A body already standing there does not spring it. Nothing here
        records who owned it."""
        for cell in [c for c in self.rigs if self.geom.tile(c) != T.FLOOR]:
            del self.rigs[cell]                             # the floor is gone (rubble fell on it)
        if not self.rigs:
            return
        now = self._standing_bodies()
        for cell in sorted(self.rigs):
            if any(c == cell and before.get(who) != cell for who, c in now.items()):
                self.mech.loose.setdefault(cell, 0)         # shaking, as a touched loose floor
                self.sprung.add(cell)
                del self.rigs[cell]

    def guard_at(self, cell: Cell) -> Guard | None:
        """A standing (not downed) guard in `cell`."""
        for g in self.guards.values():
            if g.cell == cell and not g.downed:
                return g
        return None

    def cell_free_for_guard(self, g: Guard, cell: Cell) -> bool:
        return (isinstance(cell, tuple) and cell[0] == g.room and 0 <= cell[2] < 10
                and self.geom.tile(cell) != T.WALL and not self.mech.gate_bars(cell)
                and self.geom.supported(cell)
                and not any(r.kid.cell == cell and r.alive for r in self.rivals.values())
                and cell not in self.landings()
                and all(o is g or o.downed or o.cell != cell for o in self.guards.values()))

    def claims(self) -> dict[str, Cell]:
        """Each rival in mid-jump: the cell it will land in, when that cell is in
        its own room. A jumper keeps its cell until it lands, so nobody may step
        into its landing cell meanwhile (R-V22: a flip ends right beside whoever
        it passed). Only in its own room, where every seat and guard that could
        step in sees `motion.to`; a landing in the next room is out of their
        sight and settles on arrival instead (R-V23, reviewer 2026-11-18)."""
        out = {}
        for seat, r in self.rivals.items():
            to = (r.plan or {}).get("to")
            if (self.busy(seat) and r.plan["effect"] in JUMPS
                    and isinstance(to, tuple) and to[0] == r.kid.room):
                out[seat] = to
        return out

    def landings(self) -> set[Cell]:
        return set(self.claims().values())

    def claimed(self, cell: Cell, other_than: str) -> bool:
        """`cell` is the other rival's landing cell (as at frame start while the
        rivals advance, like standing_at)."""
        claims = ({s: v["claim"] for s, v in self._view.items()} if self._view is not None
                  else self.claims())
        return any(c == cell for s, c in claims.items() if s != other_than)

    def guard_sees(self, g: Guard) -> str | None:
        """R-V14: the nearest rival in the guard's room and row, in front, within
        5 cells, with no wall or closed gate between."""
        best = None
        for seat in sorted(self.rivals):
            r = self.rivals[seat]
            k = r.kid
            if not r.alive or k.room != g.room or k.row != g.row or k.posture == "hanging":
                continue
            d = (k.col - g.col) * g.facing
            if not 1 <= d <= SIGHT_CELLS or blocked_between(self.geom, self.mech, g.cell, k.cell):
                continue
            if not self.guard_ignores(g, r) and (best is None or d < best[0]):
                best = (d, seat)
        return best[1] if best else None

    def guard_ignores(self, g: Guard, r: "Rival") -> bool:
        """R-V18: a disguised rival is ignored until this guard's suspicion is full."""
        return r.disguised and self.suspicion.get((g.name, r.seat), 0) < SUSPICION_MAX

    def in_sight(self, g: Guard, r: "Rival") -> bool:
        """R-V14 sight, disguise or not (suspicion grows only in sight)."""
        k = r.kid
        if g.downed or not r.alive or k.room != g.room or k.row != g.row:
            return False
        d = (k.col - g.col) * g.facing
        return 1 <= d <= SIGHT_CELLS and not blocked_between(self.geom, self.mech, g.cell, k.cell)

    def hopping(self, seat: str) -> bool:
        """A hop straight up in progress: UP on open floor, not a climb (R-V24).
        Crouching (DOWN) has the same effect name, "none", so the input decides."""
        return (self.busy(seat) and self._move_action[seat] == "UP"
                and (self.rivals[seat].plan or {}).get("effect") in HOPS)

    def suspicious_rise(self, seat: str) -> int:
        """Per-frame suspicion this rival's move in progress adds in a guard's
        sight: running (R-V19), jumping or climbing (R-V19), hopping (R-V24)."""
        m = self.motion(seat)
        if m is None:
            return 0
        if m["effect"] == "moved" and m["frames"] == P.RUN:
            return SUSPICION_RUN
        if m["effect"] in LEAPS or self.hopping(seat):
            return SUSPICION_LEAP
        return 0

    def kneeling(self, seat: str) -> bool:
        m = self.motion(seat)
        return m is not None and m["effect"] == "kneeled"

    def _suspect(self) -> None:
        """R-V19 to R-V21, R-V24: each guard's meter for each disguised rival."""
        for seat, r in self.rivals.items():
            m = self.motion(seat)
            idle = m is None or m["effect"] == "waited"     # R-V19, QA3: a re-sent WAIT is still
            r.still = r.still + 1 if idle else 0
            if not r.disguised:
                continue
            for name, g in self.guards.items():
                key = (name, seat)
                level = self.suspicion.get(key, 0)
                if self.in_sight(g, r):
                    near = abs(r.kid.col - g.col) <= 1
                    if idle:
                        delta = (SUSPICION_LINGER if r.still > LINGER_AFTER else 0) if near \
                            else -SUSPICION_FALL
                    elif self.suspicious_rise(seat):
                        delta = self.suspicious_rise(seat)
                    elif self.kneeling(seat):
                        delta = SUSPICION_RIG                   # R-V33: rigging in sight
                    elif m["effect"] == "moved":
                        delta = -SUSPICION_FALL                 # walking (a careful step)
                    else:
                        delta = 0
                else:
                    delta = -SUSPICION_FALL
                level = max(0, min(SUSPICION_MAX, level + delta))
                self.suspicion[key] = level
                if level >= SUSPICION_MAX:
                    r.disguised = False                         # R-V21: found out

    def busy(self, seat: str) -> bool:
        return self._moves[seat] is not None

    def motion(self, seat: str) -> dict | None:
        """The move in progress: effect, frames done, length, planned end."""
        r = self.rivals[seat]
        if not self.busy(seat) or r.plan is None:
            return None
        return {**r.plan, "frame": self._move_frame[seat] - r.plan_from}

    def airborne_jump(self, seat: str) -> bool:
        r = self.rivals[seat]
        return self.busy(seat) and r._airborne and (r.plan or {}).get("effect") in JUMPS

    def legal_actions(self, seat: str) -> tuple[str, ...]:
        if self.terminal is not None:
            return ()
        r = self.rivals[seat]
        if r.knocked_down:
            return ()                                       # R-V12
        acts = list(LEGAL_BY_POSTURE[r.kid.posture])
        if r.kid.posture == "standing":
            if r.sword == "drawn":
                # Up/Down change stance while the sword is drawn (VERSUS_SPEC 2.3).
                acts = [a for a in acts if a not in ("UP", "DOWN")]
                target = r.stance_change[0] if r.stance_change else r.stance
                i = STANCES.index(target)
                if i < 2:
                    acts.append("STANCE_UP")
                if i > 0:
                    acts.append("STANCE_DOWN")
                acts += ["LUNGE", "THROW", "SHEATHE"]
            elif r.sword == "sheathed":
                acts.append("DRAW")
            acts.append("SWEEP")
            if not r.disguised and r.downed_guard_ahead() is not None:
                acts.append("TAKE")                         # R-V26: whether or not a uniform remains
            if r.rig_target() is not None:
                acts.append("RIG")                          # R-V27
        if self.airborne_jump(seat):
            acts.append("KICK")
        return tuple(acts)

    # --- inputs and frames -------------------------------------------
    def submit(self, seat: str, action: str) -> None:
        """Queue a validated input; a newer input replaces an older one. A stance
        change is not queued: it starts at once beside any move (R-V03)."""
        r = self.rivals[seat]
        if action in ("STANCE_UP", "STANCE_DOWN"):
            base = r.stance_change[0] if r.stance_change else r.stance
            i = STANCES.index(base) + (1 if action == "STANCE_UP" else -1)
            r.stance_change = (STANCES[i], STANCE_FRAMES)
            return
        if self.pending[seat] is not None:
            self.replaced[seat] += 1         # the latest press wins (VERSUS_SPEC 2.1)
        self.pending[seat] = action

    def tick(self) -> None:
        """One frame: the world once, then each rival's move one frame."""
        if self.terminal is not None:
            return
        self.frames += 1
        for body in [*self.rivals.values(), *self.guards.values()]:
            body.invulnerable = max(0, body.invulnerable - 1)
            body.knocked_down = max(0, body.knocked_down - 1)
        cells0 = self._standing_bodies()
        alive = [r for r in self.rivals.values() if r.alive]
        pressing = sorted({c for r in alive if (c := r._pressing()) is not None})
        near: set[Cell] = set()
        for r in alive:
            near |= r._near_cells()
        first = pressing[0] if pressing else None
        self.events = self.mech.tick(first, near, frozenset(pressing[1:]))
        for _, fell, landed in self.events:               # R-V16: a trap downs a guard
            for g in self.guards.values():
                if not g.downed and g.cell in (fell, landed):
                    g.knock_out()
        before = {seat: r.kid.cell for seat, r in self.rivals.items()}
        claims = self.claims()
        self._view = {seat: {"cell": r.kid.cell, "posture": r.kid.posture,
                             "claim": claims.get(seat)} for seat, r in self.rivals.items()}
        try:
            for seat in SEATS:
                self._advance(seat)
        finally:
            self._view = None
        self._settle_arrivals(before)
        for r in self.rivals.values():                      # R-V03: stance timers
            if r.stance_change and r.armed:
                target, left = r.stance_change
                if left <= 1:
                    r.stance, r.stance_change, r.stance_landed = target, None, self.frames
                else:
                    r.stance_change = (target, left - 1)
        for g in self.guards.values():                      # R-V13 to R-V15
            g.update(self)
        self._suspect()
        self._fly_swords()
        self._contacts()
        self._spring_rigs(cells0)
        self._check_end()

    def _advance(self, seat: str) -> None:
        r = self.rivals[seat]
        if not r.alive:
            return
        if r.knocked_down:                   # R-V12: lies there; the world still acts on it
            r._tick()
            return
        gen = self._moves[seat]
        if gen is not None and self.pending[seat] == "KICK" and self.airborne_jump(seat):
            self.pending[seat] = None        # R-V10: the kick replaces the rest of the jump
            self.cancel(seat)
            if self._start(seat, "KICK", "kick"):
                return
            r._tick()
            return
        jump = self._grace_jump(seat) if gen is not None else None
        if jump is not None:                 # R-V35: a jump just after a direction is one flip
            self.pending[seat] = None
            self.cancel(seat)
            if self._start(seat, jump, "grace"):
                return
            r._tick()
            return
        d = self._hop_turn(seat) if gen is not None else None
        if d is not None:                    # R-V22: a direction turns the hop into a flip
            self.pending[seat] = None
            self.cancel(seat)
            if self._start(seat, "_HOP_FLIP_" + d, "hop_turn"):
                return
            r._tick()
            return
        if gen is not None:
            try:
                next(gen)
                self._move_frame[seat] += 1
                return
            except StopIteration:
                self._finish(seat)
        action = self.pending[seat]
        self.pending[seat] = None
        if action is not None:
            if action != "KICK" and action in self.legal_actions(seat) and r.terminal is None:
                if self._start(seat, action):
                    return
            else:
                self.stale[seat] += 1        # no longer legal now that the rival is free
        r._tick()                            # free this frame: the world still acts on it

    def _hop_turn(self, seat: str) -> str | None:
        """"LEFT"/"RIGHT" if this rival is hopping straight up (an UP move that
        is not a climb) and its pending input points a direction (R-V22)."""
        act, r = self.pending[seat], self.rivals[seat]
        if (act is None or self._move_action[seat] != "UP"
                or (r.plan or {}).get("effect") not in HOPS):
            return None
        return next((d for d in ("LEFT", "RIGHT") if act in DIRECTIONAL[d]), None)

    def _grace_jump(self, seat: str) -> str | None:
        """R-V35 (Saad #54, 2026-11-24): the jump a seat meant, if a jump input
        arrived within GRACE_TICKS of a plain direction (a run, a careful step or
        a turn) that began a fresh run, and the jump would not be a climb.

        Direction first, then jump: the pending input is a jump that way, a
        running jump asked for by a front end that already saw the first run
        frame, or a bare UP that hops. The unfinished direction move is dropped
        (it places the kid only at its end, so nothing is lost) and a standing
        jump that way starts now. A direction that began a run chain is left
        alone: a jump mid-run is the ordinary running jump. Jump first, then
        direction is the hop turn (`_hop_turn`, R-V22)."""
        act, mv = self.pending[seat], self._move_action[seat]
        if (act is None or mv is None or not self._fresh[seat]
                or not 1 <= self._move_frame[seat] <= GRACE_TICKS):
            return None
        d = next((n for n in ("LEFT", "RIGHT") if mv in (n, "STEP_" + n)), None)
        if d is None:
            return None
        if act == "JUMP_" + d or (act == "RUN_JUMP_" + d and mv == d) or (
                act == "UP" and self.rivals[seat].up_hops()):
            return "JUMP_" + d
        return None

    def _start(self, seat: str, action: str, rewrite: str | None = None) -> bool:
        """Start a move and run its first frame; False if it had no frames. `rewrite`
        names the engine rule that replaced the accepted input (reporting only)."""
        self._rewrite[seat] = rewrite
        r = self.rivals[seat]
        last = self._last_end[seat]
        side = next((n for n in ("LEFT", "RIGHT") if n in action), None)
        self._fresh[seat] = not (last is not None and last[1] == "moved"
                                 and last[2] >= self.frames - 1
                                 and side is not None and side in (last[0] or ""))
        self._move_action[seat] = action
        self._started[seat] = self.frames
        gen = r._versus_macro(action)
        self._moves[seat], self._move_frame[seat] = gen, 0
        try:
            next(gen)
            self._move_frame[seat] = 1
            return True
        except StopIteration:                # a move with no frames (dropping from a hang)
            self._finish(seat)
            return False

    def cancel(self, seat: str) -> None:
        """Stop a rival's move where it is (hit, knocked down, disarmed)."""
        gen = self._moves[seat]
        if gen is not None:
            gen.close()
        self._moves[seat] = None
        self._move_frame[seat] = 0
        r = self.rivals[seat]
        r.attack, r.plan, r._airborne = None, None, False

    def _finish(self, seat: str) -> None:
        r = self.rivals[seat]
        r._result["frames"] = self._move_frame[seat]
        self._last_end[seat] = (self._move_action[seat], r._result.get("effect"), self.frames)
        self.last_result[seat] = dict(r._result)
        self._moves[seat] = None
        self._move_frame[seat] = 0

    def _settle_arrivals(self, before: dict[str, Cell]) -> None:
        """A rival that ended this frame standing on someone else's cell.

        R-V00: two rivals that ran into one cell in the same frame both go back
        where they were. R-V23 (Saad, 2026-11-23, "step in and settle"): one that
        arrived on someone it could not plan around (a body out of sight, or one
        that arrived after its move began) ends on the nearest free cell of the
        room it arrived in, back toward where it came from first, then forward.
        It never goes back to a room it has left, so a body out of sight is only
        found by entering its room and seeing it. Only if that row has no free
        cell does it go back where it was."""
        a, b = self.rivals["A"].kid, self.rivals["B"].kid
        movers = [seat for seat in SEATS if self.rivals[seat].kid.cell != before[seat]]
        if len(movers) == 2 and a.cell == b.cell and a.posture == b.posture == "standing":
            for seat in SEATS:
                k = self.rivals[seat].kid
                k.room, k.row, k.col = before[seat]
            return
        dest = {seat: self._nearest_free(seat, before[seat])
                for seat in movers if self._on_someone(seat)}
        if len(dest) == 2 and dest["A"] == dest["B"]:
            dest = {seat: before[seat] for seat in dest}      # symmetric: both go back
        for seat, cell in dest.items():
            k = self.rivals[seat].kid
            k.room, k.row, k.col = cell
            self.mech.touch_loose(cell)
            self._replan(seat)

    def _on_someone(self, seat: str) -> bool:
        r = self.rivals[seat]
        return (r.alive and r.kid.posture == "standing"
                and (self.standing_at(r.kid.cell, other_than=seat)
                     or self.guard_at(r.kid.cell) is not None))

    def _nearest_free(self, seat: str, came_from: Cell) -> Cell:
        k = self.rivals[seat].kid
        back = -k.facing                                    # every arrival moves forward
        for n in range(1, 10):
            for d in (back * n, -back * n):
                c = self.geom.offset(k.cell, 0, d)
                if (isinstance(c, tuple) and c[0] == k.room and self._settles_in(seat, c)
                        and not blocked_between(self.geom, self.mech, k.cell, c)):
                    return c
        return came_from

    def _settles_in(self, seat: str, c: Cell) -> bool:
        return (self.geom.tile(c) not in (T.WALL, T.SPIKES) and not self.mech.gate_bars(c)
                and self.geom.supported(c) and not self.standing_at(c, other_than=seat)
                and self.guard_at(c) is None and not self.claimed(c, other_than=seat))

    def _replan(self, seat: str) -> None:
        """A settled rival's move in progress was planned from the cell it was
        moved off: stop it. A move that only began this frame (an input queued
        for the landing) is queued again, to be planned from the new cell."""
        if not self.busy(seat):
            return
        action = self._move_action[seat] if self._started[seat] == self.frames else None
        self.cancel(seat)
        if action is not None and not action.startswith("_") and self.pending[seat] is None:
            self.pending[seat] = action

    # --- swords and contacts (R-V04 to R-V12) ---------------------------------
    def _free(self, r: Rival, cell) -> bool:
        return (isinstance(cell, tuple) and cell[0] == r.kid.room and not r.blocks(cell)
                and self.geom.supported(cell))

    def _push(self, r: Rival, d: int) -> None:
        dest = self.geom.offset(r.kid.cell, 0, d)
        if self._free(r, dest):
            r.kid.room, r.kid.row, r.kid.col = dest

    def _settle(self, cell: Cell) -> Cell | None:
        """Where a dropped sword comes to rest: this cell or the first floor below."""
        while isinstance(cell, tuple):
            if self.geom.supported(cell):
                return cell
            cell = self.geom.offset(cell, 1, 0)
        return None

    def drop_sword(self, r: Rival, behind: bool) -> None:
        """Knock r's sword away, 1 or 2 cells behind it (R-V07, R-V10)."""
        r.sword, r.stance, r.stance_change = "none", None, None
        d = -r.kid.facing if behind else r.kid.facing
        n = self.rng.choice((1, 2))
        spot = r.kid.cell
        for step in range(n, 0, -1):
            c = self.geom.offset(r.kid.cell, 0, d * step)
            if isinstance(c, tuple) and c[0] == r.kid.room and not Game.blocks(r, c):
                spot = c
                break
        if (rest := self._settle(spot)) is not None:
            self.swords.append(rest)

    def take_sword(self, cell: Cell) -> bool:
        if cell in self.swords:
            self.swords.remove(cell)
            return True
        return False

    def release_sword(self, thrower: Rival, height: str) -> None:       # R-V08
        d = thrower.kid.facing
        start = self.geom.offset(thrower.kid.cell, 0, d)
        if not (isinstance(start, tuple) and start[0] == thrower.kid.room
                and not Game.blocks(thrower, start)):
            if (rest := self._settle(thrower.kid.cell)) is not None:
                self.swords.append(rest)
            return
        sword = {"cell": start, "dir": d, "height": height, "owner": thrower.seat}
        if not self._sword_meets(sword):
            self.flying.append(sword)

    def _sword_meets(self, sword: dict) -> bool:
        """A flying sword reaching a rival or a standing guard: deflected by the
        thrower's stance, else a hit (a guard is downed, R-V16). True if it stopped."""
        for seat, r in self.rivals.items():
            if seat == sword["owner"] or not r.alive or r.kid.cell != sword["cell"]:
                continue
            if not (r.armed and r.stance == sword["height"] and r.kid.facing == -sword["dir"]):
                self._hit(r, sword["dir"], "died:thrown_sword")
            if (rest := self._settle(sword["cell"])) is not None:
                self.swords.append(rest)
            return True
        g = self.guard_at(sword["cell"])
        if g is not None:
            if not (g.armed and g.stance == sword["height"] and g.facing == -sword["dir"]):
                g.knock_out()
            if (rest := self._settle(sword["cell"])) is not None:
                self.swords.append(rest)
            return True
        return False

    def _fly_swords(self) -> None:
        still = []
        for sword in self.flying:
            # A body that arrived in the sword's cell this frame meets it here: a
            # sword and a walker swapping cells must not pass through each other.
            if self._sword_meets(sword):
                continue
            stopped = False
            for _ in range(THROW_SPEED):
                nxt = self.geom.offset(sword["cell"], 0, sword["dir"])
                if (not isinstance(nxt, tuple) or nxt[0] != sword["cell"][0]
                        or self.geom.tile(nxt) == T.WALL or self.mech.gate_bars(nxt)):
                    if (rest := self._settle(sword["cell"])) is not None:
                        self.swords.append(rest)
                    stopped = True
                    break
                sword["cell"] = nxt
                if self._sword_meets(sword):
                    stopped = True
                    break
            if not stopped:
                still.append(sword)
        self.flying = still

    def _hit(self, r: Rival, d: int, reason: str) -> None:
        """A clean hit: 1 heart, pushed back 1 cell, 12 frames invulnerable (R-V06)."""
        if r.invulnerable:
            return
        self.cancel(r.seat)
        r._hurt(1, reason)
        r.invulnerable = INVULNERABLE_FRAMES
        if r.alive:
            self._push(r, d)

    def _body_at(self, cell, exclude) -> object | None:
        for r in self.rivals.values():
            if r is not exclude and r.alive and r.kid.cell == cell:
                return r
        g = self.guard_at(cell)
        return g if g is not exclude else None

    @staticmethod
    def _facing(body) -> int:
        return body.kid.facing if isinstance(body, Rival) else body.facing

    def _contacts(self) -> None:
        """Every attack's effect this frame, decided on the frame's end state for
        every attacker first, then applied (no seat-order advantage). Rivals and
        guards attack and defend by the same rules (R-V04 to R-V12)."""
        effects = []
        attackers = [r for r in self.rivals.values() if r.alive and r.attack]
        attackers += [g for g in self.guards.values() if not g.downed and g.attack]
        for att in attackers:
            a = att.attack
            if a["resolved"]:
                continue
            here = att.kid.cell if isinstance(att, Rival) else att.cell
            target = self.geom.offset(a.get("land", here), 0, self._facing(att))
            other = self._body_at(target, att)
            if other is None:
                continue
            facing_me = self._facing(other) == -self._facing(att)
            if a["kind"] == "lunge" and a["phase"] == "windup":
                if (isinstance(att, Rival) and other.armed and facing_me
                        and other.stance == a["height"] and other.stance_landed == self.frames):
                    effects.append(("disarm", att, other))           # R-V07 (guards cannot be disarmed)
            elif a["kind"] == "lunge" and a["phase"] == "active":
                if other.knocked_down:
                    effects.append(("hit", att, other))              # R-V12
                elif other.armed and facing_me and other.stance == a["height"]:
                    effects.append(("block", att, other))            # R-V05
                else:
                    effects.append(("hit", att, other))              # R-V06
            elif a["kind"] == "kick" and a["phase"] == "active":
                if other.armed and facing_me and other.stance == "high":
                    effects.append(("blocked", att, other))
                else:
                    effects.append(("kicked", att, other))           # R-V10
            elif a["kind"] == "sweep" and a["phase"] == "active":
                if (other.armed and other.stance == "low") or other._airborne:
                    effects.append(("blocked", att, other))
                else:
                    effects.append(("swept", att, other))            # R-V11
        for kind, att, other in effects:
            if att.attack is not None:
                att.attack["resolved"] = True
            if kind == "disarm":
                self.cancel(att.seat)
                self.drop_sword(att, behind=True)
            elif kind == "block":
                self._push_back(att)
            elif kind == "hit":
                if isinstance(other, Rival):
                    reason = "died:guard" if isinstance(att, Guard) else "died:stabbed"
                    self._hit(other, self._facing(att), reason)
                else:
                    other.knock_out()                                # R-V16
            elif kind in ("kicked", "swept"):
                if isinstance(other, Rival):
                    self.cancel(other.seat)
                    if kind == "kicked" and other.sword == "drawn":
                        self.drop_sword(other, behind=True)
                else:
                    other.action = other.attack = None
                other.knocked_down = KNOCKDOWN_FRAMES

    def _push_back(self, body) -> None:
        if isinstance(body, Rival):
            self._push(body, -body.kid.facing)
        else:
            dest = (body.room, body.row, body.col - body.facing)
            if self.cell_free_for_guard(body, dest):
                body.col = dest[2]

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
                              "sword": r.sword, "stance": r.stance,
                              "stance_change": r.stance_change, "attack": r.attack,
                              "invulnerable": r.invulnerable, "knocked_down": r.knocked_down,
                              "busy": self.busy(seat), "move_frame": self._move_frame[seat]}
                       for seat, r in self.rivals.items()},
            "guards": {n: g.snapshot() for n, g in self.guards.items()},
            "disguised": {seat: r.disguised for seat, r in self.rivals.items()},
            "suspicion": {f"{g}:{seat}": v for (g, seat), v in sorted(self.suspicion.items())},
            "swords": list(self.swords),
            "rigs": {str(c): dict(v) for c, v in sorted(self.rigs.items())},
            "traps_left": dict(self.traps_left),
            "sprung": sorted(self.sprung),
            "flying": [dict(s) for s in self.flying],
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
    # The duel's own clock, not the single-player one observation.build reads.
    obs["minutes_left"] = max(0, (duel.time_limit - duel.frames) // (TICKS_PER_SECOND * 60))
    obs["me"] = {**obs["kid"], "stance": me.stance, "armed": me.armed,
                 "disguised": me.disguised, "knocked_down_frames": me.knocked_down,
                 "motion": _motion_view(duel, seat, room), "traps_left": duel.traps_left[seat]}
    figures = []
    for other, r in duel.rivals.items():
        if other == seat or r.kid.room != room:
            continue
        # R-V18: a disguised rival is observed exactly as a guard (same kind and
        # fields; sheathed, so stance None and armed False, like a patrolling guard).
        motion = _motion_view(duel, other, room)
        # A move that ends in another room is masked too (GATE-T01 QA1): a guard's
        # move never does, and the figure still leaves the room on arrival.
        if (r.disguised and motion is not None
                and ((motion["effect"], motion["frames"]) not in GUARD_MOTIONS
                     or motion["to"] is None)
                and not duel.suspicious_rise(other)):
            motion = None           # T01 / AUDIT-B F1: shown as a paused guard is
        figures.append({"kind": "guard" if r.disguised else "rival",
                        "row": r.kid.row, "col": r.kid.col,
                        "facing": "right" if r.kid.facing > 0 else "left",
                        "posture": "knocked_down" if r.knocked_down else r.kid.posture,
                        "stance": r.stance, "armed": r.armed,
                        "motion": motion})
    for g in duel.guards.values():
        if g.room != room:
            continue
        m = g.motion()
        figures.append({"kind": "guard", "row": g.row, "col": g.col,
                        "facing": "right" if g.facing > 0 else "left",
                        "posture": "downed" if g.downed else
                        "knocked_down" if g.knocked_down else "standing",
                        "stance": g.stance, "armed": g.armed,
                        "motion": None if m is None else {
                            "effect": m["effect"], "frame": m["frame"], "frames": m["frames"],
                            "to": [m["to"][1], m["to"][2]] if m["to"][0] == room else None,
                            "to_posture": m["posture"],
                            "to_facing": "right" if m["facing"] > 0 else "left"}})
    # Every observed field, so a tie never falls back to insertion order (rivals
    # before guards), which would tell a disguised rival from a guard (GATE-T01 L2).
    obs["figures"] = sorted(figures, key=lambda f: (f["row"], f["col"], f["kind"], json.dumps(f, sort_keys=True)))
    obs["swords"] = sorted(
        [{"row": c[1], "col": c[2], "flying": False} for c in duel.swords if c[0] == room]
        + [{"row": f["cell"][1], "col": f["cell"][2], "flying": True}
           for f in duel.flying if f["cell"][0] == room],
        key=lambda s: (s["row"], s["col"], s["flying"]))
    # R-V34: this seat's own unsprung rigs in its room; never the other seat's.
    obs["my_traps"] = sorted(
        ({"row": c[1], "col": c[2], "kind": kinds[seat]}
         for c, kinds in duel.rigs.items() if c[0] == room and seat in kinds),
        key=lambda t: (t["row"], t["col"]))
    # R-V19: each guard's meter for THIS rival only, for guards in its room.
    obs["suspicion"] = [{"row": g.row, "col": g.col, "level": lvl}
                        for (name, s), lvl in sorted(duel.suspicion.items())
                        if s == seat and lvl > 0 and (g := duel.guards[name]).room == room
                        and not g.downed]
    return obs


class StartedMove(str):
    """The name of a move the engine started (see `VersusEpisode.started_move`). It is a
    plain string; `rewrite` says which engine rule replaced the accepted input, if any:
    "kick" (R-V10), "grace" (R-V35), "hop_turn" (R-V22) or None."""

    rewrite: str | None = None


class VersusEpisode:
    """The five operations per seat (VERSUS_SPEC 2.2), plus `tick` for the runner
    and server only. Seats never receive the Duel."""

    def __init__(self, situation: Situation, starts: dict[str, tuple[int, int, int, int]],
                 seed: int = 0, time_limit_frames: int = DUEL_FRAMES,
                 guard_posts: dict | None = None):
        self._situation = situation
        self._starts = dict(starts)
        self._time_limit = time_limit_frames
        self._guard_posts = dict(guard_posts or {})
        self.reset(seed)

    # 1
    def reset(self, seed: int) -> None:
        self.seed = seed
        self._duel = Duel(self._situation, self._starts, seed, self._time_limit,
                          self._guard_posts)
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
        if name not in ACTIONS and name not in VERSUS_ACTIONS:
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
                "invalid_inputs": dict(self.invalid),
                "stale_inputs": dict(self._duel.stale),
                "replaced_inputs": dict(self._duel.replaced)}

    # runner and server only
    def tick(self) -> None:
        self._duel.tick()

    def started_move(self, seat: str) -> str | None:
        """T20-fix1 (decision #81): the move the engine started for `seat` on the last
        tick, or None. It is the move after every rewrite the engine makes to an
        accepted input (R-V10 kick swap, R-V22 hop turn, R-V35 grace cancel) and after
        stale-input drops, so a held key or a queued input is not a start. Read-only
        reporting for the host's playtest log: no rule reads it and no observation
        carries it. The internal hop-flip keeps its engine name (`_HOP_FLIP_LEFT`). The
        result is a str whose `.rewrite` names the rule that replaced the input."""
        _check_seat(seat)
        d = self._duel
        if d._started[seat] != d.frames:
            return None
        action = d._move_action[seat]
        # `_replan` puts a move cancelled on its first frame back in the queue: it
        # starts again next tick, so it is counted then.
        if action is not None and d.pending[seat] == action:
            return None
        move = StartedMove(action)
        move.rewrite = d._rewrite[seat]
        return move

    def _refuse(self, seat: str, error: str, count: bool = True) -> dict:
        if count:
            self.invalid[seat] += 1
        return {"accepted": False, "error": error}


def _check_seat(seat: str) -> None:
    if seat not in SEATS:
        raise ValueError(INVALID_SEAT)


def arena_episode(seed: int = 0, time_limit_frames: int = DUEL_FRAMES) -> VersusEpisode:
    """The six-room arena (pop/arena.py) with both rivals at their starts."""
    from . import arena
    return VersusEpisode(arena.situation("A"), arena.STARTS, seed, time_limit_frames,
                         arena.GUARD_POSTS)

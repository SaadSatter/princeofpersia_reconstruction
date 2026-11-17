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
import random

from . import observation
from . import physics as P
from . import tiles as T
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
VERSUS_ACTIONS = ("DRAW", "SHEATHE", "STANCE_UP", "STANCE_DOWN", "LUNGE", "THROW",
                  "KICK", "SWEEP")


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
        # Swordplay state (VERSUS_SPEC 3).
        self.sword = "sheathed"            # "drawn", "sheathed" or "none" (disarmed / thrown)
        self.stance: str | None = None     # set while drawn
        self.stance_change: tuple[str, int] | None = None   # (target, frames left), R-V03
        self.stance_landed = -1            # duel frame the last stance change took effect
        self.attack: dict | None = None    # the attack in progress and its phase this frame
        self.invulnerable = 0              # R-V06
        self.knocked_down = 0              # R-V12
        self.disguised = False

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

    @property
    def armed(self) -> bool:
        return self.sword == "drawn"

    # --- swordplay macros (per-frame generators, like the inherited ones) ---
    def _versus_macro(self, action: str):
        if action in VERSUS_ACTIONS or (action == "DOWN" and self.sword == "none"
                                        and self.kid.cell in self.duel.swords):
            self._result = {"effect": None, "frames": 0, "fell_rows": 0, "hp_change": 0}
            self.plan = None
            return {"DRAW": self._draw, "SHEATHE": self._sheathe, "LUNGE": self._lunge,
                    "THROW": self._throw, "KICK": self._kick, "SWEEP": self._sweep,
                    "DOWN": self._pickup}[action]()
        return self._macro(action)

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

    def _pickup(self):                                      # R-V09
        self._result["effect"] = "took_sword"
        self._plan("took_sword", PICKUP_FRAMES)
        yield from self._frames(PICKUP_FRAMES)
        if self.duel.take_sword(self.kid.cell):
            self.sword, self.stance = "drawn", "mid"


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
        self.swords: list[Cell] = []            # dropped swords (R-V07, R-V08)
        self.flying: list[dict] = []            # thrown swords in flight (R-V08)

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

    def airborne_jump(self, seat: str) -> bool:
        r = self.rivals[seat]
        return self.busy(seat) and r._airborne and (r.plan or {}).get("effect") == "jumped"

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
        self.pending[seat] = action

    def tick(self) -> None:
        """One frame: the world once, then each rival's move one frame."""
        if self.terminal is not None:
            return
        self.frames += 1
        for r in self.rivals.values():
            r.invulnerable = max(0, r.invulnerable - 1)
            r.knocked_down = max(0, r.knocked_down - 1)
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
        for r in self.rivals.values():                      # R-V03: stance timers
            if r.stance_change and r.armed:
                target, left = r.stance_change
                if left <= 1:
                    r.stance, r.stance_change, r.stance_landed = target, None, self.frames
                else:
                    r.stance_change = (target, left - 1)
        self._fly_swords()
        self._contacts()
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
            if self._start(seat, "KICK"):
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
        if action is not None and action != "KICK" and action in self.legal_actions(seat) \
                and r.terminal is None and self._start(seat, action):
            return
        r._tick()                            # free this frame: the world still acts on it

    def _start(self, seat: str, action: str) -> bool:
        """Start a move and run its first frame; False if it had no frames."""
        r = self.rivals[seat]
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
        """A flying sword reaching a rival: deflected by the thrower's stance, else a hit.
        True if it stopped there."""
        for seat, r in self.rivals.items():
            if seat == sword["owner"] or not r.alive or r.kid.cell != sword["cell"]:
                continue
            if not (r.armed and r.stance == sword["height"] and r.kid.facing == -sword["dir"]):
                self._hit(r, sword["dir"], "died:thrown_sword")
            if (rest := self._settle(sword["cell"])) is not None:
                self.swords.append(rest)
            return True
        return False

    def _fly_swords(self) -> None:
        still = []
        for sword in self.flying:
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

    def _contacts(self) -> None:
        """Every attack's effect this frame, decided on the frame's end state for
        both rivals first, then applied (no seat-order advantage)."""
        effects = []
        for seat, att in self.rivals.items():
            a = att.attack
            if not a or a["resolved"] or not att.alive:
                continue
            base = a.get("land", att.kid.cell)
            target = self.geom.offset(base, 0, att.kid.facing)
            other = self.rivals["B" if seat == "A" else "A"]
            if not (other.alive and other.kid.cell == target):
                continue
            facing_me = other.kid.facing == -att.kid.facing
            if a["kind"] == "lunge" and a["phase"] == "windup":
                if (other.armed and facing_me and other.stance == a["height"]
                        and other.stance_landed == self.frames):
                    effects.append(("disarm", att, other))           # R-V07
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
                self._push(att, -att.kid.facing)
            elif kind == "hit":
                self._hit(other, att.kid.facing, "died:stabbed")
            elif kind == "kicked":
                self.cancel(other.seat)
                if other.sword == "drawn":
                    self.drop_sword(other, behind=True)
                other.knocked_down = KNOCKDOWN_FRAMES
            elif kind == "swept":
                self.cancel(other.seat)
                other.knocked_down = KNOCKDOWN_FRAMES

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
            "swords": list(self.swords),
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
    obs["me"] = {**obs["kid"], "stance": me.stance, "armed": me.armed,
                 "disguised": me.disguised, "knocked_down_frames": me.knocked_down,
                 "motion": _motion_view(duel, seat, room)}
    figures = []
    for other, r in duel.rivals.items():
        if other == seat or r.kid.room != room:
            continue
        figures.append({"kind": "rival", "row": r.kid.row, "col": r.kid.col,
                        "facing": "right" if r.kid.facing > 0 else "left",
                        "posture": "knocked_down" if r.knocked_down else r.kid.posture,
                        "stance": r.stance, "armed": r.armed,
                        "motion": _motion_view(duel, other, room)})
    obs["figures"] = sorted(figures, key=lambda f: (f["row"], f["col"], f["kind"]))
    obs["swords"] = sorted(
        [{"row": c[1], "col": c[2], "flying": False} for c in duel.swords if c[0] == room]
        + [{"row": f["cell"][1], "col": f["cell"][2], "flying": True}
           for f in duel.flying if f["cell"][0] == room],
        key=lambda s: (s["row"], s["col"], s["flying"]))
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

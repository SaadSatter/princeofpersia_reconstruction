"""Scripted guards, R-V13 to R-V16 (docs/final/VERSUS_SPEC.md Section 4).

Scripted, not AI (GDD): hostile to both rivals equally. A guard patrols its
post with its sword sheathed, so a disguised rival (Stage 4, R-V18) can look
exactly like one. On seeing an undisguised rival it draws, advances, copies
the rival's stance after a reaction delay and lunges when adjacent. One clean
hit or a trap downs it for the rest of the duel (R-V16).

A guard's timed actions (step, turn, draw, sheathe) report their progress the
way a rival's moves do (frames 1..N, the result applied when the guard is
next updated), and its lunge publishes the same windup/active/recovery phases,
so the duel resolves every contact with one rule set (pop/versus.py).

Implementation choices the spec left open (listed for Saad in the PR): a
guard chases at run pace (4 frames per cell), cannot be disarmed, and a kick
or sweep knocks it down for 10 frames rather than downing it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import physics as P
from . import tiles as T
from .physics import Cell

SIGHT_CELLS = 5                  # R-V14
PATROL_PAUSE = 12                # R-V13
REACTION_FRAMES = 6              # R-V15
LUNGE_COOLDOWN = 16              # R-V15
ALERT_DRAW_FRAMES = 3            # draws like a rival (R-V02)
PATROL_FRAMES = P.STEP           # R-V13: step speed
CHASE_FRAMES = P.RUN             # implementation choice: run pace


@dataclass
class Guard:
    name: str
    room: int
    row: int
    col: int
    facing: int
    c0: int
    c1: int
    sword: str = "sheathed"
    stance: str | None = None
    stance_change: tuple[str, int] | None = None
    stance_landed: int = -1
    downed: bool = False
    uniform: bool = True
    knocked_down: int = 0
    target: str | None = None          # the rival it is after (never observed)
    action: dict | None = None         # step / turn / draw / sheathe in progress
    attack: dict | None = None         # lunge in progress, same shape as a rival's
    cooldown: int = 0
    pause: int = 0
    turn_due: bool = False
    _airborne: bool = field(default=False, repr=False)
    invulnerable: int = 0

    @classmethod
    def at_post(cls, name: str, post: tuple) -> "Guard":
        room, row, (c0, c1), *rest = post
        facing = rest[0] if rest else +1
        return cls(name, room, row, c0 if facing > 0 else c1, facing, c0, c1)

    @property
    def cell(self) -> Cell:
        return (self.room, self.row, self.col)

    @property
    def armed(self) -> bool:
        return self.sword == "drawn" and not self.downed

    @property
    def standing(self) -> bool:
        return not self.downed

    def knock_out(self) -> None:
        """Downed for good (R-V16): one clean hit or a trap."""
        self.downed = True
        self.action = self.attack = None
        self.stance, self.stance_change, self.target = None, None, None

    def motion(self) -> dict | None:
        """The action in progress as a rival's move would report it."""
        if self.attack:
            return {"effect": "lunge", "frame": self.attack["frame"], "frames": self.attack["total"],
                    "to": self.cell, "posture": "standing", "facing": self.facing}
        if self.action:
            a = self.action
            return {"effect": a["effect"], "frame": a["frame"], "frames": a["frames"],
                    "to": a.get("to", self.cell), "posture": "standing",
                    "facing": a.get("to_facing", self.facing)}
        return None

    # --- one frame --------------------------------------------------------
    def update(self, duel) -> None:
        from .versus import LUNGE_ACTIVE, LUNGE_RECOVERY, LUNGE_WINDUP
        if self.downed:
            return
        self.cooldown = max(0, self.cooldown - 1)
        if self.knocked_down:
            return
        if self.stance_change and self.armed:                       # R-V15 reaction
            target, left = self.stance_change
            if left <= 1:
                self.stance, self.stance_change, self.stance_landed = target, None, duel.frames
            else:
                self.stance_change = (target, left - 1)
        seen = duel.guard_sees(self)
        self.target = seen
        if seen and self.armed:
            r = duel.rivals[seen]
            want = r.stance if r.armed else None
            if want and want != self.stance and (not self.stance_change
                                                 or self.stance_change[0] != want):
                self.stance_change = (want, REACTION_FRAMES)
        if self.attack:
            a = self.attack
            if a["frame"] >= a["total"]:
                self.attack = None
            else:
                a["frame"] += 1
                i = a["frame"] - 1
                a["phase"] = ("windup" if i < LUNGE_WINDUP else
                              "active" if i < LUNGE_WINDUP + LUNGE_ACTIVE else "recovery")
                return
        if self.action:
            a = self.action
            if a["frame"] < a["frames"]:
                a["frame"] += 1
                return
            self._complete(duel)
        self._decide(duel, seen, LUNGE_WINDUP + LUNGE_ACTIVE + LUNGE_RECOVERY)

    def _start(self, effect: str, frames: int, **extra) -> None:
        self.action = {"effect": effect, "frames": frames, "frame": 1, **extra}

    def _complete(self, duel) -> None:
        a, self.action = self.action, None
        if a["effect"] == "moved":
            to = a["to"]
            if duel.cell_free_for_guard(self, to):
                self.room, self.row, self.col = to
        elif a["effect"] == "drew":
            self.sword, self.stance = "drawn", "mid"
        elif a["effect"] == "sheathed":
            self.sword, self.stance, self.stance_change = "sheathed", None, None

    def _decide(self, duel, seen: str | None, lunge_frames: int) -> None:
        if seen:
            if not self.armed:
                self._start("drew", ALERT_DRAW_FRAMES)
                return
            ahead = (self.room, self.row, self.col + self.facing)
            r = duel.rivals[seen]
            if r.kid.cell == ahead:
                if self.cooldown == 0:
                    self.attack = {"kind": "lunge", "height": self.stance, "phase": "windup",
                                   "resolved": False, "frame": 1, "total": lunge_frames}
                    self.cooldown = LUNGE_COOLDOWN
                return
            if duel.cell_free_for_guard(self, ahead):
                self._start("moved", CHASE_FRAMES, to=ahead)
            return
        if self.armed:                                            # lost sight: back to patrol
            self._start("sheathed", ALERT_DRAW_FRAMES)
            return
        if self.pause:
            self.pause -= 1
            return
        if self.turn_due:
            self.turn_due = False
            self.facing = -self.facing                            # a turn faces round at once
            self._start("turned", P.TURN, to_facing=self.facing)
            return
        at_end = (self.facing > 0 and self.col >= self.c1) or (self.facing < 0 and self.col <= self.c0)
        if self.c0 <= self.col <= self.c1 and at_end:
            self.pause, self.turn_due = PATROL_PAUSE, True
            return
        nxt = (self.room, self.row, self.col + self.facing)
        if duel.cell_free_for_guard(self, nxt):
            self._start("moved", PATROL_FRAMES, to=nxt)
        else:
            self.pause, self.turn_due = PATROL_PAUSE, True

    def snapshot(self) -> dict:
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}


def blocked_between(geom, mech, a: Cell, b: Cell) -> bool:
    """A wall or a closed gate on the row strictly between cells a and b."""
    room, row, c1 = a
    c2 = b[2]
    step = 1 if c2 > c1 else -1
    for c in range(c1 + step, c2, step):
        cell = (room, row, c)
        if geom.tile(cell) == T.WALL or mech.gate_bars(cell):
            return True
    return False

"""The scripted versus baseline (docs/final/MACROS.md, task T05).

A macro policy for `MacroController` (agents/macros.py), labelled `scripted`.
It sees what a seat sees: one observation and the legal list. It is the
competent opponent the PPO rival is compared with (PLAN v2).

Priorities, first match wins:
  1. one heart left and an armed figure close in this row: FLEE;
  2. a figure labelled "rival", or a "guard" with a tell (below): STRIKE it;
  3. a "guard" with a weaker tell: FOLLOW it, to give it the chance to show one;
  4. not disguised and a downed guard in view: DISGUISE (nearest uniform);
  5. not disguised, one standing guard in view: STRIKE it only when the matchup
     favours it (full hearts, and the guard knocked down, or unarmed, walking
     and facing away); an armed guard that has come for me: FLEE the room
     (STRIKE if cornered); otherwise keep away from its sight line (rule 7);
  6. disguised with suspicion above half, or one heart: BLEND;
  7. otherwise SEARCH for the rival (walking, if disguised).

Tells, all visible to a human watching the screen: a "guard" that jumps,
climbs or flips; one that runs without a drawn sword (guards run only when
chasing, sword out); one that stands motionless for over 2 seconds (a
patrolling guard pauses 1 second at the end of its stretch); one facing me in
its sight line that does not draw its sword within 1 second of my being in
view while I am not disguised.
"""

from __future__ import annotations

from agents.macros import MacroController

SIGHT = 5                     # a guard sees 5 cells ahead (VERSUS_SPEC R-V14, a published rule)
STILL_SUSPECT = 24            # frames motionless: a guard pauses 12
STILL_MAYBE = 12
NOREACT_SUSPECT = 12          # frames in sight without drawing: a guard draws within 3
LEAPS = ("jumped", "flipped", "climbed", "hanging", "dropped")
AVOID_FOR = 8                 # decisions to leave a failed macro alone
FLEE_RANGE = 4
BLEND_SUSPICION = 50
FAVOUR_HP = 3                 # full hearts (hearts are 3): a lone-guard fight must not cost one
DANGER_RANGE = 3              # an armed guard this close in my row has come for me
ENGAGED = 2                   # closer than this, fleeing costs more hearts than fighting
WAIT_FOR_BACK = 40            # decisions to wait for a patrolling guard to turn its back


class FigureTracker:
    """Follows each visible guard-looking figure between decisions and keeps the
    tells seen so far. Positions only; no ids exist, tracks are matched by place."""

    def __init__(self, every: int = 6) -> None:
        self.every = every
        self.room = None
        self.tracks: list[dict] = []

    def update(self, obs: dict) -> None:
        if obs["room"] != self.room:
            self.room, self.tracks = obs["room"], []
        me = obs["me"]
        old, new = self.tracks, []
        for f in obs["figures"]:
            if f["kind"] != "guard" or f["posture"] != "standing":
                continue
            best = None
            for t in old:
                if t["row"] == f["row"] and abs(t["col"] - f["col"]) <= 2 and not t.get("used"):
                    if best is None or abs(t["col"] - f["col"]) < abs(best["col"] - f["col"]):
                        best = t
            if best is not None:
                best["used"] = True
            tr = dict(best) if best else {"still": 0, "noreact": 0, "suspect": False}
            tr.pop("used", None)
            tr.update(row=f["row"], col=f["col"])
            m = f["motion"]
            tr["still"] = tr["still"] + self.every if m is None else 0
            if m is not None:
                if m["effect"] in LEAPS or (m["effect"] == "moved" and m["frames"] <= 4
                                            and not f["armed"]):
                    tr["suspect"] = True
            sees_me = (not me["disguised"] and me["row"] == f["row"]
                       and 1 <= (me["col"] - f["col"]) * (1 if f["facing"] == "right" else -1)
                       <= SIGHT and not self._wall_between(obs, f["row"], f["col"], me["col"]))
            if sees_me and not f["armed"] and (m is None or m["effect"] != "drew"):
                tr["noreact"] += self.every
            else:
                tr["noreact"] = 0
            if (tr["still"] > STILL_SUSPECT and not f["armed"]) or tr["noreact"] > NOREACT_SUSPECT:
                tr["suspect"] = True
            new.append(tr)
        self.tracks = new

    @staticmethod
    def _wall_between(obs, row, c1, c2) -> bool:
        lo, hi = sorted((c1, c2))
        return any(obs["tiles"][row][c] == "#" for c in range(lo + 1, hi))

    def suspects(self) -> list[tuple[int, int]]:
        return [(t["row"], t["col"]) for t in self.tracks if t["suspect"]]

    def maybes(self) -> list[tuple[int, int]]:
        return [(t["row"], t["col"]) for t in self.tracks
                if not t["suspect"] and (t["still"] >= STILL_MAYBE or t["noreact"] > 0)]


class VersusBaseline:
    """Macro policy. `choose(obs, legal, status)` -> macro name or (macro, params)."""

    def __init__(self, decision_every: int = 6) -> None:
        self.tracker = FigureTracker(decision_every)
        self.n = 0
        self.avoid: dict[str, int] = {}
        self.waits = 0

    def reset(self, seed: int) -> None:
        self.tracker = FigureTracker(self.tracker.every)
        self.n = 0
        self.avoid = {}
        self.waits = 0

    def _ok(self, macro: str) -> bool:
        return self.n - self.avoid.get(macro, -AVOID_FOR) >= AVOID_FOR

    def choose(self, obs: dict, legal: tuple, status: dict):
        self.n += 1
        if status["state"] == "failed" and status["macro"]:
            self.avoid[status["macro"]] = self.n
        self.tracker.update(obs)
        me = obs["me"]
        figs = [f for f in obs["figures"] if f["posture"] not in ("downed", "dead")]
        if not figs:
            self.waits = 0
        sus = self.tracker.suspects()
        rivals = [f for f in figs if f["kind"] == "rival"]
        near_armed = [f for f in figs if f["row"] == me["row"]
                      and abs(f["col"] - me["col"]) <= FLEE_RANGE
                      and f["posture"] != "knocked_down"       # it cannot act for 10 frames
                      and (f["armed"] or (f["row"], f["col"]) in sus)]       # an unarmed rival cannot cost a heart
        felled = [f for f in figs if f["posture"] == "knocked_down" and f["row"] == me["row"]
                  and abs(f["col"] - me["col"]) <= ENGAGED + 1]
        if felled and not me["disguised"]:
            # A lunge always hits a knocked-down figure (R-V12): finish it inside its 10
            # frames, whatever the hearts (it is what a sweep was thrown for).
            return "STRIKE", {"suspects": [(felled[0]["row"], felled[0]["col"])]}
        if me["hp"] <= 1 and near_armed and self._ok("FLEE"):
            return "FLEE", {"suspects": sus}
        if rivals or sus:
            if self._ok("STRIKE"):
                return "STRIKE", {"suspects": sus}
            return "WAIT"                       # cannot reach it just now: let it come
        maybes = self.tracker.maybes()
        if maybes and self._ok("FOLLOW"):
            return "FOLLOW", {"suspects": maybes}
        if not me["disguised"]:
            if any(f["posture"] == "downed" for f in obs["figures"]) and self._ok("DISGUISE"):
                return "DISGUISE"
            guards = [f for f in figs if f["kind"] == "guard"]
            if len(guards) == 1:
                g = guards[0]
                if self._favours(me, g) and self._ok("STRIKE"):
                    return "STRIKE", {"suspects": [(g["row"], g["col"])]}
                near = g["row"] == me["row"] and g["posture"] == "standing"
                dist = abs(g["col"] - me["col"])
                if near and (g["armed"] or self._in_sight(obs, g)) and dist <= DANGER_RANGE:
                    # It has come for me. Beyond ENGAGED cells there is room to leave
                    # the room; closer, running costs hearts (it lunges as I turn), so
                    # the fight is the lesser risk. Measured in MACROS.md.
                    if dist > ENGAGED and self._ok("FLEE"):
                        return "FLEE", {"suspects": [(g["row"], g["col"])]}
                    if self._ok("STRIKE"):
                        return "STRIKE", {"suspects": [(g["row"], g["col"])]}
                if (self.waits < WAIT_FOR_BACK and me["hp"] >= FAVOUR_HP and not g["armed"]
                        and g["row"] == me["row"] and not self._in_sight(obs, g)):
                    # Not favourable yet, and it cannot see me: let a patrol turn its back.
                    self.waits += 1
                    return "WAIT"
                if (me["hp"] >= FAVOUR_HP and g["row"] > me["row"] and not g["armed"]
                        and self._ok("CLIMB")):
                    # A uniform comes from a downed guard, and a guard is fought on its own
                    # row: go down to it (a drop of one row at a time, hearts kept).
                    return "CLIMB", {"direction": "down"}
        else:
            level = max([s["level"] for s in obs.get("suspicion", [])] or [0])
            if (level > BLEND_SUSPICION or me["hp"] <= 1) and self._ok("BLEND"):
                return "BLEND"
        return "SEARCH", {"prefer": "down"}

    @staticmethod
    def _in_sight(obs: dict, g: dict) -> bool:
        """Would this guard see me now (R-V14: its row, in front, within 5, no wall)?"""
        me = obs["me"]
        ahead = (me["col"] - g["col"]) * (1 if g["facing"] == "right" else -1)
        return (g["row"] == me["row"] and 1 <= ahead <= SIGHT
                and not FigureTracker._wall_between(obs, g["row"], g["col"], me["col"]))

    @staticmethod
    def _favours(me: dict, g: dict) -> bool:
        """A lone guard worth fighting: at full hearts, one that is knocked down (a
        lunge always hits, R-V12) or unarmed, walking, with its back to me (a lunge
        lands before it sees me). An armed guard otherwise wins too often."""
        if me["hp"] < FAVOUR_HP or me["disguised"]:
            return False
        if g["posture"] == "knocked_down":
            return True
        if g["posture"] != "standing" or g["armed"]:
            return False
        behind = (g["col"] > me["col"]) == (g["facing"] == "right")
        return g["row"] == me["row"] and g["col"] != me["col"] and behind


def make_baseline(name: str = "versus-baseline", decision_every: int = 6) -> MacroController:
    return MacroController(VersusBaseline(decision_every), name=name, kind="scripted",
                           decision_every=decision_every)

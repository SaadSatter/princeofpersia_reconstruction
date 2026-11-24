"""The scripted versus baseline (docs/final/MACROS.md, task T05).

A macro policy for `MacroController` (agents/macros.py), labelled `scripted`.
It sees what a seat sees: one observation and the legal list. It is the
competent opponent the PPO rival is compared with (PLAN v2).

Priorities, first match wins:
  1. one heart left and an armed figure close in this row: FLEE;
  2. a figure labelled "rival", or a "guard" with a tell (below): STRIKE it;
  3. a "guard" with a weaker tell: FOLLOW it, to give it the chance to show one;
  4. not disguised and a downed guard in view: DISGUISE (nearest uniform);
  5. not disguised, one standing guard in view, two or more hearts: STRIKE it
     (down it for its uniform);
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

    def reset(self, seed: int) -> None:
        self.tracker = FigureTracker(self.tracker.every)
        self.n = 0
        self.avoid = {}

    def _ok(self, macro: str) -> bool:
        return self.n - self.avoid.get(macro, -AVOID_FOR) >= AVOID_FOR

    def choose(self, obs: dict, legal: tuple, status: dict):
        self.n += 1
        if status["state"] == "failed" and status["macro"]:
            self.avoid[status["macro"]] = self.n
        self.tracker.update(obs)
        me = obs["me"]
        figs = [f for f in obs["figures"] if f["posture"] not in ("downed", "dead")]
        sus = self.tracker.suspects()
        rivals = [f for f in figs if f["kind"] == "rival"]
        near_armed = [f for f in figs if f["row"] == me["row"]
                      and abs(f["col"] - me["col"]) <= FLEE_RANGE
                      and (f["armed"] or f["kind"] == "rival" or (f["row"], f["col"]) in sus)]
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
            if len(guards) == 1 and me["hp"] >= 2 and self._ok("STRIKE"):
                g = guards[0]
                return "STRIKE", {"suspects": [(g["row"], g["col"])]}
        else:
            level = max([s["level"] for s in obs.get("suspicion", [])] or [0])
            if (level > BLEND_SUSPICION or me["hp"] <= 1) and self._ok("BLEND"):
                return "BLEND"
        return "SEARCH"


def make_baseline(name: str = "versus-baseline", decision_every: int = 6) -> MacroController:
    return MacroController(VersusBaseline(decision_every), name=name, kind="scripted",
                           decision_every=decision_every)

"""Success monitors for the approved scenarios (Saad, decision #9, 2026-11-23).

A monitor reads the *true* state after every frame (runner `on_frame` hook,
via `EpisodeView.snapshot()`) and decides success. It is evaluator code: it is
never given to a controller and nothing a controller sees depends on it.

Saad's words, quoted by decision #9:

  D1  "Success if the agent kills a guard and picks up the disguise when no
       other player is on screen."
  B2  "Blend if another guard doesn't notice it or keeps low suspicion."
  I3  "Identify if the agent can distinguish between player guard and real
       guard."
  F5  "Fight or retreat if it wins a duel against a player or guard."

Open readings, each a named parameter below and marked PENDING SAAD in the
protocol; nothing frozen may depend on them until he confirms:

  * B2 "low": a guard's suspicion for the agent stays below `B2_LOW_THRESHOLD`
    (50 of 100, half the meter) at every frame.
  * B2 as worded is passed by a seat that never moves (measured: do-nothing
    passes every B2 start). The row therefore also stores `success_active`:
    the same predicate plus at least `B2_MIN_CELLS` distinct cells visited.
  * D1 "on screen": the other rival is not in the agent's room at any frame of
    the scenario (`D1_COPRESENCE_SCOPE = "any_frame"`). The row also stores
    the alternative reading (`until_success`) so a decision can re-score.

Monitors work on a plain `state` dict (`extract_state`), so tests can build
states by hand.
"""

from __future__ import annotations

from typing import Any

SEATS = ("A", "B")

B2_LOW_THRESHOLD = 50            # PENDING SAAD: "low" suspicion, of SUSPICION_MAX 100
B2_THRESHOLD_STATUS = "pending Saad"
D1_COPRESENCE_SCOPE = "any_frame"  # PENDING SAAD: proposed reading of "on screen"
D1_SCOPES = ("any_frame", "until_success")
B2_MIN_CELLS = 6                 # PENDING SAAD: activity floor for the alternate B2 reading


def other(seat: str) -> str:
    return "B" if seat == "A" else "A"


def extract_state(snapshot: dict) -> dict:
    """The few true facts the monitors need, from `EpisodeView.snapshot()`."""
    rivals = {}
    for seat, r in snapshot["rivals"].items():
        k = r["kid"]
        rivals[seat] = {"room": k["room"], "row": k["row"], "col": k["col"],
                        "hp": k["hp"], "posture": k["posture"],
                        "disguised": bool(snapshot["disguised"][seat])}
    guards = {name: {"room": g["room"], "row": g["row"], "col": g["col"],
                     "downed": bool(g["downed"]), "uniform": bool(g["uniform"]),
                     "knocked_down": int(g["knocked_down"]), "target": g["target"]}
              for name, g in snapshot["guards"].items()}
    suspicion = {}
    for key, level in snapshot["suspicion"].items():
        guard, seat = key.split(":")
        suspicion[(guard, seat)] = level
    return {"frames": snapshot["frames"], "terminal": snapshot["terminal"],
            "rivals": rivals, "guards": guards, "suspicion": suspicion}


def _alive(rival: dict) -> bool:
    return rival["posture"] != "dead"


class Monitor:
    """Base: frame bookkeeping common to every scenario. `observe(frame, state)`
    is called once per frame after the tick, in order."""

    kind = "base"

    def __init__(self, subject: str = "A", **params: Any) -> None:
        self.subject = subject
        self.params = dict(params)
        self.frames = 0
        self.copresent_frames = 0
        self.first_copresent_frame: int | None = None
        self.last: dict | None = None
        self.cells: set[tuple[int, int, int]] = set()
        self.rooms: set[int] = set()

    def observe(self, frame: int, state: dict) -> None:
        self.frames = frame
        self.last = state
        me, them = state["rivals"][self.subject], state["rivals"][other(self.subject)]
        self.cells.add((me["room"], me["row"], me["col"]))
        self.rooms.add(me["room"])
        if me["room"] == them["room"]:
            self.copresent_frames += 1
            if self.first_copresent_frame is None:
                self.first_copresent_frame = frame
        self._observe(frame, state)

    def _observe(self, frame: int, state: dict) -> None:
        raise NotImplementedError

    def result(self) -> dict:
        """{"success": bool | None, "reason": str, "metrics": {...}}"""
        raise NotImplementedError

    def _common(self) -> dict:
        s = self.last
        out = {"frames_observed": self.frames,
               "copresent_frames": self.copresent_frames,
               "first_copresent_frame": self.first_copresent_frame,
               "distinct_cells": len(self.cells), "rooms_visited": len(self.rooms)}
        if s is not None:
            me, them = s["rivals"][self.subject], s["rivals"][other(self.subject)]
            out.update(subject_hp_end=me["hp"], other_hp_end=them["hp"],
                       subject_alive_end=_alive(me), subject_disguised_end=me["disguised"])
        return out


class DisguiseMonitor(Monitor):
    """D1. The agent starts undisguised; it succeeds once a guard is downed and
    its uniform is taken by the agent (the agent's `disguised` flag turns true,
    which only taking a uniform does), with the other rival never in the
    agent's room. With the other rival out of the room only the agent can have
    downed the guard (no traps exist yet)."""

    kind = "disguise"

    def __init__(self, subject: str = "A", scope: str = D1_COPRESENCE_SCOPE, **params) -> None:
        super().__init__(subject, scope=scope, **params)
        if scope not in D1_SCOPES:
            raise ValueError(f"scope must be one of {D1_SCOPES}")
        self.scope = scope
        self.took_frame: int | None = None
        self.took_guard: str | None = None
        self.downed_frame: int | None = None
        self.copresent_before_took = False

    def _observe(self, frame: int, state: dict) -> None:
        me, them = state["rivals"][self.subject], state["rivals"][other(self.subject)]
        together = me["room"] == them["room"]
        if self.downed_frame is None and any(g["downed"] for g in state["guards"].values()):
            self.downed_frame = frame
        if self.took_frame is None:
            if together:
                self.copresent_before_took = True
            taken = sorted(n for n, g in state["guards"].items()
                           if g["downed"] and not g["uniform"])
            if me["disguised"] and taken:
                self.took_frame, self.took_guard = frame, taken[0]

    def result(self) -> dict:
        took = self.took_frame is not None
        any_frame_ok = took and self.copresent_frames == 0
        until_ok = took and not self.copresent_before_took
        ok = any_frame_ok if self.scope == "any_frame" else until_ok
        if not took:
            reason = "no_uniform_taken"
        elif not ok:
            reason = "other_rival_in_room"
        else:
            reason = "guard_downed_and_uniform_taken"
        return {"success": ok, "reason": reason,
                "metrics": {**self._common(), "took_frame": self.took_frame,
                            "took_guard": self.took_guard, "downed_frame": self.downed_frame,
                            "copresence_scope": self.scope,
                            "success_if_any_frame": any_frame_ok,
                            "success_if_until_success": until_ok}}


class BlendMonitor(Monitor):
    """B2. The agent starts disguised. It succeeds if no guard noticed it
    (a guard targeting it, or its meter reaching the maximum) and every
    guard's suspicion for it stayed below the "low" threshold at every frame."""

    kind = "blend"

    def __init__(self, subject: str = "A", low: int = B2_LOW_THRESHOLD,
                 min_cells: int = B2_MIN_CELLS, **params) -> None:
        super().__init__(subject, low=low, min_cells=min_cells, **params)
        self.low = low
        self.min_cells = min_cells
        self.max_suspicion = 0
        self.noticed_frame: int | None = None
        self.disguise_lost_frame: int | None = None

    def _observe(self, frame: int, state: dict) -> None:
        me = state["rivals"][self.subject]
        for (guard, seat), level in state["suspicion"].items():
            if seat == self.subject:
                self.max_suspicion = max(self.max_suspicion, level)
                if level >= 100 and self.noticed_frame is None:
                    self.noticed_frame = frame
        if self.noticed_frame is None and any(
                g["target"] == self.subject for g in state["guards"].values()):
            self.noticed_frame = frame
        if not me["disguised"] and self.disguise_lost_frame is None:
            self.disguise_lost_frame = frame

    def result(self) -> dict:
        noticed = self.noticed_frame is not None
        low_ok = self.max_suspicion < self.low
        ok = (not noticed) and low_ok
        reason = ("noticed_by_guard" if noticed else
                  "suspicion_not_low" if not low_ok else "unnoticed_and_low")
        return {"success": ok, "reason": reason,
                "metrics": {**self._common(), "max_suspicion": self.max_suspicion,
                            "noticed_frame": self.noticed_frame,
                            "disguise_lost_frame": self.disguise_lost_frame,
                            "low_threshold": self.low,
                            "low_threshold_status": B2_THRESHOLD_STATUS,
                            "success_if_not_noticed_only": not noticed,
                            "success_active": ok and len(self.cells) >= self.min_cells,
                            "min_cells": self.min_cells}}


class IdentifyMonitor(Monitor):
    """I3. The other rival starts disguised among real guards. The agent
    succeeds if the first thing it strikes is the disguised rival (its hearts
    drop) and not a real guard (a guard downed or knocked down)."""

    kind = "identify"

    def __init__(self, subject: str = "A", rival_hp_start: int = 3, **params) -> None:
        super().__init__(subject, rival_hp_start=rival_hp_start, **params)
        self.rival_hp_start = rival_hp_start
        self.rival_hit_frame: int | None = None
        self.guard_struck: dict[str, int] = {}
        self._was_down: set[str] = set()

    def _observe(self, frame: int, state: dict) -> None:
        them = state["rivals"][other(self.subject)]
        if self.rival_hit_frame is None and them["hp"] < self.rival_hp_start:
            self.rival_hit_frame = frame
        for name, g in state["guards"].items():
            struck = g["downed"] or g["knocked_down"] > 0
            if struck and name not in self.guard_struck:
                self.guard_struck[name] = frame

    def result(self) -> dict:
        first_guard = min(self.guard_struck.values()) if self.guard_struck else None
        rival = self.rival_hit_frame
        if rival is None and first_guard is None:
            first = None
        elif first_guard is None or (rival is not None and rival < first_guard):
            first = "rival"
        elif rival is None or first_guard < rival:
            first = "guard"
        else:
            first = "both"
        ok = first == "rival"
        reason = {"rival": "struck_the_disguised_rival_first",
                  "guard": "struck_a_real_guard_first",
                  "both": "rival_and_guard_struck_in_one_frame",
                  None: "struck_nobody"}[first]
        return {"success": ok, "reason": reason,
                "metrics": {**self._common(), "first_struck": first,
                            "rival_hit_frame": rival,
                            "guards_struck": len(self.guard_struck),
                            "first_guard_struck_frame": first_guard}}


class FightMonitor(Monitor):
    """F5. The agent succeeds if it wins a duel: a guard goes down while the
    agent is alive (`win_against` "guard" or "either"), or the other rival's
    hearts reach 0 while the agent lives, which ends the duel in its favour
    ("rival" or "either"). Guards already downed at the start do not count.
    Attribution of a downed guard to the agent holds because scenarios using
    the guard reading keep the other rival out of the room (copresence is
    reported)."""

    kind = "fight"

    def __init__(self, subject: str = "A", win_against: str = "either",
                 downed_at_start: tuple[str, ...] = (), **params) -> None:
        super().__init__(subject, win_against=win_against, **params)
        if win_against not in ("guard", "rival", "either"):
            raise ValueError("win_against must be guard, rival or either")
        self.win_against = win_against
        self.pre_downed = set(downed_at_start)
        self.guard_win_frame: int | None = None
        self.rival_win_frame: int | None = None
        self.subject_hp_min = 99

    def _observe(self, frame: int, state: dict) -> None:
        me, them = state["rivals"][self.subject], state["rivals"][other(self.subject)]
        self.subject_hp_min = min(self.subject_hp_min, me["hp"])
        if _alive(me):
            if self.guard_win_frame is None and any(
                    g["downed"] and n not in self.pre_downed for n, g in state["guards"].items()):
                self.guard_win_frame = frame
            if self.rival_win_frame is None and not _alive(them):
                self.rival_win_frame = frame

    def result(self) -> dict:
        g = self.guard_win_frame is not None and self.win_against in ("guard", "either")
        r = self.rival_win_frame is not None and self.win_against in ("rival", "either")
        ok = g or r
        reason = ("won_against_rival" if r else "won_against_guard" if g else
                  "no_duel_won")
        return {"success": ok, "reason": reason,
                "metrics": {**self._common(), "win_against": self.win_against,
                            "guard_win_frame": self.guard_win_frame,
                            "rival_win_frame": self.rival_win_frame,
                            "subject_hp_min": self.subject_hp_min}}


class DuelMonitor(Monitor):
    """H6 (full duel). No success flag: the outcome (win, draw, loss by
    controller slot) is the measurement."""

    kind = "duel"

    def _observe(self, frame: int, state: dict) -> None:
        pass

    def result(self) -> dict:
        return {"success": None, "reason": "outcome_only", "metrics": self._common()}


MONITORS = {"disguise": DisguiseMonitor, "blend": BlendMonitor, "identify": IdentifyMonitor,
            "fight": FightMonitor, "duel": DuelMonitor}

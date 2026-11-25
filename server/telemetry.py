"""Playtest telemetry (T20, decisions #67 and #68): one JSON Lines log per room, duel and seat.

Off by default. It is a pure reader: it calls only `observe`, `legal_actions`,
`outcome` and (T20-fix1, decision #81) `started_move` of the episode, never `step` or
`tick`, and never touches the engine RNG or `GameState`. `started_move(seat)` is the one
read beyond the frontend's: the move the engine actually started for a seat on the last
tick, after its own rewrites (R-V10, R-V22, R-V35) and stale drops. It is the seat's own
input as resolved by the engine; it carries nothing about the other seat. Wall-clock seconds come from
the clock the caller passes in (the server's), never from the engine. So a duel's
trace and state hash are the same with and without it (tests/test_t20_telemetry.py).

Knowledge boundary (#68 item 3). A seat's log is built from that seat's own
`observe(seat)` and its own inputs, plus the fixed status text its client is shown
(pause, forfeit, outcome). Nothing about the other seat that its observation hides:
no disguise identity, no trap ownership. A disguised rival is a "guard" in the
other's view, so nothing is logged about it. A rival's trap never appears in the
other seat's log, even when it hurts that seat (that is a `heart_lost` with a cause
read from the seat's own `last_result`). The seed is in each file's header: the files
are host-side only and never sent to a client. The one combined summary per duel
(`...-host.json`) is host-side and may read both seats.

File: `<date>-<room>-<duel n>-<seat>.jsonl`. Line 1 is a header, then one event per
line: {"t": tick, "s": seconds since duel start, "seat", "type", ...}. The tick is
the duel's frame count after the tick that produced the event (0 at the start).

Inputs and moves are different things. An `action` row is an input the seat asked for
(accepted into the queue, or refused): a held key makes one per tick. A `move` row is
the move the engine started, once per start, and is the only source of "how often was
this used". A `move` row's `effect` is that move's own planned effect. An `action` row
has no effect field.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Callable

from pop.versus import BREAKS_DISGUISE, DUEL_FRAMES, SEATS, TICKS_PER_SECOND

log = logging.getLogger("server.telemetry")

SCHEMA = 2        # 2: `move` rows; `action` rows lose `effect` (T20-fix1)
# Proposal for Saad (decision #68): a spell with no accepted action for this long is an
# `idle` event. Measured in duel ticks, so a pause never counts as idle time.
IDLE_THRESHOLD_S = 3.0
IDLE_TICKS = int(IDLE_THRESHOLD_S * TICKS_PER_SECOND)
RECENT_TICKS = 12      # a sword that leaves the hand within this long of THROW/SHEATHE/TAKE was that

EVENT_TYPES = ("duel_start", "action", "move", "room", "disguise_on", "disguise_broken", "sword_drop",
               "sword_pickup", "trap_rigged", "trap_sprung", "hit", "heart_lost", "idle", "pause",
               "disconnect", "reconnect", "forfeit", "duel_end", "rematch")

DEFAULT_DIR = "traces/playtest"

# One physical key can resolve to two actions in turn: the draw key is DRAW when unarmed and
# SHEATHE when armed, and up plus a direction is JUMP_x until the rival is running, then
# RUN_JUMP_x (web/bridge.py seat_input). Holding such a key changes the action it asks for,
# so for "is this the same held key" those are one key (T20-fix2, E3).
_SAME_KEY = {"SHEATHE": "DRAW", "RUN_JUMP_LEFT": "JUMP_LEFT", "RUN_JUMP_RIGHT": "JUMP_RIGHT"}
# A stance change is never an engine move start (it begins at once beside any move, R-V03), so
# it has no `move` row. Its accepted `action` row is the use, and carries `repeat` while the
# key stays held (T20-fix2, item 4: `block` was counted from `move` rows and read 0).
_STANCES = ("STANCE_UP", "STANCE_DOWN")


def _key(action: str) -> str:
    return _SAME_KEY.get(action, action)


def _today() -> str:
    return datetime.date.today().isoformat()


def _view(obs: dict) -> dict:
    """The facts this module keeps from one seat's own observation."""
    me = obs["me"]
    res = obs["last_result"] or {}
    return {
        "room": obs["room"], "disguised": bool(me["disguised"]), "armed": bool(me["armed"]),
        "hp": me["hp"], "traps": {(t["row"], t["col"]): t["kind"] for t in obs["my_traps"]},
        "traps_left": me["traps_left"], "fell": bool(res.get("fell_rows", 0)) or res.get("effect") == "fell",
        "motion": (me["motion"] or {}).get("effect"), "last_effect": res.get("effect"),
        # someone (rival or guard, as the seat sees them) or a flying sword is in this room
        "company": bool(obs["figures"]) or any(x["flying"] for x in obs["swords"]),
    }


def seat_outcome(reason: str | None, seat: str) -> dict:
    """One seat's own view of the engine's terminal reason ("won:A", "draw:..."), as the
    bridge shows it to that seat (web/bridge.py `_outcome`)."""
    if reason is None:
        return {"result": None, "reason": None}
    result = "draw" if reason.startswith("draw") else "won" if reason == f"won:{seat}" else "lost"
    return {"result": result, "reason": reason}


class DuelRecorder:
    """The logs of one duel, one file per human seat. Never raises into the game."""

    def __init__(self, ep, seats: tuple[str, ...], paths: dict[str, Path], host_path: Path,
                 headers: dict[str, dict], now: float):
        self.ep, self.seats = ep, tuple(seats)
        self.paths, self.host_path, self.headers = paths, host_path, headers
        self.t0, self.t = now, 0
        self.dead = False
        self.ended = False
        self._refused: list[tuple[str, str, str]] = []
        self._prev: dict[str, dict] = {}
        self._last_accept = {s: 0 for s in self.seats}
        self._idle_open = {s: False for s in self.seats}
        self._recent: dict[str, list[tuple[int, str]]] = {s: [] for s in self.seats}  # own inputs
        self._pressed = {s: False for s in self.seats}
        self._counts: dict[str, dict[str, int]] = {s: {} for s in self.seats}
        self._ended_by = None
        self._forfeit_seat = None
        self._paused = False
        # A held key: [id, action, last tick it was asked]; and the (hold id, move) of the
        # last start. A start fed by the same hold as the last start of that move is a
        # repeat of one held key (the engine honours an input queued while a move runs).
        self._hold: dict[str, list | None] = {s: None for s in self.seats}
        self._holds = 0
        self._start_hold: dict[str, tuple[int, str] | None] = {s: None for s in self.seats}

    # --- writing ---------------------------------------------------------------
    def _write(self, seat: str, obj: dict) -> None:
        if self.dead:
            return
        try:
            with open(self.paths[seat], "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, separators=(",", ":")) + "\n")
        except OSError:
            log.exception("telemetry write failed; this duel's logs stop here")
            self.dead = True

    def _emit(self, seat: str, type_: str, now: float, **fields) -> None:
        ev = {"t": self.t, "s": round(max(0.0, now - self.t0), 3), "seat": seat, "type": type_}
        ev.update(fields)
        self._counts[seat][type_] = self._counts[seat].get(type_, 0) + 1
        self._write(seat, ev)

    # --- the duel's life ---------------------------------------------------------
    def start(self) -> None:
        for seat in self.seats:
            self._write(seat, self.headers[seat])
        for seat in self.seats:
            v = self._prev[seat] = _view(self.ep.observe(seat))
            self._emit(seat, "duel_start", self.t0, room=v["room"], hearts=v["hp"],
                       armed=v["armed"], traps_left=v["traps_left"])

    def refused(self, seat: str, action: str, error: str = "not legal now") -> None:
        """An input a seat asked for that was not legal this tick (the frontend never
        submits it). Written with the tick's other events."""
        if seat in self.seats:
            self._refused.append((seat, action, error))

    def after_tick(self, accepted: list[tuple[str, str]], now: float) -> None:
        """Call after `ep.tick()`. accepted: [(seat, action)] this tick (the episode log)."""
        if self.ended:
            return
        self.t = self.ep.outcome()["frames"]
        refused, self._refused = self._refused, []
        for seat in self.seats:
            old = self._prev[seat]
            v = _view(self.ep.observe(seat))
            mine = [a for s, a in accepted if s == seat]
            started = self.ep.started_move(seat)
            held = self._note_asked(seat, [a for a in mine] + [a for s, a, _ in refused if s == seat])
            # R-V35: the engine cancelled a direction for this jump; the summary drops it
            grace = {"grace": True} if started is not None and started.rewrite == "grace" else {}
            for a in mine:
                again = {"repeat": True} if held and a in _STANCES else {}
                self._emit(seat, "action", now, action=a, accepted=True, started=started,
                           **grace, **again)
            for s, a, err in refused:
                if s == seat:
                    self._emit(seat, "action", now, action=a, accepted=False, error=err)
            if started is not None:
                # the effect is the started move's own plan, never an earlier move's
                repeat = {"repeat": True} if self._is_repeat(seat, started) else {}
                self._emit(seat, "move", now, move=started, effect=v["motion"], **grace, **repeat)
            self._diff(seat, old, v, mine, now)
            self._idle(seat, bool(mine), now)
            self._recent[seat] = [(t, a) for t, a in self._recent[seat]
                                  if self.t - t <= RECENT_TICKS] + [(self.t, a) for a in mine]
            self._prev[seat] = v

    def _note_asked(self, seat: str, asked: list[str]) -> bool:
        """Track the key the seat is holding: the same action asked on consecutive ticks
        (accepted or refused, so a tick where the key was not legal does not break it).
        True if this tick continues a hold that began earlier."""
        if not asked:
            return False
        cur, hold = asked[-1], self._hold[seat]
        if hold is not None and _key(hold[1]) == _key(cur) and self.t - hold[2] <= 1:
            hold[2] = self.t
            return True
        self._holds += 1
        self._hold[seat] = [self._holds, cur, self.t]
        return False

    def _is_repeat(self, seat: str, started: str) -> bool:
        hold = self._hold[seat]
        hid = hold[0] if hold else None
        last, self._start_hold[seat] = self._start_hold[seat], (hid, started)
        return hid is not None and last is not None and last[0] == hid and _key(last[1]) == _key(started)

    def _diff(self, seat: str, old: dict, v: dict, mine: list[str], now: float) -> None:
        if v["room"] != old["room"]:
            self._emit(seat, "room", now, room=v["room"])
        lost = old["hp"] - v["hp"]
        if v["disguised"] and not old["disguised"]:
            self._emit(seat, "disguise_on", now)
        if old["disguised"] and not v["disguised"]:
            cause = next((f"action:{a}" for a in mine if a in BREAKS_DISGUISE), None)
            self._emit(seat, "disguise_broken", now,
                       cause=cause or ("heart_lost" if lost > 0 else "suspicion"))
        recent = {a for t, a in self._recent[seat] if self.t - t <= RECENT_TICKS} | set(mine)
        if old["armed"] and not v["armed"] and not recent & {"SHEATHE", "TAKE"}:
            # Not put away or hidden under a uniform by this seat: thrown or knocked away.
            self._emit(seat, "sword_drop", now,
                       cause="thrown" if "THROW" in recent else "knocked_away")
        if not old["armed"] and v["armed"] and v["last_effect"] == "took_sword":
            self._emit(seat, "sword_pickup", now)
        if v["room"] == old["room"]:        # a trap out of sight is not seen
            for cell in sorted(v["traps"].keys() - old["traps"].keys()):
                self._emit(seat, "trap_rigged", now, row=cell[0], col=cell[1],
                           kind=v["traps"][cell], traps_left=v["traps_left"])
            for cell in sorted(old["traps"].keys() - v["traps"].keys()):
                self._emit(seat, "trap_sprung", now, row=cell[0], col=cell[1], whose="mine")
        if lost > 0:
            # What the seat's own view shows: a fall, a strike with someone (or a flying
            # sword) in the room, else the room itself (spikes and the like).
            cause = "fall" if v["fell"] else "strike" if v["company"] else "hazard"
            if cause == "strike":
                self._emit(seat, "hit", now, hearts=v["hp"])
            self._emit(seat, "heart_lost", now, lost=lost, hearts=v["hp"], cause=cause)

    def _idle(self, seat: str, acted: bool, now: float) -> None:
        if acted:
            if self._idle_open[seat]:
                self._emit(seat, "idle", now, phase="end",
                           seconds=round((self.t - self._last_accept[seat]) / TICKS_PER_SECOND, 3))
                self._idle_open[seat] = False
            self._last_accept[seat] = self.t
        elif not self._idle_open[seat] and self.t - self._last_accept[seat] >= IDLE_TICKS:
            self._idle_open[seat] = True
            self._emit(seat, "idle", now, phase="start", since_t=self._last_accept[seat],
                       threshold_s=IDLE_THRESHOLD_S)

    # --- connection and end ------------------------------------------------------
    def disconnect(self, seat: str, now: float) -> None:
        if seat in self.seats:
            self._emit(seat, "disconnect", now)

    def reconnect(self, seat: str, now: float) -> None:
        if seat in self.seats:
            self._emit(seat, "reconnect", now)

    def pause(self, starting: bool, now: float) -> None:
        if starting == self._paused:
            return
        self._paused = starting
        for seat in self.seats:          # both clients are shown the paused text
            self._emit(seat, "pause", now, phase="start" if starting else "end")

    def forfeit(self, loser: str, now: float) -> None:
        self.pause(False, now)           # a paused duel that ends by forfeit closes its pause (F3)
        self._forfeit_seat, self._ended_by = loser, "forfeit"
        for seat in self.seats:          # both clients are told the result
            self._emit(seat, "forfeit", now, by="me" if seat == loser else "rival")

    def end(self, outcomes: dict[str, dict], now: float, reason: str | None = None) -> None:
        """outcomes: each seat's own client-visible outcome ({"result", "reason"})."""
        if self.ended:
            return
        self.ended = True
        self.pause(False, now)           # an abandoned paused duel closes its pause too
        self._ended_by = self._ended_by or reason or "outcome"
        for seat in self.seats:
            if self._idle_open[seat]:
                self._emit(seat, "idle", now, phase="end",
                           seconds=round((self.t - self._last_accept[seat]) / TICKS_PER_SECOND, 3))
                self._idle_open[seat] = False
            o = outcomes.get(seat) or {}
            self._emit(seat, "duel_end", now, result=o.get("result"),
                       reason=reason or o.get("reason"), frames=self.t)
        self._write_host()

    def rematch(self, seat: str, pressed: bool, now: float) -> None:
        if seat in self.seats:
            if pressed:
                self._pressed[seat] = True
            self._emit(seat, "rematch", now, pressed=pressed)

    def close(self, now: float, reason: str = "abandoned") -> None:
        """The room closed or the duel is replaced. A duel still running is abandoned;
        a seat that never pressed rematch is logged as not pressed."""
        if not self.ended:
            self.end({}, now, reason=reason)
            self._write_host()
            return
        if reason in ("restart",):
            return
        for seat in self.seats:
            if not self._pressed[seat]:
                self._pressed[seat] = True      # once
                self._emit(seat, "rematch", now, pressed=False)
        self._write_host()

    def _write_host(self) -> None:
        if self.dead:
            return
        out = self.ep.outcome()
        doc = {"schema": SCHEMA, "seed": self.ep.seed, "room": self.headers[self.seats[0]]["room"],
               "duel": self.headers[self.seats[0]]["duel"], "frames": out["frames"],
               "engine_reason": out["reason"], "ended_by": self._ended_by,
               "forfeit_seat": self._forfeit_seat, "events": self._counts}
        try:
            self.host_path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        except OSError:
            log.exception("telemetry host summary failed")


class Telemetry:
    """One room's telemetry: numbers its duels and makes their recorders."""

    def __init__(self, directory: str | Path = DEFAULT_DIR, room: str = "HOME",
                 info: dict | None = None, today: Callable[[], str] = _today):
        self.dir, self.room = Path(directory), room
        self.info = dict(info or {})
        self.today = today
        self.n = 0

    def new_duel(self, ep, seats: tuple[str, ...], rival: str, now: float) -> DuelRecorder | None:
        """Start the next duel's logs (the episode has just been reset). None on an
        unwritable directory: telemetry never stops a duel."""
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            day = self.today()
            while True:                                  # a restart never appends to old files
                self.n += 1
                stem = f"{day}-{self.room}-{self.n:03d}"
                if not any((self.dir / f"{stem}-{s}.jsonl").exists() for s in SEATS):
                    break
            header = {"type": "header", "schema": SCHEMA, **self.info, "seed": ep.seed,
                      "rival": rival, "room": self.room, "duel": self.n,
                      "duel_frames": DUEL_FRAMES, "ticks_per_second": TICKS_PER_SECOND,
                      "idle_threshold_s": IDLE_THRESHOLD_S}
            rec = DuelRecorder(ep, seats, {s: self.dir / f"{stem}-{s}.jsonl" for s in seats},
                               self.dir / f"{stem}-host.json",
                               {s: {**header, "seat": s} for s in seats}, now)
            rec.start()
            return rec
        except OSError:
            log.exception("telemetry could not start for room %s", self.room)
            return None

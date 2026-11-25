"""The online duel's rules (T13): seats, tokens, held keys, pacing, disconnect, rematch.

One `Match` holds the only `WebGame` (and so the only `GameState`). It is pure
logic: every call is given `now` (seconds, any monotonic clock), so tests
inject time and wall time never reaches the engine. `server/app.py` moves its
messages over WebSockets.

What a client may do (and all it may do): `join` (with an optional seat
token), send `{"type": "keys", "keys": [...]}` (physical key names from either
control set; they steer the sender's own seat only) and `{"type": "rematch"}`. Everything else is ignored. What a
client receives is one seat's payload (`web/bridge.py` `_seat_payload`:
`seat_view`, `draw`, `hud`, `outcome`) and fixed status text; nothing else
(docs/final/ONLINE_PLAY.md).

Input resolution is `web/bridge.py` `WebGame.tick`: this module only feeds it
the held keys of each seat: either control set (decision #55), renamed into
that seat's own set for the two-seat game.
"""

from __future__ import annotations

import hmac
import json
import secrets
from typing import Callable

from pop.versus import SEATS, TICKS_PER_SECOND, VersusEpisode
from web.bridge import ALL_KEY_NAMES, WebGame, make_game, to_seat_keys

from .rival import DEFAULT_BUDGET_S, TimeLimitedRival
from .trace import state_hash

TICK_S = 1.0 / TICKS_PER_SECOND
MAX_CATCH_UP = 3                 # a stall never fast-forwards the duel
FORFEIT_GRACE_S = 15.0           # decision #38
MAX_MESSAGE_CHARS = 512          # a keys message is under 200
MAX_KEYS = 16
_EPS = 1e-9

WAITING_TEXT = "Waiting for rival to join"
PAUSED_TEXT = "Rival disconnected, waiting up to 15 s"
REMATCH_WAIT_TEXT = "Waiting for rival…"
REMATCH_WANTS_TEXT = "Rival wants a rematch"
STATE_FIELDS = ("rival", "seat_view", "draw", "hud", "outcome")


class Match:
    def __init__(self, seed: int = 0, rival: str | None = None,
                 episode: VersusEpisode | None = None,
                 token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(24),
                 on_finish: Callable[[dict], None] | None = None,
                 neutral: bool = False, rival_budget_s: float = DEFAULT_BUDGET_S,
                 honest: bool = False):
        if rival not in (None, "baseline", "ai"):
            raise ValueError("rival must be None, 'baseline' or 'ai'")
        self.rival = rival
        self.honest = honest                       # T22 (#88): honest mode names (agents/modes.py), not "AI rival: ..."
        self.neutral = neutral                     # label the AI seat just "Rival"
        self._rival_budget_s = rival_budget_s
        self.seed = episode.seed if episode is not None else seed
        self._token_factory = token_factory
        self._on_finish = on_finish
        self._fresh_episode = episode
        self.past_traces: list[dict] = []
        self._reset_lobby()

    # --- construction ---------------------------------------------------------
    def _new_game(self) -> WebGame:
        if self.rival in ("baseline", "ai"):
            g = make_game("human_vs_ai", "A", self.seed, self.rival, neutral=self.neutral,
                          honest=self.honest)
            # The bridge calls its rival synchronously with no limit: bound it so a
            # slow controller never stalls the 12 Hz loop for the human seat.
            g.rival = TimeLimitedRival(g.rival, self._rival_budget_s)
        else:
            g = WebGame(mode="local_two_players", seed=self.seed, episode=self._fresh_episode)
        self._fresh_episode = None
        return g

    def close(self) -> None:
        """Stop the AI seat's worker thread (called on lobby reset and server exit)."""
        rival = getattr(getattr(self, "game", None), "rival", None)
        if hasattr(rival, "close"):
            rival.close()

    def _reset_lobby(self) -> None:
        self.close()
        self.game = self._new_game()
        self.state = "waiting"                    # waiting | playing | paused | ended
        self.tokens: dict[str, str] = {}          # seat -> token
        self.connected: dict[str, bool] = {}
        self.held: dict[str, set[str]] = {s: set() for s in SEATS}
        self.deadline: dict[str, float] = {}      # seat -> forfeit time
        self.forfeit: str | None = None
        self.rematch_pressed: set[str] = set()
        self._ticks: list[list[tuple[str, str]]] = []
        self._next_tick = 0.0
        self._outbox: dict[str, list[dict]] = {s: [] for s in SEATS}
        self._finished = False
        self._fallbacks: list[dict] = []           # the AI seat's fallbacks (server only)
        self._seen_fallbacks = (0, 0, 0)
        self._duel_fallbacks_from = 0

    @property
    def episode(self) -> VersusEpisode:
        return self.game.episode

    @property
    def human_seats(self) -> tuple[str, ...]:
        return ("A",) if self.rival else SEATS

    # --- joining and leaving ----------------------------------------------------
    def join(self, token: object, now: float) -> dict:
        if token is not None and token != "":
            seat = self._seat_of(token)
            if seat is None:
                return {"ok": False, "code": "bad_token"}
            self.connected[seat] = True
            self.deadline.pop(seat, None)
            self.held[seat] = set()
            if self.state == "paused" and all(self.connected.get(s) for s in self.tokens):
                self.state, self._next_tick = "playing", now + TICK_S
            self._push_state(seat)
            self._announce()
            return {"ok": True, "seat": seat, "token": self.tokens[seat]}
        seat = next((s for s in self.human_seats if s not in self.tokens), None)
        if seat is None:
            return {"ok": False, "code": "full"}
        self.tokens[seat] = self._token_factory()
        self.connected[seat] = True
        if len(self.tokens) == len(self.human_seats) and self.state == "waiting":
            self.state, self._next_tick = "playing", now + TICK_S
        self._push_state(seat)
        self._announce()
        return {"ok": True, "seat": seat, "token": self.tokens[seat]}

    def _seat_of(self, token: object) -> str | None:
        if not isinstance(token, str) or len(token) > 200:
            return None
        found = None
        for seat, t in self.tokens.items():       # compare every seat: no early exit
            if hmac.compare_digest(t.encode(), token.encode()):
                found = seat
        return found

    def connection_lost(self, seat: str, now: float) -> None:
        if seat not in self.tokens or not self.connected.get(seat):
            return
        self.connected[seat] = False
        self.held[seat] = set()
        self.rematch_pressed.discard(seat)
        if self.state == "waiting":
            del self.tokens[seat]                 # nothing started: the seat is free again
            del self.connected[seat]
        elif self.state in ("playing", "paused"):
            self.state = "paused"
            self.deadline[seat] = now + FORFEIT_GRACE_S
        elif not any(self.connected.values()):    # ended and everyone left
            self._reset_lobby()
            return
        self._announce()

    # --- what a client sends -----------------------------------------------------
    def receive(self, seat: str, raw: object, now: float) -> None:
        """One client message. Anything unexpected is ignored without an error."""
        if seat not in self.tokens or not isinstance(raw, str) or len(raw) > MAX_MESSAGE_CHARS:
            return
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return
        if "seat" in msg and msg["seat"] != seat:
            return                                 # claims another seat
        kind = msg.get("type")
        if kind == "keys":
            self._set_keys(seat, msg.get("keys"))
        elif kind == "rematch":
            self._press_rematch(seat, now)

    def _set_keys(self, seat: str, keys: object) -> None:
        if not isinstance(keys, list) or len(keys) > MAX_KEYS:
            return
        # Decision #55: either control set drives the sender's own seat.
        self.held[seat] = {k for k in keys if isinstance(k, str) and k in ALL_KEY_NAMES}

    def _press_rematch(self, seat: str, now: float) -> None:
        if self.state != "ended" or not self.connected.get(seat):
            return
        self.rematch_pressed.add(seat)
        everyone = all(s in self.rematch_pressed for s in self.human_seats)
        if everyone and all(self.connected.get(s) for s in self.human_seats):
            self._restart(now)
        else:
            self._announce()

    def _restart(self, now: float) -> None:
        self.past_traces.append(self.trace())      # same seed again (decision #25)
        self.game.rematch()
        self._ticks = []
        self._duel_fallbacks_from = len(self._fallbacks)   # each duel's trace carries only its own
        self._seen_fallbacks = self._fallback_counts()
        self.forfeit = None
        self.rematch_pressed = set()
        self.held = {s: set() for s in SEATS}
        self._finished = False
        self.state, self._next_tick = "playing", now + TICK_S
        for seat in self.human_seats:
            self._push_state(seat)
        self._announce()

    # --- the clock ----------------------------------------------------------------
    def advance(self, now: float) -> None:
        if self.state == "paused":
            lost = [s for s, t in sorted(self.deadline.items()) if now >= t]
            if lost:
                self._end_by_forfeit(lost[0])
            return
        if self.state != "playing":
            return
        n = 0
        while now + _EPS >= self._next_tick and self.state == "playing":
            if n == MAX_CATCH_UP:
                self._next_tick = now + TICK_S     # drop the backlog, never replay it
                break
            self._tick()
            self._next_tick += TICK_S
            n += 1

    def _tick(self) -> None:
        if self.episode.outcome()["status"] == "terminal":
            self._finish()
            return
        if self.rival:                    # one human seat: the bridge reads both sets itself
            keys = {name: True for seat in self.human_seats for name in self.held[seat]}
        else:                             # two seats: rename each seat's keys into its own set
            keys = {name: True for seat in self.human_seats
                    for name in to_seat_keys(seat, self.held[seat])}
        self.game.press(keys)
        before = len(self.episode.log)
        payload = self.game.tick()
        self._ticks.append([(seat, action) for _, seat, action in self.episode.log[before:]])
        self._note_fallbacks()
        ended = self.episode.outcome()["status"] == "terminal"
        for seat in self.human_seats:
            if self.connected.get(seat):
                self._outbox[seat].append(self._state_message(seat, payload))
        if ended:
            self._finish()

    def _fallback_counts(self) -> tuple[int, int, int]:
        rival = self.game.rival if self.rival else None
        inner = getattr(rival, "inner", None)
        return (getattr(rival, "slow", 0), getattr(inner, "fallbacks", 0),
                getattr(inner, "policy_errors", 0))

    def _note_fallbacks(self) -> None:
        """Log each fallback of the server's AI seat as it happens, labelled as such.
        Kept in the trace and read by the server log; never sent to a client."""
        rival = self.game.rival if self.rival else None
        if rival is None:
            return
        now = self._fallback_counts()
        # a rival reset (rematch) may restart its own counters: count from the new zero
        self._seen_fallbacks = tuple(min(a, b) for a, b in zip(self._seen_fallbacks, now))
        for i, reason in enumerate(("slow_answer_replaced_by_wait", "controller_failed_no_input",
                                    "policy_error")):
            for _ in range(now[i] - self._seen_fallbacks[i]):
                self._fallbacks.append({"frame": self.episode.outcome()["frames"], "seat": "B",
                                        "source": "fallback", "reason": reason})
        self._seen_fallbacks = now

    def _finish(self) -> None:
        self.state = "ended"
        self._announce()
        self._record()

    def _end_by_forfeit(self, seat: str) -> None:
        self.forfeit = seat
        self.deadline.clear()
        self.state = "ended"
        for s in self.human_seats:
            self._push_state(s)
        self._announce()
        self._record()

    def _record(self) -> None:
        if self._finished:
            return
        self._finished = True
        if self._on_finish is not None:
            self._on_finish(self.trace())

    # --- what a client receives ------------------------------------------------------
    def _state_message(self, seat: str, payload: dict) -> dict:
        p = payload if self.rival else payload["seats"][seat]
        msg = {"type": "state", "seat": seat}
        msg.update({k: p[k] for k in STATE_FIELDS if k in p})
        if self.forfeit is not None:
            lost = self.forfeit == seat
            msg["outcome"] = {"status": "terminal",
                              "reason": "you_disconnected" if lost else "rival_disconnected",
                              "result": "lost" if lost else "won"}
        return msg

    def _push_state(self, seat: str) -> None:
        if seat in self.human_seats and self.connected.get(seat):
            self._outbox[seat].append(self._state_message(seat, self.game.payload()))

    def status(self, seat: str) -> dict:
        """Fixed text chosen by connection state alone, never by game state."""
        text, rematch = "", "none"
        if self.state == "waiting":
            text = WAITING_TEXT
        elif self.state == "paused":
            text = PAUSED_TEXT
        elif self.state == "ended":
            others = [s for s in self.human_seats if s != seat]
            if seat in self.rematch_pressed:
                rematch, text = "waiting", REMATCH_WAIT_TEXT
            elif any(s in self.rematch_pressed for s in others):
                rematch, text = "rival_wants", REMATCH_WANTS_TEXT
        return {"type": "status", "state": self.state, "text": text, "rematch": rematch}

    def _announce(self) -> None:
        for seat in self.human_seats:
            if self.connected.get(seat):
                self._outbox[seat].append(self.status(seat))

    def drain(self, seat: str) -> list[dict]:
        out, self._outbox[seat] = self._outbox[seat], []
        return out

    # --- the trace (server only) ----------------------------------------------------------
    def trace(self) -> dict:
        return {"seed": self.seed, "rival": self.rival,
                "ticks": [[list(x) for x in t] for t in self._ticks],
                "fallbacks": list(self._fallbacks[self._duel_fallbacks_from:]),
                "forfeit": self.forfeit, "outcome": self.episode.outcome(),
                "state_hash": state_hash(self.episode)}

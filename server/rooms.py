"""Room codes, room records and the join rate limit (T18, decision #52).

Pure helpers with no sockets, so tests inject a clock and a code source. A room is one
`Match` (the only `GameState` of that duel), its seat links and sockets, and the times
that decide when it expires. Nothing here is ever sent to a client except a room's own
code, in that room's own `hello`.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from .match import FORFEIT_GRACE_S, Match

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ"     # A to Z without I and O (easy to read aloud)
CODE_LENGTH = 4
ROOM_WAIT_S = 600.0                            # no second player this long after creation: expires
EMPTY_EXPIRY_S = FORFEIT_GRACE_S               # nobody connected this long (#38 window): expires
MAX_ROOMS = 50                                 # proposal: a cap so a flood of Create cannot fill memory
MAX_FAILED_JOINS = 10                          # proposal for Saad: per connection ...
FAILED_JOIN_WINDOW_S = 60.0                    # ... per minute

_SYSTEM = random.SystemRandom()                # server-owned, never the duel seed (#52)


def make_code(rng: random.Random | None = None) -> str:
    """A fresh code from the OS entropy source (or an injected one in tests)."""
    r = rng or _SYSTEM
    return "".join(r.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(raw: object) -> str | None:
    """Upper-case a typed code; None when it cannot be a code (the caller says "no room")."""
    if not isinstance(raw, str):
        return None
    code = raw.strip().upper()
    if len(code) != CODE_LENGTH or any(c not in CODE_ALPHABET for c in code):
        return None
    return code


class FailedJoins:
    """Sliding window of failed joins on one connection."""

    def __init__(self, limit: int = MAX_FAILED_JOINS, window_s: float = FAILED_JOIN_WINDOW_S):
        self.limit, self.window_s = limit, window_s
        self._times: deque[float] = deque()

    def _trim(self, now: float) -> None:
        while self._times and now - self._times[0] >= self.window_s:
            self._times.popleft()

    def blocked(self, now: float) -> bool:
        self._trim(now)
        return len(self._times) >= self.limit

    def record(self, now: float) -> None:
        self._trim(now)
        self._times.append(now)


@dataclass
class Room:
    code: str | None                            # None: the single-duel lobby of T13 (no code)
    match: Match
    created: float = 0.0
    second_joined: bool = False                 # a baseline room never waits for one
    empty_since: float | None = None
    links: dict = field(default_factory=dict)   # seat -> SeatLink
    conns: dict = field(default_factory=dict)   # seat -> websocket

    def expired(self, now: float) -> bool:
        if self.code is None:
            return False
        if not self.second_joined and now - self.created >= ROOM_WAIT_S:
            return True
        if self.conns:
            return False
        return self.empty_since is not None and now - self.empty_since >= EMPTY_EXPIRY_S

    def note_presence(self, now: float) -> None:
        """Start or stop the "everybody gone" timer."""
        if self.conns:
            self.empty_since = None
        elif self.empty_since is None:
            self.empty_since = now


RoomFactory = Callable[[str], Match]            # code -> a fresh Match for that room

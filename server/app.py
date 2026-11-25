"""The network layer of online play (T13): WebSocket game channel and the page over HTTP.

Needs the `online` extra (`uv run --extra online python -m server`). All rules
live in `server/match.py`; this module only moves messages:

* `GET /` and the files listed in the build manifest are served on the same
  port (online.html, scripts, art). Nothing else is: no directory listing, no
  source files.
* `WebSocket /ws`: the first client message is `{"type": "join", "token"?}`;
  the server answers `hello` (seat and token, to that client only) or `error`
  (`full`, `bad_token`) and closes. Then the client sends `keys` and
  `rematch` messages and receives `state` and `status` messages for its own
  seat.
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import time
from http import HTTPStatus
from pathlib import Path
from collections import deque
from typing import Callable
from urllib.parse import urlsplit

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

from .match import TICK_S, Match
from .rooms import (MAX_FAILED_JOINS, MAX_ROOMS, FailedJoins, Room, RoomFactory,
                    make_code, normalize_code)

log = logging.getLogger("server")

JOIN_TIMEOUT_S = 5.0
SEND_TIMEOUT_S = 2.0         # a client that cannot take one message in this long is dropped
MAX_QUEUED = 48              # per seat; older `state` messages are dropped first (stale frames)
PING_INTERVAL_S = 3.0        # decision #48: a silent drop is noticed in about 6 s
PING_TIMEOUT_S = 3.0
CLOSE_TIMEOUT_S = 1.0        # the library default (10 s) would delay the notice
LOBBY_IDLE_S = 60.0          # a client choosing Create or Join may think this long
ERROR_TEXT = {"full": "That room is full", "bad_token": "That seat token is not valid.",
              "no_room": "No room with that code", "expired": "That room has expired",
              "rate_limited": "Too many tries. Wait a minute.", "busy": "The server is full. Try later.",
              "no_rooms": "This server has no rooms."}
INDEX = "online.html"
ONLINE_FILES = frozenset({"online.html", "online.js", "keys.js", "draw.js", "ui.js"})


def hello_message(seat: str, token: str, rival: str | None, code: str | None = None) -> dict:
    msg = {"type": "hello", "seat": seat, "token": token, "rival": rival}
    if code is not None:
        msg["code"] = code                        # this room's own code, to its own seats only
    return msg


def error_message(code: str) -> dict:
    return {"type": "error", "code": code, "text": ERROR_TEXT.get(code, "Cannot join.")}


class SeatLink:
    """One seat's outgoing queue and its writer task.

    The tick loop only appends here and never awaits a socket, so a client that
    stops reading cannot stall the loop or the other seat. If one send does not
    finish within `send_timeout` that socket alone is aborted (a disconnect, #38).
    """

    def __init__(self, ws, send_timeout: float):
        self.ws = ws
        self.send_timeout = send_timeout
        self.q: deque[str] = deque()
        self.wake = asyncio.Event()
        self.task: asyncio.Task | None = None

    def start(self) -> None:
        self.task = asyncio.create_task(self._write())

    def put(self, text: str, stale_ok: bool) -> None:
        self.q.append(text)
        if len(self.q) > MAX_QUEUED:
            for i, t in enumerate(self.q):         # drop the oldest state frame, keep statuses
                if t.startswith('{"type":"state"'):
                    del self.q[i]
                    break
        self.wake.set()

    async def _write(self) -> None:
        try:
            while True:
                await self.wake.wait()
                self.wake.clear()
                while self.q:
                    await asyncio.wait_for(self.ws.send(self.q.popleft()), self.send_timeout)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.ws.transport.abort()               # only this socket; its handler then ends

    def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()


class OnlineServer:
    """Many rooms (T18, #52), each with its own `Match`, links, sockets and expiry.

    `match` alone is the T13 single-duel lobby (a join with no code), kept so the old
    clients and tests work unchanged. `match_factory` turns on rooms: `create` makes a
    room with a 4-letter code, `join` with a code takes its free seat.
    """

    def __init__(self, match: Match | None = None, clock: Callable[[], float] = time.monotonic,
                 site_dir: Path | None = None, send_timeout: float = SEND_TIMEOUT_S,
                 ping_interval: float = PING_INTERVAL_S, ping_timeout: float = PING_TIMEOUT_S,
                 close_timeout: float = CLOSE_TIMEOUT_S,
                 match_factory: RoomFactory | None = None,
                 code_factory: Callable[[], str] = make_code, max_rooms: int = MAX_ROOMS,
                 max_failed_joins: int = MAX_FAILED_JOINS):
        self.clock = clock
        self.send_timeout = send_timeout
        self.ping_interval, self.ping_timeout = ping_interval, ping_timeout
        self.close_timeout = close_timeout
        self.match_factory = match_factory
        self.code_factory = code_factory
        self.max_rooms = max_rooms
        self.max_failed_joins = max_failed_joins
        self.default = Room(None, match) if match is not None else None
        self.rooms: dict[str, Room] = {}
        self._bg: set[asyncio.Task] = set()
        self.site_dir = Path(site_dir) if site_dir is not None else None
        self._files: dict[str, Path] = {}
        if self.site_dir is not None:
            manifest = json.loads((self.site_dir / "manifest.json").read_text())
            # Only what the online page draws with. Never game.zip, index.html or main.js
            # (the engine, the arena layout and the guard scripts live in game.zip).
            names = {n for n in manifest["files"]
                     if n in ONLINE_FILES or n.startswith("art/")} | {"manifest.json"}
            self._files = {"/" + n: self.site_dir / n for n in sorted(names)}
            self._files["/"] = self.site_dir / INDEX

    # The single-duel lobby's parts, under the names T13 used.
    @property
    def match(self) -> Match | None:
        return self.default.match if self.default else None

    @property
    def links(self) -> dict:
        return self.default.links if self.default else {}

    @property
    def conns(self) -> dict:
        return self.default.conns if self.default else {}

    def all_rooms(self) -> list[Room]:
        return ([self.default] if self.default else []) + list(self.rooms.values())

    # --- serving ------------------------------------------------------------------
    async def start(self, host: str, port: int):
        return await serve(self.handler, host, port, process_request=self._http,
                           ping_interval=self.ping_interval, ping_timeout=self.ping_timeout,
                           close_timeout=self.close_timeout)

    def _http(self, connection, request):
        if request.headers.get("Upgrade", "").lower() == "websocket":
            # LAN-only server: a page from another site must not open a seat.
            origin = request.headers.get("Origin")
            if origin is not None:
                host = (request.headers.get("Host") or "").lower()
                if urlsplit(origin).netloc.lower() != host:
                    return self._reply(HTTPStatus.FORBIDDEN, b"forbidden\n", "text/plain")
            return None
        path = request.path.split("?", 1)[0]
        f = self._files.get(path)
        if f is None or not f.is_file():
            return self._reply(HTTPStatus.NOT_FOUND, b"not found\n", "text/plain")
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        return self._reply(HTTPStatus.OK, f.read_bytes(), ctype)

    @staticmethod
    def _reply(status: HTTPStatus, body: bytes, ctype: str) -> Response:
        headers = Headers([("Content-Type", ctype), ("Content-Length", str(len(body))),
                           ("Cache-Control", "no-store"), ("Connection", "close"),
                           ("X-Content-Type-Options", "nosniff")])
        return Response(status.value, status.phrase, headers, body)

    # --- one client -----------------------------------------------------------------
    async def handler(self, ws) -> None:
        room = seat = None
        try:
            got = await self._join(ws)
            if got is None:
                return
            room, seat = got
            async for raw in ws:
                room.match.receive(seat, raw, self.clock())
                await self._flush_room(room)
        except Exception:                       # a bad client must never stop the server
            pass
        finally:
            if seat is not None and room.conns.get(seat) is ws:
                self._release(room, seat)
                await self._flush_room(room)

    def _release(self, room: Room, seat: str) -> None:
        """A seat's socket is gone: the duel pauses (#38) and the room's empty timer may start."""
        del room.conns[seat]
        self._drop_link(room, seat)
        room.match.connection_lost(seat, self.clock())
        room.note_presence(self.clock())

    @staticmethod
    def _drop_link(room: Room, seat: str) -> None:
        link = room.links.pop(seat, None)
        if link is not None:
            link.stop()

    def _background(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._bg.add(task)
        task.add_done_callback(self._bg.discard)

    @staticmethod
    async def _close_quietly(ws, reason: str = "replaced") -> None:
        try:
            await ws.close(1000, reason)            # same token, new socket (or an expired room)
        except Exception:
            pass
        ws.transport.abort()                         # a half-open old socket must not linger

    async def _refuse(self, ws, code: str, close: bool = True) -> None:
        try:
            await asyncio.wait_for(ws.send(json.dumps(error_message(code))), self.send_timeout)
        except Exception:
            close = True
        if close:
            await ws.close(1008, code)

    async def _join(self, ws) -> tuple[Room, str] | None:
        """The lobby phase of one connection. A failed code join keeps the socket open for a
        retry, but only `max_failed_joins` times a minute (then a refusal and a close)."""
        fails = FailedJoins(self.max_failed_joins)
        wait = JOIN_TIMEOUT_S
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), wait)
                msg = json.loads(raw) if isinstance(raw, str) and len(raw) <= 512 else None
            except (asyncio.TimeoutError, ValueError):
                msg = None
            kind = msg.get("type") if isinstance(msg, dict) else None
            if kind == "join" and msg.get("create") is True:
                kind = "create"                  # the page's spelling: {"type":"join","create":true}
            if kind not in ("join", "create"):
                await ws.close(1008, "join first")
                return None
            now = self.clock()
            legacy = kind == "join" and "code" not in msg and self.default is not None
            if legacy:
                room, res = self.default, self.default.match.join(msg.get("token"), now)
                if not res["ok"]:
                    await self._refuse(ws, res["code"])
                    return None
            else:
                if fails.blocked(now):
                    await self._refuse(ws, "rate_limited")
                    return None
                room, res = (self._create(now) if kind == "create"
                             else self._join_code(msg, now))
                if not res["ok"]:
                    if kind == "join":
                        fails.record(now)
                    await self._refuse(ws, res["code"], close=False)
                    wait = LOBBY_IDLE_S
                    continue
            return await self._seat_up(room, ws, res)

    def _create(self, now: float) -> tuple[Room | None, dict]:
        if self.match_factory is None:
            return None, {"ok": False, "code": "no_rooms"}
        self._reap(now)
        if len(self.rooms) >= self.max_rooms:
            return None, {"ok": False, "code": "busy"}
        code = self.code_factory()
        while code in self.rooms:                    # a code is reused only after its room expired
            code = self.code_factory()
        match = self.match_factory(code)
        room = self.rooms[code] = Room(code, match, created=now, second_joined=match.rival is not None)
        return room, match.join(None, now)           # the creator takes seat A

    def _join_code(self, msg: dict, now: float) -> tuple[Room | None, dict]:
        self._reap(now)
        code = normalize_code(msg.get("code"))
        room = self.rooms.get(code) if code is not None else None
        if room is None:
            return None, {"ok": False, "code": "no_room"}
        res = room.match.join(msg.get("token"), now)  # a token of another room is "bad_token" here
        if res["ok"] and not msg.get("token"):
            room.second_joined = True
        return room, res

    async def _seat_up(self, room: Room, ws, res: dict) -> tuple[Room, str] | None:
        seat = res["seat"]
        old = room.conns.get(seat)
        room.conns[seat] = ws
        room.note_presence(self.clock())
        self._drop_link(room, seat)
        link = room.links[seat] = SeatLink(ws, self.send_timeout)
        if old is not None and old is not ws:
            self._background(self._close_quietly(old))   # never wait on the old socket
        try:
            await asyncio.wait_for(
                ws.send(json.dumps(hello_message(seat, res["token"], None, room.code))),
                self.send_timeout)
        except Exception:
            # The new socket died before it heard hello: free the seat now (pause, grace).
            if room.conns.get(seat) is ws:
                self._release(room, seat)
                await self._flush_room(room)
            return None
        link.start()
        await self._flush_room(room)
        return room, seat

    # --- the clock --------------------------------------------------------------------
    async def _flush_room(self, room: Room) -> None:
        for seat, link in list(room.links.items()):
            for msg in room.match.drain(seat):
                link.put(json.dumps(msg, separators=(",", ":")), msg.get("type") == "state")

    async def flush(self) -> None:
        """Move every room's outgoing messages onto each seat's queue. Never awaits a socket."""
        for room in self.all_rooms():
            await self._flush_room(room)

    def _reap(self, now: float) -> None:
        """Drop expired rooms (item 6). Their connected clients are told and closed."""
        for code, room in list(self.rooms.items()):
            if not room.expired(now):
                continue
            del self.rooms[code]
            for ws in list(room.conns.values()):
                self._background(self._tell_expired(ws))
            for seat in list(room.links):
                self._drop_link(room, seat)
            room.match.close()

    async def _tell_expired(self, ws) -> None:
        try:
            await asyncio.wait_for(ws.send(json.dumps(error_message("expired"))), self.send_timeout)
        except Exception:
            pass
        await self._close_quietly(ws, "expired")

    async def pump(self) -> None:
        """One step of the tick loop: advance every room to `clock()` and send."""
        now = self.clock()
        for room in self.all_rooms():
            try:
                room.match.advance(now)
            except Exception:
                self._room_failed(room)
            await self._flush_room(room)
        self._reap(now)

    @staticmethod
    def _room_failed(room: Room) -> None:
        """One room's error (an unwritable trace dir, say) must never stop the others (#63).
        Log it here with the room code, never to a client, and treat that room as finished."""
        log.exception("room %s: error while advancing or recording its duel", room.code)
        match = room.match
        if match.state != "ended":
            match.state = "ended"
            match._finished = True

    async def run_ticks(self, sleep=asyncio.sleep) -> None:
        while True:
            await self.pump()
            await sleep(TICK_S / 4)

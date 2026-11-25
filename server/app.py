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

JOIN_TIMEOUT_S = 5.0
SEND_TIMEOUT_S = 2.0         # a client that cannot take one message in this long is dropped
MAX_QUEUED = 48              # per seat; older `state` messages are dropped first (stale frames)
PING_INTERVAL_S = 3.0        # decision #48: a silent drop is noticed in about 6 s
PING_TIMEOUT_S = 3.0
CLOSE_TIMEOUT_S = 1.0        # the library default (10 s) would delay the notice
ERROR_TEXT = {"full": "The duel is full.", "bad_token": "That seat token is not valid."}
INDEX = "online.html"
ONLINE_FILES = frozenset({"online.html", "online.js", "keys.js", "draw.js", "ui.js"})


def hello_message(seat: str, token: str, rival: str | None) -> dict:
    return {"type": "hello", "seat": seat, "token": token, "rival": rival}


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
    def __init__(self, match: Match, clock: Callable[[], float] = time.monotonic,
                 site_dir: Path | None = None, send_timeout: float = SEND_TIMEOUT_S,
                 ping_interval: float = PING_INTERVAL_S, ping_timeout: float = PING_TIMEOUT_S,
                 close_timeout: float = CLOSE_TIMEOUT_S):
        self.match = match
        self.clock = clock
        self.send_timeout = send_timeout
        self.ping_interval, self.ping_timeout = ping_interval, ping_timeout
        self.close_timeout = close_timeout
        self.links: dict[str, SeatLink] = {}
        self._bg: set[asyncio.Task] = set()
        self.site_dir = Path(site_dir) if site_dir is not None else None
        self.conns: dict[str, object] = {}
        self._files: dict[str, Path] = {}
        if self.site_dir is not None:
            manifest = json.loads((self.site_dir / "manifest.json").read_text())
            # Only what the online page draws with. Never game.zip, index.html or main.js
            # (the engine, the arena layout and the guard scripts live in game.zip).
            names = {n for n in manifest["files"]
                     if n in ONLINE_FILES or n.startswith("art/")} | {"manifest.json"}
            self._files = {"/" + n: self.site_dir / n for n in sorted(names)}
            self._files["/"] = self.site_dir / INDEX

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
        seat = None
        try:
            seat = await self._join(ws)
            if seat is None:
                return
            async for raw in ws:
                self.match.receive(seat, raw, self.clock())
                await self.flush()
        except Exception:                       # a bad client must never stop the server
            pass
        finally:
            if seat is not None and self.conns.get(seat) is ws:
                del self.conns[seat]
                self._drop_link(seat)
                self.match.connection_lost(seat, self.clock())
                await self.flush()

    def _drop_link(self, seat: str) -> None:
        link = self.links.pop(seat, None)
        if link is not None:
            link.stop()

    def _background(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._bg.add(task)
        task.add_done_callback(self._bg.discard)

    @staticmethod
    async def _close_quietly(ws) -> None:
        try:
            await ws.close(1000, "replaced")        # same token, new socket
        except Exception:
            pass
        ws.transport.abort()                         # a half-open old socket must not linger

    async def _join(self, ws) -> str | None:
        try:
            raw = await asyncio.wait_for(ws.recv(), JOIN_TIMEOUT_S)
            msg = json.loads(raw) if isinstance(raw, str) and len(raw) <= 512 else None
        except (asyncio.TimeoutError, ValueError):
            msg = None
        if not isinstance(msg, dict) or msg.get("type") != "join":
            await ws.close(1008, "join first")
            return None
        res = self.match.join(msg.get("token"), self.clock())
        if not res["ok"]:
            await ws.send(json.dumps(error_message(res["code"])))
            await ws.close(1008, res["code"])
            return None
        seat = res["seat"]
        old = self.conns.get(seat)
        self.conns[seat] = ws
        self._drop_link(seat)
        link = self.links[seat] = SeatLink(ws, self.send_timeout)
        if old is not None and old is not ws:
            self._background(self._close_quietly(old))   # never wait on the old socket
        try:
            await asyncio.wait_for(
                ws.send(json.dumps(hello_message(seat, res["token"], None))), self.send_timeout)
        except Exception:
            # The new socket died before it heard hello: free the seat now (pause, grace).
            if self.conns.get(seat) is ws:
                del self.conns[seat]
                self._drop_link(seat)
                self.match.connection_lost(seat, self.clock())
                await self.flush()
            return None
        link.start()
        await self.flush()
        return seat

    # --- the clock --------------------------------------------------------------------
    async def flush(self) -> None:
        """Move the match's outgoing messages onto each seat's queue. Never awaits a socket."""
        for seat, link in list(self.links.items()):
            for msg in self.match.drain(seat):
                link.put(json.dumps(msg, separators=(",", ":")), msg.get("type") == "state")

    async def pump(self) -> None:
        """One step of the tick loop: advance the match to `clock()` and send."""
        self.match.advance(self.clock())
        await self.flush()

    async def run_ticks(self, sleep=asyncio.sleep) -> None:
        while True:
            await self.pump()
            await sleep(TICK_S / 4)

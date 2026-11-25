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
from typing import Callable

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

from .match import TICK_S, Match

JOIN_TIMEOUT_S = 5.0
ERROR_TEXT = {"full": "The duel is full.", "bad_token": "That seat token is not valid."}
INDEX = "online.html"
ONLINE_FILES = frozenset({"online.html", "online.js", "keys.js", "draw.js", "ui.js"})


def hello_message(seat: str, token: str, rival: str | None) -> dict:
    return {"type": "hello", "seat": seat, "token": token, "rival": rival}


def error_message(code: str) -> dict:
    return {"type": "error", "code": code, "text": ERROR_TEXT.get(code, "Cannot join.")}


class OnlineServer:
    def __init__(self, match: Match, clock: Callable[[], float] = time.monotonic,
                 site_dir: Path | None = None):
        self.match = match
        self.clock = clock
        self.site_dir = Path(site_dir) if site_dir is not None else None
        self.conns: dict[str, object] = {}
        self._flush_lock = asyncio.Lock()
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
        return await serve(self.handler, host, port, process_request=self._http)

    def _http(self, connection, request):
        if request.headers.get("Upgrade", "").lower() == "websocket":
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
                self.match.connection_lost(seat, self.clock())
                await self.flush()

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
        if old is not None and old is not ws:
            await old.close(1000, "replaced")      # same token, new socket
        label = None
        await ws.send(json.dumps(hello_message(seat, res["token"], label)))
        await self.flush()
        return seat

    # --- the clock --------------------------------------------------------------------
    async def flush(self) -> None:
        async with self._flush_lock:
            for seat, ws in list(self.conns.items()):
                for msg in self.match.drain(seat):
                    try:
                        await ws.send(json.dumps(msg, separators=(",", ":")))
                    except Exception:
                        break

    async def pump(self) -> None:
        """One step of the tick loop: advance the match to `clock()` and send."""
        self.match.advance(self.clock())
        await self.flush()

    async def run_ticks(self, sleep=asyncio.sleep) -> None:
        while True:
            await self.pump()
            await sleep(TICK_S / 4)

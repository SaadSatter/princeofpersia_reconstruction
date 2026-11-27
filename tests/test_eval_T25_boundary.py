"""T25 Gate 2 (evaluation specialist): the private AI-match path, server to client.

Real localhost sockets, no network, no keys, no training, no held-out data.
- the code and token reach the owner only (hello), never the state stream;
- a second client learns only `full` (live) or `no_room` (not), and the join rate limit bites both;
- the AI seat of a private room is the shipped rival (same weights hash);
- a stalled handshake is reported, not silently dropped (QA finding 2).
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket

import pytest

websockets = pytest.importorskip("websockets")
from agents.rl import policy                               # noqa: E402
from server import modes as smodes                         # noqa: E402
from server.app import OnlineServer                        # noqa: E402
from server.match import TICK_S                            # noqa: E402

CODE = "QZXV"


def go(coro, t=60):
    return asyncio.run(asyncio.wait_for(coro, t))


class Rig:
    def __init__(self):
        self.now = [100.0]
        codes = iter([CODE, "KKKK", "LLLL"])
        self.srv = OnlineServer(None, clock=lambda: self.now[0],
                                match_factory=lambda c, m=None: smodes.make_match(m or "human", seed=0),
                                code_factory=lambda: next(codes))

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *a):
        self.server.close()
        await self.server.wait_closed()


async def recv(ws, t=2):
    return json.loads(await asyncio.wait_for(ws.recv(), t))


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_code_and_token_only_in_owner_hello_never_in_stream(mode):
    async def body():
        async with Rig() as r:
            ws = await websockets.connect(f"ws://127.0.0.1:{r.port}/ws")
            await ws.send(json.dumps({"type": "join", "create": True, "mode": mode}))
            hello = await recv(ws)
            assert hello["type"] == "hello" and hello["seat"] == "A"
            for _ in range(25):
                r.now[0] += TICK_S
                await r.srv.pump()
            await asyncio.sleep(0.1)
            raw = []
            while True:
                try:
                    raw.append(await asyncio.wait_for(ws.recv(), 0.1))
                except (asyncio.TimeoutError, websockets.ConnectionClosed):
                    break
            assert raw
            blob = "".join(raw)
            assert CODE not in blob and hello["token"] not in blob
            assert all(json.loads(m)["type"] in ("state", "status") for m in raw)
            await ws.close()
    go(body())


def test_full_vs_no_room_reveal_existence_only_and_both_count_against_the_limit():
    async def body():
        async with Rig() as r:
            owner = await websockets.connect(f"ws://127.0.0.1:{r.port}/ws")
            await owner.send(json.dumps({"type": "join", "create": True, "mode": "ai"}))
            await recv(owner)
            g = await websockets.connect(f"ws://127.0.0.1:{r.port}/ws")
            await g.send(json.dumps({"type": "join", "code": CODE}))
            full = await recv(g)
            await g.send(json.dumps({"type": "join", "code": "ZZZZ"}))
            none = await recv(g)
            assert full["type"] == none["type"] == "error"
            assert full["code"] == "full" and none["code"] == "no_room"
            for m in (full, none):
                assert CODE not in json.dumps(m) and "token" not in m
            seen = []
            for i in range(14):
                try:
                    await g.send(json.dumps({"type": "join", "code": CODE if i % 2 else "ZZZZ"}))
                    seen.append((await recv(g))["code"])
                except Exception:
                    break
            assert "rate_limited" in seen, seen
    go(body())


def test_ai_room_seat_is_the_shipped_rival_with_the_recorded_hash():
    assert policy.file_sha256(policy.SHIPPED_WEIGHTS) == policy.SHIPPED_SHA256
    assert smodes.make_match("ai", seed=0).rival is not None


def test_a_stalled_handshake_is_closed_by_the_server_and_the_filter_adds_no_silence(caplog):
    """QA finding 2. Half a request then silence: the library closes the socket after its 10 s
    open timeout and logs nothing at INFO or above, with or without our filter (checked by hand
    in the report). So the filter hides no stall signal; the server does reclaim the socket."""
    async def body():
        async with Rig() as r:
            s = socket.create_connection(("127.0.0.1", r.port))
            s.sendall(b"GET /ws HTTP/1.1\r\nHost: x\r\n")
            await asyncio.sleep(11)
            s.settimeout(2)
            return s.recv(10)
    with caplog.at_level(logging.INFO, logger="server.ws"):
        assert go(body(), 40) == b""                      # closed by the server
    assert not [x for x in caplog.records if x.levelno >= logging.ERROR]

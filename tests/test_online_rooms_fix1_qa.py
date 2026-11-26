"""T18-fix1 QA: a room error from the tick itself (not only on_finish) and log-once behaviour."""

from __future__ import annotations

import asyncio
import json
import logging

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer      # noqa: E402
from server.match import Match, TICK_S   # noqa: E402


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def hello(port, msg):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    await ws.send(json.dumps(msg))
    json.loads(await asyncio.wait_for(ws.recv(), 2))
    return ws


async def drain(ws):
    out = []
    while True:
        try:
            out.append(await asyncio.wait_for(ws.recv(), 0.1))
        except asyncio.TimeoutError:
            return out


def test_tick_exception_in_one_room_is_contained_logged_once_and_not_leaked(caplog):
    made: dict[str, Match] = {}
    now = [100.0]
    seq = iter(["AAAA"])

    def factory(code):
        made[code] = Match(seed=0, rival=None)
        return made[code]

    home = Match(seed=0, rival=None)
    srv = OnlineServer(home, clock=lambda: now[0], match_factory=factory,
                       code_factory=lambda: next(seq))

    async def go():
        server = await srv.start("127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        a1 = await hello(port, {"type": "create"})
        a2 = await hello(port, {"type": "join", "code": "AAAA"})
        h1 = await hello(port, {"type": "join"})
        h2 = await hello(port, {"type": "join"})
        await asyncio.sleep(0.1)

        def boom():
            raise RuntimeError("SECRET-INTERNAL-DETAIL /private/path")
        made["AAAA"]._tick = boom
        h0 = home.episode.outcome()["frames"]
        with caplog.at_level(logging.ERROR, logger="server"):
            for _ in range(6):
                now[0] += TICK_S
                await srv.pump()                          # must not raise
        assert home.episode.outcome()["frames"] > h0      # HOME still ticks
        assert home.state == "playing"
        assert made["AAAA"].state == "ended"
        errs = [r for r in caplog.records if "AAAA" in r.getMessage()]
        assert len(errs) == 1                             # not repeated every tick
        seen = []
        for w in (a1, a2, h1, h2):
            seen += await drain(w)
        assert not any("SECRET" in str(m) or "RuntimeError" in str(m) or "Traceback" in str(m)
                       for m in seen)
        for w in (a1, a2, h1, h2):
            await w.close()
        server.close()
        await server.wait_closed()
    run(go())
    for m in [*made.values(), home]:
        m.close()

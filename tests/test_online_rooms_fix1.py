"""T18-fix1 (decision #63): one room's error never stops the server.

An error from a room's on_finish (an unwritable trace dir) is caught at the room boundary,
logged server-side with the room code, never sent to a client; other rooms and HOME keep ticking.
Localhost sockets and an injected clock only.
"""

from __future__ import annotations

import asyncio
import json
import logging

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer                      # noqa: E402
from server.match import Match, TICK_S                   # noqa: E402


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def drain(ws):
    out = []
    while True:
        try:
            out.append(await asyncio.wait_for(ws.recv(), 0.1))
        except asyncio.TimeoutError:
            return out


async def hello(port, msg):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    await ws.send(json.dumps(msg))
    json.loads(await asyncio.wait_for(ws.recv(), 2))
    return ws


def test_unwritable_trace_dir_in_one_room_stops_nothing(tmp_path, caplog):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")                              # mkdir under a file raises
    finished: list[str] = []
    made: dict[str, Match] = {}
    now = [100.0]
    seq = iter(["AAAA", "BBBB"])

    def write_bad(trace):
        (blocker / "sub").mkdir(parents=True)            # the real failure mode of --trace-dir

    def factory(code):
        fin = write_bad if code == "AAAA" else (lambda t, c=code: finished.append(c))
        made[code] = Match(seed=0, rival=None, on_finish=fin)
        return made[code]

    home = Match(seed=0, rival=None, on_finish=lambda t: finished.append("HOME"))
    srv = OnlineServer(home, clock=lambda: now[0], match_factory=factory,
                       code_factory=lambda: next(seq))

    async def go():
        server = await srv.start("127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        a1 = await hello(port, {"type": "create"})
        a2 = await hello(port, {"type": "join", "code": "AAAA"})
        b1 = await hello(port, {"type": "create"})
        b2 = await hello(port, {"type": "join", "code": "BBBB"})
        h1 = await hello(port, {"type": "join"})
        h2 = await hello(port, {"type": "join"})
        await asyncio.sleep(0.1)
        for _ in range(3):
            now[0] += TICK_S
            await srv.pump()
        frames = {c: m.episode.outcome()["frames"] for c, m in [*made.items(), ("HOME", home)]}
        await a1.close()
        await b1.close()
        await h1.close()
        await asyncio.sleep(0.1)
        now[0] += 16                                      # past the forfeit window in all three
        with caplog.at_level(logging.ERROR, logger="server"):
            for _ in range(10):
                now[0] += TICK_S
                await srv.pump()                          # must not raise
        for c, m in [*made.items(), ("HOME", home)]:
            assert m.episode.outcome()["frames"] >= frames[c]
            assert m.state == "ended", c
        assert sorted(finished) == ["BBBB", "HOME"]       # the others recorded normally
        assert any("AAAA" in r.getMessage() for r in caplog.records)
        # no client heard the error text
        seen = []
        for w in (a2, b2, h2):
            seen += await drain(w)
        assert not any("not-a-dir" in str(m) or "Errno" in str(m) or "Traceback" in str(m)
                       for m in seen)
        # the tick loop itself survives
        task = asyncio.create_task(srv.run_ticks(sleep=lambda s: asyncio.sleep(0.001)))
        await asyncio.sleep(0.05)
        assert not task.done()
        task.cancel()
        for w in (a2, b2, h2):
            await w.close()
        server.close()
        await server.wait_closed()
    run(go())
    for m in [*made.values(), home]:
        m.close()

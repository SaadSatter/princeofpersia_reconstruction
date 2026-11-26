"""Gate 2 (T18-fix1): the room-error boundary leaks nothing and touches no other room.

Room AAAA fails mid-tick (its `advance` raises with a secret path). Room BBBB must end up
byte-identical to a control run where AAAA never fails, and no client message anywhere may
contain the exception text. Localhost sockets and an injected clock only.
"""

from __future__ import annotations

import asyncio
import json
import logging

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer                      # noqa: E402
from server.match import Match, TICK_S                   # noqa: E402

SECRET = "/secret/trace/dir-EVAL-9731"


async def _hello(port, msg):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    await ws.send(json.dumps(msg))
    await asyncio.wait_for(ws.recv(), 2)
    return ws


async def _drain(ws, into):
    while True:
        try:
            into.append(await asyncio.wait_for(ws.recv(), 0.1))
        except asyncio.TimeoutError:
            return


def _scenario(fail: bool):
    now, made, seq = [100.0], {}, iter(["AAAA", "BBBB"])

    def factory(code):
        made[code] = Match(seed=0, rival=None)
        return made[code]

    srv = OnlineServer(None, clock=lambda: now[0], match_factory=factory, code_factory=lambda: next(seq))

    async def go():
        server = await srv.start("127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        a = [await _hello(port, {"type": "create"}), await _hello(port, {"type": "join", "code": "AAAA"})]
        b = [await _hello(port, {"type": "create"}), await _hello(port, {"type": "join", "code": "BBBB"})]
        await asyncio.sleep(0.1)
        if fail:
            def bad(_now):
                raise OSError(f"[Errno 2] {SECRET}")
            made["AAAA"].advance = bad
        for _ in range(12):
            now[0] += TICK_S
            await srv.pump()
        await asyncio.sleep(0.1)
        got = {"A": [], "B": []}
        for ws in a:
            await _drain(ws, got["A"])
        for ws in b:
            await _drain(ws, got["B"])
        state_a = made["AAAA"].state                  # before the seats leave (an emptied ended room resets)
        for ws in a + b:
            await ws.close()
        server.close()
        await server.wait_closed()
        trace_b = made["BBBB"].trace()
        for m in made.values():
            m.close()
        return got, trace_b, state_a

    return asyncio.run(asyncio.wait_for(go(), 60))


def test_failed_room_leaks_nothing_and_leaves_other_rooms_byte_identical(caplog):
    with caplog.at_level(logging.ERROR, logger="server"):
        got_f, trace_f, state_a = _scenario(fail=True)
    got_c, trace_c, _ = _scenario(fail=False)
    blob = "".join(got_f["A"] + got_f["B"])
    for needle in (SECRET, "Errno", "Traceback", "OSError", "File \""):
        assert needle not in blob
    assert state_a == "ended"
    assert any("AAAA" in r.getMessage() for r in caplog.records)      # logged server-side with the code
    assert trace_f == trace_c                                         # room BBBB unaffected, byte for byte
    assert got_f["B"] == got_c["B"]


@pytest.mark.xfail(strict=True, reason="EVAL-T18-2 (minor): a room that fails mid-tick ends without "
                   "telling its clients; frames just stop")
def test_a_room_that_fails_mid_tick_tells_its_clients_it_ended():
    got_f, _, _ = _scenario(fail=True)
    assert any(json.loads(m).get("state") == "ended" for m in got_f["A"])

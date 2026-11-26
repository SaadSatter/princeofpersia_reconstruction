"""T18 Gate 1 (QA): adversarial checks on room codes, written independently of the Tech Lead's
tests. Real localhost sockets, injected clock. Needs the `online` extra."""

from __future__ import annotations

import asyncio
import json

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer                      # noqa: E402
from server.match import Match, TICK_S                   # noqa: E402
from server.rooms import (CODE_ALPHABET, EMPTY_EXPIRY_S, ROOM_WAIT_S,   # noqa: E402
                          make_code, normalize_code)


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def settle(ms=60):
    await asyncio.sleep(ms / 1000)


async def drain(ws):
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            return out


async def recv(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), 2))


async def raw(port, payload, ws=None):
    ws = ws or await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    await ws.send(payload if isinstance(payload, str) else json.dumps(payload))
    return ws, await recv(ws)


class Rig:
    def __init__(self, codes=None, default=False, **kw):
        self.now = [100.0]
        self.made = {}
        seq = iter(codes) if codes else None

        def factory(code):
            self.made[code] = Match(seed=0)
            return self.made[code]

        self.srv = OnlineServer(Match(seed=0) if default else None, clock=lambda: self.now[0],
                                match_factory=factory,
                                code_factory=(lambda: next(seq)) if seq else make_code, **kw)

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()

    async def ticks(self, n):
        for _ in range(n):
            self.now[0] += TICK_S
            await self.srv.pump()
        await settle()


def test_malformed_join_payloads_never_crash_and_read_as_no_room():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            wa, ha = await raw(r.port, {"type": "create"})
            ws = None
            for bad in (7, ["AAAA"], {"c": "AAAA"}, True, "", "AAAAA", " ", "AA AA", "A\u0000AA"):
                ws, got = await raw(r.port, {"type": "join", "code": bad}, ws)
                assert got == {"type": "error", "code": "no_room", "text": "No room with that code"}, bad
            ws, got = await raw(r.port, {"type": "join", "code": "AAAA", "token": ["x"]}, ws)
            assert got["type"] == "error"                       # a junk token is never a seat
            with pytest.raises(websockets.exceptions.ConnectionClosed):   # not JSON: closed "join first"
                await raw(r.port, "not json", ws)
            # the server still serves a normal join afterwards (creator still holds seat A)
            w2, h2 = await raw(r.port, {"type": "join", "code": "aaaa"})
            assert h2["seat"] == "B"
            await w2.close()
            await wa.close()
    run(go())


@pytest.mark.xfail(strict=True, reason="QA-T18-1")
def test_ligature_input_is_not_a_second_spelling_of_a_code():
    # "ﬀ".upper() == "FF": three typed characters would read as the code FFAB.
    assert normalize_code("ﬀAB") is None, "finding QA-T18-1: Unicode upper() widens the code"


def test_a_coded_token_in_the_default_room_and_back_is_refused_and_changes_nothing():
    async def go():
        async with Rig(default=True, codes=["AAAA"]) as r:
            d, dh = await raw(r.port, {"type": "join"})
            a, ah = await raw(r.port, {"type": "create"})
            _, bad = await raw(r.port, {"type": "join", "token": ah["token"]})   # coded token, no code
            assert bad["type"] == "error" and bad["code"] == "bad_token"
            _, bad2 = await raw(r.port, {"type": "join", "code": "AAAA", "token": dh["token"]})
            assert bad2["code"] == "bad_token"
            await settle()
            # the legitimate seats still hold: A of the coded room refreshes into A
            a2, ah2 = await raw(r.port, {"type": "join", "code": "AAAA", "token": ah["token"]})
            assert ah2["seat"] == "A" and ah2["code"] == "AAAA"
            for w in (d, a, a2):
                await w.close()
    run(go())


def test_room_cap_answers_busy_then_frees_when_a_room_expires():
    async def go():
        async with Rig(max_rooms=2) as r:
            ws = []
            for _ in range(2):
                w, h = await raw(r.port, {"type": "create"})
                assert h["type"] == "hello"
                ws.append(w)
            w3, busy = await raw(r.port, {"type": "create"})
            assert busy["type"] == "error" and busy["code"] == "busy"
            r.now[0] += ROOM_WAIT_S + 1
            await r.srv.pump()
            _, again = await raw(r.port, {"type": "create"}, w3)
            assert again["type"] == "hello"
            for w in ws + [w3]:
                await w.close()
    run(go())


def test_rate_limit_counts_only_failed_joins_slides_with_time_and_gates_create():
    async def go():
        async with Rig(codes=["AAAA", "BBBB"]) as r:
            w, h = await raw(r.port, {"type": "create"})         # creates do not count
            w2 = None
            for _ in range(10):
                w2, e = await raw(r.port, {"type": "join", "code": "ZZZZ"}, w2)
                assert e["code"] == "no_room"
            _, e = await raw(r.port, {"type": "join", "code": "ZZZZ"}, w2)
            assert e["code"] == "rate_limited"
            # a new connection has its own allowance
            w3, e3 = await raw(r.port, {"type": "join", "code": "ZZZZ"})
            assert e3["code"] == "no_room"
            await w.close(), await w3.close()
        # window slides: after a minute a connection may try again
        async with Rig() as r:
            w = None
            for _ in range(10):
                w, e = await raw(r.port, {"type": "join", "code": "ZZZZ"}, w)
            r.now[0] += 61
            w, e = await raw(r.port, {"type": "join", "code": "ZZZZ"}, w)
            assert e["code"] == "no_room"
            await w.close()
    run(go())


def test_rate_limit_stops_a_code_guess_even_when_the_room_exists():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            a, _ = await raw(r.port, {"type": "create"})
            b, hb = await raw(r.port, {"type": "join", "code": "AAAA"})   # take B
            w = None
            for _ in range(10):                                  # guesses against a full room
                w, e = await raw(r.port, {"type": "join", "code": "AAAA"}, w)
                assert e["code"] == "full"
            _, e = await raw(r.port, {"type": "join", "code": "AAAA"}, w)
            assert e["code"] == "rate_limited"
            await a.close(), await b.close()
    run(go())


def test_hello_carries_only_seat_token_rival_and_the_own_code():
    async def go():
        async with Rig(codes=["AAAA", "BBBB"]) as r:
            a, ha = await raw(r.port, {"type": "create"})
            b, hb = await raw(r.port, {"type": "create"})
            assert set(ha) == {"type", "seat", "token", "rival", "code"} and ha["code"] == "AAAA"
            assert hb["code"] == "BBBB"
            await r.ticks(3)
            seen = json.dumps(await drain(a))
            assert "BBBB" not in seen and hb["token"] not in seen and "seed" not in seen
            await a.close(), await b.close()
    run(go())


def test_expired_room_tells_its_connected_client_and_the_code_is_then_unknown():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            a, ha = await raw(r.port, {"type": "create"})
            r.now[0] += ROOM_WAIT_S + 1
            await r.srv.pump()
            await settle(200)
            msgs = await drain(a)
            assert any(m.get("code") == "expired" for m in msgs if m["type"] == "error")
            _, e = await raw(r.port, {"type": "join", "code": "AAAA"})
            assert e == {"type": "error", "code": "no_room", "text": "No room with that code"}
    run(go())


def test_code_collision_with_a_live_room_is_retried():
    async def go():
        async with Rig(codes=["AAAA", "AAAA", "BBBB"]) as r:
            a, ha = await raw(r.port, {"type": "create"})
            b, hb = await raw(r.port, {"type": "create"})
            assert (ha["code"], hb["code"]) == ("AAAA", "BBBB")
            await a.close(), await b.close()
    run(go())


def test_empty_expiry_and_alphabet_constants_match_the_brief():
    assert "I" not in CODE_ALPHABET and "O" not in CODE_ALPHABET and len(CODE_ALPHABET) == 24
    assert ROOM_WAIT_S == 600 and EMPTY_EXPIRY_S == 15

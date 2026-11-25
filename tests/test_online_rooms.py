"""T18 (decision #52): online room codes. Real localhost sockets, injected clock, no real sleeps
over a fraction of a second. Needs the `online` extra (skipped without it).
"""

from __future__ import annotations

import asyncio
import json
import random
import re

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer           # noqa: E402
from server.match import FORFEIT_GRACE_S, Match, TICK_S   # noqa: E402
from server.rooms import (CODE_ALPHABET, CODE_LENGTH, EMPTY_EXPIRY_S, ROOM_WAIT_S,   # noqa: E402
                          FailedJoins, make_code, normalize_code)


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def settle(ms: int = 60):
    await asyncio.sleep(ms / 1000)


async def drain(ws) -> list[dict]:
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except asyncio.TimeoutError:
            return out


async def recv(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), 2))


async def connect(port):
    return await websockets.connect(f"ws://127.0.0.1:{port}/ws")


async def create(port):
    ws = await connect(port)
    await ws.send(json.dumps({"type": "create"}))
    return ws, await recv(ws)


async def join_code(port, code, token=None, ws=None):
    ws = ws or await connect(port)
    msg = {"type": "join", "code": code}
    if token:
        msg["token"] = token
    await ws.send(json.dumps(msg))
    return ws, await recv(ws)


class Rig:
    def __init__(self, codes=None, rival=None, **kw):
        self.now = [100.0]
        self.made: dict[str, Match] = {}
        seq = iter(codes) if codes else None

        def factory(code):
            self.made[code] = Match(seed=0, rival=rival)
            return self.made[code]

        self.srv = OnlineServer(clock=lambda: self.now[0], match_factory=factory,
                                code_factory=(lambda: next(seq)) if seq else make_code, **kw)

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()

    async def ticks(self, n, seconds=None):
        for _ in range(n):
            self.now[0] += TICK_S if seconds is None else seconds
            await self.srv.pump()
        await settle()


def test_create_then_join_with_any_case_starts_the_duel():
    async def go():
        async with Rig() as r:
            wa, ha = await create(r.port)
            assert ha["type"] == "hello" and ha["seat"] == "A"
            code = ha["code"]
            assert re.fullmatch(f"[{CODE_ALPHABET}]{{{CODE_LENGTH}}}", code)
            wb, hb = await join_code(r.port, code.lower())
            assert hb["type"] == "hello" and hb["seat"] == "B" and hb["code"] == code
            await settle()
            assert r.made[code].state == "playing"
            await r.ticks(6)
            sa = [m for m in await drain(wa) if m["type"] == "state"]
            sb = [m for m in await drain(wb) if m["type"] == "state"]
            assert sa and sb and {m["seat"] for m in sa} == {"A"} and {m["seat"] for m in sb} == {"B"}
            await wa.close(), await wb.close()
    run(go())


def test_two_rooms_play_independent_duels_and_a_stalled_client_stalls_nobody():
    async def go():
        async with Rig(codes=["AAAA", "BBBB"], send_timeout=0.3) as r:
            a1, _ = await create(r.port)
            b1, _ = await join_code(r.port, "AAAA")
            a2, _ = await create(r.port)
            b2, _ = await join_code(r.port, "BBBB")
            await settle()
            await drain(a1), await drain(b1), await drain(a2), await drain(b2)
            col1 = r.made["AAAA"].episode.observe("A")["me"]["col"]
            col2 = r.made["BBBB"].episode.observe("A")["me"]["col"]
            await a2.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle()
            # room 1's clients never read again: its sockets back up, room 2 must not care
            frames0 = r.made["BBBB"].episode.outcome()["frames"]
            for _ in range(40):
                await r.ticks(1)
            assert r.made["BBBB"].episode.outcome()["frames"] - frames0 >= 30
            assert r.made["BBBB"].episode.observe("A")["me"]["col"] != col2
            assert r.made["AAAA"].episode.observe("A")["me"]["col"] == col1
            got = [m for m in await drain(a2) if m["type"] == "state"]
            assert len(got) >= 30
            assert {m["seat"] for m in got} == {"A"}
            for w in (a1, b1, a2, b2):
                await w.close()
    run(go())


def test_unknown_full_and_malformed_codes_are_refused_alike_and_leak_nothing():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            wa, ha = await create(r.port)
            wb, _ = await join_code(r.port, "AAAA")
            wc, full = await join_code(r.port, "aaaa")
            assert full == {"type": "error", "code": "full", "text": "That room is full"}
            _, unknown = await join_code(r.port, "ZZZZ", ws=wc)
            assert unknown == {"type": "error", "code": "no_room", "text": "No room with that code"}
            _, junk = await join_code(r.port, "I0O!", ws=wc)         # not a possible code
            assert junk == unknown
            _, nocode = await join_code(r.port, None, ws=wc)
            assert nocode == unknown
            assert "AAAA" not in json.dumps([unknown, junk, nocode])
            for w in (wa, wb, wc):
                await w.close()
    run(go())


def test_a_token_from_one_room_cannot_rejoin_another_but_refresh_rejoin_works():
    async def go():
        async with Rig(codes=["AAAA", "BBBB"]) as r:
            a1, h1 = await create(r.port)
            b1, _ = await join_code(r.port, "AAAA")
            a2, h2 = await create(r.port)
            b2, _ = await join_code(r.port, "BBBB")
            await settle()
            w, bad = await join_code(r.port, "BBBB", token=h1["token"])
            assert bad["type"] == "error" and bad["code"] == "bad_token"
            assert r.made["BBBB"].connected == {"A": True, "B": True}
            await w.close()
            # refresh in room 1: the old socket dies, the same token comes back
            await a1.close()
            await settle()
            await r.ticks(1)
            assert r.made["AAAA"].state == "paused"
            a1b, again = await join_code(r.port, "aaaa", token=h1["token"])
            assert again["type"] == "hello" and again["seat"] == "A" and again["code"] == "AAAA"
            await settle()
            assert r.made["AAAA"].state == "playing"
            for x in (a1b, b1, a2, b2):
                await x.close()
    run(go())


def test_room_expires_after_ten_minutes_without_a_second_player_and_the_code_is_then_free():
    async def go():
        async with Rig(codes=["AAAA", "AAAA", "CCCC"]) as r:
            wa, ha = await create(r.port)
            r.now[0] += ROOM_WAIT_S - 1
            await r.srv.pump()
            assert "AAAA" in r.srv.rooms
            r.now[0] += 2
            await r.srv.pump()
            assert "AAAA" not in r.srv.rooms
            note = await recv(wa)                                   # told, then closed
            while note["type"] != "error":
                note = await recv(wa)
            assert note["code"] == "expired"
            wj, err = await join_code(r.port, "AAAA")
            assert err["code"] == "no_room"                         # same words as unknown
            wn, hn = await create(r.port)                           # code_factory repeats AAAA, then CCCC
            assert hn["code"] == "AAAA"                          # reusable only now
            for w in (wj, wn):
                await w.close()
    run(go())


def test_code_is_not_reused_while_its_room_lives():
    async def go():
        async with Rig(codes=["AAAA", "AAAA", "BBBB"]) as r:
            w1, h1 = await create(r.port)
            w2, h2 = await create(r.port)
            assert (h1["code"], h2["code"]) == ("AAAA", "BBBB")
            await w1.close(), await w2.close()
    run(go())


def test_room_expires_when_both_seats_have_been_gone_past_the_forfeit_window():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            wa, _ = await create(r.port)
            wb, _ = await join_code(r.port, "AAAA")
            await settle()
            await wa.close(), await wb.close()
            await settle()
            await r.ticks(1)
            assert "AAAA" in r.srv.rooms
            r.now[0] += EMPTY_EXPIRY_S - 1
            await r.srv.pump()
            assert "AAAA" in r.srv.rooms and r.made["AAAA"].state == "paused"
            r.now[0] += 2
            await r.srv.pump()
            assert "AAAA" not in r.srv.rooms
            assert r.made["AAAA"].forfeit is not None or r.made["AAAA"].state == "ended"
            assert EMPTY_EXPIRY_S == FORFEIT_GRACE_S
    run(go())


def test_one_seat_back_in_time_keeps_the_room_alive():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            wa, ha = await create(r.port)
            wb, hb = await join_code(r.port, "AAAA")
            await settle()
            await wa.close()
            await settle()
            r.now[0] += 60
            await r.srv.pump()
            assert "AAAA" in r.srv.rooms                            # B is still there
            await wb.close()
    run(go())


def test_codes_use_the_alphabet_and_never_touch_the_duel_rng():
    assert "I" not in CODE_ALPHABET and "O" not in CODE_ALPHABET and len(CODE_ALPHABET) == 24
    codes = {make_code() for _ in range(300)}
    assert all(re.fullmatch("[A-HJ-NP-Z]{4}", c) for c in codes) and len(codes) > 250
    random.seed(7)
    before = random.getstate()
    make_code()
    assert random.getstate() == before                              # not the global random
    assert normalize_code(" abcd ") == "ABCD" and normalize_code("abco") is None
    assert normalize_code("abc") is None and normalize_code(None) is None


def test_the_seed_zero_duel_is_the_same_with_and_without_rooms():
    keys = [["d"], ["d"], [], ["a"], ["d"], ["f"], []] * 6

    def drive(match, seat_a_keys, t=0.0, join=True):
        if join:
            match.join(None, t)
            match.join(None, t)
        match.advance(t + TICK_S)
        for k in seat_a_keys:
            match.receive("A", json.dumps({"type": "keys", "keys": k}), t)
            t += TICK_S
            match.advance(t)
        return match.trace()

    plain = drive(Match(seed=0), keys)

    async def with_rooms():
        async with Rig(codes=["AAAA"]) as r:
            for _ in range(5):                                      # churn codes first
                make_code()
            wa, _ = await create(r.port)
            wb, _ = await join_code(r.port, "AAAA")
            await settle()
            trace = drive(r.made["AAAA"], keys, t=r.now[0], join=False)   # the room's own Match
            await wa.close(), await wb.close()
            return trace
    assert run(with_rooms()) == plain


def test_ten_failed_joins_a_minute_then_a_refusal_per_connection():
    fj = FailedJoins(10, 60.0)
    for i in range(10):
        assert not fj.blocked(i)
        fj.record(i)
    assert fj.blocked(10) and fj.blocked(59.0)
    assert not fj.blocked(60.0 + 1)                                 # the window slid

    async def go():
        async with Rig() as r:
            ws = await connect(r.port)
            for _ in range(10):
                _, err = await join_code(r.port, "ZZZZ", ws=ws)
                assert err["code"] == "no_room"
            _, err = await join_code(r.port, "ZZZZ", ws=ws)
            assert err["code"] == "rate_limited"
            with pytest.raises(websockets.ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 2)
            ok, fresh = await create(r.port)                        # another connection is fine
            assert fresh["type"] == "hello"
            await ok.close()
    run(go())


def test_baseline_room_gives_seat_b_to_the_ai_at_once_and_join_is_full():
    async def go():
        async with Rig(codes=["AAAA"], rival="baseline") as r:
            wa, ha = await create(r.port)
            assert ha["seat"] == "A" and ha["code"] == "AAAA"
            await settle()
            assert r.made["AAAA"].state == "playing"
            await r.ticks(4)
            _, full = await join_code(r.port, "AAAA")
            assert full["code"] == "full"
            r.now[0] += ROOM_WAIT_S + 5                             # never "waits for a second player"
            await r.srv.pump()
            assert "AAAA" in r.srv.rooms
            await wa.close()
    run(go())


def test_the_trace_name_carries_the_room_code():
    from server.__main__ import trace_name
    assert "ABCD" in trace_name("ABCD", 3, 0)
    assert trace_name("ABCD", 3, 0) != trace_name("WXYZ", 3, 0)


def test_the_single_duel_lobby_still_works_without_a_factory():
    async def go():
        now = [0.0]
        srv = OnlineServer(Match(), clock=lambda: now[0])
        server = await srv.start("127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ws = await connect(port)
        await ws.send(json.dumps({"type": "join"}))
        h = await recv(ws)
        assert h["seat"] == "A" and "code" not in h
        await ws.close()
        server.close()
        await server.wait_closed()
    run(go())


def test_the_page_spelling_of_create_is_a_join_with_a_create_flag():
    async def go():
        async with Rig(codes=["AAAA"]) as r:
            ws = await connect(r.port)
            await ws.send(json.dumps({"type": "join", "create": True}))
            h = await recv(ws)
            assert h["type"] == "hello" and h["code"] == "AAAA" and h["seat"] == "A"
            await ws.close()
    run(go())


def test_create_without_rooms_enabled_is_refused():
    async def go():
        srv = OnlineServer(Match())
        server = await srv.start("127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ws, err = await create(port)
        assert err["type"] == "error"
        await ws.close()
        server.close()
        await server.wait_closed()
    run(go())


def test_nothing_from_another_room_reaches_a_client():
    async def go():
        async with Rig(codes=["AAAA", "BBBB"]) as r:
            a1, h1 = await create(r.port)
            b1, hb1 = await join_code(r.port, "AAAA")
            a2, h2 = await create(r.port)
            b2, hb2 = await join_code(r.port, "BBBB")
            await settle()
            await r.ticks(12)
            seen1 = json.dumps(await drain(a1) + await drain(b1))
            seen2 = json.dumps(await drain(a2) + await drain(b2))
            for secret in ("BBBB", h2["token"], hb2["token"]):
                assert secret not in seen1
            for secret in ("AAAA", h1["token"], hb1["token"]):
                assert secret not in seen2
            for w in (a1, b1, a2, b2):
                await w.close()
    run(go())

"""T18 Gate 2 (evaluation specialist): server-to-client boundary of the room codes (#52, #56).

Nothing crosses rooms or seats, codes never derive from the duel RNG, the code-less default
room is isolated from coded rooms, and each room's `--rival baseline` seat sees only its own
observation. Localhost sockets and an injected clock only; no network, no keys.
Tests marked xfail(strict=True) reproduce a finding; whoever fixes it removes the mark.
(EVAL-T18-1 was fixed in T18-fix1 and its mark removed at Gate 2.)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import random
import re
import threading
import time
from pathlib import Path

import pytest

websockets = pytest.importorskip("websockets")

from server import rooms as rooms_mod                    # noqa: E402
from server.app import OnlineServer                      # noqa: E402
from server.match import Match, TICK_S                   # noqa: E402
from server.rooms import ROOM_WAIT_S, make_code, normalize_code   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 90))


async def settle(ms=60):
    await asyncio.sleep(ms / 1000)


async def drain(ws):
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except asyncio.TimeoutError:
            return out


async def recv(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), 2))


async def open_ws(port):
    return await websockets.connect(f"ws://127.0.0.1:{port}/ws")


async def create(port):
    ws = await open_ws(port)
    await ws.send(json.dumps({"type": "create"}))
    return ws, await recv(ws)


async def join(port, code=None, token=None):
    ws = await open_ws(port)
    msg = {"type": "join"}
    if code is not None:
        msg["code"] = code
    if token:
        msg["token"] = token
    await ws.send(json.dumps(msg))
    return ws, await recv(ws)


class Spy:
    """Controller recording exactly what its room's AI seat is given."""
    name, kind = "spy", "scripted"

    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def reset(self, seed):
        pass

    def decide(self, obs, legal):
        self.calls.append((json.dumps(obs, sort_keys=True), tuple(legal)))
        if self.fail:
            raise RuntimeError("boom")
        return "WAIT"


class Rig:
    def __init__(self, codes, rival=None, spies=False, default_rival=None, default=False, on_finish=None,
                 **kw):
        self.now = [100.0]
        self.made: dict[str, Match] = {}
        self.spies: dict[str, Spy] = {}
        seq = iter(codes)

        def build(code, rv, fin=None):
            m = Match(seed=0, rival=rv, rival_budget_s=1.0, on_finish=fin)
            if spies and rv == "baseline":
                self.spies[code] = Spy()
                m.game.rival.inner.controller = self.spies[code]
            self.made[code] = m
            return m

        self.default_match = build("HOME", default_rival) if default else None
        self.srv = OnlineServer(self.default_match, clock=lambda: self.now[0],
                                match_factory=lambda c: build(c, rival, (on_finish or {}).get(c)),
                                code_factory=lambda: next(seq), **kw)

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()
        for m in self.made.values():
            m.close()

    async def ticks(self, n):
        for _ in range(n):
            self.now[0] += TICK_S
            await self.srv.pump()
        await settle()


# --- codes never derive from the duel RNG --------------------------------------------------

def test_code_generation_never_touches_the_global_or_the_duel_rng():
    random.seed(12345)
    before = random.getstate()
    codes = {make_code() for _ in range(200)}
    assert random.getstate() == before, "make_code consumed the global `random` stream"
    assert len(codes) > 190                        # OS entropy: not a fixed or tiny sequence
    src = inspect.getsource(rooms_mod)
    assert "SystemRandom" in src
    assert not re.search(r"\bseed\b", re.sub(r'""".*?"""|#.*', "", src, flags=re.S)), \
        "rooms.py reads a seed somewhere outside comments and docstrings"
    for name in ("app.py", "rooms.py"):                # the server layer never owns a seeded RNG
        text = (ROOT / "server" / name).read_text()
        assert not re.search(r"random\.Random\(|random\.seed\(|\.seed\b", text), name


def test_rooms_with_the_same_duel_seed_get_different_codes_and_the_code_is_not_in_the_trace():
    async def go():
        async with Rig(["AAAA", "BBBB"]) as r:
            a, ha = await create(r.port)
            b, hb = await create(r.port)
            assert ha["code"] != hb["code"]                          # same seed 0, different codes
            for code in ("AAAA", "BBBB"):
                assert code not in json.dumps(r.made[code].trace())  # the code is a server label only
                assert r.made[code].seed == 0
            await a.close(), await b.close()
    run(go())


# --- cross-room and cross-seat: what a client can ever receive -------------------------------

def test_every_message_a_client_gets_names_only_its_own_room_and_seat():
    """Four rooms (default + three coded), every client's whole stream scanned for any
    other room's code, any token but its own, and the other seat's token."""
    async def go():
        async with Rig(["AAAA", "BBBB", "CCCC"], default=True) as r:
            clients = {}                                 # name -> (ws, hello)
            clients["d1"] = await join(r.port)
            clients["d2"] = await join(r.port)
            for code in ("AAAA", "BBBB", "CCCC"):
                clients[code + "1"] = await create(r.port)
                clients[code + "2"] = await join(r.port, code.lower())
            await settle()
            await r.ticks(30)
            streams = {k: json.dumps(await drain(ws)) for k, (ws, _) in clients.items()}
            tokens = {k: h["token"] for k, (_, h) in clients.items()}
            for k, text in streams.items():
                room = k[:-1]
                for other_room in ("AAAA", "BBBB", "CCCC"):
                    if other_room != room:
                        assert other_room not in text, (k, other_room)
                for k2, tok in tokens.items():
                    assert tok not in text, f"{k} received the token of {k2}"
                assert "HOME" not in text
            # every client is told its own seat and nothing but its own room's code
            for k, (_, h) in clients.items():
                assert set(h) <= {"type", "seat", "token", "rival", "code"}
                assert h.get("code") == (None if k.startswith("d") else k[:-1])
            for ws, _ in clients.values():
                await ws.close()
    run(go())


def test_state_messages_carry_only_the_documented_fields_in_a_coded_room():
    async def go():
        async with Rig(["AAAA"]) as r:
            a, _ = await create(r.port)
            b, _ = await join(r.port, "AAAA")
            await settle()
            await r.ticks(12)
            for ws in (a, b):
                msgs = await drain(ws)
                states = [m for m in msgs if m["type"] == "state"]
                assert states
                for m in states:
                    assert set(m) <= {"type", "seat", "rival", "seat_view", "draw", "hud", "outcome"}
                assert {m["type"] for m in msgs} <= {"state", "status"}
            await a.close(), await b.close()
    run(go())


def test_the_default_room_is_not_a_joinable_code_and_hello_has_no_code():
    """The CLI names the default room HOME for trace files; it contains O, so no typed code
    can ever reach it, and a client in it is never told that name."""
    assert normalize_code("HOME") is None and normalize_code("home") is None
    async def go():
        async with Rig(["AAAA"], default=True) as r:
            ws, h = await join(r.port)
            assert "code" not in h
            _, e = await join(r.port, "HOME")
            assert e["code"] == "no_room"
            await settle()
            assert "HOME" not in json.dumps(await drain(ws))
            await ws.close()
    run(go())


def test_default_room_survives_while_coded_rooms_expire_and_never_the_reverse():
    async def go():
        async with Rig(["AAAA"], default=True) as r:
            d, _ = await join(r.port)
            c, hc = await create(r.port)
            await c.close()
            await settle()
            r.now[0] += ROOM_WAIT_S + 1
            await r.srv.pump()
            assert "AAAA" not in r.srv.rooms and r.srv.default is not None
            _, e = await join(r.port, "AAAA")
            assert e["code"] == "no_room"
            # the default room's lone seat is untouched by the coded room's expiry
            assert r.default_match.connected.get("A") is True
            _, e2 = await join(r.port, "AAAA", token=hc["token"])        # old coded token, gone room
            assert e2["code"] == "no_room"
            await d.close()
    run(go())


# --- --rival baseline: one AI seat per room, isolated ---------------------------------------------

def test_each_baseline_room_has_its_own_controller_that_sees_only_its_own_observation():
    async def go():
        async with Rig(["AAAA", "BBBB"], rival="baseline", spies=True) as r:
            a, ha = await create(r.port)
            b, hb = await create(r.port)
            assert ha["seat"] == hb["seat"] == "A" and ha["rival"] is None
            await settle()
            await r.ticks(36)
            sa, sb = r.spies["AAAA"], r.spies["BBBB"]
            assert sa is not sb and sa.calls and sb.calls
            assert r.made["AAAA"].game is not r.made["BBBB"].game
            assert r.made["AAAA"].game.rival is not r.made["BBBB"].game.rival
            for m, spy in ((r.made["AAAA"], sa), (r.made["BBBB"], sb)):
                keys = set(m.episode.observe("B"))
                for obs_text, legal in spy.calls:
                    obs = json.loads(obs_text)
                    assert set(obs) == keys
                    assert all(isinstance(x, str) for x in legal)
                text = "\n".join(c[0] for c in spy.calls)
                for secret in ("AAAA", "BBBB", ha["token"], hb["token"], '"seed"', "token", "GameState"):
                    assert secret not in text
            await a.close(), await b.close()
    run(go())


def test_a_failing_ai_in_one_room_leaves_the_other_rooms_duel_byte_identical():
    def duel(fail_in_other):
        async def go():
            async with Rig(["AAAA", "BBBB"], rival="baseline") as r:
                a, _ = await create(r.port)
                b, _ = await create(r.port)
                bad = Spy(fail=fail_in_other)
                r.made["BBBB"].game.rival.inner.controller = bad
                good = r.made["AAAA"]
                await settle()
                await r.ticks(36)
                out = (good.trace()["ticks"], good.trace()["state_hash"], len(r.made["BBBB"]._fallbacks))
                await a.close(), await b.close()
                return out
        return run(go())
    base_ticks, base_hash, base_fb = duel(False)
    ticks, h, fb = duel(True)
    assert fb > 0 and base_fb == 0                  # room B really failed, and was counted as such
    assert (ticks, h) == (base_ticks, base_hash)    # room A did not notice


def test_the_baseline_seat_is_never_a_joinable_seat_and_default_baseline_is_separate():
    async def go():
        async with Rig(["AAAA"], rival="baseline", default=True, default_rival="baseline") as r:
            dws, dh = await join(r.port)                    # HOME: A, with the AI as B
            cws, ch = await create(r.port)                  # coded: A, with its own AI as B
            assert dh["seat"] == ch["seat"] == "A"
            _, full_d = await join(r.port)
            _, full_c = await join(r.port, "AAAA")
            assert full_d["code"] == full_c["code"] == "full"
            assert r.made["HOME"] is not r.made["AAAA"]
            assert r.made["HOME"].game.rival is not r.made["AAAA"].game.rival
            await settle()
            await r.ticks(12)
            assert r.made["HOME"].state == r.made["AAAA"].state == "playing"
            await dws.close(), await cws.close()
    run(go())


def test_expired_baseline_rooms_stop_their_worker_threads():
    async def go():
        codes = [f"{a}{a}{a}{a}" for a in "ABCDEF"]
        async with Rig(codes, rival="baseline") as r:
            before = threading.active_count()
            ws = []
            for _ in codes:
                w, _ = await create(r.port)
                ws.append(w)
            assert threading.active_count() >= before + len(codes)
            for w in ws:
                await w.close()
            await settle(200)
            r.now[0] += ROOM_WAIT_S + 60
            await r.srv.pump()
            assert not r.srv.rooms
            for _ in range(50):
                if threading.active_count() <= before:
                    break
                time.sleep(0.05)
            assert threading.active_count() <= before, "an expired room left its AI worker running"
    run(go())


# --- one room must not be able to stop the others --------------------------------------------------

def test_a_failing_trace_write_in_one_room_does_not_stop_the_other_rooms():
    def boom(trace):
        raise OSError("disk full")

    async def go():
        async with Rig(["AAAA", "BBBB"], on_finish={"AAAA": boom}) as r:
            a1, _ = await create(r.port)
            a2, _ = await join(r.port, "AAAA")
            b1, _ = await create(r.port)
            b2, _ = await join(r.port, "BBBB")
            await settle()
            frame_before = r.made["BBBB"].episode.outcome()["frames"]
            await a1.close()                        # seat A of room AAAA leaves: pause, then forfeit
            await settle()
            r.now[0] += 16                          # past the 15 s window: the duel ends, on_finish runs
            for _ in range(10):
                r.now[0] += TICK_S
                await r.srv.pump()                  # raises today; the CLI's run_ticks would die
            assert r.made["BBBB"].episode.outcome()["frames"] > frame_before
            for w in (a1, a2, b1, b2):
                await w.close()
    run(go())

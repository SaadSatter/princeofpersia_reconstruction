"""T22: the online server's three room modes. Real localhost sockets for the room tests
(`online` extra), pure `Match` tests otherwise.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from agents import modes
from server import modes as smodes
from server.match import TICK_S, Match

AI_LABEL, BASE_LABEL = "AI Model (trained)", "Baseline (scripted)"
ALLOWED_STATE = {"type", "seat", "rival", "seat_view", "draw", "hud", "outcome"}
FORBIDDEN = {"seed", "token", "_duel", "duel", "snapshot", "owner", "trap_owner", "rigged_by",
             "pending", "rng", "inputs", "invalid_inputs", "trace", "fallback", "fallbacks", "source"}


def walk(v):
    if isinstance(v, dict):
        for k, x in v.items():
            yield k
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def run_ticks(m, now, n):
    for _ in range(n):
        now += TICK_S
        m.advance(now)
    return now


def test_the_server_accepts_exactly_the_shared_mode_list():
    assert smodes.MODE_IDS == modes.MODE_IDS == ("ai", "baseline", "human")
    for mid, rival in (("ai", "ai"), ("baseline", "baseline"), ("human", None)):
        assert smodes.rival_for(mid) == rival
    with pytest.raises(modes.ModeError):
        smodes.rival_for("zzz")


@pytest.mark.parametrize("mode, label", [("ai", AI_LABEL), ("baseline", BASE_LABEL)])
def test_an_ai_room_fills_seat_b_starts_on_one_join_and_shows_the_honest_label(mode, label):
    m = smodes.make_match(mode, seed=2)
    assert m.state == "waiting"
    assert m.join(None, 0.0)["seat"] == "A" and m.state == "playing"
    assert m.join(None, 0.0) == {"ok": False, "code": "full"}
    run_ticks(m, 0.0, 120)
    st = [x for x in m.drain("A") if x["type"] == "state"]
    assert st and {x["rival"] for x in st} == {label}
    assert any(s == "B" for t in m.trace()["ticks"] for s, _ in t)


def test_an_ai_room_sends_nothing_beyond_its_own_seat_payload():
    m = smodes.make_match("ai", seed=918)
    m.join(None, 0.0)
    m.receive("A", json.dumps({"type": "keys", "keys": ["d", "g"]}), 0.0)
    run_ticks(m, 0.0, 150)
    msgs = m.drain("A")
    assert msgs
    for msg in msgs:
        if msg["type"] == "state":
            assert set(msg) <= ALLOWED_STATE and msg["seat"] == "A"
        else:
            assert set(msg) == {"type", "state", "text", "rematch"}
        assert not (set(walk(msg)) & FORBIDDEN), set(walk(msg)) & FORBIDDEN
    assert m.drain("B") == []                                  # there is no seat-B client


def test_the_default_budget_is_forty_milliseconds_and_a_slow_ai_seat_is_a_logged_fallback():
    import time
    from server.rival import DEFAULT_BUDGET_S, TimeLimitedRival
    assert DEFAULT_BUDGET_S == 0.04
    assert Match(seed=1, rival="ai")._rival_budget_s == 0.04

    class Slow:
        def __call__(self, obs, legal):
            time.sleep(0.5)
            return legal[0] if legal else None
    m = smodes.make_match("ai", seed=1, rival_budget_s=0.01)
    m.game.rival = TimeLimitedRival(Slow(), 0.01)
    m.join(None, 0.0)
    t0 = time.perf_counter()
    run_ticks(m, 0.0, 20)
    assert time.perf_counter() - t0 < 0.5
    fb = m.trace()["fallbacks"]
    assert fb and all(f["source"] == "fallback" and f["seat"] == "B" for f in fb)
    assert "fallback" not in json.dumps(m.drain("A"))


def test_a_policy_error_in_an_online_ai_room_is_logged_as_a_fallback_not_sent():
    m = smodes.make_match("ai", seed=4)
    m.join(None, 0.0)
    ctrl = m.game.rival.inner.controller

    def boom(obs):
        raise RuntimeError("x")
    ctrl.policy_macro.encoder.update = boom
    run_ticks(m, 0.0, 30)
    fb = m.trace()["fallbacks"]
    assert fb and {f["reason"] for f in fb} == {"policy_error"}
    assert all(f["source"] == "fallback" for f in fb)
    assert "policy" not in json.dumps([x for x in m.drain("A") if x["type"] == "state"][-1])


def test_rematch_is_one_press_against_an_ai_and_both_against_a_human():
    m = smodes.make_match("ai", seed=2)
    m.join(None, 0.0)
    now = run_ticks(m, 0.0, 3)
    m.episode._duel.terminal = "won:B"
    now = run_ticks(m, now, 2)
    assert m.state == "ended"
    m.receive("A", '{"type":"rematch"}', now)
    assert m.state == "playing"
    h = smodes.make_match("human", seed=2)
    h.join(None, 0.0)
    h.join(None, 0.0)
    now = run_ticks(h, 0.0, 3)
    h.episode._duel.terminal = "won:B"
    now = run_ticks(h, now, 2)
    h.receive("A", '{"type":"rematch"}', now)
    assert h.state == "ended"
    h.receive("B", '{"type":"rematch"}', now)
    assert h.state == "playing"


def test_the_trace_names_the_ai_rival_for_replays():
    m = smodes.make_match("ai", seed=2)
    m.join(None, 0.0)
    run_ticks(m, 0.0, 5)
    assert m.trace()["rival"] == "ai"


def test_the_server_checks_the_shipped_weights_before_it_starts(monkeypatch):
    from agents.rl import policy
    monkeypatch.setattr(policy, "SHIPPED_SHA256", "1" * 64)
    with pytest.raises(policy.WeightsError):
        modes.verify_shipped()
    from server.__main__ import main
    with pytest.raises(SystemExit) as e:
        main(["--rival", "ai", "--port", "0"])
    assert e.value.code not in (0, None)


# --- the room layer ---------------------------------------------------------------------------
websockets = pytest.importorskip("websockets")
from server.app import OnlineServer           # noqa: E402


def go(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


class Rig:
    def __init__(self):
        self.now = [100.0]
        self.made = {}
        codes = iter(["AAAA", "BBBB", "CCCC", "DDDD"])

        def factory(code, mode=None):
            self.made[code] = smodes.make_match(mode or "human", seed=0)
            return self.made[code]
        self.srv = OnlineServer(None, clock=lambda: self.now[0], match_factory=factory,
                                code_factory=lambda: next(codes))

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
        await asyncio.sleep(0.06)


async def create(port, mode):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    msg = {"type": "join", "create": True}
    if mode is not None:
        msg["mode"] = mode
    await ws.send(json.dumps(msg))
    return ws, json.loads(await asyncio.wait_for(ws.recv(), 2))


async def drain(ws):
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except asyncio.TimeoutError:
            return out


def test_the_room_creator_picks_the_mode_and_an_ai_room_starts_on_that_one_join():
    async def body():
        async with Rig() as r:
            wa, ha = await create(r.port, "ai")
            assert ha["type"] == "hello" and ha["seat"] == "A" and ha["rival"] is None
            await asyncio.sleep(0.05)
            assert r.made["AAAA"].rival == "ai" and r.made["AAAA"].state == "playing"
            await r.ticks(12)
            states = [m for m in await drain(wa) if m["type"] == "state"]
            assert states and {m["rival"] for m in states} == {AI_LABEL}
            wb, _ = await create(r.port, "baseline")
            assert r.made["BBBB"].rival == "baseline"
            wc, _ = await create(r.port, "human")
            assert r.made["CCCC"].rival is None and r.made["CCCC"].state == "waiting"
            for w in (wa, wb, wc):
                await w.close()
    go(body())


def test_an_unknown_mode_is_refused_and_no_room_is_made():
    async def body():
        async with Rig() as r:
            ws, msg = await create(r.port, "model")
            assert msg["type"] == "error" and msg["code"] == "bad_mode"
            assert r.made == {} and r.srv.rooms == {}
            await ws.close()
    go(body())


def test_a_create_without_a_mode_keeps_the_old_one_argument_factory_call():
    async def body():
        async with Rig() as r:
            ws, msg = await create(r.port, None)
            assert msg["type"] == "hello" and r.made["AAAA"].rival is None
            await ws.close()
    go(body())

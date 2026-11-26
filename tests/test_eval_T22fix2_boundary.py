"""T22-fix2 Gate 2 (evaluation specialist): the merge of the T22 modes with T20 telemetry.

Checks, with the shipped PPO rival and no network, training or held-out data:
 * the parity chain runner == game hook == server Match still holds on more seeds, with
   telemetry ON in the server room;
 * telemetry in an AI room changes neither the trace, the state hash, the final snapshot nor any
   client message, and logs only seat A's own facts (nothing of seat B, fallbacks, the policy,
   the weights hash);
 * the recorder ignores seat B's accepted inputs even when handed them;
 * the weights cache is keyed on (path, digest) and a wrong hash is refused warm and cold.
"""

from __future__ import annotations

import json
import random
import shutil

import pytest

from agents import modes
from agents.rl import policy
from agents.versus_baseline import make_baseline
from pop.versus import arena_episode
from pop.versus_runner import VersusLimits, VersusRunner, snapshot
from server import modes as room_modes
from server.match import TICK_S
from server.telemetry import Telemetry

SEEDS = (0, 1, 2, 5, 7, 11)
FRAMES = 720
KEYSETS = [[], ["d"], ["a"], ["w", "d"], ["f"], ["g"], ["t"], ["s"], ["d", "lshift"], ["right"]]


def _tele(tmp):
    return None if tmp is None else Telemetry(tmp, "EVAL", info={"build": "t"}, today=lambda: "2026-11-25")


def _hook_idle_a(seed):
    ep = arena_episode(seed)
    ep.reset(seed)
    b = modes.make_seat_rival("ai")
    b.reset(seed)
    while ep.outcome()["status"] == "ongoing" and ep.outcome()["frames"] < FRAMES:
        modes.step_ai_seat(ep, b, "B")
        ep.tick()
    return ep


def _server_idle_a(seed, tmp):
    m = room_modes.make_match("ai", seed=seed, telemetry=_tele(tmp), rival_budget_s=5.0)
    m.join(None, 0.0)
    for _ in range(FRAMES):
        m._tick()
        m.drain("A")
    return m


def _hook_and_runner(seed):
    ep = arena_episode(seed)
    ep.reset(seed)
    a = modes._rival_class()(make_baseline(), "baseline")
    b = modes.make_seat_rival("ai")
    a.reset(seed)
    b.reset(seed)
    while ep.outcome()["status"] == "ongoing" and ep.outcome()["frames"] < FRAMES:
        modes.step_ai_seat(ep, a, "A")
        modes.step_ai_seat(ep, b, "B")
        ep.tick()
    res = VersusRunner(lambda: arena_episode(seed),
                       {"A": make_baseline(),
                        "B": policy.make_rl_rival(policy.SHIPPED_WEIGHTS, policy.SHIPPED_SHA256)},
                       limits=VersusLimits(max_frames=FRAMES), threaded=False).run(seed)
    return snapshot(ep), res["final_snapshot"], b


@pytest.mark.parametrize("seed", SEEDS)
def test_game_hook_equals_runner_after_the_merge(seed):
    hook, runner, b = _hook_and_runner(seed)
    assert hook == runner
    assert b.policy_errors == 0 and b.fallback_log == []


@pytest.mark.parametrize("seed", SEEDS)
def test_server_match_equals_game_hook_with_telemetry_on(seed, tmp_path):
    m = _server_idle_a(seed, tmp_path)
    assert snapshot(m.episode) == snapshot(_hook_idle_a(seed))
    assert m._fallback_counts() == (0, 0, 0) and m._fallbacks == []
    assert [p.name for p in tmp_path.glob("*.jsonl")] == ["2026-11-25-EVAL-001-A.jsonl"]


@pytest.mark.parametrize("seed", (3, 9))
def test_telemetry_changes_nothing_in_an_ai_room_with_a_busy_human(seed, tmp_path):
    outs = []
    for tmp in (None, tmp_path):
        m = room_modes.make_match("ai", seed=seed, telemetry=_tele(tmp), rival_budget_s=5.0)
        m.join(None, 0.0)
        rng, now, sent = random.Random(seed), 0.0, []
        for i in range(900):
            if i % 5 == 0:
                m.receive("A", json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
            now += TICK_S
            m.advance(now)
            sent += m.drain("A")
        outs.append((m.trace(), json.dumps(sent), snapshot(m.episode)))
    assert outs[0] == outs[1]
    assert outs[0][0]["state_hash"] == outs[1][0]["state_hash"]


def test_ai_room_logs_hold_only_seat_a_even_with_many_fallbacks(tmp_path):
    m = room_modes.make_match("ai", seed=4, telemetry=_tele(tmp_path), rival_budget_s=0.0)
    m.join(None, 0.0)
    rng, now = random.Random(4), 0.0
    for i in range(400):
        if i % 5 == 0:
            m.receive("A", json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
        now += TICK_S
        m.advance(now)
        for msg in m.drain("A"):
            assert "fallback" not in json.dumps(msg).lower()
    m.close_telemetry("abandoned")
    assert m.trace()["fallbacks"], "the probe must exercise fallbacks"
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["2026-11-25-EVAL-001-A.jsonl", "2026-11-25-EVAL-001-host.json"]
    sha = policy.SHIPPED_SHA256.lower()
    for p in tmp_path.iterdir():
        text = p.read_text().lower()
        for word in ("fallback", "source", "policy", "ppo", "macro", "weights", sha, "seat b", '"b"'):
            assert word not in text, (p.name, word)
    rows = [json.loads(x) for x in (tmp_path / files[0]).read_text().splitlines()]
    assert {r.get("seat") for r in rows if "seat" in r} == {"A"}


def test_recorder_ignores_seat_b_inputs_even_when_handed_them(tmp_path):
    logs = []
    for sub, extra in (("plain", False), ("fed", True)):
        out = tmp_path / sub
        m = room_modes.make_match("ai", seed=6, telemetry=_tele(out), rival_budget_s=5.0)
        m.join(None, 0.0)
        if extra:
            real = m._rec.after_tick
            m._rec.after_tick = lambda acc, now, real=real: real(
                list(acc) + [("B", "DRAW"), ("B", "RIGHT"), ("B", "TAKE")], now)
        rng, now = random.Random(6), 0.0
        for i in range(300):
            if i % 5 == 0:
                m.receive("A", json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
            now += TICK_S
            m.advance(now)
            m.drain("A")
        m.close_telemetry("abandoned")
        logs.append((out / "2026-11-25-EVAL-001-A.jsonl").read_text())
    assert logs[0] == logs[1]


def test_human_room_still_logs_each_seat_in_its_own_file_only(tmp_path):
    m = room_modes.make_match("human", seed=3, telemetry=_tele(tmp_path))
    m.join(None, 0.0)
    m.join(None, 0.0)
    for i in range(200):
        m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), 0.0)
        m.receive("B", json.dumps({"type": "keys", "keys": ["t"] if i == 3 else []}), 0.0)
        m.advance((i + 1) * TICK_S)
    for seat in ("A", "B"):
        rows = [json.loads(x) for x in
                (tmp_path / f"2026-11-25-EVAL-001-{seat}.jsonl").read_text().splitlines()]
        assert {r["seat"] for r in rows if "seat" in r} == {seat}


def test_weights_cache_keyed_on_path_and_digest_and_refuses_a_wrong_hash(tmp_path):
    src = policy.SHIPPED_WEIGHTS
    copy = tmp_path / ("w" + __import__("pathlib").Path(src).suffix)
    shutil.copy(src, copy)
    modes._NET_CACHE.clear()
    n1 = modes._shared_net(policy, copy, policy.SHIPPED_SHA256)
    assert modes._shared_net(policy, copy, policy.SHIPPED_SHA256) is n1
    assert any(isinstance(k, tuple) and len(k) == 2 and k[1] == policy.SHIPPED_SHA256.lower()
               for k in modes._NET_CACHE)
    with pytest.raises(policy.WeightsError):
        modes._shared_net(policy, copy, "0" * 64)          # warm cache, wrong hash: refused
    data = bytearray(copy.read_bytes())
    data[len(data) // 2] ^= 1
    copy.write_bytes(bytes(data))
    with pytest.raises(policy.WeightsError):
        modes._shared_net(policy, copy, policy.SHIPPED_SHA256)   # same path, edited: refused
    modes._NET_CACHE.clear()

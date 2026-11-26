"""Gate 2 (Evaluation Specialist) probes of the T14 web payload and rival hook."""

from __future__ import annotations

import json
import random

import pytest

from web.bridge import IdleRival, RandomRival, WebGame

KNOWN_REASONS = {None, "won:A", "won:B", "draw:both_died", "draw:time_up"}
TOP_KEYS = {"mode", "seat", "rival", "seat_view", "draw", "hud", "outcome"}


def _keys(rng):
    return {k: rng.random() < 0.3 for k in ("a", "d", "w", "s", "f", "g", "t", "lshift")}


def test_ai_payload_top_level_and_outcome_keys_are_closed():
    g = WebGame(seed=5, rival=RandomRival(5))
    rng = random.Random(1)
    for t in range(240):
        if t % 12 == 0:
            keys = _keys(rng)
        g.press(keys)
        p = g.tick()
        assert set(p) == TOP_KEYS
        assert set(p["outcome"]) == {"status", "reason", "result"}
        assert p["outcome"]["reason"] in KNOWN_REASONS
        assert "seed" not in json.dumps(p) and "_duel" not in json.dumps(p)


def test_rival_hook_cannot_alter_engine_by_mutating_its_view():
    seen = []

    class Vandal:
        label = "test"

        def __call__(self, obs, legal):
            seen.append(sorted(obs))
            stack = [obs]
            while stack:
                v = stack.pop()
                it = v.items() if isinstance(v, dict) else enumerate(v)
                for k, x in list(it):
                    if isinstance(x, (dict, list)):
                        stack.append(x)
                    elif isinstance(x, str):
                        v[k] = "#"
            legal.clear()
            return None

    a, b = WebGame(seed=1, rival=Vandal()), WebGame(seed=1, rival=IdleRival())
    for _ in range(60):
        assert a.tick()["seat_view"] == b.tick()["seat_view"]
    assert seen and all("_duel" not in k and "seed" not in k for k in seen)


def test_ai_mode_outcome_keeps_the_raw_reason_by_decision_25():
    """DECISIONS #25 (Saad): the end screen states how the duel ended, so the raw
    reason stays in the payload. The evaluation gate's recommendation to hide it
    (draw:both_died tells the player the unseen rival died too) is declined."""
    from pop.versus import arena_episode
    ep = arena_episode(0)
    ep._duel.terminal = "won:B"
    g = WebGame(seed=0, episode=ep)
    o = g._outcome("A")
    assert o["reason"] == "won:B" and o["result"] == "lost"

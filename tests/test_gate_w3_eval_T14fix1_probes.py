"""Gate 2 (Evaluation Specialist) probes for T14-fix1: the AI seat's view and the neutral label."""

from __future__ import annotations

import json

from web.bridge import make_game


def test_the_neutral_payload_names_no_rival_kind_and_hides_fallbacks():
    for rival in ("baseline", "idle", "random"):
        g = make_game("human_vs_ai", "A", 3, rival, True)
        for _ in range(30):
            p = g.tick()
        text = json.dumps(p).lower()
        assert p["rival"] == "Rival"
        for word in ("baseline", "scripted", "fallback", "placeholder", "idle", "random", "ppo", "policy"):
            assert word not in text, (rival, word)


def test_the_ai_seat_is_called_with_only_its_own_observation_and_its_own_legal_actions():
    seen = []

    def spy(obs, legal):
        seen.append((obs, tuple(legal)))
        return None
    g = make_game("human_vs_ai", "A", 1, "baseline", True)
    g.rival = spy
    for _ in range(10):
        g.tick()
    from pop.versus import OBSERVATION_KEYS
    ep = g.episode
    assert seen and all(set(o) == set(OBSERVATION_KEYS) for o, _ in seen)
    assert all(o["me"]["row"] is not None for o, _ in seen)

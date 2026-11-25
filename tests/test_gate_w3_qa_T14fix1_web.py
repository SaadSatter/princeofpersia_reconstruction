"""Gate 1 (QA) tests for T14-fix1 (web adapter, defaults, neutral label, build hash)."""

from __future__ import annotations

import json
import re

from pop import versus as V
from web import bridge
from web.bridge import SeatControllerRival, make_game

HOLD_D = {"d": True}


def play(game, ticks, keys=HOLD_D):
    game.press(keys)
    return [json.dumps(game.tick(), sort_keys=True) for _ in range(ticks)]


class Mutator:
    """A hostile controller: scribbles over everything in the observation it is given."""
    kind, name = "scripted", "mutator"

    def __init__(self):
        self.seen = []

    def decide(self, obs, legal):
        self.seen.append(set(obs))
        def scribble(x):
            if isinstance(x, dict):
                for k in list(x):
                    scribble(x[k]); x[k] = 0 if not isinstance(x[k], (dict, list)) else x[k]
            elif isinstance(x, list):
                for i in range(len(x)):
                    scribble(x[i])
                x.clear()
        scribble(obs)
        return "WAIT"


def test_a_controller_that_scribbles_on_its_observation_cannot_change_the_duel():
    plain = bridge.WebGame(seed=3, rival=bridge.IdleRival())
    hostile_ctl = Mutator()
    hostile = bridge.WebGame(seed=3, rival=SeatControllerRival(hostile_ctl))
    a, b = play(plain, 120), play(hostile, 120)
    assert a == b or [json.loads(x)["seat_view"] for x in a] == [json.loads(x)["seat_view"] for x in b]
    assert hostile_ctl.seen and all(s == V.OBSERVATION_KEYS for s in hostile_ctl.seen)


def test_rival_seat_sees_exactly_the_observation_keys_of_its_own_seat_and_no_seed():
    ctl = Mutator()
    g = bridge.WebGame(seed=9, rival=SeatControllerRival(ctl))
    play(g, 30)
    assert ctl.seen and all(s == V.OBSERVATION_KEYS for s in ctl.seen)
    assert not any("seed" in s or "state_obj" in s for s in ctl.seen)


def test_1200_ticks_with_a_rematch_in_the_middle_have_no_invalid_inputs_and_no_fallbacks():
    for seat in ("A", "B"):
        g = make_game("human_vs_ai", seat, 5)
        play(g, 600, {"d": True} if seat == "A" else {"left": True})
        g.rematch()
        play(g, 600, {"d": True} if seat == "A" else {"left": True})
        o = g.episode.outcome()
        assert o["invalid_inputs"] == {"A": 0, "B": 0}, o
        assert g.rival.fallbacks == 0


def test_rematch_replays_the_same_duel_exactly():
    g = make_game("human_vs_ai", "A", 11)
    first = play(g, 300)
    g.rematch()
    assert play(g, 300) == first


def test_two_games_never_share_a_controller():
    a, b = make_game(seed=1), make_game(seed=1)
    assert a.rival is not b.rival and a.rival.controller is not b.rival.controller
    assert play(a, 200) == play(b, 200)


def test_the_adapter_survives_the_duel_ending_and_keeps_counts_flat():
    g = make_game("human_vs_ai", "A", 2)
    g.episode._duel.rivals["B"]._hurt(9, "died:stabbed")
    play(g, 30)
    assert g.episode.outcome()["status"] == "terminal"
    before = dict(g.episode.outcome()["invalid_inputs"])
    play(g, 60)
    assert g.episode.outcome()["invalid_inputs"] == before


def test_neutral_payload_differs_from_the_default_only_in_the_rival_label():
    a, b = make_game(seed=4), make_game(seed=4, neutral=True)
    for _ in range(40):
        pa, pb = a.tick(), b.tick()
        assert pb["rival"] == "Rival" and pa["rival"] != "Rival"
        pa2, pb2 = dict(pa), dict(pb)
        pa2.pop("rival"), pb2.pop("rival")
        assert pa2 == pb2


def test_the_default_rival_label_says_baseline_so_the_neutral_option_is_needed():
    assert "baseline" in make_game(seed=0).rival.label.lower() or "scripted" in make_game(seed=0).rival.label.lower()


def test_build_hash_is_short_hex_reproducible_and_changes_with_content(tmp_path):
    from tools.web import build as B
    m1 = B.build(tmp_path / "a")
    m2 = B.build(tmp_path / "b")
    assert re.fullmatch(r"[0-9a-f]{8}", m1["build"]) and m1["build"] == m2["build"]
    h = dict(m1["files"])
    h["web/bridge.py"] = "0" * 64
    assert B.build_hash(h) != m1["build"]
    assert str(tmp_path) not in json.dumps(m1)

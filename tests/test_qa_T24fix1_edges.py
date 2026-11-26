"""QA probes for T24-fix1 (Saad #101): at a ledge edge DOWN hangs, even over a body.

Differential: for every tile ahead, in both facings, DOWN over a body must hang exactly when the same
DOWN with no body hangs (the engine's own hang-down), and must take the uniform exactly when it does not.
"""
from __future__ import annotations

import json

import pytest

from pop import arena
from pop import tiles as T
from pop import versus as V
from pop.mechanics import GATE_MAX, Gate
from pop.versus import VersusEpisode

OWN_COL = 4
TILES = ["space", "floor", "wall", "gate_closed", "gate_open", "loose", "drop", "sword", "rubble", "spikes"]
SYM = {"space": T.SPACE, "floor": T.FLOOR, "wall": T.WALL, "gate_closed": T.GATE, "gate_open": T.GATE,
       "loose": T.LOOSE, "drop": T.DROP_PLATE, "sword": T.SWORD, "rubble": T.RUBBLE, "spikes": T.SPIKES}


def build(tile, facing, body, sword_own=False):
    posts = {}
    if body == "own":
        posts = {"down": (1, 0, (OWN_COL, OWN_COL), facing)}
    elif body == "ahead":
        posts = {"down": (1, 0, (OWN_COL + facing,) * 2, facing)}
    ep = VersusEpisode(arena.situation("A"),
                       dict(arena.STARTS, A=(1, 0, OWN_COL, facing), B=(3, 2, 7, -1)), 0, guard_posts=posts)
    d = ep._duel
    ahead = (1, 0, OWN_COL + facing)
    d.geom.set_tile(ahead, SYM[tile])
    if tile.startswith("gate"):
        d.mech.gates[ahead] = Gate(pos=GATE_MAX if tile == "gate_open" else 0)
    if sword_own:
        d.geom.set_tile((1, 0, OWN_COL), T.SWORD)
    if body:
        d.guards["down"].knock_out()
    return ep


def outcome(ep):
    r = ep._duel.rivals["A"]
    ep.step("A", "DOWN")
    for _ in range(V.TAKE_FRAMES + 20):
        ep.tick()
    return r.kid.posture == "hanging", r.disguised


@pytest.mark.parametrize("facing", [+1, -1])
@pytest.mark.parametrize("tile", TILES)
@pytest.mark.parametrize("body", ["own", "ahead"])
def test_down_hangs_exactly_when_it_would_without_a_body(tile, facing, body):
    ref_hang, ref_dis = outcome(build(tile, facing, None))
    assert ref_dis is False
    hang, dis = outcome(build(tile, facing, body))
    assert hang == ref_hang, (tile, facing, body)
    if hang:
        assert dis is False
    elif tile != "sword" or body == "own":
        assert dis is True, (tile, facing, body)


def test_sanity_cases_really_hang_and_really_take():
    for f in (+1, -1):
        assert outcome(build("space", f, "own"))[0] is True
        assert outcome(build("floor", f, "own")) == (False, True)
        assert outcome(build("wall", f, "own")) == (False, True)
        assert outcome(build("gate_closed", f, "own")) == (False, True)


@pytest.mark.parametrize("facing", [+1, -1])
def test_dropped_sword_on_own_cell_at_an_edge_never_takes_the_uniform(facing):
    ep = build("space", facing, "own")
    d = ep._duel
    r = d.rivals["A"]
    r.sword = "none"
    d.swords.append(r.kid.cell)
    assert r._kneel_target() == "sword"          # sword branch is unaffected by the hang test
    ep.step("A", "DOWN")
    for _ in range(V.TAKE_FRAMES + 20):
        ep.tick()
    assert r.disguised is False


@pytest.mark.parametrize("facing", [+1, -1])
@pytest.mark.parametrize("tile", ["space", "floor", "wall", "gate_closed", "loose"])
def test_take_still_takes_at_every_edge_case(tile, facing):
    ep = build(tile, facing, "own")
    r = ep._duel.rivals["A"]
    ep.step("A", "TAKE")
    for _ in range(V.TAKE_FRAMES + 2):
        ep.tick()
    assert r.disguised is True and r.kid.posture == "standing"


@pytest.mark.parametrize("start", [(2, 0, 1, +1), (2, 0, 2, -1)])
def test_other_seat_view_identical_for_down_take_and_take_take_away_from_edges(start):
    from tests.test_disguise import episode
    a, b = episode(a=start), episode(a=start)
    a.step("A", "DOWN")
    b.step("A", "TAKE")
    for _ in range(V.TAKE_FRAMES + 3):
        a.tick()
        b.tick()
        assert json.dumps(a.observe("B"), sort_keys=True) == json.dumps(b.observe("B"), sort_keys=True)
    assert a._duel.rivals["A"].disguised and b._duel.rivals["A"].disguised

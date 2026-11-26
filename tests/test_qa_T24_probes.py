"""QA probes for T24 (Saad #94): DOWN over or beside-and-facing a downed guard takes the
uniform. Adversarial edges beyond the Tech Lead's tests/test_t24_*.py."""
from __future__ import annotations

import json

import pytest

from pop import versus as V
from pop import tiles as T
from pop.versus_runner import digest, snapshot
from tests.test_disguise import episode, meter, run


def obs_pair(ep):
    return json.dumps({s: ep.observe(s) for s in "AB"}, sort_keys=True)


def over():
    return episode(a=(2, 0, 1, +1))


# ---- negative edges ----------------------------------------------------------
def test_beside_but_facing_away_does_not_take():
    ep = episode(a=(2, 0, 2, +1))                       # body at col 1, facing right
    assert "TAKE" not in ep.legal_actions("A")
    ep.step("A", "DOWN")
    run(ep, 20)
    assert not ep._duel.rivals["A"].disguised and ep._duel.guards["down"].uniform


def test_a_guard_that_is_not_downed_is_not_stripped():
    ep = episode(posts={"live": (2, 0, (1, 1), +1)}, a=(2, 0, 1, +1))
    d = ep._duel
    d.guards["live"].pause = 10_000
    assert not d.guards["live"].downed
    ep.step("A", "DOWN")
    run(ep, 20)
    assert not d.rivals["A"].disguised and d.guards["live"].uniform


def test_second_down_after_a_take_never_retakes():
    ep = over()
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 1)
    r = ep._duel.rivals["A"]
    assert r.disguised
    ep.step("A", "DOWN")
    run(ep, 20)
    assert r.disguised and ep._duel.guards["down"].uniform is False
    assert ep.observe("A")["last_result"]["effect"] != "no_uniform"


def test_down_potion_cell_uniform_wins_and_potion_stays():
    ep = over()
    d = ep._duel
    cell = d.rivals["A"].kid.cell
    d.geom.set_tile(cell, T.POTION)
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 1)
    assert d.rivals["A"].disguised
    assert d.geom.tile(cell) == T.POTION                 # not drunk
    assert ep.observe("A")["last_result"]["effect"] == "took_uniform"


def test_potion_cell_without_a_body_still_drinks():
    ep = episode(a=(2, 0, 4, +1))
    d = ep._duel
    d.geom.set_tile(d.rivals["A"].kid.cell, T.POTION)
    ep.step("A", "DOWN")
    run(ep, 20)
    assert ep.observe("A")["last_result"]["effect"] == "drank"


@pytest.mark.parametrize("sword,effect", [("sheathed", "took_uniform"), ("none", "took_sword")])
def test_sword_on_cell_armed_vs_unarmed(sword, effect):
    ep = over()
    d = ep._duel
    r = d.rivals["A"]
    r.sword = sword
    d.swords.append(r.kid.cell)
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 2)
    assert ep.observe("A")["last_result"]["effect"] == effect
    assert r.disguised == (effect == "took_uniform")


def test_other_rival_on_the_same_cell_does_not_change_the_take():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 1, -1))
    d = ep._duel
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 1)
    assert d.rivals["A"].disguised and not d.rivals["B"].disguised
    assert d.guards["down"].uniform is False


def test_trap_rigged_on_the_cell_does_not_stop_a_take():
    ep = over()
    d = ep._duel
    d.rigs[d.rivals["A"].kid.cell] = {"B": V.RIG_KIND}
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 1)
    assert d.rivals["A"].disguised


def test_two_downed_guards_in_reach_down_equals_take():
    posts = {"down": (2, 0, (1, 1), +1), "down2": (2, 0, (2, 2), +1)}
    res = {}
    for act in ("DOWN", "TAKE"):
        ep = episode(a=(2, 0, 2, -1), posts=posts)
        d = ep._duel
        d.guards["down2"].knock_out()
        ep.step("A", act)
        run(ep, V.TAKE_FRAMES + 1)
        res[act] = (d.rivals["A"].disguised, d.guards["down"].uniform, d.guards["down2"].uniform)
    assert res["DOWN"] == res["TAKE"]


def test_down_issued_mid_move_never_disguises_during_the_move_and_is_deterministic():
    def go():
        ep = episode(a=(2, 0, 5, -1))
        ep.step("A", "LEFT")
        ep.tick()
        ep.step("A", "DOWN")                             # accepted (queued) as in the base
        early = ep._duel.rivals["A"].disguised
        run(ep, 80)
        return early, digest(snapshot(ep))
    first = go()
    assert first[0] is False and first == go()


# ---- other seat, suspicion, determinism, legal actions --------------------------------
@pytest.mark.parametrize("start", [(2, 0, 1, +1), (2, 0, 2, -1)])
def test_whole_world_identical_for_down_and_take_including_suspicion(start):
    traces = {}
    for act in ("DOWN", "TAKE"):
        ep = episode(a=start)
        ep.step("A", act)
        t = []
        for _ in range(V.TAKE_FRAMES + 30):
            ep.tick()
            t.append((obs_pair(ep), meter(ep), json.dumps(ep.legal_actions("A")),
                      json.dumps(ep.legal_actions("B"))))
        traces[act] = (t, digest(snapshot(ep)))
    assert traces["DOWN"] == traces["TAKE"]


def test_legal_actions_unchanged_by_the_feature():
    ep = over()
    legal = ep.legal_actions("A")
    assert "DOWN" in legal and "TAKE" in legal
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 1)
    after = ep.legal_actions("A")
    assert "DOWN" in after and "TAKE" not in after


def test_determinism_same_seed_same_inputs_same_hash():
    def go():
        ep = over()
        ep.step("A", "DOWN")
        run(ep, 40)
        return digest(snapshot(ep))
    assert go() == go()


# ---- front ends: S key over a body disguises -----------------------------------------
@pytest.mark.parametrize("mode", ["human_vs_ai", "local_two_players"])
def test_webgame_s_key_disguises(mode):
    from web.bridge import WebGame
    g = WebGame(mode=mode, episode=over())
    g.press({"s": True})
    for _ in range(V.TAKE_FRAMES + 2):
        g.tick()
    g.press({})
    for _ in range(3):
        g.tick()
    assert g.episode._duel.rivals["A"].disguised


@pytest.mark.parametrize("rival", [None, "baseline"])
def test_server_match_s_key_disguises(rival):
    from server.match import TICK_S, Match
    m = Match(episode=over() if rival is None else None, rival=rival)
    m.join(None, 0.0)
    if rival is None:
        m.join(None, 0.0)
    else:                                                # baseline: the arena is rebuilt, stage a body
        d = m.episode._duel
        g = d.guards["barracks"]
        g.knock_out()
        r = d.rivals["A"]
        r.kid.room, r.kid.row, r.kid.col = g.cell[0], g.cell[1], g.cell[2]
        r.kid.facing = 1
        d.rivals["B"].kid.room = 3
    now = 0.0
    m.receive("A", json.dumps({"type": "keys", "keys": ["s"]}), now)
    for _ in range(V.TAKE_FRAMES + 3):
        now += TICK_S
        m.advance(now)
    assert m.episode._duel.rivals["A"].disguised
    assert m.episode._duel.rivals["A"].kid.posture != "dead"


def test_pygame_versus_input_maps_down_and_engine_takes():
    play = pytest.importorskip("play")
    act = play.versus_input({"down"}, False)
    assert act == "DOWN"
    ep = over()
    assert act in ep.legal_actions("A")
    ep.step("A", act)
    run(ep, V.TAKE_FRAMES + 1)
    assert ep._duel.rivals["A"].disguised

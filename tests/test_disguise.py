"""Disguise and suspicion, R-V17 to R-V21 (docs/final/VERSUS_SPEC.md Sections 5-6).

The Gatehouse's top row (room 2, row 0) is open floor. Posts used here:
`down` - a guard downed at col 1 (its uniform is taken in these tests);
`watch` - a live guard at col 8 facing left, frozen in place (pause) so its
sight is fixed.
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import physics as P
from pop import versus as V
from pop.versus import VersusEpisode

POSTS = {"down": (2, 0, (1, 1), +1), "watch": (2, 0, (8, 8), -1)}


def episode(a=(2, 0, 2, -1), b=(3, 2, 7, -1), posts=POSTS, seed=0) -> VersusEpisode:
    ep = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), seed,
                       guard_posts=posts)
    d = ep._duel
    if "down" in d.guards:
        d.guards["down"].knock_out()
    if "watch" in d.guards:
        d.guards["watch"].pause = 10_000                # holds still, always facing left
    return ep


def run(ep, n):
    for _ in range(n):
        ep.tick()


def take(ep, seat="A"):
    assert "TAKE" in ep.legal_actions(seat)
    ep.step(seat, "TAKE")
    run(ep, V.TAKE_FRAMES + 1)


def meter(ep, seat="A", guard="watch"):
    return ep._duel.suspicion.get((guard, seat), 0)


def disguise_directly(ep, seat="A"):
    r = ep._duel.rivals[seat]
    r.disguised, r.sword, r.stance = True, "sheathed", None


# R-V17 -------------------------------------------------------------------
def test_take_beside_a_downed_guard_disguises_in_12_frames():
    ep = episode()
    ep.step("A", "TAKE")
    run(ep, V.TAKE_FRAMES)
    assert ep.observe("A")["me"]["disguised"] is False
    run(ep, 1)
    me = ep.observe("A")["me"]
    assert me["disguised"] is True and me["armed"] is False
    assert ep._duel.guards["down"].uniform is False
    assert V.TAKE_FRAMES == 12


def test_take_needs_a_downed_uniformed_guard_ahead():
    ep = episode(a=(2, 0, 2, +1))                       # facing away from the downed guard
    assert "TAKE" not in ep.legal_actions("A")
    ep = episode()
    take(ep)
    ep2 = episode(b=(2, 0, 2, -1), a=(1, 2, 2, +1))     # B at the same spot after A took it
    ep2._duel.guards["down"].uniform = False
    assert "TAKE" not in ep2.legal_actions("B")         # one uniform per downed guard
    assert "TAKE" not in ep.legal_actions("A")          # already disguised


def test_taking_a_uniform_sheathes_a_drawn_sword():
    ep = episode()
    ep.step("A", "DRAW")
    run(ep, V.DRAW_FRAMES + 1)
    take(ep)
    assert ep._duel.rivals["A"].sword == "sheathed"


# R-V18 -------------------------------------------------------------------
def test_the_other_seat_sees_a_disguised_rival_exactly_as_a_guard():
    """Leak test: B's view of disguised A equals B's view of a real guard
    standing in the same cell and pose."""
    ep = episode(a=(2, 0, 4, -1), b=(2, 1, 0, +1), posts={})
    disguise_directly(ep)
    run(ep, 1)
    seen = [f for f in ep.observe("B")["figures"] if (f["row"], f["col"]) == (0, 4)]
    real = episode(a=(1, 2, 2, +1), b=(2, 1, 0, +1), posts={"fake": (2, 0, (4, 4), -1)})
    run(real, 1)
    guard = [f for f in real.observe("B")["figures"] if (f["row"], f["col"]) == (0, 4)]
    assert seen == guard and seen[0]["kind"] == "guard"


def test_a_disguised_rival_walking_is_observed_like_a_patrolling_guard():
    ep = episode(a=(2, 0, 4, -1), b=(2, 1, 0, +1), posts={})
    disguise_directly(ep)
    ep.step("A", "STEP_LEFT")
    run(ep, 3)
    fig = [f for f in ep.observe("B")["figures"] if f["kind"] == "guard"][0]
    real = episode(a=(1, 2, 2, +1), b=(2, 1, 0, +1), posts={"fake": (2, 0, (3, 4), -1)})
    real._duel.guards["fake"].col = 4
    run(real, 3)
    gfig = [f for f in real.observe("B")["figures"] if f["kind"] == "guard"][0]
    assert set(fig) == set(gfig) == V.FIGURE_KEYS
    assert set(fig["motion"]) == set(gfig["motion"])
    assert (fig["motion"]["effect"], fig["motion"]["frames"]) == \
        (gfig["motion"]["effect"], gfig["motion"]["frames"]) == ("moved", P.STEP)


def test_no_seat_or_disguise_flag_reaches_the_other_seat():
    ep = episode(a=(2, 0, 4, -1), b=(2, 1, 0, +1), posts={})
    disguise_directly(ep)
    run(ep, 1)
    obs = ep.observe("B")
    assert obs["me"]["disguised"] is False
    assert all(f["kind"] == "guard" for f in obs["figures"])
    text = json.dumps(obs["figures"])
    assert "rival" not in text and "disguis" not in text


def test_guards_ignore_a_disguised_rival():
    ep = episode(a=(2, 0, 5, -1))
    disguise_directly(ep)
    run(ep, 5)
    g = ep._duel.guards["watch"]
    assert g.target is None and not g.armed


# R-V19 / R-V20 -----------------------------------------------------------
def test_running_in_sight_raises_suspicion_by_4_a_frame():
    ep = episode(a=(2, 0, 5, -1))
    disguise_directly(ep)
    ep.step("A", "LEFT")
    run(ep, P.RUN)
    assert meter(ep) == 4 * P.RUN


def test_jumping_in_sight_raises_suspicion_by_6_a_frame():
    ep = episode(a=(2, 0, 5, -1))
    disguise_directly(ep)
    ep.step("A", "JUMP_LEFT")
    run(ep, 5)
    assert meter(ep) == 6 * 5


def test_walking_lowers_suspicion_by_2_a_frame():
    ep = episode(a=(2, 0, 5, -1))
    disguise_directly(ep)
    ep._duel.suspicion[("watch", "A")] = 50
    ep.step("A", "STEP_LEFT")
    run(ep, 4)
    assert meter(ep) == 50 - 2 * 4


def test_standing_still_next_to_a_guard_for_over_2_s_raises_it_by_1():
    ep = episode(a=(2, 0, 7, +1))
    disguise_directly(ep)
    run(ep, 24)
    assert meter(ep) == 0
    run(ep, 6)
    assert meter(ep) == 6


def test_out_of_sight_it_falls_by_2():
    ep = episode(a=(2, 0, 1, +1))                       # 7 cells: out of sight
    disguise_directly(ep)
    ep._duel.suspicion[("watch", "A")] = 20
    run(ep, 5)
    assert meter(ep) == 10


# R-V21 -------------------------------------------------------------------
def test_full_suspicion_breaks_the_disguise_and_the_guard_attacks():
    ep = episode(a=(2, 0, 5, -1))
    disguise_directly(ep)
    ep._duel.suspicion[("watch", "A")] = 98
    ep.step("A", "LEFT")
    run(ep, 2)
    assert ep.observe("A")["me"]["disguised"] is False
    run(ep, 1)
    assert ep._duel.guards["watch"].target == "A"


@pytest.mark.parametrize("act", ["DRAW", "SWEEP"])
def test_drawing_or_any_attack_breaks_the_disguise(act):
    ep = episode(a=(2, 0, 4, -1), posts={})
    disguise_directly(ep)
    ep.step("A", act)
    run(ep, 1)
    assert ep.observe("A")["me"]["disguised"] is False


def test_losing_a_heart_breaks_the_disguise_for_good():
    ep = episode(a=(2, 0, 4, -1), posts={})
    disguise_directly(ep)
    ep._duel._hit(ep._duel.rivals["A"], +1, "died:stabbed")
    run(ep, 1)
    assert ep.observe("A")["me"]["disguised"] is False


# what each seat sees (VERSUS_SPEC 6) -------------------------------------
def test_suspicion_is_shown_only_to_the_suspected_seat():
    ep = episode(a=(2, 0, 5, -1), b=(2, 1, 0, +1))
    disguise_directly(ep)
    ep.step("A", "LEFT")
    run(ep, 3)
    assert ep.observe("A")["suspicion"] == [{"row": 0, "col": 8, "level": meter(ep)}]
    assert meter(ep) > 0
    assert ep.observe("B")["suspicion"] == []
    assert "level" not in json.dumps(ep.observe("B"))


def test_disguise_and_suspicion_are_deterministic():
    def trace():
        ep = episode(a=(2, 0, 5, -1), seed=4)
        disguise_directly(ep)
        out = []
        for f in range(40):
            if f in (0, 10, 20):
                ep.step("A", ("LEFT", "STEP_RIGHT", "JUMP_LEFT")[f // 10])
            ep.tick()
            out.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
        return out
    assert trace() == trace()

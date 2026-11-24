"""T01-fix1: TAKE is always legal over a downed guard (R-V26, Saad 2026-11-23,
decision 15), figure order ignores who is behind a figure (L2), and a disguised
step toward the next room is masked (QA1, under R-V25)."""

from __future__ import annotations

from pop import arena
from pop.versus import VersusEpisode


def episode(a, b, posts):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0,
                         guard_posts=posts)


def downed_ahead(uniform: bool, me=(2, 0, 4, +1)):
    ep = episode((1, 2, 2, +1), me, {"g": (2, 0, (5, 5), -1)})
    g = ep._duel.guards["g"]
    g.knock_out()
    g.uniform = uniform
    ep.tick()
    return ep, g


def test_take_is_legal_over_a_body_whose_uniform_is_gone():
    ep, _ = downed_ahead(False)
    assert "TAKE" in ep.legal_actions("B")


def test_take_without_a_uniform_is_accepted_and_changes_nothing_else():
    ep, g = downed_ahead(False)
    assert ep.step("B", "TAKE")["accepted"]
    for _ in range(14):
        ep.tick()
    r = ep._duel.rivals["B"]
    assert not r.disguised and not g.uniform
    assert ep._duel.last_result["B"]["effect"] == "no_uniform"
    assert ep.outcome()["invalid_inputs"]["B"] == 0


def test_take_with_a_uniform_still_disguises():
    ep, g = downed_ahead(True)
    assert ep.step("B", "TAKE")["accepted"]
    for _ in range(14):
        ep.tick()
    assert ep._duel.rivals["B"].disguised and not g.uniform
    assert ep._duel.last_result["B"]["effect"] == "took_uniform"


def test_take_over_nobody_is_still_not_legal():
    ep = episode((1, 2, 2, +1), (2, 0, 4, +1), {})
    ep.tick()
    assert "TAKE" not in ep.legal_actions("B")


def test_the_other_seat_sees_the_same_with_or_without_a_uniform():
    obs = {}
    for uniform in (True, False):
        ep = episode((2, 0, 2, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})
        g = ep._duel.guards["g"]
        g.knock_out()
        g.uniform = uniform
        ep.tick()
        ep.step("B", "TAKE")
        frames = []
        for _ in range(11):                   # before the move ends and the disguise shows
            ep.tick()
            frames.append(ep.observe("A")["figures"])
        obs[uniform] = frames
    assert obs[True] == obs[False]


def _lingering(seat, other, wait):
    ep = episode(*((((2, 0, 7, +1), (2, 0, 1, +1)) if seat == "A"
                    else ((2, 0, 1, +1), (2, 0, 7, +1)))),
                 {"watch": (2, 0, (8, 8), -1)})
    for _ in range(120):
        if wait:
            ep.step(seat, "WAIT")
        ep.tick()
    return ep._duel.suspicion.get(("watch", seat), 0)


def test_repeated_wait_lingers_like_standing_idle_for_both_seats():
    """R-V19 (QA3, Saad 2026-11-23): over 2 s within 1 cell raises suspicion
    whether or not the rival re-sends WAIT."""
    for seat in ("A", "B"):
        idle = _lingering(seat, None, False)
        assert idle > 0
        assert _lingering(seat, None, True) == idle

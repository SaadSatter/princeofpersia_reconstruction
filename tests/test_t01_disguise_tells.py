"""T01: a disguised rival's moves as the other seat sees them (AUDIT-B F1, F2).

R-V18: the other seat observes a disguised rival exactly as a guard. A move
may differ from anything a guard shows only if it raises the watching
guard's suspicion by rule (R-V19, R-V24) or breaks the disguise (R-V21).
R-V24 (Saad, 2026-11-23, "Hopping should raise suspicion"): a hop straight up
in a guard's sight raises that guard's suspicion like a jump.
"""

from __future__ import annotations

import pytest

from pop import arena
from pop import guards as G
from pop import physics as P
from pop import versus as V
from pop.versus import VersusEpisode

# Every motion a guard can show (pop/guards.py Guard.motion): (effect, frames).
GUARD_MOTIONS = {("moved", G.PATROL_FRAMES), ("moved", G.CHASE_FRAMES),
                 ("turned", P.TURN), ("drew", G.ALERT_DRAW_FRAMES),
                 ("sheathed", G.ALERT_DRAW_FRAMES),
                 ("lunge", V.LUNGE_WINDUP + V.LUNGE_ACTIVE + V.LUNGE_RECOVERY)}


def episode(a, b, posts):
    ep = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0,
                       guard_posts=posts)
    for g in ep._duel.guards.values():
        g.pause = 10_000                                # holds still: sight stays fixed
    return ep


def disguise(ep, seat="A"):
    r = ep._duel.rivals[seat]
    r.disguised, r.sword, r.stance = True, "sheathed", None


def figure_at(obs, cell):
    found = [f for f in obs["figures"] if (f["row"], f["col"]) == cell]
    assert len(found) == 1
    return found[0]


def test_disguised_rival_waiting_is_observed_like_a_paused_guard():
    ep = episode((2, 0, 4, -1), (2, 1, 0, +1), {})
    disguise(ep)
    real = episode((1, 2, 2, +1), (2, 1, 0, +1), {"fake": (2, 0, (4, 4), -1)})
    real._duel.guards["fake"].pause = 0                  # an ordinary post-end pause
    ep.step("A", "WAIT")
    for _ in range(P.WAIT + 2):
        ep.tick()
        real.tick()
        seen = figure_at(ep.observe("B"), (0, 4))
        guard = figure_at(real.observe("B"), (0, 4))
        assert real._duel.guards["fake"].motion() is None
        assert seen == guard


# Scenarios: (A's start, B's start, a guard watching A from the same row, frozen).
SCENARIOS = {
    "open_floor_left": ((2, 0, 5, -1), (2, 1, 0, +1), (2, 0, (9, 9), -1)),
    "open_floor_right": ((2, 0, 5, +1), (2, 1, 0, +1), (2, 0, (9, 9), -1)),
    "facing_the_guard": ((2, 0, 6, +1), (2, 1, 0, +1), (2, 0, (8, 8), -1)),
    "edge_of_a_hole": ((1, 0, 7, +1), (1, 2, 1, +1), (1, 0, (3, 3), +1)),
    "against_a_wall": ((1, 0, 1, -1), (1, 2, 1, +1), (1, 0, (4, 4), -1)),
    "below_a_ledge": ((1, 1, 8, +1), (1, 2, 1, +1), (1, 1, (4, 4), +1)),
}


def _disguised_legal_inputs():
    out = []
    for name, (a, b, post) in SCENARIOS.items():
        ep = episode(a, b, {"watch": post})
        disguise(ep)
        out += [(name, act) for act in ep.legal_actions("A")]
    return out


@pytest.mark.parametrize("scenario,act", _disguised_legal_inputs())
def test_disguised_figure_motion_effects_are_guard_effects(scenario, act):
    """Every input a disguised, sheathed rival may send: the other seat sees a
    motion a guard can show (or none), or the move raises the watching guard's
    suspicion that frame, or the disguise is gone (the figure is a rival)."""
    a, b, post = SCENARIOS[scenario]
    ep = episode(a, b, {"watch": post})
    disguise(ep)
    d = ep._duel
    assert ep.step("A", act)["accepted"]
    before = 0
    for _ in range(30):
        ep.tick()
        k = d.rivals["A"].kid
        level = d.suspicion.get(("watch", "A"), 0)
        if k.room == a[0] and k.posture == "standing":
            fig = figure_at(ep.observe("B"), (k.row, k.col))
            m = fig["motion"]
            if fig["kind"] == "guard" and m is not None:
                shown = (m["effect"], m["frames"])
                assert shown in GUARD_MOTIONS or level > before, (act, shown, level)
        before = level
        if not d.busy("A") and d.pending["A"] is None:
            break


def test_hop_in_a_guards_sight_raises_suspicion_by_6_a_frame():
    """R-V24 (proposed +6/frame, the jumping or climbing step of R-V19)."""
    ep = episode((2, 0, 5, -1), (3, 2, 7, -1), {"watch": (2, 0, (8, 8), -1)})
    disguise(ep)
    ep.step("A", "UP")
    for _ in range(5):
        ep.tick()
    assert ep._duel.motion("A")["effect"] == "none"     # a hop, not a climb
    assert ep._duel.suspicion[("watch", "A")] == V.SUSPICION_LEAP * 5


def test_hop_out_of_a_guards_sight_raises_nothing():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1), {"watch": (2, 0, (8, 8), -1)})
    disguise(ep)
    ep.step("A", "UP")
    for _ in range(5):
        ep.tick()
    assert ep._duel.suspicion.get(("watch", "A"), 0) == 0


def test_crouching_is_not_a_hop():
    """DOWN on open floor has the same effect name ("none") as a hop; only the
    hop raises suspicion."""
    ep = episode((2, 0, 5, -1), (3, 2, 7, -1), {"watch": (2, 0, (8, 8), -1)})
    disguise(ep)
    ep.step("A", "DOWN")
    for _ in range(3):
        ep.tick()
    assert ep._duel.motion("A")["effect"] == "none"
    assert ep._duel.suspicion.get(("watch", "A"), 0) == 0


def test_undisguised_rival_motion_is_unchanged():
    """Only a disguised figure is masked: an undisguised rival's wait is still shown."""
    ep = episode((2, 0, 4, -1), (2, 1, 0, +1), {})
    ep.step("A", "WAIT")
    ep.tick()
    fig = figure_at(ep.observe("B"), (0, 4))
    assert fig["kind"] == "rival" and fig["motion"]["effect"] == "waited"


def test_the_disguised_rival_still_sees_its_own_move():
    ep = episode((2, 0, 4, -1), (2, 1, 0, +1), {})
    disguise(ep)
    ep.step("A", "WAIT")
    ep.tick()
    assert ep.observe("A")["me"]["motion"]["effect"] == "waited"

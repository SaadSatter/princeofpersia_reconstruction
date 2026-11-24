"""GATE-T01 (Evaluation Specialist): the knowledge boundary after T01 (83127cf).

Two kinds of test, written by the gate reviewer, not by the implementer:

- `xfail(strict=True)`: a hidden fact reaches a seat through a channel the
  other channels do not show (a leak). They fail today; a fix turns them
  into passes, and strict mode then flags the stale marker.
- plain tests that pin a *design tell* (something a watching player or a
  policy can legitimately use to tell a disguised rival from a guard). They
  pass today. They are evidence for evaluation design (I3 "Identify",
  baseline fairness), not defects; if a rule change removes a tell, the
  matching test should be updated with that decision.

No production code is changed here.
"""

from __future__ import annotations

import pytest

from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode, arena_episode


def episode(a, b, posts):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0,
                         guard_posts=posts)


def disguise(ep, seat="A"):
    r = ep._duel.rivals[seat]
    r.disguised, r.sword, r.stance = True, "sheathed", None


# --- leaks (fail today) -----------------------------------------------------

@pytest.mark.xfail(strict=True, reason="GATE-T01-eval-L1: a downed guard's uniform "
                   "(taken or not) is absent from the observation and the renderer, "
                   "but TAKE in legal_actions reveals it")
def test_legal_actions_reveal_nothing_the_observation_does_not():
    """B faces a downed guard. Whether a rival already took its uniform is not
    in B's observation (nor drawn), yet TAKE is legal only if it was not: an
    AI seat can probe a body to learn the other rival disguised itself."""
    seen = {}
    for stripped in (False, True):
        ep = episode((1, 2, 2, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})
        g = ep._duel.guards["g"]
        g.knock_out()
        g.uniform = not stripped
        ep.tick()
        seen[stripped] = (ep.observe("B"), ep.legal_actions("B"))
    assert seen[False][0] == seen[True][0]              # the observations are identical
    assert seen[False][1] == seen[True][1]              # ... so the legal actions must be


@pytest.mark.xfail(strict=True, reason="GATE-T01-eval-L2: figures tied on (row, col, "
                   "kind) keep insertion order, rivals before guards")
def test_figure_order_does_not_tell_a_disguised_rival_from_a_guard():
    """A standing 'guard' over a downed guard (a downed body can be walked onto):
    the list order is rival-first for the disguised rival, dict order for a
    real guard. The sort key should not leave the tie to insertion order."""
    fake = episode((2, 0, 5, -1), (2, 1, 0, +1), {"z_down": (2, 0, (5, 5), -1)})
    fake._duel.guards["z_down"].knock_out()
    disguise(fake)
    fake.tick()
    real = episode((1, 2, 2, +1), (2, 1, 0, +1),
                   {"a_down": (2, 0, (5, 5), -1), "real": (2, 0, (5, 5), -1)})
    real._duel.guards["a_down"].knock_out()
    real._duel.guards["real"].pause = 10_000
    real.tick()
    order = lambda ep: [f["posture"] for f in ep.observe("B")["figures"] if f["row"] == 0]
    assert order(fake) == order(real)


# --- design tells (pass today; evidence for I3 and the baseline) -----------

def test_tell_real_arena_guards_stand_still_only_at_patrol_ends_and_briefly():
    """Undisturbed, an arena guard is still (motion None) for at most 13 frames
    and only at its patrol ends; it never leaves its room and row. A 'guard'
    still elsewhere, still for longer, or seen outside rooms 4/5 row 2 is the
    disguised rival (the arena has one guard per room)."""
    ep = arena_episode()
    d = ep._duel
    longest = {n: 0 for n in d.guards}
    run = dict(longest)
    still_cols = {n: set() for n in d.guards}
    for _ in range(V.DUEL_FRAMES):
        ep.tick()
        for n, g in d.guards.items():
            if g.motion() is None:
                run[n] += 1
                still_cols[n].add(g.col)
                longest[n] = max(longest[n], run[n])
            else:
                run[n] = 0
    assert max(longest.values()) <= 13
    for n, g in d.guards.items():
        _, row, (c0, c1), *_ = arena.GUARD_POSTS[n]
        assert still_cols[n] <= {c0, c1}
        assert (g.room, g.row) == arena.GUARD_POSTS[n][:2]


def test_tell_a_real_guard_draws_on_an_undisguised_rival_in_front_a_disguised_one_never():
    """B (undisguised) one cell from a figure facing it: a real guard starts
    'drew' on the next frame; the disguised rival never does. A one-step
    classifier for I3, available to the scripted baseline too."""
    real = episode((1, 2, 2, +1), (2, 0, 3, +1), {"g": (2, 0, (6, 6), -1)})
    fake = episode((2, 0, 6, -1), (2, 0, 3, +1), {})
    disguise(fake)
    effects = {}
    for name, ep in (("real", real), ("fake", fake)):
        ep.tick()
        (fig,) = [f for f in ep.observe("B")["figures"] if f["col"] == 6]
        effects[name] = (fig["kind"], fig["motion"] and fig["motion"]["effect"])
    assert effects == {"real": ("guard", "drew"), "fake": ("guard", None)}


def test_tell_a_disguised_run_out_of_any_guards_sight_is_shown_at_no_cost():
    """R-V25 exempts moves that raise suspicion *by type*, not by actual cost:
    with no guard in sight, a run (moved/4 while unarmed, which no guard shows:
    guards run only to chase, sword drawn) is shown to B and costs nothing."""
    ep = episode((2, 0, 5, -1), (2, 1, 0, +1), {})
    disguise(ep)
    ep.step("A", "LEFT")
    ep.tick()
    (fig,) = [f for f in ep.observe("B")["figures"] if f["row"] == 0]
    m = fig["motion"]
    assert (fig["kind"], fig["armed"], m["effect"], m["frames"]) == ("guard", False, "moved", 4)
    assert ep._duel.suspicion == {} or not any(ep._duel.suspicion.values())


def test_tell_a_gap_between_moves_unless_the_next_input_is_queued_ahead():
    """A patrolling guard steps back to back; a disguised rival shows one frame
    of motion None between moves unless its controller sends the next input no
    later than the frame the current move ends (AUDIT-C tell c). At a ~4 s
    macro cadence this needs the macro layer to queue primitives ahead."""
    ep = episode((2, 0, 7, -1), (2, 1, 0, +1), {})
    disguise(ep)
    ep.step("A", "STEP_LEFT")
    shown = []
    for t in range(10):
        if t == 9:
            ep.step("A", "STEP_LEFT")                   # one frame after the rival was free
        ep.tick()
        (fig,) = [f for f in ep.observe("B")["figures"] if f["row"] == 0]
        shown.append(fig["motion"])
    assert shown[7]["frame"] == shown[7]["frames"]      # last frame of the first step
    assert shown[8] is None                             # the gap no guard shows


# --- metric semantics (AC4) ---------------------------------------------------

def test_metric_queueing_the_same_input_ahead_counts_as_replaced():
    """A macro executor that re-sends the same primitive while a move runs (to
    avoid the gap above) inflates replaced_inputs although nothing was
    overridden. The harness must not read replaced_inputs as 'wasted
    decisions' without this caveat."""
    ep = episode((2, 0, 7, -1), (3, 2, 7, -1), {})
    for t in range(17):
        if t % 4 == 0:
            ep.step("A", "STEP_LEFT")
        ep.tick()
    out = ep.outcome()
    assert out["replaced_inputs"]["A"] >= 1 and out["stale_inputs"]["A"] == 0


def test_metric_outcome_carries_both_seats_counts():
    """outcome() is global: it shows the other seat's input, invalid, stale and
    replaced counts while the duel runs. It must feed reporting and terminal
    reward only, never a seat's policy features."""
    ep = episode((2, 0, 5, -1), (3, 2, 7, -1), {})
    ep.step("A", "STEP_LEFT")
    out = ep.outcome()
    assert out["inputs"] == {"A": 1, "B": 0}
    assert set(out) >= {"stale_inputs", "replaced_inputs", "invalid_inputs"}

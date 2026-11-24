"""QA T02: disguise identity through `motion` (AUDIT-B F1, F2) at commit 13c7488.

R-V18: a disguised rival is observed exactly as a guard. The observation fields
were already equal for a figure standing still with no move; these tests look
at the `motion` a disguised rival shows the other seat while it acts.

Tests marked `xfail(strict=True)` fail against 13c7488 on purpose: they are QA
findings routed to the Tech Lead (T01). Strict means a fix makes them XPASS and
fail the suite, so the mark must then be removed (by whoever owns the fix, with
Saad's approval to edit this test).

What a real guard can show (pop/guards.py `Guard.motion`, `_decide`, `_start`):
  sheathed: no motion (paused or standing), "moved" over P.STEP (patrol),
            "turned" over P.TURN, "drew" over ALERT_DRAW_FRAMES
  drawn:    no motion, "moved" over P.RUN (chase), "sheathed" over
            ALERT_DRAW_FRAMES, "lunge" over the lunge's total frames
Every guard move ends standing.

Deterministic, offline, no keys.
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import guards as G
from pop import physics as P
from pop.versus import LUNGE_ACTIVE, LUNGE_RECOVERY, LUNGE_WINDUP, VersusEpisode

PARKED = (3, 2, 7, -1)
LUNGE_TOTAL = LUNGE_WINDUP + LUNGE_ACTIVE + LUNGE_RECOVERY

# (armed, effect, frames, to_posture) a guard figure can show; None = no motion.
GUARD_MOTIONS = {
    (False, None, None, None),
    (False, "moved", G.PATROL_FRAMES, "standing"),
    (False, "turned", P.TURN, "standing"),
    (False, "drew", G.ALERT_DRAW_FRAMES, "standing"),
    (True, None, None, None),
    (True, "moved", G.CHASE_FRAMES, "standing"),
    (True, "sheathed", G.ALERT_DRAW_FRAMES, "standing"),
    (True, "lunge", LUNGE_TOTAL, "standing"),
}


def episode(a, b, posts=None) -> VersusEpisode:
    ep = VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts=posts or {})
    for g in ep._duel.guards.values():
        g.pause = 10_000                       # stands still at its post
    return ep


def disguise(ep, seat):
    r = ep._duel.rivals[seat]
    r.disguised, r.sword, r.stance, r.stance_change = True, "sheathed", None, None


def shown(fig):
    m = fig["motion"]
    if m is None:
        return (fig["armed"], None, None, None)
    return (fig["armed"], m["effect"], m["frames"], m["to_posture"])


# --- F1 -------------------------------------------------------------------------
def test_qa_t02_disguised_wait_matches_paused_guard():
    """AUDIT-B F1 as a test. B (the observer) stands in room 2 row 1. In one game
    the disguised rival A stands at (2,0,4) facing left and sends WAIT; in the
    other A is parked out of sight and a real guard stands paused at (2,0,4)
    facing left. B's whole observation must be the same every frame."""
    def seen(real_guard):
        if real_guard:
            ep = episode(PARKED, (2, 1, 0, +1), {"g": (2, 0, (4, 4), -1)})
        else:
            ep = episode((2, 0, 4, -1), (2, 1, 0, +1))
            disguise(ep, "A")
            assert ep.step("A", "WAIT")["accepted"]
        out = []
        for _ in range(8):
            ep.tick()
            out.append(json.dumps(ep.observe("B"), sort_keys=True))
        return out
    assert seen(real_guard=False) == seen(real_guard=True)


# --- motion-effect set over every input a disguised, sheathed rival may send ------
EXPECTED_TELLS = {
    "WAIT": "T02-F1: 'waited' is not a guard motion and raises no suspicion",
    "UP": "T02-F2 / R-V24 (decided 2026-11-23, not built): the hop shows effect "
          "'none' over 8 frames and raises no suspicion",
    "DOWN": "T02-F2b: DOWN shows effect 'none' over 4 frames and raises no "
            "suspicion; no decision covers it yet",
}


def _cases():
    out = []
    for action in ("WAIT", "LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT", "JUMP_LEFT",
                   "JUMP_RIGHT", "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT", "UP", "DOWN",
                   "DRAW", "SWEEP"):
        out.append(pytest.param(action, id=action))
    return out


@pytest.mark.parametrize("action", _cases())
def test_qa_t02_disguised_motion_is_a_guard_motion_or_costs_the_disguise(action):
    """For each input a disguised, sheathed rival may legally send while a real
    guard watches it, every frame the other seat sees must either show a motion
    a real guard could show (GUARD_MOTIONS), or the act must cost the disguise
    by rule: the watching guard's suspicion rises during it (R-V19, R-V24) or
    the disguise breaks (R-V21).

    Room 2 row 0: the watching guard is held at col 1 facing right; disguised
    A stands at col 5 facing left (4 cells in front of the guard); the
    observer B stands at col 9, facing left, out of the guard's sight."""
    ep = episode((2, 0, 5, -1), (2, 0, 9, -1), {"watch": (2, 0, (1, 1), +1)})
    disguise(ep, "A")
    assert action in ep.legal_actions("A")
    assert ep.step("A", action)["accepted"]
    duel = ep._duel
    tells, suspicion = [], 0
    for _ in range(P.RUN + P.RUN_JUMP_FLIGHT + 2):
        ep.tick()
        suspicion = max(suspicion, duel.suspicion.get(("watch", "A"), 0))
        a_cell = duel.rivals["A"].kid.cell
        for fig in ep.observe("B")["figures"]:
            if (fig["row"], fig["col"]) == a_cell[1:] and a_cell[0] == 2:
                if fig["kind"] == "guard" and shown(fig) not in GUARD_MOTIONS:
                    tells.append(shown(fig))
    costs_disguise = suspicion > 0 or not duel.rivals["A"].disguised
    assert not tells or costs_disguise, (
        f"{action}: shown {sorted(set(tells), key=str)} with suspicion {suspicion} "
        f"and the disguise kept")


def test_qa_t02_disguised_hop_in_a_guards_sight_raises_suspicion():
    ep = episode((2, 0, 5, -1), PARKED, {"watch": (2, 0, (1, 1), +1)})
    disguise(ep, "A")
    assert ep.step("A", "UP")["accepted"]
    peak = 0
    for _ in range(P.JUMP_IN_PLACE + 1):
        ep.tick()
        peak = max(peak, ep._duel.suspicion.get(("watch", "A"), 0))
    assert peak > 0

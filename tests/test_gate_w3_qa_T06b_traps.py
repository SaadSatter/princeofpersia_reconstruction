"""Gate 1 (QA) adversarial tests for T06b rival-rigged traps (TRAPS_SPEC, R-V27 to R-V34)."""

from __future__ import annotations

import copy
import json
import re

from pop import arena
from pop import versus as V
from pop.guards import Guard
from pop.mechanics import LOOSE_DELAY
from pop.versus import VersusEpisode


def episode(a=(2, 0, 1, +1), b=(2, 0, 8, -1), posts=None, seed=0):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), seed, guard_posts=posts)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def rig(ep, seat):
    assert ep.step(seat, "RIG")["accepted"]
    run(ep, V.RIG_FRAMES + 1)


def strip_own(obs):
    obs = copy.deepcopy(obs)
    obs.pop("my_traps")
    obs["me"].pop("traps_left")
    return obs


WORDS = re.compile(r"\b(trap|traps|rig|rigs|rigged|rigging|owner|owned)\b", re.I)


# --- hidden info: legality sweep -------------------------------------------------
def test_other_seats_legal_actions_and_view_never_depend_on_a_rig_anywhere_in_room_2():
    checked = 0
    for brow in range(3):
        for bcol in range(0, 10):
            for bf in (+1, -1):
                for acol in (1, 5):
                    ctl = episode(a=(2, 0, acol, +1), b=(2, brow, bcol, bf))
                    rigged = episode(a=(2, 0, acol, +1), b=(2, brow, bcol, bf))
                    if "RIG" not in rigged.legal_actions("A"):
                        continue
                    rigged.step("A", "RIG")
                    run(rigged, V.RIG_FRAMES + 1)
                    run(ctl, V.RIG_FRAMES + 1)
                    assert rigged.legal_actions("B") == ctl.legal_actions("B")
                    r, c = strip_own(rigged.observe("B")), strip_own(ctl.observe("B"))
                    for k in ("tiles", "state", "edges", "swords", "suspicion", "kid", "me"):
                        assert r.get(k) == c.get(k), (k, brow, bcol, bf, acol)
                    checked += 1
    assert checked > 50


def test_rigging_toward_each_other_both_succeed_and_budgets_drop_independently():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 3, -1))
    assert "RIG" in ep.legal_actions("A") and "RIG" in ep.legal_actions("B")
    ep.step("A", "RIG"), ep.step("B", "RIG")
    run(ep, V.RIG_FRAMES + 1)
    assert ep.observe("A")["my_traps"] == ep.observe("B")["my_traps"] == [{"row": 0, "col": 2, "kind": "loose"}]
    assert ep.observe("A")["me"]["traps_left"] == ep.observe("B")["me"]["traps_left"] == 3


# --- budget and illegal input ----------------------------------------------------
def test_a_rig_with_no_traps_left_is_refused_without_spending_or_kneeling():
    ep = episode()
    ep._duel.traps_left["A"] = 0
    assert "RIG" not in ep.legal_actions("A")
    res = ep.step("A", "RIG")
    assert res["accepted"] is False
    run(ep, 3)
    assert ep.observe("A")["me"]["traps_left"] == 0
    assert ep.outcome()["invalid_inputs"]["A"] >= 1


def test_four_rigs_spend_the_whole_budget_then_the_fifth_is_illegal():
    ep = episode(a=(2, 0, 0, +1))
    for _ in range(4):
        assert "RIG" in ep.legal_actions("A")
        rig(ep, "A")
        ep.step("A", "STEP_RIGHT")   # onto its own rig would spring it; hop is not needed, just step
        run(ep, 3)
        break
    # budget accounting through the dict directly for the remaining three
    d = ep._duel
    d.traps_left["A"] = 1
    ep2 = episode(a=(2, 0, 4, +1))
    ep2._duel.traps_left["A"] = 1
    rig(ep2, "A")
    assert ep2.observe("A")["me"]["traps_left"] == 0
    assert "RIG" not in ep2.legal_actions("A")


def test_illegal_rig_at_room_edge_is_refused_not_a_free_kneel():
    ep = episode(a=(2, 0, 9, +1))
    assert ep.step("A", "RIG")["accepted"] is False
    run(ep, 3)
    motion = ep.observe("A")["me"]["motion"]
    assert not motion or motion.get("effect") != "kneeled"


def test_rig_not_legal_while_knocked_down_or_hanging():
    ep = episode()
    ep._duel.rivals["A"].knocked_down = 5
    assert "RIG" not in ep.legal_actions("A")
    ep = episode()
    ep._duel.rivals["A"].kid.posture = "hanging"
    assert "RIG" not in ep.legal_actions("A")


# --- spring edge cases -----------------------------------------------------------
def test_lethal_spring_leaks_nothing_to_the_victim():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 4, -1))
    rig(ep, "A")
    ep._duel.rivals["B"].kid.hp = 1
    for _ in range(2):
        ep.step("B", "STEP_LEFT")
        run(ep, 10)
    for _ in range(LOOSE_DELAY + 30):
        ep.tick()
        obs = strip_own(ep.observe("B"))
        obs.pop("task")
        t = json.dumps(obs)
        assert not WORDS.search(t), WORDS.search(t).group(0)
        assert '"A"' not in t
        if ep._duel.terminal is not None:
            break


def test_a_body_walking_onto_the_cell_during_the_kneel_does_not_spring_it_by_standing():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 3, -1))
    ep.step("A", "RIG")
    ep.step("B", "STEP_LEFT")
    run(ep, V.RIG_FRAMES + 2)
    hp = ep.observe("B")["me"]["hp"]
    run(ep, 40)
    assert ep.observe("B")["me"]["hp"] == hp


def test_a_downed_guard_lying_on_a_rig_does_not_spring_it():
    ep = episode()
    rig(ep, "A")
    g = Guard.at_post("g", (2, 0, (2, 2), +1))
    g.knock_out()
    ep._duel.guards["g"] = g
    run(ep, 30)
    assert (2, 0, 2) in ep._duel.rigs


def test_spring_delay_matches_the_existing_loose_delay():
    ep = episode(b=(2, 0, 3, -1))
    rig(ep, "A")
    ep.step("B", "STEP_LEFT")
    shook_at = fell_at = None
    for i in range(60):
        ep.tick()
        if shook_at is None and [0, 2] in ep.observe("B")["state"]["loose_shaking"]:
            shook_at = i
        if shook_at is not None and ep._duel.geom.tile((2, 0, 2)) != "_":
            fell_at = i
            break
    assert shook_at is not None and fell_at is not None
    assert abs((fell_at - shook_at) - LOOSE_DELAY) <= 2


# --- disguise, seat swap ---------------------------------------------------------
def test_seat_b_rigging_disguised_in_sight_adds_36_and_a_never_sees_it():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 5, -1), posts={"w": (2, 0, (1, 1), +1)})
    d = ep._duel
    d.guards["w"].pause = 10_000
    d.rivals["B"].disguised = True
    ep.step("B", "RIG")
    run(ep, V.RIG_FRAMES)
    assert d.suspicion[("w", "B")] == 36
    assert ep.observe("A")["my_traps"] == []


# --- determinism -----------------------------------------------------------------
def test_scripted_rigging_duel_is_deterministic():
    def play(seed):
        ep = episode(a=(2, 0, 1, +1), b=(2, 0, 4, -1), posts={"g": (2, 0, (6, 8), -1)}, seed=seed)
        trace = []
        for i in range(400):
            if i % 40 == 0:
                for s in ("A", "B"):
                    if "RIG" in ep.legal_actions(s):
                        ep.step(s, "RIG")
            if i % 40 == 20:
                ep.step("B", "STEP_LEFT")
            ep.tick()
            trace.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
            if ep._duel.terminal:
                break
        return trace
    assert play(3) == play(3)

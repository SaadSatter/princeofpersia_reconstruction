"""Gate 1 QA probes for T19 (decisions #53, #54, #55, item 3). Written by QA, not the Tech Lead.

Adversarial: the grace window over every floor cell of every arena room, both orders,
gaps 0 to 3, at walls and ledges, while disguised (R-V24/R-V25), with both seats acting
together, end to end through the hosted-page bridge, and determinism.
"""

from __future__ import annotations

import json
import random

import pytest

from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode
from render import versus_view
from web import bridge

FAR = (3, 2, 7, -1)
TICKS = 40


def episode(a, b=FAR, posts=None, seed=0) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, seed,
                         guard_posts={} if posts is None else posts)


def snap(ep, seat="A"):
    me = ep.observe(seat)["me"]
    room = ep._duel.rivals[seat].kid.room          # the observation hides the room id
    return (room, me["row"], me["col"], me["posture"], me["facing"])


def play(ep, script, ticks=TICKS, seat="A"):
    """script: {tick: action}. Returns the per-tick (effect, snapshot) trace."""
    trace = []
    for t in range(ticks):
        if t in script:
            ep.step(seat, script[t])
        ep.tick()
        m = ep.observe(seat)["me"]["motion"]
        trace.append((m["effect"] if m else None, snap(ep, seat)))
    return trace


CELLS = [(r, 2, c, f) for r in range(1, 7)
         for c, ch in enumerate(arena.ROOMS[r][2]) if ch in "_tP.^" for f in (+1, -1)]


# --- the window matrix over the whole arena ---------------------------------------------
@pytest.mark.parametrize("d", ["LEFT", "RIGHT"])
@pytest.mark.parametrize("gap", [0, 1, 2])
def test_direction_then_jump_ends_exactly_where_the_plain_jump_does_in_every_cell(d, gap):
    """For every bottom-row cell, a direction then a jump `gap` ticks later lands
    where the same jump pressed alone would: the window never changes a jump's
    distance, landing, bump or fall; it only decides which move starts."""
    bad = []
    for room, row, col, facing in CELLS:
        start = (room, row, col, facing)
        want = play(episode(start), {0: f"JUMP_{d}"})[-1][1]
        script = {0: f"JUMP_{d}"} if gap == 0 else {0: d, gap: f"JUMP_{d}"}
        got = play(episode(start), script)[-1][1]
        if got != want:
            bad.append((start, want, got))
    assert not bad, bad[:5]


@pytest.mark.parametrize("d", ["LEFT", "RIGHT"])
@pytest.mark.parametrize("gap", [0, 1, 2])
def test_jump_then_direction_ends_where_the_plain_jump_does_in_every_cell(d, gap):
    bad = []
    hops = 0
    for room, row, col, facing in CELLS:
        start = (room, row, col, facing)
        if "climbed" in [e for e, _ in play(episode(start), {0: "UP"}, 30)]:
            continue                      # UP under a ledge climbs: not a hop
        hops += 1
        want = play(episode(start), {0: f"JUMP_{d}"})[-1][1]
        script = {0: "UP", gap: d} if gap else {0: f"JUMP_{d}"}
        got = play(episode(start), script)[-1][1]
        if got != want:
            bad.append((start, want, got))
    assert hops > 30 and not bad, bad[:5]


@pytest.mark.parametrize("d", ["LEFT", "RIGHT"])
def test_three_ticks_apart_direction_then_jump_runs_first(d):
    """Gap 3 is two inputs: the run happens, the jump starts from the next cell."""
    sgn = 1 if d == "RIGHT" else -1
    tr = play(episode((2, 0, 4, sgn)), {0: d, 3: f"JUMP_{d}"}, 30)
    effects = [e for e, _ in tr]
    assert effects.index("flipped") >= 4
    assert tr[-1][1][2] == 4 + sgn + 3 * sgn


def test_the_window_is_not_sticky_a_second_pair_after_a_flip_works_again():
    tr = play(episode((2, 0, 1, +1)),
              {0: "RIGHT", 1: "JUMP_RIGHT", 25: "RIGHT", 26: "JUMP_RIGHT"}, 60)
    assert tr[-1][1][2] == 1 + 3 + 3
    starts = sum(1 for i, (e, _) in enumerate(tr)
                 if e == "flipped" and (i == 0 or tr[i - 1][0] != "flipped"))
    assert starts == 2


# --- walls and ledges ----------------------------------------------------------------
@pytest.mark.parametrize("gap", [0, 1, 2])
def test_into_a_wall_the_window_ends_where_the_plain_jump_does(gap):
    """Room 1 col 0 and room 3 col 9 are walls on every row."""
    for room, col, d, facing in ((1, 1, "LEFT", -1), (3, 8, "RIGHT", +1)):
        want = play(episode((room, 2, col, facing)), {0: f"JUMP_{d}"})[-1][1]
        script = {0: f"JUMP_{d}"} if gap == 0 else {0: d, gap: f"JUMP_{d}"}
        got = play(episode((room, 2, col, facing)), script)[-1][1]
        assert got == want
        assert got[2] not in (0, 9) and got[0] == room


@pytest.mark.parametrize("gap", [0, 1, 2])
def test_up_under_a_ledge_still_climbs_whatever_direction_came_first(gap):
    tr = play(episode((2, 2, 1, -1)), {0: "RIGHT", gap: "UP"} if gap else {0: "UP"}, 40)
    assert "climbed" in [e for e, _ in tr]


@pytest.mark.parametrize("gap", [1, 2])
def test_a_jump_at_a_gap_edge_lands_the_same_with_and_without_the_window(gap):
    """Room 1 middle floor has air at cols 1-2 (row 1)."""
    want = play(episode((1, 1, 3, -1)), {0: "JUMP_LEFT"})[-1][1]
    got = play(episode((1, 1, 3, -1)), {0: "LEFT", gap: "JUMP_LEFT"})[-1][1]
    assert got == want


# --- disguise: R-V24 suspicion and R-V25 masking ---------------------------------------------
POSTS = {"g": (2, 0, (6, 6), -1)}


def suspicion_peak(script, ticks=30):
    """Suspicion gained on the ticks A is in a flip or hop (what R-V19/R-V24 price)."""
    ep = episode((2, 0, 2, +1), posts=POSTS)
    ep._duel.rivals["A"].disguised = True
    gained = 0
    for t in range(ticks):
        if t in script:
            ep.step("A", script[t])
        before = sum(ep._duel.suspicion.values())
        ep.tick()
        m = ep.observe("A")["me"]["motion"]
        if m and m["effect"] in ("flipped", "jumped", "none") and m["frame"] <= 10:
            gained += sum(ep._duel.suspicion.values()) - before     # first 10 frames: the guard
            #                                                         patrol turns away later
    return gained


@pytest.mark.parametrize("gap", [0, 1, 2])
def test_a_disguised_grace_flip_raises_suspicion_like_a_plain_jump(gap):
    """R-V19/R-V24: the flip counts as a jump for suspicion, with a guard in sight."""
    plain = suspicion_peak({0: "JUMP_RIGHT"})
    assert plain > 0, "vacuous probe: the guard never saw the jump"
    script = {0: "JUMP_RIGHT"} if gap == 0 else {0: "RIGHT", gap: "JUMP_RIGHT"}
    assert suspicion_peak(script) == plain


@pytest.mark.parametrize("gap", [0, 1, 2])
def test_a_disguised_hop_turned_into_a_flip_raises_suspicion(gap):
    script = {0: "UP"} if gap == 0 else {0: "UP", gap: "RIGHT"}
    assert suspicion_peak(script) > 0


def seen_by_b(script):
    ep = episode((3, 0, 3, +1), (3, 2, 7, -1))
    ep._duel.rivals["A"].disguised = True
    effects, shapes = set(), set()
    for t in range(30):
        if t in script:
            ep.step("A", script[t])
        ep.tick()
        for fig in ep.observe("B")["figures"]:
            assert fig["kind"] == "guard"            # R-V18: never "rival"
            shapes.add(tuple(sorted(fig)))
            if fig["motion"] is not None:
                effects.add(fig["motion"]["effect"])
    return effects, shapes


@pytest.mark.parametrize("script", [
    {0: "RIGHT", 1: "JUMP_RIGHT"}, {0: "RIGHT", 2: "JUMP_RIGHT"}, {0: "UP", 1: "RIGHT"},
    {0: "UP", 2: "RIGHT"}, {0: "RUN_JUMP_RIGHT"}, {0: "RIGHT", 1: "UP"}])
def test_a_disguised_rival_in_the_window_shows_the_other_seat_nothing_a_plain_jump_would_not(script):
    """R-V25: the figure keeps the guard shape and only guard-legal or suspicion-raising
    effects (the plain jump's own, which R-V25 lets through) reach the other seat; the
    grace window must not add a new effect name (no `hopped`, no stray `moved` run
    frames beyond the guard's own chase run)."""
    plain_effects, plain_shapes = seen_by_b({0: "JUMP_RIGHT"})
    hop_effects, _ = seen_by_b({0: "UP"})          # a disguised hop is shown too (R-V24)
    plain_effects |= hop_effects
    effects, shapes = seen_by_b(script)
    guard_ok = {e for e, _ in V.GUARD_MOTIONS}
    assert effects <= plain_effects | guard_ok, effects - plain_effects
    assert shapes == plain_shapes


# --- both seats together ---------------------------------------------------------------
def pair_script(d, gap):
    return {0: f"JUMP_{d}"} if gap == 0 else {0: d, gap: f"JUMP_{d}"}


@pytest.mark.parametrize("gap_a", [0, 1, 2, 3])
@pytest.mark.parametrize("gap_b", [0, 1, 2, 3])
def test_both_seats_in_the_window_at_once_do_not_disturb_each_other(gap_a, gap_b):
    """A in room 2, B in room 4: each seat's trace equals its solo trace."""
    sa, sb = pair_script("RIGHT", gap_a), pair_script("LEFT", gap_b)
    solo_a = play(episode((2, 0, 2, +1), (4, 2, 8, -1)), sa)
    solo_b = play(episode((2, 0, 2, +1), (4, 2, 8, -1)), sb, seat="B")
    ep = episode((2, 0, 2, +1), (4, 2, 8, -1))
    both_a, both_b = [], []
    for t in range(TICKS):
        for seat, sc in (("A", sa), ("B", sb)):
            if t in sc:
                ep.step(seat, sc[t])
        ep.tick()
        for seat, out in (("A", both_a), ("B", both_b)):
            m = ep.observe(seat)["me"]["motion"]
            out.append((m["effect"] if m else None, snap(ep, seat)))
    assert both_a == solo_a and both_b == solo_b


def test_two_seats_flipping_toward_the_same_cell_never_end_sharing_it():
    ep = episode((2, 0, 2, +1), (2, 0, 8, -1))
    for t in range(60):
        if t == 0:
            ep.step("A", "RIGHT")
            ep.step("B", "LEFT")
        if t == 1:
            ep.step("A", "JUMP_RIGHT")
            ep.step("B", "JUMP_LEFT")
        ep.tick()
    a, b = snap(ep, "A"), snap(ep, "B")
    assert a[:3] != b[:3], (a, b)


def test_seat_b_gets_the_same_window_mirrored():
    ep = episode((2, 0, 2, +1), (3, 2, 7, -1))
    tr = play(ep, {0: "LEFT", 1: "JUMP_LEFT"}, seat="B")
    assert "flipped" in [e for e, _ in tr]
    assert tr[-1][1][2] == 4


# --- end to end through the hosted-page bridge (held keys, per tick) -----------------------
@pytest.mark.parametrize("gap", [0, 1, 2])
@pytest.mark.parametrize("order", ["dir_first"])
@pytest.mark.parametrize("scheme", [("d", "w"), ("right", "up")])
def test_held_keys_through_the_bridge_give_a_flip_not_a_run(gap, order, scheme):
    """A human holds the direction, adds up `gap` ticks later (or the reverse), and
    keeps both held. The first move is a flip, with either key set."""
    right, up = scheme
    first, second = (right, up) if order == "dir_first" else (up, right)
    g = bridge.WebGame(mode="human_vs_ai", seed=0, human_seat="A", art=bridge.load_art())
    effects = []
    for t in range(14):
        held = {first: True}
        if t >= gap:
            held[second] = True
        g.press(held)
        g.tick()
        m = g.episode.observe("A")["me"]["motion"]
        effects.append(m["effect"] if m else None)
    assert "flipped" in effects, effects
    assert effects.index("flipped") == gap, effects            # starts on the second press
    end = g.episode.observe("A")["me"]["col"]
    assert end in (2, 5), (end, effects)      # never a run's one-cell step before the flip


@pytest.mark.parametrize("gap", [0, 1, 2])
def test_held_up_then_a_direction_under_the_start_ledge_still_climbs(gap):
    """Seat A starts under a ledge: UP climbs (#53 keeps that); a direction pressed
    later in the window does not turn the climb into a flip."""
    g = bridge.WebGame(mode="human_vs_ai", seed=0, human_seat="A", art=bridge.load_art())
    effects = []
    for t in range(14):
        g.press({"up": True, **({"right": True} if t >= gap else {})})
        g.tick()
        m = g.episode.observe("A")["me"]["motion"]
        effects.append(m["effect"] if m else None)
    if gap == 0:
        assert effects[0] == "flipped"          # up and right together is JUMP_RIGHT, a jump
        return
    last_climb = max(i for i, e in enumerate(effects) if e == "climbed")
    assert effects[0] == "climbed"
    assert "flipped" not in effects[:last_climb], effects      # the climb is not turned into a flip


def test_opposing_directions_from_both_sets_do_not_crash_and_replay_identically():
    def run():
        g = bridge.WebGame(mode="human_vs_ai", seed=2, human_seat="A", art=bridge.load_art())
        out = []
        for t in range(40):
            g.press({"a": True, "right": True, "w": t % 3 == 0, "up": t % 5 == 0})
            g.tick()
            out.append(json.dumps(g.episode.observe("A")["me"], sort_keys=True))
        return out
    assert run() == run()


# --- kneel: what the other seat draws -------------------------------------------------------
def test_the_other_seat_never_draws_a_crouch_for_a_disguised_rivals_take():
    """R-V25/R-V33: a disguised B kneeling to take a uniform is a standing guard to A,
    so the drawn sprite for that figure is not the crouch strip."""
    ep = episode((2, 0, 2, +1), (2, 0, 4, +1), posts={"g": (2, 0, (5, 5), -1)})
    ep._duel.guards["g"].knock_out()
    ep.tick()
    ep.step("B", "TAKE")
    ep._duel.rivals["B"].disguised = True
    for _ in range(V.TAKE_FRAMES):
        ep.tick()
        for fig in ep.observe("A")["figures"]:
            if fig["kind"] == "guard" and fig["motion"] is not None:
                assert fig["motion"]["effect"] != "took_uniform", fig
        for fig in ep.observe("A")["figures"]:
            spr = versus_view.guard_sprite(fig, {"crouch": 6, "take": 5, "downed": 6})
            assert spr is None or spr.strip != "crouch", fig


# --- determinism and robustness ----------------------------------------------------------
ACTIONS = ["LEFT", "RIGHT", "UP", "DOWN", "JUMP_LEFT", "JUMP_RIGHT", "RUN_JUMP_LEFT",
           "RUN_JUMP_RIGHT", "STEP_LEFT", "STEP_RIGHT", "WAIT", "KICK", "TAKE", "DRAW"]


def fuzz_trace(seed, ticks=300):
    rng = random.Random(seed)
    a = (rng.randrange(1, 7), 2, rng.randrange(1, 9), rng.choice((-1, 1)))
    b = (rng.randrange(1, 7), 2, rng.randrange(1, 9), rng.choice((-1, 1)))
    ep = VersusEpisode(arena.situation("A"), {"A": a, "B": b}, seed, guard_posts=arena.GUARD_POSTS)
    out = []
    for _ in range(ticks):
        for seat in "AB":
            if rng.random() < 0.5:
                ep.step(seat, rng.choice(ACTIONS))
        ep.tick()
        out.append(json.dumps([ep.observe("A"), ep.observe("B")], sort_keys=True))
        if ep.outcome()["status"] != "running":
            break
    return out


@pytest.mark.parametrize("seed", range(12))
def test_random_two_seat_inputs_never_crash_and_replay_identically(seed):
    one = fuzz_trace(seed)
    assert one == fuzz_trace(seed)
    for line in one:
        for obs in json.loads(line):
            assert 0 <= obs["me"]["col"] <= 9

"""Gate 1 QA probes for T05-fix1 (commit ce8c8c0). Independent sweep: sampler seed 20261124,
own sampler (floor cells of every arena room, both facings, alternating seats). Offline."""

from __future__ import annotations

import random

import pytest

from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import RandomController, WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner

SLOW = lambda: 0.0                                                    # noqa: E731
SWEEP_SEED = 20261124


def _cells(room):
    return [(room, 2, c) for c, ch in enumerate(arena.ROOMS[room][2]) if ch in "_tP"]


def _sweep(other_cls, n, seed=SWEEP_SEED, frames=3600):
    rng = random.Random(seed)
    tally = {"W": 0, "L": 0, "T": 0}
    fallbacks = 0
    for k in range(n):
        ra, rb = rng.sample(range(1, 7), 2)
        a = rng.choice(_cells(ra)) + (rng.choice((-1, 1)),)
        b = rng.choice(_cells(rb)) + (rng.choice((-1, 1)),)
        mk = lambda a=a, b=b: VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, frames,  # noqa: E731
                                            arena.GUARD_POSTS)
        res = VersusRunner(mk, {"A": make_baseline("a"), "B": other_cls()}, swap_seats=bool(k % 2),
                           clock=SLOW, limits=VersusLimits(max_frames=frames)).run(k)
        slot = res["winner_slot"]
        tally["W" if slot == "A" else "L" if slot == "B" else "T"] += 1
        st = res["seats"]["A"]
        fallbacks += st["fallbacks"] if st["kind"] == "scripted" else 0
    return tally, fallbacks


@pytest.mark.parametrize("other", [WaitController, RandomController])
def test_qa_fix1_independent_random_start_sweep_beats_the_opponent(other):
    tally, _ = _sweep(other, 30)
    print(f"sweep seed {SWEEP_SEED} vs {other.__name__}: {tally}")
    assert tally["W"] > tally["L"] + tally["T"], tally


def test_qa_fix1_baseline_never_falls_back_in_the_independent_sweep():
    _, fb = _sweep(WaitController, 12, seed=SWEEP_SEED + 1)
    assert fb == 0


def test_qa_fix1_default_start_vs_wait():
    got = 0
    for seed in (4, 5, 6):
        for swap in (False, True):
            res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600,
                                                     arena.GUARD_POSTS),
                               {"A": make_baseline("a"), "B": WaitController()},
                               swap_seats=swap, clock=SLOW).run(seed)
            got += res["winner_slot"] == "A"
    print("default start vs WAIT wins", got, "/ 6")
    assert got >= 4


@pytest.mark.xfail(strict=True, reason="QA-F1: baseline loses in 78 frames to a WAIT seat from this start")
def test_qa_fix1_baseline_does_not_lose_to_wait_from_a_random_start():
    def mk():
        return VersusEpisode(arena.situation("A"), {"A": (5, 2, 0, -1), "B": (6, 2, 0, 1)}, 0, 3600,
                             arena.GUARD_POSTS)
    res = VersusRunner(mk, {"A": make_baseline("a"), "B": WaitController()}, swap_seats=True,
                       clock=SLOW, limits=VersusLimits(max_frames=3600)).run(17)
    assert res["winner_slot"] == "A", res["status"]

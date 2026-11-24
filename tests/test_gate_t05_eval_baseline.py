"""Gate 2 (Evaluation Specialist) probes for T05, commit 19b5da2.

Boundary probe passes; the two competence probes document findings and are
xfail(strict) so they flip loudly once fixed. Offline, deterministic.
"""

from __future__ import annotations

import collections

import pytest

from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner

A_START = (1, 2, 2, +1)


class _Logged(dict):
    used: collections.Counter = collections.Counter()

    def __init__(self, d, path):
        super().__init__({k: _wrap(v, f"{path}.{k}") for k, v in d.items()})
        self.path = path

    def __getitem__(self, k):
        _Logged.used[f"{self.path}.{k}"] += 1
        return super().__getitem__(k)

    def get(self, k, default=None):
        _Logged.used[f"{self.path}.{k}"] += 1
        return super().get(k, default)


def _wrap(v, path):
    if isinstance(v, dict):
        return _Logged(v, path)
    if isinstance(v, list):
        return [_wrap(x, path + "[]") for x in v]
    return v


class _Spy:
    kind = "scripted"
    name = "spy"

    def __init__(self, inner):
        self.inner = inner

    def reset(self, seed):
        self.inner.reset(seed)

    def decide(self, obs, legal):
        return self.inner.decide(_wrap(obs, "obs"), legal)


class _Staged(VersusEpisode):
    def __init__(self, *a, setup=None, **kw):
        self._setup = setup
        super().__init__(*a, **kw)

    def reset(self, seed):
        super().reset(seed)
        if self._setup:
            self._setup(self._duel)


ALLOWED_TOP = {"room", "edges", "tiles", "state", "kid", "me", "figures", "suspicion"}
ALLOWED_FIGURE = {"kind", "row", "col", "facing", "posture", "stance", "armed", "motion"}


def test_gate_t05_eval_baseline_reads_only_this_seats_visible_fields():
    """Boundary: over a disguised-rival duel with a real guard, a guard-room
    start, and a default start, the baseline reads no field outside the
    visible set (no task text, clock, swords list, seed or episode)."""
    _Logged.used = collections.Counter()
    setups = [
        ({"A": A_START, "B": (1, 2, 6, +1)}, {"g": (1, 2, (1, 8), +1)}, True),
        ({"A": (4, 2, 3, +1), "B": (1, 2, 2, +1)}, arena.GUARD_POSTS, False),
        (dict(arena.STARTS), arena.GUARD_POSTS, False),
    ]
    for starts, posts, disguise in setups:
        make = lambda s=starts, p=posts, d=disguise: _Staged(  # noqa: E731
            arena.situation("A"), s, 0, 900, p,
            setup=lambda duel: setattr(duel.rivals["B"], "disguised", d))
        VersusRunner(make, {"A": _Spy(make_baseline()), "B": WaitController()},
                     limits=VersusLimits(max_frames=900),
                     copy_mode="json", threaded=False).run(1)
    top = {k.split(".")[1].rstrip("[]") for k in _Logged.used}
    assert top <= ALLOWED_TOP, top - ALLOWED_TOP
    fig = {k.split(".")[2] for k in _Logged.used if k.startswith("obs.figures[].")}
    assert fig <= ALLOWED_FIGURE, fig - ALLOWED_FIGURE
    assert "obs.figures[].motion" in _Logged.used       # the tracker really ran on guards


def _wins_vs_wait(rival_start, posts, a_start=A_START, seeds=(0, 1)):
    wins = games = 0
    for swap in (0, 1):
        for seed in seeds:
            mine, theirs = a_start, rival_start
            starts = {"A": theirs, "B": mine} if swap else {"A": mine, "B": theirs}
            ctrls = ({"A": WaitController(), "B": make_baseline()} if swap
                     else {"A": make_baseline(), "B": WaitController()})
            res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), starts, 0, 3600, posts),
                               ctrls, limits=VersusLimits(max_frames=3600),
                               copy_mode="json", threaded=False).run(seed)
            games += 1
            wins += res["outcome"]["reason"] == ("won:B" if swap else "won:A")
    return wins, games


@pytest.mark.xfail(strict=True, reason="GATE-T05-eval-1: baseline loses to a passive WAIT seat "
                   "(8/8 duels) when it starts in a guard room; rule 5 fights a patrolling armed guard")
@pytest.mark.parametrize("room", [4, 5])
def test_gate_t05_eval_baseline_survives_a_guard_room_start(room):
    wins, games = _wins_vs_wait((3, 2, 7, -1), arena.GUARD_POSTS, a_start=(room, 2, 3, +1))
    assert wins > games / 2, (wins, games)


@pytest.mark.xfail(strict=True, reason="GATE-T05-eval-2: no macro descends a floor, so a passive "
                   "rival in rooms 4-6 is never found (draw 6/6) and no uniform is reachable")
@pytest.mark.parametrize("room,col", [(4, 3), (6, 5), (5, 7)])
def test_gate_t05_eval_baseline_finds_a_passive_rival_on_the_lower_floor(room, col):
    wins, games = _wins_vs_wait((room, 2, col, -1), {})
    assert wins > 0, (wins, games)

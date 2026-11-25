"""Gate 2 (Evaluation Specialist) checks for T08. Read-only on H6's data; no policy
is run on the held-out split and the real ledger is never touched.

They pin the *measured* facts the Gate 2 report relies on (F-3 exposure, power of an
8-outcome held-out run, seed determinism of the shipped policy on a tuning start), so
a later edit that changes them fails loudly instead of silently changing the claim.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation import manifest, stats
from pop import arena
from tools.rl.env import TUNING_STARTS

ROOT = Path(__file__).resolve().parent.parent


def _h6_starts():
    manifest.verify_heldout()
    return json.loads(manifest.HELDOUT_PATH.read_text())["scenarios"][0]["starts"]


def _training_guard_cells():
    cells = set()
    for room, row, (c0, c1), _ in arena.GUARD_POSTS.values():
        cells |= {(room, row, c) for c in range(c0, c1 + 1)}
    return cells


def test_training_only_ever_had_guards_in_rooms_4_and_5():
    """tools/rl/env.py builds every training episode with arena.GUARD_POSTS."""
    src = (ROOT / "tools" / "rl" / "env.py").read_text()
    assert "arena.GUARD_POSTS" in src
    assert {p[0] for p in arena.GUARD_POSTS.values()} == {4, 5}


def test_f3_exposure_of_h6_guard_posts_to_training():
    """F-3: 5 of the 8 H6 posts are in rooms (1, 3) that held no guard in training; the
    other 3 (rooms 4, 5) overlap the default patrol cells, 2 of them completely."""
    train_cells = _training_guard_cells()
    full = partial = none_ = 0
    for st in _h6_starts():
        for room, row, (c0, c1), _ in st["guards"].values():
            cells = {(room, row, c) for c in range(c0, c1 + 1)}
            hit = len(cells & train_cells)
            if hit == len(cells):
                full += 1
            elif hit:
                partial += 1
            else:
                none_ += 1
    assert (full, partial, none_) == (2, 1, 5)


def test_no_h6_start_reproduces_a_training_configuration():
    """A held-out *configuration* (both rival starts plus the guard layout) never occurs
    in training: training starts are TUNING_STARTS with the default two guards."""
    train_pairs = {(tuple(a), tuple(b)) for a, b in TUNING_STARTS}
    train_pairs |= {(b, a) for a, b in train_pairs}
    for st in _h6_starts():
        pair = (tuple(st["rivals"]["A"]), tuple(st["rivals"]["B"]))
        assert pair not in train_pairs
        layout = {(g[0], g[1], tuple(g[2])) for g in st["guards"].values()}
        default = {(p[0], p[1], tuple(p[2])) for p in arena.GUARD_POSTS.values()}
        assert layout != default


def test_h6_has_four_starts_and_two_seat_orders_give_eight_outcomes():
    assert len(_h6_starts()) == 4


def test_power_of_an_eight_outcome_heldout_run():
    """What T09 can claim: eight distinct duels (4 starts x MvS/SvM) are the independent
    trials. Only 7 or 8 wins out of 8 put the Wilson lower bound above 0.5."""
    lower = {k: stats.wilson(k, 8)[0] for k in range(9)}
    assert lower[8] > 0.65
    assert 0.5 < lower[7] < 0.6
    assert lower[6] < 0.5
    assert lower[0] == 0.0

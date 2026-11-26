"""Gate 2 (Evaluation Specialist) checks for T08-fix1. Read-only on H6's data: no policy
runs on the held-out split, the real ledger is never written (temp paths only).

They pin the measured facts the Gate 2 report relies on: where the eight H6 starts put
the rivals, which new starts face a hazard on the first step, the power of the
pre-registered 14-of-16 bar (also with the two seat orders of a start treated as one
cluster), and that a new commit reopens a (weights, commit) claim, which T09's brief
must therefore forbid by rule.
"""

from __future__ import annotations

import json
from collections import Counter
from math import comb
from pathlib import Path

import pytest

from evaluation import manifest, stats
from pop import arena

ROOT = Path(__file__).resolve().parent.parent


def _starts():
    manifest.verify_heldout()
    return json.loads(manifest.HELDOUT_PATH.read_text())["scenarios"][0]["starts"]


def test_new_rival_cells_sit_in_rooms_2_4_5_6_and_none_in_1_or_3():
    new = _starts()[4:]
    rooms = Counter(s["rivals"][seat][0] for s in new for seat in "AB")
    assert sorted(rooms.items()) == [(2, 3), (4, 1), (5, 1), (6, 3)]
    allrooms = Counter(s["rivals"][seat][0] for s in _starts() for seat in "AB")
    assert sorted(allrooms.items()) == [(1, 2), (2, 3), (3, 2), (4, 3), (5, 3), (6, 3)]


def test_guard_rooms_over_all_eight_starts():
    rooms = Counter(g[0] for s in _starts() for g in s["guards"].values())
    assert sorted(rooms.items()) == [(1, 6), (3, 3), (4, 3), (5, 3), (6, 1)]   # room 2: none


def test_three_new_starts_have_a_hazard_one_cell_ahead_of_a_rival():
    """Disclosure, not a defect: the facing rule (toward the room's middle) puts a pit
    (H6-5 A) or spikes (H6-6 B, H6-8 A) directly ahead. Both controllers play both seats
    of every start, so the seat swap cancels it; T09 reports it beside the per-start rows."""
    ahead = {}
    for s in _starts()[4:]:
        for seat in "AB":
            room, row, col, face = s["rivals"][seat]
            ch = arena.ROOMS[room][row][col + face]
            if ch in ".^":
                ahead[(s["id"], seat)] = ch
    assert ahead == {("H6-5", "A"): ".", ("H6-6", "B"): "^", ("H6-8", "A"): "^"}


def test_every_start_has_its_rivals_in_rooms_one_or_two_hops_apart():
    """No start puts the rivals out of reach of each other (that would force a draw and
    make the 14-of-16 bar unattainable)."""
    def hops(a, b):
        seen, q = {a: 0}, [a]
        while q:
            x = q.pop(0)
            for y in arena.LINKS[x]:
                if y and y not in seen:
                    seen[y] = seen[x] + 1
                    q.append(y)
        return seen[b]
    assert {hops(s["rivals"]["A"][0], s["rivals"]["B"][0]) for s in _starts()} <= {1, 2}


def _tail(n, k, p):
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def test_power_of_the_14_of_16_bar_independent_duels():
    """Under a coin-flip rival the bar passes 0.2 % of the time (small false positive).
    Against a rival that wins 80 % of independent duels it passes 35 %, at 90 % 79 %."""
    assert _tail(16, 14, 0.5) == pytest.approx(0.0021, abs=5e-4)
    assert _tail(16, 14, 0.8) == pytest.approx(0.352, abs=5e-3)
    assert _tail(16, 14, 0.9) == pytest.approx(0.789, abs=5e-3)
    lows = {k: stats.wilson(k, 16)[0] for k in (16, 14, 13, 12, 11)}
    assert lows[16] > 0.80 and 0.63 < lows[14] < 0.65 and lows[12] > 0.5 > lows[11]


def test_power_when_the_two_seat_orders_of_a_start_are_one_cluster():
    """The two orders of a start share geometry, so the effective n lies between 8 and 16.
    Model: a start gives 2 wins (prob q2), 1 win (q1) or 0. The bar needs at least 14."""
    def passes(q2, q1):
        dist = {0: 1.0}
        for _ in range(8):
            nxt = {}
            for k, v in dist.items():
                for w, pw in ((2, q2), (1, q1), (0, 1 - q2 - q1)):
                    nxt[k + w] = nxt.get(k + w, 0) + v * pw
            dist = nxt
        return sum(v for k, v in dist.items() if k >= 14)
    assert passes(0.25, 0.5) < 0.01          # a coin-flip rival
    assert 0.40 < passes(0.7, 0.25) < 0.50   # a strong rival sweeping 70 % of starts
    assert passes(0.9, 0.1) > 0.9            # a dominant rival


def test_heldout_hash_is_the_same_in_every_recorded_place():
    h = manifest.HELDOUT_SHA256
    assert h.startswith("d013152a") and h.endswith("5266")
    for rel in ("evaluation/heldout/README.md", "docs/final/evaluation/PROTOCOL.md"):
        assert h in (ROOT / rel).read_text()


def test_a_new_commit_reopens_a_claim_so_t09_must_forbid_a_second_run_by_rule(tmp_path):
    """Decision #64 as built: the key is (weights, commit). Committing a report after the
    run makes a new HEAD, so the tool would allow a second claim. That is visible (both
    lines stay) but is not a barrier, so the T09 brief states the one-run rule itself."""
    ledger = tmp_path / "ledger.jsonl"
    manifest.claim_heldout_run("w" * 64, {"commit": "c1", "run_id": "r1"}, ledger)
    with pytest.raises(manifest.FreezeError):
        manifest.claim_heldout_run("w" * 64, {"commit": "c1", "run_id": "r2"}, ledger)
    manifest.claim_heldout_run("w" * 64, {"commit": "c2", "run_id": "r3"}, ledger)
    assert len(manifest.read_ledger(ledger)) == 2

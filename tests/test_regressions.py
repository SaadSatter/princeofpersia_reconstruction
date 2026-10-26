"""Regression tests for bugs actually observed during development."""

from pop.engine import Game
from pop.situations import Situation


def test_regression_fall_death_reported_full_hp():
    """Observed 2026-10-26 (first run of tests/test_rules.py): a kid killed by a
    3-row fall stayed at hp=3, so the observation would show a dead kid at
    full health. Fix: Game._die sets hp to 0."""
    rooms = {1: ("__________", "_.________", "_.________"),
             2: ("_.________", "__________", "##########")}
    s = Situation(id="fixture", rooms=rooms, links={1: (0, 0, 0, 2), 2: (0, 0, 1, 0)},
                  start=(1, 1, 0, +1))
    g = Game(s)
    g.perform("RIGHT")
    while g.terminal is None:
        g.perform("WAIT")
    assert g.terminal == "died:fall"
    assert g.kid.hp == 0

"""Level 1 reconstruction: isolation from the suite, start, rules, leakage.

Runs in CI on a level file we author (tests/level_fixture.py); the original
file is never needed here. Tests on the original file itself are in
tests/test_level1_original.py and skip when it is not present.
"""

import json
import subprocess
from pathlib import Path

import pytest

import evaluate
from level_fixture import MINI_ROOMS, mini_level
from pop import levelfile as LF
from pop import levels
from pop import observation as O
from pop.interface import Episode
from pop.situations import SITUATIONS

PROJECT = Path(__file__).resolve().parent.parent


def mini(**kw):
    return levels.to_situation(LF.parse(mini_level()), "mini", **kw)


def play(ep, *actions):
    out = None
    for a in actions:
        out = ep.step("kid", a)
        assert out["accepted"], (a, out)
    return out


# --- isolation from the frozen suite ------------------------------------
def test_level1_is_not_in_the_suite_or_the_evaluator():
    assert "L1" not in SITUATIONS
    for situations, _seeds in evaluate.SUITES.values():
        assert "L1" not in situations


def test_evaluate_refuses_level1(tmp_path):
    with pytest.raises(SystemExit):
        evaluate.main(["--suite", "final", "--situations", "L1", "--out", str(tmp_path)])


def test_suite_situations_have_no_level1_options():
    for s in SITUATIONS.values():
        assert (s.gates_open, s.start_falling, s.start_presses, s.rules) == ((), False, (), frozenset())


def test_missing_level_file_explains_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("POP_LEVEL1", str(tmp_path / "LEVEL1"))
    with pytest.raises(levels.LevelDataMissing, match="tools/fetch_level1.py"):
        Episode("L1")


def test_a_level_file_other_than_the_pinned_one_is_refused(monkeypatch, tmp_path):
    path = tmp_path / "LEVEL1"
    path.write_bytes(mini_level())
    monkeypatch.setenv("POP_LEVEL1", str(path))
    with pytest.raises(levels.LevelDataMismatch, match="not the pinned"):
        Episode("L1")


def test_no_original_level_file_is_tracked_by_git():
    """Decision D1: the original layout is never committed, in any form we can detect."""
    files = subprocess.run(["git", "ls-files", "-z"], cwd=PROJECT, capture_output=True,
                           check=True).stdout.decode().split("\0")
    import hashlib
    pinned = {levels.APPLE2.sha256, levels.DOS.sha256}
    for name in filter(None, files):
        p = PROJECT / name
        if p.is_file() and p.stat().st_size in (LF.SIZE_APPLE2, LF.SIZE_DOS):
            assert hashlib.sha256(p.read_bytes()).hexdigest() not in pinned, name


# --- start (R-C30) and gates open at load (R-C29) -----------------------
def test_kid_drops_in_and_the_gate_behind_him_slams():
    ep = Episode(mini())
    obs = ep.reset(0)
    assert obs["kid"] == {"row": 1, "col": 0, "facing": "right", "posture": "standing",
                          "hp": 3, "max_hp": 3, "sword": False}
    assert obs["last_result"]["fell_rows"] == 1 and obs["last_result"]["effect"] == "landed"
    gate = ep._game.mech.gates[(5, 0, 9)]
    assert gate.pos == 0                              # was open at load, slammed
    assert ep._game.frames == obs["last_result"]["frames"] > 0


def test_gate_open_at_load_stays_open_without_the_start_script():
    ep = Episode(mini(special_start=False))
    ep.reset(0)
    gate = ep._game.mech.gates[(5, 0, 9)]
    for _ in range(30):
        ep.step("kid", "WAIT")
    assert gate.pos == 188 and not gate.bars


def test_reset_is_deterministic():
    a, b = Episode(mini()), Episode(mini())
    assert a.reset(3) == b.reset(3)
    for act in ("RIGHT", "RIGHT", "DOWN", "RIGHT"):
        assert a.step("kid", act) == b.step("kid", act)
    assert a._game.snapshot() == b._game.snapshot()


# --- sword (R-C21) --------------------------------------------------------
def test_crouching_on_the_sword_picks_it_up():
    ep = Episode(mini())
    ep.reset(0)
    out = play(ep, "RIGHT", "RIGHT", "DOWN")
    assert out["effect"] == "took_sword" and out["frames"] == 12
    obs = ep.observe("kid")
    assert obs["kid"]["sword"] is True
    assert obs["tiles"][1][2] == "_"


def test_sword_tile_is_plain_floor_without_the_rule():
    s = mini()
    from dataclasses import replace
    ep = Episode(replace(s, rules=frozenset()))
    ep.reset(0)
    out = play(ep, "RIGHT", "RIGHT", "DOWN")
    assert out["effect"] == "none"
    assert "sword" not in ep.observe("kid")["kid"]


# --- loose floor knocked from below (R-C31) --------------------------------
def test_hopping_under_a_loose_floor_knocks_it_down_onto_the_kid():
    ep = Episode(mini())
    ep.reset(0)
    play(ep, *["RIGHT"] * 9, "RIGHT", "RIGHT", "RIGHT")    # into room 2, col 2
    obs = ep.observe("kid")
    assert (obs["kid"]["row"], obs["kid"]["col"]) == (1, 2)
    out = play(ep, "UP")
    assert out["effect"] == "bumped_ceiling"
    assert ep.observe("kid")["state"]["loose_shaking"] == [[0, 2]]
    out = play(ep, "WAIT")                                  # falls 10 frames after the hop
    obs = ep.observe("kid")
    assert obs["tiles"][0][2] == "."
    assert obs["kid"]["hp"] == 2                            # struck by the falling floor (R-C14)


# --- cross-room plate, exit, win -----------------------------------------
def test_plate_opens_exit_in_the_next_room_and_the_kid_escapes():
    ep = Episode(mini())
    ep.reset(0)
    play(ep, *["RIGHT"] * 5)                                # onto the plate at (1,5)
    play(ep, *["RIGHT"] * 10)                               # room 2, col 5 (exit)
    for _ in range(10):
        ep.step("kid", "WAIT")
    assert ep.observe("kid")["state"]["exits"][0]["open"]
    out = play(ep, "UP")
    assert out["effect"] == "won"
    assert ep.outcome()["reason"] == "won"


# --- what a player sees ---------------------------------------------------
def test_observation_shows_only_the_current_room():
    ep = Episode(mini())
    obs = ep.reset(0)
    assert set(obs) == O.OBSERVATION_KEYS
    assert set(obs["kid"]) == O.LEVEL1_KID_KEYS
    text = json.dumps(obs)
    for room, rows in MINI_ROOMS.items():
        if room != 1:
            for row in rows:
                if row not in MINI_ROOMS[1]:
                    assert row not in text
    for word in ("link", "rooms", "plate_links", "gates_open", "guard", "start_", "sha256", "LEVEL1"):
        assert word not in text
    # Legal actions depend on posture only (R-D06): L1 gives exactly the same
    # list as a suite scenario in the same posture, so it hints at nothing.
    suite = Episode("S1")
    suite.reset(0)
    assert obs["kid"]["posture"] == suite.observe("kid")["kid"]["posture"] == "standing"
    assert ep.legal_actions("kid") == suite.legal_actions("kid")
    assert len(ep.legal_actions("kid")) == 11

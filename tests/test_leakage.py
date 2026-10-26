"""Information boundary (rubric 2c): observe and legal_actions show only what
a human sees on the current screen."""

import json

from pop import observation as O
from pop.engine import ACTIONS
from pop.interface import Episode
from pop.situations import SITUATIONS


def test_observation_has_exactly_the_allowed_keys():
    obs = Episode("S3").observe("kid")
    assert set(obs) == O.OBSERVATION_KEYS
    assert set(obs["state"]) == O.STATE_KEYS
    assert set(obs["kid"]) == O.KID_KEYS


def test_observation_shows_only_the_current_room():
    ep = Episode("S3")
    text = json.dumps(ep.observe("kid"))
    current = SITUATIONS["S3"].rooms[1]
    for row in current:
        assert row in text
    for room, rows in SITUATIONS["S3"].rooms.items():
        if room != 1:
            for row in rows:
                if row not in current:
                    assert row not in text


def test_observation_hides_links_ids_and_held_out_status():
    for sid in SITUATIONS:
        obs = Episode(sid).observe("kid")
        text = json.dumps(obs)
        assert sid not in text
        assert "held" not in text and "link" not in text
        assert "up" not in obs["edges"] and "down" not in obs["edges"]


def test_task_text_is_identical_in_every_situation():
    assert len({Episode(sid).observe("kid")["task"] for sid in SITUATIONS}) == 1


def test_room_labels_are_opaque():
    label = Episode("S3").observe("kid")["room"]
    assert label == O.room_label("S3", 1)
    assert label.startswith("room-") and len(label) == len("room-") + 6
    assert O.room_label("S3", 1) != O.room_label("S3", 2)
    # Same room number in different situations gets a different label.
    assert O.room_label("S3", 1) != O.room_label("H3", 1)


def test_gate_state_shows_openness_not_timers():
    ep = Episode("S2")
    ep.step("kid", "RIGHT")                  # press the plate
    for a in ["RIGHT"] * 2 + ["STEP_RIGHT"] * 4 + ["RIGHT"] * 3:
        ep.step("kid", a)
    gates = ep.observe("kid")["state"]["gates"]
    assert gates and set(gates[0]) == {"row", "col", "open_pct", "bars"}


def test_legal_actions_depend_only_on_posture():
    seen = set()
    for sid in SITUATIONS:
        ep = Episode(sid)
        seen.add(tuple(ep.legal_actions("kid")))
        ep.step("kid", "WAIT")
        seen.add(tuple(ep.legal_actions("kid")))
    assert seen == {tuple(ACTIONS)}


def test_step_result_reveals_nothing_beyond_the_observation():
    ep = Episode("S2")
    res = ep.step("kid", "RIGHT")            # stepping on a linked plate
    assert set(res) == {"accepted", "action", "observation"} | O.RESULT_KEYS
    assert "gate" not in json.dumps({k: v for k, v in res.items() if k != "observation"})

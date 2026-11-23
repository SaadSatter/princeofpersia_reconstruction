"""The frozen evaluation suite (docs/EVALUATION_SUITE.md) and what players see
of it stay byte-identical while Level 1 work changes the engine.

The pinned hashes were computed on 2026-10-26 (session 08) before any
Level 1 code existed. If one of these fails, the suite or the model's view
of it changed: that needs the student's approval and a change-log row.
"""

import hashlib
import json

import pytest

from agents.model_player import build_system_prompt
from pop.interface import Episode
from pop.situations import SITUATIONS

FROZEN = ("S1", "S2", "S3", "H1", "H2", "H3")

PROMPT_SHA = "a2b9c254073deab5b5ad8e795d74c441c21051c22e025e0b402e06f9dd5b3bab"

FIRST_OBS_SHA = {   # reset(100) observation, JSON with sorted keys
    "H1": "519542287e8470b9684e62a0520f9fbfb8f89cfea07061195d26cd0e19da7a45",
    "H2": "242566c014fef011d3770c01dcdf3efbda1292f082eaf93ad48ca809602281aa",
    "H3": "2cc4c22e60aafe764d6d9b326c274064715e27ec7ba722d0fc41e48f1e3ddb2f",
    "S1": "fd937ba9f083636245bc4d33a249d2b911a78fd9c16f491e936cab700c52ef70",
    "S2": "956daf7f0c750516cac1dd5dbf1e90c4cf9d4b04e32dce73d956bf2a03001d6c",
    "S3": "c407a442de592fd210e647ca4985860916b8b3b3b03375a1ca1e81c9f43d01c6",
}

DEFINITION_SHA = {
    "S1": "7ce2190cb620d11af41e0922cb1d73a100ac3fc2ff44fb9118211cea7e5a0e1a",
    "S2": "e993c1142fb156e22c76115d5ec523c44a3ad598fd385981e60374bd3aed340c",
    "S3": "ad273fb3ca73293152beebd7fb21a95b301a18d155c73e2cb3b31fced89eb34f",
    "H1": "d7e17903f266b79145a87525c80b2c1d1988e6c7702f705598e993ececc9b8e0",
    "H2": "6b8c046791bec3878c3c7dd389259a35836df73803dbc32625b21082d6637fa7",
    "H3": "00c1268e8d92b36e26ae7775a882d7ebe2a20acaf98f09ce7e5c2bcfb7e13a9f",
}


def _definition(sid: str) -> str:
    s = SITUATIONS[sid]
    return json.dumps({
        "id": s.id, "rooms": {str(k): v for k, v in sorted(s.rooms.items())},
        "links": {str(k): v for k, v in sorted(s.links.items())}, "start": s.start,
        "plate_links": sorted([list(k), [list(t) for t in v]] for k, v in s.plate_links.items()),
        "exits_open": s.exits_open, "max_actions": s.max_actions, "max_calls": s.max_calls,
        "held_out": s.held_out, "task": s.task,
    }, sort_keys=True)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_suite_ids_unchanged():
    assert set(FROZEN) <= set(SITUATIONS)
    assert set(SITUATIONS) == set(FROZEN), "new scenarios belong in pop/levels.py, not the suite"


@pytest.mark.parametrize("sid", FROZEN)
def test_definition_unchanged(sid):
    assert _sha(_definition(sid)) == DEFINITION_SHA[sid]


@pytest.mark.parametrize("sid", FROZEN)
def test_first_observation_unchanged(sid):
    obs = Episode(sid).reset(100)
    assert _sha(json.dumps(obs, sort_keys=True)) == FIRST_OBS_SHA[sid]


def test_model_system_prompt_unchanged():
    assert _sha(build_system_prompt()) == PROMPT_SHA

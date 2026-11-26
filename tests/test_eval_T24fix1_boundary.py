"""T24-fix1 Gate 2 (evaluation specialist): #101 at a ledge edge, seen from the duel boundary.

R-V25: both seats share the rule and the other seat's view carries no new key.
R-V19: the hang keeps suspicion where it was; TAKE still takes the uniform at the edge.
"""
from __future__ import annotations

import json

from tests.test_eval_T24_f1 import edge_episode


def trace(ep, action, n=30):
    out = []
    for i in range(n):
        if i == 0:
            ep.step("A", action)
        ep.tick()
        out.append((json.dumps(ep.observe("A"), sort_keys=True, default=str),
                    json.dumps(ep.observe("B"), sort_keys=True, default=str)))
    return out


def test_edge_down_with_body_hangs_like_down_without_body_for_both_seats_keys():
    with_body, no_body = edge_episode(True), edge_episode(False)
    a, b = trace(with_body, "DOWN"), trace(no_body, "DOWN")
    for (oa1, ob1), (oa2, ob2) in zip(a, b):
        assert json.loads(oa1).keys() == json.loads(oa2).keys()
        assert json.loads(ob1).keys() == json.loads(ob2).keys()
    r = with_body._duel.rivals["A"]
    assert r.kid.posture == "hanging" and r.disguised is False
    assert with_body.observe("A")["last_result"]["effect"] == "hanging"


def test_edge_take_still_takes_the_uniform():
    ep = edge_episode(True)
    ep.step("A", "TAKE")
    for _ in range(40):
        ep.tick()
    assert ep._duel.rivals["A"].disguised is True
    assert ep._duel.rivals["A"].kid.posture != "hanging"

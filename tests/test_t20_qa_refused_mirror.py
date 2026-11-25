"""T20 QA: the refused-input mirror (Match._note_refused) against the real key resolution
(WebGame.tick). Differential fuzz: for every tick and seat, a held key set that asks for an
action the real tick did not step must be logged refused (with an action name), and an
input the real tick stepped must never be logged refused."""

from __future__ import annotations

import json
import random

import pytest

from server.match import TICK_S, Match
from server.telemetry import Telemetry
from web.bridge import running_dir, seat_input

ALL = ["a", "d", "w", "s", "f", "g", "t", "left", "right", "up", "down", ".", "/", "'",
       "lshift", "rshift"]


def _run(tmp_path, seed, rival, ticks, rng_seed):
    tele = Telemetry(tmp_path, "QA", info={"build": "qa"}, today=lambda: "2026-11-25")
    m = Match(seed=seed, rival=rival, telemetry=tele, rival_budget_s=1.0)
    m.join(None, 0.0)
    if not rival:
        m.join(None, 0.0)
    ep = m.episode
    stepped: list[tuple[str, str]] = []
    real_step = ep.step

    def spy(seat, action):
        stepped.append((seat, action))
        return real_step(seat, action)
    ep.step = spy
    refused: list[tuple[str, str]] = []
    rng = random.Random(rng_seed)
    now, mism, asked_total, ref_total = 0.0, [], 0, 0
    for i in range(ticks):
        if i % 3 == 0:
            for seat in m.human_seats:
                ks = rng.sample(ALL, rng.choice([0, 1, 1, 2, 2, 3]))
                m.receive(seat, json.dumps({"type": "keys", "keys": ks}), now)
        rec = m._rec
        if rec is not None and not hasattr(rec, "_qa"):
            orig = rec.refused

            def hook(seat, action, error="x", _o=orig):
                refused.append((seat, action))
                return _o(seat, action, error)
            rec.refused = hook
            rec._qa = True
        pre = {}
        if m.state == "playing" and ep.outcome()["status"] == "ongoing":
            # the real game's own key resolution (press + _held), read before the tick
            from server.match import to_seat_keys
            if m.rival:
                keys = {n: True for s in m.human_seats for n in m.held[s]}
            else:
                keys = {n: True for s in m.human_seats for n in to_seat_keys(s, m.held[s])}
            held = m.game.press(keys)
            for seat, k in held.items():
                me = ep.observe(seat)["me"]
                pre[seat] = (seat_input(set(k["held"]), k["shift"], armed=me["armed"],
                                        running=running_dir(me)), tuple(ep.legal_actions(seat)))
        stepped.clear()
        refused.clear()
        now += TICK_S
        m.advance(now)
        for seat, (act, legal) in pre.items():
            st = [a for s, a in stepped if s == seat]
            rf = [a for s, a in refused if s == seat]
            if act is None:
                if rf or st:
                    mism.append((i, seat, "no ask but event", st, rf))
                continue
            asked_total += 1
            if st and rf:
                mism.append((i, seat, "both stepped and refused", st, rf))
            elif not st and not rf:
                mism.append((i, seat, "dropped silently", act, legal))
            elif rf:
                ref_total += 1
        for s in ("A", "B"):
            m.drain(s)
    return mism, asked_total, ref_total


@pytest.mark.parametrize("seed,rival", [(1, None), (2, None), (3, None), (4, "baseline"),
                                        (5, "baseline")])
def test_refused_mirror_agrees_with_real_resolution(tmp_path, seed, rival):
    mism, asked, refused = _run(tmp_path, seed, rival, 1500, rng_seed=seed * 13)
    assert asked > 300 and refused > 20, (asked, refused)
    assert mism == [], mism[:5]

"""The PPO rival's feature encoder and action mask (T07, docs/final/RL_POLICY.md)."""

from __future__ import annotations

import ast
import copy
import random
from pathlib import Path

from agents.macros import MACROS
from agents.rl import encoder as enc_mod
from agents.rl.encoder import (FEATURE_NAMES, K_FIGURES, MACRO_SLOTS, N_FEATURES, Encoder,
                               macro_mask)
from pop import arena
from pop.versus import VersusEpisode

HIDDEN_TOP = {"minutes_left", "task", "kid", "last_result", "state", "actions_left"}
SHOWN_TOP = {"room", "tiles", "edges", "me", "figures", "swords", "suspicion"}


class Spy(dict):
    """A dict that records every key read, recursively."""

    def __init__(self, data, log, path=""):
        super().__init__()
        self.log, self.path = log, path
        for k, v in data.items():
            super().__setitem__(k, self._wrap(v, f"{path}/{k}"))

    def _wrap(self, v, path):
        if isinstance(v, dict):
            return Spy(v, self.log, path)
        if isinstance(v, list):
            return [self._wrap(x, path + "[]") for x in v]
        return v

    def __getitem__(self, k):
        self.log.add(f"{self.path}/{k}")
        return super().__getitem__(k)

    def get(self, k, default=None):
        self.log.add(f"{self.path}/{k}")
        return super().get(k, default)

    def items(self):
        self.log.add(self.path + "/*")
        return super().items()

    def keys(self):
        self.log.add(self.path + "/*")
        return super().keys()

    def __iter__(self):
        self.log.add(self.path + "/*")
        return super().__iter__()


def _episode_with_guard_figure(disguised: bool):
    a_start, spot = (1, 2, 2, +1), (1, 2, 6, +1)
    if disguised:
        ep = VersusEpisode(arena.situation("A"), {"A": a_start, "B": spot}, 0, 3600, {})
        ep._duel.rivals["B"].disguised = True
    else:
        ep = VersusEpisode(arena.situation("A"), {"A": a_start, "B": (3, 2, 7, -1)}, 0, 3600,
                           {"g": (1, 2, (6, 6), +1)})
    return ep


def _play(enc, ep, frames=60):
    out = []
    for f in range(frames):
        if f % 6 == 0:
            obs, legal = ep.observe("A"), tuple(ep.legal_actions("A"))
            out.append(enc.encode(obs, legal))
        ep.tick()
    return out


def test_feature_vector_has_fixed_length_names_and_finite_numbers():
    ep = _episode_with_guard_figure(True)
    e = Encoder()
    x = e.encode(ep.observe("A"), tuple(ep.legal_actions("A")))
    assert len(x) == N_FEATURES == len(FEATURE_NAMES) == len(set(FEATURE_NAMES))
    assert all(isinstance(v, float) and abs(v) < 1e6 for v in x)
    empty = Encoder().encode(VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600, {}).observe("A"), ("WAIT",))
    assert len(empty) == N_FEATURES


def test_a_disguised_rival_and_a_real_guard_give_identical_features_over_time():
    d, g = _episode_with_guard_figure(True), _episode_with_guard_figure(False)
    assert d.observe("A")["figures"] == g.observe("A")["figures"] != []
    ed, eg, same = Encoder(), Encoder(), 0
    for f in range(120):
        if f % 6 == 0:
            od, og = d.observe("A"), g.observe("A")
            if od != og:                 # a patrolling guard and a waiting rival drift apart
                break
            ld, lg = tuple(d.legal_actions("A")), tuple(g.legal_actions("A"))
            assert ed.encode(od, ld) == eg.encode(og, lg)
            same += 1
        d.tick(); g.tick()
    assert same >= 3


def test_encoder_reads_only_what_a_human_sees():
    ep = _episode_with_guard_figure(True)
    obs, legal = ep.observe("A"), tuple(ep.legal_actions("A"))
    log: set[str] = set()
    Encoder().encode(Spy(obs, log), legal)
    top = {p.split("/")[1].replace("[]", "") for p in log if p.count("/") >= 1 and p != "/*"}
    assert top <= SHOWN_TOP, top - SHOWN_TOP
    assert not (top & HIDDEN_TOP)
    # The figure's kind is read only as the visible label, never an id.
    assert not any("id" == p.rsplit("/", 1)[-1] or "name" == p.rsplit("/", 1)[-1] for p in log)


def test_minutes_left_and_other_unlisted_fields_do_not_change_the_features():
    ep = _episode_with_guard_figure(True)
    obs, legal = ep.observe("A"), tuple(ep.legal_actions("A"))
    other = copy.deepcopy(obs)
    other["minutes_left"], other["task"], other["actions_left"] = 0, "x", 3
    other["last_result"] = {"effect": "zzz"}
    assert Encoder().encode(obs, legal) == Encoder().encode(other, legal)


def test_encoder_module_never_mentions_outcome_or_the_duel_clock():
    text = Path(enc_mod.__file__).read_text()
    tree = ast.parse(text)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
               and isinstance(n.value, str)}
    assert "outcome" not in names and "outcome" not in strings
    assert "minutes_left" not in strings
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                for a in n.names} | {(n.module or "").split(".")[0] for n in ast.walk(tree)
                                      if isinstance(n, ast.ImportFrom)}
    assert imported <= {"__future__", "agents", "math", "dataclasses"}, imported


def _figs(n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        out.append({"kind": rnd.choice(["guard", "rival"]), "row": rnd.randrange(3),
                    "col": rnd.randrange(10), "facing": rnd.choice(["left", "right"]),
                    "posture": rnd.choice(["standing", "downed", "knocked_down"]),
                    "stance": rnd.choice([None, "low", "mid", "high"]),
                    "armed": rnd.random() < .5, "motion": None})
    return out


def test_features_do_not_depend_on_the_order_of_the_figures():
    ep = _episode_with_guard_figure(True)
    base = ep.observe("A")
    for seed in range(20):
        figs = _figs(6, seed)
        a, b = copy.deepcopy(base), copy.deepcopy(base)
        a["figures"] = figs
        b["figures"] = random.Random(seed + 99).sample(figs, len(figs))
        assert Encoder().encode(a, ("WAIT",)) == Encoder().encode(b, ("WAIT",))


def test_only_the_nearest_k_figures_matter_and_far_ones_are_dropped():
    base = _episode_with_guard_figure(True).observe("A")
    near = [{"kind": "guard", "row": 2, "col": 3 + i, "facing": "left", "posture": "standing",
             "stance": None, "armed": False, "motion": None} for i in range(K_FIGURES)]
    far = dict(near[0], col=9, row=0)
    a, b = copy.deepcopy(base), copy.deepcopy(base)
    a["me"].update(row=2, col=2)
    b["me"].update(row=2, col=2)
    a["figures"], b["figures"] = near, near + [far]
    assert Encoder().encode(a, ("WAIT",)) == Encoder().encode(b, ("WAIT",))


# --- the macro mask -------------------------------------------------------------
def test_macro_slots_are_the_t05_vocabulary_plus_the_reserved_trap_slot():
    assert MACRO_SLOTS == tuple(MACROS) + ("RIG_TRAP",) and len(MACRO_SLOTS) == 9


def _obs(figures=(), disguised=False, hp=3):
    o = _episode_with_guard_figure(True).observe("A")
    o["figures"] = list(figures)
    o["me"]["disguised"], o["me"]["hp"] = disguised, hp
    return o


def _m(obs, legal=("WAIT", "LEFT", "RIGHT")):
    return dict(zip(MACRO_SLOTS, macro_mask(obs, tuple(legal))))


def test_mask_always_allows_wait_and_never_the_reserved_trap_slot():
    for o in (_obs(), _obs(_figs(3, 1))):
        m = _m(o)
        assert m["WAIT"] and not m["RIG_TRAP"]
        assert m["SEARCH"] and m["BLEND"] and m["CLIMB"]


def test_mask_needs_a_figure_for_follow_strike_flee_and_a_downed_one_for_disguise():
    m = _m(_obs())
    assert not (m["FOLLOW"] or m["STRIKE"] or m["FLEE"] or m["DISGUISE"])
    standing = {"kind": "guard", "row": 1, "col": 5, "facing": "left", "posture": "standing",
                "stance": None, "armed": False, "motion": None}
    m = _m(_obs([standing]))
    assert m["FOLLOW"] and m["STRIKE"] and m["FLEE"] and not m["DISGUISE"]
    downed = dict(standing, posture="downed")
    m = _m(_obs([downed]))
    assert m["DISGUISE"] and not m["STRIKE"] and not m["FOLLOW"]
    assert not _m(_obs([downed], disguised=True))["DISGUISE"]


def test_mask_with_no_legal_input_leaves_only_wait():
    m = _m(_obs([]), legal=())
    assert [k for k, v in m.items() if v] == ["WAIT"]


def test_history_resets_and_is_bounded():
    ep = _episode_with_guard_figure(True)
    e = Encoder()
    first = _play(e, ep, 60)
    e.reset()
    again = _play(e, _episode_with_guard_figure(True), 60)
    assert first == again

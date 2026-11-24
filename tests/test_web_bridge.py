"""T14: the web bridge (web/bridge.py) and the draw list (render/draw_list.py).

The page runs the engine in the browser (Pyodide) and draws only what the
bridge returns. These tests pin the knowledge boundary of that payload, its
determinism, and the key map shared with `play.py --versus`. CPython only:
the browser run itself is checked by .github/workflows/web-smoke.yml.
"""

from __future__ import annotations

import itertools
import json

import pytest

import play
from pop import versus
from pop.versus import arena_episode
from render import draw_list
from web import bridge

FORBIDDEN_KEYS = {"seed", "_duel", "duel", "snapshot", "suspicion_of", "owner", "trap_owner",
                  "rigged_by", "pending", "rng", "disguised_rivals"}


def walk(value, path=()):
    """Every (path, key, value) in a JSON value."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k, v
            yield from walk(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, path + (i,))


def disguise_paths(payload):
    return [p + (k,) for p, k, _ in walk(payload) if k == "disguised"]


def roundtrip(x):
    return json.loads(json.dumps(x))


# --- the key map is play.py's -----------------------------------------------------
def test_key_map_is_play_py_versus_table():
    assert bridge.KEY_MAP == play.VERSUS_KEYS


@pytest.mark.parametrize("armed", [False, True])
@pytest.mark.parametrize("running", [None, "left", "right"])
def test_seat_input_matches_play_py_for_every_held_set(armed, running):
    names = ("left", "right", "up", "down", "attack", "draw", "take")
    for n in range(len(names) + 1):
        for held in itertools.combinations(names, n):
            for shift in (False, True):
                assert (bridge.seat_input(set(held), shift, armed, running)
                        == play.versus_input(set(held), shift, armed=armed, running=running)), held


def test_running_dir_matches_play_py():
    for me in ({"motion": None, "facing": "left"},
               {"motion": {"effect": "moved", "frames": 4}, "facing": "right"},
               {"motion": {"effect": "moved", "frames": 99}, "facing": "right"}):
        assert bridge.running_dir(me) == play.running_dir(me)


def test_press_maps_physical_keys_to_each_seat():
    g = bridge.WebGame(mode="local_two_players", seed=1, art=bridge.load_art())
    held = g.press({"a": True, "lshift": True, "up": True, "'": True, "rshift": False})
    assert held == {"A": {"held": ["left"], "shift": True},
                    "B": {"held": ["take", "up"], "shift": False}}


def test_human_vs_ai_ignores_the_ai_seats_keys():
    g = bridge.WebGame(mode="human_vs_ai", seed=1, human_seat="A", art=bridge.load_art())
    held = g.press({"d": True, "right": True})
    assert held == {"A": {"held": ["right"], "shift": False}}


# --- the payload holds one seat's view and nothing else ---------------------------
def disguised_duel(seed=0):
    """Seat B disguised and in seat A's room, beside a real guard."""
    ep = arena_episode(seed)
    d = ep._duel
    a, b = d.rivals["A"], d.rivals["B"]
    g = next(iter(d.guards.values()))
    a.kid.room, a.kid.row, a.kid.col = g.room, g.row, 1
    b.kid.room, b.kid.row, b.kid.col, b.kid.facing = g.room, g.row, 8, g.facing
    b.disguised = True
    d.suspicion[(g.name, "B")] = 40
    return ep


def test_payload_is_derivable_from_the_human_seats_observation_only():
    g = bridge.WebGame(mode="human_vs_ai", seed=4, human_seat="A",
                       rival=bridge.RandomRival(9), art=bridge.load_art())
    for t in range(60):
        g.press({"d": t % 7 < 4, "w": t % 11 == 0, "f": t % 13 == 0})
        payload = roundtrip(g.tick())
        obs = g.episode.observe("A")
        expect = draw_list.seat_payload(obs, "indigo", "crimson", g.display_tick,
                                        g.art, cache=None)
        assert payload["seat_view"] == roundtrip(obs)
        assert payload["draw"] == roundtrip(expect["draw"])
        assert payload["hud"] == roundtrip(expect["hud"])
        assert set(payload) == {"mode", "seat", "rival", "seat_view", "draw", "hud", "outcome"}
        assert set(payload["outcome"]) == {"status", "reason", "result"}


def test_payload_holds_no_secret_anywhere():
    ep = disguised_duel()
    g = bridge.WebGame(mode="human_vs_ai", seed=0, human_seat="A", art=bridge.load_art(),
                       episode=ep)
    payload = roundtrip(g.tick())
    text = json.dumps(payload)
    for _, k, v in walk(payload):
        assert k not in FORBIDDEN_KEYS, k
    # The only disguise flag is the human's own rival's, which it knows.
    assert disguise_paths(payload) == [("seat_view", "me", "disguised"), ("hud", "disguised")]
    assert payload["seat_view"]["me"]["disguised"] is False
    # No other-seat observation, no suspicion of seat B, no snapshot fields.
    assert payload["seat_view"] == roundtrip(ep.observe("A"))
    assert "stale" not in text and "replaced" not in text and "invalid" not in text
    assert all(f["kind"] == "guard" for f in payload["seat_view"]["figures"])


def test_hidden_state_outside_the_observation_never_changes_the_payload():
    """Two duels that differ only in what seat A cannot observe give the same payload."""
    art = bridge.load_art()
    one, two = arena_episode(2), arena_episode(2)
    b = two._duel.rivals["B"]                      # seat B is in another room at the start
    b.disguised = True
    two._duel.suspicion[(next(iter(two._duel.guards)), "B")] = 77
    assert one.observe("A") == two.observe("A")
    p1 = bridge.WebGame(mode="human_vs_ai", seed=2, art=art, episode=one).tick()
    p2 = bridge.WebGame(mode="human_vs_ai", seed=2, art=art, episode=two).tick()
    assert roundtrip(p1) == roundtrip(p2)


def test_a_disguised_rival_is_drawn_exactly_as_a_guard():
    """Seat B disguised at col 8, versus a real guard standing at col 8 facing the
    same way: the figure and every draw entry for it are equal, field for field."""
    art = bridge.load_art()
    ep1 = disguised_duel()
    ep2 = arena_episode(0)
    d2 = ep2._duel
    a2, b2 = d2.rivals["A"], d2.rivals["B"]
    g2 = next(iter(d2.guards.values()))
    a2.kid.room, a2.kid.row, a2.kid.col = g2.room, g2.row, 1
    g1 = next(iter(ep1._duel.guards.values()))
    g2.col, g2.facing = 8, ep1._duel.rivals["B"].kid.facing
    assert b2.kid.room != g2.room
    obs1, obs2 = ep1.observe("A"), ep2.observe("A")
    fig1 = next(f for f in obs1["figures"] if f["col"] == 8)
    fig2 = next(f for f in obs2["figures"] if f["col"] == 8)
    assert fig1 == fig2 and fig1["kind"] == "guard"
    j1, j2 = obs1["figures"].index(fig1), obs2["figures"].index(fig2)

    def draws_of(obs, j):
        return draw_list.guard_draws("figures", obs["figures"][j], obs["room"],
                                     art["sprites"], {}, ("fig", j))
    e1, e2 = draws_of(obs1, j1), draws_of(obs2, j2)
    assert e1 == e2 and e1
    assert all(e["img"].startswith("guard/") for e in e1)
    # In the full payload the disguised rival's entries appear exactly so, and
    # nothing is drawn in the other rival's colour.
    full = draw_list.seat_draws(obs1, "indigo", "crimson", 0, art)
    assert all(e in full for e in e1)
    assert not any(e.get("img", "").startswith("rival_crimson/") for e in full)
    assert g1.col != 8


def test_seat_draws_use_only_named_keys():
    art = bridge.load_art()
    ep = arena_episode(0)
    obs = ep.observe("A")
    for e in draw_list.seat_draws(obs, "indigo", "crimson", 0, art):
        kinds = {"img", "rect", "line"} & set(e)
        assert len(kinds) == 1
        if "img" in e:
            assert set(e) == {"layer", "img", "src", "x", "y", "w", "h", "flip", "tint",
                              "rot", "ox", "oy"}
        else:
            assert set(e) == {"layer", next(iter(kinds)), "color"}


# --- modes, rival hook, outcome ---------------------------------------------------
def test_local_two_players_has_one_panel_per_seat_and_says_so():
    g = bridge.WebGame(mode="local_two_players", seed=3, art=bridge.load_art())
    p = roundtrip(g.tick())
    assert set(p["seats"]) == {"A", "B"}
    assert "local test mode" in p["label"].lower()
    for seat in ("A", "B"):
        assert p["seats"][seat]["seat_view"] == roundtrip(g.episode.observe(seat))


def test_the_rival_hook_sees_only_its_own_seat():
    seen = []

    def rival(obs, legal):
        seen.append((obs, list(legal)))
        return "RIGHT" if "RIGHT" in legal else None

    g = bridge.WebGame(mode="human_vs_ai", seed=5, human_seat="A", rival=rival,
                       art=bridge.load_art())
    obs_before = g.episode.observe("B")
    g.tick()
    assert seen[0][0] == obs_before and seen[0][1] == g_legal_b(5)
    assert g.episode.outcome()["inputs"]["B"] == 1


def g_legal_b(seed):
    return arena_episode(seed).legal_actions("B")


def test_placeholder_rivals_are_labelled():
    for r in (bridge.IdleRival(), bridge.RandomRival(0)):
        assert "placeholder" in r.label.lower()
    g = bridge.WebGame(mode="human_vs_ai", seed=0, art=bridge.load_art())
    assert "placeholder" in g.tick()["rival"].lower()


def test_outcome_and_rematch():
    g = bridge.WebGame(mode="human_vs_ai", seed=0, art=bridge.load_art(),
                       episode=arena_episode(0, time_limit_frames=3))
    for _ in range(3):
        p = g.tick()
    assert p["outcome"] == {"status": "terminal", "reason": "draw:time_up", "result": "draw"}
    g.rematch()
    assert g.display_tick == 0 and g.tick()["outcome"]["status"] == "ongoing"


def test_human_input_is_validated_like_play_py():
    g = bridge.WebGame(mode="human_vs_ai", seed=0, human_seat="A", art=bridge.load_art())
    g.press({"d": True})
    g.tick()
    assert g.episode.outcome()["inputs"]["A"] == 1
    assert g.episode.outcome()["invalid_inputs"]["A"] == 0


def test_unknown_mode_or_seat_is_refused():
    with pytest.raises(ValueError):
        bridge.WebGame(mode="online", art=bridge.load_art())
    with pytest.raises(ValueError):
        bridge.WebGame(human_seat="C", art=bridge.load_art())


# --- determinism ---------------------------------------------------------------
def stream(seed, keys, mode="human_vs_ai"):
    g = bridge.WebGame(mode=mode, seed=seed, rival=bridge.RandomRival(seed),
                       art=bridge.load_art())
    out = []
    for k in keys:
        g.press(k)
        out.append(g.tick_json())
    return out


KEYS = [{"d": i % 9 < 5, "w": i % 17 == 3, "f": i % 23 == 0, "g": i == 30, "lshift": i % 5 == 0,
         "left": i % 4 == 0, ".": i % 19 == 0}
        for i in range(120)]


@pytest.mark.parametrize("mode", ["human_vs_ai", "local_two_players"])
def test_same_seed_and_keys_give_the_same_payload_stream(mode):
    assert stream(7, KEYS, mode) == stream(7, KEYS, mode)


def test_the_stream_moves():
    s = stream(7, KEYS)
    assert len(set(s)) > 10
    assert json.loads(s[-1])["seat_view"]["me"] != json.loads(s[0])["seat_view"]["me"]


def test_tick_json_is_the_payload():
    g = bridge.WebGame(seed=1, art=bridge.load_art())
    h = bridge.WebGame(seed=1, art=bridge.load_art())
    assert json.loads(g.tick_json()) == roundtrip(h.tick())


def test_bridge_imports_only_the_standard_library_pop_and_render():
    import ast
    from pathlib import Path
    src = Path(bridge.__file__).read_text()
    allowed = {"__future__", "json", "random", "pathlib", "pop", "render", "sys"}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            mods = [node.module]
        else:
            continue
        for m in mods:
            assert m.split(".")[0] in allowed, m
    assert "pygame" not in src


def test_draw_list_and_webart_are_pygame_free():
    from pathlib import Path
    for mod in ("draw_list", "webart"):
        text = (Path(draw_list.__file__).parent / f"{mod}.py").read_text()
        assert "import pygame" not in text and "from pygame" not in text


def test_versus_constants_used_by_the_page():
    assert bridge.TICKS_PER_SECOND == versus.TICKS_PER_SECOND == 12

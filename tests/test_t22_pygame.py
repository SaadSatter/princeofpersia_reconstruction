"""T22: the pygame front end: the start menu and `play.py --mode ai|baseline|human`.

Headless (SDL dummy driver). Needs the `play` extra (skipped without pygame).
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

import play                                   # noqa: E402
from agents import modes                      # noqa: E402
from render import draw, menu                 # noqa: E402


# --- the menu --------------------------------------------------------------------------
def test_the_menu_offers_the_one_mode_list_in_order():
    assert [(i, label) for i, label in menu.items()] == [(m.id, m.label) for m in modes.MODES]


def test_menu_keys_move_wrap_choose_and_quit():
    assert menu.step(0, "down") == (1, None)
    assert menu.step(0, "up") == (2, None)             # wraps
    assert menu.step(2, "down") == (0, None)
    assert menu.step(1, "return") == (1, "baseline")
    assert menu.step(0, "return") == (0, "ai")
    assert menu.step(2, "escape") == (2, "quit")
    assert menu.step(1, "x") == (1, None)


def test_the_menu_draws_with_the_games_own_palette_and_names_every_mode():
    pygame.init()
    surf = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
    for sel in range(3):
        menu.draw_menu(surf, sel)
        seen = {tuple(surf.get_at((x, y)))[:3] for x in range(surf.get_width())
                for y in range(surf.get_height())}
        assert seen <= set(menu.PALETTE), seen - set(menu.PALETTE)
        assert len(seen) >= 4
    assert set(menu.PALETTE) <= {draw.BG, draw.STONE, draw.STONE_LIGHT, draw.STONE_DARK,
                                 draw.WHITE, draw.GOLD}
    assert menu.title_lines()[0] == "SHADOW MASQUE"


def test_the_selected_row_differs_from_the_others():
    pygame.init()
    a, b = (pygame.Surface((draw.SCREEN_W, draw.SCREEN_H)) for _ in range(2))
    menu.draw_menu(a, 0)
    menu.draw_menu(b, 1)
    assert pygame.image.tobytes(a, "RGB") != pygame.image.tobytes(b, "RGB")


# --- --mode starts the right controllers -------------------------------------------------------
@pytest.fixture
def made(monkeypatch):
    calls = []
    real = modes.make_seat_rival

    def spy(mode, **kw):
        calls.append(mode)
        return real(mode, **kw)
    monkeypatch.setattr(modes, "make_seat_rival", spy)
    return calls


def _run(tmp_path, *argv, name="s.png"):
    png = tmp_path / name
    assert play.main([*argv, "--scale", "1", "--screenshot", str(png)]) == 0
    return png


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_mode_flag_starts_the_ai_seat_with_one_panel(tmp_path, made, mode):
    png = _run(tmp_path, "--mode", mode, "--keys", "A:RIGHT,A:RIGHT")
    assert made == [mode]
    assert pygame.image.load(str(png)).get_width() == draw.SCREEN_W      # the human's own panel only


def test_mode_human_is_the_two_panel_local_game_with_no_ai_seat(tmp_path, made):
    png = _run(tmp_path, "--mode", "human")
    assert made == []
    assert pygame.image.load(str(png)).get_width() > draw.SCREEN_W * 2 - 1


def test_versus_flag_still_means_human_vs_human(tmp_path, made):
    png = _run(tmp_path, "ARENA", "--versus")
    assert made == [] and pygame.image.load(str(png)).get_width() > draw.SCREEN_W * 2 - 1


def test_a_scripted_ai_mode_run_is_reproducible(tmp_path):
    keys = "A:RIGHT,A:RIGHT,A:DRAW"
    a = _run(tmp_path, "--mode", "ai", "--seed", "3", "--keys", keys, name="a.png")
    b = _run(tmp_path, "--mode", "ai", "--seed", "3", "--keys", keys, name="b.png")
    assert a.read_bytes() == b.read_bytes()


@pytest.mark.parametrize("keys, expect", [("return", ["ai"]), ("down,return", ["baseline"]),
                                           ("down,down,return", [])])
def test_menu_then_choice_starts_the_chosen_mode(tmp_path, made, keys, expect):
    _run(tmp_path, "--menu", "--menu-keys", keys)
    assert made == expect


def test_escape_in_the_menu_quits_without_starting_a_game(tmp_path, made):
    assert play.main(["--menu", "--menu-keys", "escape", "--scale", "1"]) == 0
    assert made == []


@pytest.mark.parametrize("argv", [["--mode", "ai", "--watch", "baseline"],
                                  ["--mode", "ai", "--replay", "x"]])
def test_mode_is_refused_with_watch_and_replay(argv):
    with pytest.raises(SystemExit):
        play.main(argv)


def test_mode_ai_refuses_a_wrong_hash_with_a_clear_error(monkeypatch, capsys, tmp_path):
    from agents.rl import policy
    monkeypatch.setattr(policy, "SHIPPED_SHA256", "0" * 64)
    rc = play.main(["--mode", "ai", "--scale", "1", "--screenshot", str(tmp_path / "x.png")])
    assert rc == 2 and "hash" in capsys.readouterr().err
    assert not (tmp_path / "x.png").exists()                     # no silent baseline game


def test_the_human_seat_reads_both_key_sets_in_ai_modes():
    keys = play.ai_key_names()
    physical = {v for m in play.VERSUS_KEYS.values() for k, v in m.items() if k != "shift"}
    assert set(keys) == {pygame.key.key_code(v) for v in physical}
    assert all(seat == "A" for seat, _ in keys.values())

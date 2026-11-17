"""The generated art pack (assets/generated/, OQ-8) and its renderer (render/dungeon.py).

Deterministic, offline: reads committed files only.
"""

from __future__ import annotations

import colorsys
import hashlib
import os

import pytest

from render import anim, genart
from render.anim import COL_W, HANG_DROP, hang_point, ledge_of, stand_point

pygame = pytest.importorskip("pygame")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import play  # noqa: E402

CTX = dict(tick=0, gates={}, exits={}, sprung=set(), shaking=set(), pressed=set())


@pytest.fixture(scope="module")
def art():
    pygame.init()
    from render.dungeon import DungeonArt
    return DungeonArt(genart.PACK_DIR)


def test_pack_matches_its_manifest():
    rows = genart.manifest_rows()
    listed = {r["path"] for r in rows}
    on_disk = {p.relative_to(genart.PACK_DIR).as_posix()
               for p in genart.PACK_DIR.rglob("*") if p.is_file()} - {"MANIFEST.tsv"}
    assert listed == on_disk
    for r in rows:
        data = (genart.PACK_DIR / r["path"]).read_bytes()
        assert len(data) == int(r["bytes"]) and hashlib.sha256(data).hexdigest() == r["sha256"], r["path"]
        assert r["source"].startswith(("PixelLab", "hand-built", "tools/")), r["path"]
    assert genart.pack_dir() == genart.PACK_DIR


def test_every_animation_frame_has_a_generated_frame():
    counts = {k: v["n"] for k, v in genart.sprites()["rival"].items()}
    for f in anim.ALL_FRAMES:
        strip, i = genart.frame_for(f, counts)
        assert 0 <= i < counts[strip], (f, strip, i)


def test_strips_match_their_sprite_table():
    for who, table in genart.sprites().items():
        for name, m in table.items():
            im = pygame.image.load(str(genart.PACK_DIR / m["file"]))
            assert im.get_size() == (m["w"] * m["n"], m["h"]), (who, name)
            assert 0 <= m["x"] < m["w"] and 0 <= m["y"] < m["h"]


def test_ledge_corner_is_the_inverse_of_the_hang_point():
    for row in range(3):
        for col in range(10):
            for f in (1, -1):
                edge = (col + 1) * COL_W if f > 0 else col * COL_W
                assert ledge_of(hang_point(row, col, f), f) == (edge, stand_point(row, col)[1])


def test_hang_frame_hands_on_the_ledge_and_feet_on_the_engines_line(art):
    m = art.meta["rival"]["climb"]
    bb = art.frame("rival", "climb", 0, False).get_bounding_rect()
    assert bb.y == m["y"]                                   # hands on the ledge surface
    assert bb.bottom - 1 == m["y"] + HANG_DROP               # feet where hang_point puts them
    assert bb.right <= m["x"] + 1                            # the grip wraps at most 1 px over the lip
    im = art.frame("rival", "climb", 0, False)
    feet = [x for x in range(im.get_width()) if im.get_at((x, bb.bottom - 1)).a]
    assert abs((min(feet) + max(feet)) / 2 - (m["x"] - 7)) <= 2    # feet 7 px back, in the gap


def test_a_one_cell_gap_is_drawn_one_cell_wide(art):
    from render.dungeon import surface_y
    plain = pygame.Surface((320, 192)); art.draw_room(plain, ("..........",) * 3, CTX)
    s = pygame.Surface((320, 192)); art.draw_room(s, ("..........", "..........", "____._____"), CTX)
    y = surface_y(2) + 5
    floor = [s.get_at((x, y)) != plain.get_at((x, y)) for x in range(320)]
    gap = [x for x in range(320) if not floor[x]]
    assert gap == list(range(4 * COL_W, 5 * COL_W))


def test_climb_poses_carry_the_ledge_they_hold():
    d = play.Driver("ARENA")
    for act in ("UP", "LEFT", "DOWN", "UP"):                 # climb, turn, hang down, climb again
        shown = d.apply(act)
        assert shown.accepted
        climbs = [p for p in shown.poses if p.kind == "climb"]
        if act in ("DOWN", "UP"):
            assert climbs and len({p.ledge for p in climbs}) == 1
            assert climbs[0].ledge == (3 * COL_W, stand_point(1, 3)[1])   # room 1, row 1, col 3's edge


def test_second_rival_is_crimson_not_indigo(art):
    from render.dungeon import crimson
    im = crimson(art.frame("rival", "stand", 0, False))
    hues = []
    for x in range(im.get_width()):
        for y in range(im.get_height()):
            r, g, b, a = im.get_at((x, y))
            if a:
                h, s_, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                if s_ > 0.25:
                    hues.append(h)
    assert not [h for h in hues if 0.55 <= h <= 0.75]        # no indigo cloth left
    assert len([h for h in hues if h >= 0.95 or h <= 0.03]) > 20


def test_window_draws_the_arena_with_generated_art(tmp_path):
    shot = tmp_path / "shot.png"
    assert play.main(["ARENA", "--art", "generated", "--screenshot", str(shot),
                      "--keys", "RIGHT,UP"]) == 0
    assert shot.stat().st_size > 0


def test_generated_art_is_the_default_without_original_images(monkeypatch, tmp_path):
    from render import draw
    monkeypatch.setenv("POP_ASSETS", str(tmp_path))            # no original images there
    assert draw.default_art() == "generated"
    assert draw.Renderer(original=False, art="generated").art == "generated"

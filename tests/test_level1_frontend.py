"""Frontend support for Level 1 objects and the entry drop (pure parts, no pygame)."""

import play
from level_fixture import mini_level
from pop import levelfile as LF
from pop import levels
from render import layout


def test_sword_and_skeleton_tiles_get_their_own_pieces():
    ctx = dict(room="r", tick=0, gates={}, exits={}, sprung=set(), shaking=set(), pressed=set())
    pieces = layout.room_pieces(["##########", "__S__k____", "##########"], ctx)
    names = {(p.name, p.cell) for p in pieces}
    assert ("sword", (1, 2)) in names and ("bones", (1, 5)) in names
    assert ("floor", (1, 2)) in names                 # still standing on a floor


def test_entry_drop_is_shown_as_an_opening_clip():
    d = play.Driver(levels.to_situation(LF.parse(mini_level()), "mini"))
    shown = d.intro()
    assert shown is not None and shown.source == "game"
    frames = d.obs["last_result"]["frames"]
    assert len(shown.poses) == frames
    assert shown.poses[0].y < shown.poses[-1].y        # starts above, lands below


def test_suite_situations_have_no_opening_clip():
    assert play.Driver("S3").intro() is None


def test_play_lists_level1_and_explains_missing_data(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("POP_LEVEL1", str(tmp_path / "none"))
    levels._CACHE.clear()
    assert play.main(["L1"]) == 2
    assert "tools/fetch_level1.py" in capsys.readouterr().err

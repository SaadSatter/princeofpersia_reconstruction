"""The original level-file reader, tested on level files we author ourselves."""

import pytest

from pop import levelfile as LF
from pop import levels
from pop import tiles as T
from level_fixture import build, link_bytes, mini_level


def test_wrong_size_is_refused():
    with pytest.raises(LF.LevelFormatError):
        LF.parse(b"\0" * 100)


def test_both_file_sizes_parse_to_the_same_layout():
    a, b = LF.parse(mini_level()), LF.parse(mini_level(extra_byte=True))
    assert LF.same_layout(a, b)
    assert a.sha256 != b.sha256


def test_tile_ids_and_required_bit():
    lvl = LF.parse(mini_level())
    assert lvl.tile_id(1, 12) == LF.SWORD
    assert lvl.tile_id(2, 15) == LF.EXIT and lvl.tile_id(2, 16) == LF.EXIT2
    raw = bytearray(mini_level())
    raw[0 * 30 + 11] |= LF.REQUIRED
    assert LF.parse(bytes(raw)).required(1, 11)
    assert LF.parse(bytes(raw)).tile_id(1, 11) == LF.FLOOR


@pytest.mark.parametrize("room", [1, 3, 4, 9, 13, 24])
def test_link_room_number_is_split_across_both_bytes(room):
    """Low 2 bits in LINKLOC, high 3 in LINKMAP (Source/MOVER.S:1563-1576)."""
    data = build({1: ("_" * 10,) * 3}, {1: (0, 0, 0, 0)}, door_links=[(room, 27, True)])
    assert LF.parse(data).link_chain(0) == ((room, 27),)


def test_link_chain_stops_at_last_entry_flag():
    data = build({1: ("_" * 10,) * 3}, {1: (0, 0, 0, 0)},
                 door_links=[(5, 9, False), (5, 5, True), (7, 1, True)])
    lvl = LF.parse(data)
    assert lvl.link_chain(0) == ((5, 9), (5, 5))
    assert lvl.link_chain(2) == ((7, 1),)


def test_link_chain_without_last_flag_is_refused():
    data = bytearray(build({1: ("_" * 10,) * 3}, {1: (0, 0, 0, 0)}))
    for i in range(256):
        data[1440 + i], data[1696 + i] = link_bytes(1, 0, last=False)
    with pytest.raises(LF.LevelFormatError):
        LF.parse(bytes(data)).link_chain(250)


@pytest.mark.parametrize("byte, facing", [(0xFF, +1), (0x00, -1)])
def test_start_face_byte_is_inverted(byte, facing):
    """Stored -1 is used as 0 = right (Source/SUBS.S:1516-1518)."""
    assert LF.parse(mini_level(start=(1, 0, byte))).start_facing == facing


def test_guards_are_read_but_absent_ones_skipped():
    lvl = LF.parse(mini_level(guards={2: (17, 0xFF, 0)}))
    assert lvl.guards == (LF.Guard(room=2, block=17, face_byte=0xFF, program=0),)


def test_to_situation_maps_tiles_links_and_specs():
    s = levels.to_situation(LF.parse(mini_level()), "mini")
    assert s.rooms[1][1] == "__S__u____"
    assert s.links == {1: (5, 2, 0, 0), 2: (1, 0, 0, 0), 5: (0, 1, 0, 0)}
    assert s.plate_links == {(1, 1, 5): ((2, 1, 5),), (5, 0, 2): ((5, 0, 9),)}
    assert s.gates_open == ((5, 0, 9),)
    assert s.start == (1, 0, 0, +1)
    assert s.start_falling and s.start_presses == ((5, 0, 2),)
    assert s.rules == levels.RULES and not s.exits_open


def test_unsupported_tile_id_is_refused_not_drawn_as_floor():
    data = mini_level(raw_ids={(1, 1, 9): 18})          # chomper: not in Level 1
    with pytest.raises(LF.LevelFormatError, match="tile id 18"):
        levels.to_situation(LF.parse(data), "x")


def test_non_heal_potion_is_refused():
    data = build({1: ("_" * 9 + T.POTION, "_" * 10, "_" * 10)}, {1: (0, 0, 0, 0)},
                 specs={(1, 0, 9): 2})
    with pytest.raises(LF.LevelFormatError, match="potion type 2"):
        levels.to_situation(LF.parse(data), "x", special_start=False)

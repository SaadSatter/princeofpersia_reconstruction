"""Tile symbols used in our authored room layouts.

Tile kinds follow the original's tile names (BGDATA.S:6-35, rule R-C03), but the
symbols and the layouts are our own (R-D13).
"""

SPACE = "."
FLOOR = "_"
WALL = "#"
SPIKES = "^"
LOOSE = "L"
GATE = "G"
RAISE_PLATE = "u"
DROP_PLATE = "p"
EXIT_LEFT = "E"
EXIT_RIGHT = "e"
POTION = "f"
RUBBLE = "r"
PILLAR = "P"
TORCH = "t"

ALL = {SPACE, FLOOR, WALL, SPIKES, LOOSE, GATE, RAISE_PLATE, DROP_PLATE,
       EXIT_LEFT, EXIT_RIGHT, POTION, RUBBLE, PILLAR, TORCH}

# Every tile except space and wall has a floor the kid can stand on (R-D04).
HAS_FLOOR = ALL - {SPACE, WALL}

PLATES = {RAISE_PLATE, DROP_PLATE}
EXITS = {EXIT_LEFT, EXIT_RIGHT}

# Shown to players (prompt and README). Describes appearance only.
LEGEND = {
    SPACE: "empty air (no floor)",
    FLOOR: "floor",
    WALL: "solid wall",
    SPIKES: "floor with spikes",
    LOOSE: "loose floor tile",
    GATE: "gate (see state for how open)",
    RAISE_PLATE: "raised pressure plate",
    DROP_PLATE: "sunken pressure plate",
    EXIT_LEFT: "exit door (left half)",
    EXIT_RIGHT: "exit door (right half)",
    POTION: "small potion",
    RUBBLE: "floor with rubble",
    PILLAR: "floor with pillar",
    TORCH: "floor with torch on the wall",
}

"""Scenario specs: JSON data -> validated dataclasses -> a seeded episode.

A scenario file holds scenarios; each has starts. A start fixes the initial
conditions: both rivals' room, row, column and facing, hearts, disguise state
and the guard posts (name -> room, row, [first col, last col], facing). Rooms
are arena A's (pop/arena.py); the map is not copied here.

`ScenarioEpisode` is a `VersusEpisode` that applies a start's hearts and
disguise state right after every `reset`. It touches the duel's private state
(`_duel`) because `pop/` has no public set-up hook; that is a request to the
Tech Lead (docs/final/evaluation/PROTOCOL.md, "Plumbing requests"). It changes
only the initial state, never a rule.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from pop import arena
from pop.versus import SEATS, VersusEpisode

from . import SCHEMA_VERSION
from .monitors import MONITORS

SPLITS = ("tuning", "heldout")
OTHER_CONTROLLERS = (None, "wait", "decoy")      # None: the configured controller plays seat B
WALKABLE = set("_tPr")                            # floor, torch, pillar, rubble (agents/macros.py)
MIN_FRAMES, MAX_FRAMES = 60, 3600


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class Start:
    id: str
    rivals: dict            # seat -> (room, row, col, facing)
    hearts: dict            # seat -> 1..3
    disguised: dict         # seat -> bool
    guards: dict            # name -> (room, row, (c0, c1), facing)
    other_controller: str | None = None   # forced stand-in for the seat that is not the subject
    subject: str = "A"                    # the seat being measured (seat B in a mirrored start)

    @property
    def forced_seat(self) -> str | None:
        """The seat `other_controller` plays (the one that is not the subject), or None."""
        if self.other_controller is None:
            return None
        return "B" if self.subject == "A" else "A"

    def episode_starts(self) -> dict:
        return {s: tuple(v) for s, v in self.rivals.items()}


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    split: str
    kind: str               # a key of MONITORS
    definition: str         # Saad's words
    duration_frames: int
    starts: tuple
    params: dict = field(default_factory=dict)
    subject: str = "A"

    def start(self, start_id: str) -> Start:
        for s in self.starts:
            if s.id == start_id:
                return s
        raise KeyError(start_id)


def _floor_ok(room: int, row: int, col: int) -> bool:
    rows = arena.ROOMS[room]
    return 0 <= row < 3 and 0 <= col < 10 and rows[row][col] in WALKABLE


def parse_start(raw: dict, where: str = "") -> Start:
    try:
        rivals = {s: (int(raw["rivals"][s][0]), int(raw["rivals"][s][1]),
                      int(raw["rivals"][s][2]), int(raw["rivals"][s][3])) for s in SEATS}
        hearts = {s: int(raw.get("hearts", {}).get(s, 3)) for s in SEATS}
        disguised = {s: bool(raw.get("disguised", {}).get(s, False)) for s in SEATS}
        guards = {n: (int(g[0]), int(g[1]), (int(g[2][0]), int(g[2][1])), int(g[3]))
                  for n, g in raw.get("guards", {}).items()}
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise SpecError(f"{where}{raw.get('id', '?')}: malformed start ({exc!r})") from exc
    start = Start(raw["id"], rivals, hearts, disguised, guards, raw.get("other_controller"),
                  raw.get("subject", "A"))
    validate_start(start, where)
    return start


def validate_start(start: Start, where: str = "") -> None:
    tag = f"{where}{start.id}"
    if start.other_controller not in OTHER_CONTROLLERS:
        raise SpecError(f"{tag}: other_controller must be one of {OTHER_CONTROLLERS}")
    if start.subject not in SEATS:
        raise SpecError(f"{tag}: subject must be one of {SEATS}")
    cells = []
    for seat,(room, row, col, facing) in start.rivals.items():
        if room not in arena.ROOMS or facing not in (-1, 1) or not _floor_ok(room, row, col):
            raise SpecError(f"{tag}: rival {seat} start {(room, row, col, facing)} is not "
                            "a walkable cell of arena A")
        cells.append((room, row, col))
        if not 1 <= start.hearts[seat] <= 3:
            raise SpecError(f"{tag}: hearts of {seat} must be 1..3")
    if cells[0] == cells[1]:
        raise SpecError(f"{tag}: both rivals start on one cell")
    for name, (room, row, (c0, c1), facing) in start.guards.items():
        if room not in arena.ROOMS or facing not in (-1, 1) or c0 > c1:
            raise SpecError(f"{tag}: guard {name} post is malformed")
        if not all(_floor_ok(room, row, c) for c in range(c0, c1 + 1)):
            raise SpecError(f"{tag}: guard {name} patrol {c0}..{c1} crosses a non-floor cell")


def parse_scenarios(raw: dict, expect_split: str | None = None) -> dict[str, Scenario]:
    if raw.get("schema") != SCHEMA_VERSION + "/scenarios":
        raise SpecError("not a Shadow Masque scenario file (schema mismatch)")
    split = raw["split"]
    if split not in SPLITS or (expect_split and split != expect_split):
        raise SpecError(f"split must be {expect_split or SPLITS}, got {split!r}")
    out: dict[str, Scenario] = {}
    for item in raw["scenarios"]:
        if item["kind"] not in MONITORS:
            raise SpecError(f"{item['id']}: unknown kind {item['kind']!r}")
        frames = int(item["duration_frames"])
        if not MIN_FRAMES <= frames <= MAX_FRAMES:
            raise SpecError(f"{item['id']}: duration_frames must be {MIN_FRAMES}..{MAX_FRAMES}")
        starts = tuple(parse_start(s, f"{item['id']}/") for s in item["starts"])
        ids = [s.id for s in starts]
        if not starts or len(set(ids)) != len(ids):
            raise SpecError(f"{item['id']}: start ids must be unique and not empty")
        sc = Scenario(item["id"], item["name"], split, item["kind"], item["definition"],
                      frames, starts, dict(item.get("params", {})), item.get("subject", "A"))
        if sc.id in out or sc.subject != "A":
            raise SpecError(f"{sc.id}: duplicate id, or subject other than seat A")
        out[sc.id] = sc
    return out


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_scenario_file(path: str | Path, expect_split: str | None = None) -> dict[str, Scenario]:
    return parse_scenarios(json.loads(Path(path).read_text()), expect_split)


class ScenarioEpisode(VersusEpisode):
    """A VersusEpisode whose `reset` also applies the start's initial state."""

    def __init__(self, start: Start, duration_frames: int, seed: int = 0) -> None:
        self._start = start
        super().__init__(arena.situation("A"), start.episode_starts(), seed, duration_frames,
                         {n: (g[0], g[1], g[2], g[3]) for n, g in start.guards.items()})

    def reset(self, seed: int) -> None:
        super().reset(seed)
        duel, st = self._duel, self._start
        for seat in SEATS:
            r = duel.rivals[seat]
            r.kid.hp = st.hearts[seat]
            r.disguised = st.disguised[seat]


def episode_factory(scenario: Scenario, start_id: str):
    """A zero-argument factory for `VersusRunner` / `replay`."""
    start = scenario.start(start_id)
    return lambda: ScenarioEpisode(start, scenario.duration_frames)


def make_monitor(scenario: Scenario, start: Start, **overrides):
    params = {**scenario.params, **overrides}
    if scenario.kind == "identify":
        rival = "B" if start.subject == "A" else "A"
        params.setdefault("rival_hp_start", start.hearts[rival])
    return MONITORS[scenario.kind](start.subject, **params)

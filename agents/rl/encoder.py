"""Feature encoder for the PPO rival (docs/final/RL_POLICY.md, task T07).

Maps ONE seat's observation, plus a short history this object keeps itself, to
a fixed-length vector of floats. Standard library only (it also runs in the
browser build).

What it reads (everything a human sees on screen, nothing else):
  room tiles, edges, `me` (position, facing, posture, hearts, stance, sword,
  disguise, knock-down timer, current move), `figures` (position, facing,
  posture, stance, sword, current move and the label "guard" or "rival"),
  `swords`, `suspicion` (the on-screen meter).
What it never reads: `minutes_left` and the other duel clock fields, the task
text, the episode outcome, any id or seed. A disguised rival and a real guard
with the same observed fields therefore give identical features.

Figures are ordered by distance to me, then by their observed fields, never by
their position in the list, and only the nearest K are used.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.macros import MACROS, RESERVED

MACRO_SLOTS: tuple[str, ...] = tuple(MACROS) + tuple(RESERVED)   # 9 slots; RIG_TRAP stays masked
K_FIGURES = 3
ROWS, COLS = 3, 10
SIGHT = 5                         # a guard sees 5 cells (R-V14, a published rule)
POSTURES = ("standing", "hanging", "falling")           # anything else is "other"
FIG_POSTURES = ("standing", "downed", "knocked_down")
STANCES = (None, "low", "mid", "high")
LEAPS = ("jumped", "flipped", "climbed", "hanging", "dropped")
TILE_CHANNELS = {"wall": "#", "air": ".", "hazard": "^", "loose": "L"}
SPECIAL = set("GupEe")            # gates, plates, exits
STILL_CAP, NOREACT_CAP, ROOM_CAP = 48, 24, 60

# ----------------------------------------------------------------- feature names
def _names() -> list[str]:
    n = []
    for r in range(ROWS):
        for c in range(COLS):
            n += [f"tile_{r}{c}_{k}" for k in ("wall", "air", "hazard", "loose", "special")]
    n += ["edge_left", "edge_right"]
    n += ["me_row", "me_col", "me_facing"] + [f"me_posture_{p}" for p in POSTURES + ("other",)]
    n += ["me_hp", "me_one_heart"] + [f"me_stance_{s}" for s in ("none", "low", "mid", "high")]
    n += ["me_armed", "me_disguised", "me_knocked_down", "me_moving", "me_leaping"]
    n += ["susp_max", "susp_nearest"]
    n += ["sword_present", "sword_dx", "sword_dy", "sword_count"]
    for k in range(K_FIGURES):
        p = f"fig{k}_"
        n += [p + s for s in ("present", "dx", "dy", "same_row", "ahead", "faces_me",
                              "label_rival", "posture_standing", "posture_downed",
                              "posture_knocked_down", "posture_other", "armed",
                              "stance_none", "stance_low", "stance_mid", "stance_high",
                              "moving", "leap_seen", "still", "noreact")]
    n += [f"last_macro_{m}" for m in MACRO_SLOTS] + ["last_macro_none"]
    n += ["last_running", "last_done", "last_failed", "rooms_seen", "in_room"]
    return n


FIG_WIDTH = 20
FEATURE_NAMES: list[str] = _names()
N_FEATURES = len(FEATURE_NAMES)


def _onehot(value, options) -> list[float]:
    return [1.0 if value == o else 0.0 for o in options]


@dataclass
class _Track:
    row: int
    col: int
    still: int = 0
    noreact: int = 0
    leap: bool = False
    used: bool = False


@dataclass
class Encoder:
    """Stateful: call `update(obs)` at every runner decision and `features(...)`
    when a macro choice is needed (`encode` does both)."""

    decision_every: int = 6
    tracks: list = field(default_factory=list)
    rooms: set = field(default_factory=set)
    room: str | None = None
    in_room: int = 0

    def reset(self) -> None:
        self.tracks, self.rooms, self.room, self.in_room = [], set(), None, 0

    # ---------------------------------------------------------------- history
    def update(self, obs: dict) -> None:
        label = obs["room"]
        if label != self.room:
            self.room, self.in_room, self.tracks = label, 0, []
            self.rooms.add(label)
        self.in_room += 1
        me = obs["me"]
        old, new = self.tracks, []
        for f in sorted(obs["figures"], key=_fields_key):
            if f["posture"] in ("downed", "dead"):
                continue
            best = None
            for t in old:
                if (not t.used and t.row == f["row"] and abs(t.col - f["col"]) <= 2
                        and (best is None or abs(t.col - f["col"]) < abs(best.col - f["col"]))):
                    best = t
            if best is not None:
                best.used = True
            tr = _Track(f["row"], f["col"], best.still if best else 0,
                        best.noreact if best else 0, best.leap if best else False)
            m = f["motion"]
            tr.still = tr.still + self.decision_every if m is None else 0
            if m is not None and (m["effect"] in LEAPS or
                                  (m["effect"] == "moved" and m["frames"] <= 4 and not f["armed"])):
                tr.leap = True
            side = 1 if f["facing"] == "right" else -1
            dist = (me["col"] - f["col"]) * side
            sees = (not me["disguised"] and me["row"] == f["row"] and 1 <= dist <= SIGHT
                    and not _wall_between(obs["tiles"], f["row"], f["col"], me["col"]))
            if sees and not f["armed"] and (m is None or m["effect"] != "drew"):
                tr.noreact += self.decision_every
            else:
                tr.noreact = 0
            new.append(tr)
        for t in new:
            t.used = False
        self.tracks = new

    def _track_for(self, f: dict):
        for t in self.tracks:
            if t.row == f["row"] and t.col == f["col"]:
                return t
        return None

    # --------------------------------------------------------------- features
    def encode(self, obs: dict, legal: tuple, status: dict | None = None) -> list[float]:
        self.update(obs)
        return self.features(obs, legal, status)

    def features(self, obs: dict, legal: tuple, status: dict | None = None) -> list[float]:
        me, x = obs["me"], []
        tiles = obs["tiles"]
        for r in range(ROWS):
            for c in range(COLS):
                ch = tiles[r][c]
                x += [float(ch == "#"), float(ch == "."), float(ch == "^"),
                      float(ch == "L"), float(ch in SPECIAL)]
        x += [float(bool(obs["edges"]["left"])), float(bool(obs["edges"]["right"]))]
        face = 1.0 if me["facing"] == "right" else -1.0
        post = me["posture"] if me["posture"] in POSTURES else "other"
        m = me.get("motion")
        x += [me["row"] / (ROWS - 1), me["col"] / (COLS - 1), face]
        x += _onehot(post, POSTURES + ("other",))
        x += [me["hp"] / max(1, me["max_hp"]), float(me["hp"] <= 1)]
        x += _onehot(me["stance"], STANCES)
        x += [float(bool(me["armed"])), float(bool(me["disguised"])),
              min(me["knocked_down_frames"], 60) / 60.0,
              float(m is not None and m["effect"] != "waited"),
              float(m is not None and m["effect"] in LEAPS)]
        susp = obs.get("suspicion", [])
        x.append(max([s["level"] for s in susp] or [0]) / 100.0)
        near = min(susp, key=lambda s: (abs(s["col"] - me["col"]) + 4 * abs(s["row"] - me["row"]),
                                         s["row"], s["col"]), default=None)
        x.append(0.0 if near is None else near["level"] / 100.0)
        swords = obs.get("swords", [])
        sw = min(swords, key=lambda s: (abs(s["col"] - me["col"]) + 4 * abs(s["row"] - me["row"]),
                                         s["row"], s["col"], s["flying"]), default=None)
        x += ([0.0, 0.0, 0.0] if sw is None else
              [1.0, (sw["col"] - me["col"]) / 9.0, (sw["row"] - me["row"]) / 2.0])
        x.append(min(len(swords), 3) / 3.0)
        figs = sorted(obs["figures"], key=lambda f: (
            abs(f["row"] - me["row"]) * 4 + abs(f["col"] - me["col"]), _fields_key(f)))[:K_FIGURES]
        for f in figs:
            t = self._track_for(f)
            dx = f["col"] - me["col"]
            fpost = f["posture"] if f["posture"] in FIG_POSTURES else "other"
            fm = f["motion"]
            fside = 1 if f["facing"] == "right" else -1
            x += [1.0, dx / 9.0, (f["row"] - me["row"]) / 2.0, float(f["row"] == me["row"]),
                  float(dx * (1 if face > 0 else -1) > 0),
                  float(dx != 0 and fside * dx < 0), float(f["kind"] == "rival")]
            x += _onehot(fpost, FIG_POSTURES + ("other",))
            x += [float(bool(f["armed"]))] + _onehot(f["stance"], STANCES)
            x += [float(fm is not None and fm["effect"] != "waited"),
                  float(t is not None and t.leap),
                  min(0 if t is None else t.still, STILL_CAP) / STILL_CAP,
                  min(0 if t is None else t.noreact, NOREACT_CAP) / NOREACT_CAP]
        x += [0.0] * (FIG_WIDTH * (K_FIGURES - len(figs)))
        last = status["macro"] if status else None
        x += _onehot(last, MACRO_SLOTS) + [0.0 if last in MACRO_SLOTS else 1.0]
        st = status["state"] if status else "idle"
        x += [float(st == "running"), float(st == "done"), float(st == "failed")]
        x += [min(len(self.rooms), 6) / 6.0, min(self.in_room, ROOM_CAP) / ROOM_CAP]
        return x


def _wall_between(tiles, row, c1, c2) -> bool:
    lo, hi = sorted((c1, c2))
    return any(tiles[row][c] == "#" for c in range(lo + 1, hi))


def _fields_key(f: dict) -> tuple:
    """A total order on observed fields only (ties never fall back to list order)."""
    m = f["motion"]
    return (f["row"], f["col"], f["kind"], f["facing"], f["posture"], str(f["stance"]),
            bool(f["armed"]), "" if m is None else f"{m['effect']}:{m['frame']}:{m['frames']}")


# ------------------------------------------------------------------ action mask
def macro_mask(obs: dict, legal: tuple) -> list[bool]:
    """Which of the 9 macro slots can be started now. RIG_TRAP stays False until
    traps exist. With no legal input only WAIT remains."""
    mask = {m: False for m in MACRO_SLOTS}
    mask["WAIT"] = True
    if not legal:
        return [mask[m] for m in MACRO_SLOTS]
    me = obs["me"]
    live = [f for f in obs["figures"] if f["posture"] not in ("downed", "dead")]
    mask["SEARCH"] = mask["BLEND"] = mask["CLIMB"] = True
    if live:
        mask["FOLLOW"] = mask["STRIKE"] = mask["FLEE"] = True
    if not me["disguised"] and any(f["posture"] == "downed" for f in obs["figures"]):
        mask["DISGUISE"] = True
    return [mask[m] for m in MACRO_SLOTS]

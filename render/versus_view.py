"""Poses for a versus seat's view (pure Python, no pygame).

Reads only one seat's observation (pop/versus.py `observe`): its own rival
(`me`) and the figures in its room, each with an optional `motion` (the move
in progress: effect, frames done, length, planned end if in this room). A
move is shown with the same clips as single-player play (render/anim.py
`clip`), built once for the whole move and indexed by its progress, so the
picture keeps up with the duel's real-time ticks.
"""

from __future__ import annotations

from dataclasses import dataclass

from pop import physics as P

from .anim import AnimState, Pose, Step, clip, idle_pose, stand_point


@dataclass(frozen=True)
class Sprite:
    """A swordplay frame drawn straight from one of our strips (no original frame
    number exists for it): strip name, frame index, feet point, facing."""
    strip: str
    index: int
    x: float
    y: float
    facing: int


COMBAT_STRIPS = {"lunge": None, "throw": "throw", "dive_kick": "dive_kick",
                 "sweep": "sweep", "took_sword": "take", "took_uniform": "take",
                 "drew": "stance_mid"}


def _dir(facing: str) -> str:
    return "RIGHT" if facing == "right" else "LEFT"


def action_for(motion: dict, posture: str, facing: str) -> str:
    """The input that produces this move (anim.clip branches on action and effect)."""
    e, n = motion["effect"], motion["frames"]
    d = _dir(facing)
    if e == "turned":
        return _dir(motion["to_facing"])
    if e == "moved":
        return "STEP_" + d if n == P.STEP else d
    if e == "jumped":
        return "JUMP_" + d
    if e in ("bumped", "edge"):
        return "JUMP_" + d if n == P.JUMP_IN_PLACE else d
    if e in ("climbed", "won"):
        return "UP"
    if e in ("hanging", "drank", "took_sword", "dropped"):
        return "DOWN"
    if e == "none":
        return "DOWN" if n == P.CROUCH else "UP"
    return "WAIT"


def _kid(view: dict) -> dict:
    return {"row": view["row"], "col": view["col"], "facing": view["facing"],
            "posture": view["posture"]}


def _strip_index(frame: int, frames: int, n: int) -> int:
    return max(0, min(n - 1, (max(1, frame) - 1) * n // max(1, frames)))


def sprite(view: dict, counts: dict[str, int]) -> Sprite | None:
    """A swordplay picture for `view`, or None when an ordinary pose applies.
    counts: frames per rival strip (sprites.json)."""
    f = 1 if view["facing"] == "right" else -1
    x, y = stand_point(view["row"], view["col"])
    if view["posture"] == "knocked_down" or view.get("knocked_down_frames"):
        return Sprite("death", 6, x, y, f)                       # lying on the floor
    m = view.get("motion")
    if m and m["effect"] in COMBAT_STRIPS:
        strip = COMBAT_STRIPS[m["effect"]] or f"lunge_{view.get('stance') or 'mid'}"
        i = _strip_index(m["frame"], m["frames"], counts[strip])
        if m["effect"] == "dive_kick" and m["to"] is not None:
            tx, ty = stand_point(*m["to"])
            t = min(1.0, m["frame"] / max(1, m["frames"]))
            x, y = x + (tx - x) * t, y + (ty - y) * t - 10 * (1 - t)   # dropping in
        return Sprite(strip, i, x, y, f)
    if not m and view.get("armed") and view["posture"] == "standing" and view.get("stance"):
        return Sprite(f"stance_{view['stance']}", 0, x, y, f)
    return None


def pose(view: dict, room: str, cache: dict | None = None, key: object = None) -> Pose:
    """This frame's pose for `view` (obs["me"] or one of obs["figures"]).
    cache/key: optional memo so a move's clip is built once."""
    m = view.get("motion")
    if not m or m["frames"] <= 0 or m["effect"] in COMBAT_STRIPS or m["effect"] == "sheathed":
        return idle_pose(_kid(view))
    before = _kid(view)
    after = dict(before)
    if m["to"] is not None:
        after["row"], after["col"] = m["to"]
    elif m["effect"] == "moved":                       # leaving the room: run off the edge
        after["col"] = view["col"] + (1 if view["facing"] == "right" else -1)
    after["posture"] = m["to_posture"] if m["to_posture"] != "won" else "standing"
    after["facing"] = m["to_facing"]
    action = action_for(m, view["posture"], view["facing"])
    sig = (key, view["row"], view["col"], view["facing"], view["posture"],
           m["effect"], m["frames"], tuple(m["to"] or ()), m["to_facing"])
    poses = cache.get(sig) if cache is not None else None
    if poses is None:
        step = Step(action=action, before=before, after=after, before_room=room,
                    after_room=room, effect=m["effect"], frames=m["frames"])
        poses = clip(step, AnimState())
        if cache is not None:
            cache.clear() if len(cache) > 64 else None
            cache[sig] = poses
    return poses[max(0, min(len(poses), m["frame"]) - 1)]


GUARD_LOOK = ("lunge", "drew", "sheathed", "turned")       # guard-only clips


def guard_sprite(view: dict, counts: dict[str, int]) -> Sprite | None:
    """A guard figure (or anything observed as one) drawn from the guard strips:
    patrol walking (a careful step's pace), turning, drawing, the three stances,
    lunges at the stance's height, knocked down and downed. Returns None for
    any other move (running, jumping, climbing, hanging, falling): the caller
    draws those with `pose` and the guard's movement strips, as for a rival."""
    f = 1 if view["facing"] == "right" else -1
    x, y = stand_point(view["row"], view["col"])
    if view["posture"] == "downed":
        return Sprite("downed", counts["downed"] - 1, x, y, f)
    if view["posture"] == "knocked_down":
        return Sprite("downed", min(3, counts["downed"] - 1), x, y, f)
    if view["posture"] in ("hanging", "falling"):
        return None
    m = view.get("motion")
    if m:
        if m["effect"] == "lunge":
            strip = f"lunge_{view.get('stance') or 'mid'}"
            return Sprite(strip, _strip_index(m["frame"], m["frames"], counts[strip]), x, y, f)
        if m["effect"] == "moved" and m["frames"] == P.STEP:
            if m["to"] is not None:
                tx, ty = stand_point(*m["to"])
                t = min(1.0, m["frame"] / max(1, m["frames"]))
                x, y = x + (tx - x) * t, y + (ty - y) * t
            return Sprite("walk", _strip_index(m["frame"], m["frames"], counts["walk"]), x, y, f)
        if m["effect"] == "drew":
            return Sprite("stance_mid", 0, x, y, f)
        if m["effect"] not in GUARD_LOOK:
            return None                                   # run, jump, climb...: like a rival
    if view.get("armed") and view.get("stance"):
        return Sprite(f"stance_{view['stance']}", 0, x, y, f)
    return Sprite("stand", 0, x, y, f)

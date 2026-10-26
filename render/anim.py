"""Turn one engine step into an animation clip (pure Python, no pygame).

The engine moves the kid whole blocks per action and reports how many frames
the action took (R-D01). This module shows that step as exactly that many
display frames: the original frame sequence for the move, resampled to the
step's length, with the kid slid between the observed start and end cells
(R-D26). It reads only what the observation shows: the kid before and after,
the room label, the step's effect and frames, and the outcome.

Frame numbers are the original's (`Source/SEQTABLE.S`, historicalsource
commit 2b4ddb5). The DOS image for frame N is `KID/res(400+N).png`
(docs/ASSETS.md). Coordinates are pixels in the 320x192 room picture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pop import physics as P

COL_W = 32                 # original tile width in pixels
ROW_H = 63                 # original row height in pixels
TOP = 3                    # the floor edge of the room above shows in y 0..3
FEET = 55                  # feet line below a row's top
HANG_DROP = 33             # hanging: feet this far below the ledge's feet line
ROOM_W, ROOM_H = 10 * COL_W, TOP + 3 * ROW_H

# Original frame numbers, with their SEQTABLE.S labels.
STAND = 15                                         # stand, line 182
START_RUN = (1, 2, 3, 4, 5, 6)                     # startrun, line 159
RUN_CYCLE = (7, 8, 9, 10, 11, 12, 13, 14)          # runcyc1, line 168
STAND_JUMP = tuple(range(16, 34))                  # standjump, line 442
RUN_JUMP = tuple(range(34, 45))                    # runjump, line 469
TURN = tuple(range(45, 53))                        # turn, line 541
JUMP_UP = tuple(range(67, 79))                     # jumpup, line 905
HANG_DROP_FRAMES = (81, 82, 83, 84, 85)            # hangdrop, line 850
HANG = 91                                          # hang, line 757
FALL = (102, 103, 104, 105, 106)                   # stepfall/freefall, lines 640, 882
CROUCH = (107, 108, 109)                           # stoop / softland, lines 1227, 1316
STAND_UP = (110, 111, 112, 113, 114, 115, 116, 117, 118, 119)  # standup, line 1241
FULL_STEP = tuple(range(121, 133))                 # fullstep, line 1069
CLIMB_UP = tuple(range(135, 149))                  # climbup, line 816
CLIMB_DOWN = (148, 146, 144, 142, 140, 138, 136)   # climbdown, line 797 (reverse)
IMPALED = 177                                      # impale, line 1417
DROP_DEAD = (179, 180, 181, 182, 183, 185)         # dropdead, line 1401
DEAD = 185
DRINK = tuple(range(191, 206))                     # drinkpotion, line 1297
STAIRS = tuple(range(217, 229))                    # climbstairs, line 1463

ALL_FRAMES = frozenset(
    {STAND, HANG, IMPALED, DEAD} | set(START_RUN) | set(RUN_CYCLE) | set(STAND_JUMP)
    | set(RUN_JUMP) | set(TURN) | set(JUMP_UP) | set(HANG_DROP_FRAMES) | set(FALL)
    | set(CROUCH) | set(STAND_UP) | set(FULL_STEP) | set(CLIMB_UP) | set(CLIMB_DOWN)
    | set(DROP_DEAD) | set(DRINK) | set(STAIRS))

HORIZONTAL = {"LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT", "JUMP_LEFT", "JUMP_RIGHT",
              "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT"}


@dataclass(frozen=True)
class Pose:
    """One display frame of the kid."""
    frame: int                 # original frame number (0: not drawn)
    x: float                   # feet point, room pixels
    y: float
    facing: int                # +1 right, -1 left
    kind: str                  # stand run step jump turn hang climb fall crouch drink dead stairs
    flash: bool = False        # hurt this frame (red flash)

    @property
    def visible(self) -> bool:
        return self.frame != 0


@dataclass
class Step:
    """What one accepted step looked like from the player's side."""
    action: str
    before: dict               # observation["kid"] before the step
    after: dict                # observation["kid"] after the step
    before_room: str
    after_room: str
    effect: str | None
    frames: int
    fell_rows: int = 0
    terminal: str | None = None   # outcome reason if the step ended the episode


@dataclass
class AnimState:
    run_phase: int = -1        # -1: not running; else index into RUN_CYCLE halves
    run_dir: int = 0
    history: list = field(default_factory=list)


def facing_of(kid: dict) -> int:
    return 1 if kid["facing"] == "right" else -1


def stand_point(row: float, col: float) -> tuple[float, float]:
    return col * COL_W + COL_W / 2, TOP + row * ROW_H + FEET


def hang_point(row: int, col: int, facing: int) -> tuple[float, float]:
    """Feet point while hanging in cell (row, col) from the ledge at col+facing."""
    edge = (col + 1) * COL_W if facing > 0 else col * COL_W
    return edge - facing * 7, TOP + row * ROW_H + FEET + HANG_DROP


def resample(seq: tuple[int, ...] | list[int], n: int) -> list[int]:
    """Pick n frames evenly from seq (the original sequence, shortened or held)."""
    if n <= 0:
        return []
    return [seq[min(len(seq) - 1, (i * len(seq)) // n)] for i in range(n)]


def lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def idle_pose(kid: dict, terminal: str | None = None, fell_rows: int = 0) -> Pose:
    """The pose to show between steps."""
    f = facing_of(kid)
    r, c = kid["row"], kid["col"]
    posture = kid["posture"]
    if posture == "hanging":
        return Pose(HANG, *hang_point(r, c, f), f, "hang")
    if posture == "falling":
        return Pose(FALL[-1], *stand_point(r, c), f, "fall")
    if posture == "won":
        return Pose(0, *stand_point(r, c), f, "stairs")
    if posture == "dead":
        if terminal == "died:fall" and fell_rows == 0:
            return Pose(0, *stand_point(r, c), f, "dead")     # fell out of the world
        frame = IMPALED if terminal == "died:spikes" else DEAD
        return Pose(frame, *stand_point(r, c), f, "dead")
    return Pose(STAND, *stand_point(r, c), f, "stand")


def _virtual_before(step: Step) -> tuple[int, int]:
    """The before cell in the after room's coordinates (the room may change mid-step)."""
    row, col = step.before["row"], step.before["col"]
    if step.before_room == step.after_room:
        return row, col
    a_row, a_col = step.after["row"], step.after["col"]
    d = facing_of(step.before)
    if step.action in HORIZONTAL and d * (a_col - col) < 0:
        col -= 10 * d                                  # crossed the side edge
    if step.action == "UP" and a_row > row:
        row += 3                                       # climbed into the room above
    elif a_row < row or (a_row == row and col == step.before["col"]):
        row -= 3                                       # fell into the room below
    return row, col


def _movement_frames(step: Step, running_ok: bool) -> int:
    """Frames the move itself took before any fall (engine constants, pop/physics.py)."""
    a, e, b = step.action, step.effect, step.before["posture"]
    if b == "falling" or a == "WAIT":
        return 0
    if e == "turned":
        return P.TURN
    if e in ("bumped", "edge"):
        return P.JUMP_IN_PLACE if a.startswith(("JUMP", "RUN_JUMP")) else P.BUMP
    if a in ("LEFT", "RIGHT"):
        return P.RUN
    if a in ("STEP_LEFT", "STEP_RIGHT"):
        return P.STEP
    if a in ("JUMP_LEFT", "JUMP_RIGHT"):
        return P.JUMP
    if a in ("RUN_JUMP_LEFT", "RUN_JUMP_RIGHT"):
        return P.RUN + P.RUN_JUMP_FLIGHT if running_ok else P.RUN
    if a == "UP":
        if b == "hanging":
            return P.HANG_UP
        return {"won": P.STAIRS, "climbed": P.CLIMB_UP}.get(e, P.JUMP_IN_PLACE)
    if a == "DOWN":
        if b == "hanging":
            return 0
        return {"drank": P.DRINK, "hanging": P.HANG_DOWN}.get(e, P.CROUCH)
    return step.frames


def clip(step: Step, state: AnimState | None = None) -> list[Pose]:
    """Exactly max(step.frames, 1) poses for this step."""
    state = state if state is not None else AnimState()
    n = max(step.frames, 1)
    b, a = step.before, step.after
    fb, fa = facing_of(b), facing_of(a)
    vb_row, vb_col = _virtual_before(step)
    start = stand_point(vb_row, vb_col)
    if b["posture"] == "hanging":
        start = hang_point(vb_row, vb_col, fb)
    end_stand = stand_point(a["row"], a["col"])
    poses: list[Pose] = []
    act = step.action
    eff = step.effect
    fell = a["posture"] in ("falling",) or a["row"] != vb_row or eff in ("landed", "hurt")
    if a["posture"] == "dead" and step.terminal == "died:spikes":
        fell = a["row"] != vb_row
    # A running jump whose run-up block fell away is a plain run.
    running_ok = not (act.startswith("RUN_JUMP") and abs(a["col"] - vb_col) <= 1)
    move_n = min(_movement_frames(step, running_ok), n)
    move_end = (a["col"], vb_row)                     # moves are horizontal; falls vertical

    def add(frames: list[int], p0, p1, facing, kind, ease=None):
        k = len(frames)
        for i, fr in enumerate(frames):
            t = (i + 1) / k if k else 1.0
            if ease:
                t = ease(t)
            poses.append(Pose(fr, *lerp(p0, p1, t), facing, kind))

    continuing_run = state.run_phase >= 0 and state.run_dir == fb
    new_run_phase = -1

    # ---- the move ---------------------------------------------------------
    if b["posture"] == "falling" or act == "WAIT":
        pass
    elif eff == "turned":
        add(resample(TURN, move_n), start, start, fa, "turn")
    elif eff in ("bumped", "edge"):
        seq = JUMP_UP if move_n >= P.JUMP_IN_PLACE else (STAND,)
        add(resample(seq, move_n), start, start, fb, "stand")
    elif act in ("LEFT", "RIGHT") or (act.startswith("RUN_JUMP") and not running_ok):
        mid = stand_point(move_end[1], move_end[0])
        if continuing_run:
            half = state.run_phase % 2
            seq = RUN_CYCLE[half * 4:half * 4 + 4]
            new_run_phase = state.run_phase + 1
        else:
            seq = START_RUN
            new_run_phase = 0
        add(resample(seq, move_n), start, mid, fb, "run")
    elif act in ("STEP_LEFT", "STEP_RIGHT"):
        add(resample(FULL_STEP, move_n), start, stand_point(move_end[1], move_end[0]), fb, "step")
    elif act in ("JUMP_LEFT", "JUMP_RIGHT"):
        land = stand_point(move_end[1], move_end[0])
        add(resample(STAND_JUMP, move_n), start, land, fb, "jump",
            ease=lambda t: min(1.0, max(0.0, (t - 0.2) / 0.65)))
    elif act.startswith("RUN_JUMP"):
        first = stand_point(vb_row, vb_col + fb)
        land = stand_point(move_end[1], move_end[0])
        seq = RUN_CYCLE[:4] if continuing_run else START_RUN
        add(resample(seq, P.RUN), start, first, fb, "run")
        add(resample(RUN_JUMP, move_n - P.RUN), first, land, fb, "jump")
    elif act == "UP" and eff == "won":
        door = (start[0] + 20, start[1] - 22)          # the stairs rise to the right
        add(resample(STAIRS, move_n - 1), start, door, fb, "stairs")
        poses.append(Pose(0, *door, fb, "stairs"))
    elif act == "UP" and b["posture"] == "hanging":
        add(resample(CLIMB_UP, move_n), start, end_stand, fa, "climb")
    elif act == "UP" and eff == "climbed":
        grab = hang_point(vb_row - 1, vb_col, fb)
        add(resample(JUMP_UP[:8], 4), start, grab, fb, "jump")
        add(resample(CLIMB_UP, move_n - 4), grab, end_stand, fb, "climb")
    elif act == "UP":
        add(resample(JUMP_UP, move_n), start, start, fb, "jump")
    elif act == "DOWN" and eff == "drank":
        add(resample(DRINK, move_n), start, start, fb, "drink")
    elif act == "DOWN" and eff == "hanging":
        add(resample(CLIMB_DOWN, move_n), start, hang_point(a["row"], a["col"], fa), fa, "climb")
    elif act == "DOWN" and b["posture"] != "hanging":
        add(resample(CROUCH + STAND_UP[-1:], move_n), start, start, fb, "crouch")

    # ---- the fall (if any), then landing ------------------------------------
    rest = n - len(poses)
    if rest > 0:
        p0 = (poses[-1].x, poses[-1].y) if poses else start
        if b["posture"] == "hanging" and act == "DOWN":
            p0 = start
        if fell or b["posture"] == "falling":
            bottomless = step.terminal == "died:fall" and step.fell_rows == 0 \
                and a["posture"] == "dead"
            landed = a["posture"] in ("standing", "dead") and not bottomless
            land_n = min(3, rest - 1) if landed and rest > 1 else 0
            fall_n = rest - land_n
            target = end_stand
            if bottomless:
                target = (end_stand[0], ROOM_H + 70)
            elif a["posture"] == "hanging":
                target = hang_point(a["row"], a["col"], fa)
            if b["posture"] == "standing" and act == "WAIT":
                hold = fall_n // 2                        # floor gives way mid-wait
                add([STAND] * hold, p0, p0, fb, "stand")
                fall_n -= hold
            first = HANG_DROP_FRAMES if (b["posture"] == "hanging" and act == "DOWN") else FALL
            seq = list(first) + [FALL[-1]] * max(0, fall_n - len(first))
            add(resample(seq, fall_n), p0, target, fa, "fall", ease=lambda t: t * t)
            if land_n:
                add(resample(CROUCH, land_n), target, target, fa, "crouch")
        else:
            last = poses[-1] if poses else idle_pose(b)
            idle = idle_pose(a)
            if act == "WAIT":
                last = Pose(idle.frame, *start, fa, idle.kind) if b["posture"] != "falling" else idle
            add([idle.frame if act == "WAIT" else last.frame] * rest,
                (last.x, last.y), (idle.x, idle.y), fa, last.kind if act != "WAIT" else idle.kind)

    poses = poses[:n]

    # ---- endings: hurt flash, death, win -------------------------------------
    if eff == "hurt" or (step.terminal or "").startswith("died"):
        for i in range(max(0, len(poses) - 2), len(poses)):
            poses[i] = Pose(poses[i].frame, poses[i].x, poses[i].y, poses[i].facing,
                            poses[i].kind, flash=True)
    if a["posture"] == "dead":
        final = idle_pose(a, step.terminal, step.fell_rows)
        if final.visible:
            k = min(len(poses), 3 if final.frame == DEAD else 1)
            tail = resample(DROP_DEAD[-3:], k) if final.frame == DEAD else [IMPALED]
            for j, fr in enumerate(tail):
                i = len(poses) - k + j
                poses[i] = Pose(fr, final.x, final.y, final.facing, "dead", flash=True)

    if fell or b["posture"] == "falling" or a["posture"] != "standing":
        new_run_phase = -1                           # a fall or landing ends the run
    state.run_phase = new_run_phase
    state.run_dir = fb if new_run_phase >= 0 else 0
    return poses

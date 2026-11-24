"""Macro layer for the versus seats (docs/final/MACROS.md, task T05).

A macro is a short intent ("take that uniform", "strike that figure"). The
`MacroExecutor` expands the current macro into one primitive input per runner
decision, from this seat's observation and legal list only. The
`MacroController` is a `SeatController` (pop/seats.py): it asks a macro policy
which macro to run (the scripted baseline now, a PPO policy later) and drives
the executor between those choices.

Boundary. Nothing here imports the engine or the duel, and nothing reads
anything but the observation dict and the legal tuple. A target is chosen by
observed attributes (position, posture, motion, armed); the `kind` label that
the observation shows is only used where the policy hands it in (a visible
"rival"), never to tell a disguised rival from a guard.

Queue-ahead. The runner answers every `decision_every` ticks and a seat holds
one pending input (a newer one replaces it), so the executor plans from where
the move in progress will end (`me.motion.to`), and the input it returns
starts the frame the current move finishes: no idle frame between primitives
while the primitive is at least `decision_every` frames long (a careful step is
8, a cadence of 6). A run is 4 frames and leaves two idle frames per decision;
that is inherent to the cadence and is why blending walks, never runs.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from agents.baseline import COLS, LEAVE, RoomView, Pose

from pop.seats import WAIT

MACROS = ("BLEND", "DISGUISE", "WAIT", "FOLLOW", "STRIKE", "FLEE", "CLIMB", "SEARCH")
RESERVED = ("RIG_TRAP",)                 # traps are not built yet (T05 brief)

FRAMES = {"turn": 4, "run": 4, "step": 8, "jump": 12, "run_jump": 12, "up": 12}
WALKABLE = set("_tPr")                   # plain floor, torch, pillar, rubble: safe to step on
FOLLOW_GAP = 3                           # FOLLOW stops this many cells from its figure
DRAW_RANGE, DRAW_RANGE_DISGUISED = 5, 3  # STRIKE draws this close (a draw breaks a disguise)
MAX_DECISIONS = {"BLEND": 40, "DISGUISE": 60, "WAIT": 1, "FOLLOW": 40, "STRIKE": 80,
                 "FLEE": 30, "CLIMB": 20, "SEARCH": 80}
RETRY_AFTER = 5                          # decisions before a failed macro may be asked again
STUCK_AFTER = 5                          # decisions with no change of pose and no motion


def _facing(text: str) -> int:
    return +1 if text == "right" else -1


def _primitive(action: str) -> str:
    if action in ("LEFT", "RIGHT"):
        return "run"
    kind = action.rsplit("_", 1)[0]
    return {"STEP": "step", "JUMP": "jump", "RUN_JUMP": "run_jump", "UP": "up"}.get(kind, "step")


def plan_path(view: RoomView, start: Pose, goal, actions: tuple[str, ...], every: int,
              limit: int = 30) -> list[str] | None:
    """Cheapest action list to a pose (or outcome string) that `goal` accepts.
    The cost of an action is its frames, at least one decision long, plus the
    room model's penalty for hurting falls and sunken plates."""
    frontier = [(0, 0, start, [])]
    best = {start: 0}
    tie = 0
    while frontier:
        cost, _, pose, path = heapq.heappop(frontier)
        if goal(pose):
            return path
        if len(path) >= limit:
            continue
        for action in actions:
            result, extra = view.predict(pose, action)
            if result is None or result == "dead":
                continue
            turning = action not in ("UP",) and not action.endswith(
                "LEFT" if pose.facing < 0 else "RIGHT")
            frames = FRAMES["turn"] if turning else FRAMES[_primitive(action)]
            new = cost + max(frames, every) + 3 * extra
            if not isinstance(result, Pose):
                if goal(result):
                    tie += 1
                    heapq.heappush(frontier, (new, tie, result, path + [action]))
                continue
            if new < best.get(result, 1 << 30):
                best[result] = new
                tie += 1
                heapq.heappush(frontier, (new, tie, result, path + [action]))
    return None


ALL_ACTIONS = ("LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT", "JUMP_LEFT", "JUMP_RIGHT",
               "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT", "UP")
CAREFUL_ACTIONS = ("LEFT", "RIGHT", "STEP_LEFT", "STEP_RIGHT")   # turn-in-place and walks


class FieldView(RoomView):
    """The room model plus the figures standing in it: a body stops a walk but a
    jump flies over it and lands beyond (VERSUS_SPEC R-V22, a published rule)."""

    def __init__(self, obs: dict) -> None:
        super().__init__(obs)
        self.bodies = {(f["row"], f["col"]) for f in obs["figures"]
                       if f["posture"] not in ("downed", "dead")}

    def _move(self, p, how):
        if (p.row, p.col + p.facing) in self.bodies:
            return None, 0
        return super()._move(p, how)

    def _jump(self, p, r, c0, span):
        # Land on the last free cell of the flight; a body in the way is passed over.
        saved, self.bodies = self.bodies, set()
        try:
            res = super()._jump(p, r, c0, span)
        finally:
            self.bodies = saved
        if isinstance(res[0], Pose) and (res[0].row, res[0].col) in self.bodies:
            return None, 0
        return res


@dataclass
class Context:
    obs: dict
    legal: tuple
    view: RoomView
    me: dict
    pose: Pose                 # where this seat will be when its current move ends
    cur: Pose                  # where it is now
    moving: bool
    figures: list              # the observed figures, as given


class MacroExecutor:
    """Deterministic. `begin(macro)`, then `step(obs, legal)` once per runner decision."""

    def __init__(self, decision_every: int = 6) -> None:
        self.every = decision_every
        self.reset()

    # --- lifecycle ------------------------------------------------------------
    def reset(self) -> None:
        self.macro: str | None = None
        self.state = "idle"                  # idle | running | done | failed
        self.reason: str | None = None
        self.events: list[dict] = []
        self.suspects: list[tuple[int, int]] = []
        self.params: dict = {}
        self.decisions = 0                   # since reset (all macros)
        self.tried: set[tuple[str, int, int]] = set()   # downed cells whose uniform failed
        self.rooms: dict[str, dict] = {}     # SEARCH memory: label -> visits, last, sides
        self._room: str | None = None
        self._leaving: int | None = None
        self.substituted = 0                 # inputs replaced by WAIT because illegal now
        self._begin_state()

    def _begin_state(self) -> None:
        self.n = 0                           # decisions in this macro
        self._sig = None
        self._same = 0
        self._start_row: int | None = None
        self._start_room: str | None = None
        self._phase = "walk"                 # BLEND: walk | pause | turn
        self._waits = 0
        self._last_wait_frame = -1
        self._last_effect: str | None = None
        self._struck = False
        self._took = False

    def begin(self, macro: str, suspects=(), **params) -> None:
        self.macro, self.state, self.reason = macro, "running", None
        self.suspects = [tuple(c) for c in suspects]
        self.params = dict(params)
        self._begin_state()
        if macro in RESERVED:
            self._fail("reserved")
        elif macro not in MACROS:
            self._fail("unknown_macro")

    def _event(self, name: str) -> None:
        self.events.append({"decision": self.decisions, "event": name,
                            "macro": self.macro, "reason": self.reason})

    def _fail(self, reason: str) -> str:
        self.state, self.reason = "failed", reason
        self._event("macro_failed")
        return WAIT

    def _done(self, action: str = WAIT, reason: str | None = None) -> str:
        self.state, self.reason = "done", reason
        self._event("macro_done")
        return action

    # --- one decision -------------------------------------------------------------
    def step(self, obs: dict, legal: tuple[str, ...]) -> str:
        legal = tuple(legal)
        if self.state != "running":
            return WAIT if WAIT in legal or not legal else legal[0]
        self.decisions += 1
        self.n += 1
        ctx = self._context(obs, legal)
        self._note_room(obs)
        action = self._expand(ctx)
        return self._valid(action, ctx)

    def _valid(self, action: str, ctx: Context) -> str:
        """Re-validate against the legal list of this decision. An input that is
        legal only after the current move ends is replaced by WAIT and asked
        for again at the next decision."""
        if action in ctx.legal:
            return action
        self.substituted += 1
        if action == "UP" and "SHEATHE" in ctx.legal:      # a drawn sword turns UP into a stance
            return "SHEATHE"
        return WAIT if WAIT in ctx.legal or not ctx.legal else ctx.legal[0]

    def _context(self, obs: dict, legal: tuple) -> Context:
        me = obs["me"]
        view = FieldView(obs)
        face = _facing(me["facing"])
        loose = 0 if view.tile(me["row"], me["col"]) == "L" else -1
        cur = Pose(me["row"], me["col"], face, loose)
        m = me.get("motion")
        pose = cur
        if m is not None and m.get("to") is not None and m["to_posture"] == "standing":
            r, c = m["to"]
            pose = Pose(r, c, _facing(m["to_facing"]), 0 if view.tile(r, c) == "L" else -1)
        moving = m is not None and m["effect"] != "waited"        # a wait is idle, not a move
        return Context(obs, legal, view, me, pose, cur, moving, obs["figures"])

    def _note_room(self, obs: dict) -> None:
        label = obs["room"]
        if label != self._room:
            if self._room is not None and self._leaving is not None:
                self.rooms[self._room]["sides"][self._leaving] = label
            self._room, self._leaving = label, None
            rec = self.rooms.setdefault(label, {"visits": 0, "last": 0, "sides": {}})
            rec["visits"] += 1
        self.rooms[label]["last"] = self.decisions

    # --- dispatch -------------------------------------------------------------------
    def _expand(self, ctx: Context) -> str:
        me = ctx.me
        if me["posture"] == "falling":
            return WAIT
        if me["posture"] == "hanging" and self.macro != "CLIMB":
            return "UP"
        if self.n > MAX_DECISIONS[self.macro]:
            return self._fail("timeout")
        sig = (ctx.obs["room"], me["row"], me["col"], me["facing"], me["posture"], me["hp"],
               me["armed"], me["stance"])
        stuck_ok = self.macro in ("WAIT", "BLEND", "DISGUISE", "FOLLOW", "STRIKE")
        if sig == self._sig and not ctx.moving:
            self._same += 1
        else:
            self._same = 0
        self._sig = sig
        if self._same >= STUCK_AFTER and not (stuck_ok and self.macro != "BLEND" and self._holding):
            return self._fail("stuck")
        return getattr(self, "_do_" + self.macro.lower())(ctx)

    _holding = False                          # set by macros that wait on purpose

    # --- target helpers (observed attributes only) ------------------------------------
    def _near(self, ctx: Context, pred) -> list[dict]:
        out = [f for f in ctx.figures if pred(f)]
        out.sort(key=lambda f: (abs(f["row"] - ctx.me["row"]) * 4 + abs(f["col"] - ctx.me["col"]),
                                f["row"], f["col"]))
        return out

    def _suspected(self, ctx: Context) -> dict | None:
        """The nearest figure standing where a suspect was last seen, else the
        nearest figure the observation labels a rival."""
        for cell in self.suspects:
            hits = self._near(ctx, lambda f, c=cell: abs(f["row"] - c[0]) <= 1
                              and abs(f["col"] - c[1]) <= 2
                              and f["posture"] not in ("downed", "dead"))
            hits.sort(key=lambda f: (abs(f["row"] - cell[0]) + abs(f["col"] - cell[1]),
                                     f["row"], f["col"]))
            if hits:
                self.suspects = [(hits[0]["row"], hits[0]["col"])]
                return hits[0]
        rivals = self._near(ctx, lambda f: f["kind"] == "rival"
                            and f["posture"] not in ("downed", "dead"))
        return rivals[0] if rivals else None

    def _actions(self, ctx: Context, careful: bool) -> tuple[str, ...]:
        if careful:
            return CAREFUL_ACTIONS
        acts = ALL_ACTIONS
        return acts if not ctx.me["armed"] else acts[:-1]       # UP is a stance change when drawn

    def _go(self, ctx: Context, goal, careful: bool = False) -> str | None:
        """First action toward the goal from where the current move ends, or None."""
        path = plan_path(ctx.view, ctx.pose, goal, self._actions(ctx, careful), self.every)
        if path is None:
            return None
        return path[0] if path else WAIT      # already there: hold until the move ends

    # --- macros -------------------------------------------------------------------------
    def _do_wait(self, ctx: Context) -> str:
        return self._done(WAIT)

    def _do_disguise(self, ctx: Context) -> str:
        me = ctx.me
        if me["disguised"]:
            return self._done(WAIT)
        if me["motion"] and me["motion"]["effect"] == "took_uniform":
            return WAIT                                         # the take is in progress
        room = ctx.obs["room"]
        bodies = self._near(ctx, lambda f: f["posture"] == "downed"
                            and (room, f["row"], f["col"]) not in self.tried)
        if not bodies:
            return self._fail("no_target")
        t = bodies[0]
        at = (ctx.pose.row == t["row"]
              and ctx.pose.col in (t["col"], t["col"] - ctx.pose.facing)
              and ctx.pose.col + ctx.pose.facing in (t["col"], t["col"] + 0) or
              (ctx.pose.row == t["row"] and ctx.pose.col == t["col"]))
        if at:
            if self._took and not ctx.moving and not (me["motion"] and me["motion"]["effect"] == "took_uniform"):
                self.tried.add((room, t["row"], t["col"]))      # taken, yet no disguise: stripped already
                return self._fail("no_uniform")
            if not ctx.moving and "TAKE" not in ctx.legal:
                self.tried.add((room, t["row"], t["col"]))
                return self._fail("no_uniform")
            self._holding = True
            if "TAKE" in ctx.legal and not (me["motion"] and me["motion"]["effect"] == "took_uniform"):
                self._took = True
                return "TAKE"
            return WAIT
        self._holding = False
        a = self._go(ctx, lambda p, t=t: isinstance(p, Pose) and p.row == t["row"]
                     and (p.col == t["col"] or p.col + p.facing == t["col"]))
        return a if a else self._fail("unreachable")

    def _do_follow(self, ctx: Context) -> str:
        t = self._suspected(ctx)
        if t is None:
            return self._fail("no_target")
        me = ctx.me
        if t["row"] == me["row"] and abs(t["col"] - me["col"]) <= FOLLOW_GAP:
            self._holding = True
            face = +1 if t["col"] > me["col"] else -1
            if _facing(me["facing"]) != face and not ctx.moving:
                return "RIGHT" if face > 0 else "LEFT"          # face it (a turn)
            return self._done(WAIT, "in_range")
        d = (lambda p, t=t: isinstance(p, Pose) and p.row == t["row"]
             and abs(p.col - t["col"]) <= FOLLOW_GAP and p.col - t["col"] != 0)
        a = self._go(ctx, d)
        return a if a else self._fail("unreachable")

    def _do_strike(self, ctx: Context) -> str:
        t = self._suspected(ctx)
        me = ctx.me
        if t is None:
            return self._done(WAIT, "target_gone") if self._struck else self._fail("no_target")
        face_me = _facing(me["facing"])
        same_row = t["row"] == me["row"]
        dist = abs(t["col"] - me["col"])
        want = +1 if t["col"] > me["col"] else -1
        adjacent = same_row and dist == 1 and face_me == want and not ctx.moving
        near = same_row and dist <= (DRAW_RANGE_DISGUISED if me["disguised"] else DRAW_RANGE)
        if not me["armed"] and "DRAW" in ctx.legal and near and not ctx.moving:
            return "DRAW"
        if adjacent:
            return self._attack(ctx, t)
        if (same_row and dist == 1 and not ctx.moving
                and me["armed"] and face_me != want):
            return "RIGHT" if want > 0 else "LEFT"              # turn to face it
        a = self._go(ctx, lambda p, t=t: isinstance(p, Pose) and p.row == t["row"]
                     and p.col + p.facing == t["col"])
        return a if a else self._fail("unreachable")

    def _attack(self, ctx: Context, t: dict) -> str:
        me = ctx.me
        self._struck = True
        facing_me = _facing(t["facing"]) == -_facing(me["facing"])
        if t["posture"] == "knocked_down" or not t["armed"] or not facing_me:
            return "LUNGE" if "LUNGE" in ctx.legal else "DRAW"
        if me["armed"] and t["stance"] != "low" and "SWEEP" in ctx.legal:
            return "SWEEP"                                      # a block cannot stop a sweep
        # Armed and facing me with a low guard: strike at a different height.
        if me["stance"] == t["stance"]:
            return "STANCE_UP" if "STANCE_UP" in ctx.legal and t["stance"] != "high" \
                else ("STANCE_DOWN" if "STANCE_DOWN" in ctx.legal else WAIT)
        return "LUNGE" if "LUNGE" in ctx.legal else "DRAW"

    def _do_flee(self, ctx: Context) -> str:
        me = ctx.me
        if self._start_room is None:
            self._start_room = ctx.obs["room"]
        if ctx.obs["room"] != self._start_room:
            return self._done(WAIT, "left_room")
        threats = self._near(ctx, lambda f: f["posture"] not in ("downed", "dead")
                             and (f["kind"] == "rival" or f["armed"]))
        if not threats and not self.suspects:
            return self._done(WAIT, "clear")
        origin = threats[0]["col"] if threats else self.suspects[0][1]
        away = -1 if origin >= me["col"] else +1
        for side in (away, -away):
            if ctx.view.edges[side]:
                a = self._go(ctx, lambda p, s=side: p == LEAVE[s])
                if a:
                    self._leaving = side
                    return a
        a = self._go(ctx, lambda p: isinstance(p, Pose) and abs(p.col - origin) >= 6)
        return a if a else self._fail("cornered")

    def _do_climb(self, ctx: Context) -> str:
        me = ctx.me
        if self._start_row is None:
            self._start_row = me["row"]
        if me["row"] < self._start_row or (me["posture"] == "hanging" and False):
            return self._done(WAIT, "climbed")
        if me["posture"] == "hanging":
            return "UP"
        row = self._start_row
        a = self._go(ctx, lambda p: isinstance(p, Pose) and p.row < row)
        return a if a else self._fail("no_climb")

    def _do_search(self, ctx: Context) -> str:
        """Leave by the edge toward the room seen least recently (never-seen first)."""
        careful = bool(ctx.me["disguised"])
        label = ctx.obs["room"]
        if self._start_room is None:
            self._start_room = label
        if label != self._start_room:
            return self._done(WAIT, "new_room")
        sides = [s for s in (+1, -1) if ctx.view.edges[s]]
        if "side" in self.params and self.params["side"] in sides:
            sides = [self.params["side"]]
        rec = self.rooms[label]

        def age(side):
            nb = rec["sides"].get(side)
            return -1 if nb is None else self.rooms[nb]["last"]
        sides.sort(key=lambda s: (age(s), 0 if s == self.params.get("keep", +1) else 1, -s))
        for side in sides:
            # Walk when disguised; leap only if walking cannot get there (a leap in a
            # guard's sight raises suspicion, one out of sight costs nothing).
            a = (self._go(ctx, lambda p, s=side: p == LEAVE[s], careful)
                 or (careful and self._go(ctx, lambda p, s=side: p == LEAVE[s])))
            if a:
                self._leaving = side
                return a
        return self._fail("no_edge")

    def _do_blend(self, ctx: Context) -> str:
        """Walk like a patrolling guard: careful steps along the floor, a pause of
        about 12 frames at the end of the stretch, a turn, and one leg is done."""
        me, v, pose = ctx.me, ctx.view, ctx.pose
        m = me["motion"]
        effect = m["effect"] if m else None
        if self._phase == "walk":
            ahead = (pose.row, pose.col + pose.facing)
            ok = (0 <= ahead[1] < COLS and v.tile(*ahead) in WALKABLE
                  and ahead not in v.barring and v.supported(*ahead))
            if ok:
                return "STEP_RIGHT" if pose.facing > 0 else "STEP_LEFT"
            self._phase, self._waits, self._last_effect = "pause", 0, None
        if self._phase == "pause":
            if effect == "waited":                              # count each distinct wait
                if self._last_effect != "waited" or m["frame"] <= self._last_wait_frame:
                    self._waits += 1
                self._last_wait_frame = m["frame"]
            self._last_effect = effect
            if self._waits < 2:
                return WAIT
            self._phase = "turn"
        if self._phase == "turn":
            if effect == "turned":
                return self._done(WAIT, "leg_done")
            return "LEFT" if pose.facing > 0 else "RIGHT"       # a reversal is a turn only
        return WAIT


class MacroController:
    """A SeatController (pop/seats.py) that runs a macro policy and an executor.

    `policy.choose(obs, legal, status)` returns a macro name or `(macro, params)`;
    `params` may carry `suspects` (cells) and any executor parameter. It is asked
    every `macro_every` runner decisions, and at once whenever the executor is no
    longer running. `status` is what the executor reports about the last macro:
    `{"macro", "state", "reason"}`. `log` has one row per decision; `events` the
    macro_done / macro_failed notices."""

    def __init__(self, policy, name: str = "macro", kind: str = "scripted",
                 decision_every: int = 6, macro_every: int = 1) -> None:
        self.policy = policy
        self.name, self.kind = name, kind
        self.macro_every = macro_every
        self.executor = MacroExecutor(decision_every)
        self.log: list[dict] = []
        self._calls = 0
        self._failed_at = -RETRY_AFTER

    @property
    def events(self) -> list[dict]:
        return self.executor.events

    def reset(self, seed: int) -> None:
        self.executor.reset()
        self.log = []
        self._calls = 0
        self._failed_at = -RETRY_AFTER
        if hasattr(self.policy, "reset"):
            self.policy.reset(seed)

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        ex = self.executor
        asked = (self._calls % self.macro_every == 0) or ex.state != "running"
        self._calls += 1
        if asked:
            status = {"macro": ex.macro, "state": ex.state, "reason": ex.reason}
            choice = self.policy.choose(observation, legal, status)
            macro, params = (choice, {}) if isinstance(choice, str) else choice
            suspects = params.get("suspects", ())
            rest = {k: v for k, v in params.items() if k != "suspects"}
            if ex.state == "running" and macro == ex.macro:
                ex.suspects = [tuple(c) for c in suspects]   # keep going, new suspects
            elif (ex.state == "failed" and macro == ex.macro
                  and (ex.reason in ("reserved", "unknown_macro")
                       or self._calls - self._failed_at < RETRY_AFTER)):
                pass                      # reported once; asking again at once would loop
            else:
                ex.begin(macro, suspects, **rest)
                if ex.state == "failed":
                    self._failed_at = self._calls
        was = ex.state
        action = ex.step(observation, legal)
        if was == "running" and ex.state == "failed":
            self._failed_at = self._calls
        self.log.append({"macro": ex.macro, "state": ex.state, "reason": ex.reason,
                         "input": action})
        return action

"""LLM player: one model call per action, JSON reply {"action", "reason"}.

Inputs per call (nothing else): the current observation, the legal-action
list, and, in the `history` variant, the player's own bounded memory built
from earlier observations: its last 8 steps and the rooms it has seen.
The `obs-only` variant gets the current observation and legal actions only.

The system prompt is the same for every situation. It states the published
rules (docs/GAME_SPEC.md §4-5) and the tile legend; it never names a
situation, a layout, a plate link, or a route.
"""

from __future__ import annotations

import json
import re
import threading

from pop.runner import Decision
from pop.tiles import LEGEND

from .providers import classify_error, estimate_cost

HISTORY_STEPS = 8

SYSTEM_PROMPT = """You control the prince in a side-view dungeon platformer (a reconstruction of Prince of Persia, 1989).
Goal: escape. Reach an OPEN exit door and press UP while standing on one of its two tiles.

The screen shows one room: 3 rows (row 0 top) x 10 columns (col 0 left). You see only the current room.
Moving off the left/right side leads to the neighbouring room only if that edge is open ("edges").
A missing edge is a wall. Falling below row 2 into an unseen pit may kill you.

Tiles:
{legend}
A cell holds you up if its tile has a floor, or if the cell directly below it is a wall.

Actions (each takes up to 1 second of game time). A direction you are not facing only TURNS you (no move).
- WAIT: do nothing for half a second (timers keep running).
- LEFT / RIGHT: run one block. Running onto spikes kills. Running onto a cell with no floor makes you fall.
- STEP_LEFT / STEP_RIGHT: careful step one block. Never walks off an edge, never triggers death by spikes.
- JUMP_LEFT / JUMP_RIGHT: standing jump, lands exactly 3 blocks ahead (stops early before a wall or closed gate).
- RUN_JUMP_LEFT / RUN_JUMP_RIGHT: run one block, then jump; lands 5 blocks ahead of where you started
  (clears a gap of up to 3). Needs a floor 1 block ahead, otherwise it is just a run.
- UP: on an open exit -> climb the stairs and win. If hanging -> climb back up. If the cell above you is
  empty air and the cell above-ahead has a floor -> climb up onto it. Otherwise a small hop.
- DOWN: if hanging -> let go. On a potion -> drink it (+1 HP). If the cell ahead has no floor -> climb down
  and hang from the ledge. Otherwise crouch.
Landing on spikes from a jump or a fall kills. Falls: 1 row is safe, 2 rows cost 1 HP, 3+ rows kill
(dropping from a hang counts one row less). HP 0 = death.
Loose floor (L): about 1 second after you step on it, it falls away. Keep moving.
Raised plate (u): stepping on it opens something (a gate or the exit), maybe in another room.
Sunken plate (p): stepping on it slams a gate shut. Gates (G) block you while "bars" is true; an opened gate
stays open a few seconds and then slowly closes. An exit door must be fully open ("open": true) to use.

Reply with ONLY a JSON object, no other text:
{{"action": "<one of the legal actions>", "reason": "<at most 15 words>"}}"""


def build_system_prompt() -> str:
    legend = "\n".join(f"  {sym}  {text}" for sym, text in LEGEND.items())
    return SYSTEM_PROMPT.format(legend=legend)


def render_room(tiles: list[str], kid: dict | None = None) -> str:
    rows = [list(r) for r in tiles]
    if kid is not None:
        rows[kid["row"]][kid["col"]] = ">" if kid["facing"] == "right" else "<"
    header = "     " + "".join(str(c) for c in range(10))
    return "\n".join([header] + [f"row {i} {''.join(r)}" for i, r in enumerate(rows)])


def _parse(text: str) -> str | None:
    """Return the action string from a JSON reply, or None if unparseable."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    action = data.get("action") if isinstance(data, dict) else None
    return action if isinstance(action, str) else None


class ModelPlayer:
    """Memory is written only by commit(), which the runner calls in its own
    thread after each step. decide() reads a snapshot and writes nothing, so a
    reply that arrives after the runner's timeout cannot change what the
    player remembers (audit F-1, 2026-10-26)."""

    source = "model"
    uses_model = True

    def __init__(self, provider, variant: str = "history"):
        if variant not in ("history", "obs-only"):
            raise ValueError(variant)
        self.provider = provider
        self.variant = variant
        self.name = f"model-{variant}"
        self.system = build_system_prompt()
        self.steps: list[dict] = []           # own past steps (bounded when shown)
        self.seen: dict[str, dict] = {}       # room label -> last view of that room
        self._pending: str | None = None      # last submitted action, awaiting its result
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def _memory_after(self, obs: dict) -> tuple[list[dict], dict[str, dict]]:
        """Copies of (steps, seen) as they will be once `obs` is committed."""
        with self._lock:
            steps = list(self.steps)
            seen = dict(self.seen)
            pending = self._pending
        if pending is not None:
            k = obs["kid"]
            steps.append({"action": pending, "result": obs["last_result"],
                          "room": obs["room"], "row": k["row"], "col": k["col"],
                          "facing": k["facing"]})
        seen[obs["room"]] = {"tiles": list(obs["tiles"]), "edges": dict(obs["edges"])}
        return steps, seen

    def commit(self, observation: dict, action: str, source: str, error: str | None) -> None:
        """Runner hook: record what was actually submitted for `observation`."""
        steps, seen = self._memory_after(observation)
        if source == "fallback":
            label = "WAIT (fallback)" if error == "unparseable reply" else "WAIT (failed call)"
        else:
            label = action
        with self._lock:
            self.steps, self.seen, self._pending = steps, seen, label

    def build_user_prompt(self, obs: dict, legal: list[str],
                          steps: list[dict] | None = None,
                          seen: dict[str, dict] | None = None) -> str:
        if steps is None or seen is None:
            steps, seen = self._memory_after(obs)
        kid = obs["kid"]
        parts = []
        if self.variant == "history":
            others = {k: v for k, v in seen.items() if k != obs["room"]}
            if others:
                parts.append("Rooms you have seen before (as you last saw them):")
                for label, view in others.items():
                    parts.append(f"{label} (edges {view['edges']})\n{render_room(view['tiles'])}")
            if steps:
                parts.append(f"Your last {min(HISTORY_STEPS, len(steps))} actions "
                             "(oldest first):")
                for s in steps[-HISTORY_STEPS:]:
                    parts.append(f"- {s['action']} -> {s['result']}; then in {s['room']} "
                                 f"row {s['row']} col {s['col']} facing {s['facing']}")
        parts.append(f"Current room: {obs['room']}  edges: {json.dumps(obs['edges'])}")
        parts.append(render_room(obs["tiles"], kid) + "\n(> or < marks you and your facing)")
        parts.append("Visible state: " + json.dumps(obs["state"]))
        parts.append(f"You: row {kid['row']} col {kid['col']} facing {kid['facing']}, "
                     f"{kid['posture']}, HP {kid['hp']}/{kid['max_hp']}")
        parts.append(f"Last action result: {json.dumps(obs['last_result'])}")
        parts.append(f"Minutes left: {obs['minutes_left']}. Actions left: {obs['actions_left']}. "
                     f"Model calls left: {obs.get('calls_left')}.")
        parts.append(f"Task: {obs['task']}")
        parts.append("Legal actions now: " + ", ".join(legal))
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    def decide(self, observation: dict, legal_actions: list[str]) -> Decision:
        user = self.build_user_prompt(observation, legal_actions)
        try:
            c = self.provider.complete(self.system, user)
        except Exception as exc:
            try:
                exc.error_kind = classify_error(exc)   # read by the runner (R-D25)
            except AttributeError:
                pass
            raise
        action = _parse(c.text)
        cost = estimate_cost(c.model, c.tokens_in, c.tokens_out)
        meta = {"provider": self.provider.name, "model": c.model, "variant": self.variant,
                "tokens_in": c.tokens_in, "tokens_out": c.tokens_out,
                "cost_usd": cost,                  # None = price unknown, never 0 (audit F-2)
                "cost_known": cost is not None,
                "request_id": c.request_id, "raw": c.text, "parsed_action": action}
        if action is None:
            return Decision(None, meta, fallback_reason="unparseable reply",
                            error_kind="unparseable_reply")
        return Decision(action, meta)

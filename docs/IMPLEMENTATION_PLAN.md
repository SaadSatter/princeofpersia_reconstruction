# Implementation Plan

Approved by the student on 2026-10-26 with these decisions: Level 1 only;
authored layouts (no committed original data); 15-action vocabulary
provisionally approved, combat actions deferred; Claude Haiku 4.5 as the
initial live model; Gap/Trap/Escape suite plus three held-out variations
(frozen in `docs/EVALUATION_SUITE.md`).

## Order of work (checkpoint priority)

| # | Item | Stop point |
| --- | --- | --- |
| 1 | Headless deterministic engine (`pop/`) | |
| 2 | Five-operation interface (`pop/interface.py`) | |
| 3 | Episode limits and action validation (`pop/runner.py`) | |
| 4 | Playable bounded escape scenario (S3) + scripted solutions in tests | **Stop and report to the student** |
| 5 | Baseline that completes an episode (`agents/baseline.py`) | |
| 6 | Model player + one genuine live episode (`agents/model_player.py`) | |
| 7 | First comparison table (`evaluate.py`, `EVALUATION.md`) | |
| 8 | Deterministic tests and green CI (dev workflow + `ci/midterm-saadsatter.yml`) | |
| 9 | Minimal keyboard Pygame frontend (`play.py`) — required for the finished game | |

Tests run after each component. Small commits, one component each.

## Five-operation interface

```python
class Episode:
    def __init__(self, situation_id: str): ...
    def reset(self, seed: int) -> dict            # initial observation
    def observe(self, player_id: str) -> dict     # GAME_SPEC §8 only
    def legal_actions(self, player_id: str) -> list[str]   # posture only
    def step(self, player_id: str, action: object) -> dict
    def outcome(self) -> dict
```

`step` returns `{accepted, effect, frames, observation}`; an invalid action
returns `{accepted: False, error, frames: 0, observation}` and changes
nothing. `outcome` returns `{status, reason, score, actions,
invalid_actions, frames}`.

The runner (`pop/runner.py`) owns the `Episode`. A player is any object with
`decide(observation, legal_actions) -> str` and a `uses_model` flag. The
runner passes **copies** of the observation and legal list, times each
decision (thread + timeout), counts model calls (failures included),
substitutes a `WAIT` labeled `fallback` on timeout or error, submits the
action through `step`, and stops on any terminal reason.

## After the stop point

- Baseline: cautious explorer from the earlier plan, same observations,
  own memory of seen rooms (disclosed), no layout access.
- Model player: Anthropic adapter first (`ANTHROPIC_API_KEY`, `POP_MODEL`,
  default Claude Haiku 4.5), configurable provider; JSON reply
  `{"action", "reason"}`; logs raw response, latency, tokens, dated cost,
  fallback flag. Variants `history` and `obs-only`.
- Live trials are run only by the student's explicit command.

## Transfer to the course repository

Unchanged from the earlier plan: copy this tree into
`game-dev-f26/midterms/saadsatter/`, copy `ci/midterm-saadsatter.yml` to
`.github/workflows/midterm-saadsatter.yml` (paths filter on the folder,
`working-directory: midterms/saadsatter`, no secrets), re-run the
fresh-clone check, open one PR. Start project sessions with the working
directory `midterms/saadsatter/` because the course repo has its own root
`.claude/agents/rules-reviewer.md`.

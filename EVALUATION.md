# Evaluation — preliminary (2026-10-26)

**Status: preliminary.** Baseline results are real. **One live model
episode has been run, on the tuning suite only** (S1, seed 0, 2026-10-26
18:01 UTC; see "Live tuning episode" below). It is a single development
trial, not a final-suite result, so the final-suite model rows below are
still empty. An earlier live attempt (16:26 UTC) failed before reaching the
API and is recorded separately as a failed attempt. This file will be updated with
live results, and the limitations paragraph must be written by the student.

## Declared suite

- `docs/EVALUATION_SUITE.md`, frozen in commit `8295fc0`
  (2026-10-26 01:15 EDT). `git log -- docs/EVALUATION_SUITE.md` shows no
  later change. The baseline (`12d606f`, 01:59 EDT) and the model prompt
  (`42c9fb8`, 02:02 EDT) were written after the freeze.
- Tuning cases: S1–S3, seeds 0, 1. Held-out cases: H1–H3 (final seeds only).
  H1–H3 were run for the first time in the final baseline run below, after
  the baseline was committed; the baseline was not changed afterwards. They
  have not been shown to any model.
- Final seeds: 100, 101. **No implemented mechanic uses randomness**, so
  the seed does not change the episode. The baseline is deterministic, so
  its two trials per situation are identical; repeated model trials measure
  only the model's own variability.

## Players and configuration

Both players go through the same runner (`pop/runner.py:run_episode`) and the
same limits: the situation's action limit and call limit (S1/H1 40, S2/H2 50,
S3/H3 80), a 20 s per-decision timeout, 5 consecutive invalid actions.
Both receive a copy of the same observation and the same legal-action list.

| Player | What it is | Memory | Notes |
| --- | --- | --- | --- |
| `baseline-explorer` (`agents/baseline.py`) | Cautious explorer. Plans inside the visible room with Dijkstra over its own hand-coded model of the published rules (GAME_SPEC §4–5); never picks a predicted death; avoids 2-row falls and sunken plates; presses raise plates when a closed gate or exit blocks it; goes back for a plate if a gate stays shut. | Rooms seen (by opaque label), plates pressed, edges left by. | Asymmetry to disclose: its rules knowledge is code and its per-decision compute is unbounded (≈0.2 ms mean). It makes no model calls. |
| `model-history` (`agents/model_player.py`) | One Claude call per action; JSON reply `{"action", "reason"}`. | Its last 8 steps plus the last view of each room it has seen, built from its own observations. | Not run yet. |
| `model-obs-only` | Same, without history (S1–S3 only, per the suite). | None. | Not run yet. |

Model configuration: provider `anthropic`, model `claude-haiku-4-5` (or
`$POP_MODEL`); `max_tokens` 400; no sampling parameters; SDK retries
disabled (every request is one counted call); SDK timeout 15 s inside the
runner's 20 s. Same system prompt for every situation. A reply with no
parseable action becomes `WAIT` labeled `"source": "fallback"` and
counts as a failed call (R-D22); a parseable but illegal action is submitted
and counted as invalid. A reply that arrives after the 20 s timeout is
discarded (it changes neither the episode, the steps nor the player's
memory); its tokens and cost are logged under `late_replies` (R-D23).
Price used for estimates: $1.00 / $5.00 per million input / output tokens
for Claude Haiku 4.5, verified on 2026-10-26 against
https://platform.claude.com/docs/en/about-claude/pricing
(`agents/providers.py:PRICE_DATE`, `PRICE_SOURCE`). A model without a known
price is reported as cost "unknown", never $0 (R-D24).

## Results

Run `20261026T060347Z` (UTC), game version `0.1.0+3c4c210`, command (project folder):
`uv run python evaluate.py --suite final --players baseline --out traces/eval`.

| Player | Situation | Trials (seeds) | Wins | Terminal reasons | Mean actions | Invalid | Calls | Failed calls | Fallbacks | Latency mean / max (ms) | Tokens in / out | Est. cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-explorer | H1 | 2 (100, 101) | 2/2 | won 2 | 9.0 | 0 | 0 | 0 | 0 | 0.2 / 0.4 | 0 / 0 | 0.0000 |
| baseline-explorer | H2 | 2 (100, 101) | 2/2 | won 2 | 11.0 | 0 | 0 | 0 | 0 | 0.2 / 0.4 | 0 / 0 | 0.0000 |
| baseline-explorer | H3 | 2 (100, 101) | 2/2 | won 2 | 26.0 | 0 | 0 | 0 | 0 | 0.2 / 0.6 | 0 / 0 | 0.0000 |
| baseline-explorer | S1 | 2 (100, 101) | 2/2 | won 2 | 8.0 | 0 | 0 | 0 | 0 | 0.3 / 0.6 | 0 / 0 | 0.0000 |
| baseline-explorer | S2 | 2 (100, 101) | 2/2 | won 2 | 13.0 | 0 | 0 | 0 | 0 | 0.3 / 0.5 | 0 / 0 | 0.0000 |
| baseline-explorer | S3 | 2 (100, 101) | 2/2 | won 2 | 28.0 | 0 | 0 | 0 | 0 | 0.2 / 0.5 | 0 / 0 | 0.0000 |
| model-history | S1–S3, H1–H3 | 0 | — | **not run** | — | — | — | — | — | — | — | — |
| model-obs-only | S1–S3 | 0 | — | **not run** | — | — | — | — | — | — | — | — |

### Live tuning episode: model-history, S1, seed 0

Run `20261026T180142Z`, game version `0.1.0+c23ebf7`, model returned
`claude-haiku-4-5-20251001`, provider `anthropic`, price dated 2026-10-26.
Command (project folder):
`uv run python evaluate.py --suite tuning --players model-history --situations S1 --seeds 0 --live --out traces/live`.

| Player | Situation | Trials (seeds) | Wins | Terminal reasons | Mean actions | Invalid | Calls | Failed calls | Fallbacks | Latency mean / max (ms) | Tokens in / out | Est. cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| model-history | S1 | 1 (0) | 0/1 | died:spikes 1 | 4.0 | 0 | 4 | 0 | 0 | 3010.4 / 3526.4 | 4485 / 940 | 0.0092 |

What the trace shows: the model chose `RIGHT` four times, and all four were
accepted as model decisions (no fallback, no late reply). The fourth run
took the prince off the floor at row 1, col 4 into the gap at col 5, and he
fell onto the spikes below (`died:spikes`, 20 frames). In its last reply the
model named the spikes at row 2, col 5 and said it would avoid them, then
chose `RIGHT` again. Each reply was a paragraph of analysis followed by the
JSON object, although the prompt asks for JSON only. The parser found the
action every time, and the analysis accounts for most of the 940 output
tokens. One trial on one tuning situation: this shows that the model player
works end to end, not how well it plays.

### Failed live attempt (not a model result)

Run `20261026T162629Z`, game version `0.1.0+b2a6e2a`, command (project folder):
`uv run python evaluate.py --suite tuning --players model-history --situations S1 --seeds 0 --live --out traces/live`.

| Field | Recorded value |
| --- | --- |
| Actions / outcome | 40, `step_limit` (score 0) |
| Model calls / failed / fallbacks | 40 / 40 / 40, every action a `WAIT` labeled `source: "fallback"` |
| Error on all 40 steps | `TypeError: "Could not resolve authentication method. Expected one of api_key, auth_token, or credentials to be set. ..."` (raised by the `anthropic` SDK 0.125.0) |
| Tokens in / out, cost | 0 / 0, $0 (no request was sent) |
| Latency mean / max | 0.6 / 2.8 ms (no network round trip) |
| Model ids returned | none |

**Cause.** The SDK raises this error when `ANTHROPIC_API_KEY` is unset or
empty in the Python process. It still builds the client and fails inside
each request, before anything is sent (reproduced offline:
`tests/test_provider_sdk.py::test_sdk_no_key_error_is_classified_and_the_adapter_now_stops_first`).
The trace cannot show whether the key was unset or empty. The runner then
treated each failure as an ordinary failed call. **Fix (R-D25):** a live run
now checks the credential before the first episode and stops with exit code 2
and no trace. Failed calls also carry an `error_kind`, here `auth_missing`.
This attempt says nothing about the model's play. It is kept as a record of
a setup failure.

For reference, the hand-written test routes (`tests/solutions.py`, never
shown to a player) use 12 / 16 / 38 / 11 / 16 / 44 actions for S1 / S2 / S3 /
H1 / H2 / H3; the baseline found shorter routes in all six.

**Reading this result.** The baseline wins 12/12 with no invalid actions.
On this suite the model player can at best match it on outcome. If both
players win consistently, this suite cannot distinguish them by win rate;
the comparison then rests on actions used, invalid actions, fallbacks,
limits hit, latency and cost. Student decision (2026-10-26): keep these
results and do not weaken the baseline (audit note N1).

## Traces

- Baseline, final suite: `traces/eval/20261026T060347Z-baseline-<situation>-<seed>.jsonl`
  (12 files), `traces/eval/20261026T060347Z-results.json`,
  `traces/eval/20261026T060347Z-table.md`.
- Scripted route (not a player): `traces/dev/S3-scripted-route-100.jsonl`.
- Live tuning episode (model-history, S1, seed 0):
  `traces/live/20261026T180142Z-model-history-S1-0.jsonl`, `-results.json`,
  `-table.md`. Final-suite model traces: none yet.
- Failed live attempt (40 provider failures, no gameplay):
  `traces/live/20261026T162629Z-model-history-S1-0.jsonl`, `-results.json`,
  `-table.md`, written before the R-D25 fix, so they have no `error_kind`
  field. See `traces/live/README.md`.

Each trace is JSONL: one `episode` header (situation, seed, player, game
version, outcome and reason, calls, failed calls, fallbacks, usage, latency,
limits, `failed_call_kinds`), then one `step` line per action (action, source, accepted, error,
`error_kind` for failed calls, effect, frames, latency, model metadata including raw reply and parsed action).

## How to run a live model episode

From the project folder, with an Anthropic API key in the environment:

```
uv sync --extra model
export ANTHROPIC_API_KEY=...            # never commit it; type it, don't paste it with other lines
uv run python tools/smoke_provider.py --check-only                # no network
uv run python tools/smoke_provider.py --live --out traces/live    # exactly one tiny paid call
uv run python evaluate.py --suite tuning --players model-history --situations S1 --seeds 0 --live --out traces/live
```

`evaluate.py --live` stops before any episode if the key is unset, empty, or
padded with whitespace.

The final model trials are:

```
uv run python evaluate.py --suite final --players model-history,model-obs-only --live --out traces/eval
```

## CI evidence

- Development workflow `.github/workflows/ci.yml` (personal repo, Python
  3.11 and 3.12): green on `00f6a85`, 111 passed and 1 skipped (the
  offline SDK test, which needs the `model` extra), run
  https://github.com/SaadSatter/princeofpersia_reconstruction/actions/runs/40279874123.
  Earlier: green on `e91e9b0`, 108 tests, run 40277726045.
  This is **not** the course check 3c.
- Course workflow `ci/midterm-saadsatter.yml`: not yet run in
  `game-dev-f26`. Checked statically by `tests/test_ci_workflow.py`; its
  commands were rehearsed locally on a clean copy placed at
  `midterms/saadsatter/` (108 passed).

## Limitations

*To be written by the student.* Facts to consider: only one live model
episode so far (tuning S1, died on spikes after 4 actions); one earlier
attempt failed on a missing or empty API key (40/40 calls);
seeds do not vary episodes; the baseline wins every case (ceiling effect);
the baseline's rules model is hand-coded; six small authored situations, two
trials each; cost price not re-verified on a run day; no peer playtest yet.

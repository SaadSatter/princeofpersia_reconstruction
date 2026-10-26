# Prince of Persia mechanics reconstruction

A bounded, authored-room reconstruction inspired by Prince of Persia (1989),
by Jordan Mechner / Broderbund. This audit uses the current headless engine,
not authentic Level 1 or combat. No artwork or graphics installation is needed.
See [scope](docs/GAME_SPEC.md), [rule/source map](docs/RULE_SOURCE_MAP.md),
[source and artwork terms](docs/ASSET_PROVENANCE.md),
[frozen evaluation suite](docs/EVALUATION_SUITE.md), [evaluation](EVALUATION.md),
and [agent team](AGENT-TEAM.md). Original artwork is not licensed by the source
code license; see the provenance document for the stated terms and attribution.

## Week 7 Pair Audit — 8-Minute Quickstart

**Owner remains silent. Auditor copies the blocks in order.** Use macOS/Linux
bash or zsh. Prerequisites: Git, Python 3.11 or 3.12, `uv` on PATH, network
access to GitHub/PyPI/Anthropic, authorized course-repository access, and an
Anthropic API key with API credits (a chat subscription is insufficient).
Install Git/Python/uv before the timed audit. No Pygame, original artwork,
manual Python edits, or GitHub CLI is required. Installation time depends on
network speed; prepare the environment before the eight-minute timer.

**Directory:** start in the parent directory where you want a new course clone.
Use a new destination name if `game-dev-f26-pair-audit` already exists.

```sh
git clone --single-branch --branch saadsatter/midterm https://github.com/columbia-university-ai-games/game-dev-f26.git game-dev-f26-pair-audit
cd game-dev-f26-pair-audit/midterms/saadsatter
export UV_CACHE_DIR="${TMPDIR:-/tmp}/pop-pair-audit-uv"
uv sync --frozen --extra model --python 3.12
```

**Every remaining shell block runs from `midterms/saadsatter/`**, including CI
commands. In the personal development clone, use its repository root instead.
Expected: dependency installation succeeds, including `anthropic` and `pytest`.

Before the timer, load the key in this same shell. This prompt hides typing,
does not put the key in shell history, and never prints its value:

```sh
set +x
export ANTHROPIC_API_KEY="$(uv run --frozen python -c 'import getpass; print(getpass.getpass("Anthropic API key (hidden): "))')"
uv run --frozen python -c 'from agents.providers import check_credentials; check_credentials("anthropic"); print("Credential present; value not displayed (not an authentication test)")'
```

Do not paste credentials into chat, source files, recordings, or the README.
Do not run `env`, `printenv`, or shell tracing during the audit.

### Minutes 0–3: five operations on S1, seed 0

S1 is a declared tuning scenario; the room layout and rules are unchanged.
This single process keeps state between commands. Copy the entire block:

```sh
uv run --frozen python audit.py --scenario S1 <<'AUDIT'
reset 0
observe
legal_actions
step NOT_AN_ACTION
step RIGHT
outcome
step RIGHT
step JUMP_RIGHT
step RIGHT
step RIGHT
step RIGHT
step RIGHT
step RIGHT
step RIGHT
step RUN_JUMP_RIGHT
step RIGHT
step UP
outcome
quit
AUDIT
```

Expected JSON, in order:

- `reset`: initial observation; `observe`: current room tiles, kid/HUD and
  visible mechanisms only. No other rooms, answer key, or engine internals.
- `legal_actions`: list containing `RIGHT`, `WAIT`, and other current actions.
- Illegal action: `accepted: false`, `error: "unknown action"`,
  `observation_unchanged: true`, `frames_unchanged: true`.
  World state, action count, and time do not advance. **The existing interface
  does increment its invalid-action counter**; five consecutive refusals end
  the episode. “Unchanged” means game state, not refusal bookkeeping.
- First `RIGHT`: `accepted: true`; intermediate outcome `status: "ongoing"`.
- Final outcome: `status: "terminal"`, `reason: "won"`, `score: 1`,
  `actions: 12`, `invalid_actions: 1`.

For interactive exploration, run `uv run --frozen python audit.py --scenario S1`
and type the same operation names. `reset 0` restarts; `quit` exits. `--scenario`
also accepts S2 or S3. Routes above are human test instructions only, never
passed to the model or baseline.

### Minutes 3–4: complete heuristic baseline episode

```sh
uv run --frozen python audit.py --scenario S1 --episode baseline
```

Expected: terminal `won`, score 1, zero model calls, a printed JSONL path in
`traces/audit/` ending `-baseline-S1-0.jsonl`. This is the real heuristic
baseline through the episode runner, not a replay of the route above.

### Minutes 4–6: short live Anthropic episode and saved trace

```sh
uv run --frozen python audit.py --scenario S1 --episode live
```

This makes **up to four paid calls** to `claude-haiku-4-5`, up to 400 output
tokens per call, with an eight-second runner timeout per call and SDK retries
disabled. Usually a few cents or less; not a dollar-denominated spending cap.
A timed-out request may still be billed. This is an audit smoke episode, not a
final-suite result. It ends on death/win or the existing `call_limit`; a win is
not required. Expect `status: "terminal"`, `calls` at most 4, and a trace path
ending `-model-history-S1-0.jsonl`. Output includes tokens and estimated cost.

```sh
uv run --frozen python - <<'PY'
import json
from pathlib import Path
paths = sorted(Path('traces/audit').glob('*-model-history-S1-0.jsonl'))
if not paths:
    raise SystemExit('No live audit trace: run the live command successfully first.')
p = paths[-1]
rows = [json.loads(line) for line in p.read_text().splitlines()]
print('Saved trace:', p)
print('Header:', json.dumps(rows[0], sort_keys=True))
print('Recorded step rows:', len(rows) - 1)
PY
```

The header records outcome, usage, calls and failures; subsequent lines record
actions, sources and model replies. A missing key stops before any episode.
Auth/network/rate-limit errors can produce labeled fallbacks: **all failed
calls are not proof of live gameplay** (the CLI exits nonzero in that case).
Fix credentials/access and retry; never present a fake or old trace as this run.

### Minutes 6–8: latest course CI and regression checks

Open [PR #57](https://github.com/columbia-university-ai-games/game-dev-f26/pull/57)
and the [midterm-saadsatter workflow](https://github.com/columbia-university-ai-games/game-dev-f26/actions/workflows/midterm-saadsatter.yml).
Choose the newest run for `saadsatter/midterm`, confirm its commit equals the
PR head, and inspect **saadsatter deterministic checks (Python 3.11/3.12)**.
Both must be green. Older green runs do not verify a newer commit. The course
starter and Minigame tests are separate checks.

```sh
uv run --frozen pytest -q tests/test_audit.py tests/test_regressions.py tests/test_trace_replay.py
```

Expected: all pass. Full deterministic suite: `uv run --frozen pytest -q`.
The offline provider SDK test runs with the installed `model` extra; other
optional artwork tests may skip in the personal clone without bundled images.

**Known S3 crash:** fixed in development commit
[f9c2c14bb543b8b084da2ae087fd0126b23a791f](https://github.com/SaadSatter/princeofpersia_reconstruction/commit/f9c2c14bb543b8b084da2ae087fd0126b23a791f).
A loose ledge falling during `UP` previously caused `_enter(None)` / TypeError;
climbing down could leave the kid hanging in air. Regression tests cover both.
The audit transfer includes that existing fix; it changes no frozen scenarios
or historical results. S1 is used to keep the timed demonstration short.

**Unrelated red check:** “Minigame submission boundaries” rejects the required
root midterm workflow. Trusted base [scripts/minigames.py lines 25–27](https://github.com/columbia-university-ai-games/game-dev-f26/blob/66f051b20fea7c341eab4c5bc6c5845128309500/scripts/minigames.py#L25-L27)
protect `.github/`; [lines 163–174](https://github.com/columbia-university-ai-games/game-dev-f26/blob/66f051b20fea7c341eab4c5bc6c5845128309500/scripts/minigames.py#L163-L174)
reject protected changes for non-maintainers even outside the Minigame lab.
The midterm brief explicitly requires `.github/workflows/midterm-saadsatter.yml`.
Course staff must reconcile this policy conflict. No bypass is included.

## After the pair audit

Generated audit traces live separately in `traces/audit/`; preserve the useful
trace for evidence, without editing `traces/eval/` or old live trials. This is
not yet a finished submission: final model comparisons, student-authored log
and limitations, independent review, peer notes and recording remain required.

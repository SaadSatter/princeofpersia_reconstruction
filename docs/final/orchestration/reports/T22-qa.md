---
handoff_id: HO-T22-qa
task_id: T22
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-tech-lead.md@73e6531 (brief docs/final/orchestration/tasks/T22.md@9305b3e)
source_branch: gate/T22-qa
source_commit: see the branch head (tests tests/test_qa_T22_probes.py; this report is committed with it)
reviewed_commit: 73e6531
verdict: ACCEPT WITH NOTES
---

# T22: QA report (Gate 1)

Status: done

## Work completed
Reviewed 73e6531 (tests a07ca95, work 2c70380, base 74975e1) on a clean tree. Read `agents/modes.py`, the
`play.py`, `server/` and `web/` hooks and the JS. Wrote 44 adversarial probes
(`tests/test_qa_T22_probes.py`: 43 pass, 1 strict xfail = finding QA-T22-1). No production code or existing
test touched. No reproduced blocker or major finding.

## Paths
`tests/test_qa_T22_probes.py`, this report. Scope: `git diff --name-only 74975e1..73e6531` lists 23 paths, all
inside the brief's permitted set (new `agents/modes.py`, `render/menu.py`, `server/modes.py`, `play.py`, `server/**`,
`web/**`, `tools/web/build.py`, `tests/test_t22_*.py`, the four docs, one agent-session file, the TL report). No
existing test edited; `pop/`, `agents/rl/`, `tools/rl/`, `pyproject.toml`, `uv.lock`, `README.md`, `.github/`,
`ci/` untouched. `pop/` does not import `agents.modes`.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | The three front ends list the same three modes and labels, one source | yes (1 cosmetic copy) | pygame menu, server and manifest read `agents.modes`; `web/*.js` and `*.html` hold no label text and read `manifest.modes` (probe `test_js_and_html_hold_no_label_text...`); `manifest.modes == manifest_modes()` in a fresh build. One literal copy remains: the `play.py --mode` help string (QA-T22-1). `web/bridge.py` and `server/match.py` repeat labels only in comments/docstrings |
| 2 | AI mode loads shipped weights by hash, refuses a wrong hash, no silent baseline | yes | probes with a one-byte-appended weights file and with a missing file: `make_controller`, `make_seat_rival`, `verify_shipped`, `make_game(rival="ai")` (honest on and off) all raise `WeightsError`; `play.main(["--mode","ai"])` returns 2, prints `error`, and `versus_main` is never called (spied); `server.__main__.main` exits 2; `build.build` raises. Baseline mode is unaffected by the bad file (expected, not a fallback). A wrong expected hash is refused for the good file |
| 3 | AI seat sees only its own observation and legal actions; fallback labelled | yes | spy in pygame (`--mode ai` and `baseline`, whole duel: `obs == ep.observe("B")`, legal tuple equal, no seed/_duel/rng/owner keys), in the bridge (`ai`), and in the server `Match` (`ai`, `baseline`). Fallback entries are `{"source":"fallback","seat":"B"}` (slow answer, policy error) |
| 4 | Online AI room sends nothing beyond its seat's payload; 0.04 s budget or logged fallback | yes | real-socket probes: hello and every state/status message free of seed, token (in state), snapshot, owner, fallback, source, weights, sha256, policy, ppo; junk and seat-B-claiming client messages ignored; extra create fields (`seat`, `seed`, `rival`, `neutral`, `weights`, `sha256`) cannot change the room. Slow policy injected (0.30 s per decision): worst `advance` call < 0.09 s (budget 0.04), trace gets `slow_answer_replaced_by_wait`, labelled fallback, and the string never reaches client A |
| 5 | pygame `--mode` starts the right controllers; menu uses the palette | yes | probes `--mode ai|baseline` run a whole screenshot duel with the spy; `human` starts no controller (TL test); menu palette test (TL) re-read, passes. Not seen in a real window |
| 6 | Web bundle holds weights with the right hash; bridge picks controller per mode | yes (Python side) | built bundle: `manifest.weights_sha256 == SHIPPED_SHA256`; `game.zip` member `agents/rl/weights/ppo-run-1.json` hashes to it; bundle carries no `tools/rl`, `evaluation` or `server`. `?play=` parsed by the real `keys.js` under node: `ai`→`ai`, `baseline`→`baseline`, `human`→`local_two_players`, bogus→baseline, `play=ai&rival=idle`→ai, no query→baseline. No browser run |
| 7 | Deterministic AI-mode duel with scripted input | yes | `play.main --mode ai --seed 11 --keys ...` twice gives byte-identical screenshots (PNG compare, same machine; the TL's same-final-hash test is the stronger check) |
| 8 | Suite green, real line; `uv lock --check` | yes | below; `uv lock --check`: `Resolved 27 packages` |
| 9 | Manual run | partly (TL) | I did not repeat the TL's manual server and pygame runs beyond the probes above (they use the same code paths over real localhost sockets). No window, no browser |

Further asks in the prompt:
- Both key sets drive seat A against an AI: `ai_key_names()` maps every WASD and arrow/`. / '` key to seat A (probe);
  local two-player still builds A = WASD, B = arrows (table unchanged, the `rival is None` branch is the old dict).
  I could not inject held keys through the SDL dummy driver, so the held-key loop itself is read, not run.
- Rematch over real sockets: a press mid-duel does nothing; one press restarts an AI room; in a human room one press
  leaves it `ended`, the second restarts it. Fallbacks are per duel after a rematch.
- Second client in an AI room: `full` (also with a forged `seat`, a token, or `mode: human`); the owner is unharmed.
  Reconnect with the seat token returns to seat A; a bad token is an error.
- Bad modes (`["ai"]`, `{}`, `1`, `true`, `""`, `"AI"`, `"ai "`, `"ai\n"`, 60 chars, `"Ai"`, `"__proto__"`): all
  `bad_mode`, no room created, the same socket can then create a good room.
- Old flags: `play.py ARENA --versus` still plays and screenshots; `--mode`/`--menu` with `--watch`/`--replay` and an
  unknown `--mode` are argparse errors. (`--versus` needs the `ARENA` positional, as before.)

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q          (clean tree, 73e6531)
1856 passed, 11 skipped, 5 xfailed, 2 warnings in 443.55s (0:07:23)

uv run --frozen --extra play --extra train --extra online pytest -q tests/test_qa_T22_probes.py
43 passed, 1 xfailed in 6.01s
```
Same counts as the Tech Lead's run (base 1805 + 51 new). The probe file was added after this run; the suite with it
adds 43 passed and 1 xfailed.

## Findings
Reproduced:
- [cosmetic] QA-T22-1 `play.py:518-519`: the `--mode` help string spells "AI Model (trained)", "Baseline (scripted)",
  "Human vs Human", a second copy of the labels outside `agents/modes.py` (brief: "no second copy"). Repro:
  `pytest tests/test_qa_T22_probes.py::test_no_file_but_agents_modes_spells_a_mode_label` (strict xfail; it will XPASS
  when the help text is generated from `modes.MODES` or stops naming labels). Expected: help built from the list.
  Harmless today, drifts if a label changes.
- [minor] QA-T22-2 (#88 not met on the legacy path) `server/__main__.py:64-66`: `--rival baseline` with no
  creator-chosen mode, which is the server's default room (the code-less join, decision #56) and any client that sends
  no `mode`, keeps "AI rival: <name> (<kind>)". This answers the TL's concern 1: it is the **only** path where #88
  fails. Checked: `--rival ai` rooms, every room made with a `mode`, the hosted page (JS passes `honest=true`), and
  pygame are labelled honestly. The `Match(honest=False)` and `make_game(..., honest=False)` defaults are also
  legacy but only reached by old tests and code-less callers. Fix is the one the TL proposed (delete `legacy`, update
  `tests/test_gate_t13_qa_online.py` CLI baseline case); needs the orchestrator to allow the existing-test edit.
  Pinned in `test_label_honesty_is_missing_only_on_the_legacy_default_room_path`.

Observations (not failures):
- [minor, observation] The pygame AI seat is called synchronously with no time limit (probe: a 0.15 s policy blocks
  the frame 0.15 s). #45 names the live server only, and measured inference is about 1 ms, so this is within the
  decisions. Same for the hosted page (Pyodide).
- [minor, observation] Creating an AI room loads the 430 KB weights inside the asyncio loop: about 40 ms the first time,
  about 6 ms after, per room. It can delay other rooms' 12 Hz tick by up to half a tick. 50 rooms maximum.
- [observation] The label "AI Model (trained)" is now sent to the client by design (#88); the kind is no longer
  hidden. Nothing else about the rival (hash, weights, fallbacks) is in any client message.
- [unverified] Pyodide load time of the weights, any browser behaviour (mode buttons, `online.html` picker with the
  `aria-pressed` state), real keyboard focus; the held-key loop in `versus_main` under a real display.

## Known limitations
No browser, no window, no `tools/web/smoke.cjs` run, no two-human session. The PNG determinism check is byte-exact on
one machine only.

## Unresolved findings
QA-T22-1 (cosmetic), QA-T22-2 (minor, needs a decision to edit one existing test).

## Requested next action
Evaluation Specialist (Gate 2): read `docs/final/orchestration/reports/T22-qa.md` and
`tests/test_qa_T22_probes.py` on `gate/T22-qa`, then judge the AI seat in the three front ends, the server-to-client
payload of an AI room and the fallback paths (`agents/modes.py` `ModeRival`, `server/match.py`
`_note_fallbacks`). Then the orchestrator decides QA-T22-2 (delete `legacy`, update the one T13 test) before Gate 3.

## Student decision required
none

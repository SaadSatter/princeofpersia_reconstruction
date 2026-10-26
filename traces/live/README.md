# traces/live

Live model runs from development (the tuning suite), kept as records.

| Files | What it is |
| --- | --- |
| `20261026T061626Z-model-history-S1-0.jsonl`, `20261026T061626Z-results.json`, `20261026T061626Z-table.md` | **Live development trial 1** (provenance confirmed by the student, 2026-10-26), model-history on S1 seed 0, `claude-haiku-4-5-20251001`, game `0.1.0+06ff044` (before the session-03 fixes; no `late_replies` field; price stamped 2026-10-06, same rate): 4 calls, 0 failed, `died:spikes` after 4 actions, 4485 / 956 tokens, $0.0093. |
| `20261026T180142Z-model-history-S1-0.jsonl`, `20261026T180142Z-results.json`, `20261026T180142Z-table.md` | **Live development trial 2**, model-history on S1 seed 0, `claude-haiku-4-5-20251001`, game `0.1.0+c23ebf7`: 4 calls, 0 failed, `died:spikes` after 4 actions, 4485 / 940 tokens, $0.0092. See `EVALUATION.md`, "Live development trials". |
| `20261026T162629Z-model-history-S1-0.jsonl`, `20261026T162629Z-results.json`, `20261026T162629Z-table.md` | **Failed live attempt, not model gameplay.** All 40 calls failed in the `anthropic` SDK with `TypeError: Could not resolve authentication method` because `ANTHROPIC_API_KEY` was unset or empty in the Python process. No request reached the API: 0 tokens, $0, every action a `WAIT` fallback, outcome `step_limit`. Written before the R-D25 fix, so it has no `error_kind` field. See `EVALUATION.md`, "Failed live attempt". |

These are development trials on the tuning suite, not final-suite results.

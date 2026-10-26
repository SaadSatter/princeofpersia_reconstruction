# traces/live

Live model runs from development (the tuning suite), kept as records.

| Files | What it is |
| --- | --- |
| `20261026T162629Z-model-history-S1-0.jsonl`, `20261026T162629Z-results.json`, `20261026T162629Z-table.md` | **Failed live attempt, not model gameplay.** All 40 calls failed in the `anthropic` SDK with `TypeError: Could not resolve authentication method` because `ANTHROPIC_API_KEY` was unset or empty in the Python process. No request reached the API: 0 tokens, $0, every action a `WAIT` fallback, outcome `step_limit`. Written before the R-D25 fix, so it has no `error_kind` field. See `EVALUATION.md`, "Failed live attempt". |

Other files in this folder are not committed until their origin is
confirmed by the student.

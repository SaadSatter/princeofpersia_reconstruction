"""Versus evaluation suite (docs/final/evaluation/PROTOCOL.md, task T08).

Scenario registry, success monitors, controller registry, the held-out freeze
check and result statistics. Evaluator code only: nothing here is imported by
`pop/`, `agents/`, `tools/rl/` or any training code, and no controller ever
sees a monitor.
"""

SCHEMA_VERSION = "shadow-masque-versus-eval/1"

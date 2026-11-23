"""Shared redaction rules for agent-session evidence.

Every string that leaves a local transcript passes through `redact()` before it
is written anywhere. The patterns are deliberately broad: a false positive costs
a few characters of evidence, a false negative publishes a credential.
"""

from __future__ import annotations

import os
import re

HOME = os.path.expanduser("~")

# Order matters: the specific token shapes run before the generic UUID-in-URL rule.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")),
    ("openai-key", re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_\-]{20,}")),
    ("google-key", re.compile(r"AIza[0-9A-Za-z_\-]{30,}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}")),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer-token", re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{16,}")),
    ("url-credential", re.compile(r"(https?://)[^\s/@:\"']+(?::[^\s/@\"']+)?@")),
    ("env-assignment", re.compile(r"(?i)\b([A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)=([^\s\"'$]{6,})")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    for name, pattern in PATTERNS:
        if name == "bearer-token":
            out = pattern.sub(lambda m: m.group(1) + "[REDACTED]", out)
        elif name == "url-credential":
            out = pattern.sub(lambda m: m.group(1) + "[REDACTED]@", out)
        elif name == "env-assignment":
            out = pattern.sub(lambda m: m.group(1) + "=[REDACTED]", out)
        else:
            out = pattern.sub("[REDACTED]", out)
    # Local paths: keep them inspectable but not tied to one machine's home.
    return out.replace(HOME, "~")


def findings(text: str) -> list[tuple[str, int]]:
    """Return (pattern name, line number) for every credential-shaped match."""
    hits: list[tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS:
            for m in pattern.finditer(line):
                frag = m.group(0)
                if "[REDACTED]" in line[m.start(): m.end() + 12]:
                    continue
                # ${VAR} and $VAR references are not secrets.
                if name == "env-assignment" and m.group(2).startswith(("${", "$", "<", "...")):
                    continue
                hits.append((name, lineno))
    return hits

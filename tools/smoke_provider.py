"""One-call provider smoke test. Not part of the evaluation suite.

Checks that the credential, model id and SDK work by sending exactly one tiny
request (a few input tokens, at most 8 output tokens). No game, no situation,
no player. Run from the project folder:

    # no network: is the key visible to Python? (never prints the key)
    uv run python tools/smoke_provider.py --check-only

    # exactly one paid call (about $0.00005 at $1 / $5 per MTok)
    uv run python tools/smoke_provider.py --live --out traces/live

With --out, the result (model id, request id, tokens, cost, latency, error
kind) is saved as JSON. The SDK's retries are off, so one run is one request.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # run from anywhere

from agents.providers import (PRICE_DATE, PRICE_SOURCE, ProviderConfigError,  # noqa: E402
                              check_credentials, classify_error, estimate_cost, make_provider)
from pop.runner import safe_error_text  # noqa: E402

SYSTEM = "Reply with the single word OK."
USER = "OK?"
MAX_TOKENS = 8


def key_status(provider: str) -> str:
    """Describe the credential without revealing it."""
    if provider != "anthropic":
        return f"{provider}: credentials come from the provider's own setup"
    v = os.environ.get("ANTHROPIC_API_KEY")
    if v is None:
        return "ANTHROPIC_API_KEY: not set in this process"
    return (f"ANTHROPIC_API_KEY: set, {len(v)} characters, "
            f"starts with 'sk-ant-': {v.startswith('sk-ant-')}, "
            f"surrounding whitespace: {v != v.strip()}")


def main(argv: list[str] | None = None, provider=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true", help="send the one paid request")
    ap.add_argument("--check-only", action="store_true", help="no network; check the key only")
    ap.add_argument("--provider", default="anthropic", choices=["anthropic", "vertex"])
    ap.add_argument("--model", help="model id (default: $POP_MODEL or claude-haiku-4-5)")
    ap.add_argument("--out", help="folder for the JSON result (e.g. traces/live)")
    args = ap.parse_args(argv)

    print(key_status(args.provider))
    try:
        check_credentials(args.provider)
    except ProviderConfigError as exc:
        ap.exit(2, f"smoke_provider.py: error: {exc} No request was sent.\n")
    if args.check_only:
        print("credential check passed; no request sent")
        return 0
    if not args.live:
        ap.error("this sends one paid request; pass --live (or --check-only)")

    if provider is None:
        provider = make_provider(args.provider, args.model)
        provider.max_tokens = MAX_TOKENS
    record = {"type": "provider_smoke", "provider": args.provider, "model_requested": provider.model,
              "max_tokens": MAX_TOKENS, "price_date": PRICE_DATE, "price_source": PRICE_SOURCE,
              "run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}
    t0 = time.perf_counter()
    try:
        c = provider.complete(SYSTEM, USER)
        record.update(ok=True, error_kind=None, model=c.model, request_id=c.request_id,
                      tokens_in=c.tokens_in, tokens_out=c.tokens_out, text=c.text,
                      cost_usd=estimate_cost(c.model, c.tokens_in, c.tokens_out))
    except Exception as exc:  # noqa: BLE001 - report every failure with its kind
        record.update(ok=False, error_kind=classify_error(exc), error=safe_error_text(exc),
                      request_id=getattr(exc, "request_id", None))
    record["latency_ms"] = round(1000 * (time.perf_counter() - t0), 1)

    print(json.dumps(record, indent=2))
    if args.out:
        path = Path(args.out) / f"{record['run_utc']}-provider-smoke.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n")
        print(f"-> {path}")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

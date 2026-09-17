"""cache_hitrate.py - Deliverable 3: before/after measurement for the
cache lever (cache_triage.py) against the shared fixture (fixtures.py).

"Before" = every request calls the model directly (no cache).
"After"  = the same 20-request sequence run through TriageCache.

Reuses ../cost/cost_model.py's token_cost_per_request() for the $/1k
line so this script and the cost model can never silently disagree about
the token rate.

Run it:
    python cache_hitrate.py
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cost"))
from cost_model import token_cost_per_request  # noqa: E402

from cache_triage import TriageCache  # noqa: E402
from fixtures import FIXTURE_MESSAGES  # noqa: E402
from stub_model import stub_triage_model  # noqa: E402


def p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    idx = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[idx]


def run_before() -> tuple[list[float], int]:
    """No cache: every one of the 20 requests calls the model."""
    latencies = []
    for message in FIXTURE_MESSAGES:
        started = time.perf_counter()
        stub_triage_model(message)
        latencies.append(time.perf_counter() - started)
    return latencies, len(FIXTURE_MESSAGES)


def run_after() -> tuple[list[float], int, float]:
    """With cache: repeats within the fixture are served from the dict."""
    cache = TriageCache()
    latencies = []
    for message in FIXTURE_MESSAGES:
        started = time.perf_counter()
        cache.get_or_call(message)
        latencies.append(time.perf_counter() - started)
    return latencies, cache.misses, cache.hit_rate


def print_report() -> None:
    before_latencies, before_calls = run_before()
    after_latencies, after_calls, hit_rate = run_after()

    token_rate = token_cost_per_request()  # $/request, model-call only
    before_cost_per_1k = token_rate * (before_calls / len(FIXTURE_MESSAGES)) * 1000
    after_cost_per_1k = token_rate * (after_calls / len(FIXTURE_MESSAGES)) * 1000

    print(f"fixture size:        {len(FIXTURE_MESSAGES)} requests")
    print(f"hit rate (after):    {hit_rate:.0%}\n")
    print(f"{'':24}{'before (no cache)':>20}{'after (cache)':>16}")
    print(f"{'model calls':24}{before_calls:>20}{after_calls:>16}")
    print(f"{'token $/1k (calls)':24}{before_cost_per_1k:>20.2f}{after_cost_per_1k:>16.2f}")
    print(f"{'p50 latency (ms)':24}{sorted(before_latencies)[len(before_latencies)//2]*1000:>20.1f}"
          f"{sorted(after_latencies)[len(after_latencies)//2]*1000:>16.1f}")
    print(f"{'p95 latency (ms)':24}{p95(before_latencies)*1000:>20.1f}{p95(after_latencies)*1000:>16.1f}")


if __name__ == "__main__":
    print_report()

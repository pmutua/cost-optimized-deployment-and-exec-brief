"""batch_worker.py - Deliverable 3, lever two: a batch queue that groups
triage requests so the system prompt's fixed token overhead
(api/app/triage_model.py's SYSTEM_PROMPT, 143 tokens -- see
../cost/cost_model.py footnote [2]) is paid once per batch instead of
once per request.

Not a quantization proxy -- this repo has no GPU and did not attempt one
(capstone_extras fallback for quantization is declared as "not attempted"
in ../README.md, not silently substituted here). This is a genuine,
independent second lever: token sharing across a batch, orthogonal to the
caching lever in cache_triage.py.

Honesty note this module exists to demonstrate: batching trades latency
for cost. A request must wait for its batch to fill (or for
max_wait_seconds to elapse) before it is processed at all -- see
measurements.md for why that makes batching unsafe for the highest-
urgency triage messages without a separate fast path.

Run it:
    python batch_worker.py
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cost"))
from cost_model import INPUT_RATE_PER_1M_TOKENS, OUTPUT_RATE_PER_1M_TOKENS  # noqa: E402

from fixtures import FIXTURE_MESSAGES  # noqa: E402
from stub_model import (  # noqa: E402
    COMPLETION_TOKENS_PER_CALL,
    STUB_CALL_LATENCY_SECONDS,
    SYSTEM_PROMPT_TOKENS,
    stub_triage_model,
)

PER_ITEM_PROMPT_TOKENS = 60  # the patient message itself; see cost_model.py footnote [2]


@dataclass
class QueuedRequest:
    patient_message: str
    arrival_time: float


@dataclass
class BatchResult:
    patient_message: str
    response: dict
    arrival_time: float
    completed_time: float
    batch_size: int

    @property
    def added_latency_seconds(self) -> float:
        return self.completed_time - self.arrival_time


class BatchQueue:
    """Flushes when either `batch_size` requests have queued or
    `max_wait_seconds` has elapsed since the oldest queued request --
    whichever comes first. Driven explicitly by run_simulation() below
    (arrival time -> flush decision) rather than a real timer/event loop,
    so the measurement stays deterministic and offline.
    """

    def __init__(self, batch_size: int = 5, max_wait_seconds: float = 2.0):
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self._queue: list[QueuedRequest] = []

    def add(self, patient_message: str, arrival_time: float) -> None:
        self._queue.append(QueuedRequest(patient_message, arrival_time))

    def should_flush(self, now: float) -> bool:
        if not self._queue:
            return False
        if len(self._queue) >= self.batch_size:
            return True
        oldest = self._queue[0].arrival_time
        return (now - oldest) >= self.max_wait_seconds

    def flush(self, now: float) -> list[BatchResult]:
        batch = self._queue
        self._queue = []
        n = len(batch)
        # One stub call stands in for one real call carrying all n items:
        # the round trip happens once for the whole batch, not n times.
        time.sleep(STUB_CALL_LATENCY_SECONDS)
        completed_time = now + STUB_CALL_LATENCY_SECONDS
        return [
            BatchResult(item.patient_message, stub_triage_model(item.patient_message), item.arrival_time, completed_time, n)
            for item in batch
        ]

    def batch_prompt_tokens(self, n_items: int) -> int:
        return SYSTEM_PROMPT_TOKENS + (PER_ITEM_PROMPT_TOKENS * n_items)


def run_simulation(
    messages: list[str], arrival_times: list[float], batch_size: int = 5, max_wait_seconds: float = 2.0
) -> list[BatchResult]:
    """Replays `messages` arriving at `arrival_times` (seconds, same
    length, monotonically increasing) through a BatchQueue, checking the
    flush condition after every arrival and once more at the end for
    whatever is left queued.
    """
    queue = BatchQueue(batch_size=batch_size, max_wait_seconds=max_wait_seconds)
    results: list[BatchResult] = []
    for message, arrival in zip(messages, arrival_times):
        queue.add(message, arrival)
        if queue.should_flush(arrival):
            results.extend(queue.flush(arrival))
    if queue._queue:  # noqa: SLF001 -- final partial batch, same module
        results.extend(queue.flush(arrival_times[-1] + max_wait_seconds))
    return results


def _shift_arrivals() -> list[float]:
    """20 arrival times over a simulated shift, shaped so both flush
    paths in BatchQueue actually trigger: a busy morning and a moderate
    afternoon fill batches by size; a quiet evening forces each of the
    last 5 requests into its own timeout-triggered, size-1 "batch" --
    the honest worst case this lever's docstring warns about.
    """
    arrivals: list[float] = []
    t = 0.0
    for _ in range(10):  # busy morning: one every 0.3s
        arrivals.append(t)
        t += 0.3
    t += 3.0  # lull
    for _ in range(5):  # moderate afternoon: one every 0.5s
        arrivals.append(t)
        t += 0.5
    t += 3.0  # lull
    for _ in range(5):  # quiet evening: one every 2.5s, past max_wait_seconds
        arrivals.append(t)
        t += 2.5
    return arrivals


def p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    idx = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[idx]


def print_report(batch_size: int = 5, max_wait_seconds: float = 2.0) -> None:
    arrivals = _shift_arrivals()
    messages = list(FIXTURE_MESSAGES)

    # Before: no batching, one call per request, processed immediately.
    before_prompt_tokens = len(messages) * (SYSTEM_PROMPT_TOKENS + PER_ITEM_PROMPT_TOKENS)
    before_latencies = [STUB_CALL_LATENCY_SECONDS] * len(messages)  # no queue wait

    # After: batched per _shift_arrivals()'s flush pattern. Each distinct
    # completed_time is one flush event (one batch); its batch_size tells
    # us how many items shared that one system-prompt payment.
    results = run_simulation(messages, arrivals, batch_size=batch_size, max_wait_seconds=max_wait_seconds)
    batch_sizes_by_flush: dict[float, int] = {r.completed_time: r.batch_size for r in results}
    after_prompt_tokens = sum(SYSTEM_PROMPT_TOKENS + PER_ITEM_PROMPT_TOKENS * bs for bs in batch_sizes_by_flush.values())
    after_latencies = [r.added_latency_seconds for r in results]

    completion_tokens_total = len(messages) * COMPLETION_TOKENS_PER_CALL  # unchanged by batching either way

    def cost_per_1k(prompt_tokens_total: int) -> float:
        prompt_cost = (prompt_tokens_total / 1_000_000) * INPUT_RATE_PER_1M_TOKENS
        completion_cost = (completion_tokens_total / 1_000_000) * OUTPUT_RATE_PER_1M_TOKENS
        return ((prompt_cost + completion_cost) / len(messages)) * 1000

    print(f"fixture size:         {len(messages)} requests, {len(batch_sizes_by_flush)} batches (batch_size={batch_size}, max_wait={max_wait_seconds}s)\n")
    print(f"{'':24}{'before (no batch)':>20}{'after (batched)':>18}")
    print(f"{'prompt tokens total':24}{before_prompt_tokens:>20}{after_prompt_tokens:>18}")
    print(f"{'token $/1k':24}{cost_per_1k(before_prompt_tokens):>20.3f}{cost_per_1k(after_prompt_tokens):>18.3f}")
    print(f"{'p50 added latency ms':24}{sorted(before_latencies)[len(before_latencies)//2]*1000:>20.1f}"
          f"{sorted(after_latencies)[len(after_latencies)//2]*1000:>18.1f}")
    print(f"{'p95 added latency ms':24}{p95(before_latencies)*1000:>20.1f}{p95(after_latencies)*1000:>18.1f}")


if __name__ == "__main__":
    print("--- minimal flush-path demo ---")
    demo_messages = ["msg-a", "msg-b", "msg-c", "msg-d", "msg-e", "msg-f"]
    demo_arrivals = [0.0, 0.1, 0.2, 0.3, 0.4, 3.0]  # last one arrives after a gap
    for result in run_simulation(demo_messages, demo_arrivals, batch_size=5, max_wait_seconds=2.0):
        print(
            f"{result.patient_message:8} arrived={result.arrival_time:>5.1f}s "
            f"completed={result.completed_time:>5.2f}s batch_size={result.batch_size} "
            f"added_latency={result.added_latency_seconds * 1000:>6.1f}ms"
        )

    print("\n--- before/after measurement over a simulated shift ---")
    print_report()

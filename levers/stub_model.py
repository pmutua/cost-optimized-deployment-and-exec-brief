"""stub_model.py - deterministic stand-in for api/app/triage_model.py's
real gpt-4o-mini call, used only by the lever measurement scripts in this
folder so the cache and batch experiments never spend against a live key.

capstone_extras fallback declared: "No OpenAI credits: stub the model
behind the same response schema; still implement cache, batch queue, and
cost model arithmetic on recorded/fake usage." api/app/triage_model.py
itself is untouched -- this stub lives entirely in levers/ and is never
imported by the real API.

Same response schema as the real triage_model(): {"urgency", "advice",
"model_used"}, plus token counts the real endpoint doesn't expose
client-side, added here purely so the lever scripts can compute $/1k
without parsing a live usage field.
"""

from __future__ import annotations

import hashlib
import random
import time

STUB_CALL_LATENCY_SECONDS = 0.05  # simulated network + inference round trip
LATENCY_JITTER_SECONDS = 0.04     # +/- spread, so p95 measurements are meaningful

# Matches ../cost/cost_model.py's AVG_PROMPT_TOKENS / AVG_COMPLETION_TOKENS
# (footnotes [2]/[3]) so the lever measurements and the cost model agree.
PROMPT_TOKENS_PER_CALL = 203
COMPLETION_TOKENS_PER_CALL = 72
SYSTEM_PROMPT_TOKENS = 143  # the shared portion batch_worker.py amortises

_RESPONSES = [
    {"urgency": "low", "advice": "Rest, stay hydrated, and monitor your symptoms over the next 24 hours."},
    {"urgency": "medium", "advice": "See a clinician within the next day if symptoms persist or worsen."},
    {"urgency": "high", "advice": "Go to the nearest clinic immediately; this needs urgent attention."},
]

_jitter_rng = random.Random(1234)  # fixed seed: reproducible latency samples across runs


def stub_triage_model(patient_message: str) -> dict:
    """Deterministic on patient_message (same input -> same urgency/advice
    every call, which is what makes the exact-match cache in
    cache_triage.py meaningful to measure), with a small randomised
    latency so p95 numbers in measurements.md aren't a flat line.
    """
    jitter = _jitter_rng.uniform(0, LATENCY_JITTER_SECONDS)
    time.sleep(STUB_CALL_LATENCY_SECONDS + jitter)

    idx = int(hashlib.sha256(patient_message.strip().lower().encode()).hexdigest(), 16) % len(_RESPONSES)
    response = dict(_RESPONSES[idx])
    response["model_used"] = "stub-gpt-4o-mini"
    response["prompt_tokens"] = PROMPT_TOKENS_PER_CALL
    response["completion_tokens"] = COMPLETION_TOKENS_PER_CALL
    return response

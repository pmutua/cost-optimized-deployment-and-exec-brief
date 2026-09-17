"""cache_triage.py - Deliverable 3, lever one: an in-memory dict cache in
front of the triage stub.

capstone_extras fallback declared: "No Redis: use the in-memory dict
cache from Lab 1; document TTL + hit-rate the same way." This is that
cache -- a plain process-local dict, not Redis. It would not survive a
restart or work across more than one replica; that limitation is called
out in measurements.md rather than hidden.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from stub_model import stub_triage_model

DEFAULT_TTL_SECONDS = 300  # 5 minutes


@dataclass
class CacheEntry:
    value: dict
    expires_at: float


class TriageCache:
    """Exact-match cache keyed on the normalised patient message text.
    Not semantic -- two differently-worded messages describing the same
    symptom are two different keys and both call the model. That's a
    deliberate, safer choice for a triage workload: a semantic cache
    could match a *similar-sounding* message to a cached answer for a
    *different* underlying complaint. Exact-match only risks staleness
    when the identical text recurs, not misclassification from a fuzzy
    match.

    Quality/honesty note: 'high' urgency responses are never cached (see
    get_or_call below) -- a repeated identical message from a patient
    whose condition has changed since deserves a fresh read every time,
    not a cached one, even inside the TTL window.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _key(patient_message: str) -> str:
        return patient_message.strip().lower()

    def get_or_call(self, patient_message: str) -> tuple[dict, bool]:
        """Returns (response, was_cache_hit)."""
        key = self._key(patient_message)
        now = time.time()
        entry = self._store.get(key)
        if entry is not None and entry.expires_at > now:
            self.hits += 1
            return entry.value, True

        self.misses += 1
        response = stub_triage_model(patient_message)
        if response["urgency"] != "high":
            self._store[key] = CacheEntry(value=response, expires_at=now + self.ttl_seconds)
        return response, False

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


if __name__ == "__main__":
    # Minimal MISS/HIT transcript -- see cache_hitrate.py for the full
    # before/after measurement this feeds into.
    cache = TriageCache()
    for message in ["I have a mild headache.", "I have a mild headache.", "A different complaint entirely."]:
        _, hit = cache.get_or_call(message)
        print(f"{'HIT ' if hit else 'MISS'}  {message}")
    print(f"hit_rate={cache.hit_rate:.2f} hits={cache.hits} misses={cache.misses}")

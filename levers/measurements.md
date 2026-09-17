# Optimisation levers — before/after measurements

Both levers run against `stub_triage_model()` (`stub_model.py`), the
capstone's declared fallback for "No OpenAI credits" — same response
schema as the real `api/app/triage_model.py`, no live key spent. Both
measurements replay the same 20-request fixture (`fixtures.py`) so the
two levers are being tested against one consistent "shift", not two
cherry-picked samples.

## Lever 1 — response caching (`cache_triage.py`)

Minimal MISS/HIT transcript (`python cache_triage.py`):

```
MISS  I have a mild headache.
HIT   I have a mild headache.
MISS  A different complaint entirely.
hit_rate=0.33 hits=1 misses=2
```

Full before/after over the 20-request fixture (`python cache_hitrate.py`):

```
fixture size:        20 requests
hit rate (after):    40%

                           before (no cache)   after (cache)
model calls                               20              12
token $/1k (calls)                      0.07            0.04
p50 latency (ms)                        70.0            61.2
p95 latency (ms)                        87.8            79.6
```

**Reading it:** the fixture has 10 unique messages each appearing twice,
which sets a naive ceiling of 50% hit rate (10 misses, 10 hits). The
measured rate is **40%**, not 50%, because 2 of the 10 fixture messages
hash to `urgency: "high"` in the stub, and `TriageCache.get_or_call`
deliberately never caches a high-urgency response (see the class
docstring in `cache_triage.py`) — both occurrences of those two messages
are misses. That's the cache giving up 2 hits on purpose.

**Quality/honesty note:** this is an exact-match cache, not semantic — a
differently-worded message about the same symptom is a cache miss, never
a wrong-but-confident cached answer for a different complaint. The
remaining risk is narrower: TTL staleness (5-minute default) if the
identical message text recurs for a patient whose condition has changed
in that window. High-urgency responses bypass the cache entirely for
exactly this reason — the one case where a stale "everything's fine"
answer would be dangerous is the one case guaranteed never to be served
from cache.

## Lever 2 — batch queue (`batch_worker.py`)

Minimal flush-path demo (`python batch_worker.py`, first section):

```
msg-a    arrived=  0.0s completed= 0.45s batch_size=5 added_latency= 450.0ms
msg-b    arrived=  0.1s completed= 0.45s batch_size=5 added_latency= 350.0ms
msg-c    arrived=  0.2s completed= 0.45s batch_size=5 added_latency= 250.0ms
msg-d    arrived=  0.3s completed= 0.45s batch_size=5 added_latency= 150.0ms
msg-e    arrived=  0.4s completed= 0.45s batch_size=5 added_latency=  50.0ms
msg-f    arrived=  3.0s completed= 5.05s batch_size=1 added_latency=2050.0ms
```

Five requests arriving within 0.4s fill a batch of 5 and flush
immediately (size-triggered). The sixth arrives alone after a 3-second
gap and has to wait out the full `max_wait_seconds` (2.0s) before its
own timeout-triggered flush — the "whichever comes first" rule from
`BatchQueue.should_flush` in action.

Full before/after over a simulated shift (`python batch_worker.py`,
second section — busy morning, moderate afternoon, quiet evening):

```
fixture size:         20 requests, 6 batches (batch_size=5, max_wait=2.0s)

                           before (no batch)   after (batched)
prompt tokens total                     4060              2058
token $/1k                             0.074             0.059
p50 added latency ms                    50.0             950.0
p95 added latency ms                    50.0            2550.0
```

**Reading it:** batching amortises the 143-token system prompt across
each batch instead of paying it per request, cutting total prompt tokens
nearly in half (4,060 → 2,058) and token $/1k by ~20% (0.074 → 0.059).
That saving is concentrated in the busy morning and afternoon, where
batches fill by size with almost no wait. The quiet evening is the
opposite story: three of the six batches there are partially filled
(sizes 2, 2, 1) because no fifth request arrives before `max_wait_seconds`
elapses, so those requests pay up to 2 full seconds of queuing latency
for little or no token saving — a batch of 1 shares its system prompt
with nobody.

**Quality/honesty note:** batching does not change the *content* of any
answer (same stub response either way) — what it degrades is *latency*,
and for a triage endpoint, latency is a safety property, not just a UX
one. `max_wait_seconds=2.0s` bounds the worst case here at 2 seconds
before processing even starts; that may be acceptable for a coordinator
clearing a routine queue, but is not something this design would ship
for the highest-urgency messages without a separate fast path that
bypasses the batch queue entirely (the same bypass principle the cache
lever already applies to high-urgency responses, above).

## Net effect if both levers ran together

Not measured directly (the two scripts above test each lever in
isolation against the same fixture, not a combined pipeline), but the
mechanism is additive and non-overlapping: caching reduces how many
requests ever reach the model; batching reduces the prompt-token cost of
whichever requests still do. Combining them is future work flagged
honestly as such, not claimed here without a measurement to back it.

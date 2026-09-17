"""fixtures.py - the fixed request set both lever measurement scripts run
against, so cache_hitrate.py and batch_worker.py are measuring the same
"shift" of triage requests rather than two unrelated samples.

10 distinct patient messages, each appearing twice across a 20-request
sequence -- modelling a small clinic's front desk, where common
complaints (headache-and-fever, a child's cough, a minor cut) recur
across different patients using the same standard triage phrasing. This
is a fixture, not measured production traffic; see
../cost/cost_model.md footnote [7].
"""

from __future__ import annotations

_UNIQUE_MESSAGES = [
    "I have a mild headache and a slight fever since this morning.",
    "My child has a persistent cough and runny nose for three days.",
    "There is mild swelling and redness around a small cut on my arm.",
    "I feel dizzy and nauseous after skipping meals today.",
    "I have chest pain and difficulty breathing right now.",
    "My joints ache and I have a low-grade fever this afternoon.",
    "I have a sore throat and mild difficulty swallowing since yesterday.",
    "My baby has a rash and has been unusually fussy all day.",
    "I twisted my ankle and it is swollen but I can still walk.",
    "I have stomach cramps and mild diarrhoea since last night.",
]

# 20 requests: each of the 10 unique messages appears once in the first
# half (a guaranteed cache MISS the first time) and once again in the
# second half (a guaranteed cache HIT), interleaved rather than in two
# clean blocks so the sequence reads like a real queue, not a rigged demo.
FIXTURE_MESSAGES = (
    _UNIQUE_MESSAGES[0:5]
    + [_UNIQUE_MESSAGES[0], _UNIQUE_MESSAGES[2]]
    + _UNIQUE_MESSAGES[5:10]
    + [_UNIQUE_MESSAGES[1], _UNIQUE_MESSAGES[3], _UNIQUE_MESSAGES[4]]
    + [_UNIQUE_MESSAGES[6], _UNIQUE_MESSAGES[8]]
    + [_UNIQUE_MESSAGES[5], _UNIQUE_MESSAGES[7], _UNIQUE_MESSAGES[9]]
)

assert len(FIXTURE_MESSAGES) == 20
assert len(set(FIXTURE_MESSAGES)) == 10

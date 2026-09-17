# API vs. self-host — AfyaPlus triage workload

**Scope:** `POST /triage`'s single `gpt-4o-mini` call only. The FastAPI
container, auth, and rate-limit layers are identical either way and are
excluded from this comparison — only "who answers the triage question"
changes between the two options.

**Labelling note:** self-hosting was **not run** in this environment (no
GPU available — the capstone's own fallback path). Every self-host figure
below is a sourced or explicitly-assumed estimate, footnoted as such, not
a measurement. Treat this memo as a decision framework to re-run with
real numbers before committing budget, not as a verified benchmark.

## The two options

**Option A — API (current).** OpenAI `gpt-4o-mini`, pay-per-token, no
infrastructure to run beyond the existing FastAPI container. Marginal
cost per request: **$0.0000743** (`../cost/cost_model.py`'s
`token_cost_per_request()` — footnotes [1]–[3]).

**Option B — self-host.** An open-weight instruction-tuned model in
gpt-4o-mini's rough capability class (e.g. Llama 3 8B Instruct or Phi-3-
mini) served from a single-GPU instance, replacing the OpenAI call inside
`triage_model()` with a local inference call. Fixed monthly cost, near-
zero marginal cost per request.

## Self-host cost estimate (unmeasured — footnoted)

| Line | Estimate | Source |
|---|---|---|
| GPU instance | $379/month | 1x NVIDIA T4 (16GB), ~$0.526/hr on-demand, 24/7 — Azure NC4as_T4_v3 list price, accessed 2026-09-17. Not reserved/spot-discounted; a real deployment could do better. |
| Extra ops | +$120/month (3 hrs/month at $40/hr, on top of the $80/month baseline in `../cost/cost_model.py`) | Assumption: running your own inference stack (model server, GPU driver/health monitoring, occasional model updates) is more ops burden than calling a managed API, not less. |
| **Total fixed** | **$499/month** | |
| Marginal cost/request | ~$0 | A single T4 serving an 8B model has far more throughput than AfyaPlus's traffic needs at any volume modelled in `../cost/cost_model.py`, so capacity is not the binding constraint here — cost is. |

## Break-even sketch

Setting API monthly cost equal to self-host's fixed monthly cost:

```
0.0000743 * V = 499
V ≈ 6,715,000 requests/month  (≈ 224,000/day)
```

**Assumptions this rests on:** the $0.150/$0.600-per-1M-token API rate
holds ([1]); the $379/month GPU estimate holds; the self-host model needs
no additional fine-tuning spend to match triage-quality output (a real
risk — see below).

For context against `../cost/cost_model.py`'s own traffic scenarios:

| Scenario | Requests/month | vs. break-even |
|---|---|---|
| Baseline | 60,000 | 112x **below** break-even |
| 10x spike | 600,000 | 11x **below** break-even |
| Break-even | 6,715,000 | — |

**Reading it:** at AfyaPlus's current scale, and even at the stated 10x
spike, the API stays cheaper by more than an order of magnitude. Self-
hosting would need traffic roughly **11x the stated spike scenario** —
essentially a much larger, multi-region platform, not a clinic pilot —
before the fixed GPU cost pays for itself.

## What would change this decision

- **Data residency / compliance.** If patient health data must not leave
  a specific jurisdiction's infrastructure — a real consideration for
  clinical data in Kenya — self-hosting could be the right call *below*
  break-even, for regulatory reasons the cost model doesn't capture.
- **API price changes.** A material rise in `gpt-4o-mini` pricing lowers
  the break-even volume; a price drop raises it further in the API's
  favour.
- **Cheaper GPU access.** A reserved instance, spot pricing, or a GPU the
  organisation already owns for other workloads would lower the $379/
  month line and pull break-even volume down — worth re-costing with real
  quotes before deciding, not assumed here.
- **Sustained, not spiky, volume.** This break-even assumes the 10x spike
  is occasional. If traffic sustained near or above the spike level
  month over month (not just a burst), the case for self-hosting
  strengthens well before the literal break-even point, because the
  fixed GPU cost is paid whether or not it's the peak day.
- **Answer quality.** No GPU mythology: an 8B-class open-weight model is
  not assumed equivalent to `gpt-4o-mini` on this task's structured JSON
  output and non-diagnostic-advice constraints (`api/app/triage_model.py`'s
  `SYSTEM_PROMPT`) without evaluation. This memo prices the infrastructure
  trade-off only; a quality regression from switching models is a
  separate risk that would need its own fixture-based evaluation before
  a real migration, not assumed away here.

## Recommendation

Stay on the API at current and 10x-spike volume — the cost gap is too
large for infrastructure economics alone to justify the switch. Revisit
if sustained volume approaches the multi-million-request/month range, if
a data-residency requirement emerges, or if GPU access becomes materially
cheaper than the estimate above.

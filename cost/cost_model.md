# Cost model — AfyaPlus triage API

Unit economics for `POST /triage` (`api/app/triage_model.py`, one
`gpt-4o-mini` call per request). Every rate is footnoted; the arithmetic
lives in `cost_model.py` (run it — `python cost_model.py` — to regenerate
the numbers below rather than trusting this file to stay in sync by hand).

## What's in the model

Three cost lines per request:

1. **Tokens** — prompt (system prompt + patient message) and completion,
   priced separately because they have different rates.
2. **Infra** — the container instance(s) serving the API, amortised over
   the month's request volume. More traffic needs more instances past a
   capacity threshold, so this line does not shrink linearly with volume.
3. **People/ops** — a fixed monthly allowance for on-call, budget-alert
   triage, and key rotation, also amortised over volume.

## Footnoted assumptions and rates

| # | Assumption | Value | Source |
|---|---|---|---|
| 1 | gpt-4o-mini input rate | $0.150 / 1M tokens | OpenAI API pricing page, accessed 2026-09-17 — re-verify before budgeting against it |
| 1 | gpt-4o-mini output rate | $0.600 / 1M tokens | same |
| 2 | System prompt size | 143 tokens | counted directly (cl100k_base) from `api/app/triage_model.py`'s `SYSTEM_PROMPT` |
| 2 | Avg. patient message | 60 tokens | assumption — roughly two sentences, consistent with the fixture set in `../levers/measurements.md` |
| 3 | Avg. completion length | 72 tokens (60% of the 120-token cap) | assumption — not measured against a live model in this environment; replace with a measured average once real traffic exists |
| 4 | Instance cost | $15.00/month | Azure Container Apps, 0.5 vCPU / 1 GiB, consumption plan kept warm 24/7, Azure Pricing Calculator (East US), accessed 2026-09-17 |
| 5 | Instance capacity | 5,000 requests/day before scaling out | assumption pending a real load test, not a measured ceiling |
| 6 | Ops line | 2 hrs/month × $40/hr = $80/month | placeholder blended contractor rate — swap for real payroll allocation |
| 7 | Baseline traffic | 2,000 requests/day | assumption sized for a small clinic network pilot, not measured production traffic |

## $/1,000 requests — baseline vs. 10x spike

Output of `python cost_model.py`:

```
                          baseline       10x spike
requests/day                 2,000          20,000
instances needed                 1               4
token $/req                0.000074        0.000074
infra $/req                 0.000250        0.000100
ops $/req                  0.001333        0.000133
total $/req                0.001657        0.000307
$/1,000 requests               1.66            0.31
```

**Reading it:** the token cost per request is flat across both scenarios
— it's a per-call price, not a volume discount. What moves is the fixed
cost (infra + ops) being spread across far more requests at the spike:
going from 1 instance to 4 (footnote 5's capacity threshold) is a 4x
infra spend against a 10x request increase, so $/1k *drops* under load in
this model rather than rising — the fixed-cost lines dilute faster than
the token line stays flat. This is the case for a stateless API scaling
horizontally; it stops holding if the spike is sustained long enough to
need a bigger ops allowance (footnote 6 assumes light-touch monitoring,
not incident response).

## Sensitivity

`python sensitivity.py` flexes one assumption at a time around baseline
to show which levers move $/1k the most:

```
baseline $/1k = 1.6570

lever varied        value                             $/1k     delta
completion tokens   48 (0.4x cap)                   1.6426  -0.0144
completion tokens   120 (full cap)                  1.6858  +0.0288
patient msg tokens  30 (short)                      1.6525  -0.0045
patient msg tokens  150 (long)                      1.6705  +0.0135
cache hit-rate      40% (measured, see levers/)     1.6275  -0.0295
cache hit-rate      60% (optimistic)                1.6128  -0.0442
traffic             1000/day (half baseline)        3.2403  +1.5833
traffic             20000/day (10x spike)           0.3070  -1.3500
```

Traffic volume dwarfs every other lever — which is exactly the finding
that justifies optimising for scale (caching, batching) over
micro-optimising token counts. See `../levers/measurements.md` for the
cache hit-rate row measured for real rather than assumed.

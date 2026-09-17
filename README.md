# Week 7, Cost-Optimised AI Deployment

## Overview

AfyaPlus triage API (`api/`, Week 6's FastAPI + Docker + JWT spine,
unchanged — see `api/README.md`): one `gpt-4o-mini` call per request,
classifying patient message urgency and returning safe, non-diagnostic
advice. Baseline traffic is modelled at 2,000 requests/day, with a stated
10x spike scenario (20,000 requests/day) per the capstone brief. Unit
metric: **$/1,000 requests** — **$1.66 at baseline, $0.31 at the 10x
spike** (cost per 1,000 *drops* under load because fixed infra/ops costs
are spread across far more requests while the per-request AI cost stays
flat — see `cost/cost_model.md` for why).

## Repo layout

Matches the capstone brief's target layout exactly — one folder per
deliverable, nothing renamed:

```
api/       Week 6 spine (unchanged) — see api/README.md
cost/      Deliverable 1 — cost model, sensitivity, $/1k writeup
deploy/    Deliverable 2 — docker-compose, budget alert configs
levers/    Deliverable 3 — cache + batch levers, measurements
memo/      Deliverable 4 — API vs self-host trade-off memo
exec/      Deliverable 5 — executive one-pager
evidence/  Captured terminal transcripts (local run, health check, tags)
```

## Cost model

[`cost/cost_model.md`](cost/cost_model.md) — every rate footnoted
(token, infra, ops). Baseline vs. 10x spike $/1k table, plus
[`cost/sensitivity.py`](cost/sensitivity.py) showing which single
assumption moves $/1k the most (traffic volume, by a wide margin).

Run it:

```
cd cost
python cost_model.py
python sensitivity.py
```

## Deploy & budgets

[`deploy/docker-compose.cost.yml`](deploy/docker-compose.cost.yml) — runs
the triage API sized to match the cost model's assumptions (0.5 vCPU /
1 GiB), tagged with FinOps labels (`finops.cost-center`, `finops.owner`,
`finops.environment`, `finops.budget-ceiling-usd-month`). Built and run
for real against a local Docker engine; transcript in
[`evidence/local_run_transcript.md`](evidence/local_run_transcript.md).

Budget alerts: [`deploy/azure_budget_triage.json`](deploy/azure_budget_triage.json)
and [`deploy/aws_budget.json`](deploy/aws_budget.json), a $20/month
ceiling with 80%-actual and 100%-forecasted thresholds, scoped by the
same FinOps tag. Never applied against a live account — see
[`deploy/budget_alert_notes.md`](deploy/budget_alert_notes.md) for the
fallback declaration and the exact CLI commands that would apply them.

Run it:

```
cd api && cp .env.example .env   # fill in real values, or leave dev defaults for a local smoke test
cd ../deploy
docker compose -f docker-compose.cost.yml up --build -d
curl http://localhost:8000/health
```

## Levers implemented

Both run against a stubbed model (`levers/stub_model.py`, same response
schema as the real endpoint) — no live API key spent. Full evidence and
honesty notes: [`levers/measurements.md`](levers/measurements.md).

1. **Response caching** (`levers/cache_triage.py`) — in-memory TTL dict
   cache. Measured **40% hit rate** on a 20-request fixture, cutting the
   AI-call token cost by the same share. High-urgency responses are
   never cached (safety over savings).
2. **Batch queue** (`levers/batch_worker.py`) — groups concurrent
   requests into one call, sharing the fixed system-prompt token cost.
   Measured **~20% token $/1k reduction** during busy periods, at the
   cost of up to **2.55s p95 added latency** during quiet periods —
   stated plainly as a trade-off, not hidden.

Quality notes: caching risks TTL-window staleness only for an exact
repeated message (mitigated by the high-urgency bypass); batching risks
latency, not answer quality (mitigated the same way — no batching for
urgent messages). Both documented in full in `levers/measurements.md`.

## API vs self-host memo

[`memo/api_vs_selfhost.md`](memo/api_vs_selfhost.md) — self-hosting was
**not run** (no GPU available); every self-host figure is a labelled
estimate, not a measurement.

- API marginal cost: **$0.0000743/request**. Self-host fixed cost
  estimate: **$499/month** (GPU + extra ops), footnoted.
- Break-even: **~6.7M requests/month** — about **11x** the stated 10x
  spike scenario.
- **Recommendation: stay on the API** at current and spike volume; revisit
  on sustained multi-million-request/month growth, a data-residency
  requirement, or materially cheaper GPU access.

## Executive one-pager

[`exec/one_pager.md`](exec/one_pager.md) (written) and
[`exec/executive_deck.pptx`](exec/executive_deck.pptx) (10-slide deck) —
cost per 1,000 requests, the spike plan, both levers in business
language, one risk + mitigation (urgent-case bypass on both levers), and
a **Go** recommendation with three explicit conditions (budget alert
activation, urgent-case bypass staying enforced, re-costing before
scaling past the modelled 10x spike). Same numbers, same recommendation,
two formats for two audiences.

## Fallbacks declared

- [x] Redis / dict cache — no Redis; in-memory TTL dict cache used
      (`levers/cache_triage.py`), TTL and hit-rate documented in
      `levers/measurements.md`.
- [ ] GPU quantization / mocked smoke — not applicable. The brief allows
      "cache + batch queue" *or* "cache + quantization smoke" as the two
      levers; this submission implements the former, so no quantization
      smoke test was built.
- [x] Paid cloud / config-only budgets — no paid Azure/AWS account;
      `deploy/azure_budget_triage.json` and `deploy/aws_budget.json` are
      submitted as config-as-code plus local Docker Compose run evidence
      (`evidence/local_run_transcript.md`), per `deploy/budget_alert_notes.md`.
- [x] No OpenAI credits committed to this repo — the lever measurement
      scripts (`levers/`) run entirely against a stubbed model
      (`levers/stub_model.py`), same response schema as the real
      endpoint, so no live key is spent running this repo's evidence.
      The real `api/app/triage_model.py` still makes a real call when a
      key is configured — it is untouched from Week 6.
- [ ] No Kubernetes cluster — not applicable; Week 6's `deployment.yaml`
      (in `api/`) already documents this as a read-only manifest with no
      live cluster, per that capstone's own fallback note.

## Checklist

- [x] $/1k at baseline ($1.66) and 10x spike ($0.31) — `cost/cost_model.md`
- [x] Budget alert evidence — configs + local run transcript, no live
      cloud console (`deploy/budget_alert_notes.md`)
- [x] Two levers with before/after measurements — `levers/measurements.md`
- [x] Honest quality/trade-off notes on both levers — cache: TTL
      staleness, mitigated by urgent-case bypass; batch: added latency,
      mitigated the same way
- [ ] Executive language reviewed by a non-author classmate — not done
      in this environment; flagged here rather than silently skipped

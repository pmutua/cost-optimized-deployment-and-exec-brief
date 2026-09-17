# AfyaPlus Triage API — Executive One-Pager

*Five-minute read. Full detail: `../cost/cost_model.md`, `../levers/measurements.md`, `../memo/api_vs_selfhost.md`.*

## What this is

An AI-assisted triage service for AfyaPlus clinic coordinators: a patient
message comes in, the system suggests an urgency level and safe,
non-diagnostic next steps. It runs today on OpenAI's `gpt-4o-mini`
behind our own secured API — we are not running our own AI hardware.

## What it costs

| | Cost per 1,000 requests |
|---|---|
| **Today's traffic** (~2,000 requests/day) | **$1.66** |
| **10x traffic spike** (~20,000 requests/day) | **$0.31** |

Cost per 1,000 *drops* under a spike, not rises — the fixed costs (the
server, the light ops overhead) get spread across far more requests,
while the per-request AI cost stays flat. Full breakdown and every rate
used: `../cost/cost_model.md`.

## The spike plan

If traffic jumps 10x, the system scales from 1 server instance to 4
automatically — no manual intervention needed, and cost per 1,000
requests actually improves, as shown above. The 10x scenario is modelled,
not guessed: see `../cost/cost_model.py`.

## Two cost levers, already built and measured

**1. Caching common questions.** When the same question text comes in
again within 5 minutes, we answer instantly from memory instead of
calling the AI model again. Measured on a 20-request test batch: **40% of
requests were served from cache**, cutting the AI portion of the bill by
roughly the same share. *Safety rule:* anything flagged urgent is never
served from cache — those always get a fresh answer.

**2. Batching routine requests.** When several requests arrive close
together, we group them into one AI call instead of many, sharing the
fixed "instructions" portion of the request. Measured saving: **~20% cost
reduction** on the AI portion during busy periods. *Trade-off, stated
plainly:* in our test batch, the slowest 5% of requests waited up to
**2.55 seconds** for a response — this "slowest 5%" figure is what
engineers call **p95** (95% of requests were faster than this; only the
worst 5% were slower). That is acceptable for routine queue traffic, and
is exactly why this lever never runs for the most urgent cases.

## One risk, and how we're handling it

**Risk:** both cost levers above trade a small amount of *speed* or
*freshness* for cost savings. If misapplied to an urgent case, a delayed
or stale answer could matter clinically.

**Mitigation:** both levers already have an urgent-case bypass built in —
high-urgency messages always get a fresh, unbatched, immediate answer.
This is enforced in code today, not a future to-do.

## Budget controls

A $20/month spend ceiling is configured (Azure and AWS budget alert
configs included in the repo), with automatic warnings at 80% of actual
spend and 100% of forecasted spend. We do not yet have a paid cloud
account to activate these live — the configs are ready to apply the
moment one exists; local run evidence is included in the meantime.

## Build vs. buy: should we run our own AI hardware?

No, not at current scale. Running our own model on our own hardware only
becomes cheaper than the API once traffic is roughly **11x today's spike
scenario** — effectively a much larger platform than a clinic pilot. Full
reasoning: `../memo/api_vs_selfhost.md`.

## Go / No-Go

**Go**, with three conditions:

1. **Budget alert activated** within 30 days of the first paid cloud
   account being available (config is ready now).
2. **Urgent-case bypass stays enforced** for both cost levers — this is
   a safety condition, not a performance one.
3. **Re-cost before scaling past the 10x spike scenario** — the model
   above is validated to 20,000 requests/day; sustained growth beyond
   that should get a fresh look, not an assumption that the same numbers
   still hold.

## Fallbacks used in this packet

No Redis (in-memory cache instead), no paid cloud account (config-as-code
plus local run evidence instead of a live console), no GPU (self-host
memo uses footnoted estimates, clearly labelled, not measurements). Full
list: top-level `README.md`.

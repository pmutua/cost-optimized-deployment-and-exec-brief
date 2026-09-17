"""cost_model.py - Deliverable 1: unit economics for the AfyaPlus triage
API (api/app/triage_model.py's single gpt-4o-mini call behind POST
/triage).

Every rate below is a named constant with a footnote in its comment,
sourced or explicitly labelled as an assumption -- see cost_model.md for
the same numbers written out for a non-engineer, and for the footnote
list in one place. Nothing here is invented silently: if a number isn't
footnoted, it's a bug in this file, not a deliberate omission.

Run it:
    python cost_model.py
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Token rates -- gpt-4o-mini, OpenAI API list price.
# Footnote [1]: https://openai.com/api/pricing/ , accessed 2026-09-17.
# Re-check before relying on this for a real budget; OpenAI has changed
# gpt-4o-mini pricing before and may again.
# ---------------------------------------------------------------------------
INPUT_RATE_PER_1M_TOKENS = 0.150   # USD, [1]
OUTPUT_RATE_PER_1M_TOKENS = 0.600  # USD, [1]

# ---------------------------------------------------------------------------
# Token counts per request.
# Footnote [2]: SYSTEM_PROMPT in api/app/triage_model.py is 143 tokens by
# tiktoken's cl100k_base encoding (counted directly, not estimated). Patient
# message length is assumed at 60 tokens -- roughly two sentences of
# plain-language symptom description, in line with the five fixture
# messages used for the lever measurements in ../levers/measurements.md.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TOKENS = 143   # [2], counted
AVG_PATIENT_MESSAGE_TOKENS = 60  # [2], assumption
AVG_PROMPT_TOKENS = SYSTEM_PROMPT_TOKENS + AVG_PATIENT_MESSAGE_TOKENS  # 203

# Footnote [3]: api/app/triage_model.py caps max_tokens=120. Assumed actual
# completion averages 60% of the cap -- the response schema is a short JSON
# object ({"urgency": ..., "advice": "<one or two short sentences>"}), which
# rarely needs the full 120 tokens. Not measured against a live model in
# this environment (no paid key committed to this repo); treat as an
# assumption to replace with a measured average once real traffic exists.
AVG_COMPLETION_TOKENS = 72  # [3], assumption: 0.6 * 120

# ---------------------------------------------------------------------------
# Infra: one container instance running api/Dockerfile's image, sized for
# the docker-compose deploy in ../deploy/docker-compose.cost.yml.
# Footnote [4]: Azure Container Apps, 0.5 vCPU / 1 GiB, consumption plan,
# priced from the Azure Pricing Calculator (East US, accessed 2026-09-17)
# assuming the instance is kept warm 24/7 rather than scaling to zero, so
# this is a conservative (higher) number: ~$13.50/month compute + ~$1.50/
# month for the minimum always-on vCPU-second/GiB-second floor.
# Footnote [5]: one instance is assumed to comfortably serve 5,000
# requests/day before p95 latency or the in-process rate limiter
# (api/app/rate_limit.py, 10 req/60s/user) force horizontal scaling -- an
# assumption pending a real load test, not a measured ceiling.
# ---------------------------------------------------------------------------
INSTANCE_MONTHLY_COST_USD = 15.00       # [4]
INSTANCE_CAPACITY_REQ_PER_DAY = 5000    # [5]

# ---------------------------------------------------------------------------
# People/ops line: on-call + budget-review time, not zero just because no
# cloud bill exists yet.
# Footnote [6]: 2 hours/month at a blended $40/hr contractor/ops rate,
# covering budget alert triage, key rotation, and dependency patching.
# Both the hours and the rate are placeholders footnoted here so Finance
# can swap in real numbers without hunting through code.
# ---------------------------------------------------------------------------
OPS_HOURS_PER_MONTH = 2.0     # [6]
OPS_HOURLY_RATE_USD = 40.0    # [6]
OPS_MONTHLY_COST_USD = OPS_HOURS_PER_MONTH * OPS_HOURLY_RATE_USD  # 80.00

# ---------------------------------------------------------------------------
# Traffic assumptions.
# Footnote [7]: baseline sized for a small clinic network (roughly the
# AfyaPlus pilot: a handful of coordinators triaging patient messages
# through the day) -- an assumption, not a measured production figure. The
# capstone brief's "10x spike" is applied directly to this baseline.
# ---------------------------------------------------------------------------
BASELINE_REQ_PER_DAY = 2000  # [7]
SPIKE_MULTIPLIER = 10
DAYS_PER_MONTH = 30


@dataclass(frozen=True)
class CostBreakdown:
    label: str
    requests_per_day: int
    monthly_requests: int
    instances_needed: int
    token_cost_per_request: float
    infra_cost_per_request: float
    ops_cost_per_request: float

    @property
    def total_cost_per_request(self) -> float:
        return self.token_cost_per_request + self.infra_cost_per_request + self.ops_cost_per_request

    @property
    def cost_per_1k(self) -> float:
        return self.total_cost_per_request * 1000


def token_cost_per_request(
    prompt_tokens: int = AVG_PROMPT_TOKENS,
    completion_tokens: int = AVG_COMPLETION_TOKENS,
) -> float:
    """[1][2][3] -- the LLM line item only, no infra or ops."""
    prompt_cost = (prompt_tokens / 1_000_000) * INPUT_RATE_PER_1M_TOKENS
    completion_cost = (completion_tokens / 1_000_000) * OUTPUT_RATE_PER_1M_TOKENS
    return prompt_cost + completion_cost


def instances_needed(requests_per_day: int) -> int:
    """[5] -- whole instances, rounded up; you cannot run 0.4 of a container."""
    import math

    return max(1, math.ceil(requests_per_day / INSTANCE_CAPACITY_REQ_PER_DAY))


def build_breakdown(label: str, requests_per_day: int) -> CostBreakdown:
    monthly_requests = requests_per_day * DAYS_PER_MONTH
    n_instances = instances_needed(requests_per_day)
    infra_monthly = n_instances * INSTANCE_MONTHLY_COST_USD
    tok_cost = token_cost_per_request()
    infra_cost = infra_monthly / monthly_requests
    ops_cost = OPS_MONTHLY_COST_USD / monthly_requests
    return CostBreakdown(
        label=label,
        requests_per_day=requests_per_day,
        monthly_requests=monthly_requests,
        instances_needed=n_instances,
        token_cost_per_request=tok_cost,
        infra_cost_per_request=infra_cost,
        ops_cost_per_request=ops_cost,
    )


def baseline_and_spike() -> tuple[CostBreakdown, CostBreakdown]:
    baseline = build_breakdown("baseline", BASELINE_REQ_PER_DAY)
    spike = build_breakdown(f"{SPIKE_MULTIPLIER}x spike", BASELINE_REQ_PER_DAY * SPIKE_MULTIPLIER)
    return baseline, spike


def print_report() -> None:
    baseline, spike = baseline_and_spike()
    print(f"{'':22}{'baseline':>16}{'10x spike':>16}")
    print(f"{'requests/day':22}{baseline.requests_per_day:>16,}{spike.requests_per_day:>16,}")
    print(f"{'instances needed':22}{baseline.instances_needed:>16}{spike.instances_needed:>16}")
    print(f"{'token $/req':22}{baseline.token_cost_per_request:>16.6f}{spike.token_cost_per_request:>16.6f}")
    print(f"{'infra $/req':22}{baseline.infra_cost_per_request:>16.6f}{spike.infra_cost_per_request:>16.6f}")
    print(f"{'ops $/req':22}{baseline.ops_cost_per_request:>16.6f}{spike.ops_cost_per_request:>16.6f}")
    print(f"{'total $/req':22}{baseline.total_cost_per_request:>16.6f}{spike.total_cost_per_request:>16.6f}")
    print(f"{'$/1,000 requests':22}{baseline.cost_per_1k:>16.2f}{spike.cost_per_1k:>16.2f}")


if __name__ == "__main__":
    print_report()

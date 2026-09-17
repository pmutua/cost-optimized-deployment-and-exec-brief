"""sensitivity.py - Deliverable 1: how much does $/1k move when a single
footnoted assumption in cost_model.py changes?

Answers "what would change the number" for Finance before they ask it.
Each row flexes exactly one input around the baseline in build_breakdown()
and holds everything else fixed, so the swing shown is attributable to
that one assumption alone.

Run it:
    python sensitivity.py
"""

from __future__ import annotations

from cost_model import (
    AVG_COMPLETION_TOKENS,
    AVG_PROMPT_TOKENS,
    BASELINE_REQ_PER_DAY,
    DAYS_PER_MONTH,
    OPS_MONTHLY_COST_USD,
    instances_needed,
    token_cost_per_request,
    INSTANCE_MONTHLY_COST_USD,
)


def cost_per_1k(
    requests_per_day: int = BASELINE_REQ_PER_DAY,
    prompt_tokens: int = AVG_PROMPT_TOKENS,
    completion_tokens: int = AVG_COMPLETION_TOKENS,
    cache_hit_rate: float = 0.0,
) -> float:
    """Same arithmetic as cost_model.build_breakdown(), parameterised so
    sensitivity sweeps don't have to edit module-level constants.

    cache_hit_rate: fraction of requests served from ../levers/cache_triage.py
    instead of calling the model -- 0.0 reproduces the no-cache baseline.
    """
    monthly_requests = requests_per_day * DAYS_PER_MONTH
    n_instances = instances_needed(requests_per_day)
    infra_monthly = n_instances * INSTANCE_MONTHLY_COST_USD
    tok_cost = token_cost_per_request(prompt_tokens, completion_tokens) * (1 - cache_hit_rate)
    infra_cost = infra_monthly / monthly_requests
    ops_cost = OPS_MONTHLY_COST_USD / monthly_requests
    return (tok_cost + infra_cost + ops_cost) * 1000


def print_report() -> None:
    base = cost_per_1k()
    print(f"baseline $/1k = {base:.4f}\n")
    print(f"{'lever varied':20}{'value':<30}{'$/1k':>8}{'delta':>10}")

    scenarios = [
        ("completion tokens", "48 (0.4x cap)", cost_per_1k(completion_tokens=48)),
        ("completion tokens", "120 (full cap)", cost_per_1k(completion_tokens=120)),
        ("patient msg tokens", "30 (short)", cost_per_1k(prompt_tokens=143 + 30)),
        ("patient msg tokens", "150 (long)", cost_per_1k(prompt_tokens=143 + 150)),
        ("cache hit-rate", "40% (measured, see levers/)", cost_per_1k(cache_hit_rate=0.40)),
        ("cache hit-rate", "60% (optimistic)", cost_per_1k(cache_hit_rate=0.60)),
        ("traffic", f"{BASELINE_REQ_PER_DAY // 2}/day (half baseline)", cost_per_1k(requests_per_day=BASELINE_REQ_PER_DAY // 2)),
        ("traffic", f"{BASELINE_REQ_PER_DAY * 10}/day (10x spike)", cost_per_1k(requests_per_day=BASELINE_REQ_PER_DAY * 10)),
    ]
    for lever, value, result in scenarios:
        delta = result - base
        sign = "+" if delta >= 0 else ""
        print(f"{lever:20}{value:<30}{result:>8.4f}{sign}{delta:>9.4f}")


if __name__ == "__main__":
    print_report()

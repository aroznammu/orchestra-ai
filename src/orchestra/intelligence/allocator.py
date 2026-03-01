"""Dynamic budget allocator.

Continuously reallocates budget across platforms based on marginal return
curves. Operates within guardrails set by the bidding engine.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.intelligence.marginal_return import compute_marginal_returns

logger = structlog.get_logger("intelligence.allocator")

DEFAULT_MIN_ALLOCATION_PCT = 0.05  # No platform gets less than 5%
DEFAULT_MAX_ALLOCATION_PCT = 0.60  # No platform gets more than 60%
DEFAULT_MAX_SHIFT_PCT = 0.15       # Max 15% shift per rebalance cycle


class AllocationConstraints(BaseModel):
    min_per_platform_pct: float = DEFAULT_MIN_ALLOCATION_PCT
    max_per_platform_pct: float = DEFAULT_MAX_ALLOCATION_PCT
    max_shift_per_cycle_pct: float = DEFAULT_MAX_SHIFT_PCT
    locked_platforms: list[str] = Field(default_factory=list)


class AllocationResult(BaseModel):
    current_allocation: dict[str, float] = Field(default_factory=dict)
    recommended_allocation: dict[str, float] = Field(default_factory=dict)
    applied_allocation: dict[str, float] = Field(default_factory=dict)
    shifts: dict[str, float] = Field(default_factory=dict)
    constrained: bool = False
    reasoning: list[str] = Field(default_factory=list)


def reallocate_budget(
    total_budget: float,
    platform_data: list[dict[str, Any]],
    current_allocation: dict[str, float] | None = None,
    constraints: AllocationConstraints | None = None,
) -> AllocationResult:
    """Compute optimal budget allocation across platforms.

    Respects constraints: min/max per platform, max shift per cycle, locked platforms.
    """
    if constraints is None:
        constraints = AllocationConstraints()

    platforms = [d["platform"] for d in platform_data]
    n = len(platforms)
    if n == 0:
        return AllocationResult(reasoning=["No platforms to allocate to"])

    if current_allocation is None:
        equal_share = total_budget / n
        current_allocation = {p: equal_share for p in platforms}

    # Get unconstrained optimal from marginal returns
    analysis = compute_marginal_returns(platform_data, total_budget)
    raw_recommended = analysis.recommended_allocation

    # If no marginal data, use equal allocation
    if not raw_recommended:
        raw_recommended = {p: total_budget / n for p in platforms}

    # Ensure all platforms are represented
    for p in platforms:
        if p not in raw_recommended:
            raw_recommended[p] = total_budget / n

    # Apply constraints
    applied, reasoning, constrained = _apply_constraints(
        total_budget=total_budget,
        current=current_allocation,
        recommended=raw_recommended,
        constraints=constraints,
    )

    shifts = {
        p: round(applied.get(p, 0) - current_allocation.get(p, 0), 2)
        for p in platforms
    }

    logger.info(
        "budget_reallocated",
        total=total_budget,
        shifts=shifts,
        constrained=constrained,
    )

    return AllocationResult(
        current_allocation=current_allocation,
        recommended_allocation={k: round(v, 2) for k, v in raw_recommended.items()},
        applied_allocation=applied,
        shifts=shifts,
        constrained=constrained,
        reasoning=reasoning,
    )


def _apply_constraints(
    total_budget: float,
    current: dict[str, float],
    recommended: dict[str, float],
    constraints: AllocationConstraints,
) -> tuple[dict[str, float], list[str], bool]:
    """Apply guardrail constraints to the recommended allocation."""
    applied = dict(recommended)
    reasoning: list[str] = []
    constrained = False

    platforms = list(applied.keys())
    min_amount = total_budget * constraints.min_per_platform_pct
    max_amount = total_budget * constraints.max_per_platform_pct
    max_shift = total_budget * constraints.max_shift_per_cycle_pct

    for p in platforms:
        # Locked platforms keep current allocation
        if p in constraints.locked_platforms:
            applied[p] = current.get(p, 0)
            reasoning.append(f"{p}: locked at ${applied[p]:.2f}")
            constrained = True
            continue

        # Min/max bounds
        if applied[p] < min_amount:
            applied[p] = min_amount
            reasoning.append(f"{p}: raised to minimum ${min_amount:.2f}")
            constrained = True
        elif applied[p] > max_amount:
            applied[p] = max_amount
            reasoning.append(f"{p}: capped at maximum ${max_amount:.2f}")
            constrained = True

        # Max shift per cycle
        current_amount = current.get(p, 0)
        shift = applied[p] - current_amount
        if abs(shift) > max_shift:
            capped_shift = max_shift if shift > 0 else -max_shift
            applied[p] = current_amount + capped_shift
            reasoning.append(
                f"{p}: shift capped from ${shift:.2f} to ${capped_shift:.2f}"
            )
            constrained = True

    # Normalize to total budget
    total_applied = sum(applied.values())
    if total_applied > 0 and abs(total_applied - total_budget) > 0.01:
        scale = total_budget / total_applied
        applied = {p: round(v * scale, 2) for p, v in applied.items()}

    return applied, reasoning, constrained

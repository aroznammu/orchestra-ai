"""Marginal return analysis.

Compares the marginal return per dollar across all connected platforms.
Answers: "If I have $1 more to spend, which platform gives the best return?"
"""

import math
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("intelligence.marginal_return")


class MarginalReturn(BaseModel):
    """Marginal return estimate for a single platform."""

    platform: str
    current_spend: float
    current_return: float
    marginal_return_per_dollar: float
    diminishing_factor: float
    recommended_increment: float
    confidence: float


class MarginalAnalysis(BaseModel):
    """Cross-platform marginal return comparison."""

    platforms: list[MarginalReturn] = Field(default_factory=list)
    best_marginal_platform: str = ""
    recommended_allocation: dict[str, float] = Field(default_factory=dict)
    total_available_budget: float = 0.0


def compute_marginal_returns(
    platform_data: list[dict[str, Any]],
    additional_budget: float = 100.0,
) -> MarginalAnalysis:
    """Compute marginal returns across platforms.

    Uses a log-based diminishing returns model:
      Return(spend) = k * ln(1 + spend/scale)

    where k and scale are estimated from historical data.
    """
    marginals: list[MarginalReturn] = []

    for data in platform_data:
        platform = data["platform"]
        spend = data.get("spend", 0.0)
        revenue = data.get("revenue", 0.0)

        if spend <= 0:
            marginals.append(MarginalReturn(
                platform=platform,
                current_spend=0.0,
                current_return=0.0,
                marginal_return_per_dollar=0.0,
                diminishing_factor=1.0,
                recommended_increment=additional_budget * 0.1,
                confidence=0.0,
            ))
            continue

        # Estimate diminishing returns curve parameters
        roi = revenue / spend
        scale = _estimate_scale(spend, roi)
        k = revenue / math.log1p(spend / scale) if math.log1p(spend / scale) > 0 else revenue

        # Marginal return = d/d(spend)[k * ln(1 + spend/scale)] = k / (spend + scale)
        marginal = k / (spend + scale) if (spend + scale) > 0 else 0.0

        # Diminishing factor: how much has returns diminished vs. initial
        initial_marginal = k / scale if scale > 0 else 0.0
        diminishing = marginal / initial_marginal if initial_marginal > 0 else 0.0

        # Confidence based on data volume
        data_points = data.get("data_points", 1)
        confidence = min(data_points / 30.0, 1.0)

        marginals.append(MarginalReturn(
            platform=platform,
            current_spend=round(spend, 2),
            current_return=round(revenue, 2),
            marginal_return_per_dollar=round(marginal, 4),
            diminishing_factor=round(diminishing, 3),
            recommended_increment=round(_optimal_increment(marginal, additional_budget), 2),
            confidence=round(confidence, 3),
        ))

    # Sort by marginal return
    marginals.sort(key=lambda m: m.marginal_return_per_dollar, reverse=True)

    # Allocate additional budget proportional to marginal returns
    allocation = _allocate_by_marginal(marginals, additional_budget)

    return MarginalAnalysis(
        platforms=marginals,
        best_marginal_platform=marginals[0].platform if marginals else "",
        recommended_allocation=allocation,
        total_available_budget=additional_budget,
    )


def _estimate_scale(spend: float, roi: float) -> float:
    """Estimate the scale parameter for the diminishing returns curve.

    Higher scale = slower diminishing (platform has more headroom).
    """
    base_scale = spend * 2.0
    if roi > 3.0:
        return base_scale * 1.5  # High ROI => more headroom
    elif roi > 1.0:
        return base_scale
    else:
        return base_scale * 0.5  # Low ROI => diminishing faster


def _optimal_increment(marginal_return: float, budget: float) -> float:
    """Calculate optimal spend increment based on marginal return."""
    if marginal_return <= 0:
        return 0.0
    # Spend more where marginal return is higher
    return min(budget * min(marginal_return, 1.0), budget * 0.5)


def _allocate_by_marginal(
    marginals: list[MarginalReturn],
    budget: float,
) -> dict[str, float]:
    """Allocate budget proportional to marginal returns."""
    positive = [m for m in marginals if m.marginal_return_per_dollar > 0]
    if not positive:
        return {}

    total_marginal = sum(m.marginal_return_per_dollar for m in positive)
    if total_marginal == 0:
        equal = budget / len(positive)
        return {m.platform: round(equal, 2) for m in positive}

    return {
        m.platform: round(budget * m.marginal_return_per_dollar / total_marginal, 2)
        for m in positive
    }

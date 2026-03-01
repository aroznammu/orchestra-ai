"""Channel saturation detection.

Detects when a platform is hitting diminishing returns --
additional spend yields progressively less engagement/revenue.
"""

import math
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("intelligence.saturation")


class SaturationLevel(BaseModel):
    """Saturation analysis for a single platform."""

    platform: str
    saturation_pct: float = 0.0   # 0-100: how saturated
    headroom_pct: float = 100.0   # remaining growth potential
    trend: str = "stable"         # growing, stable, saturating, saturated
    spend_efficiency: float = 1.0 # current $ efficiency vs. baseline
    recommended_action: str = "maintain"
    data_points: int = 0


class SaturationAnalysis(BaseModel):
    """Cross-platform saturation overview."""

    platforms: list[SaturationLevel] = Field(default_factory=list)
    most_saturated: str = ""
    most_headroom: str = ""
    reallocation_suggested: bool = False


def detect_saturation(
    platform_history: list[dict[str, Any]],
) -> SaturationAnalysis:
    """Analyze saturation across all platforms.

    Each entry in platform_history should contain:
      platform, spend_history (list of floats), return_history (list of floats)
    """
    levels: list[SaturationLevel] = []

    for entry in platform_history:
        platform = entry["platform"]
        spends = entry.get("spend_history", [])
        returns = entry.get("return_history", [])

        level = _analyze_platform(platform, spends, returns)
        levels.append(level)

    # Identify extremes
    sorted_by_sat = sorted(levels, key=lambda l: l.saturation_pct, reverse=True)
    most_sat = sorted_by_sat[0].platform if sorted_by_sat else ""
    most_head = sorted_by_sat[-1].platform if sorted_by_sat else ""

    # Suggest reallocation if any platform > 70% saturated
    realloc = any(l.saturation_pct > 70 for l in levels)

    return SaturationAnalysis(
        platforms=levels,
        most_saturated=most_sat,
        most_headroom=most_head,
        reallocation_suggested=realloc,
    )


def _analyze_platform(
    platform: str,
    spends: list[float],
    returns: list[float],
) -> SaturationLevel:
    """Analyze saturation for a single platform."""
    n = min(len(spends), len(returns))

    if n < 3:
        return SaturationLevel(
            platform=platform,
            saturation_pct=0.0,
            headroom_pct=100.0,
            trend="insufficient_data",
            recommended_action="collect_more_data",
            data_points=n,
        )

    # Compute marginal returns over time
    marginal_returns: list[float] = []
    for i in range(1, n):
        d_spend = spends[i] - spends[i - 1]
        d_return = returns[i] - returns[i - 1]
        if d_spend > 0:
            marginal_returns.append(d_return / d_spend)

    if not marginal_returns:
        return SaturationLevel(platform=platform, data_points=n)

    # Saturation = how much marginal returns have declined
    initial_mr = marginal_returns[0] if marginal_returns[0] > 0 else 0.01
    current_mr = marginal_returns[-1]

    decline_ratio = 1.0 - (current_mr / initial_mr) if initial_mr > 0 else 0.0
    saturation_pct = max(min(decline_ratio * 100, 100), 0)

    # Trend detection
    if len(marginal_returns) >= 3:
        recent = marginal_returns[-3:]
        trend_slope = (recent[-1] - recent[0]) / len(recent)
        if trend_slope > 0.01:
            trend = "growing"
        elif trend_slope < -0.05:
            trend = "saturating"
        elif saturation_pct > 80:
            trend = "saturated"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Current efficiency
    latest_spend = spends[-1]
    latest_return = returns[-1]
    efficiency = latest_return / latest_spend if latest_spend > 0 else 0.0

    # Recommendation
    if saturation_pct > 80:
        action = "reduce_spend"
    elif saturation_pct > 60:
        action = "hold_steady"
    elif saturation_pct > 30:
        action = "maintain"
    else:
        action = "increase_spend"

    return SaturationLevel(
        platform=platform,
        saturation_pct=round(saturation_pct, 1),
        headroom_pct=round(100 - saturation_pct, 1),
        trend=trend,
        spend_efficiency=round(efficiency, 4),
        recommended_action=action,
        data_points=n,
    )


def estimate_optimal_spend(
    current_spend: float,
    saturation_pct: float,
) -> float:
    """Estimate optimal spend level given current saturation.

    Uses an inverse-saturation curve: optimal = current * (1 - saturation/200)
    """
    if saturation_pct >= 95:
        return current_spend * 0.5

    factor = 1.0 - (saturation_pct / 200.0)
    return round(current_spend * max(factor, 0.3), 2)

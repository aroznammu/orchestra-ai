"""Cross-platform ROI normalization.

Normalizes ROI across platforms into a unified metric so that
$1 spent on Twitter can be compared to $1 spent on LinkedIn.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("intelligence.cross_platform")

# Platform-specific cost factors (CPM baselines for normalization)
PLATFORM_CPM_BASELINES: dict[str, float] = {
    "twitter": 6.50,
    "youtube": 9.00,
    "instagram": 8.00,
    "facebook": 7.50,
    "linkedin": 12.00,
    "tiktok": 5.00,
    "pinterest": 4.50,
    "snapchat": 5.50,
    "google_ads": 10.00,
}

# Value multipliers per engagement type (platform-adjusted)
ENGAGEMENT_VALUE: dict[str, float] = {
    "impression": 0.001,
    "view": 0.003,
    "click": 0.05,
    "like": 0.01,
    "comment": 0.08,
    "share": 0.15,
    "save": 0.10,
    "follow": 0.25,
    "conversion": 1.00,
}


class PlatformROI(BaseModel):
    """ROI data for a single platform."""

    platform: str
    spend: float = 0.0
    revenue: float = 0.0
    raw_roi: float = 0.0
    normalized_roi: float = 0.0
    effective_cpm: float = 0.0
    engagement_value: float = 0.0
    impressions: int = 0
    engagements: dict[str, int] = Field(default_factory=dict)


class CrossPlatformROI(BaseModel):
    """Unified ROI view across all platforms."""

    platforms: list[PlatformROI] = Field(default_factory=list)
    total_spend: float = 0.0
    total_revenue: float = 0.0
    blended_roi: float = 0.0
    best_platform: str = ""
    worst_platform: str = ""
    reallocation_opportunity: float = 0.0


def compute_platform_roi(
    platform: str,
    spend: float,
    revenue: float,
    impressions: int,
    engagements: dict[str, int],
) -> PlatformROI:
    """Compute normalized ROI for a single platform."""
    raw_roi = (revenue - spend) / spend if spend > 0 else 0.0

    # Effective CPM
    effective_cpm = (spend / impressions * 1000) if impressions > 0 else 0.0

    # Baseline-normalized CPM
    baseline_cpm = PLATFORM_CPM_BASELINES.get(platform, 7.0)
    cpm_efficiency = baseline_cpm / effective_cpm if effective_cpm > 0 else 1.0

    # Total engagement value
    eng_value = sum(
        count * ENGAGEMENT_VALUE.get(etype, 0.01)
        for etype, count in engagements.items()
    )

    # Normalized ROI: factors in both revenue ROI and engagement efficiency
    normalized_roi = raw_roi * 0.6 + (eng_value / max(spend, 1.0)) * 0.4

    return PlatformROI(
        platform=platform,
        spend=round(spend, 2),
        revenue=round(revenue, 2),
        raw_roi=round(raw_roi, 4),
        normalized_roi=round(normalized_roi, 4),
        effective_cpm=round(effective_cpm, 2),
        engagement_value=round(eng_value, 2),
        impressions=impressions,
        engagements=engagements,
    )


def compute_cross_platform_roi(
    platform_data: list[dict[str, Any]],
) -> CrossPlatformROI:
    """Aggregate ROI across all platforms into a unified view.

    Each entry in platform_data should have:
      platform, spend, revenue, impressions, engagements (dict)
    """
    platform_rois: list[PlatformROI] = []

    for data in platform_data:
        roi = compute_platform_roi(
            platform=data["platform"],
            spend=data.get("spend", 0.0),
            revenue=data.get("revenue", 0.0),
            impressions=data.get("impressions", 0),
            engagements=data.get("engagements", {}),
        )
        platform_rois.append(roi)

    total_spend = sum(p.spend for p in platform_rois)
    total_revenue = sum(p.revenue for p in platform_rois)
    blended_roi = (total_revenue - total_spend) / total_spend if total_spend > 0 else 0.0

    # Identify best/worst
    sorted_by_roi = sorted(platform_rois, key=lambda p: p.normalized_roi, reverse=True)
    best = sorted_by_roi[0].platform if sorted_by_roi else ""
    worst = sorted_by_roi[-1].platform if sorted_by_roi else ""

    # Estimate reallocation opportunity
    realloc = _estimate_reallocation_gain(platform_rois, total_spend)

    return CrossPlatformROI(
        platforms=platform_rois,
        total_spend=round(total_spend, 2),
        total_revenue=round(total_revenue, 2),
        blended_roi=round(blended_roi, 4),
        best_platform=best,
        worst_platform=worst,
        reallocation_opportunity=round(realloc, 2),
    )


def _estimate_reallocation_gain(
    platforms: list[PlatformROI],
    total_spend: float,
) -> float:
    """Estimate potential gain from optimal budget reallocation.

    Compares current allocation vs. proportional-to-ROI allocation.
    """
    if not platforms or total_spend == 0:
        return 0.0

    current_revenue = sum(p.revenue for p in platforms)

    # Hypothetical: allocate proportional to normalized ROI
    total_norm_roi = sum(max(p.normalized_roi, 0.01) for p in platforms)
    if total_norm_roi == 0:
        return 0.0

    hypothetical_revenue = 0.0
    for p in platforms:
        ideal_spend = total_spend * max(p.normalized_roi, 0.01) / total_norm_roi
        if p.spend > 0:
            revenue_per_dollar = p.revenue / p.spend
            hypothetical_revenue += ideal_spend * revenue_per_dollar

    return max(hypothetical_revenue - current_revenue, 0.0)

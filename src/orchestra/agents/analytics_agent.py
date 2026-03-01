"""Analytics Agent -- cross-platform metrics aggregation and insights.

Collects data from connected platforms, normalizes metrics,
identifies trends, and generates actionable recommendations.
"""

from typing import Any

import structlog

from orchestra.agents.contracts import AnalyticsRequest, AnalyticsResult
from orchestra.agents.trace import ExecutionTrace, TraceTimer

logger = structlog.get_logger("agent.analytics")

ENGAGEMENT_BENCHMARKS = {
    "twitter": {"engagement_rate": 0.028, "click_rate": 0.009},
    "youtube": {"engagement_rate": 0.05, "click_rate": 0.012},
    "instagram": {"engagement_rate": 0.06, "click_rate": 0.008},
    "facebook": {"engagement_rate": 0.035, "click_rate": 0.01},
    "linkedin": {"engagement_rate": 0.038, "click_rate": 0.015},
    "tiktok": {"engagement_rate": 0.08, "click_rate": 0.005},
    "pinterest": {"engagement_rate": 0.02, "click_rate": 0.025},
}


async def run_analytics(
    request: AnalyticsRequest,
    trace: ExecutionTrace,
) -> AnalyticsResult:
    """Aggregate analytics across platforms and generate insights."""
    with TraceTimer() as timer:
        platforms = request.platforms or list(ENGAGEMENT_BENCHMARKS.keys())

        # Build per-platform metrics (placeholder -- real impl queries each connector)
        platform_metrics: dict[str, Any] = {}
        for platform in platforms:
            platform_metrics[platform] = {
                "impressions": 0,
                "engagement": 0,
                "clicks": 0,
                "engagement_rate": 0.0,
                "click_rate": 0.0,
                "spend": 0.0,
                "roi": 0.0,
                "benchmark": ENGAGEMENT_BENCHMARKS.get(platform, {}),
            }

        # Cross-platform aggregation
        totals = _aggregate_metrics(platform_metrics)

        # Generate insights
        insights = _generate_insights(platform_metrics, totals)

        # Recommendations
        recommendations = _generate_recommendations(platform_metrics)

    result = AnalyticsResult(
        metrics=totals,
        insights=insights,
        recommendations=recommendations,
        cross_platform_summary={
            "total_platforms": len(platforms),
            "total_impressions": totals.get("total_impressions", 0),
            "total_engagement": totals.get("total_engagement", 0),
            "average_engagement_rate": totals.get("average_engagement_rate", 0.0),
            "total_spend": totals.get("total_spend", 0.0),
            "best_platform": _find_best_platform(platform_metrics),
            "platforms": platform_metrics,
        },
    )

    trace.log(
        agent="analytics",
        action="cross_platform_analytics",
        input_summary=f"platforms={platforms}, days={request.date_range_days}",
        output_summary=f"insights={len(insights)}, recommendations={len(recommendations)}",
        confidence=0.5,
        duration_ms=timer.duration_ms,
    )

    return result


def _aggregate_metrics(platform_metrics: dict[str, Any]) -> dict[str, Any]:
    total_impressions = sum(m.get("impressions", 0) for m in platform_metrics.values())
    total_engagement = sum(m.get("engagement", 0) for m in platform_metrics.values())
    total_clicks = sum(m.get("clicks", 0) for m in platform_metrics.values())
    total_spend = sum(m.get("spend", 0.0) for m in platform_metrics.values())

    avg_er = (
        total_engagement / total_impressions * 100 if total_impressions > 0 else 0.0
    )

    return {
        "total_impressions": total_impressions,
        "total_engagement": total_engagement,
        "total_clicks": total_clicks,
        "total_spend": round(total_spend, 2),
        "average_engagement_rate": round(avg_er, 4),
        "cost_per_engagement": (
            round(total_spend / total_engagement, 4) if total_engagement > 0 else 0.0
        ),
        "cost_per_click": (
            round(total_spend / total_clicks, 4) if total_clicks > 0 else 0.0
        ),
    }


def _generate_insights(
    platform_metrics: dict[str, Any],
    totals: dict[str, Any],
) -> list[str]:
    insights: list[str] = []

    if not any(m.get("impressions", 0) > 0 for m in platform_metrics.values()):
        insights.append(
            "No engagement data yet. Connect platforms and start posting "
            "to begin receiving analytics insights."
        )
        return insights

    for platform, metrics in platform_metrics.items():
        benchmark = metrics.get("benchmark", {})
        er = metrics.get("engagement_rate", 0.0)
        bench_er = benchmark.get("engagement_rate", 0.0)

        if er > bench_er * 1.5 and er > 0:
            insights.append(
                f"{platform.title()} engagement rate ({er:.2%}) is significantly "
                f"above industry benchmark ({bench_er:.2%}). "
                f"Consider increasing investment."
            )
        elif 0 < er < bench_er * 0.5:
            insights.append(
                f"{platform.title()} engagement rate ({er:.2%}) is below "
                f"benchmark ({bench_er:.2%}). "
                f"Review content strategy for this platform."
            )

    return insights


def _generate_recommendations(platform_metrics: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []

    active_platforms = [
        p for p, m in platform_metrics.items() if m.get("impressions", 0) > 0
    ]

    if not active_platforms:
        recommendations.append(
            "Start by connecting and posting to at least 2-3 platforms "
            "to enable cross-platform optimization."
        )
    elif len(active_platforms) < 3:
        recommendations.append(
            f"Only {len(active_platforms)} platform(s) active. "
            f"Expanding to 3+ platforms enables better cross-platform insights."
        )

    return recommendations


def _find_best_platform(platform_metrics: dict[str, Any]) -> str:
    best = ""
    best_er = -1.0
    for platform, metrics in platform_metrics.items():
        er = metrics.get("engagement_rate", 0.0)
        if er > best_er:
            best_er = er
            best = platform
    return best or "none"

"""Analytics Agent -- cross-platform metrics aggregation and insights.

Collects data from connected platforms, normalizes metrics,
identifies trends, and generates actionable recommendations.
"""

import uuid
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
    # Programmatic CTV / DSP (illustrative benchmarks for VCR + eCPM)
    "ctv": {
        "engagement_rate": 0.055,
        "click_rate": 0.004,
        "video_completion_rate": 0.915,
        "effective_cpm": 24.5,
    },
}


async def run_analytics(
    request: AnalyticsRequest,
    trace: ExecutionTrace,
    *,
    tenant_id: str | None = None,
) -> AnalyticsResult:
    """Aggregate analytics across platforms and generate insights.

    When tenant_id is provided, queries PlatformConnection records and
    fetches real metrics from each connector.  Falls back to zeros when
    a connector is unreachable or the tenant has no connections.
    """
    with TraceTimer() as timer:
        platforms = request.platforms or list(ENGAGEMENT_BENCHMARKS.keys())

        real_data: dict[str, Any] = {}
        if tenant_id:
            try:
                real_data = await _fetch_real_platform_data(tenant_id, platforms)
            except Exception as e:
                logger.warning("real_data_fetch_failed", error=str(e))

        platform_metrics: dict[str, Any] = {}
        for platform in platforms:
            live = real_data.get(platform, {})
            bench = ENGAGEMENT_BENCHMARKS.get(platform, {})
            platform_metrics[platform] = {
                "impressions": live.get("impressions", 0),
                "engagement": live.get("engagement", 0),
                "clicks": live.get("clicks", 0),
                "engagement_rate": live.get("engagement_rate", 0.0),
                "click_rate": live.get("click_rate", 0.0),
                "spend": live.get("spend", 0.0),
                "roi": live.get("roi", 0.0),
                "video_completion_rate": live.get(
                    "video_completion_rate",
                    bench.get("video_completion_rate", 0.0),
                ),
                "effective_cpm": live.get(
                    "effective_cpm",
                    bench.get("effective_cpm", 0.0),
                ),
                "benchmark": bench,
            }

        for _name, row in platform_metrics.items():
            row.setdefault("video_completion_rate", 0.0)
            row.setdefault("effective_cpm", 0.0)

        ctv_b = ENGAGEMENT_BENCHMARKS.get("ctv", {})
        if request.include_ctv_dashboard_preview:
            existing_ctv = platform_metrics.get("ctv")
            if existing_ctv is None or (
                existing_ctv.get("impressions", 0) == 0 and existing_ctv.get("spend", 0) == 0
            ):
                platform_metrics["ctv"] = {
                    "impressions": 185_000,
                    "engagement": 11_000,
                    "clicks": 720,
                    "engagement_rate": ctv_b.get("engagement_rate", 0.055),
                    "click_rate": ctv_b.get("click_rate", 0.004),
                    "spend": 4280.0,
                    "roi": 1.42,
                    "video_completion_rate": ctv_b.get("video_completion_rate", 0.915),
                    "effective_cpm": ctv_b.get("effective_cpm", 24.5),
                    "benchmark": ctv_b,
                }
            else:
                if existing_ctv.get("video_completion_rate", 0) == 0:
                    existing_ctv["video_completion_rate"] = ctv_b.get("video_completion_rate", 0.915)
                if existing_ctv.get("effective_cpm", 0) == 0:
                    existing_ctv["effective_cpm"] = ctv_b.get("effective_cpm", 24.5)

        totals = _aggregate_metrics(platform_metrics)
        insights = _generate_insights(platform_metrics, totals)
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


# ---------------------------------------------------------------------------
# Real platform data fetching
# ---------------------------------------------------------------------------

async def _fetch_real_platform_data(
    tenant_id: str | None,
    platforms: list[str],
) -> dict[str, dict[str, Any]]:
    """Query PlatformConnection records and call each connector's get_analytics.

    Returns a dict mapping platform name -> aggregated metric dict.
    Falls back gracefully to empty dicts on any failure.
    """
    if not tenant_id:
        return {}

    try:
        from sqlalchemy import select
        from orchestra.db.models import PlatformConnection, PlatformType, CampaignPost
        from orchestra.db.session import async_session_factory
        from orchestra.security.encryption import decrypt_token
        from orchestra.platforms import get_platform

        tenant_uuid = uuid.UUID(tenant_id)
        platform_data: dict[str, dict[str, Any]] = {}

        async with async_session_factory() as session:
            result = await session.execute(
                select(PlatformConnection).where(
                    PlatformConnection.tenant_id == tenant_uuid,
                    PlatformConnection.is_active == True,  # noqa: E712
                )
            )
            connections = result.scalars().all()

            conn_by_platform = {c.platform.value: c for c in connections}

            for platform_name in platforms:
                conn = conn_by_platform.get(platform_name)
                if not conn:
                    continue

                try:
                    access_token = decrypt_token(conn.access_token_encrypted)
                    connector = get_platform(PlatformType(platform_name))

                    posts_result = await session.execute(
                        select(CampaignPost).where(
                            CampaignPost.platform == PlatformType(platform_name),
                        ).limit(20)
                    )
                    posts = posts_result.scalars().all()

                    agg: dict[str, Any] = {
                        "impressions": 0, "engagement": 0, "clicks": 0,
                        "spend": 0.0, "engagement_rate": 0.0, "click_rate": 0.0,
                        "roi": 0.0,
                    }

                    for post in posts:
                        if not post.platform_post_id:
                            continue
                        try:
                            analytics = await connector.get_analytics(
                                post.platform_post_id, access_token,
                            )
                            m = analytics.metrics
                            agg["impressions"] += m.impressions
                            agg["engagement"] += m.likes + m.comments + m.shares
                            agg["clicks"] += m.clicks
                        except Exception as e:
                            logger.debug(
                                "post_analytics_fetch_failed",
                                platform=platform_name,
                                post_id=post.platform_post_id,
                                error=str(e),
                            )

                    if agg["impressions"] > 0:
                        agg["engagement_rate"] = round(
                            agg["engagement"] / agg["impressions"], 4
                        )
                        agg["click_rate"] = round(
                            agg["clicks"] / agg["impressions"], 4
                        )

                    platform_data[platform_name] = agg

                except Exception as e:
                    logger.warning(
                        "platform_analytics_failed",
                        platform=platform_name,
                        error=str(e),
                    )

        return platform_data

    except Exception as e:
        logger.warning("analytics_data_fetch_failed", error=str(e))
        return {}


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

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

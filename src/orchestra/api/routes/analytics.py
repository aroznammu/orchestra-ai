"""Cross-platform analytics endpoints."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from orchestra.api.deps import CurrentUser, DbSession
from orchestra.db.models import Campaign, CampaignPost, PlatformConnection, PlatformType
from orchestra.agents.analytics_agent import run_analytics, ENGAGEMENT_BENCHMARKS
from orchestra.agents.contracts import AnalyticsRequest
from orchestra.agents.trace import ExecutionTrace

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = structlog.get_logger("api.analytics")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class PlatformMetrics(BaseModel):
    impressions: int = 0
    engagement: int = 0
    clicks: int = 0
    engagement_rate: float = 0.0
    click_rate: float = 0.0
    spend: float = 0.0
    roi: float = 0.0
    video_completion_rate: float = 0.0
    effective_cpm: float = 0.0


class OverviewResponse(BaseModel):
    total_impressions: int = 0
    total_engagement: int = 0
    total_clicks: int = 0
    total_spend: float = 0.0
    average_engagement_rate: float = 0.0
    platforms: dict[str, PlatformMetrics] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class CampaignAnalyticsResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    status: str
    budget: float
    spent: float
    platforms: dict[str, PlatformMetrics] = Field(default_factory=dict)
    posts: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=OverviewResponse)
async def get_analytics_overview(
    current_user: CurrentUser,
    db: DbSession,
    days: int = 30,
) -> OverviewResponse:
    """Aggregated metrics across all connected platforms for the tenant."""
    tenant_uuid = uuid.UUID(current_user.tenant_id)

    try:
        connections = await db.execute(
            select(PlatformConnection).where(
                PlatformConnection.tenant_id == tenant_uuid,
                PlatformConnection.is_active == True,  # noqa: E712
            )
        )
        active_platforms = [c.platform.value for c in connections.scalars().all()]
    except Exception:
        active_platforms = []

    if not active_platforms:
        active_platforms = list(ENGAGEMENT_BENCHMARKS.keys())

    trace = ExecutionTrace(trace_id=str(uuid.uuid4()), tenant_id=current_user.tenant_id)
    request = AnalyticsRequest(
        platforms=active_platforms,
        date_range_days=days,
        include_insights=True,
        include_ctv_dashboard_preview=True,
    )
    result = await run_analytics(request, trace, tenant_id=current_user.tenant_id)
    summary = result.cross_platform_summary

    platform_metrics = {}
    for name, data in summary.get("platforms", {}).items():
        platform_metrics[name] = PlatformMetrics(**{
            k: data.get(k, 0) for k in PlatformMetrics.model_fields
        })

    return OverviewResponse(
        total_impressions=result.metrics.get("total_impressions", 0),
        total_engagement=result.metrics.get("total_engagement", 0),
        total_clicks=result.metrics.get("total_clicks", 0),
        total_spend=result.metrics.get("total_spend", 0.0),
        average_engagement_rate=result.metrics.get("average_engagement_rate", 0.0),
        platforms=platform_metrics,
        insights=result.insights,
        recommendations=result.recommendations,
    )


@router.get("/platform/{platform}")
async def get_platform_analytics(
    platform: str,
    current_user: CurrentUser,
    db: DbSession,
    days: int = 30,
) -> dict[str, Any]:
    """Platform-specific metrics for the tenant."""
    normalized = platform.lower().replace("-", "_")
    if normalized == "streaming_tv":
        normalized = "ctv"
    if normalized != "ctv":
        try:
            PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown platform: {platform}",
            )

    trace = ExecutionTrace(trace_id=str(uuid.uuid4()), tenant_id=current_user.tenant_id)
    request = AnalyticsRequest(
        platforms=[normalized],
        date_range_days=days,
        include_insights=True,
        include_ctv_dashboard_preview=(normalized == "ctv"),
    )
    result = await run_analytics(request, trace, tenant_id=current_user.tenant_id)
    platform_data = result.cross_platform_summary.get("platforms", {}).get(normalized, {})

    return {
        "platform": normalized,
        "days": days,
        "metrics": platform_data,
        "insights": result.insights,
        "benchmark": ENGAGEMENT_BENCHMARKS.get(normalized, {}),
    }


@router.get("/campaign/{campaign_id}", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignAnalyticsResponse:
    """Campaign-level metrics aggregated from its posts."""
    try:
        cid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    tenant_uuid = uuid.UUID(current_user.tenant_id)
    try:
        result = await db.execute(
            select(Campaign).where(Campaign.id == cid, Campaign.tenant_id == tenant_uuid)
        )
        campaign = result.scalar_one_or_none()
    except Exception:
        campaign = None
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    posts_result = await db.execute(
        select(CampaignPost).where(CampaignPost.campaign_id == cid)
    )
    posts = posts_result.scalars().all()

    platform_agg: dict[str, dict[str, Any]] = {}
    post_list: list[dict[str, Any]] = []

    for post in posts:
        pname = post.platform.value
        analytics = post.analytics or {}

        if pname not in platform_agg:
            platform_agg[pname] = {"impressions": 0, "engagement": 0, "clicks": 0, "spend": 0.0}

        platform_agg[pname]["impressions"] += analytics.get("impressions", 0)
        platform_agg[pname]["engagement"] += analytics.get("engagement", 0)
        platform_agg[pname]["clicks"] += analytics.get("clicks", 0)

        post_list.append({
            "id": str(post.id),
            "platform": pname,
            "status": post.status.value,
            "analytics": analytics,
        })

    platform_metrics = {
        name: PlatformMetrics(**{k: data.get(k, 0) for k in PlatformMetrics.model_fields})
        for name, data in platform_agg.items()
    }

    return CampaignAnalyticsResponse(
        campaign_id=str(campaign.id),
        campaign_name=campaign.name,
        status=campaign.status.value,
        budget=campaign.budget,
        spent=campaign.spent,
        platforms=platform_metrics,
        posts=post_list,
    )

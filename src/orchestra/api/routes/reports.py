"""AI-generated performance report endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from orchestra.api.deps import CurrentUser
from orchestra.agents.analytics_agent import run_analytics
from orchestra.agents.contracts import AnalyticsRequest
from orchestra.agents.trace import ExecutionTrace

router = APIRouter(prefix="/reports", tags=["reports"])
logger = structlog.get_logger("api.reports")

_report_store: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    title: str = "Performance Report"
    platforms: list[str] = Field(default_factory=list)
    date_range_days: int = 30


class ReportSummary(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    platforms: list[str]
    date_range_days: int


class ReportResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    platforms: list[str]
    date_range_days: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    cross_platform_summary: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=ReportSummary, status_code=status.HTTP_201_CREATED)
async def generate_report(
    body: ReportGenerateRequest,
    current_user: CurrentUser,
) -> ReportSummary:
    """Trigger an AI-generated performance report using the analytics agent."""
    report_id = str(uuid.uuid4())

    trace = ExecutionTrace(trace_id=report_id, tenant_id=current_user.tenant_id)
    request = AnalyticsRequest(
        platforms=body.platforms,
        date_range_days=body.date_range_days,
        include_insights=True,
    )
    result = await run_analytics(request, trace, tenant_id=current_user.tenant_id)

    now = datetime.now(UTC).isoformat()
    report = {
        "id": report_id,
        "tenant_id": current_user.tenant_id,
        "title": body.title,
        "status": "completed",
        "created_at": now,
        "platforms": body.platforms or list(result.cross_platform_summary.get("platforms", {}).keys()),
        "date_range_days": body.date_range_days,
        "metrics": result.metrics,
        "insights": result.insights,
        "recommendations": result.recommendations,
        "cross_platform_summary": result.cross_platform_summary,
    }
    _report_store[report_id] = report

    logger.info("report_generated", report_id=report_id, tenant_id=current_user.tenant_id)
    return ReportSummary(
        id=report_id,
        title=body.title,
        status="completed",
        created_at=now,
        platforms=report["platforms"],
        date_range_days=body.date_range_days,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: CurrentUser,
) -> ReportResponse:
    """Retrieve a generated report (tenant-isolated)."""
    report = _report_store.get(report_id)
    if not report or report.get("tenant_id") != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return ReportResponse(
        id=report["id"],
        title=report["title"],
        status=report["status"],
        created_at=report["created_at"],
        platforms=report["platforms"],
        date_range_days=report["date_range_days"],
        metrics=report["metrics"],
        insights=report["insights"],
        recommendations=report["recommendations"],
        cross_platform_summary=report["cross_platform_summary"],
    )

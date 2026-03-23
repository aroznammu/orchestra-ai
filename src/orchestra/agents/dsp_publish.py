"""CTV / programmatic DSP publish path for the orchestrator."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any

import structlog
from sqlalchemy import select

from orchestra.agents.contracts import OrchestratorState, PlatformActionResult
from orchestra.bidding.guardrails import SpendGuardrails, check_all_guardrails
from orchestra.config import get_settings
from orchestra.connectors.dsp_client import (
    CreativeComplianceError,
    DSPClient,
    DSPNotConfiguredError,
)
from orchestra.db.models import Campaign, Tenant
from orchestra.db.session import async_session_factory

logger = structlog.get_logger("agent.dsp_publish")


def _parse_date_val(val: Any, default: date) -> date:
    if isinstance(val, date):
        return val
    if not val:
        return default
    try:
        return date.fromisoformat(str(val)[:10])
    except ValueError:
        return default


def _dsp_budget(raw: dict[str, Any]) -> float:
    for key in ("budget_amount", "budget", "campaign_budget"):
        val = raw.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return 0.0


def _compliance_status_for_upload(state: OrchestratorState) -> tuple[str, str | None]:
    """Return (status, error_message). status is Passed or Failed."""
    vc = state.visual_compliance_result
    video_url = state.video_result.video_url if state.video_result else ""
    if video_url:
        if not vc or not vc.safe:
            return "Failed", "Vision compliance gate did not pass; CTV creative upload blocked."
        return "Passed", None
    if vc is not None and not vc.safe:
        return "Failed", "Vision compliance gate did not pass; CTV creative upload blocked."
    return "Passed", None


async def execute_dsp_ctv_publish(
    state: OrchestratorState,
    content_payload: dict[str, Any],
    action: str,
    platform_label: str,
) -> PlatformActionResult:
    """Run financial guardrails then DSP campaign + optional creative upload."""
    raw = state.raw_payload
    budget = _dsp_budget(raw)
    settings = get_settings()

    tenant_uuid = uuid.UUID(state.tenant_id)
    async with async_session_factory() as session:
        tenant = await session.get(Tenant, tenant_uuid)
        if not tenant:
            return PlatformActionResult(
                success=False,
                platform=platform_label,
                action=action,
                error="Tenant not found",
            )

        # v1: approximate spend using sum of campaign.spent (no separate daily rollup in DB).
        spent_result = await session.execute(
            select(Campaign.spent).where(Campaign.tenant_id == tenant_uuid),
        )
        spent_rows = spent_result.scalars().all()
        total_spent = float(sum(spent_rows) if spent_rows else 0.0)

    tenant_guardrails = SpendGuardrails(
        global_daily_cap=float(tenant.daily_spend_cap),
        global_monthly_cap=float(tenant.monthly_spend_cap),
    )
    checks = check_all_guardrails(
        action="create_campaign",
        amount=budget,
        tenant_guardrails=tenant_guardrails,
        current_daily_spend=total_spent,
        current_monthly_spend=total_spent,
        current_platform_daily=total_spent,
        campaigns_created_today=0,
    )
    blockers = [c for c in checks if not c.passed and c.severity == "block"]
    if blockers:
        msg = "; ".join(c.message for c in blockers)
        logger.warning("dsp_guardrails_blocked", tenant_id=state.tenant_id, message=msg)
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error=msg,
        )

    if not settings.has_dsp:
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error="DSP is not configured (set DSP_API_KEY and DSP_PARTNER_ID).",
        )

    creative_url = ""
    if state.video_result and state.video_result.video_url:
        creative_url = state.video_result.video_url
    elif content_payload.get("media_urls"):
        urls = content_payload["media_urls"]
        if isinstance(urls, list) and urls:
            creative_url = str(urls[0])

    if not creative_url:
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error="No video URL for CTV creative. Generate a video or provide media_urls.",
        )

    comp_status, comp_err = _compliance_status_for_upload(state)
    if comp_status != "Passed":
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error=comp_err or "Compliance failed",
        )

    campaign_name = raw.get("campaign_name") or (content_payload.get("text") or "CTV Campaign")[:120]
    start_d = _parse_date_val(raw.get("start_date"), date.today())
    end_d = _parse_date_val(raw.get("end_date"), start_d + timedelta(days=30))

    target_audience = raw.get("target_audience") or {}
    if not isinstance(target_audience, dict):
        target_audience = {}
    bid_cpm = float(raw.get("bid_cpm", 25.0))

    client = DSPClient(
        base_url=settings.dsp_base_url,
        api_key=settings.dsp_api_key.get_secret_value(),
        partner_id=settings.dsp_partner_id,
    )

    try:
        await client.authenticate()
        camp = await client.create_ctv_campaign(campaign_name, budget, start_d, end_d)
        campaign_id = camp.get("campaign_id", "")
        if not campaign_id:
            return PlatformActionResult(
                success=False,
                platform=platform_label,
                action=action,
                error="DSP did not return a campaign id",
                result=camp,
            )
        ag = await client.create_ctv_ad_group(campaign_id, target_audience, bid_cpm)
        creative = await client.upload_creative(creative_url, "Passed")
    except DSPNotConfiguredError as e:
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error=str(e),
        )
    except CreativeComplianceError as e:
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error=str(e),
        )
    except Exception as e:
        logger.exception("dsp_publish_failed", error=str(e))
        return PlatformActionResult(
            success=False,
            platform=platform_label,
            action=action,
            error=str(e),
        )

    return PlatformActionResult(
        success=True,
        platform=platform_label,
        action=action,
        result={
            "dsp_campaign_id": campaign_id,
            "dsp_ad_group_id": ag.get("ad_group_id", ""),
            "dsp_creative_id": creative.get("creative_id", ""),
            "video_url": creative_url,
            "channel": "CTV",
        },
    )

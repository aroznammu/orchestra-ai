"""Audit trail API routes."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query

from orchestra.api.deps import CurrentUser
from orchestra.security.audit_trail import get_audit_trail
from orchestra.security.rbac import Permission, check_permission

logger = structlog.get_logger("api.audit")

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def get_audit_log(
    category: str | None = None,
    action: str | None = None,
    outcome: str | None = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(CurrentUser),
) -> dict[str, Any]:
    """Query audit log entries."""
    check_permission(user.get("role", "viewer"), Permission.AUDIT_VIEW)

    trail = get_audit_trail()
    entries = trail.query(
        tenant_id=user.get("tenant_id", ""),
        category=category,
        action=action,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )

    return {
        "entries": [e.model_dump() for e in entries],
        "total": len(entries),
        "limit": limit,
        "offset": offset,
    }


@router.get("/financial")
async def get_financial_audit(
    platform: str | None = None,
    user: dict = Depends(CurrentUser),
) -> dict[str, Any]:
    """Get financial audit summary."""
    check_permission(user.get("role", "viewer"), Permission.AUDIT_VIEW)

    trail = get_audit_trail()
    return trail.get_financial_summary(
        tenant_id=user.get("tenant_id", ""),
        platform=platform,
    )


@router.get("/stats")
async def get_audit_stats(
    user: dict = Depends(CurrentUser),
) -> dict[str, Any]:
    """Get audit statistics."""
    check_permission(user.get("role", "viewer"), Permission.AUDIT_VIEW)

    trail = get_audit_trail()
    return trail.get_stats(tenant_id=user.get("tenant_id", ""))

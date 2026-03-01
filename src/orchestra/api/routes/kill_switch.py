"""Kill switch API routes."""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from orchestra.api.deps import CurrentUser
from orchestra.bidding.kill_switch import get_kill_switch
from orchestra.security.rbac import Permission, check_permission

logger = structlog.get_logger("api.kill_switch")

router = APIRouter(prefix="/kill-switch", tags=["kill-switch"])


class KillSwitchRequest(BaseModel):
    reason: str


@router.get("/status")
async def get_status(
    user: CurrentUser = None,
) -> dict[str, Any]:
    """Get current kill switch status."""
    check_permission(user.role, Permission.KILL_SWITCH_VIEW)

    ks = get_kill_switch()
    status = ks.get_status()

    tenant_id = user.tenant_id
    return {
        "global_active": status["global_active"],
        "tenant_active": ks.is_active(tenant_id),
        "is_affected": ks.is_active(tenant_id),
    }


@router.post("/activate")
async def activate_tenant_kill_switch(
    request: KillSwitchRequest,
    user: CurrentUser = None,
) -> dict[str, Any]:
    """Activate kill switch for the current tenant."""
    check_permission(user.role, Permission.KILL_SWITCH_ACTIVATE)

    ks = get_kill_switch()
    event = ks.activate_tenant(
        tenant_id=user.tenant_id,
        triggered_by=user.sub,
        reason=request.reason,
    )

    return {"activated": True, "event_id": event.id, "reason": request.reason}


@router.post("/deactivate")
async def deactivate_tenant_kill_switch(
    user: CurrentUser = None,
) -> dict[str, Any]:
    """Deactivate kill switch for the current tenant."""
    check_permission(user.role, Permission.KILL_SWITCH_ACTIVATE)

    ks = get_kill_switch()
    event = ks.deactivate_tenant(
        tenant_id=user.tenant_id,
        triggered_by=user.sub,
    )

    return {"deactivated": True, "event_id": event.id}


@router.get("/history")
async def get_kill_switch_history(
    user: CurrentUser = None,
) -> list[dict[str, Any]]:
    """Get kill switch event history for the current tenant."""
    check_permission(user.role, Permission.KILL_SWITCH_VIEW)

    ks = get_kill_switch()
    return ks.get_event_log(tenant_id=user.tenant_id)

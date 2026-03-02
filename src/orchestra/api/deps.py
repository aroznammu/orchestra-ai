"""FastAPI dependency injection."""

import uuid
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestra.api.middleware.auth import TokenPayload, get_current_user, require_role
from orchestra.config import Settings, get_settings
from orchestra.db.models import Tenant
from orchestra.db.session import get_db

logger = structlog.get_logger("deps")

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser = Annotated[TokenPayload, Depends(require_role("owner", "admin"))]

ACTIVE_STATUSES = {"active", "trialing"}


async def check_active_subscription(
    current_user: CurrentUser,
    db: DbSession,
) -> TokenPayload:
    """Reject requests from tenants without an active or trialing subscription.

    Returns 402 Payment Required when the tenant needs to subscribe.
    """
    try:
        result = await db.execute(
            select(Tenant.subscription_status).where(
                Tenant.id == uuid.UUID(current_user.tenant_id),
            )
        )
        sub_status = result.scalar_one_or_none()
    except Exception:
        logger.warning("subscription_check_db_error", tenant_id=current_user.tenant_id)
        return current_user

    if sub_status and sub_status not in ACTIVE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription required to access AI agents.",
        )

    return current_user


PaidUser = Annotated[TokenPayload, Depends(check_active_subscription)]

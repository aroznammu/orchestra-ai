"""Billing API routes: Stripe Checkout, Portal, and Webhooks."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from orchestra.api.deps import CurrentUser, DbSession
from orchestra.core.billing import (
    PLANS,
    create_checkout_session,
    create_portal_session,
    get_subscription_status,
    handle_webhook_event,
)

router = APIRouter(prefix="/billing", tags=["billing"])
logger = structlog.get_logger("api.billing")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    plan: str = Field(..., pattern="^(starter|agency)$")


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class PlanInfo(BaseModel):
    key: str
    name: str
    price_monthly: int
    features: list[str]


class PlansResponse(BaseModel):
    plans: list[PlanInfo]


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    stripe_customer_id: str | None = None
    has_subscription: bool
    plan_expires_at: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/plans", response_model=PlansResponse)
async def list_plans() -> PlansResponse:
    """Return available subscription plans (public)."""
    return PlansResponse(
        plans=[
            PlanInfo(key=k, **v)
            for k, v in PLANS.items()
        ],
    )


@router.get("/status", response_model=SubscriptionResponse)
async def billing_status(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Return the current tenant's subscription status."""
    return await get_subscription_status(db, current_user.tenant_id)


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CheckoutResponse:
    """Create a Stripe Checkout session and return the redirect URL."""
    try:
        url = await create_checkout_session(db, current_user.tenant_id, body.plan)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return CheckoutResponse(url=url)


@router.post("/portal", response_model=PortalResponse)
async def portal(
    current_user: CurrentUser,
    db: DbSession,
) -> PortalResponse:
    """Create a Stripe Customer Portal session so users can manage billing."""
    try:
        url = await create_portal_session(db, current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return PortalResponse(url=url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: DbSession,
) -> dict[str, str]:
    """Receive and verify Stripe webhook events. No auth required (signature-verified)."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event_type = await handle_webhook_event(db, payload, sig)
    except Exception as exc:
        logger.error("webhook_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook verification failed",
        ) from exc

    return {"status": "ok", "event_type": event_type}

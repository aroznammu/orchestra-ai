"""Stripe billing service for subscription management."""

from __future__ import annotations

import uuid
from collections import OrderedDict
from typing import Any

import stripe
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestra.config import get_settings
from orchestra.db.models import Tenant

logger = structlog.get_logger("billing")

_IDEMPOTENCY_MAX = 2048
_processed_events: OrderedDict[str, bool] = OrderedDict()

PLANS: dict[str, dict[str, Any]] = {
    "starter": {
        "name": "Starter",
        "price_monthly": 99_00,
        "features": [
            "5 active campaigns",
            "3 platform connections",
            "Basic AI orchestration",
            "Email support",
        ],
    },
    "agency": {
        "name": "Agency",
        "price_monthly": 999_00,
        "features": [
            "Unlimited campaigns",
            "All platform connections",
            "Full AI orchestration & bidding",
            "Priority support",
            "Custom compliance rules",
            "Advanced analytics",
        ],
    },
}


def _configure_stripe() -> None:
    settings = get_settings()
    key = settings.stripe_secret_key.get_secret_value()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = key


def _price_id_for_plan(plan: str) -> str:
    settings = get_settings()
    if plan == "starter":
        pid = settings.stripe_starter_price_id
    elif plan == "agency":
        pid = settings.stripe_agency_price_id
    else:
        raise ValueError(f"Unknown plan: {plan}")
    if not pid:
        raise RuntimeError(f"STRIPE_{plan.upper()}_PRICE_ID is not configured")
    return pid


async def create_checkout_session(
    db: AsyncSession,
    tenant_id: str,
    plan: str,
) -> str:
    """Create a Stripe Checkout Session and return its URL."""
    _configure_stripe()

    tenant = await _get_tenant(db, tenant_id)
    price_id = _price_id_for_plan(plan)

    if not tenant.stripe_customer_id:
        customer = stripe.Customer.create(
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id)},
        )
        tenant.stripe_customer_id = customer.id
        await db.flush()

    settings = get_settings()
    session = stripe.checkout.Session.create(
        customer=tenant.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/settings/billing?status=success",
        cancel_url=f"{settings.frontend_url}/settings/billing?status=cancelled",
        metadata={"tenant_id": str(tenant.id), "plan": plan},
        subscription_data={"metadata": {"tenant_id": str(tenant.id), "plan": plan}},
    )

    logger.info("checkout_session_created", tenant_id=tenant_id, plan=plan)
    return session.url or ""


async def create_portal_session(
    db: AsyncSession,
    tenant_id: str,
) -> str:
    """Create a Stripe Customer Portal session and return its URL."""
    _configure_stripe()

    tenant = await _get_tenant(db, tenant_id)
    if not tenant.stripe_customer_id:
        raise ValueError("Tenant has no Stripe customer record")

    settings = get_settings()
    session = stripe.billing_portal.Session.create(
        customer=tenant.stripe_customer_id,
        return_url=f"{settings.frontend_url}/settings/billing",
    )
    return session.url


async def handle_webhook_event(
    db: AsyncSession,
    payload: bytes,
    sig_header: str,
) -> str:
    """Verify and process a Stripe webhook event. Returns the event type."""
    settings = get_settings()
    webhook_secret = settings.stripe_webhook_secret.get_secret_value()
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")

    _configure_stripe()
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    event_id: str = event["id"]
    event_type: str = event["type"]

    if event_id in _processed_events:
        logger.info("stripe_webhook_duplicate_skipped", event_id=event_id, event_type=event_type)
        return event_type

    logger.info("stripe_webhook_received", event_id=event_id, event_type=event_type)

    try:
        if event_type == "invoice.paid":
            await _on_invoice_paid(db, event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            await _on_subscription_deleted(db, event["data"]["object"])
        elif event_type == "customer.subscription.updated":
            await _on_subscription_updated(db, event["data"]["object"])
    except Exception:
        logger.exception("webhook_handler_error", event_id=event_id, event_type=event_type)
        raise

    _processed_events[event_id] = True
    while len(_processed_events) > _IDEMPOTENCY_MAX:
        _processed_events.popitem(last=False)

    return event_type


async def get_subscription_status(
    db: AsyncSession,
    tenant_id: str,
) -> dict[str, Any]:
    """Return the current subscription state for a tenant."""
    tenant = await _get_tenant(db, tenant_id)
    return {
        "plan": tenant.subscription_plan,
        "status": tenant.subscription_status,
        "stripe_customer_id": tenant.stripe_customer_id,
        "has_subscription": tenant.stripe_subscription_id is not None,
        "plan_expires_at": tenant.plan_expires_at.isoformat() if tenant.plan_expires_at else None,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_tenant(db: AsyncSession, tenant_id: str) -> Tenant:
    result = await db.execute(
        select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    return tenant


async def _on_invoice_paid(db: AsyncSession, invoice: dict[str, Any]) -> None:
    sub_id = invoice.get("subscription")
    if not sub_id:
        parent = invoice.get("parent") or {}
        sub_details = parent.get("subscription_details") or {}
        sub_id = sub_details.get("subscription")
    customer_id = invoice.get("customer")
    logger.info("invoice_paid_processing", subscription=sub_id, customer=customer_id)
    if not sub_id or not customer_id:
        logger.warning("invoice_paid_missing_fields", subscription=sub_id, customer=customer_id)
        return

    result = await db.execute(
        select(Tenant).where(Tenant.stripe_customer_id == customer_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        logger.warning("webhook_tenant_not_found", customer_id=customer_id)
        return

    try:
        sub = stripe.Subscription.retrieve(sub_id)
        meta = dict(sub.get("metadata", {})) if hasattr(sub, "get") else {}
        plan_name = meta.get("plan") or _resolve_plan_from_subscription(sub)
    except Exception:
        logger.exception("subscription_retrieve_failed", sub_id=sub_id)
        plan_name = "starter"

    tenant.stripe_subscription_id = sub_id
    tenant.subscription_status = "active"
    tenant.subscription_plan = plan_name
    await db.commit()

    logger.info(
        "subscription_activated",
        tenant_id=str(tenant.id),
        plan=plan_name,
        subscription_id=sub_id,
    )


async def _on_subscription_deleted(db: AsyncSession, subscription: dict[str, Any]) -> None:
    customer_id = subscription.get("customer")
    if not customer_id:
        return

    result = await db.execute(
        select(Tenant).where(Tenant.stripe_customer_id == customer_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return

    tenant.subscription_status = "cancelled"
    tenant.stripe_subscription_id = None
    tenant.subscription_plan = "free"
    await db.commit()

    logger.info("subscription_cancelled", tenant_id=str(tenant.id))


async def _on_subscription_updated(db: AsyncSession, subscription: dict[str, Any]) -> None:
    customer_id = subscription.get("customer")
    status = subscription.get("status", "")
    if not customer_id:
        return

    result = await db.execute(
        select(Tenant).where(Tenant.stripe_customer_id == customer_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return

    tenant.subscription_status = status
    await db.commit()


def _resolve_plan_from_subscription(sub: Any) -> str:
    """Derive the plan name by matching the subscription's price ID to configured plans."""
    settings = get_settings()
    price_map = {
        settings.stripe_starter_price_id: "starter",
        settings.stripe_agency_price_id: "agency",
    }
    try:
        items = sub.get("items", {}).get("data", [])
        for item in items:
            price_id = item.get("price", {}).get("id", "")
            if price_id in price_map:
                return price_map[price_id]
    except Exception:
        logger.warning("plan_resolution_failed", subscription_id=sub.get("id"))
    return "starter"

"""Bidding guardrails -- hard limits, approval gates, conservative defaults.

These are the non-negotiable safety rails that apply regardless of autonomy phase.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.core.exceptions import BudgetExceededError

logger = structlog.get_logger("bidding.guardrails")


class SpendGuardrails(BaseModel):
    """Per-tenant guardrail configuration."""

    global_daily_cap: float = 500.0
    global_monthly_cap: float = 10000.0
    per_platform_daily_cap: float = 200.0
    per_campaign_total_cap: float = 5000.0
    max_bid_increase_pct: float = 20.0
    max_budget_increase_pct: float = 25.0
    min_budget_per_campaign: float = 5.0
    max_new_campaigns_per_day: int = 5
    require_approval_above: float = 100.0


# Absolute hard limits that can NEVER be overridden
ABSOLUTE_LIMITS = {
    "max_daily_spend_any_tenant": 50000.0,
    "max_single_bid": 10000.0,
    "max_single_campaign_budget": 100000.0,
    "min_budget": 1.0,
}


class GuardrailCheck(BaseModel):
    passed: bool
    guardrail: str
    message: str
    current_value: float = 0.0
    limit_value: float = 0.0
    severity: str = "block"  # block, warn, info


def check_all_guardrails(
    action: str,
    amount: float,
    tenant_guardrails: SpendGuardrails | None = None,
    current_daily_spend: float = 0.0,
    current_monthly_spend: float = 0.0,
    current_platform_daily: float = 0.0,
    campaigns_created_today: int = 0,
) -> list[GuardrailCheck]:
    """Run all guardrail checks for a spend operation."""
    if tenant_guardrails is None:
        tenant_guardrails = SpendGuardrails()

    checks: list[GuardrailCheck] = []

    # Absolute hard limits (never overrideable)
    checks.append(_check_absolute_limit(amount))

    # Daily cap
    checks.append(GuardrailCheck(
        passed=(current_daily_spend + amount) <= tenant_guardrails.global_daily_cap,
        guardrail="daily_spend_cap",
        message=f"Daily spend: ${current_daily_spend + amount:.2f} / ${tenant_guardrails.global_daily_cap:.2f}",
        current_value=current_daily_spend + amount,
        limit_value=tenant_guardrails.global_daily_cap,
        severity="block",
    ))

    # Monthly cap
    checks.append(GuardrailCheck(
        passed=(current_monthly_spend + amount) <= tenant_guardrails.global_monthly_cap,
        guardrail="monthly_spend_cap",
        message=f"Monthly spend: ${current_monthly_spend + amount:.2f} / ${tenant_guardrails.global_monthly_cap:.2f}",
        current_value=current_monthly_spend + amount,
        limit_value=tenant_guardrails.global_monthly_cap,
        severity="block",
    ))

    # Per-platform daily cap
    checks.append(GuardrailCheck(
        passed=(current_platform_daily + amount) <= tenant_guardrails.per_platform_daily_cap,
        guardrail="platform_daily_cap",
        message=f"Platform daily: ${current_platform_daily + amount:.2f} / ${tenant_guardrails.per_platform_daily_cap:.2f}",
        current_value=current_platform_daily + amount,
        limit_value=tenant_guardrails.per_platform_daily_cap,
        severity="block",
    ))

    # Campaign creation limit
    if action == "create_campaign":
        checks.append(GuardrailCheck(
            passed=campaigns_created_today < tenant_guardrails.max_new_campaigns_per_day,
            guardrail="campaign_creation_limit",
            message=f"Campaigns today: {campaigns_created_today} / {tenant_guardrails.max_new_campaigns_per_day}",
            current_value=float(campaigns_created_today),
            limit_value=float(tenant_guardrails.max_new_campaigns_per_day),
            severity="block",
        ))

    # Approval threshold warning
    if amount > tenant_guardrails.require_approval_above:
        checks.append(GuardrailCheck(
            passed=True,
            guardrail="approval_threshold",
            message=f"Amount ${amount:.2f} exceeds approval threshold ${tenant_guardrails.require_approval_above:.2f}",
            current_value=amount,
            limit_value=tenant_guardrails.require_approval_above,
            severity="warn",
        ))

    # Budget floor
    if amount < tenant_guardrails.min_budget_per_campaign and action == "create_campaign":
        checks.append(GuardrailCheck(
            passed=False,
            guardrail="minimum_budget",
            message=f"Budget ${amount:.2f} below minimum ${tenant_guardrails.min_budget_per_campaign:.2f}",
            current_value=amount,
            limit_value=tenant_guardrails.min_budget_per_campaign,
            severity="block",
        ))

    return checks


def enforce_guardrails(checks: list[GuardrailCheck]) -> None:
    """Raise if any blocking guardrail check failed."""
    failures = [c for c in checks if not c.passed and c.severity == "block"]
    if failures:
        messages = [f.message for f in failures]
        raise BudgetExceededError(
            f"Guardrail violation: {'; '.join(messages)}",
            details={
                "violations": [
                    {"guardrail": f.guardrail, "message": f.message, "value": f.current_value, "limit": f.limit_value}
                    for f in failures
                ]
            },
        )

    warnings = [c for c in checks if not c.passed and c.severity == "warn"]
    for w in warnings:
        logger.warning("guardrail_warning", guardrail=w.guardrail, message=w.message)


def _check_absolute_limit(amount: float) -> GuardrailCheck:
    max_bid = ABSOLUTE_LIMITS["max_single_bid"]
    if amount > max_bid:
        return GuardrailCheck(
            passed=False,
            guardrail="absolute_max_bid",
            message=f"Amount ${amount:.2f} exceeds absolute maximum ${max_bid:.2f}",
            current_value=amount,
            limit_value=max_bid,
            severity="block",
        )
    if amount < ABSOLUTE_LIMITS["min_budget"]:
        return GuardrailCheck(
            passed=False,
            guardrail="absolute_min_budget",
            message=f"Amount ${amount:.2f} below absolute minimum ${ABSOLUTE_LIMITS['min_budget']:.2f}",
            current_value=amount,
            limit_value=ABSOLUTE_LIMITS["min_budget"],
            severity="block",
        )
    return GuardrailCheck(
        passed=True,
        guardrail="absolute_limits",
        message="Within absolute limits",
        current_value=amount,
        limit_value=max_bid,
        severity="info",
    )

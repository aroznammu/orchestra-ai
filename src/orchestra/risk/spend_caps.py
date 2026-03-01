"""Three-tier spend cap system.

Tier 1: Global hard ceiling per account
Tier 2: Per-platform budget cap
Tier 3: Per-campaign cap

All three tiers must pass for any spend operation to proceed.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.core.exceptions import BudgetExceededError

logger = structlog.get_logger("risk.spend_caps")


class SpendCaps(BaseModel):
    """Three-tier cap configuration for a tenant."""

    # Tier 1: Global
    global_daily_cap: float = 500.0
    global_monthly_cap: float = 10000.0
    global_total_cap: float | None = None  # lifetime cap (optional)

    # Tier 2: Per-platform
    platform_daily_caps: dict[str, float] = Field(default_factory=dict)
    default_platform_daily_cap: float = 200.0

    # Tier 3: Per-campaign
    campaign_caps: dict[str, float] = Field(default_factory=dict)
    default_campaign_cap: float = 1000.0

    # New account conservative defaults
    new_account_daily_cap: float = 100.0
    new_account_max_exposure: float = 500.0


class SpendTracker:
    """Tracks spend against caps in real-time."""

    def __init__(self, tenant_id: str, caps: SpendCaps | None = None) -> None:
        self.tenant_id = tenant_id
        self.caps = caps or SpendCaps()
        self._global_daily: float = 0.0
        self._global_monthly: float = 0.0
        self._global_total: float = 0.0
        self._platform_daily: dict[str, float] = {}
        self._campaign_spend: dict[str, float] = {}

    def check_spend(
        self,
        amount: float,
        platform: str,
        campaign_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Check if a spend operation would violate any cap.

        Returns list of violations (empty = all clear).
        """
        violations: list[dict[str, Any]] = []

        # Tier 1: Global
        if self._global_daily + amount > self.caps.global_daily_cap:
            violations.append({
                "tier": 1,
                "cap": "global_daily",
                "current": self._global_daily,
                "amount": amount,
                "limit": self.caps.global_daily_cap,
            })

        if self._global_monthly + amount > self.caps.global_monthly_cap:
            violations.append({
                "tier": 1,
                "cap": "global_monthly",
                "current": self._global_monthly,
                "amount": amount,
                "limit": self.caps.global_monthly_cap,
            })

        if self.caps.global_total_cap and self._global_total + amount > self.caps.global_total_cap:
            violations.append({
                "tier": 1,
                "cap": "global_total",
                "current": self._global_total,
                "amount": amount,
                "limit": self.caps.global_total_cap,
            })

        # Tier 2: Per-platform
        platform_cap = self.caps.platform_daily_caps.get(
            platform, self.caps.default_platform_daily_cap
        )
        platform_daily = self._platform_daily.get(platform, 0.0)
        if platform_daily + amount > platform_cap:
            violations.append({
                "tier": 2,
                "cap": f"platform_daily:{platform}",
                "current": platform_daily,
                "amount": amount,
                "limit": platform_cap,
            })

        # Tier 3: Per-campaign
        if campaign_id:
            campaign_cap = self.caps.campaign_caps.get(
                campaign_id, self.caps.default_campaign_cap
            )
            campaign_spent = self._campaign_spend.get(campaign_id, 0.0)
            if campaign_spent + amount > campaign_cap:
                violations.append({
                    "tier": 3,
                    "cap": f"campaign:{campaign_id}",
                    "current": campaign_spent,
                    "amount": amount,
                    "limit": campaign_cap,
                })

        return violations

    def record_spend(
        self,
        amount: float,
        platform: str,
        campaign_id: str | None = None,
    ) -> None:
        """Record a spend. Raises BudgetExceededError if caps are violated."""
        violations = self.check_spend(amount, platform, campaign_id)

        if violations:
            details = violations[0]
            raise BudgetExceededError(
                f"Spend cap exceeded: {details['cap']} "
                f"(${details['current']:.2f} + ${amount:.2f} > ${details['limit']:.2f})",
                details={"violations": violations, "tenant_id": self.tenant_id},
            )

        self._global_daily += amount
        self._global_monthly += amount
        self._global_total += amount
        self._platform_daily[platform] = self._platform_daily.get(platform, 0.0) + amount

        if campaign_id:
            self._campaign_spend[campaign_id] = (
                self._campaign_spend.get(campaign_id, 0.0) + amount
            )

        logger.info(
            "spend_recorded",
            tenant_id=self.tenant_id,
            amount=amount,
            platform=platform,
            campaign_id=campaign_id,
            global_daily=round(self._global_daily, 2),
        )

    def reset_daily(self) -> None:
        """Reset daily counters (called by scheduler at midnight)."""
        self._global_daily = 0.0
        self._platform_daily.clear()
        logger.info("daily_spend_reset", tenant_id=self.tenant_id)

    def reset_monthly(self) -> None:
        """Reset monthly counter (called by scheduler on 1st of month)."""
        self._global_monthly = 0.0
        logger.info("monthly_spend_reset", tenant_id=self.tenant_id)

    def get_utilization(self) -> dict[str, Any]:
        """Get current spend utilization across all tiers."""
        return {
            "tenant_id": self.tenant_id,
            "global_daily": {
                "used": round(self._global_daily, 2),
                "cap": self.caps.global_daily_cap,
                "pct": round(self._global_daily / self.caps.global_daily_cap * 100, 1)
                if self.caps.global_daily_cap > 0 else 0.0,
            },
            "global_monthly": {
                "used": round(self._global_monthly, 2),
                "cap": self.caps.global_monthly_cap,
                "pct": round(self._global_monthly / self.caps.global_monthly_cap * 100, 1)
                if self.caps.global_monthly_cap > 0 else 0.0,
            },
            "platforms": {
                p: {"used": round(v, 2), "cap": self.caps.platform_daily_caps.get(p, self.caps.default_platform_daily_cap)}
                for p, v in self._platform_daily.items()
            },
        }

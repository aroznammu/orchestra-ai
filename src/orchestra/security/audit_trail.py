"""Financial audit trail.

Logs every spend decision with reasoning, approval status, and outcome.
Provides query interface for compliance auditing.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("security.audit_trail")


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    user_id: str | None = None
    agent: str | None = None
    action: str
    category: str  # financial, campaign, platform, auth, data, system
    resource_type: str = ""
    resource_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    approval_status: str | None = None  # pending, approved, rejected, auto_approved
    approved_by: str | None = None
    outcome: str = "success"  # success, failure, pending
    risk_score: float = 0.0
    ip_address: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class FinancialAuditEntry(AuditEntry):
    """Extended audit entry for financial operations."""

    platform: str = ""
    campaign_id: str | None = None
    amount: float = 0.0
    currency: str = "USD"
    previous_value: float | None = None
    new_value: float | None = None
    budget_utilization_pct: float | None = None


class AuditTrail:
    """Centralized audit trail for all operations."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def log(
        self,
        tenant_id: str,
        action: str,
        category: str,
        user_id: str | None = None,
        agent: str | None = None,
        resource_type: str = "",
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        reasoning: str = "",
        outcome: str = "success",
        risk_score: float = 0.0,
        ip_address: str | None = None,
    ) -> AuditEntry:
        """Log a general audit entry."""
        entry = AuditEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            agent=agent,
            action=action,
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            reasoning=reasoning,
            outcome=outcome,
            risk_score=risk_score,
            ip_address=ip_address,
        )
        self._entries.append(entry)

        logger.info(
            "audit_log",
            tenant_id=tenant_id,
            action=action,
            category=category,
            outcome=outcome,
        )

        return entry

    def log_financial(
        self,
        tenant_id: str,
        action: str,
        platform: str,
        amount: float,
        user_id: str | None = None,
        agent: str | None = None,
        campaign_id: str | None = None,
        previous_value: float | None = None,
        new_value: float | None = None,
        reasoning: str = "",
        approval_status: str | None = None,
        approved_by: str | None = None,
        outcome: str = "success",
        risk_score: float = 0.0,
        budget_utilization_pct: float | None = None,
    ) -> FinancialAuditEntry:
        """Log a financial audit entry with extended details."""
        entry = FinancialAuditEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            agent=agent,
            action=action,
            category="financial",
            resource_type="spend",
            resource_id=campaign_id,
            platform=platform,
            campaign_id=campaign_id,
            amount=amount,
            previous_value=previous_value,
            new_value=new_value,
            reasoning=reasoning,
            approval_status=approval_status,
            approved_by=approved_by,
            outcome=outcome,
            risk_score=risk_score,
            budget_utilization_pct=budget_utilization_pct,
        )
        self._entries.append(entry)

        logger.info(
            "financial_audit",
            tenant_id=tenant_id,
            action=action,
            platform=platform,
            amount=amount,
            approval_status=approval_status,
            outcome=outcome,
        )

        return entry

    def query(
        self,
        tenant_id: str,
        category: str | None = None,
        action: str | None = None,
        user_id: str | None = None,
        outcome: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries with filters."""
        entries = [e for e in self._entries if e.tenant_id == tenant_id]

        if category:
            entries = [e for e in entries if e.category == category]
        if action:
            entries = [e for e in entries if e.action == action]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if outcome:
            entries = [e for e in entries if e.outcome == outcome]

        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[offset: offset + limit]

    def get_financial_summary(
        self,
        tenant_id: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Get financial audit summary."""
        financial = [
            e for e in self._entries
            if e.tenant_id == tenant_id
            and e.category == "financial"
            and isinstance(e, FinancialAuditEntry)
        ]

        if platform:
            financial = [e for e in financial if e.platform == platform]

        total_spend = sum(e.amount for e in financial if e.outcome == "success")
        approvals = sum(1 for e in financial if e.approval_status == "approved")
        rejections = sum(1 for e in financial if e.approval_status == "rejected")
        auto_approved = sum(1 for e in financial if e.approval_status == "auto_approved")

        return {
            "tenant_id": tenant_id,
            "total_entries": len(financial),
            "total_spend": round(total_spend, 2),
            "approved": approvals,
            "rejected": rejections,
            "auto_approved": auto_approved,
            "by_platform": self._group_by_platform(financial),
        }

    def get_stats(self, tenant_id: str) -> dict[str, Any]:
        entries = [e for e in self._entries if e.tenant_id == tenant_id]
        return {
            "total_entries": len(entries),
            "by_category": self._count_by(entries, "category"),
            "by_outcome": self._count_by(entries, "outcome"),
        }

    @staticmethod
    def _count_by(entries: list[AuditEntry], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in entries:
            val = getattr(e, field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts

    @staticmethod
    def _group_by_platform(entries: list) -> dict[str, float]:
        by_platform: dict[str, float] = {}
        for e in entries:
            if hasattr(e, "platform") and e.outcome == "success":
                by_platform[e.platform] = by_platform.get(e.platform, 0.0) + e.amount
        return {k: round(v, 2) for k, v in by_platform.items()}


# Singleton
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail

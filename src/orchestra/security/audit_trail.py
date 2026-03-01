"""Financial audit trail with DB write-through.

Keeps in-memory cache for fast reads, persists to PostgreSQL for durability.
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
    category: str
    resource_type: str = ""
    resource_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    approval_status: str | None = None
    approved_by: str | None = None
    outcome: str = "success"
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


def _safe_uuid(value: str | None):
    """Convert string to UUID, returning None if invalid."""
    if not value:
        return None
    try:
        import uuid as _uuid
        return _uuid.UUID(value)
    except (ValueError, AttributeError):
        return None


async def _persist_audit_entry(entry: AuditEntry) -> None:
    """Write-through to audit_logs DB table. Fire-and-forget."""
    try:
        from orchestra.db.models import AuditLog
        from orchestra.db.session import async_session_factory

        async with async_session_factory() as session:
            record = AuditLog(
                tenant_id=_safe_uuid(entry.tenant_id),
                user_id=_safe_uuid(entry.user_id),
                action=entry.action,
                resource_type=entry.resource_type or entry.category,
                resource_id=entry.resource_id,
                details={
                    "category": entry.category,
                    "reasoning": entry.reasoning,
                    "outcome": entry.outcome,
                    "risk_score": entry.risk_score,
                    **({"agent": entry.agent} if entry.agent else {}),
                    **(entry.details or {}),
                },
                ip_address=entry.ip_address,
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.debug("audit_db_write_skipped", error=str(e))


class AuditTrail:
    """Centralized audit trail with in-memory cache + DB persistence."""

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

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist_audit_entry(entry))
        except RuntimeError:
            pass

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

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist_audit_entry(entry))
        except RuntimeError:
            pass

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
        """Query audit entries from in-memory cache (sync fallback)."""
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

    async def query_db(
        self,
        tenant_id: str,
        category: str | None = None,
        action: str | None = None,
        outcome: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries from PostgreSQL, falling back to in-memory."""
        try:
            from sqlalchemy import select, desc
            from orchestra.db.models import AuditLog
            from orchestra.db.session import async_session_factory

            tid = _safe_uuid(tenant_id)
            if tid is None:
                raise ValueError("invalid tenant_id for DB query")

            async with async_session_factory() as session:
                stmt = select(AuditLog).where(AuditLog.tenant_id == tid)
                if action:
                    stmt = stmt.where(AuditLog.action == action)
                stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
                result = await session.execute(stmt)
                rows = result.scalars().all()

            entries = []
            for row in rows:
                details = row.details or {}
                entries.append(AuditEntry(
                    id=str(row.id),
                    tenant_id=str(row.tenant_id) if row.tenant_id else tenant_id,
                    user_id=str(row.user_id) if row.user_id else None,
                    action=row.action,
                    category=details.get("category", row.resource_type),
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    details=details,
                    reasoning=details.get("reasoning", ""),
                    outcome=details.get("outcome", "success"),
                    risk_score=details.get("risk_score", 0.0),
                    ip_address=row.ip_address,
                    timestamp=row.created_at.isoformat() if row.created_at else "",
                ))

            if category:
                entries = [e for e in entries if e.category == category]
            if outcome:
                entries = [e for e in entries if e.outcome == outcome]

            return entries
        except Exception as e:
            logger.debug("audit_db_read_fallback", error=str(e))
            return self.query(
                tenant_id=tenant_id,
                category=category,
                action=action,
                outcome=outcome,
                limit=limit,
                offset=offset,
            )

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


_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail

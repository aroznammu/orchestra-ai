"""Kill switch with DB write-through.

In-memory state for fast checks, events persisted to PostgreSQL.
Once activated, NO spend operations can proceed until manually deactivated.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("bidding.kill_switch")


class KillSwitchEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    action: str
    triggered_by: str
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    affected_platforms: list[str] = Field(default_factory=list)
    affected_campaigns: list[str] = Field(default_factory=list)


async def _persist_ks_event(event: KillSwitchEvent) -> None:
    """Write-through to kill_switch_events DB table. Fire-and-forget."""
    try:
        from orchestra.db.models import KillSwitchEventLog
        from orchestra.db.session import async_session_factory

        async with async_session_factory() as session:
            record = KillSwitchEventLog(
                tenant_id=event.tenant_id,
                action=event.action,
                triggered_by=event.triggered_by,
                reason=event.reason,
                affected_platforms=event.affected_platforms,
                affected_campaigns=event.affected_campaigns,
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.debug("ks_db_write_skipped", error=str(e))


def _fire_persist(event: KillSwitchEvent) -> None:
    """Schedule DB persistence if an event loop is running."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_persist_ks_event(event))
    except RuntimeError:
        pass


class KillSwitch:
    """Global and per-tenant kill switch for spend operations."""

    def __init__(self) -> None:
        self._global_active: bool = False
        self._tenant_active: dict[str, bool] = {}
        self._event_log: list[KillSwitchEvent] = []

    @property
    def is_global_active(self) -> bool:
        return self._global_active

    def is_active(self, tenant_id: str) -> bool:
        """Check if kill switch is active for a tenant (or globally)."""
        return self._global_active or self._tenant_active.get(tenant_id, False)

    def activate_global(self, triggered_by: str, reason: str) -> KillSwitchEvent:
        """Activate kill switch for ALL tenants."""
        self._global_active = True

        event = KillSwitchEvent(
            tenant_id="GLOBAL",
            action="activate",
            triggered_by=triggered_by,
            reason=reason,
        )
        self._event_log.append(event)
        _fire_persist(event)

        logger.critical(
            "KILL_SWITCH_GLOBAL_ACTIVATED",
            triggered_by=triggered_by,
            reason=reason,
        )

        return event

    def deactivate_global(self, triggered_by: str) -> KillSwitchEvent:
        """Deactivate global kill switch."""
        self._global_active = False

        event = KillSwitchEvent(
            tenant_id="GLOBAL",
            action="deactivate",
            triggered_by=triggered_by,
            reason="Manual deactivation",
        )
        self._event_log.append(event)
        _fire_persist(event)

        logger.info("kill_switch_global_deactivated", triggered_by=triggered_by)

        return event

    def activate_tenant(
        self,
        tenant_id: str,
        triggered_by: str,
        reason: str,
        affected_platforms: list[str] | None = None,
        affected_campaigns: list[str] | None = None,
    ) -> KillSwitchEvent:
        """Activate kill switch for a specific tenant."""
        self._tenant_active[tenant_id] = True

        event = KillSwitchEvent(
            tenant_id=tenant_id,
            action="activate",
            triggered_by=triggered_by,
            reason=reason,
            affected_platforms=affected_platforms or [],
            affected_campaigns=affected_campaigns or [],
        )
        self._event_log.append(event)
        _fire_persist(event)

        logger.critical(
            "KILL_SWITCH_TENANT_ACTIVATED",
            tenant_id=tenant_id,
            triggered_by=triggered_by,
            reason=reason,
        )

        return event

    def deactivate_tenant(self, tenant_id: str, triggered_by: str) -> KillSwitchEvent:
        """Deactivate kill switch for a specific tenant."""
        self._tenant_active[tenant_id] = False

        event = KillSwitchEvent(
            tenant_id=tenant_id,
            action="deactivate",
            triggered_by=triggered_by,
            reason="Manual deactivation",
        )
        self._event_log.append(event)
        _fire_persist(event)

        logger.info(
            "kill_switch_tenant_deactivated",
            tenant_id=tenant_id,
            triggered_by=triggered_by,
        )

        return event

    def get_status(self) -> dict[str, Any]:
        """Get current kill switch status."""
        active_tenants = [t for t, active in self._tenant_active.items() if active]
        return {
            "global_active": self._global_active,
            "active_tenants": active_tenants,
            "total_activations": sum(1 for e in self._event_log if e.action == "activate"),
            "last_event": self._event_log[-1].model_dump() if self._event_log else None,
        }

    def get_event_log(self, tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get kill switch event history."""
        events = self._event_log
        if tenant_id:
            events = [e for e in events if e.tenant_id in (tenant_id, "GLOBAL")]
        return [e.model_dump() for e in events[-limit:]]


_kill_switch: KillSwitch | None = None


def get_kill_switch() -> KillSwitch:
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitch()
    return _kill_switch

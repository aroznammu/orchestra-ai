"""Automatic rollback mechanism.

Reverts bid/budget changes if an anomaly is confirmed.
Maintains a stack of recent changes that can be undone.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("risk.rollback")


class ChangeRecord(BaseModel):
    """A record of a bid/budget change that can be rolled back."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    platform: str
    campaign_id: str | None = None
    change_type: str  # bid_adjustment, budget_change, audience_change
    previous_value: float
    new_value: float
    change_pct: float
    applied_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    rolled_back: bool = False
    rolled_back_at: str | None = None
    rollback_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RollbackResult(BaseModel):
    success: bool
    change_id: str
    reverted_from: float
    reverted_to: float
    reason: str


class RollbackManager:
    """Manages change history and automatic rollback."""

    def __init__(self, tenant_id: str, max_history: int = 100) -> None:
        self.tenant_id = tenant_id
        self.max_history = max_history
        self._changes: list[ChangeRecord] = []

    def record_change(
        self,
        platform: str,
        change_type: str,
        previous_value: float,
        new_value: float,
        campaign_id: str | None = None,
        **metadata: Any,
    ) -> ChangeRecord:
        """Record a change that can potentially be rolled back."""
        change_pct = (
            (new_value - previous_value) / previous_value * 100
            if previous_value > 0 else 100.0
        )

        record = ChangeRecord(
            tenant_id=self.tenant_id,
            platform=platform,
            campaign_id=campaign_id,
            change_type=change_type,
            previous_value=previous_value,
            new_value=new_value,
            change_pct=round(change_pct, 2),
            metadata=metadata,
        )

        self._changes.append(record)

        # Trim history
        if len(self._changes) > self.max_history:
            self._changes = self._changes[-self.max_history:]

        logger.info(
            "change_recorded",
            change_id=record.id,
            platform=platform,
            change_type=change_type,
            change_pct=round(change_pct, 2),
        )

        return record

    def rollback(
        self,
        change_id: str,
        reason: str = "anomaly_detected",
    ) -> RollbackResult | None:
        """Roll back a specific change."""
        for change in self._changes:
            if change.id == change_id and not change.rolled_back:
                change.rolled_back = True
                change.rolled_back_at = datetime.now(UTC).isoformat()
                change.rollback_reason = reason

                logger.warning(
                    "change_rolled_back",
                    change_id=change_id,
                    platform=change.platform,
                    reverted_to=change.previous_value,
                    reason=reason,
                )

                return RollbackResult(
                    success=True,
                    change_id=change_id,
                    reverted_from=change.new_value,
                    reverted_to=change.previous_value,
                    reason=reason,
                )

        return None

    def rollback_recent(
        self,
        count: int = 1,
        reason: str = "anomaly_detected",
    ) -> list[RollbackResult]:
        """Roll back the N most recent (un-rolled-back) changes."""
        results: list[RollbackResult] = []
        recent = [c for c in reversed(self._changes) if not c.rolled_back]

        for change in recent[:count]:
            result = self.rollback(change.id, reason)
            if result:
                results.append(result)

        return results

    def rollback_by_platform(
        self,
        platform: str,
        reason: str = "platform_anomaly",
    ) -> list[RollbackResult]:
        """Roll back all recent changes on a specific platform."""
        results: list[RollbackResult] = []

        for change in reversed(self._changes):
            if change.platform == platform and not change.rolled_back:
                result = self.rollback(change.id, reason)
                if result:
                    results.append(result)

        return results

    def get_pending_rollbacks(self) -> list[ChangeRecord]:
        """Get changes that haven't been rolled back."""
        return [c for c in self._changes if not c.rolled_back]

    def get_rollback_history(self, limit: int = 50) -> list[ChangeRecord]:
        """Get changes that were rolled back."""
        rolled = [c for c in self._changes if c.rolled_back]
        return sorted(rolled, key=lambda c: c.rolled_back_at or "", reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "total_changes": len(self._changes),
            "rolled_back": sum(1 for c in self._changes if c.rolled_back),
            "pending": sum(1 for c in self._changes if not c.rolled_back),
        }

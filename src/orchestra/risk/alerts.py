"""Budget alert thresholds with notifications.

Fires alerts at 50%, 75%, and 90% of budget utilization
via webhook, email, or structured log.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("risk.alerts")


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(str, Enum):
    BUDGET_50 = "budget_50pct"
    BUDGET_75 = "budget_75pct"
    BUDGET_90 = "budget_90pct"
    BUDGET_100 = "budget_100pct"
    ANOMALY = "anomaly_detected"
    VELOCITY_SPIKE = "velocity_spike"
    KILL_SWITCH = "kill_switch_activated"
    APPROVAL_NEEDED = "approval_needed"
    POLICY_CHANGE = "policy_change"


ALERT_THRESHOLDS = [
    {"pct": 50, "type": AlertType.BUDGET_50, "severity": AlertSeverity.INFO},
    {"pct": 75, "type": AlertType.BUDGET_75, "severity": AlertSeverity.WARNING},
    {"pct": 90, "type": AlertType.BUDGET_90, "severity": AlertSeverity.CRITICAL},
    {"pct": 100, "type": AlertType.BUDGET_100, "severity": AlertSeverity.EMERGENCY},
]


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    acknowledged: bool = False
    acknowledged_by: str | None = None


class AlertManager:
    """Manages budget and risk alerts with optional email notification."""

    def __init__(self, notify_email: str | None = None) -> None:
        self._alerts: list[Alert] = []
        self._fired_thresholds: dict[str, set[int]] = {}
        self._notify_email = notify_email

    async def _notify(self, alert: Alert) -> None:
        """Send email for WARNING+ severity alerts."""
        if not self._notify_email:
            return
        if alert.severity in (AlertSeverity.INFO,):
            return

        try:
            from orchestra.notifications.email import send_alert_email

            subject = f"[OrchestraAI {alert.severity.value.upper()}] {alert.alert_type.value}"
            body = (
                f"Tenant: {alert.tenant_id}\n"
                f"Severity: {alert.severity.value}\n"
                f"Alert: {alert.message}\n\n"
                f"Details: {alert.details}\n\n"
                f"Time: {alert.created_at}\n"
                f"Alert ID: {alert.id}"
            )
            await send_alert_email(self._notify_email, subject, body)
        except Exception as e:
            logger.warning("alert_notify_failed", alert_id=alert.id, error=str(e))

    async def check_budget_thresholds(
        self,
        tenant_id: str,
        current_spend: float,
        budget_cap: float,
        context: str = "daily",
    ) -> list[Alert]:
        """Check if spend has crossed any alert thresholds."""
        if budget_cap <= 0:
            return []

        utilization_pct = (current_spend / budget_cap) * 100
        fired = self._fired_thresholds.get(tenant_id, set())
        new_alerts: list[Alert] = []

        for threshold in ALERT_THRESHOLDS:
            pct = threshold["pct"]
            if utilization_pct >= pct and pct not in fired:
                alert = Alert(
                    tenant_id=tenant_id,
                    alert_type=threshold["type"],
                    severity=threshold["severity"],
                    message=(
                        f"{context.title()} budget at {utilization_pct:.1f}% "
                        f"(${current_spend:.2f} / ${budget_cap:.2f})"
                    ),
                    details={
                        "context": context,
                        "current_spend": current_spend,
                        "budget_cap": budget_cap,
                        "utilization_pct": round(utilization_pct, 1),
                        "threshold_pct": pct,
                    },
                )
                new_alerts.append(alert)
                self._alerts.append(alert)
                fired.add(pct)

                log_fn = (
                    logger.critical if threshold["severity"] == AlertSeverity.EMERGENCY
                    else logger.warning if threshold["severity"] in (AlertSeverity.WARNING, AlertSeverity.CRITICAL)
                    else logger.info
                )
                log_fn(
                    "budget_alert",
                    tenant_id=tenant_id,
                    threshold=pct,
                    utilization=round(utilization_pct, 1),
                    severity=threshold["severity"].value,
                )
                await self._notify(alert)

        self._fired_thresholds[tenant_id] = fired
        return new_alerts

    async def fire_alert(
        self,
        tenant_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> Alert:
        """Fire a custom alert."""
        alert = Alert(
            tenant_id=tenant_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
        )
        self._alerts.append(alert)

        logger.warning(
            "alert_fired",
            tenant_id=tenant_id,
            alert_type=alert_type.value,
            severity=severity.value,
            message=message,
        )

        await self._notify(alert)
        return alert

    def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool:
        for alert in self._alerts:
            if alert.id == alert_id and not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                return True
        return False

    def get_active_alerts(self, tenant_id: str | None = None) -> list[Alert]:
        alerts = [a for a in self._alerts if not a.acknowledged]
        if tenant_id:
            alerts = [a for a in alerts if a.tenant_id == tenant_id]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_alert_history(self, tenant_id: str, limit: int = 100) -> list[Alert]:
        alerts = [a for a in self._alerts if a.tenant_id == tenant_id]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)[:limit]

    def reset_thresholds(self, tenant_id: str) -> None:
        """Reset fired thresholds (e.g., daily reset)."""
        self._fired_thresholds.pop(tenant_id, None)


# Singleton
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

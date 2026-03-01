"""Async approval workflow for bidding decisions.

Supports notification via webhook, email (placeholder), and CLI.
Pending approvals are tracked in-memory (DB persistence in production).
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("bidding.approval")


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class NotificationChannel(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    CLI = "cli"
    IN_APP = "in_app"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    decision_id: str
    action: str
    platform: str
    campaign_id: str | None = None
    current_value: float = 0.0
    proposed_value: float = 0.0
    change_pct: float = 0.0
    reasoning: str = ""
    risk_score: float = 0.0
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    resolved_at: str | None = None
    resolved_by: str | None = None
    expires_hours: int = 24
    notification_channels: list[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.IN_APP]
    )


class ApprovalWorkflow:
    """Manages pending approval requests."""

    def __init__(self) -> None:
        self._pending: dict[str, ApprovalRequest] = {}
        self._resolved: list[ApprovalRequest] = []

    def create_request(
        self,
        tenant_id: str,
        decision_id: str,
        action: str,
        platform: str,
        current_value: float,
        proposed_value: float,
        change_pct: float,
        reasoning: str = "",
        risk_score: float = 0.0,
        campaign_id: str | None = None,
        notification_channels: list[NotificationChannel] | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request and send notifications."""
        request = ApprovalRequest(
            tenant_id=tenant_id,
            decision_id=decision_id,
            action=action,
            platform=platform,
            campaign_id=campaign_id,
            current_value=current_value,
            proposed_value=proposed_value,
            change_pct=change_pct,
            reasoning=reasoning,
            risk_score=risk_score,
            notification_channels=notification_channels or [NotificationChannel.IN_APP],
        )

        self._pending[request.id] = request

        # Send notifications
        for channel in request.notification_channels:
            self._send_notification(channel, request)

        logger.info(
            "approval_requested",
            request_id=request.id,
            tenant_id=tenant_id,
            action=action,
            change_pct=change_pct,
        )

        return request

    def approve(self, request_id: str, approved_by: str) -> ApprovalRequest | None:
        """Approve a pending request."""
        request = self._pending.pop(request_id, None)
        if not request:
            return None

        request.status = ApprovalStatus.APPROVED
        request.resolved_at = datetime.now(UTC).isoformat()
        request.resolved_by = approved_by
        self._resolved.append(request)

        logger.info(
            "approval_granted",
            request_id=request_id,
            approved_by=approved_by,
        )

        return request

    def reject(self, request_id: str, rejected_by: str) -> ApprovalRequest | None:
        """Reject a pending request."""
        request = self._pending.pop(request_id, None)
        if not request:
            return None

        request.status = ApprovalStatus.REJECTED
        request.resolved_at = datetime.now(UTC).isoformat()
        request.resolved_by = rejected_by
        self._resolved.append(request)

        logger.info(
            "approval_rejected",
            request_id=request_id,
            rejected_by=rejected_by,
        )

        return request

    def get_pending(self, tenant_id: str | None = None) -> list[ApprovalRequest]:
        """Get all pending approval requests, optionally filtered by tenant."""
        pending = list(self._pending.values())
        if tenant_id:
            pending = [r for r in pending if r.tenant_id == tenant_id]
        return sorted(pending, key=lambda r: r.requested_at, reverse=True)

    def get_history(self, tenant_id: str, limit: int = 50) -> list[ApprovalRequest]:
        """Get resolved approval history for a tenant."""
        history = [r for r in self._resolved if r.tenant_id == tenant_id]
        return sorted(history, key=lambda r: r.resolved_at or "", reverse=True)[:limit]

    def expire_stale(self) -> int:
        """Expire approval requests that have exceeded their TTL."""
        now = datetime.now(UTC)
        expired_count = 0

        for request_id, request in list(self._pending.items()):
            requested = datetime.fromisoformat(request.requested_at)
            hours_elapsed = (now - requested).total_seconds() / 3600

            if hours_elapsed > request.expires_hours:
                request.status = ApprovalStatus.EXPIRED
                request.resolved_at = now.isoformat()
                self._resolved.append(request)
                del self._pending[request_id]
                expired_count += 1

                logger.info("approval_expired", request_id=request_id)

        return expired_count

    def _send_notification(
        self, channel: NotificationChannel, request: ApprovalRequest,
    ) -> None:
        """Send approval notification via the specified channel."""
        if channel == NotificationChannel.WEBHOOK:
            self._notify_webhook(request)
        elif channel == NotificationChannel.EMAIL:
            self._notify_email(request)
        elif channel == NotificationChannel.CLI:
            self._notify_cli(request)
        else:
            logger.debug("in_app_notification", request_id=request.id)

    def _notify_webhook(self, request: ApprovalRequest) -> None:
        """Send webhook notification (placeholder -- needs httpx in production)."""
        logger.info(
            "webhook_notification_queued",
            request_id=request.id,
            action=request.action,
        )

    def _notify_email(self, request: ApprovalRequest) -> None:
        """Send email notification (placeholder -- needs SMTP/SES config)."""
        logger.info(
            "email_notification_queued",
            request_id=request.id,
            action=request.action,
        )

    def _notify_cli(self, request: ApprovalRequest) -> None:
        """Log to console for CLI-based approval."""
        logger.info(
            "cli_approval_needed",
            request_id=request.id,
            action=request.action,
            platform=request.platform,
            change=f"${request.current_value:.2f} -> ${request.proposed_value:.2f} ({request.change_pct:+.1f}%)",
        )

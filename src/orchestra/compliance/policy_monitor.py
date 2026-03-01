"""Policy monitor -- tracks platform API changelog feeds.

Auto-disables features if a policy shift is detected, and alerts
the team to review and update ToS rules.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("compliance.policy_monitor")


class PolicyChange(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    platform: str
    change_type: str  # deprecation, new_restriction, limit_change, tos_update
    description: str
    severity: str = "info"  # info, warning, critical
    detected_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_url: str = ""
    auto_disabled_features: list[str] = Field(default_factory=list)
    requires_code_update: bool = False
    acknowledged: bool = False


class PolicyMonitor:
    """Monitors platform policy changes and manages feature flags."""

    def __init__(self) -> None:
        self._changes: list[PolicyChange] = []
        self._disabled_features: dict[str, set[str]] = {}  # platform -> set of features
        self._check_urls: dict[str, str] = {
            "twitter": "https://developer.twitter.com/en/updates",
            "youtube": "https://developers.google.com/youtube/v3/revision_history",
            "facebook": "https://developers.facebook.com/docs/graph-api/changelog",
            "instagram": "https://developers.facebook.com/docs/instagram-api/changelog",
            "linkedin": "https://learn.microsoft.com/en-us/linkedin/marketing/versioning",
            "tiktok": "https://developers.tiktok.com/doc/changelog",
            "pinterest": "https://developers.pinterest.com/docs/api/v5/changelog",
            "google_ads": "https://developers.google.com/google-ads/api/docs/release-notes",
        }

    def record_change(
        self,
        platform: str,
        change_type: str,
        description: str,
        severity: str = "info",
        source_url: str = "",
        auto_disable: list[str] | None = None,
    ) -> PolicyChange:
        """Record a detected policy change."""
        change = PolicyChange(
            platform=platform,
            change_type=change_type,
            description=description,
            severity=severity,
            source_url=source_url,
            auto_disabled_features=auto_disable or [],
            requires_code_update=severity == "critical",
        )

        self._changes.append(change)

        # Auto-disable features if critical
        if auto_disable:
            if platform not in self._disabled_features:
                self._disabled_features[platform] = set()
            self._disabled_features[platform].update(auto_disable)

            logger.warning(
                "features_auto_disabled",
                platform=platform,
                features=auto_disable,
                reason=description,
            )

        if severity == "critical":
            logger.critical(
                "CRITICAL_POLICY_CHANGE",
                platform=platform,
                description=description,
            )
        else:
            logger.info(
                "policy_change_recorded",
                platform=platform,
                change_type=change_type,
                severity=severity,
            )

        return change

    def is_feature_enabled(self, platform: str, feature: str) -> bool:
        """Check if a feature is still enabled for a platform."""
        disabled = self._disabled_features.get(platform, set())
        return feature not in disabled

    def re_enable_feature(self, platform: str, feature: str) -> None:
        """Re-enable a previously disabled feature (after manual review)."""
        if platform in self._disabled_features:
            self._disabled_features[platform].discard(feature)
            logger.info("feature_re_enabled", platform=platform, feature=feature)

    def get_pending_changes(self, platform: str | None = None) -> list[PolicyChange]:
        """Get unacknowledged policy changes."""
        changes = [c for c in self._changes if not c.acknowledged]
        if platform:
            changes = [c for c in changes if c.platform == platform]
        return sorted(changes, key=lambda c: c.detected_at, reverse=True)

    def acknowledge_change(self, change_id: str) -> bool:
        """Mark a policy change as acknowledged (after team review)."""
        for change in self._changes:
            if change.id == change_id:
                change.acknowledged = True
                return True
        return False

    def get_disabled_features(self) -> dict[str, list[str]]:
        """Get all currently disabled features across platforms."""
        return {p: sorted(f) for p, f in self._disabled_features.items() if f}

    def get_check_urls(self) -> dict[str, str]:
        """Get changelog URLs for manual monitoring."""
        return dict(self._check_urls)

    def get_status(self) -> dict[str, Any]:
        return {
            "total_changes": len(self._changes),
            "pending_review": sum(1 for c in self._changes if not c.acknowledged),
            "critical_pending": sum(
                1 for c in self._changes
                if not c.acknowledged and c.severity == "critical"
            ),
            "disabled_features": self.get_disabled_features(),
        }

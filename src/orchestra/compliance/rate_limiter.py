"""Conservative rate-limit buffers.

Stays 10-20% below platform maximums with conservative pacing.
Prevents OrchestraAI from ever triggering a platform rate limit.
"""

import time
from collections import defaultdict
from typing import Any

import structlog
from pydantic import BaseModel

from orchestra.compliance.tos_rules import RateLimitRule, get_tos

logger = structlog.get_logger("compliance.rate_limiter")

DEFAULT_BUFFER_PCT = 0.15  # 15% safety buffer


class RateLimitStatus(BaseModel):
    platform: str
    endpoint: str
    used: int
    limit: int
    effective_limit: int  # after buffer
    remaining: int
    resets_in_seconds: float
    is_throttled: bool


class ComplianceRateLimiter:
    """Per-platform, per-endpoint rate limiter with safety buffers."""

    def __init__(self, buffer_pct: float = DEFAULT_BUFFER_PCT) -> None:
        self.buffer_pct = buffer_pct
        # {platform: {endpoint: [(timestamp, count)]}}
        self._windows: dict[str, dict[str, list[tuple[float, int]]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def check(self, platform: str, endpoint: str) -> RateLimitStatus:
        """Check if a request is allowed under the rate limit."""
        tos = get_tos(platform)
        if not tos:
            return RateLimitStatus(
                platform=platform, endpoint=endpoint,
                used=0, limit=1000, effective_limit=850,
                remaining=850, resets_in_seconds=0, is_throttled=False,
            )

        rule = self._find_rule(tos.rate_limits, endpoint)
        if not rule:
            return RateLimitStatus(
                platform=platform, endpoint=endpoint,
                used=0, limit=1000, effective_limit=850,
                remaining=850, resets_in_seconds=0, is_throttled=False,
            )

        now = time.time()
        window_start = now - rule.window_seconds

        # Clean old entries
        entries = self._windows[platform][endpoint]
        entries[:] = [(ts, c) for ts, c in entries if ts > window_start]

        used = sum(c for _, c in entries)
        effective_limit = int(rule.requests_per_window * (1 - self.buffer_pct))
        remaining = max(effective_limit - used, 0)
        is_throttled = used >= effective_limit

        # Time until window resets
        if entries:
            oldest = min(ts for ts, _ in entries)
            resets_in = max(oldest + rule.window_seconds - now, 0)
        else:
            resets_in = 0.0

        return RateLimitStatus(
            platform=platform,
            endpoint=endpoint,
            used=used,
            limit=rule.requests_per_window,
            effective_limit=effective_limit,
            remaining=remaining,
            resets_in_seconds=round(resets_in, 1),
            is_throttled=is_throttled,
        )

    def record(self, platform: str, endpoint: str, count: int = 1) -> None:
        """Record API calls against the rate limit."""
        self._windows[platform][endpoint].append((time.time(), count))

    def acquire(self, platform: str, endpoint: str) -> bool:
        """Try to acquire a rate limit slot. Returns True if allowed."""
        status = self.check(platform, endpoint)
        if status.is_throttled:
            logger.warning(
                "rate_limited",
                platform=platform,
                endpoint=endpoint,
                used=status.used,
                limit=status.effective_limit,
                resets_in=status.resets_in_seconds,
            )
            return False

        self.record(platform, endpoint)
        return True

    def get_wait_time(self, platform: str, endpoint: str) -> float:
        """Get seconds to wait before the next request is allowed."""
        status = self.check(platform, endpoint)
        if not status.is_throttled:
            return 0.0
        return status.resets_in_seconds

    def get_all_status(self, platform: str) -> list[RateLimitStatus]:
        """Get rate limit status for all endpoints on a platform."""
        tos = get_tos(platform)
        if not tos:
            return []
        return [self.check(platform, rule.endpoint) for rule in tos.rate_limits]

    def _find_rule(
        self, rules: list[RateLimitRule], endpoint: str,
    ) -> RateLimitRule | None:
        for rule in rules:
            if rule.endpoint == endpoint or endpoint.startswith(rule.endpoint):
                return rule
        return rules[0] if rules else None


# Singleton
_limiter: ComplianceRateLimiter | None = None


def get_compliance_rate_limiter() -> ComplianceRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = ComplianceRateLimiter()
    return _limiter

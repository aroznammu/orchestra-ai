"""Unified attribution intelligence.

Tracks the customer journey across platforms to understand
which touchpoints drive conversions. No single platform can see this.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("intelligence.attribution")


class TouchPoint(BaseModel):
    """A single interaction in the customer journey."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    platform: str
    action: str  # impression, click, view, engagement, conversion
    timestamp: datetime
    campaign_id: str | None = None
    value: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttributionResult(BaseModel):
    """Attribution weights for a conversion."""

    touchpoints: list[TouchPoint] = Field(default_factory=list)
    attribution_model: str = "position_based"
    platform_credits: dict[str, float] = Field(default_factory=dict)
    campaign_credits: dict[str, float] = Field(default_factory=dict)
    total_value: float = 0.0
    journey_length: int = 0
    time_to_conversion_hours: float = 0.0


class AttributionEngine:
    """Multi-touch attribution across platforms."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._journeys: dict[str, list[TouchPoint]] = {}

    def record_touchpoint(
        self,
        journey_id: str,
        platform: str,
        action: str,
        timestamp: datetime,
        campaign_id: str | None = None,
        value: float = 0.0,
        **metadata: Any,
    ) -> TouchPoint:
        """Record a touchpoint in a customer journey."""
        tp = TouchPoint(
            platform=platform,
            action=action,
            timestamp=timestamp,
            campaign_id=campaign_id,
            value=value,
            metadata=metadata,
        )

        if journey_id not in self._journeys:
            self._journeys[journey_id] = []

        self._journeys[journey_id].append(tp)
        # Keep sorted by timestamp
        self._journeys[journey_id].sort(key=lambda t: t.timestamp)

        return tp

    def attribute_conversion(
        self,
        journey_id: str,
        conversion_value: float,
        model: str = "position_based",
    ) -> AttributionResult:
        """Attribute a conversion across all touchpoints in a journey."""
        touchpoints = self._journeys.get(journey_id, [])

        if not touchpoints:
            return AttributionResult(
                attribution_model=model,
                total_value=conversion_value,
            )

        if model == "last_touch":
            weights = _last_touch_weights(len(touchpoints))
        elif model == "first_touch":
            weights = _first_touch_weights(len(touchpoints))
        elif model == "linear":
            weights = _linear_weights(len(touchpoints))
        elif model == "time_decay":
            weights = _time_decay_weights(touchpoints)
        else:  # position_based (default)
            weights = _position_based_weights(len(touchpoints))

        # Compute credits
        platform_credits: dict[str, float] = {}
        campaign_credits: dict[str, float] = {}

        for tp, weight in zip(touchpoints, weights):
            credit = conversion_value * weight

            platform_credits[tp.platform] = (
                platform_credits.get(tp.platform, 0.0) + credit
            )

            if tp.campaign_id:
                campaign_credits[tp.campaign_id] = (
                    campaign_credits.get(tp.campaign_id, 0.0) + credit
                )

        # Time to conversion
        if len(touchpoints) >= 2:
            delta = touchpoints[-1].timestamp - touchpoints[0].timestamp
            hours = delta.total_seconds() / 3600
        else:
            hours = 0.0

        return AttributionResult(
            touchpoints=touchpoints,
            attribution_model=model,
            platform_credits={k: round(v, 2) for k, v in platform_credits.items()},
            campaign_credits={k: round(v, 2) for k, v in campaign_credits.items()},
            total_value=conversion_value,
            journey_length=len(touchpoints),
            time_to_conversion_hours=round(hours, 1),
        )

    def get_platform_attribution_summary(self) -> dict[str, Any]:
        """Summarize attribution across all tracked journeys."""
        platform_totals: dict[str, float] = {}
        platform_counts: dict[str, int] = {}

        for journey_id, touchpoints in self._journeys.items():
            for tp in touchpoints:
                platform_totals[tp.platform] = (
                    platform_totals.get(tp.platform, 0.0) + tp.value
                )
                platform_counts[tp.platform] = (
                    platform_counts.get(tp.platform, 0) + 1
                )

        return {
            "tenant_id": self.tenant_id,
            "total_journeys": len(self._journeys),
            "platform_value": {k: round(v, 2) for k, v in platform_totals.items()},
            "platform_touchpoints": platform_counts,
            "avg_journey_length": (
                sum(len(tps) for tps in self._journeys.values()) / len(self._journeys)
                if self._journeys else 0.0
            ),
        }


def _last_touch_weights(n: int) -> list[float]:
    weights = [0.0] * n
    weights[-1] = 1.0
    return weights


def _first_touch_weights(n: int) -> list[float]:
    weights = [0.0] * n
    weights[0] = 1.0
    return weights


def _linear_weights(n: int) -> list[float]:
    if n == 0:
        return []
    return [1.0 / n] * n


def _position_based_weights(n: int) -> list[float]:
    """40% first, 40% last, 20% distributed evenly among middle."""
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.5, 0.5]

    weights = [0.0] * n
    weights[0] = 0.4
    weights[-1] = 0.4

    middle_share = 0.2 / (n - 2) if n > 2 else 0.0
    for i in range(1, n - 1):
        weights[i] = middle_share

    return weights


def _time_decay_weights(touchpoints: list[TouchPoint]) -> list[float]:
    """More recent touchpoints get more credit (exponential decay)."""
    n = len(touchpoints)
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    last_ts = touchpoints[-1].timestamp
    raw: list[float] = []

    for tp in touchpoints:
        hours_before = (last_ts - tp.timestamp).total_seconds() / 3600
        # Half-life of 7 days
        weight = 2.0 ** (-hours_before / 168.0)
        raw.append(weight)

    total = sum(raw)
    return [w / total for w in raw] if total > 0 else _linear_weights(n)

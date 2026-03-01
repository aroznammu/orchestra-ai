"""Spend velocity monitoring.

Tracks the rate of spend over time and flags deviations from baseline.
A sudden increase in spend velocity ($/hour) triggers alerts.
"""

import time
from collections import deque
from typing import Any

import structlog

logger = structlog.get_logger("risk.velocity")

DEFAULT_VELOCITY_WINDOW = 3600  # 1 hour window
VELOCITY_SPIKE_MULTIPLIER = 3.0  # 3x baseline = spike


class SpendVelocityMonitor:
    """Monitors spend rate ($/hour) and detects velocity spikes."""

    def __init__(
        self,
        tenant_id: str,
        window_seconds: int = DEFAULT_VELOCITY_WINDOW,
        spike_multiplier: float = VELOCITY_SPIKE_MULTIPLIER,
    ) -> None:
        self.tenant_id = tenant_id
        self.window_seconds = window_seconds
        self.spike_multiplier = spike_multiplier
        self._events: deque[tuple[float, float]] = deque()  # (timestamp, amount)
        self._hourly_history: deque[float] = deque(maxlen=168)  # 7 days of hourly rates
        self._baseline_velocity: float = 0.0

    def record_spend(self, amount: float) -> dict[str, Any]:
        """Record a spend event and check velocity."""
        now = time.time()
        self._events.append((now, amount))

        # Clean old events outside window
        cutoff = now - self.window_seconds
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

        current_velocity = self._compute_velocity()
        is_spike = self._check_spike(current_velocity)

        if is_spike:
            logger.warning(
                "velocity_spike_detected",
                tenant_id=self.tenant_id,
                current_velocity=round(current_velocity, 2),
                baseline=round(self._baseline_velocity, 2),
                multiplier=round(
                    current_velocity / self._baseline_velocity
                    if self._baseline_velocity > 0 else 0, 2
                ),
            )

        return {
            "current_velocity_per_hour": round(current_velocity, 2),
            "baseline_velocity_per_hour": round(self._baseline_velocity, 2),
            "is_spike": is_spike,
            "events_in_window": len(self._events),
            "window_spend": round(sum(a for _, a in self._events), 2),
        }

    def update_baseline(self) -> None:
        """Update the baseline velocity from recent hourly data.

        Should be called periodically (e.g., every hour by scheduler).
        """
        current_velocity = self._compute_velocity()
        self._hourly_history.append(current_velocity)

        if self._hourly_history:
            self._baseline_velocity = sum(self._hourly_history) / len(self._hourly_history)

        logger.debug(
            "velocity_baseline_updated",
            tenant_id=self.tenant_id,
            baseline=round(self._baseline_velocity, 2),
            data_points=len(self._hourly_history),
        )

    def get_status(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "current_velocity": round(self._compute_velocity(), 2),
            "baseline_velocity": round(self._baseline_velocity, 2),
            "events_in_window": len(self._events),
            "window_spend": round(sum(a for _, a in self._events), 2),
            "historical_data_points": len(self._hourly_history),
        }

    def _compute_velocity(self) -> float:
        """Compute current $/hour rate from events in window."""
        if not self._events:
            return 0.0
        total_spend = sum(a for _, a in self._events)
        hours = self.window_seconds / 3600.0
        return total_spend / hours if hours > 0 else 0.0

    def _check_spike(self, current_velocity: float) -> bool:
        if self._baseline_velocity <= 0 or len(self._hourly_history) < 3:
            return False
        return current_velocity > self._baseline_velocity * self.spike_multiplier

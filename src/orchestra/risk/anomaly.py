"""Real-time anomaly detection on spend patterns.

Detects sudden spikes, unusual velocity, and deviation from baseline.
Uses statistical methods (z-score, IQR) for detection.
"""

import math
from collections import deque
from typing import Any

import structlog

from orchestra.core.exceptions import AnomalyDetectedError

logger = structlog.get_logger("risk.anomaly")

DEFAULT_WINDOW_SIZE = 30  # data points
Z_SCORE_THRESHOLD = 2.5
IQR_MULTIPLIER = 1.5


class AnomalyDetector:
    """Statistical anomaly detection for spend patterns."""

    def __init__(
        self,
        tenant_id: str,
        window_size: int = DEFAULT_WINDOW_SIZE,
        z_threshold: float = Z_SCORE_THRESHOLD,
    ) -> None:
        self.tenant_id = tenant_id
        self.window_size = window_size
        self.z_threshold = z_threshold
        self._history: deque[float] = deque(maxlen=window_size)
        self._platform_history: dict[str, deque[float]] = {}

    def check(
        self,
        amount: float,
        platform: str | None = None,
        auto_raise: bool = True,
    ) -> dict[str, Any]:
        """Check if a spend amount is anomalous.

        Returns anomaly report. Raises AnomalyDetectedError if auto_raise=True.
        """
        result = {
            "is_anomaly": False,
            "amount": amount,
            "platform": platform,
            "z_score": 0.0,
            "iqr_anomaly": False,
            "reason": "",
        }

        # Check global pattern
        if len(self._history) >= 5:
            z = self._z_score(amount, list(self._history))
            iqr_flag = self._iqr_check(amount, list(self._history))

            result["z_score"] = round(z, 2)
            result["iqr_anomaly"] = iqr_flag

            if abs(z) > self.z_threshold or iqr_flag:
                result["is_anomaly"] = True
                result["reason"] = (
                    f"Spend ${amount:.2f} deviates from pattern "
                    f"(z-score: {z:.2f}, IQR anomaly: {iqr_flag})"
                )

        # Check platform-specific pattern
        if platform:
            if platform not in self._platform_history:
                self._platform_history[platform] = deque(maxlen=self.window_size)

            ph = self._platform_history[platform]
            if len(ph) >= 5:
                pz = self._z_score(amount, list(ph))
                if abs(pz) > self.z_threshold:
                    result["is_anomaly"] = True
                    result["platform_z_score"] = round(pz, 2)
                    result["reason"] = (
                        f"Platform {platform} spend ${amount:.2f} anomalous "
                        f"(z-score: {pz:.2f})"
                    )

        if result["is_anomaly"]:
            logger.warning(
                "spend_anomaly_detected",
                tenant_id=self.tenant_id,
                amount=amount,
                platform=platform,
                z_score=result["z_score"],
                reason=result["reason"],
            )

            if auto_raise:
                raise AnomalyDetectedError(
                    result["reason"],
                    details={"tenant_id": self.tenant_id, **result},
                )

        return result

    def record(self, amount: float, platform: str | None = None) -> None:
        """Record a spend amount into the historical window."""
        self._history.append(amount)

        if platform:
            if platform not in self._platform_history:
                self._platform_history[platform] = deque(maxlen=self.window_size)
            self._platform_history[platform].append(amount)

    def get_baseline(self, platform: str | None = None) -> dict[str, float]:
        """Get the current statistical baseline."""
        history = list(self._history)
        if platform and platform in self._platform_history:
            history = list(self._platform_history[platform])

        if not history:
            return {"mean": 0.0, "std": 0.0, "median": 0.0, "data_points": 0}

        mean = sum(history) / len(history)
        std = self._std(history, mean)
        sorted_h = sorted(history)
        median = sorted_h[len(sorted_h) // 2]

        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "median": round(median, 2),
            "data_points": len(history),
        }

    def _z_score(self, value: float, data: list[float]) -> float:
        if not data:
            return 0.0
        mean = sum(data) / len(data)
        std = self._std(data, mean)
        if std == 0:
            return 0.0
        return (value - mean) / std

    def _iqr_check(self, value: float, data: list[float]) -> bool:
        if len(data) < 4:
            return False
        sorted_data = sorted(data)
        n = len(sorted_data)
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1
        lower = q1 - IQR_MULTIPLIER * iqr
        upper = q3 + IQR_MULTIPLIER * iqr
        return value < lower or value > upper

    @staticmethod
    def _std(data: list[float], mean: float) -> float:
        if len(data) < 2:
            return 0.0
        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        return math.sqrt(variance)

"""Cross-platform signal normalization.

Normalizes engagement metrics across platforms into a unified schema
so that a "like" on Twitter, YouTube, and LinkedIn can be compared.
"""

from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("moat.signals")


class SignalType(str, Enum):
    IMPRESSION = "impression"
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    CLICK = "click"
    SAVE = "save"
    FOLLOW = "follow"


PLATFORM_SIGNAL_WEIGHTS: dict[str, dict[str, float]] = {
    "twitter": {
        "impression": 0.01, "like": 0.5, "comment": 2.0,
        "share": 3.0, "click": 1.5, "save": 1.0,
    },
    "youtube": {
        "view": 0.05, "like": 0.3, "comment": 3.0,
        "share": 2.0, "click": 1.0, "save": 1.5,
    },
    "instagram": {
        "impression": 0.01, "like": 0.3, "comment": 2.5,
        "share": 3.0, "click": 2.0, "save": 2.5,
    },
    "facebook": {
        "impression": 0.01, "like": 0.3, "comment": 2.0,
        "share": 3.5, "click": 1.5, "save": 1.0,
    },
    "linkedin": {
        "impression": 0.02, "like": 0.5, "comment": 3.0,
        "share": 4.0, "click": 2.0, "save": 1.5,
    },
    "tiktok": {
        "view": 0.02, "like": 0.2, "comment": 2.0,
        "share": 3.0, "click": 1.5, "save": 2.0,
    },
    "pinterest": {
        "impression": 0.01, "like": 0.3, "click": 2.5,
        "save": 3.0, "share": 1.5,
    },
}


class NormalizedSignal(BaseModel):
    """A platform-agnostic engagement signal."""

    platform: str
    signal_type: SignalType
    raw_count: int
    weighted_value: float
    timestamp: datetime | None = None


class EngagementScore(BaseModel):
    """Unified engagement score for cross-platform comparison."""

    platform: str
    post_id: str
    raw_signals: dict[str, int] = Field(default_factory=dict)
    weighted_score: float = 0.0
    normalized_score: float = 0.0  # 0-100 scale
    signals: list[NormalizedSignal] = Field(default_factory=list)


class TimeOfDayIntelligence(BaseModel):
    """Optimal posting time analysis per platform."""

    platform: str
    best_hours: list[int] = Field(default_factory=list)
    best_days: list[int] = Field(default_factory=list)  # 0=Mon
    avg_engagement_by_hour: dict[int, float] = Field(default_factory=dict)


class AttentionDecayCurve(BaseModel):
    """Models how engagement decays over time after posting."""

    platform: str
    half_life_hours: float = 24.0
    peak_hour: int = 1
    decay_rate: float = 0.1
    total_engagement_captured_24h: float = 0.8  # % of total in first 24h


PLATFORM_ATTENTION_DECAY: dict[str, AttentionDecayCurve] = {
    "twitter": AttentionDecayCurve(
        platform="twitter", half_life_hours=4, peak_hour=0, decay_rate=0.25,
        total_engagement_captured_24h=0.95,
    ),
    "youtube": AttentionDecayCurve(
        platform="youtube", half_life_hours=168, peak_hour=24, decay_rate=0.01,
        total_engagement_captured_24h=0.3,
    ),
    "instagram": AttentionDecayCurve(
        platform="instagram", half_life_hours=12, peak_hour=2, decay_rate=0.08,
        total_engagement_captured_24h=0.85,
    ),
    "facebook": AttentionDecayCurve(
        platform="facebook", half_life_hours=8, peak_hour=1, decay_rate=0.12,
        total_engagement_captured_24h=0.9,
    ),
    "linkedin": AttentionDecayCurve(
        platform="linkedin", half_life_hours=24, peak_hour=4, decay_rate=0.05,
        total_engagement_captured_24h=0.75,
    ),
    "tiktok": AttentionDecayCurve(
        platform="tiktok", half_life_hours=48, peak_hour=6, decay_rate=0.03,
        total_engagement_captured_24h=0.55,
    ),
}


def normalize_engagement(
    platform: str,
    raw_metrics: dict[str, int],
    post_id: str = "",
) -> EngagementScore:
    """Normalize raw platform metrics into a unified engagement score."""
    weights = PLATFORM_SIGNAL_WEIGHTS.get(platform, {})

    signals: list[NormalizedSignal] = []
    total_weighted = 0.0

    for signal_name, count in raw_metrics.items():
        weight = weights.get(signal_name, 0.1)
        weighted = count * weight
        total_weighted += weighted

        try:
            signal_type = SignalType(signal_name)
        except ValueError:
            signal_type = SignalType.IMPRESSION

        signals.append(NormalizedSignal(
            platform=platform,
            signal_type=signal_type,
            raw_count=count,
            weighted_value=round(weighted, 4),
        ))

    # Normalize to 0-100 scale (log-based to handle viral posts)
    import math
    normalized = min(math.log1p(total_weighted) * 10, 100.0)

    return EngagementScore(
        platform=platform,
        post_id=post_id,
        raw_signals=raw_metrics,
        weighted_score=round(total_weighted, 4),
        normalized_score=round(normalized, 2),
        signals=signals,
    )


def compare_cross_platform(
    scores: list[EngagementScore],
) -> dict[str, Any]:
    """Compare engagement scores across platforms."""
    if not scores:
        return {"platforms": [], "best_platform": None, "comparison": []}

    ranked = sorted(scores, key=lambda s: s.normalized_score, reverse=True)

    return {
        "platforms": [s.platform for s in ranked],
        "best_platform": ranked[0].platform,
        "best_score": ranked[0].normalized_score,
        "comparison": [
            {
                "platform": s.platform,
                "post_id": s.post_id,
                "weighted_score": s.weighted_score,
                "normalized_score": s.normalized_score,
                "raw_signals": s.raw_signals,
            }
            for s in ranked
        ],
    }


def get_attention_decay(platform: str) -> AttentionDecayCurve:
    """Get the attention decay curve for a platform."""
    return PLATFORM_ATTENTION_DECAY.get(
        platform,
        AttentionDecayCurve(platform=platform),
    )


def score_content_structure(
    text: str,
    platform: str,
) -> dict[str, Any]:
    """Score content based on structural best practices per platform."""
    scores: dict[str, float] = {}

    # Length optimization
    optimal_lengths = {
        "twitter": 100, "instagram": 150, "linkedin": 200,
        "facebook": 80, "tiktok": 100, "youtube": 300,
    }
    optimal = optimal_lengths.get(platform, 150)
    length_ratio = len(text) / optimal if optimal else 1.0
    scores["length"] = max(0, 1.0 - abs(1.0 - length_ratio) * 0.5)

    # Question presence (boosts engagement)
    scores["has_question"] = 1.0 if "?" in text else 0.0

    # CTA presence
    cta_keywords = ["click", "link", "learn more", "sign up", "follow", "subscribe", "share"]
    scores["has_cta"] = 1.0 if any(kw in text.lower() for kw in cta_keywords) else 0.0

    # Emoji usage
    import re
    emoji_pattern = re.compile(r"[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff]")
    emoji_count = len(emoji_pattern.findall(text))
    scores["emoji_usage"] = min(emoji_count / 3.0, 1.0) if platform in ("instagram", "tiktok") else min(emoji_count / 1.0, 1.0)

    # Hashtag count
    hashtag_count = text.count("#")
    ideal_hashtags = {"instagram": 15, "twitter": 2, "linkedin": 3, "tiktok": 5}
    ideal = ideal_hashtags.get(platform, 3)
    scores["hashtags"] = max(0, 1.0 - abs(hashtag_count - ideal) / (ideal + 1))

    overall = sum(scores.values()) / len(scores) if scores else 0.0

    return {
        "overall_score": round(overall, 3),
        "component_scores": {k: round(v, 3) for k, v in scores.items()},
        "platform": platform,
    }

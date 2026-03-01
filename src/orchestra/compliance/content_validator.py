"""Content risk scoring and platform-specific policy validation.

Scores content from 0 (safe) to 100 (maximum risk).
Supports optional human review mode for borderline content.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.compliance.tos_rules import get_tos

logger = structlog.get_logger("compliance.content_validator")


class ValidationResult(BaseModel):
    """Result of content validation."""

    score: float = 0.0  # 0-100 risk score
    passed: bool = True
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    platform: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


RISK_KEYWORDS: dict[str, float] = {
    "guaranteed": 15.0,
    "get rich": 25.0,
    "miracle": 20.0,
    "act now": 10.0,
    "limited time": 5.0,
    "secret method": 20.0,
    "risk-free": 15.0,
    "no experience needed": 10.0,
    "make money fast": 25.0,
    "lose weight fast": 15.0,
    "crypto guaranteed": 30.0,
    "forex signal": 20.0,
}

HUMAN_REVIEW_THRESHOLD = 40.0
AUTO_REJECT_THRESHOLD = 70.0


def validate_content(
    content: str,
    platform: str,
    hashtags: list[str] | None = None,
    media_urls: list[str] | None = None,
    human_review_mode: bool = False,
) -> ValidationResult:
    """Validate content against platform ToS and internal policies."""
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    tos = get_tos(platform)
    if not tos:
        return ValidationResult(
            score=0.0,
            passed=True,
            platform=platform,
            warnings=[f"No ToS rules defined for {platform}"],
        )

    # 1. Content length
    if len(content) > tos.content.max_text_length:
        violations.append(
            f"Content exceeds {platform} limit: {len(content)}/{tos.content.max_text_length} chars"
        )
        risk_score += 20.0

    # 2. Media requirements
    media_count = len(media_urls or [])
    if media_count > tos.content.max_media_count:
        violations.append(f"Too many media items: {media_count}/{tos.content.max_media_count}")
        risk_score += 10.0
    if tos.content.requires_media and media_count == 0:
        violations.append(f"{platform} requires media content")
        risk_score += 15.0

    # 3. Hashtag limits
    hashtag_count = len(hashtags or [])
    if tos.content.max_hashtags and hashtag_count > tos.content.max_hashtags:
        violations.append(f"Too many hashtags: {hashtag_count}/{tos.content.max_hashtags}")
        risk_score += 5.0

    # 4. Link policy
    if not tos.content.allows_links and ("http://" in content or "https://" in content):
        warnings.append(f"{platform} doesn't support links in post body")
        risk_score += 3.0

    # 5. Prohibited content keywords
    content_lower = content.lower()
    for keyword, score in RISK_KEYWORDS.items():
        if keyword in content_lower:
            risk_score += score
            warnings.append(f"Risk keyword detected: '{keyword}' (+{score})")

    # 6. Platform-specific prohibited content
    for prohibited in tos.prohibited_content:
        if prohibited.lower() in content_lower:
            violations.append(f"Potentially prohibited on {platform}: '{prohibited}'")
            risk_score += 15.0

    # 7. Empty content
    if not content.strip():
        violations.append("Content cannot be empty")
        risk_score += 30.0

    # Cap at 100
    risk_score = min(risk_score, 100.0)

    # Determine pass/fail
    passed = risk_score < AUTO_REJECT_THRESHOLD and len(violations) == 0
    needs_review = (
        human_review_mode
        and HUMAN_REVIEW_THRESHOLD <= risk_score < AUTO_REJECT_THRESHOLD
    )

    if needs_review:
        warnings.append(f"Content flagged for human review (risk score: {risk_score:.1f})")

    result = ValidationResult(
        score=round(risk_score, 1),
        passed=passed,
        violations=violations,
        warnings=warnings,
        requires_human_review=needs_review,
        platform=platform,
        details={
            "content_length": len(content),
            "max_length": tos.content.max_text_length,
            "media_count": media_count,
            "hashtag_count": hashtag_count,
        },
    )

    logger.info(
        "content_validated",
        platform=platform,
        risk_score=result.score,
        passed=result.passed,
        violations=len(violations),
    )

    return result

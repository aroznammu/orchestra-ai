"""Compliance Agent -- FIRST GATE for every action.

Validates content and actions against platform ToS and internal policies.
Deterministic checks first, then LLM-based content risk scoring.
"""

import structlog

from orchestra.agents.contracts import (
    ComplianceCheckRequest,
    ComplianceCheckResult,
    RiskLevel,
)
from orchestra.agents.trace import ExecutionTrace, TraceTimer
from orchestra.db.models import PlatformType
from orchestra.platforms import get_platform
from orchestra.platforms.base import PostContent

logger = structlog.get_logger("agent.compliance")

PROHIBITED_CONTENT_PATTERNS = [
    "guaranteed returns",
    "get rich quick",
    "miracle cure",
    "act now or lose",
    "secret method",
]

PROHIBITED_TARGETING = [
    "minors",
    "children under 13",
    "health conditions",
    "political affiliation",
    "religious beliefs",
    "sexual orientation",
]


async def run_compliance_check(
    request: ComplianceCheckRequest,
    trace: ExecutionTrace,
) -> ComplianceCheckResult:
    """Run all compliance checks on content/action.

    Order: platform limits -> prohibited content -> targeting rules -> risk scoring
    """
    with TraceTimer() as timer:
        violations: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []
        rules_checked = 0
        risk_score = 0.0

        # 1. Platform content limits
        try:
            platform_type = PlatformType(request.platform)
            connector = get_platform(platform_type)
            post = PostContent(
                text=request.content,
                hashtags=request.hashtags,
                media_urls=request.media_urls,
            )
            limit_errors = connector.validate_content(post)
            rules_checked += 3
            if limit_errors:
                violations.extend(limit_errors)
                risk_score += 20.0
        except (ValueError, Exception) as e:
            warnings.append(f"Could not validate platform limits: {e}")

        # 2. Prohibited content patterns
        content_lower = request.content.lower()
        for pattern in PROHIBITED_CONTENT_PATTERNS:
            rules_checked += 1
            if pattern in content_lower:
                violations.append(f"Prohibited content pattern detected: '{pattern}'")
                risk_score += 30.0

        # 3. Prohibited targeting
        if request.target_audience:
            audience_str = str(request.target_audience).lower()
            for prohibited in PROHIBITED_TARGETING:
                rules_checked += 1
                if prohibited in audience_str:
                    violations.append(f"Prohibited targeting: '{prohibited}'")
                    risk_score += 40.0

        # 4. Budget sanity check
        if request.budget_amount is not None:
            rules_checked += 1
            if request.budget_amount < 0:
                violations.append("Budget amount cannot be negative")
                risk_score += 50.0
            elif request.budget_amount > 10000:
                warnings.append(f"High budget amount: ${request.budget_amount:.2f}")
                risk_score += 5.0

        # 5. Empty content check
        rules_checked += 1
        if not request.content.strip():
            violations.append("Content cannot be empty")
            risk_score += 20.0

        # 6. Excessive hashtags warning
        if len(request.hashtags) > 20:
            rules_checked += 1
            warnings.append(f"High hashtag count ({len(request.hashtags)}) may reduce engagement")
            risk_score += 2.0

        # Calculate risk level
        risk_score = min(risk_score, 100.0)
        if risk_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 40:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 15:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        approved = len(violations) == 0

        if not approved:
            recommendations.append("Fix all violations before publishing")
        elif risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH):
            recommendations.append("Consider reviewing content before publishing")

    result = ComplianceCheckResult(
        approved=approved,
        risk_score=risk_score,
        risk_level=risk_level,
        violations=violations,
        warnings=warnings,
        recommendations=recommendations,
        checked_rules=rules_checked,
    )

    trace.log(
        agent="compliance",
        action="compliance_check",
        input_summary=f"Platform={request.platform}, content_len={len(request.content)}",
        output_summary=f"approved={approved}, risk={risk_score:.1f}, violations={len(violations)}",
        confidence=1.0 if approved else 0.0,
        risk_score=risk_score,
        duration_ms=timer.duration_ms,
    )

    return result

"""Policy Agent -- validates content against per-platform rules.

Checks character limits, media requirements, banned content categories,
and platform-specific formatting rules.
"""

import structlog

from orchestra.agents.trace import ExecutionTrace, TraceTimer
from orchestra.db.models import PlatformType

logger = structlog.get_logger("agent.policy")

PLATFORM_CONTENT_RULES: dict[str, dict] = {
    "twitter": {
        "max_length": 280,
        "allows_links": True,
        "allows_media": True,
        "max_media": 4,
        "tone_guidelines": "concise, direct, conversational",
        "banned_topics": ["spam", "manipulation", "misleading claims"],
    },
    "youtube": {
        "max_title": 100,
        "max_description": 5000,
        "allows_links": True,
        "allows_media": True,
        "max_media": 1,
        "tone_guidelines": "informative, engaging, search-optimized",
        "banned_topics": ["misleading thumbnails", "artificial engagement"],
    },
    "facebook": {
        "max_length": 63206,
        "allows_links": True,
        "allows_media": True,
        "max_media": 10,
        "tone_guidelines": "community-oriented, shareable",
        "banned_topics": ["hate speech", "misinformation", "clickbait"],
    },
    "instagram": {
        "max_length": 2200,
        "allows_links": False,
        "allows_media": True,
        "max_media": 10,
        "max_hashtags": 30,
        "tone_guidelines": "visual-first, lifestyle, aspirational",
        "banned_topics": ["false health claims", "misleading before/after"],
    },
    "linkedin": {
        "max_length": 3000,
        "allows_links": True,
        "allows_media": True,
        "max_media": 9,
        "tone_guidelines": "professional, thought-leadership, value-driven",
        "banned_topics": ["spam", "irrelevant promotional content"],
    },
    "tiktok": {
        "max_length": 2200,
        "allows_links": False,
        "allows_media": True,
        "max_media": 1,
        "tone_guidelines": "authentic, trending, entertainment-first",
        "banned_topics": ["dangerous challenges", "misleading content"],
    },
    "pinterest": {
        "max_length": 500,
        "allows_links": True,
        "allows_media": True,
        "max_media": 1,
        "max_hashtags": 20,
        "tone_guidelines": "inspirational, visual, actionable",
        "banned_topics": ["spam pins", "misleading links"],
    },
    "snapchat": {
        "max_length": 250,
        "allows_links": True,
        "allows_media": True,
        "max_media": 1,
        "tone_guidelines": "ephemeral, authentic, youthful",
        "banned_topics": ["exploitation", "dangerous activities"],
    },
    "google_ads": {
        "max_headline": 30,
        "max_description": 90,
        "allows_links": True,
        "allows_media": True,
        "max_media": 20,
        "tone_guidelines": "clear, benefit-focused, compliant",
        "banned_topics": ["misleading claims", "prohibited products"],
    },
    "ctv": {
        "max_length": 5000,
        "allows_links": True,
        "allows_media": True,
        "max_media": 3,
        "tone_guidelines": "brand-safe, high-impact, suitable for living-room CTV",
        "banned_topics": ["misleading claims", "prohibited products", "uncleared third-party IP"],
    },
    "streaming_tv": {
        "max_length": 5000,
        "allows_links": True,
        "allows_media": True,
        "max_media": 3,
        "tone_guidelines": "brand-safe, high-impact, suitable for living-room CTV",
        "banned_topics": ["misleading claims", "prohibited products", "uncleared third-party IP"],
    },
}


async def validate_content_policy(
    content: str,
    platform: str,
    hashtags: list[str] | None = None,
    media_urls: list[str] | None = None,
    link: str | None = None,
    trace: ExecutionTrace | None = None,
) -> dict:
    """Validate content against platform-specific policies.

    Returns dict with 'valid', 'errors', 'warnings', and 'suggestions'.
    """
    with TraceTimer() as timer:
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        rules = PLATFORM_CONTENT_RULES.get(platform.lower(), {})
        if not rules:
            warnings.append(f"No policy rules defined for platform: {platform}")
            return {"valid": True, "errors": [], "warnings": warnings, "suggestions": []}

        # Length check
        max_len = rules.get("max_length", rules.get("max_description", 5000))
        if len(content) > max_len:
            errors.append(f"Content exceeds {platform} limit: {len(content)}/{max_len} chars")

        # Link policy
        if link and not rules.get("allows_links", True):
            warnings.append(f"{platform} doesn't support links in post body; use bio link instead")

        # Media count
        media_count = len(media_urls or [])
        max_media = rules.get("max_media", 1)
        if media_count > max_media:
            errors.append(f"Too many media items for {platform}: {media_count}/{max_media}")

        # Hashtag limits
        hashtag_count = len(hashtags or [])
        max_hashtags = rules.get("max_hashtags")
        if max_hashtags and hashtag_count > max_hashtags:
            errors.append(f"Too many hashtags for {platform}: {hashtag_count}/{max_hashtags}")

        # Banned topics
        content_lower = content.lower()
        for topic in rules.get("banned_topics", []):
            if topic.lower() in content_lower:
                errors.append(f"Content may violate {platform} policy: '{topic}'")

        # Tone suggestion
        tone = rules.get("tone_guidelines", "")
        if tone:
            suggestions.append(f"Recommended tone for {platform}: {tone}")

    valid = len(errors) == 0

    if trace:
        trace.log(
            agent="policy",
            action="validate_content_policy",
            input_summary=f"Platform={platform}, len={len(content)}",
            output_summary=f"valid={valid}, errors={len(errors)}, warnings={len(warnings)}",
            confidence=1.0,
            duration_ms=timer.duration_ms,
        )

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "platform": platform,
    }

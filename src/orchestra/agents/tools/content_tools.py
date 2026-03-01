"""Tool definitions for content generation and optimization."""

from typing import Any

from langchain_core.tools import tool

from orchestra.db.models import PlatformType
from orchestra.platforms import get_platform


@tool
def generate_caption(
    topic: str,
    platform: str,
    tone: str = "professional",
    max_length: int | None = None,
    include_cta: bool = True,
) -> dict[str, Any]:
    """Generate a caption/post text for a specific platform.

    Args:
        topic: What the post is about
        platform: Target platform (determines length and style)
        tone: Writing tone (professional, casual, humorous, urgent)
        max_length: Override max character limit
        include_cta: Include a call-to-action
    """
    connector = get_platform(PlatformType(platform))
    limit = max_length or connector.PLATFORM_LIMITS.max_text_length

    return {
        "topic": topic,
        "platform": platform,
        "tone": tone,
        "max_length": limit,
        "include_cta": include_cta,
        "note": "LLM will generate the actual caption using this spec",
        "caption": "",
    }


@tool
def optimize_hashtags(
    content: str,
    platform: str,
    max_hashtags: int = 10,
    category: str | None = None,
) -> dict[str, Any]:
    """Suggest optimized hashtags for content on a specific platform.

    Args:
        content: The post content to generate hashtags for
        platform: Target platform
        max_hashtags: Maximum number of hashtags to suggest
        category: Content category for hashtag relevance
    """
    connector = get_platform(PlatformType(platform))
    platform_max = connector.PLATFORM_LIMITS.max_hashtags
    effective_max = min(max_hashtags, platform_max) if platform_max else max_hashtags

    return {
        "content_preview": content[:100],
        "platform": platform,
        "max_hashtags": effective_max,
        "category": category,
        "hashtags": [],
        "note": "LLM will generate hashtags based on content and platform trends",
    }


@tool
def check_content_compliance(
    content: str,
    platform: str,
    hashtags: list[str] | None = None,
    media_urls: list[str] | None = None,
) -> dict[str, Any]:
    """Check if content complies with platform rules and OrchestraAI policies.

    Args:
        content: Post text to validate
        platform: Target platform
        hashtags: Hashtags to include
        media_urls: Media URLs to attach
    """
    from orchestra.platforms.base import PostContent

    connector = get_platform(PlatformType(platform))
    post = PostContent(
        text=content,
        hashtags=hashtags or [],
        media_urls=media_urls or [],
    )
    errors = connector.validate_content(post)

    return {
        "compliant": len(errors) == 0,
        "platform": platform,
        "errors": errors,
        "content_length": len(content),
        "max_length": connector.PLATFORM_LIMITS.max_text_length,
        "hashtag_count": len(hashtags or []),
        "media_count": len(media_urls or []),
    }


@tool
def adapt_content_for_platform(
    content: str,
    source_platform: str,
    target_platform: str,
) -> dict[str, Any]:
    """Adapt content from one platform's format to another.

    Args:
        content: Original content text
        source_platform: Platform the content was written for
        target_platform: Platform to adapt the content to
    """
    source = get_platform(PlatformType(source_platform))
    target = get_platform(PlatformType(target_platform))

    return {
        "source_platform": source_platform,
        "target_platform": target_platform,
        "source_max_length": source.PLATFORM_LIMITS.max_text_length,
        "target_max_length": target.PLATFORM_LIMITS.max_text_length,
        "needs_truncation": len(content) > target.PLATFORM_LIMITS.max_text_length,
        "original_length": len(content),
        "adapted_content": "",
        "note": "LLM will adapt the tone, length, and format for the target platform",
    }

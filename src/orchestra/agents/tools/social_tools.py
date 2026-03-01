"""Tool definitions for platform API operations.

These tools are called by agents via LangChain's tool-calling framework.
"""

from typing import Any

import structlog
from langchain_core.tools import tool

from orchestra.db.models import PlatformType
from orchestra.platforms import get_platform
from orchestra.platforms.base import PostContent

logger = structlog.get_logger("tools.social")


@tool
async def publish_post(
    platform: str,
    text: str,
    access_token: str,
    hashtags: list[str] | None = None,
    media_urls: list[str] | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    """Publish a post to a social media platform.

    Args:
        platform: Platform name (twitter, youtube, facebook, etc.)
        text: Post text content
        access_token: OAuth access token for the platform
        hashtags: Optional list of hashtags
        media_urls: Optional list of media URLs to attach
        link: Optional link to include
    """
    connector = get_platform(PlatformType(platform))
    content = PostContent(
        text=text,
        hashtags=hashtags or [],
        media_urls=media_urls or [],
        link=link,
    )

    errors = connector.validate_content(content)
    if errors:
        return {"success": False, "errors": errors}

    result = await connector.publish(content, access_token)
    logger.info("post_published", platform=platform, post_id=result.platform_post_id)
    return {"success": True, "post_id": result.platform_post_id, "url": result.url}


@tool
async def schedule_post(
    platform: str,
    text: str,
    access_token: str,
    scheduled_at: str,
    hashtags: list[str] | None = None,
    media_urls: list[str] | None = None,
) -> dict[str, Any]:
    """Schedule a post for future publishing.

    Args:
        platform: Platform name
        text: Post text content
        access_token: OAuth access token
        scheduled_at: ISO 8601 datetime for scheduling
        hashtags: Optional hashtags
        media_urls: Optional media URLs
    """
    from datetime import datetime

    connector = get_platform(PlatformType(platform))
    content = PostContent(
        text=text,
        hashtags=hashtags or [],
        media_urls=media_urls or [],
        scheduled_at=datetime.fromisoformat(scheduled_at),
    )

    result = await connector.schedule(content, access_token)
    return {
        "success": True,
        "schedule_id": result.platform_schedule_id,
        "scheduled_at": result.scheduled_at.isoformat(),
    }


@tool
async def get_post_analytics(
    platform: str,
    post_id: str,
    access_token: str,
) -> dict[str, Any]:
    """Get engagement analytics for a specific post.

    Args:
        platform: Platform name
        post_id: Platform-specific post ID
        access_token: OAuth access token
    """
    connector = get_platform(PlatformType(platform))
    result = await connector.get_analytics(post_id, access_token)
    return {
        "post_id": result.post_id,
        "platform": result.platform,
        "metrics": result.metrics.model_dump(),
    }


@tool
async def get_audience_insights(
    platform: str,
    access_token: str,
) -> dict[str, Any]:
    """Get audience demographics and insights for a platform.

    Args:
        platform: Platform name
        access_token: OAuth access token
    """
    connector = get_platform(PlatformType(platform))
    result = await connector.get_audience(access_token)
    return {
        "total_followers": result.total_followers,
        "demographics": result.demographics,
        "top_segments": [s.model_dump() for s in result.top_segments],
    }


@tool
async def delete_post(
    platform: str,
    post_id: str,
    access_token: str,
) -> dict[str, Any]:
    """Delete a published post from a platform.

    Args:
        platform: Platform name
        post_id: Platform-specific post ID
        access_token: OAuth access token
    """
    connector = get_platform(PlatformType(platform))
    success = await connector.delete_post(post_id, access_token)
    return {"success": success, "platform": platform, "post_id": post_id}

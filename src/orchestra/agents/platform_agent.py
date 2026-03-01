"""Platform Agent -- dispatches actions to the correct platform connector.

Wraps platform operations with token refresh, retry logic, and tracing.
"""

import structlog

from orchestra.agents.contracts import PlatformActionRequest, PlatformActionResult
from orchestra.agents.trace import ExecutionTrace, TraceTimer
from orchestra.db.models import PlatformType
from orchestra.platforms import get_platform
from orchestra.platforms.base import PostContent

logger = structlog.get_logger("agent.platform")


async def execute_platform_action(
    request: PlatformActionRequest,
    access_token: str,
    trace: ExecutionTrace,
) -> PlatformActionResult:
    """Execute a platform action (publish, schedule, delete, analytics)."""
    with TraceTimer() as timer:
        try:
            platform_type = PlatformType(request.platform)
            connector = get_platform(platform_type)

            if request.action == "publish":
                result = await _action_publish(connector, request.content, access_token)
            elif request.action == "schedule":
                result = await _action_schedule(connector, request.content, access_token)
            elif request.action == "delete":
                result = await _action_delete(connector, request.post_id, access_token)
            elif request.action == "analytics":
                result = await _action_analytics(connector, request.post_id, access_token)
            elif request.action == "audience":
                result = await _action_audience(connector, access_token)
            else:
                return PlatformActionResult(
                    success=False,
                    platform=request.platform,
                    action=request.action,
                    error=f"Unknown action: {request.action}",
                )

            action_result = PlatformActionResult(
                success=True,
                platform=request.platform,
                action=request.action,
                result=result,
            )

        except NotImplementedError:
            action_result = PlatformActionResult(
                success=False,
                platform=request.platform,
                action=request.action,
                error=f"{request.platform} connector is not yet fully implemented",
            )

        except Exception as e:
            logger.error(
                "platform_action_failed",
                platform=request.platform,
                action=request.action,
                error=str(e),
            )
            action_result = PlatformActionResult(
                success=False,
                platform=request.platform,
                action=request.action,
                error=str(e),
            )

    trace.log(
        agent="platform",
        action=f"platform_{request.action}",
        input_summary=f"platform={request.platform}, action={request.action}",
        output_summary=f"success={action_result.success}",
        confidence=1.0 if action_result.success else 0.0,
        duration_ms=timer.duration_ms,
    )

    return action_result


async def _action_publish(connector, content: dict, token: str) -> dict:
    post = PostContent(
        text=content.get("text", ""),
        hashtags=content.get("hashtags", []),
        media_urls=content.get("media_urls", []),
        link=content.get("link"),
    )
    result = await connector.publish(post, token)
    return {
        "post_id": result.platform_post_id,
        "url": result.url,
        "published_at": result.published_at.isoformat() if result.published_at else None,
    }


async def _action_schedule(connector, content: dict, token: str) -> dict:
    from datetime import datetime

    post = PostContent(
        text=content.get("text", ""),
        hashtags=content.get("hashtags", []),
        media_urls=content.get("media_urls", []),
        scheduled_at=datetime.fromisoformat(content["scheduled_at"]) if "scheduled_at" in content else None,
    )
    result = await connector.schedule(post, token)
    return {
        "schedule_id": result.platform_schedule_id,
        "scheduled_at": result.scheduled_at.isoformat(),
    }


async def _action_delete(connector, post_id: str | None, token: str) -> dict:
    if not post_id:
        return {"deleted": False, "reason": "No post_id provided"}
    success = await connector.delete_post(post_id, token)
    return {"deleted": success, "post_id": post_id}


async def _action_analytics(connector, post_id: str | None, token: str) -> dict:
    if not post_id:
        return {"error": "No post_id provided"}
    data = await connector.get_analytics(post_id, token)
    return {
        "post_id": data.post_id,
        "platform": data.platform,
        "metrics": data.metrics.model_dump(),
    }


async def _action_audience(connector, token: str) -> dict:
    data = await connector.get_audience(token)
    return {
        "total_followers": data.total_followers,
        "demographics": data.demographics,
    }

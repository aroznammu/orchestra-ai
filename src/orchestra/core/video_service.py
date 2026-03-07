"""Seedance video generation via fal.ai."""

from __future__ import annotations

import os

import fal_client
import structlog

from orchestra.agents.contracts import VideoGenerationResult
from orchestra.config import get_settings

logger = structlog.get_logger("core.video_service")

TEXT_TO_VIDEO_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/text-to-video"
IMAGE_TO_VIDEO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"


async def generate_video(
    prompt: str,
    image_url: str | None = None,
    duration: int = 5,
    aspect_ratio: str = "16:9",
) -> VideoGenerationResult:
    """Generate a video using Seedance via fal.ai.

    Selects text-to-video or image-to-video based on whether
    ``image_url`` is provided.
    """
    settings = get_settings()
    if not settings.has_fal:
        logger.warning("fal_api_key_missing")
        return VideoGenerationResult(prompt_used=prompt)

    os.environ.setdefault("FAL_KEY", settings.fal_api_key.get_secret_value())

    is_image_to_video = bool(image_url)
    model_id = IMAGE_TO_VIDEO_MODEL if is_image_to_video else TEXT_TO_VIDEO_MODEL

    arguments: dict = {
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "resolution": "720p",
    }
    if is_image_to_video:
        arguments["image_url"] = image_url

    logger.info(
        "video_generation_start",
        model=model_id,
        prompt_preview=prompt[:120],
        duration=duration,
        image_to_video=is_image_to_video,
    )

    try:
        result = await fal_client.subscribe_async(
            model_id,
            arguments=arguments,
            with_logs=True,
        )

        video_url = ""
        if isinstance(result, dict):
            video_obj = result.get("video", {})
            if isinstance(video_obj, dict):
                video_url = video_obj.get("url", "")
            elif isinstance(video_obj, str):
                video_url = video_obj

        logger.info("video_generation_complete", video_url=video_url[:80] if video_url else "")

        return VideoGenerationResult(
            video_url=video_url,
            duration=float(duration),
            model_used=model_id,
            thumbnail_url="",
            prompt_used=prompt,
        )

    except Exception:
        logger.exception("video_generation_failed")
        return VideoGenerationResult(prompt_used=prompt, model_used=model_id)

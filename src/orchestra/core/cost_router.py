"""LLM cost-aware model routing.

3-tier text routing:
  - Cloud: OpenAI / Anthropic / Google
  - Self-hosted: Ollama (Llama, Mistral)
  - Fine-tuned: future

Tiered video pipeline:
  - Draft/Testing: cheap models (Runway Gen-3 Alpha Turbo, Kling) for bulk variations
  - Upscale: premium models (Sora, Veo) only for validated winners
  - BYOK: bypass billing when tenant provides their own unlimited credentials
"""

from enum import Enum

import structlog

from orchestra.config import get_settings

logger = structlog.get_logger("cost_router")


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ModelTier(str, Enum):
    FAST = "fast"
    CAPABLE = "capable"
    LOCAL = "local"


class VideoTier(str, Enum):
    DRAFT = "draft"
    UPSCALE = "upscale"
    BYOK = "byok"


# Video model defaults per tier
VIDEO_MODELS = {
    VideoTier.DRAFT: {
        "primary": "runway-gen3-alpha-turbo",
        "fallback": "kling-v1",
        "cost_per_minute": 0.05,
    },
    VideoTier.UPSCALE: {
        "primary": "sora-v1",
        "fallback": "veo-v2",
        "cost_per_minute": 0.50,
    },
    VideoTier.BYOK: {
        "primary": "tenant-provided",
        "fallback": None,
        "cost_per_minute": 0.0,
    },
}


def route_model(complexity: TaskComplexity, prefer_local: bool = False) -> tuple[str, ModelTier]:
    """Select the best model for a task based on complexity and cost.

    Returns (model_name, tier).
    """
    settings = get_settings()

    if prefer_local:
        return settings.default_local_model, ModelTier.LOCAL

    if complexity == TaskComplexity.SIMPLE:
        if settings.has_openai:
            return settings.default_fast_model, ModelTier.FAST
        return settings.default_local_model, ModelTier.LOCAL

    if complexity == TaskComplexity.MODERATE:
        if settings.has_openai:
            return settings.default_fast_model, ModelTier.FAST
        if settings.has_anthropic:
            return settings.default_capable_model, ModelTier.CAPABLE
        return settings.default_local_model, ModelTier.LOCAL

    # COMPLEX
    if settings.has_anthropic:
        return settings.default_capable_model, ModelTier.CAPABLE
    if settings.has_openai:
        return settings.default_fast_model, ModelTier.FAST
    return settings.default_local_model, ModelTier.LOCAL


def route_video(
    *,
    is_validated_winner: bool = False,
    tenant_byok_key: str | None = None,
    tenant_byok_model: str | None = None,
) -> tuple[str, VideoTier, dict]:
    """Select a video generation model based on the tiered pipeline.

    Args:
        is_validated_winner: True if the content variant won an A/B test
            and should be upscaled to premium quality.
        tenant_byok_key: If provided, the tenant has their own API key
            for an unlimited video subscription -- bypass billing.
        tenant_byok_model: The model name to use with the BYOK key.

    Returns:
        (model_name, tier, config) where config has cost_per_minute and
        any extra routing metadata.
    """
    if tenant_byok_key:
        model = tenant_byok_model or "tenant-provided"
        config = {**VIDEO_MODELS[VideoTier.BYOK], "primary": model, "byok_key": tenant_byok_key}
        logger.info("video_route_byok", model=model)
        return model, VideoTier.BYOK, config

    if is_validated_winner:
        tier_config = VIDEO_MODELS[VideoTier.UPSCALE]
        logger.info("video_route_upscale", model=tier_config["primary"])
        return tier_config["primary"], VideoTier.UPSCALE, dict(tier_config)

    tier_config = VIDEO_MODELS[VideoTier.DRAFT]
    logger.info("video_route_draft", model=tier_config["primary"])
    return tier_config["primary"], VideoTier.DRAFT, dict(tier_config)

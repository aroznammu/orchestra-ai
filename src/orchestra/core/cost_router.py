"""LLM cost-aware model routing.

3-tier routing:
  - Cloud: OpenAI / Anthropic / Google
  - Self-hosted: Ollama (Llama, Mistral)
  - Fine-tuned: future
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

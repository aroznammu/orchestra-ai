"""Content Agent -- generates platform-optimized marketing content.

Uses LLM to generate caption variants, adapts tone/length per platform,
and runs compliance checks before returning results.
"""

import json

import httpx
import structlog

from orchestra.agents.compliance import run_compliance_check
from orchestra.agents.contracts import (
    ComplianceCheckRequest,
    ContentGenerationRequest,
    ContentGenerationResult,
)
from orchestra.agents.trace import ExecutionTrace, TraceTimer
from orchestra.config import get_settings
from orchestra.core.cost_router import ModelTier, TaskComplexity, route_model

logger = structlog.get_logger("agent.content")

PLATFORM_STYLE_GUIDES = {
    "twitter": {
        "max_len": 280,
        "style": "concise, punchy, use thread format for longer ideas",
        "cta_style": "direct link or reply prompt",
    },
    "youtube": {
        "max_len": 5000,
        "style": "SEO-optimized title + description, keyword-rich",
        "cta_style": "subscribe, like, comment prompts",
    },
    "instagram": {
        "max_len": 2200,
        "style": "storytelling, emoji-enhanced, hashtag clusters",
        "cta_style": "link in bio, save this post",
    },
    "facebook": {
        "max_len": 63206,
        "style": "conversational, question-driven, shareable",
        "cta_style": "share, tag a friend, visit link",
    },
    "linkedin": {
        "max_len": 3000,
        "style": "professional, insight-led, value-first",
        "cta_style": "follow for more, comment your thoughts",
    },
    "tiktok": {
        "max_len": 2200,
        "style": "trendy, authentic, hook in first line",
        "cta_style": "follow, duet this, link in bio",
    },
    "pinterest": {
        "max_len": 500,
        "style": "aspirational, actionable, keyword-rich",
        "cta_style": "save this pin, visit site",
    },
    "snapchat": {
        "max_len": 250,
        "style": "casual, ephemeral feel, direct",
        "cta_style": "swipe up, tap to learn more",
    },
    "google_ads": {
        "max_len": 90,
        "style": "benefit-focused, clear value proposition, keywords",
        "cta_style": "shop now, learn more, get started",
    },
}


async def generate_content(
    request: ContentGenerationRequest,
    trace: ExecutionTrace,
    prefer_local: bool = False,
) -> ContentGenerationResult:
    """Generate content variants for a campaign post.

    In production this calls the LLM. Currently builds the prompt spec
    for model routing and returns structured placeholders.
    """
    with TraceTimer() as timer:
        style = PLATFORM_STYLE_GUIDES.get(request.platform, {})
        max_len = request.max_length or style.get("max_len", 1000)

        prompt_spec = {
            "task": "generate_marketing_content",
            "topic": request.topic,
            "platform": request.platform,
            "tone": request.tone,
            "style_guide": style.get("style", "professional"),
            "cta_style": style.get("cta_style", ""),
            "max_length": max_len,
            "num_variants": request.num_variants,
            "include_hashtags": request.include_hashtags,
            "target_audience": request.target_audience,
            "constraints": request.constraints,
        }

        complexity = TaskComplexity.MODERATE
        model_name, tier = route_model(complexity, prefer_local=prefer_local)
        logger.info("content_model_selected", tier=tier.value, model=model_name)

        variants = []
        for i in range(request.num_variants):
            text = await _call_llm(
                model_name=model_name,
                tier=tier,
                topic=request.topic,
                platform=request.platform,
                tone=request.tone,
                max_len=max_len,
                style=style,
                variant_num=i + 1,
                target_audience=request.target_audience,
            )

            hashtags: list[str] = []
            if request.include_hashtags:
                hashtags = _extract_hashtags(text)
                if not hashtags:
                    tag = request.topic.replace(" ", "")
                    hashtags = [f"#{tag}"]

            variant = {
                "index": i,
                "text": text,
                "hashtags": hashtags,
                "estimated_engagement": 0.0,
                "model_tier": str(tier),
            }
            variants.append(variant)

        # Run compliance on the selected variant
        best_variant = 0
        if variants:
            check_req = ComplianceCheckRequest(
                content=variants[best_variant]["text"],
                platform=request.platform,
                action_type="publish",
                hashtags=variants[best_variant].get("hashtags", []),
            )
            compliance = await run_compliance_check(check_req, trace)
            if not compliance.approved:
                logger.warning(
                    "content_compliance_failed",
                    violations=compliance.violations,
                )

    result = ContentGenerationResult(
        variants=variants,
        selected_variant=best_variant,
        confidence=0.7,
        reasoning=f"Generated {len(variants)} variants for {request.platform} "
        f"using {tier} tier model",
    )

    trace.log(
        agent="content",
        action="generate_content",
        input_summary=f"topic='{request.topic}', platform={request.platform}, "
        f"variants={request.num_variants}",
        output_summary=f"generated={len(variants)} variants, tier={tier}",
        confidence=result.confidence,
        duration_ms=timer.duration_ms,
    )

    return result


def _build_prompt(
    topic: str,
    platform: str,
    tone: str,
    max_len: int,
    style: dict,
    variant_num: int,
    target_audience: dict | None = None,
) -> str:
    audience_line = ""
    if target_audience:
        audience_line = f"\nTarget audience: {json.dumps(target_audience)}"

    return (
        f"You are a world-class social media marketer. "
        f"Write a single {platform} post about: {topic}\n\n"
        f"Requirements:\n"
        f"- Tone: {tone}\n"
        f"- Style: {style.get('style', 'professional')}\n"
        f"- Maximum length: {max_len} characters\n"
        f"- Include a clear call-to-action ({style.get('cta_style', 'engage')})\n"
        f"- Include 2-4 relevant hashtags inline\n"
        f"- This is variant #{variant_num}, make it unique"
        f"{audience_line}\n\n"
        f"Write ONLY the post text. No explanations, no labels, no quotes around it."
    )


def _extract_hashtags(text: str) -> list[str]:
    import re
    return re.findall(r"#\w+", text)


async def _call_llm(
    model_name: str,
    tier: ModelTier,
    topic: str,
    platform: str,
    tone: str,
    max_len: int,
    style: dict,
    variant_num: int,
    target_audience: dict | None = None,
) -> str:
    prompt = _build_prompt(topic, platform, tone, max_len, style, variant_num, target_audience)
    settings = get_settings()

    if tier == ModelTier.LOCAL:
        return await _call_ollama(settings.ollama_base_url, settings.default_local_model, prompt)

    if tier == ModelTier.FAST and settings.has_openai:
        result = await _call_openai(settings.openai_api_key.get_secret_value(), model_name, prompt)
        if not result.startswith("[Content generation failed"):
            return result
        logger.warning("openai_failed_falling_back_to_ollama")

    if tier == ModelTier.CAPABLE and settings.has_anthropic:
        result = await _call_anthropic(settings.anthropic_api_key.get_secret_value(), model_name, prompt)
        if not result.startswith("[Content generation failed"):
            return result
        logger.warning("anthropic_failed_falling_back_to_ollama")

    return await _call_ollama(settings.ollama_base_url, settings.default_local_model, prompt)


async def _call_ollama(base_url: str, model: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.error("ollama_call_failed", error=str(e))
        return f"[Content generation failed: {e}]"


async def _call_openai(api_key: str, model: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.8,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error("openai_call_failed", error=str(e))
        return f"[Content generation failed: {e}]"


async def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error("anthropic_call_failed", error=str(e))
        return f"[Content generation failed: {e}]"

"""Content Agent -- generates platform-optimized marketing content.

Uses LLM to generate caption variants, adapts tone/length per platform,
and runs compliance checks before returning results.
"""

import structlog

from orchestra.agents.compliance import run_compliance_check
from orchestra.agents.contracts import (
    ComplianceCheckRequest,
    ContentGenerationRequest,
    ContentGenerationResult,
)
from orchestra.agents.trace import ExecutionTrace, TraceTimer
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

        # Route to appropriate model tier
        complexity = TaskComplexity.MODERATE
        model_name, tier = route_model(complexity, prefer_local=prefer_local)
        logger.info("content_model_selected", tier=tier.value, model=model_name)

        # Generate variants (LLM call placeholder)
        variants = []
        for i in range(request.num_variants):
            variant = {
                "index": i,
                "text": f"[Generated {request.platform} content about '{request.topic}' "
                f"in {request.tone} tone -- variant {i + 1}]",
                "hashtags": [f"#{request.topic.replace(' ', '')}" ] if request.include_hashtags else [],
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

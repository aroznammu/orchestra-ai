"""LangGraph Orchestrator -- the main AI agent workflow.

Routes user intents through a directed graph of specialized agents:
  classify -> compliance -> route -> [content -> video -> visual_compliance -> policy -> platform] -> respond
                                  -> [analytics] -> respond
                                  -> [optimize] -> respond

Every action passes through the compliance gate first.
Content creation additionally goes through video generation (conditional), visual
compliance scanning, policy validation, and platform dispatch.
"""

import json
from collections import OrderedDict
from typing import Any

import httpx
import structlog
from langgraph.graph import END, StateGraph

from orchestra.agents.analytics_agent import run_analytics
from orchestra.agents.compliance import run_compliance_check
from orchestra.agents.content import generate_content
from orchestra.agents.contracts import (
    AgentRole,
    AnalyticsRequest,
    ComplianceCheckRequest,
    ContentGenerationRequest,
    IntentType,
    OrchestratorState,
    OptimizationRequest,
    PlatformActionRequest,
    PolicyCheckResult,
    TaskStatus,
)
from orchestra.agents.optimizer import run_optimization
from orchestra.agents.platform_agent import execute_platform_action
from orchestra.agents.policy import validate_content_policy
from orchestra.agents.safety import check_safety, cleanup_trace
from orchestra.agents.trace import ExecutionTrace, TraceTimer
from orchestra.config import get_settings
from orchestra.core.cost_router import ModelTier, TaskComplexity, route_model
from orchestra.core.exceptions import AgentLoopError, AgentTimeoutError
from orchestra.core.video_service import generate_video
from orchestra.core.visual_compliance import check_visual_compliance

logger = structlog.get_logger("agent.orchestrator")

# Keyword table kept as the fallback when all LLM providers are unreachable.
INTENT_KEYWORDS: dict[str, IntentType] = {
    "create campaign": IntentType.CREATE_CAMPAIGN,
    "new campaign": IntentType.CREATE_CAMPAIGN,
    "publish": IntentType.PUBLISH_CONTENT,
    "post": IntentType.PUBLISH_CONTENT,
    "tweet": IntentType.PUBLISH_CONTENT,
    "schedule": IntentType.SCHEDULE_CONTENT,
    "optimize": IntentType.OPTIMIZE_CAMPAIGN,
    "improve": IntentType.OPTIMIZE_CAMPAIGN,
    "analytics": IntentType.GET_ANALYTICS,
    "metrics": IntentType.GET_ANALYTICS,
    "performance": IntentType.GET_ANALYTICS,
    "report": IntentType.GENERATE_REPORT,
    "summary": IntentType.GENERATE_REPORT,
    "connect": IntentType.CONNECT_PLATFORM,
    "compliance": IntentType.CHECK_COMPLIANCE,
    "check": IntentType.CHECK_COMPLIANCE,
    "budget": IntentType.REALLOCATE_BUDGET,
    "spend": IntentType.REALLOCATE_BUDGET,
    "video ad": IntentType.GENERATE_VIDEO,
    "video": IntentType.GENERATE_VIDEO,
    "generate video": IntentType.GENERATE_VIDEO,
    "video clip": IntentType.GENERATE_VIDEO,
}

_VALID_INTENTS = {it.value for it in IntentType}

_CLASSIFY_PROMPT = (
    "You are an intent classifier for a marketing automation platform.\n"
    "Classify the user's message into exactly ONE of these intents:\n\n"
    "{intent_list}\n\n"
    "User message: \"{user_input}\"\n\n"
    "Respond with ONLY the intent value (e.g. publish_content). No explanation."
)

# ---- In-memory LRU cache for recent classifications ----

_CACHE_MAX_SIZE = 256
_intent_cache: OrderedDict[str, IntentType] = OrderedDict()


def _cache_get(key: str) -> IntentType | None:
    if key in _intent_cache:
        _intent_cache.move_to_end(key)
        return _intent_cache[key]
    return None


def _cache_put(key: str, intent: IntentType) -> None:
    _intent_cache[key] = intent
    _intent_cache.move_to_end(key)
    while len(_intent_cache) > _CACHE_MAX_SIZE:
        _intent_cache.popitem(last=False)


def clear_intent_cache() -> None:
    """Exposed for tests."""
    _intent_cache.clear()


# ---- LLM-based classification ----

def _build_classify_prompt(user_input: str) -> str:
    intent_list = "\n".join(f"- {it.value}" for it in IntentType)
    return _CLASSIFY_PROMPT.format(intent_list=intent_list, user_input=user_input)


def _parse_intent_response(text: str) -> IntentType | None:
    """Extract an IntentType from the LLM's response text."""
    cleaned = text.strip().strip('"').strip("'").lower()
    if cleaned in _VALID_INTENTS:
        return IntentType(cleaned)
    for intent_val in _VALID_INTENTS:
        if intent_val in cleaned:
            return IntentType(intent_val)
    return None


async def _classify_via_openai(api_key: str, model: str, prompt: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 30,
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("classify_openai_failed", error=str(e))
        return None


async def _classify_via_anthropic(api_key: str, model: str, prompt: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 30,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.warning("classify_anthropic_failed", error=str(e))
        return None


async def _classify_via_ollama(base_url: str, model: str, prompt: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning("classify_ollama_failed", error=str(e))
        return None


async def _classify_with_llm(user_input: str) -> IntentType | None:
    """Try LLM classification using the cost router's SIMPLE tier.

    Falls through OpenAI -> Anthropic -> Ollama. Returns None if every
    provider fails so the caller can fall back to keyword matching.
    """
    model_name, tier = route_model(TaskComplexity.SIMPLE)
    prompt = _build_classify_prompt(user_input)
    settings = get_settings()

    providers: list[tuple[str, Any]] = []
    if tier == ModelTier.FAST and settings.has_openai:
        providers.append(("openai", lambda: _classify_via_openai(
            settings.openai_api_key.get_secret_value(), model_name, prompt)))
    if settings.has_anthropic:
        providers.append(("anthropic", lambda: _classify_via_anthropic(
            settings.anthropic_api_key.get_secret_value(), settings.default_capable_model, prompt)))
    providers.append(("ollama", lambda: _classify_via_ollama(
        settings.ollama_base_url, settings.default_local_model, prompt)))

    for provider_name, call_fn in providers:
        raw = await call_fn()
        if raw is not None:
            intent = _parse_intent_response(raw)
            if intent is not None:
                logger.info("intent_classified_llm", intent=intent.value, provider=provider_name)
                return intent
            logger.debug("llm_response_unparseable", provider=provider_name, raw=raw)

    return None


def _classify_with_keywords(user_input: str) -> IntentType:
    """Original keyword-based fallback."""
    lower = user_input.lower()
    for keyword, intent in INTENT_KEYWORDS.items():
        if keyword in lower:
            return intent
    return IntentType.GET_ANALYTICS


async def classify_intent(state: OrchestratorState) -> OrchestratorState:
    """Classify user input into an IntentType.

    1. Check in-memory cache for identical input.
    2. Try LLM classification (SIMPLE tier via cost router).
    3. Fall back to keyword matching if LLM is unavailable or unparseable.
    """
    user_input = state.user_input

    cached = _cache_get(user_input)
    if cached is not None:
        logger.debug("intent_cache_hit", intent=cached.value)
        state.intent = cached
        state.current_agent = AgentRole.COMPLIANCE
        state.depth += 1
        return state

    intent = await _classify_with_llm(user_input)

    if intent is None:
        intent = _classify_with_keywords(user_input)
        logger.info("intent_classified_keyword_fallback", intent=intent.value)

    _cache_put(user_input, intent)
    state.intent = intent
    state.current_agent = AgentRole.COMPLIANCE
    state.depth += 1
    return state


async def compliance_gate(state: OrchestratorState) -> OrchestratorState:
    """Run compliance check before any action."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.COMPLIANCE)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    content = state.raw_payload.get("content", state.user_input)
    platform = state.raw_payload.get("platform", "twitter")

    request = ComplianceCheckRequest(
        content=content,
        platform=platform,
        action_type=state.intent.value if state.intent else "unknown",
        hashtags=state.raw_payload.get("hashtags", []),
        media_urls=state.raw_payload.get("media_urls", []),
        budget_amount=state.raw_payload.get("budget_amount"),
    )

    result = await run_compliance_check(request, trace)
    state.compliance_result = result
    state.depth += 1
    return state


def route_after_compliance(state: OrchestratorState) -> str:
    """Decide next node based on compliance result and intent."""
    if state.error:
        return "respond"

    if state.compliance_result and not state.compliance_result.approved:
        return "respond"

    intent = state.intent
    if intent in (
        IntentType.PUBLISH_CONTENT,
        IntentType.SCHEDULE_CONTENT,
        IntentType.CREATE_CAMPAIGN,
        IntentType.GENERATE_VIDEO,
    ):
        return "content_node"
    elif intent in (IntentType.GET_ANALYTICS, IntentType.GENERATE_REPORT):
        return "analytics_node"
    elif intent in (IntentType.OPTIMIZE_CAMPAIGN, IntentType.REALLOCATE_BUDGET):
        return "optimize_node"
    elif intent == IntentType.CHECK_COMPLIANCE:
        return "respond"
    else:
        return "respond"


async def content_node(state: OrchestratorState) -> OrchestratorState:
    """Generate content via the content agent."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.CONTENT)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    request = ContentGenerationRequest(
        campaign_id=state.raw_payload.get("campaign_id", ""),
        platform=state.raw_payload.get("platform", "twitter"),
        topic=state.raw_payload.get("topic", state.user_input),
        tone=state.raw_payload.get("tone", "professional"),
        target_audience=state.raw_payload.get("target_audience", {}),
        num_variants=state.raw_payload.get("num_variants", 3),
    )

    result = await generate_content(request, trace)
    state.content_result = result
    state.depth += 1
    return state


async def policy_node(state: OrchestratorState) -> OrchestratorState:
    """Validate generated content against platform-specific policies."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.POLICY)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    platform = state.raw_payload.get("platform", "twitter")
    content_text = ""
    hashtags: list[str] = []

    if state.content_result and state.content_result.variants:
        selected = state.content_result.selected_variant
        variant = state.content_result.variants[selected] if selected < len(state.content_result.variants) else state.content_result.variants[0]
        content_text = variant.get("text", variant.get("content", ""))
        hashtags = variant.get("hashtags", [])

    if not content_text:
        content_text = state.raw_payload.get("content", state.user_input)

    result = await validate_content_policy(
        content=content_text,
        platform=platform,
        hashtags=hashtags or state.raw_payload.get("hashtags", []),
        media_urls=state.raw_payload.get("media_urls", []),
        link=state.raw_payload.get("link"),
        trace=trace,
    )

    state.policy_result = PolicyCheckResult(**result)
    state.depth += 1
    return state


def route_after_policy(state: OrchestratorState) -> str:
    """After policy check, dispatch to platform if publish/schedule, else respond."""
    if state.error:
        return "respond"

    if state.policy_result and not state.policy_result.valid:
        return "respond"

    if state.intent in (IntentType.PUBLISH_CONTENT, IntentType.SCHEDULE_CONTENT):
        return "platform_node"

    return "respond"


async def platform_node(state: OrchestratorState) -> OrchestratorState:
    """Dispatch publish/schedule action to the target platform."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.PLATFORM)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    platform = state.raw_payload.get("platform", "twitter")

    content_payload: dict[str, Any] = {}
    if state.content_result and state.content_result.variants:
        selected = state.content_result.selected_variant
        variant = state.content_result.variants[selected] if selected < len(state.content_result.variants) else state.content_result.variants[0]
        content_payload = {
            "text": variant.get("text", variant.get("content", "")),
            "hashtags": variant.get("hashtags", []),
            "media_urls": state.raw_payload.get("media_urls", []),
            "link": state.raw_payload.get("link"),
        }
    else:
        content_payload = {
            "text": state.raw_payload.get("content", state.user_input),
            "hashtags": state.raw_payload.get("hashtags", []),
            "media_urls": state.raw_payload.get("media_urls", []),
        }

    if state.intent == IntentType.SCHEDULE_CONTENT and "scheduled_at" in state.raw_payload:
        content_payload["scheduled_at"] = state.raw_payload["scheduled_at"]

    action = "schedule" if state.intent == IntentType.SCHEDULE_CONTENT else "publish"

    access_token = state.raw_payload.get("access_token", "")
    if not access_token:
        try:
            access_token = await _lookup_platform_token(state.tenant_id, platform)
        except Exception as e:
            logger.warning("platform_token_lookup_failed", platform=platform, error=str(e))

    if not access_token:
        state.platform_result = PlatformActionRequest(
            platform=platform, action=action, content=content_payload,
        )
        state.error = f"No access token for {platform}. Connect the platform first."
        state.depth += 1
        return state

    request = PlatformActionRequest(
        platform=platform,
        action=action,
        content=content_payload,
    )

    result = await execute_platform_action(request, access_token, trace)
    state.platform_result = result
    state.depth += 1
    return state


async def _lookup_platform_token(tenant_id: str, platform: str) -> str:
    """Look up encrypted access token for a platform from the DB."""
    try:
        from sqlalchemy import select
        from orchestra.db.models import PlatformConnection, PlatformType
        from orchestra.db.session import async_session_factory
        from orchestra.security.encryption import decrypt_token
        import uuid

        pt = PlatformType(platform)
        async with async_session_factory() as session:
            result = await session.execute(
                select(PlatformConnection).where(
                    PlatformConnection.tenant_id == uuid.UUID(tenant_id),
                    PlatformConnection.platform == pt,
                    PlatformConnection.is_active == True,  # noqa: E712
                )
            )
            conn = result.scalar_one_or_none()
            if conn:
                return decrypt_token(conn.access_token_encrypted)
    except Exception as e:
        logger.debug("token_lookup_fallback", error=str(e))
    return ""


async def analytics_node(state: OrchestratorState) -> OrchestratorState:
    """Fetch and aggregate analytics via the analytics agent."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.ANALYTICS)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    request = AnalyticsRequest(
        campaign_id=state.raw_payload.get("campaign_id"),
        platforms=state.raw_payload.get("platforms", []),
        date_range_days=state.raw_payload.get("date_range_days", 30),
        metrics=state.raw_payload.get("metrics", []),
        include_insights=True,
    )

    result = await run_analytics(request, trace, tenant_id=state.tenant_id)
    state.analytics_result = result
    state.depth += 1
    return state


async def optimize_node(state: OrchestratorState) -> OrchestratorState:
    """Run optimization via the optimization agent."""
    trace = ExecutionTrace(state.trace_id, state.tenant_id)

    try:
        check_safety(state, AgentRole.OPTIMIZER)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    request = OptimizationRequest(
        campaign_id=state.raw_payload.get("campaign_id", ""),
        optimization_type=state.raw_payload.get("optimization_type", "content"),
        variants=state.raw_payload.get("variants", []),
        historical_data=state.raw_payload.get("historical_data", {}),
        constraints=state.raw_payload.get("constraints", {}),
    )

    result = await run_optimization(request, trace)
    state.optimization_result = result
    state.depth += 1
    return state


async def video_node(state: OrchestratorState) -> OrchestratorState:
    """Generate a video via Seedance if the intent requires it.

    Passes through silently when video generation is not needed.
    """
    needs_video = (
        state.intent == IntentType.GENERATE_VIDEO
        or "video" in state.user_input.lower()
    )
    if not needs_video:
        state.depth += 1
        return state

    try:
        check_safety(state, AgentRole.VIDEO)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    prompt = state.raw_payload.get("video_prompt", state.user_input)
    image_url = state.raw_payload.get("image_url")
    duration = state.raw_payload.get("video_duration", 5)
    aspect_ratio = state.raw_payload.get("aspect_ratio", "16:9")

    result = await generate_video(
        prompt=prompt,
        image_url=image_url,
        duration=duration,
        aspect_ratio=aspect_ratio,
    )
    state.video_result = result
    state.depth += 1
    return state


async def visual_compliance_gate_node(state: OrchestratorState) -> OrchestratorState:
    """Scan generated video keyframes for copyright/IP violations.

    Passes through when no video was generated.
    """
    if not state.video_result or not state.video_result.video_url:
        state.depth += 1
        return state

    try:
        check_safety(state, AgentRole.VISUAL_COMPLIANCE)
    except (AgentLoopError, AgentTimeoutError) as e:
        state.error = str(e)
        state.is_complete = True
        return state

    result = await check_visual_compliance(
        video_url=state.video_result.video_url,
        tenant_id=state.tenant_id,
    )
    state.visual_compliance_result = result

    if not result.safe:
        logger.warning(
            "video_blocked_by_compliance",
            violations_count=len(result.violations),
            tenant_id=state.tenant_id,
        )
        state.video_result.video_url = ""

    state.depth += 1
    return state


def respond(state: OrchestratorState) -> OrchestratorState:
    """Build the final response from agent results."""
    state.is_complete = True
    cleanup_trace(state.trace_id)
    return state


def build_orchestrator_graph() -> StateGraph:
    """Construct the LangGraph orchestrator workflow."""
    graph = StateGraph(OrchestratorState)

    graph.add_node("classify", classify_intent)
    graph.add_node("compliance_gate", compliance_gate)
    graph.add_node("content_node", content_node)
    graph.add_node("video_node", video_node)
    graph.add_node("visual_compliance_gate", visual_compliance_gate_node)
    graph.add_node("policy_node", policy_node)
    graph.add_node("platform_node", platform_node)
    graph.add_node("analytics_node", analytics_node)
    graph.add_node("optimize_node", optimize_node)
    graph.add_node("respond", respond)

    graph.set_entry_point("classify")

    graph.add_edge("classify", "compliance_gate")

    graph.add_conditional_edges(
        "compliance_gate",
        route_after_compliance,
        {
            "content_node": "content_node",
            "analytics_node": "analytics_node",
            "optimize_node": "optimize_node",
            "respond": "respond",
        },
    )

    graph.add_edge("content_node", "video_node")
    graph.add_edge("video_node", "visual_compliance_gate")
    graph.add_edge("visual_compliance_gate", "policy_node")

    graph.add_conditional_edges(
        "policy_node",
        route_after_policy,
        {
            "platform_node": "platform_node",
            "respond": "respond",
        },
    )

    graph.add_edge("platform_node", "respond")
    graph.add_edge("analytics_node", "respond")
    graph.add_edge("optimize_node", "respond")
    graph.add_edge("respond", END)

    return graph


async def run_orchestrator(
    user_input: str,
    tenant_id: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """High-level entry point: run the full agent orchestration pipeline."""
    graph = build_orchestrator_graph()
    app = graph.compile()

    initial_state = OrchestratorState(
        tenant_id=tenant_id,
        user_input=user_input,
        raw_payload=payload or {},
    )

    final_state = await app.ainvoke(initial_state)

    result: dict[str, Any] = {
        "trace_id": final_state.get("trace_id", initial_state.trace_id),
        "intent": final_state.get("intent"),
        "is_complete": final_state.get("is_complete", False),
        "error": final_state.get("error"),
    }

    if final_state.get("compliance_result"):
        cr = final_state["compliance_result"]
        result["compliance"] = {
            "approved": cr.approved,
            "risk_level": cr.risk_level,
            "violations": cr.violations,
        }

    if final_state.get("content_result"):
        result["content"] = final_state["content_result"].model_dump()

    if final_state.get("policy_result"):
        pr = final_state["policy_result"]
        result["policy"] = {
            "valid": pr.valid,
            "errors": pr.errors,
            "warnings": pr.warnings,
            "suggestions": pr.suggestions,
        }

    if final_state.get("platform_result"):
        result["platform"] = final_state["platform_result"].model_dump() if hasattr(final_state["platform_result"], "model_dump") else {}

    if final_state.get("video_result"):
        result["video"] = final_state["video_result"].model_dump()

    if final_state.get("visual_compliance_result"):
        result["video_compliance"] = final_state["visual_compliance_result"].model_dump()

    if final_state.get("analytics_result"):
        result["analytics"] = final_state["analytics_result"].model_dump()

    if final_state.get("optimization_result"):
        result["optimization"] = final_state["optimization_result"].model_dump()

    return result

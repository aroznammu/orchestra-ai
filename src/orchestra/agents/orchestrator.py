"""LangGraph Orchestrator -- the main AI agent workflow.

Routes user intents through a directed graph of specialized agents:
  classify -> compliance -> route -> [content -> policy -> platform] -> respond
                                  -> [analytics] -> respond
                                  -> [optimize] -> respond

Every action passes through the compliance gate first.
Content creation additionally goes through policy validation and platform dispatch.
"""

from typing import Any

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
from orchestra.core.exceptions import AgentLoopError, AgentTimeoutError

logger = structlog.get_logger("agent.orchestrator")

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
}


def classify_intent(state: OrchestratorState) -> OrchestratorState:
    """Classify user input into an IntentType (keyword-based, LLM upgrade later)."""
    user_input = state.user_input.lower()

    for keyword, intent in INTENT_KEYWORDS.items():
        if keyword in user_input:
            state.intent = intent
            break

    if state.intent is None:
        state.intent = IntentType.GET_ANALYTICS

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
    if intent in (IntentType.PUBLISH_CONTENT, IntentType.SCHEDULE_CONTENT, IntentType.CREATE_CAMPAIGN):
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

    result = await run_analytics(request, trace)
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

    graph.add_edge("content_node", "policy_node")

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

    if final_state.get("analytics_result"):
        result["analytics"] = final_state["analytics_result"].model_dump()

    if final_state.get("optimization_result"):
        result["optimization"] = final_state["optimization_result"].model_dump()

    return result

"""Tests for the orchestrator pipeline.

Covers: LLM-based intent classification, keyword fallback, in-memory caching,
routing after compliance/policy, and policy node validation.
"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestra.agents.contracts import (
    ComplianceCheckResult,
    ContentGenerationResult,
    IntentType,
    OrchestratorState,
    PolicyCheckResult,
)
from orchestra.agents.orchestrator import (
    _classify_with_keywords,
    _parse_intent_response,
    classify_intent,
    clear_intent_cache,
    route_after_compliance,
    route_after_policy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state(user_input: str) -> OrchestratorState:
    return OrchestratorState(tenant_id="t1", user_input=user_input)


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Every test starts with an empty intent cache."""
    clear_intent_cache()
    yield
    clear_intent_cache()


def _mock_llm(intent: IntentType):
    """Return an AsyncMock for _classify_with_llm that returns the given intent."""
    return AsyncMock(return_value=intent)


def _mock_llm_fail():
    """Return an AsyncMock for _classify_with_llm that simulates total LLM failure."""
    return AsyncMock(return_value=None)


# ---------------------------------------------------------------------------
# A) LLM classification returns correct intents for natural language inputs
# ---------------------------------------------------------------------------

class TestLLMClassification:

    @pytest.mark.asyncio
    async def test_llm_returns_publish_content(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.PUBLISH_CONTENT)):
            state = _state("Post a photo of our new sneakers on Instagram")
            result = await classify_intent(state)
            assert result.intent == IntentType.PUBLISH_CONTENT

    @pytest.mark.asyncio
    async def test_llm_returns_create_campaign(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.CREATE_CAMPAIGN)):
            state = _state("I want to launch a new spring sale campaign")
            result = await classify_intent(state)
            assert result.intent == IntentType.CREATE_CAMPAIGN

    @pytest.mark.asyncio
    async def test_llm_returns_get_analytics(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.GET_ANALYTICS)):
            state = _state("How did our posts perform last quarter?")
            result = await classify_intent(state)
            assert result.intent == IntentType.GET_ANALYTICS

    @pytest.mark.asyncio
    async def test_llm_returns_schedule_content(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.SCHEDULE_CONTENT)):
            state = _state("Queue up these three posts for Monday morning")
            result = await classify_intent(state)
            assert result.intent == IntentType.SCHEDULE_CONTENT

    @pytest.mark.asyncio
    async def test_llm_returns_optimize_campaign(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.OPTIMIZE_CAMPAIGN)):
            state = _state("How can we get better ROI on our ads?")
            result = await classify_intent(state)
            assert result.intent == IntentType.OPTIMIZE_CAMPAIGN

    @pytest.mark.asyncio
    async def test_llm_returns_reallocate_budget(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.REALLOCATE_BUDGET)):
            state = _state("Move $500 from Facebook to TikTok ads")
            result = await classify_intent(state)
            assert result.intent == IntentType.REALLOCATE_BUDGET

    @pytest.mark.asyncio
    async def test_llm_returns_generate_report(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.GENERATE_REPORT)):
            state = _state("Build a PDF summary of Q1 results")
            result = await classify_intent(state)
            assert result.intent == IntentType.GENERATE_REPORT

    @pytest.mark.asyncio
    async def test_llm_returns_connect_platform(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.CONNECT_PLATFORM)):
            state = _state("Link my LinkedIn business account")
            result = await classify_intent(state)
            assert result.intent == IntentType.CONNECT_PLATFORM

    @pytest.mark.asyncio
    async def test_llm_returns_check_compliance(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.CHECK_COMPLIANCE)):
            state = _state("Verify this ad copy meets FTC guidelines")
            result = await classify_intent(state)
            assert result.intent == IntentType.CHECK_COMPLIANCE

    @pytest.mark.asyncio
    async def test_llm_sets_depth_and_agent(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm(IntentType.PUBLISH_CONTENT)):
            state = _state("Share our product")
            result = await classify_intent(state)
            assert result.depth == 1
            assert result.current_agent == "compliance"


# ---------------------------------------------------------------------------
# B) Fallback to keyword matching when LLM is unavailable
# ---------------------------------------------------------------------------

class TestKeywordFallback:

    @pytest.mark.asyncio
    async def test_fallback_tweet(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Create a tweet about our product")
            result = await classify_intent(state)
            assert result.intent == IntentType.PUBLISH_CONTENT

    @pytest.mark.asyncio
    async def test_fallback_analytics(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Show me the analytics for last month")
            result = await classify_intent(state)
            assert result.intent == IntentType.GET_ANALYTICS

    @pytest.mark.asyncio
    async def test_fallback_optimize(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Optimize our campaign budget")
            result = await classify_intent(state)
            assert result.intent == IntentType.OPTIMIZE_CAMPAIGN

    @pytest.mark.asyncio
    async def test_fallback_schedule(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Schedule this content for next week")
            result = await classify_intent(state)
            assert result.intent == IntentType.SCHEDULE_CONTENT

    @pytest.mark.asyncio
    async def test_fallback_report(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Generate a summary report")
            result = await classify_intent(state)
            assert result.intent == IntentType.GENERATE_REPORT

    @pytest.mark.asyncio
    async def test_fallback_budget(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Reallocate the budget across platforms")
            result = await classify_intent(state)
            assert result.intent == IntentType.REALLOCATE_BUDGET

    @pytest.mark.asyncio
    async def test_fallback_unknown_defaults_to_analytics(self):
        with patch("orchestra.agents.orchestrator._classify_with_llm", _mock_llm_fail()):
            state = _state("Something completely random")
            result = await classify_intent(state)
            assert result.intent == IntentType.GET_ANALYTICS

    def test_keyword_classifier_standalone(self):
        assert _classify_with_keywords("Create a tweet") == IntentType.PUBLISH_CONTENT
        assert _classify_with_keywords("Get analytics") == IntentType.GET_ANALYTICS
        assert _classify_with_keywords("Optimize this") == IntentType.OPTIMIZE_CAMPAIGN
        assert _classify_with_keywords("Schedule my content") == IntentType.SCHEDULE_CONTENT
        assert _classify_with_keywords("Random gibberish") == IntentType.GET_ANALYTICS
        assert _classify_with_keywords("Check compliance rules") == IntentType.CHECK_COMPLIANCE
        assert _classify_with_keywords("Connect my account") == IntentType.CONNECT_PLATFORM
        assert _classify_with_keywords("Show the report") == IntentType.GENERATE_REPORT
        assert _classify_with_keywords("Manage the budget wisely") == IntentType.REALLOCATE_BUDGET


# ---------------------------------------------------------------------------
# C) Caching prevents duplicate LLM calls
# ---------------------------------------------------------------------------

class TestIntentCache:

    @pytest.mark.asyncio
    async def test_second_call_uses_cache(self):
        mock = AsyncMock(return_value=IntentType.PUBLISH_CONTENT)
        with patch("orchestra.agents.orchestrator._classify_with_llm", mock):
            s1 = _state("Post this to Instagram")
            await classify_intent(s1)
            assert mock.call_count == 1

            s2 = _state("Post this to Instagram")
            await classify_intent(s2)
            assert mock.call_count == 1, "LLM should NOT be called again for identical input"
            assert s2.intent == IntentType.PUBLISH_CONTENT

    @pytest.mark.asyncio
    async def test_different_inputs_are_not_cached_together(self):
        call_map = {
            "Post to Instagram": IntentType.PUBLISH_CONTENT,
            "Get my analytics": IntentType.GET_ANALYTICS,
        }

        async def side_effect(user_input):
            return call_map.get(user_input)

        mock = AsyncMock(side_effect=side_effect)
        with patch("orchestra.agents.orchestrator._classify_with_llm", mock):
            s1 = _state("Post to Instagram")
            await classify_intent(s1)
            assert s1.intent == IntentType.PUBLISH_CONTENT

            s2 = _state("Get my analytics")
            await classify_intent(s2)
            assert s2.intent == IntentType.GET_ANALYTICS
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_clear_forces_new_llm_call(self):
        mock = AsyncMock(return_value=IntentType.PUBLISH_CONTENT)
        with patch("orchestra.agents.orchestrator._classify_with_llm", mock):
            s1 = _state("Post this")
            await classify_intent(s1)
            assert mock.call_count == 1

            clear_intent_cache()

            s2 = _state("Post this")
            await classify_intent(s2)
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_hit_after_fallback(self):
        """Even keyword-fallback results get cached."""
        mock = _mock_llm_fail()
        with patch("orchestra.agents.orchestrator._classify_with_llm", mock):
            s1 = _state("Create a tweet now")
            await classify_intent(s1)
            assert s1.intent == IntentType.PUBLISH_CONTENT
            assert mock.call_count == 1

            s2 = _state("Create a tweet now")
            await classify_intent(s2)
            assert s2.intent == IntentType.PUBLISH_CONTENT
            assert mock.call_count == 1, "Fallback result should be cached too"


# ---------------------------------------------------------------------------
# Parse intent response
# ---------------------------------------------------------------------------

class TestParseIntentResponse:

    def test_exact_match(self):
        assert _parse_intent_response("publish_content") == IntentType.PUBLISH_CONTENT

    def test_with_quotes(self):
        assert _parse_intent_response('"get_analytics"') == IntentType.GET_ANALYTICS

    def test_with_whitespace(self):
        assert _parse_intent_response("  schedule_content  \n") == IntentType.SCHEDULE_CONTENT

    def test_embedded_in_sentence(self):
        assert _parse_intent_response("The intent is optimize_campaign.") == IntentType.OPTIMIZE_CAMPAIGN

    def test_unknown_returns_none(self):
        assert _parse_intent_response("something_random") is None

    def test_empty_returns_none(self):
        assert _parse_intent_response("") is None

    def test_uppercase_normalised(self):
        assert _parse_intent_response("PUBLISH_CONTENT") == IntentType.PUBLISH_CONTENT


# ---------------------------------------------------------------------------
# Routing (unchanged logic, now with async classify)
# ---------------------------------------------------------------------------

class TestRoutingAfterCompliance:

    def test_route_content_after_compliance(self):
        state = _state("tweet")
        state.intent = IntentType.PUBLISH_CONTENT
        state.compliance_result = ComplianceCheckResult(
            approved=True, risk_score=5, risk_level="low", violations=[]
        )
        assert route_after_compliance(state) == "content_node"

    def test_route_analytics_after_compliance(self):
        state = _state("metrics")
        state.intent = IntentType.GET_ANALYTICS
        state.compliance_result = ComplianceCheckResult(
            approved=True, risk_score=5, risk_level="low", violations=[]
        )
        assert route_after_compliance(state) == "analytics_node"

    def test_route_respond_on_compliance_failure(self):
        state = _state("tweet")
        state.intent = IntentType.PUBLISH_CONTENT
        state.compliance_result = ComplianceCheckResult(
            approved=False, risk_score=80, risk_level="high", violations=["blocked"]
        )
        assert route_after_compliance(state) == "respond"

    def test_route_respond_on_error(self):
        state = _state("tweet")
        state.error = "Something went wrong"
        assert route_after_compliance(state) == "respond"


class TestRoutingAfterPolicy:

    def test_dispatch_to_platform_on_publish(self):
        state = _state("tweet this")
        state.intent = IntentType.PUBLISH_CONTENT
        state.policy_result = PolicyCheckResult(valid=True, platform="twitter")
        assert route_after_policy(state) == "platform_node"

    def test_dispatch_to_platform_on_schedule(self):
        state = _state("schedule this")
        state.intent = IntentType.SCHEDULE_CONTENT
        state.policy_result = PolicyCheckResult(valid=True, platform="twitter")
        assert route_after_policy(state) == "platform_node"

    def test_respond_on_create_campaign(self):
        state = _state("new campaign")
        state.intent = IntentType.CREATE_CAMPAIGN
        state.policy_result = PolicyCheckResult(valid=True, platform="twitter")
        assert route_after_policy(state) == "respond"

    def test_respond_on_policy_failure(self):
        state = _state("tweet")
        state.intent = IntentType.PUBLISH_CONTENT
        state.policy_result = PolicyCheckResult(
            valid=False, errors=["Content exceeds twitter limit"], platform="twitter"
        )
        assert route_after_policy(state) == "respond"

    def test_respond_on_error(self):
        state = _state("tweet")
        state.intent = IntentType.PUBLISH_CONTENT
        state.error = "Something broke"
        assert route_after_policy(state) == "respond"


# ---------------------------------------------------------------------------
# Policy node integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_policy_node_validates_content():
    from orchestra.agents.orchestrator import policy_node

    state = OrchestratorState(
        tenant_id="t1",
        user_input="Short tweet",
        raw_payload={"platform": "twitter"},
    )
    state.content_result = ContentGenerationResult(
        variants=[{"text": "Hello world!", "hashtags": []}],
        selected_variant=0,
        confidence=0.9,
    )

    result = await policy_node(state)
    assert result.policy_result is not None
    assert result.policy_result.valid is True


@pytest.mark.asyncio
async def test_policy_node_catches_long_content():
    from orchestra.agents.orchestrator import policy_node

    state = OrchestratorState(
        tenant_id="t1",
        user_input="Long tweet",
        raw_payload={"platform": "twitter"},
    )
    state.content_result = ContentGenerationResult(
        variants=[{"text": "x" * 300, "hashtags": []}],
        selected_variant=0,
        confidence=0.9,
    )

    result = await policy_node(state)
    assert result.policy_result is not None
    assert result.policy_result.valid is False
    assert any("exceeds" in e.lower() for e in result.policy_result.errors)


@pytest.mark.asyncio
async def test_orchestrator_endpoint_requires_auth(client):
    resp = await client.post(
        "/api/v1/orchestrator",
        json={"input": "Create a tweet"},
    )
    assert resp.status_code in (401, 403)

"""Tests for the orchestrator pipeline."""

import pytest

from orchestra.agents.contracts import IntentType, OrchestratorState, ComplianceCheckResult
from orchestra.agents.orchestrator import classify_intent, route_after_compliance


def test_classify_tweet_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Create a tweet about our product")
    result = classify_intent(state)
    assert result.intent == IntentType.PUBLISH_CONTENT


def test_classify_analytics_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Show me the analytics for last month")
    result = classify_intent(state)
    assert result.intent == IntentType.GET_ANALYTICS


def test_classify_optimize_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Optimize our campaign budget")
    result = classify_intent(state)
    assert result.intent == IntentType.OPTIMIZE_CAMPAIGN


def test_classify_schedule_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Schedule this content for next week")
    result = classify_intent(state)
    assert result.intent == IntentType.SCHEDULE_CONTENT


def test_classify_report_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Generate a summary report")
    result = classify_intent(state)
    assert result.intent == IntentType.GENERATE_REPORT


def test_classify_budget_intent():
    state = OrchestratorState(tenant_id="t1", user_input="Reallocate the budget across platforms")
    result = classify_intent(state)
    assert result.intent == IntentType.REALLOCATE_BUDGET


def test_classify_unknown_defaults_to_analytics():
    state = OrchestratorState(tenant_id="t1", user_input="Something completely random")
    result = classify_intent(state)
    assert result.intent == IntentType.GET_ANALYTICS


def test_route_content_after_compliance():
    state = OrchestratorState(tenant_id="t1", user_input="tweet")
    state.intent = IntentType.PUBLISH_CONTENT
    state.compliance_result = ComplianceCheckResult(
        approved=True, risk_score=5, risk_level="low", violations=[]
    )
    assert route_after_compliance(state) == "content_node"


def test_route_analytics_after_compliance():
    state = OrchestratorState(tenant_id="t1", user_input="metrics")
    state.intent = IntentType.GET_ANALYTICS
    state.compliance_result = ComplianceCheckResult(
        approved=True, risk_score=5, risk_level="low", violations=[]
    )
    assert route_after_compliance(state) == "analytics_node"


def test_route_respond_on_compliance_failure():
    state = OrchestratorState(tenant_id="t1", user_input="tweet")
    state.intent = IntentType.PUBLISH_CONTENT
    state.compliance_result = ComplianceCheckResult(
        approved=False, risk_score=80, risk_level="high", violations=["blocked"]
    )
    assert route_after_compliance(state) == "respond"


def test_route_respond_on_error():
    state = OrchestratorState(tenant_id="t1", user_input="tweet")
    state.error = "Something went wrong"
    assert route_after_compliance(state) == "respond"


@pytest.mark.asyncio
async def test_orchestrator_endpoint_requires_auth(client):
    resp = await client.post(
        "/api/v1/orchestrator",
        json={"input": "Create a tweet"},
    )
    assert resp.status_code in (401, 403)

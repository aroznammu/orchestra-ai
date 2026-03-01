"""Tests for the compliance agent."""

import pytest

from orchestra.agents.compliance import run_compliance_check
from orchestra.agents.contracts import ComplianceCheckRequest
from orchestra.agents.trace import ExecutionTrace


@pytest.fixture
def trace(tenant_id):
    return ExecutionTrace("test-trace", tenant_id)


@pytest.mark.asyncio
async def test_clean_content_passes(trace):
    req = ComplianceCheckRequest(
        content="Check out our new product launch! Great deals available.",
        platform="twitter",
        action_type="publish",
    )
    result = await run_compliance_check(req, trace)
    assert result.approved is True
    assert result.risk_level == "low"
    assert len(result.violations) == 0


@pytest.mark.asyncio
async def test_empty_content_fails(trace):
    req = ComplianceCheckRequest(
        content="",
        platform="twitter",
        action_type="publish",
    )
    result = await run_compliance_check(req, trace)
    assert result.approved is False
    assert len(result.violations) > 0


@pytest.mark.asyncio
async def test_content_exceeding_platform_limit_fails(trace):
    long_content = "x" * 300
    req = ComplianceCheckRequest(
        content=long_content,
        platform="twitter",
        action_type="publish",
    )
    result = await run_compliance_check(req, trace)
    assert result.approved is False


@pytest.mark.asyncio
async def test_negative_budget_fails(trace):
    req = ComplianceCheckRequest(
        content="Promote this post",
        platform="twitter",
        action_type="publish",
        budget_amount=-100.0,
    )
    result = await run_compliance_check(req, trace)
    assert result.approved is False


@pytest.mark.asyncio
async def test_compliance_returns_risk_score(trace):
    req = ComplianceCheckRequest(
        content="Normal marketing content here.",
        platform="instagram",
        action_type="publish",
    )
    result = await run_compliance_check(req, trace)
    assert 0 <= result.risk_score <= 100

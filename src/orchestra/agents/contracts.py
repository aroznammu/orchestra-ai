"""Strict typed contracts for inter-agent communication.

All agent communication uses typed Pydantic models -- no free-text between agents.
Every message is JSON-serializable, idempotent, and auditable.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    COMPLIANCE = "compliance"
    POLICY = "policy"
    CONTENT = "content"
    OPTIMIZER = "optimizer"
    ANALYTICS = "analytics"
    PLATFORM = "platform"


class IntentType(str, Enum):
    CREATE_CAMPAIGN = "create_campaign"
    PUBLISH_CONTENT = "publish_content"
    SCHEDULE_CONTENT = "schedule_content"
    OPTIMIZE_CAMPAIGN = "optimize_campaign"
    GET_ANALYTICS = "get_analytics"
    GENERATE_REPORT = "generate_report"
    CONNECT_PLATFORM = "connect_platform"
    CHECK_COMPLIANCE = "check_compliance"
    REALLOCATE_BUDGET = "reallocate_budget"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    """Standard message envelope between agents."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    from_agent: AgentRole
    to_agent: AgentRole
    intent: IntentType
    status: TaskStatus = TaskStatus.PENDING
    tenant_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    parent_message_id: str | None = None
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    depth: int = 0


class ComplianceCheckRequest(BaseModel):
    """Request to compliance agent for content/action validation."""

    content: str
    platform: str
    action_type: str
    hashtags: list[str] = Field(default_factory=list)
    media_urls: list[str] = Field(default_factory=list)
    target_audience: dict[str, Any] = Field(default_factory=dict)
    budget_amount: float | None = None


class ComplianceCheckResult(BaseModel):
    """Result from compliance agent."""

    approved: bool
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    checked_rules: int = 0


class ContentGenerationRequest(BaseModel):
    """Request to content agent."""

    campaign_id: str
    platform: str
    topic: str
    tone: str = "professional"
    target_audience: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    num_variants: int = 3
    include_hashtags: bool = True
    max_length: int | None = None


class ContentGenerationResult(BaseModel):
    """Result from content agent."""

    variants: list[dict[str, Any]] = Field(default_factory=list)
    selected_variant: int = 0
    confidence: float = 0.0
    reasoning: str = ""


class OptimizationRequest(BaseModel):
    """Request to optimization agent."""

    campaign_id: str
    optimization_type: str = "content"
    variants: list[dict[str, Any]] = Field(default_factory=list)
    historical_data: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)


class OptimizationResult(BaseModel):
    """Result from optimization agent."""

    recommended_variant: int = 0
    expected_improvement: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""
    next_experiment: dict[str, Any] = Field(default_factory=dict)


class AnalyticsRequest(BaseModel):
    """Request to analytics agent."""

    campaign_id: str | None = None
    platforms: list[str] = Field(default_factory=list)
    date_range_days: int = 30
    metrics: list[str] = Field(default_factory=list)
    include_insights: bool = True


class AnalyticsResult(BaseModel):
    """Result from analytics agent."""

    metrics: dict[str, Any] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    cross_platform_summary: dict[str, Any] = Field(default_factory=dict)


class PlatformActionRequest(BaseModel):
    """Request to platform agent."""

    platform: str
    action: str
    content: dict[str, Any] = Field(default_factory=dict)
    post_id: str | None = None


class PlatformActionResult(BaseModel):
    """Result from platform agent."""

    success: bool
    platform: str
    action: str
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class PolicyCheckResult(BaseModel):
    """Result from policy agent content validation."""

    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    platform: str = ""


class OrchestratorState(BaseModel):
    """Full state for the LangGraph orchestrator."""

    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    intent: IntentType | None = None
    messages: list[AgentMessage] = Field(default_factory=list)
    compliance_result: ComplianceCheckResult | None = None
    content_result: ContentGenerationResult | None = None
    policy_result: PolicyCheckResult | None = None
    optimization_result: OptimizationResult | None = None
    analytics_result: AnalyticsResult | None = None
    platform_result: PlatformActionResult | None = None
    current_agent: AgentRole = AgentRole.ORCHESTRATOR
    depth: int = 0
    max_depth: int = 10
    error: str | None = None
    is_complete: bool = False
    user_input: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)

"""API routes for the agent orchestrator."""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from orchestra.agents.orchestrator import run_orchestrator
from orchestra.api.deps import PaidUser

logger = structlog.get_logger("api.orchestrator")

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class OrchestrateRequest(BaseModel):
    input: str = Field(..., description="Natural language instruction")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured parameters")


class OrchestrateResponse(BaseModel):
    trace_id: str
    intent: str | None = None
    is_complete: bool = False
    error: str | None = None
    compliance: dict[str, Any] | None = None
    content: dict[str, Any] | None = None
    analytics: dict[str, Any] | None = None
    optimization: dict[str, Any] | None = None
    policy: dict[str, Any] | None = None
    platform: dict[str, Any] | None = None
    video: dict[str, Any] | None = None
    video_compliance: dict[str, Any] | None = None


def _serialize(obj: Any) -> Any:
    """Recursively convert enums and nested objects to JSON-safe primitives."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "value"):
        return obj.value
    return obj


@router.post("", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    user: PaidUser,
) -> OrchestrateResponse:
    """Run the AI agent orchestrator with a natural language instruction."""
    tenant_id = user.tenant_id

    logger.info(
        "orchestrator_request",
        tenant_id=tenant_id,
        user_id=user.sub,
        input_preview=request.input[:100],
    )

    result = await run_orchestrator(
        user_input=request.input,
        tenant_id=tenant_id,
        payload=request.payload,
    )

    return OrchestrateResponse(**_serialize(result))

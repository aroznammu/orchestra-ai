"""API routes for the agent orchestrator."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from orchestra.agents.orchestrator import run_orchestrator
from orchestra.api.middleware.auth import TokenPayload, get_current_user

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


@router.post("", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    user: TokenPayload = Depends(get_current_user),
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

    return OrchestrateResponse(**result)

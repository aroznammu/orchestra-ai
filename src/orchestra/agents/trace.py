"""Execution trace logging for agent decisions.

Every agent action is logged with reasoning, confidence, and timing
to support the "human-in-the-know" transparency principle.
"""

import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("agent.trace")


class TraceEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str
    agent: str
    action: str
    input_summary: str = ""
    output_summary: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    risk_score: float = 0.0
    duration_ms: float = 0.0
    token_usage: dict[str, int] = Field(default_factory=dict)
    cost_usd: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace:
    """Collects trace entries for a single orchestration run."""

    def __init__(self, trace_id: str, tenant_id: str) -> None:
        self.trace_id = trace_id
        self.tenant_id = tenant_id
        self.entries: list[TraceEntry] = []
        self._start_time = time.perf_counter()

    def log(
        self,
        agent: str,
        action: str,
        input_summary: str = "",
        output_summary: str = "",
        reasoning: str = "",
        confidence: float = 0.0,
        risk_score: float = 0.0,
        duration_ms: float = 0.0,
        token_usage: dict[str, int] | None = None,
        cost_usd: float = 0.0,
        **metadata: Any,
    ) -> TraceEntry:
        entry = TraceEntry(
            trace_id=self.trace_id,
            agent=agent,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            reasoning=reasoning,
            confidence=confidence,
            risk_score=risk_score,
            duration_ms=duration_ms,
            token_usage=token_usage or {},
            cost_usd=cost_usd,
            metadata=metadata,
        )
        self.entries.append(entry)

        logger.info(
            "agent_trace",
            trace_id=self.trace_id,
            tenant_id=self.tenant_id,
            agent=agent,
            action=action,
            confidence=confidence,
            risk_score=risk_score,
            duration_ms=round(duration_ms, 2),
        )
        return entry

    def get_summary(self) -> dict[str, Any]:
        total_duration = (time.perf_counter() - self._start_time) * 1000
        total_cost = sum(e.cost_usd for e in self.entries)
        total_tokens = {}
        for e in self.entries:
            for k, v in e.token_usage.items():
                total_tokens[k] = total_tokens.get(k, 0) + v

        return {
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "num_steps": len(self.entries),
            "total_duration_ms": round(total_duration, 2),
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "agents_involved": list({e.agent for e in self.entries}),
            "steps": [e.model_dump() for e in self.entries],
        }


class TraceTimer:
    """Context manager for timing agent operations."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.duration_ms: float = 0.0

    def __enter__(self) -> "TraceTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.duration_ms = (time.perf_counter() - self.start_time) * 1000

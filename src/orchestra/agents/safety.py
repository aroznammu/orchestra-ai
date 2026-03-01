"""Agent safety: loop prevention, depth limits, timeouts, cooldowns.

Prevents recursive self-calling, enforces max execution depth,
and implements cooldown periods between repeated actions.
"""

import time
from collections import defaultdict
from typing import Any

import structlog

from orchestra.agents.contracts import AgentRole, OrchestratorState
from orchestra.core.exceptions import AgentLoopError, AgentTimeoutError

logger = structlog.get_logger("agent.safety")

MAX_DEPTH = 10
MAX_AGENT_CALLS_PER_TRACE = 50
COOLDOWN_SECONDS = 2.0
AGENT_TIMEOUT_SECONDS = 120.0


class AgentCallTracker:
    """Tracks agent calls within a trace to prevent loops."""

    def __init__(self) -> None:
        self._call_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._last_call_time: dict[str, float] = {}
        self._trace_starts: dict[str, float] = {}

    def record_call(self, trace_id: str, agent: AgentRole) -> None:
        key = f"{trace_id}:{agent.value}"
        self._call_counts[trace_id][agent.value] += 1
        self._last_call_time[key] = time.time()

        if trace_id not in self._trace_starts:
            self._trace_starts[trace_id] = time.time()

    def get_call_count(self, trace_id: str, agent: AgentRole) -> int:
        return self._call_counts.get(trace_id, {}).get(agent.value, 0)

    def get_total_calls(self, trace_id: str) -> int:
        return sum(self._call_counts.get(trace_id, {}).values())

    def get_elapsed_seconds(self, trace_id: str) -> float:
        start = self._trace_starts.get(trace_id)
        if not start:
            return 0.0
        return time.time() - start

    def cleanup_trace(self, trace_id: str) -> None:
        self._call_counts.pop(trace_id, None)
        self._trace_starts.pop(trace_id, None)
        keys_to_remove = [k for k in self._last_call_time if k.startswith(trace_id)]
        for k in keys_to_remove:
            del self._last_call_time[k]


_tracker = AgentCallTracker()


def check_safety(state: OrchestratorState, next_agent: AgentRole) -> None:
    """Run all safety checks before dispatching to an agent.

    Raises AgentLoopError or AgentTimeoutError if limits are exceeded.
    """
    trace_id = state.trace_id

    # Depth check
    if state.depth >= state.max_depth:
        logger.error("max_depth_exceeded", trace_id=trace_id, depth=state.depth)
        raise AgentLoopError(
            f"Max depth {state.max_depth} exceeded",
            details={"trace_id": trace_id, "depth": state.depth},
        )

    # Total call count check
    total = _tracker.get_total_calls(trace_id)
    if total >= MAX_AGENT_CALLS_PER_TRACE:
        logger.error("max_calls_exceeded", trace_id=trace_id, total_calls=total)
        raise AgentLoopError(
            f"Max agent calls ({MAX_AGENT_CALLS_PER_TRACE}) exceeded in trace",
            details={"trace_id": trace_id, "total_calls": total},
        )

    # Self-call loop detection (same agent called > 3 times)
    agent_calls = _tracker.get_call_count(trace_id, next_agent)
    if agent_calls >= 3:
        logger.error(
            "agent_loop_detected",
            trace_id=trace_id,
            agent=next_agent.value,
            calls=agent_calls,
        )
        raise AgentLoopError(
            f"Agent {next_agent.value} called {agent_calls} times -- possible loop",
            details={"trace_id": trace_id, "agent": next_agent.value},
        )

    # Timeout check
    elapsed = _tracker.get_elapsed_seconds(trace_id)
    if elapsed > AGENT_TIMEOUT_SECONDS:
        logger.error("trace_timeout", trace_id=trace_id, elapsed=elapsed)
        raise AgentTimeoutError(
            f"Trace execution exceeded {AGENT_TIMEOUT_SECONDS}s timeout",
            details={"trace_id": trace_id, "elapsed_seconds": elapsed},
        )

    _tracker.record_call(trace_id, next_agent)


def cleanup_trace(trace_id: str) -> None:
    """Clean up tracking data after trace completes."""
    _tracker.cleanup_trace(trace_id)


def get_trace_stats(trace_id: str) -> dict[str, Any]:
    """Get execution stats for a trace."""
    return {
        "total_calls": _tracker.get_total_calls(trace_id),
        "elapsed_seconds": round(_tracker.get_elapsed_seconds(trace_id), 2),
        "call_counts": dict(_tracker._call_counts.get(trace_id, {})),
    }

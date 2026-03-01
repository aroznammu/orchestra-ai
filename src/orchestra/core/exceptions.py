"""Custom exception hierarchy for OrchestraAI."""

from typing import Any


class OrchestraError(Exception):
    """Base exception for all OrchestraAI errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# --- Authentication & Authorization ---


class AuthenticationError(OrchestraError):
    """Invalid or missing credentials."""


class AuthorizationError(OrchestraError):
    """User lacks permission for this action."""


class TokenExpiredError(AuthenticationError):
    """JWT or OAuth token has expired."""


# --- Resource errors ---


class NotFoundError(OrchestraError):
    """Requested resource does not exist."""


class ConflictError(OrchestraError):
    """Resource state conflict (e.g. duplicate)."""


class ValidationError(OrchestraError):
    """Input validation failure."""


# --- Platform errors ---


class PlatformError(OrchestraError):
    """Base error for platform connector issues."""


class PlatformAuthError(PlatformError):
    """Platform OAuth or token error."""


class PlatformRateLimitError(PlatformError):
    """Platform rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class PlatformAPIError(PlatformError):
    """Unexpected error from platform API."""


# --- Agent errors ---


class AgentError(OrchestraError):
    """Base error for AI agent issues."""


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""


class AgentLoopError(AgentError):
    """Agent entered a recursive loop."""


# --- Financial errors ---


class BudgetExceededError(OrchestraError):
    """Spend cap or budget limit reached."""


class AnomalyDetectedError(OrchestraError):
    """Anomalous spend pattern detected."""


class KillSwitchActivatedError(OrchestraError):
    """Emergency kill switch was triggered."""


# --- Compliance errors ---


class ComplianceError(OrchestraError):
    """Content or action violates platform ToS or internal policy."""


class RestrictedActionError(ComplianceError):
    """Action is on the hard-coded prohibited list."""


# --- Infrastructure errors ---


class DatabaseError(OrchestraError):
    """Database operation failed."""


class CacheError(OrchestraError):
    """Redis cache operation failed."""


class EventBusError(OrchestraError):
    """Event bus (Redis Streams / Kafka) operation failed."""

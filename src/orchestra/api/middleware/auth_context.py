"""Auth context middleware -- populates request.state.user for downstream middleware.

Runs early in the middleware chain (before audit and rate-limit) so that
those middlewares can read tenant_id and user_id from request.state.user.

This middleware never rejects requests -- it only decorates them. Actual
auth enforcement remains in the FastAPI dependency (get_current_user).
"""

import structlog
from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from orchestra.api.middleware.auth import TokenPayload
from orchestra.config import get_settings

logger = structlog.get_logger("auth_context")


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Extract JWT from Authorization header and set request.state.user.

    If the token is missing, malformed, or expired, request.state.user stays
    unset.  This is intentional -- public endpoints (health, docs, register)
    should pass through without error.  Protected endpoints still enforce
    auth via the ``get_current_user`` FastAPI dependency.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        self._try_populate_user(request)
        return await call_next(request)

    @staticmethod
    def _try_populate_user(request: Request) -> None:
        token = _extract_bearer_token(request)
        if not token:
            return

        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
            request.state.user = TokenPayload(**payload)
        except (JWTError, KeyError, ValueError):
            pass


def _extract_bearer_token(request: Request) -> str | None:
    """Return the raw JWT string from the Authorization header, or None."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    api_key = request.headers.get("x-api-key", "")
    if api_key:
        return api_key.strip()

    return None

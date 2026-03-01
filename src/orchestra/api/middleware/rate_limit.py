"""Per-tenant rate limiting middleware using Redis."""

import time

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis (falls back to in-memory)."""

    SKIP_PATHS = {"/health", "/healthz", "/ready", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, requests_per_minute: int = 60) -> None:  # noqa: ANN001
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._fallback_store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        client_key = self._get_client_key(request)
        if not await self._is_allowed(client_key):
            logger.warning("rate_limit_exceeded", client_key=client_key, path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again shortly.",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        remaining = await self._get_remaining(client_key)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response

    def _get_client_key(self, request: Request) -> str:
        tenant_id = None
        if hasattr(request.state, "user"):
            tenant_id = getattr(request.state.user, "tenant_id", None)
        if tenant_id:
            return f"rate:{tenant_id}"
        client_ip = request.client.host if request.client else "unknown"
        return f"rate:ip:{client_ip}"

    async def _is_allowed(self, key: str) -> bool:
        """In-memory sliding window (replaced by Redis in production)."""
        now = time.time()
        window_start = now - 60

        if key not in self._fallback_store:
            self._fallback_store[key] = []

        self._fallback_store[key] = [t for t in self._fallback_store[key] if t > window_start]
        if len(self._fallback_store[key]) >= self.requests_per_minute:
            return False

        self._fallback_store[key].append(now)
        return True

    async def _get_remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - 60
        if key not in self._fallback_store:
            return self.requests_per_minute
        current = len([t for t in self._fallback_store[key] if t > window_start])
        return self.requests_per_minute - current

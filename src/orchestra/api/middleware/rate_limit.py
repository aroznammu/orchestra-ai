"""Per-tenant rate limiting middleware with Redis backend + in-memory fallback."""

import time

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis, falls back to in-memory."""

    SKIP_PATHS = {"/health", "/healthz", "/ready", "/docs", "/openapi.json", "/redoc", "/", "/static"}

    def __init__(self, app, requests_per_minute: int = 60) -> None:  # noqa: ANN001
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._fallback_store: dict[str, list[float]] = {}
        self._redis = None
        self._redis_checked = False

    async def _get_redis(self):
        """Lazily connect to Redis. Returns None if unavailable."""
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis.asyncio as aioredis
            from orchestra.config import get_settings

            self._redis = aioredis.from_url(
                get_settings().redis_url,
                socket_connect_timeout=2,
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("rate_limiter_redis_connected")
            return self._redis
        except Exception as e:
            logger.info("rate_limiter_fallback_inmemory", reason=str(e))
            self._redis = None
            return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in self.SKIP_PATHS or path.startswith("/static/"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        if not await self._is_allowed(client_key):
            logger.warning("rate_limit_exceeded", client_key=client_key, path=path)
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
        r = await self._get_redis()
        if r is not None:
            return await self._is_allowed_redis(r, key)
        return self._is_allowed_memory(key)

    async def _is_allowed_redis(self, r, key: str) -> bool:
        """Sliding window via Redis sorted set."""
        try:
            now = time.time()
            window_start = now - 60
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, 120)
            results = await pipe.execute()
            count = results[1]
            return count < self.requests_per_minute
        except Exception:
            return self._is_allowed_memory(key)

    def _is_allowed_memory(self, key: str) -> bool:
        """In-memory sliding window fallback."""
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
        r = await self._get_redis()
        if r is not None:
            try:
                now = time.time()
                window_start = now - 60
                await r.zremrangebyscore(key, 0, window_start)
                count = await r.zcard(key)
                return self.requests_per_minute - count
            except Exception:
                pass
        now = time.time()
        window_start = now - 60
        if key not in self._fallback_store:
            return self.requests_per_minute
        current = len([t for t in self._fallback_store[key] if t > window_start])
        return self.requests_per_minute - current

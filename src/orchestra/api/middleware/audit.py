"""Audit log middleware -- records all API calls."""

import time
import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs every API request with timing, user, and tenant context."""

    SKIP_PATHS = {"/health", "/healthz", "/ready", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        user_id: str | None = None
        tenant_id: str | None = None
        try:
            if hasattr(request.state, "user"):
                user_id = request.state.user.sub
                tenant_id = request.state.user.tenant_id
        except AttributeError:
            pass

        response: Response | None = None
        error: Exception | None = None
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_data: dict[str, Any] = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params) if request.query_params else None,
                "status_code": response.status_code if response else 500,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "user_id": user_id,
                "tenant_id": tenant_id,
            }

            if error:
                log_data["error"] = str(error)
                logger.error("api_request", **log_data)
            elif response and response.status_code >= 400:
                logger.warning("api_request", **log_data)
            else:
                logger.info("api_request", **log_data)

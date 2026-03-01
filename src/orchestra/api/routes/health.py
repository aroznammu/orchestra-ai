"""Health and readiness probe endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from orchestra.db.session import async_session_factory

router = APIRouter(tags=["health"])
logger = structlog.get_logger("health")


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "healthy", "service": "orchestraai"}


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness probe -- checks database connectivity."""
    checks: dict[str, str] = {}

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = "connected"
    except Exception as e:
        logger.error("readiness_db_failed", error=str(e))
        checks["database"] = "unavailable"

    all_healthy = all(v != "unavailable" for v in checks.values())
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
    }

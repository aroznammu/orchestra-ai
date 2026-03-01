"""FastAPI application entry point for OrchestraAI."""

import pathlib
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles

from orchestra.api.middleware.audit import AuditLogMiddleware
from orchestra.api.middleware.rate_limit import RateLimitMiddleware
from orchestra.api.routes import audit, auth, gdpr, health, kill_switch, orchestrator, platforms
from orchestra.config import get_settings

STATIC_DIR = pathlib.Path(__file__).parent / "static"
from orchestra.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BudgetExceededError,
    ComplianceError,
    NotFoundError,
    OrchestraError,
    ValidationError,
)

settings = get_settings()
logger = structlog.get_logger("main")


async def _run_migrations() -> None:
    """Apply pending Alembic migrations if PostgreSQL is available."""
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(pathlib.Path(__file__).parents[2] / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        alembic_cfg.set_main_option(
            "script_location",
            str(pathlib.Path(__file__).parent / "db" / "migrations"),
        )

        import asyncio
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        logger.info("db_migrations_applied")
    except Exception as e:
        logger.warning("db_migrations_skipped", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    """Startup and shutdown events."""
    logger.info(
        "starting",
        app=settings.app_name,
        env=settings.app_env.value,
        stealth_mode=settings.stealth_mode,
        debug=settings.debug,
    )
    if "postgresql" in settings.database_url:
        await _run_migrations()
    yield
    logger.info("shutting_down")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-Native Marketing Orchestration Platform",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# --- Middleware (order matters: last added = first executed) ---

app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception handlers ---


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> ORJSONResponse:
    return ORJSONResponse(status_code=404, content={"error": exc.message, "details": exc.details})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> ORJSONResponse:
    return ORJSONResponse(status_code=422, content={"error": exc.message, "details": exc.details})


@app.exception_handler(AuthenticationError)
async def auth_handler(request: Request, exc: AuthenticationError) -> ORJSONResponse:
    return ORJSONResponse(status_code=401, content={"error": exc.message})


@app.exception_handler(AuthorizationError)
async def authz_handler(request: Request, exc: AuthorizationError) -> ORJSONResponse:
    return ORJSONResponse(status_code=403, content={"error": exc.message})


@app.exception_handler(ComplianceError)
async def compliance_handler(request: Request, exc: ComplianceError) -> ORJSONResponse:
    return ORJSONResponse(status_code=403, content={"error": exc.message, "details": exc.details})


@app.exception_handler(BudgetExceededError)
async def budget_handler(request: Request, exc: BudgetExceededError) -> ORJSONResponse:
    return ORJSONResponse(status_code=402, content={"error": exc.message, "details": exc.details})


@app.exception_handler(OrchestraError)
async def orchestra_error_handler(request: Request, exc: OrchestraError) -> ORJSONResponse:
    logger.error("unhandled_orchestra_error", error=exc.message, details=exc.details)
    return ORJSONResponse(status_code=500, content={"error": exc.message})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    logger.error("unhandled_exception", error=str(exc), type=type(exc).__name__)
    return ORJSONResponse(status_code=500, content={"error": "Internal server error"})


# --- Routers ---

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(platforms.router, prefix="/api/v1")
app.include_router(orchestrator.router, prefix="/api/v1")
app.include_router(gdpr.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(kill_switch.router, prefix="/api/v1")

# --- Dashboard UI ---

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_dashboard() -> FileResponse:
        return FileResponse(str(STATIC_DIR / "index.html"))

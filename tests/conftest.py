"""Shared test fixtures for OrchestraAI."""

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("FERNET_KEY", "CHANGE-ME-test-key-will-auto-generate")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-not-for-prod")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("STEALTH_MODE", "true")


@pytest.fixture
def tenant_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def auth_token(user_id: str, tenant_id: str) -> str:
    from orchestra.api.middleware.auth import create_access_token

    return create_access_token(
        user_id=uuid.UUID(user_id),
        tenant_id=uuid.UUID(tenant_id),
        role="owner",
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def client():
    from orchestra.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

"""Tests for the auth pipeline: AuthContextMiddleware, audit/rate-limit user
propagation, API key lookup, and removal of the dangerous DB-outage fallback."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from orchestra.api.middleware.auth import (
    TokenPayload,
    _hash_api_key,
    create_access_token,
    decode_access_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: str | None = None, tenant_id: str | None = None, role: str = "member") -> str:
    return create_access_token(
        user_id=uuid.UUID(user_id or str(uuid.uuid4())),
        tenant_id=uuid.UUID(tenant_id or str(uuid.uuid4())),
        role=role,
    )


# ---------------------------------------------------------------------------
# AuthContextMiddleware: request.state.user population
# ---------------------------------------------------------------------------

class TestAuthContextMiddleware:

    @pytest.mark.asyncio
    async def test_bearer_token_populates_request_state(self, client, auth_token, user_id, tenant_id):
        """Authenticated request should have request.state.user available."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id
        assert data["tenant_id"] == tenant_id
        assert data["role"] == "owner"

    @pytest.mark.asyncio
    async def test_missing_token_leaves_state_unset(self, client):
        """Unauthenticated request to public endpoint should succeed."""
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_token_leaves_state_unset(self, client):
        """A malformed bearer token should not crash, just leave user unset."""
        resp = await client.get(
            "/health",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_expired_token_leaves_state_unset(self, client):
        """An expired JWT should not populate request.state.user."""
        token = create_access_token(
            uuid.uuid4(), uuid.uuid4(), role="owner",
            expires_delta=timedelta(seconds=-10),
        )
        resp = await client.get("/health", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_api_key_header_populates_state(self, client, auth_token, user_id, tenant_id):
        """X-API-Key with a JWT value should populate request.state.user."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": auth_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id


# ---------------------------------------------------------------------------
# Audit middleware: user_id / tenant_id propagation
# ---------------------------------------------------------------------------

class TestAuditUserPropagation:

    @pytest.mark.asyncio
    async def test_audit_log_contains_user_context(self, client, auth_token, user_id, tenant_id):
        """The audit middleware should log the real user_id and tenant_id from
        request.state.user (set by AuthContextMiddleware)."""
        with patch("orchestra.api.middleware.audit.logger") as mock_logger:
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            assert resp.status_code == 200

            logged = False
            for call in mock_logger.info.call_args_list:
                if call.args and call.args[0] == "api_request":
                    assert call.kwargs["user_id"] == user_id
                    assert call.kwargs["tenant_id"] == tenant_id
                    logged = True
            assert logged, "audit log entry with user context was not emitted"

    @pytest.mark.asyncio
    async def test_audit_log_none_for_unauthenticated(self, client):
        """Unauthenticated requests should have user_id=None in audit."""
        with patch("orchestra.api.middleware.audit.logger") as mock_logger:
            await client.get("/health")

            for call in mock_logger.info.call_args_list:
                if call.args and call.args[0] == "api_request":
                    assert call.kwargs["user_id"] is None
                    assert call.kwargs["tenant_id"] is None


# ---------------------------------------------------------------------------
# Rate-limit middleware: tenant-based keying
# ---------------------------------------------------------------------------

class TestRateLimitTenantKey:

    def test_tenant_key_when_user_present(self):
        from starlette.requests import Request
        from starlette.datastructures import Headers
        from orchestra.api.middleware.rate_limit import RateLimitMiddleware

        mw = RateLimitMiddleware(app=MagicMock(), requests_per_minute=60)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "headers": [],
            "query_string": b"",
            "root_path": "",
            "server": ("127.0.0.1", 8000),
            "client": ("10.0.0.1", 12345),
        }
        request = Request(scope)
        tenant_id = str(uuid.uuid4())
        request.state.user = TokenPayload(
            sub=str(uuid.uuid4()),
            tenant_id=tenant_id,
            role="member",
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

        key = mw._get_client_key(request)
        assert key == f"rate:{tenant_id}"

    def test_ip_key_when_no_user(self):
        from starlette.requests import Request
        from orchestra.api.middleware.rate_limit import RateLimitMiddleware

        mw = RateLimitMiddleware(app=MagicMock(), requests_per_minute=60)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "headers": [],
            "query_string": b"",
            "root_path": "",
            "server": ("127.0.0.1", 8000),
            "client": ("10.0.0.1", 12345),
        }
        request = Request(scope)

        key = mw._get_client_key(request)
        assert key == "rate:ip:10.0.0.1"


# ---------------------------------------------------------------------------
# Auth routes: no more DB-outage fallback (503 instead of fake owner token)
# ---------------------------------------------------------------------------

class TestAuthFallbackRemoved:

    @pytest.mark.asyncio
    async def test_register_returns_503_when_db_unavailable(self):
        """register should return 503 when DB is down, not a fake owner token."""
        with patch("orchestra.api.routes.auth._get_session", new_callable=AsyncMock, return_value=None):
            from orchestra.main import app
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "new@example.com",
                        "password": "SecurePass1!",
                        "full_name": "Test",
                        "tenant_name": "Org",
                    },
                )
            assert resp.status_code == 503
            assert "unavailable" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_returns_503_when_db_unavailable(self):
        """login should return 503 when DB is down, not a fake owner token."""
        with patch("orchestra.api.routes.auth._get_session", new_callable=AsyncMock, return_value=None):
            from orchestra.main import app
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/api/v1/auth/login",
                    json={"email": "user@example.com", "password": "Pass1234!"},
                )
            assert resp.status_code == 503
            assert "unavailable" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# decode_access_token
# ---------------------------------------------------------------------------

class TestDecodeAccessToken:

    def test_valid_token_decodes(self):
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        token = create_access_token(uid, tid, role="admin")
        payload = decode_access_token(token)
        assert payload.sub == str(uid)
        assert payload.tenant_id == str(tid)
        assert payload.role == "admin"

    def test_invalid_token_raises_401(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("bad-token")
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# API key hashing utility
# ---------------------------------------------------------------------------

class TestAPIKeyHash:

    def test_hash_is_deterministic(self):
        key = "orc_live_abc123xyz"
        assert _hash_api_key(key) == _hash_api_key(key)

    def test_different_keys_different_hashes(self):
        assert _hash_api_key("key-a") != _hash_api_key("key-b")

    def test_hash_is_sha256_hex(self):
        h = _hash_api_key("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

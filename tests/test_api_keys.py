"""Tests for API Keys CRUD route (/api/v1/api-keys).

Covers:
- Auth / RBAC enforcement (missing token, viewer/member rejected)
- Validation (invalid role, role elevation, bad uuid, empty name, limit reached)
- Happy-path create / list / revoke using an in-memory fake DB session
- Tenant isolation (keys created by tenant A invisible to tenant B)
- Plaintext returned exactly once; subsequent reads expose metadata only
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from orchestra.api.middleware.auth import create_access_token


_UUID_RE = re.compile(
    r"[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(
    tenant_id: str | None = None,
    user_id: str | None = None,
    role: str = "owner",
) -> tuple[str, str, str]:
    uid = user_id or str(uuid.uuid4())
    tid = tenant_id or str(uuid.uuid4())
    token = create_access_token(uuid.UUID(uid), uuid.UUID(tid), role=role)
    return token, uid, tid


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fake DB session — mimics the subset of AsyncSession used by the route
# ---------------------------------------------------------------------------


class FakeAPIKeyRow:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        key_hash: str,
        role: str,
        is_active: bool = True,
        expires_at: datetime | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.name = name
        self.key_hash = key_hash
        self.role = role
        self.is_active = is_active
        self.expires_at = expires_at
        self.last_used_at: datetime | None = None
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at


class _FakeScalarsResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return list(self._rows)


class _FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeScalarsResult:
        return _FakeScalarsResult(self._rows)

    def scalar_one_or_none(self) -> Any | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    """In-memory stand-in for AsyncSession scoped to APIKey rows."""

    def __init__(self, store: list[FakeAPIKeyRow]) -> None:
        self._store = store
        self._last_query: Any = None

    async def execute(self, stmt: Any) -> _FakeResult:
        self._last_query = stmt
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        if compiled.lower().lstrip().startswith(("delete", "update")):
            return _FakeResult([])

        uuid_strings = _UUID_RE.findall(compiled)
        uuids = {uuid.UUID(s) for s in uuid_strings}

        rows = [
            r
            for r in self._store
            if r.tenant_id in uuids and (len(uuids) == 1 or r.id in uuids)
        ]
        return _FakeResult(rows)

    def add(self, row: Any) -> None:
        # Mimic the DB populating server-side defaults (id, timestamps)
        # when `flush()` runs on the real session.
        if getattr(row, "id", None) is None:
            row.id = uuid.uuid4()
        now = datetime.now(UTC)
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        if getattr(row, "updated_at", None) is None:
            row.updated_at = now
        self._store.append(row)

    async def flush(self) -> None:
        return None

    async def refresh(self, row: FakeAPIKeyRow) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_key_store() -> list[FakeAPIKeyRow]:
    return []


@pytest.fixture
async def client(api_key_store: list[FakeAPIKeyRow]):
    from orchestra.db.session import get_db
    from orchestra.main import app

    async def _fake_get_db():
        yield FakeSession(api_key_store)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


# ===================================================================
# A) Auth / RBAC enforcement
# ===================================================================


class TestAuth:
    @pytest.mark.asyncio
    async def test_list_requires_auth(self, client):
        resp = await client.get("/api/v1/api-keys")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        resp = await client.post("/api/v1/api-keys", json={"name": "x"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_revoke_requires_auth(self, client):
        resp = await client.delete(f"/api/v1/api-keys/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_viewer_cannot_list(self, client):
        token, _, _ = _make_token(role="viewer")
        resp = await client.get("/api/v1/api-keys", headers=_headers(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_member_cannot_create(self, client):
        token, _, _ = _make_token(role="member")
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "my key"},
            headers=_headers(token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_list(self, client):
        token, _, _ = _make_token(role="admin")
        resp = await client.get("/api/v1/api-keys", headers=_headers(token))
        assert resp.status_code == 200
        assert resp.json() == {"keys": []}


# ===================================================================
# B) Validation
# ===================================================================


class TestValidation:
    @pytest.mark.asyncio
    async def test_empty_name_rejected(self, client):
        token, _, _ = _make_token()
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": ""},
            headers=_headers(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_role_rejected(self, client):
        token, _, _ = _make_token()
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "bad", "role": "superuser"},
            headers=_headers(token),
        )
        assert resp.status_code == 400
        assert "invalid role" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_issue_owner_key(self, client):
        """Admins must not be able to escalate to owner via an API key."""
        token, _, _ = _make_token(role="admin")
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "sneaky", "role": "owner"},
            headers=_headers(token),
        )
        # Owner isn't in the allow-list for issued keys anyway → 400
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_expires_rejected(self, client):
        token, _, _ = _make_token()
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "x", "expires_in_days": 0},
            headers=_headers(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_revoke_bad_uuid(self, client):
        token, _, _ = _make_token()
        resp = await client.delete(
            "/api/v1/api-keys/not-a-uuid",
            headers=_headers(token),
        )
        assert resp.status_code == 400


# ===================================================================
# C) Happy-path CRUD
# ===================================================================


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_create_returns_plaintext_once(self, client, api_key_store):
        token, _, tid = _make_token(role="owner")
        resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "CI Bot", "role": "member", "expires_in_days": 30},
            headers=_headers(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "CI Bot"
        assert body["role"] == "member"
        assert body["is_active"] is True
        assert body["key"].startswith("oa_")
        assert len(body["key"]) > 20
        assert body["prefix"] == body["key"][:8]
        assert body["expires_at"] is not None
        assert len(api_key_store) == 1
        assert api_key_store[0].tenant_id == uuid.UUID(tid)
        # Plaintext must NOT be stored
        assert body["key"] != api_key_store[0].key_hash

    @pytest.mark.asyncio
    async def test_list_returns_metadata_only(self, client, api_key_store):
        token, uid, tid = _make_token(role="admin")
        tenant_uuid = uuid.UUID(tid)
        user_uuid = uuid.UUID(uid)
        api_key_store.append(
            FakeAPIKeyRow(
                tenant_id=tenant_uuid,
                user_id=user_uuid,
                name="Existing",
                key_hash="a" * 64,
                role="member",
            )
        )

        resp = await client.get("/api/v1/api-keys", headers=_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["keys"]) == 1
        entry = body["keys"][0]
        assert entry["name"] == "Existing"
        assert entry["role"] == "member"
        assert entry["is_active"] is True
        assert "key" not in entry
        assert "key_hash" not in entry

    @pytest.mark.asyncio
    async def test_revoke_marks_inactive(self, client, api_key_store):
        token, uid, tid = _make_token(role="owner")
        row = FakeAPIKeyRow(
            tenant_id=uuid.UUID(tid),
            user_id=uuid.UUID(uid),
            name="Doomed",
            key_hash="b" * 64,
            role="member",
        )
        api_key_store.append(row)

        resp = await client.delete(
            f"/api/v1/api-keys/{row.id}",
            headers=_headers(token),
        )
        assert resp.status_code == 204
        assert row.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_unknown_key(self, client):
        token, _, _ = _make_token(role="owner")
        resp = await client.delete(
            f"/api/v1/api-keys/{uuid.uuid4()}",
            headers=_headers(token),
        )
        assert resp.status_code == 404


# ===================================================================
# D) Tenant isolation
# ===================================================================


class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_list_excludes_other_tenant(self, client, api_key_store):
        other_tenant = uuid.uuid4()
        other_user = uuid.uuid4()
        api_key_store.append(
            FakeAPIKeyRow(
                tenant_id=other_tenant,
                user_id=other_user,
                name="Foreign",
                key_hash="c" * 64,
                role="member",
            )
        )

        token, _, _ = _make_token(role="admin")
        resp = await client.get("/api/v1/api-keys", headers=_headers(token))
        assert resp.status_code == 200
        assert resp.json() == {"keys": []}

    @pytest.mark.asyncio
    async def test_revoke_other_tenant_key_404s(self, client, api_key_store):
        other_tenant = uuid.uuid4()
        other_user = uuid.uuid4()
        foreign = FakeAPIKeyRow(
            tenant_id=other_tenant,
            user_id=other_user,
            name="NotYours",
            key_hash="d" * 64,
            role="member",
        )
        api_key_store.append(foreign)

        token, _, _ = _make_token(role="owner")
        resp = await client.delete(
            f"/api/v1/api-keys/{foreign.id}",
            headers=_headers(token),
        )
        assert resp.status_code == 404
        assert foreign.is_active is True


# ===================================================================
# E) Router registration
# ===================================================================


class TestRouterRegistration:
    def test_router_registered(self):
        from orchestra.main import app

        paths = {route.path for route in app.routes}
        assert "/api/v1/api-keys" in paths
        assert "/api/v1/api-keys/{key_id}" in paths

    def test_route_prefix(self):
        from orchestra.api.routes.api_keys import router

        assert router.prefix == "/api-keys"
        assert "api-keys" in router.tags

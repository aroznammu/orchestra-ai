"""Tests for authentication routes and JWT handling."""

import uuid

import pytest

from orchestra.api.middleware.auth import create_access_token


def test_create_access_token_returns_string():
    token = create_access_token(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="owner",
    )
    assert isinstance(token, str)
    assert len(token) > 50


def test_access_token_is_decodable():
    from jose import jwt
    from orchestra.config import get_settings

    settings = get_settings()
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    token = create_access_token(user_id, tenant_id, role="admin")
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_register_creates_token(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "tenant_name": "TestOrg",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_returns_token(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Pass1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad@example.com",
            "password": "short",
            "full_name": "Bad User",
            "tenant_name": "BadOrg",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_invalid_email(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "GoodPass123!",
            "full_name": "User",
            "tenant_name": "Org",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_returns_user_info(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert data["role"] == "owner"

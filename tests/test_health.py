"""Tests for health and readiness endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_healthy(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "orchestraai"


@pytest.mark.asyncio
async def test_ready_returns_status(client):
    resp = await client.get("/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data

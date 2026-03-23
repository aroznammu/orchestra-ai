"""Tests for programmatic DSP client."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from orchestra.connectors.dsp_client import (
    CreativeComplianceError,
    DSPClient,
    DSPNotConfiguredError,
)


@pytest.mark.asyncio
async def test_upload_creative_rejects_non_passed() -> None:
    client = DSPClient(
        base_url="https://example.com",
        api_key="k",
        partner_id="p",
    )
    client._access_token = "tok"

    with pytest.raises(CreativeComplianceError):
        await client.upload_creative("https://video.example/x.mp4", "Failed")


@pytest.mark.asyncio
async def test_authenticate_missing_credentials() -> None:
    client = DSPClient(base_url="https://x.com", api_key="", partner_id="")
    with pytest.raises(DSPNotConfiguredError):
        await client.authenticate()


@pytest.mark.asyncio
async def test_authenticate_success() -> None:
    client = DSPClient(
        base_url="https://dsp.test",
        api_key="secret",
        partner_id="partner-1",
    )
    mock_resp = AsyncMock()
    mock_resp.json = lambda: {"access_token": "tok-abc"}
    mock_resp.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as ac:
        inst = ac.return_value.__aenter__.return_value
        inst.post = AsyncMock(return_value=mock_resp)
        token = await client.authenticate()

    assert token == "tok-abc"
    assert client._access_token == "tok-abc"


@pytest.mark.asyncio
async def test_upload_creative_passed_happy_path() -> None:
    client = DSPClient(
        base_url="https://dsp.test",
        api_key="secret",
        partner_id="partner-1",
    )
    client._access_token = "tok"

    mock_resp = AsyncMock()
    mock_resp.json = lambda: {"CreativeId": "cr-99"}
    mock_resp.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as ac:
        inst = ac.return_value.__aenter__.return_value
        inst.post = AsyncMock(return_value=mock_resp)
        out = await client.upload_creative("https://cdn.example/v.mp4", "Passed")

    assert out["creative_id"] == "cr-99"


@pytest.mark.asyncio
async def test_create_ctv_campaign() -> None:
    client = DSPClient(
        base_url="https://dsp.test",
        api_key="secret",
        partner_id="partner-1",
    )
    client._access_token = "tok"

    mock_resp = AsyncMock()
    mock_resp.json = lambda: {"CampaignId": "cmp-1"}
    mock_resp.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as ac:
        inst = ac.return_value.__aenter__.return_value
        inst.post = AsyncMock(return_value=mock_resp)
        out = await client.create_ctv_campaign(
            "Summer CTV",
            5000.0,
            date(2026, 4, 1),
            date(2026, 4, 30),
        )

    assert out["campaign_id"] == "cmp-1"

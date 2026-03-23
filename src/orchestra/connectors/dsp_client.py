"""Programmatic DSP client (TTD-shaped REST API).

Used for Connected TV (CTV) campaign creation and creative upload.
Requires vision-gate compliance before creative upload.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
import structlog

logger = structlog.get_logger("connectors.dsp")


class DSPNotConfiguredError(Exception):
    """Raised when DSP_API_KEY or DSP_PARTNER_ID is missing."""


class CreativeComplianceError(Exception):
    """Raised when creative upload is blocked by compliance status."""


class DSPClient:
    """Demand-side platform REST client (The Trade Desk-style paths).

    Endpoints are illustrative; set ``dsp_base_url`` to your DSP sandbox or prod host.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        partner_id: str,
        *,
        timeout: float = 45.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._partner_id = partner_id
        self._timeout = timeout
        self._access_token: str | None = None

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._access_token:
            h["Authorization"] = f"Bearer {self._access_token}"
        return h

    async def authenticate(self) -> str:
        """Obtain an access token using API key and partner id.

        Does not perform network I/O if credentials are missing.
        """
        if not self._api_key or not self._partner_id:
            raise DSPNotConfiguredError(
                "DSP is not configured: set DSP_API_KEY and DSP_PARTNER_ID in the environment.",
            )
        payload = {
            "PartnerId": self._partner_id,
            "SecretKey": self._api_key,
        }
        url = f"{self._base}/v1/auth/token"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        token = data.get("access_token") or data.get("AccessToken") or data.get("token")
        if not token:
            raise RuntimeError(f"DSP auth response missing token: keys={list(data.keys())}")
        self._access_token = str(token)
        logger.info("dsp_authenticated", partner_id=self._partner_id[:4] + "...")
        return self._access_token

    async def create_ctv_campaign(
        self,
        name: str,
        budget: float,
        start_date: date | str,
        end_date: date | str,
    ) -> dict[str, Any]:
        """Create parent CTV / programmatic campaign."""
        if not self._access_token:
            await self.authenticate()
        start = start_date.isoformat() if isinstance(start_date, date) else str(start_date)
        end = end_date.isoformat() if isinstance(end_date, date) else str(end_date)
        body = {
            "PartnerId": self._partner_id,
            "CampaignName": name,
            "BudgetAmount": budget,
            "StartDate": start,
            "EndDate": end,
            "Channel": "CTV",
        }
        url = f"{self._base}/v1/campaigns"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        cid = data.get("CampaignId") or data.get("campaign_id") or data.get("id")
        logger.info("dsp_campaign_created", campaign_id=cid)
        return {"campaign_id": str(cid) if cid else "", "raw": data}

    async def create_ctv_ad_group(
        self,
        campaign_id: str,
        target_audience: dict[str, Any],
        bid_cpm: float,
    ) -> dict[str, Any]:
        """Configure programmatic auction targeting (CTV inventory only)."""
        if not self._access_token:
            await self.authenticate()
        body = {
            "CampaignId": campaign_id,
            "BidCPM": bid_cpm,
            "DeviceTypes": ["ConnectedTV"],
            "Targeting": target_audience or {},
        }
        url = f"{self._base}/v1/adgroups"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        aid = data.get("AdGroupId") or data.get("ad_group_id") or data.get("id")
        logger.info("dsp_ad_group_created", ad_group_id=aid)
        return {"ad_group_id": str(aid) if aid else "", "raw": data}

    async def upload_creative(self, video_url: str, compliance_status: str) -> dict[str, Any]:
        """Register a video creative URL with the DSP.

        **Vision gate:** Only ``compliance_status == "Passed"`` is allowed.
        """
        if compliance_status != "Passed":
            raise CreativeComplianceError(
                f"Creative upload blocked: compliance_status must be 'Passed', got {compliance_status!r}",
            )
        if not video_url:
            raise ValueError("video_url is required for creative upload")
        if not self._access_token:
            await self.authenticate()
        body = {
            "VideoUrl": video_url,
            "Format": "VAST",
            "ComplianceStatus": compliance_status,
        }
        url = f"{self._base}/v1/creatives"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        crid = data.get("CreativeId") or data.get("creative_id") or data.get("id")
        logger.info("dsp_creative_uploaded", creative_id=crid)
        return {"creative_id": str(crid) if crid else "", "raw": data}

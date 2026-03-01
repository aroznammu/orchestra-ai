"""Snapchat platform connector.

Uses Snapchat Marketing API with OAuth 2.0.
Supports ad creative publishing and campaign analytics.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from orchestra.config import get_settings
from orchestra.core.exceptions import PlatformAPIError, PlatformAuthError, PlatformRateLimitError
from orchestra.platforms.base import (
    AnalyticsData,
    AudienceData,
    EngagementMetrics,
    PlatformBase,
    PlatformLimits,
    PostContent,
    PostResult,
    RateLimitStatus,
    ScheduleResult,
    TokenPair,
)

logger = structlog.get_logger("platform.snapchat")

SNAP_AUTH_URL = "https://accounts.snapchat.com/login/oauth2/authorize"
SNAP_TOKEN_URL = "https://accounts.snapchat.com/login/oauth2/access_token"
SNAP_API_BASE = "https://adsapi.snapchat.com/v1"


class SnapchatPlatform(PlatformBase):
    PLATFORM_NAME = "snapchat"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=250,
        max_media_count=1,
        max_hashtags=None,
        supported_media_types=["image/jpeg", "image/png", "video/mp4"],
        rate_limit_per_minute=60,
        rate_limit_per_day=None,
    )

    SCOPES = [
        "snapchat-marketing-api",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=SNAP_API_BASE,
            headers=headers,
            timeout=30.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.settings.snapchat_app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        return f"{SNAP_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                SNAP_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.settings.snapchat_app_id,
                    "client_secret": self.settings.snapchat_app_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error("snapchat_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Snapchat OAuth failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 1800)

        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            scopes=data.get("scope", "").split(),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                SNAP_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.settings.snapchat_app_id,
                    "client_secret": self.settings.snapchat_app_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Snapchat token refresh failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 1800)),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://accounts.snapchat.com/login/oauth2/revoke",
                data={
                    "token": access_token,
                    "token_type_hint": "access_token",
                    "client_id": self.settings.snapchat_app_id,
                    "client_secret": self.settings.snapchat_app_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        return response.status_code == 200

    async def _get_ad_account_id(self, access_token: str) -> str:
        async with self._get_client(access_token) as client:
            response = await client.get("/me/organizations")

        if response.status_code != 200:
            raise PlatformAPIError("Failed to get Snapchat organizations")

        orgs = response.json().get("organizations", [])
        if not orgs:
            raise PlatformAPIError("No Snapchat organizations found")

        org_id = orgs[0].get("organization", {}).get("id", "")

        async with self._get_client(access_token) as client:
            response = await client.get(f"/organizations/{org_id}/adaccounts")

        if response.status_code != 200:
            raise PlatformAPIError("Failed to get Snapchat ad accounts")

        accounts = response.json().get("adaccounts", [])
        if not accounts:
            raise PlatformAPIError("No Snapchat ad accounts found")

        return accounts[0].get("adaccount", {}).get("id", "")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        ad_account_id = await self._get_ad_account_id(access_token)

        creative_payload = {
            "creatives": [{
                "creative": {
                    "ad_account_id": ad_account_id,
                    "name": content.text[:100],
                    "type": "SNAP_AD",
                    "headline": content.text[:34],
                    "brand_name": content.platform_specific.get("brand_name", "OrchestraAI"),
                    "shareable": True,
                    "call_to_action": content.platform_specific.get("cta", "VIEW_MORE"),
                    "top_snap_media_id": content.platform_specific.get("media_id", ""),
                },
            }],
        }

        if content.link:
            creative_payload["creatives"][0]["creative"]["web_view_url"] = content.link

        async with self._get_client(access_token) as client:
            response = await client.post(
                f"/adaccounts/{ad_account_id}/creatives",
                json=creative_payload,
            )

        self._handle_rate_limit(response)

        if response.status_code not in (200, 201):
            logger.error("snapchat_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to create Snapchat creative: {response.status_code}")

        data = response.json()
        creatives = data.get("creatives", [])
        creative_id = creatives[0].get("creative", {}).get("id", "unknown") if creatives else "unknown"

        return PostResult(
            platform_post_id=creative_id,
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        ad_account_id = await self._get_ad_account_id(access_token)

        end = datetime.now(UTC)
        start = end - timedelta(days=7)

        async with self._get_client(access_token) as client:
            response = await client.get(
                f"/adaccounts/{ad_account_id}/stats",
                params={
                    "granularity": "TOTAL",
                    "fields": "impressions,swipes,spend,video_views",
                    "start_time": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "end_time": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                },
            )

        self._handle_rate_limit(response)

        impressions = clicks = video_views = 0
        if response.status_code == 200:
            timeseries = response.json().get("timeseries_stats", [])
            if timeseries:
                stats = timeseries[0].get("timeseries_stat", {}).get("timeseries", [])
                if stats:
                    row = stats[0].get("stats", {})
                    impressions = row.get("impressions", 0)
                    clicks = row.get("swipes", 0)
                    video_views = row.get("video_views", 0)

        return AnalyticsData(
            post_id=post_id,
            platform="snapchat",
            metrics=EngagementMetrics(
                impressions=impressions,
                clicks=clicks,
                video_views=video_views,
            ),
            collected_at=datetime.now(UTC),
            raw=response.json() if response.status_code == 200 else {},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get("/me")

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Snapchat user info: {response.status_code}")

        data = response.json().get("me", {})
        return AudienceData(
            total_followers=0,
            demographics={
                "display_name": data.get("display_name", ""),
                "organization_id": data.get("organization_id", ""),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "Snapchat ad scheduling is managed via campaign flight dates. Use OrchestraAI's scheduler."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/creatives/{post_id}")

        self._handle_rate_limit(response)
        return response.status_code in (200, 204)

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        return RateLimitStatus(
            remaining=self.PLATFORM_LIMITS.rate_limit_per_minute,
            limit=self.PLATFORM_LIMITS.rate_limit_per_minute,
            reset_at=datetime.now(UTC) + timedelta(minutes=1),
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 60))
            logger.warning("snapchat_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("Snapchat rate limit exceeded", retry_after=retry_after)

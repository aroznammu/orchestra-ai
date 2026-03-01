"""Pinterest platform connector.

Uses Pinterest API v5 with OAuth 2.0 authorization code flow.
Supports pin creation, board management, and analytics.
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

logger = structlog.get_logger("platform.pinterest")

PINTEREST_AUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
PINTEREST_API_BASE = "https://api.pinterest.com/v5"


class PinterestPlatform(PlatformBase):
    PLATFORM_NAME = "pinterest"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=500,
        max_media_count=1,
        max_hashtags=20,
        supported_media_types=["image/jpeg", "image/png", "image/gif", "video/mp4"],
        rate_limit_per_minute=50,
        rate_limit_per_day=1000,
    )

    SCOPES = [
        "boards:read",
        "boards:write",
        "pins:read",
        "pins:write",
        "user_accounts:read",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=PINTEREST_API_BASE,
            headers=headers,
            timeout=30.0,
        )

    def _basic_auth(self) -> str:
        import base64
        app_id = self.settings.pinterest_app_id
        app_secret = self.settings.pinterest_app_secret.get_secret_value()
        return base64.b64encode(f"{app_id}:{app_secret}".encode()).decode()

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.settings.pinterest_app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "state": state,
        }
        return f"{PINTEREST_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PINTEREST_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                },
                headers={
                    "Authorization": f"Basic {self._basic_auth()}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

        if response.status_code != 200:
            logger.error("pinterest_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Pinterest OAuth failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 2592000)

        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            scopes=data.get("scope", "").split(","),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PINTEREST_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Authorization": f"Basic {self._basic_auth()}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Pinterest token refresh failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 2592000)
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PINTEREST_API_BASE}/oauth/revoke",
                data={"token": access_token},
                headers={
                    "Authorization": f"Basic {self._basic_auth()}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        return response.status_code == 200

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        if not content.media_urls:
            raise PlatformAPIError("Pinterest requires at least one image or video URL")

        description = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags[:20])
            description = f"{description} {hashtag_str}"

        pin_data: dict = {
            "title": content.platform_specific.get("title", description[:100]),
            "description": description,
            "board_id": content.platform_specific.get("board_id", ""),
            "media_source": {
                "source_type": "image_url",
                "url": content.media_urls[0],
            },
        }

        if content.link:
            pin_data["link"] = content.link

        if content.platform_specific.get("alt_text"):
            pin_data["alt_text"] = content.platform_specific["alt_text"]

        async with self._get_client(access_token) as client:
            response = await client.post("/pins", json=pin_data)

        self._handle_rate_limit(response)

        if response.status_code not in (200, 201):
            logger.error("pinterest_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to create Pinterest pin: {response.status_code}")

        data = response.json()
        pin_id = data.get("id", "unknown")

        return PostResult(
            platform_post_id=pin_id,
            url=f"https://www.pinterest.com/pin/{pin_id}/",
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                f"/pins/{post_id}/analytics",
                params={
                    "start_date": (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "end_date": datetime.now(UTC).strftime("%Y-%m-%d"),
                    "metric_types": "IMPRESSION,PIN_CLICK,OUTBOUND_CLICK,SAVE",
                },
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Pinterest analytics: {response.status_code}")

        data = response.json()
        all_data = data.get("all", {})
        totals: dict = {}
        for metric_name, daily_values in all_data.items():
            if isinstance(daily_values, list):
                totals[metric_name] = sum(v.get("value", 0) if isinstance(v, dict) else 0 for v in daily_values)

        return AnalyticsData(
            post_id=post_id,
            platform="pinterest",
            metrics=EngagementMetrics(
                impressions=totals.get("IMPRESSION", 0),
                clicks=totals.get("PIN_CLICK", 0) + totals.get("OUTBOUND_CLICK", 0),
                saves=totals.get("SAVE", 0),
            ),
            collected_at=datetime.now(UTC),
            raw=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get("/user_account")

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Pinterest audience: {response.status_code}")

        data = response.json()
        return AudienceData(
            total_followers=data.get("follower_count", 0),
            demographics={
                "following": data.get("following_count", 0),
                "pin_count": data.get("pin_count", 0),
                "monthly_views": data.get("monthly_views", 0),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "Pinterest doesn't support native scheduling via API. Use OrchestraAI's scheduler instead."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/pins/{post_id}")

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
            logger.warning("pinterest_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("Pinterest rate limit exceeded", retry_after=retry_after)

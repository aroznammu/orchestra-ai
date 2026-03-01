"""Facebook platform connector.

Uses Meta Graph API v19.0 with OAuth 2.0.
Supports page post creation, analytics, and audience insights.
Requires Meta business verification for production access.
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

logger = structlog.get_logger("platform.facebook")

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
FB_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FB_TOKEN_URL = f"{GRAPH_API_BASE}/oauth/access_token"


class FacebookPlatform(PlatformBase):
    PLATFORM_NAME = "facebook"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=63206,
        max_media_count=10,
        max_hashtags=30,
        supported_media_types=["image/jpeg", "image/png", "image/gif", "video/mp4"],
        rate_limit_per_minute=60,
        rate_limit_per_day=None,
    )

    SCOPES = [
        "pages_manage_posts",
        "pages_read_engagement",
        "pages_read_user_content",
        "pages_show_list",
        "read_insights",
        "public_profile",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        params = {}
        if access_token:
            params["access_token"] = access_token
        return httpx.AsyncClient(
            base_url=GRAPH_API_BASE,
            params=params,
            timeout=30.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.settings.meta_app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "state": state,
        }
        return f"{FB_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                FB_TOKEN_URL,
                params={
                    "client_id": self.settings.meta_app_id,
                    "client_secret": self.settings.meta_app_secret.get_secret_value(),
                    "redirect_uri": redirect_uri,
                    "code": oauth_code,
                },
            )

        if response.status_code != 200:
            logger.error("facebook_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Facebook OAuth failed: {response.status_code}")

        data = response.json()
        if "error" in data:
            raise PlatformAuthError(f"Facebook OAuth error: {data['error'].get('message')}")

        expires_in = data.get("expires_in", 5184000)
        return TokenPair(
            access_token=data["access_token"],
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            token_type=data.get("token_type", "bearer"),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Exchange short-lived token for long-lived token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                FB_TOKEN_URL,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.settings.meta_app_id,
                    "client_secret": self.settings.meta_app_secret.get_secret_value(),
                    "fb_exchange_token": refresh_token,
                },
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Facebook token exchange failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 5184000)
        return TokenPair(
            access_token=data["access_token"],
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{GRAPH_API_BASE}/me/permissions",
                params={"access_token": access_token},
            )
        return response.status_code == 200

    async def _get_page_token(self, access_token: str) -> tuple[str, str]:
        """Get the first managed page's ID and access token."""
        async with self._get_client(access_token) as client:
            response = await client.get("/me/accounts")

        if response.status_code != 200:
            raise PlatformAPIError("Failed to retrieve Facebook pages")

        pages = response.json().get("data", [])
        if not pages:
            raise PlatformAPIError("No Facebook pages found. Create a page first.")

        page = pages[0]
        return page["id"], page["access_token"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        page_id, page_token = await self._get_page_token(access_token)

        message = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags)
            message = f"{message}\n\n{hashtag_str}"

        post_data: dict = {"message": message}
        if content.link:
            post_data["link"] = content.link

        if content.media_urls:
            if any(url.endswith((".mp4", ".mov")) for url in content.media_urls):
                post_data["file_url"] = content.media_urls[0]
                endpoint = f"/{page_id}/videos"
                post_data["description"] = message
            else:
                post_data["url"] = content.media_urls[0]
                endpoint = f"/{page_id}/photos"
            post_data.pop("message", None)
            post_data["caption"] = message
        else:
            endpoint = f"/{page_id}/feed"

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=60.0) as client:
            response = await client.post(
                endpoint,
                params={"access_token": page_token},
                data=post_data,
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            logger.error("facebook_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to publish to Facebook: {response.status_code}")

        data = response.json()
        post_id = data.get("id") or data.get("post_id", "unknown")

        return PostResult(
            platform_post_id=post_id,
            url=f"https://www.facebook.com/{post_id}",
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        fields = "likes.summary(true),comments.summary(true),shares,insights.metric(post_impressions,post_engaged_users,post_clicks)"
        async with self._get_client(access_token) as client:
            response = await client.get(f"/{post_id}", params={"fields": fields})

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Facebook analytics: {response.status_code}")

        data = response.json()
        likes = data.get("likes", {}).get("summary", {}).get("total_count", 0)
        comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = data.get("shares", {}).get("count", 0)

        impressions = 0
        clicks = 0
        reach = 0
        for insight in data.get("insights", {}).get("data", []):
            name = insight.get("name", "")
            values = insight.get("values", [{}])
            value = values[0].get("value", 0) if values else 0
            if name == "post_impressions":
                impressions = value
            elif name == "post_clicks":
                clicks = value
            elif name == "post_engaged_users":
                reach = value

        return AnalyticsData(
            post_id=post_id,
            platform="facebook",
            metrics=EngagementMetrics(
                impressions=impressions,
                reach=reach,
                likes=likes,
                comments=comments,
                shares=shares,
                clicks=clicks,
            ),
            collected_at=datetime.now(UTC),
            raw=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        page_id, page_token = await self._get_page_token(access_token)

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=30.0) as client:
            response = await client.get(
                f"/{page_id}",
                params={
                    "access_token": page_token,
                    "fields": "followers_count,fan_count,name,category",
                },
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Facebook audience: {response.status_code}")

        data = response.json()
        return AudienceData(
            total_followers=data.get("followers_count", data.get("fan_count", 0)),
            demographics={
                "page_name": data.get("name", ""),
                "category": data.get("category", ""),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        if not content.scheduled_at:
            raise PlatformAPIError("scheduled_at is required for scheduling")

        page_id, page_token = await self._get_page_token(access_token)
        publish_ts = int(content.scheduled_at.timestamp())

        message = content.text
        if content.hashtags:
            message += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in content.hashtags)

        post_data = {
            "message": message,
            "published": "false",
            "scheduled_publish_time": publish_ts,
        }
        if content.link:
            post_data["link"] = content.link

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=30.0) as client:
            response = await client.post(
                f"/{page_id}/feed",
                params={"access_token": page_token},
                data=post_data,
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to schedule Facebook post: {response.status_code}")

        data = response.json()
        return ScheduleResult(
            platform_schedule_id=data.get("id", "unknown"),
            scheduled_at=content.scheduled_at,
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/{post_id}")

        self._handle_rate_limit(response)
        return response.status_code == 200

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        async with self._get_client(access_token) as client:
            response = await client.get("/me")

        usage = response.headers.get("x-app-usage", "{}")
        import json
        try:
            usage_data = json.loads(usage)
        except (json.JSONDecodeError, TypeError):
            usage_data = {}

        call_pct = usage_data.get("call_count", 0)
        remaining = max(0, 100 - int(call_pct))

        return RateLimitStatus(
            remaining=remaining,
            limit=100,
            reset_at=datetime.now(UTC) + timedelta(hours=1),
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 600))
            logger.warning("facebook_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("Facebook rate limit exceeded", retry_after=retry_after)

        usage = response.headers.get("x-app-usage", "")
        if usage:
            import json
            try:
                data = json.loads(usage)
                if data.get("call_count", 0) > 80:
                    logger.warning("facebook_rate_approaching", usage=data)
            except (json.JSONDecodeError, TypeError):
                pass

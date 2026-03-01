"""TikTok platform connector.

Uses TikTok API v2 with OAuth 2.0 authorization code flow.
Content Posting API for publishing, Video Insights for analytics.
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

logger = structlog.get_logger("platform.tiktok")

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokPlatform(PlatformBase):
    PLATFORM_NAME = "tiktok"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=2200,
        max_media_count=1,
        max_hashtags=None,
        supported_media_types=["video/mp4"],
        rate_limit_per_minute=60,
        rate_limit_per_day=None,
    )

    SCOPES = [
        "user.info.basic",
        "user.info.stats",
        "video.publish",
        "video.list",
        "video.upload",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=TIKTOK_API_BASE,
            headers=headers,
            timeout=60.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_key": self.settings.tiktok_app_id,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{TIKTOK_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TIKTOK_TOKEN_URL,
                json={
                    "client_key": self.settings.tiktok_app_id,
                    "client_secret": self.settings.tiktok_app_secret.get_secret_value(),
                    "code": oauth_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )

        if response.status_code != 200:
            logger.error("tiktok_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"TikTok OAuth failed: {response.status_code}")

        data = response.json()
        if "error" in data and data.get("error") != "ok":
            raise PlatformAuthError(f"TikTok OAuth error: {data.get('error_description', data.get('error'))}")

        expires_in = data.get("expires_in", 86400)
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
                TIKTOK_TOKEN_URL,
                json={
                    "client_key": self.settings.tiktok_app_id,
                    "client_secret": self.settings.tiktok_app_secret.get_secret_value(),
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"TikTok token refresh failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 86400)
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TIKTOK_API_BASE}/oauth/revoke/",
                json={
                    "client_key": self.settings.tiktok_app_id,
                    "client_secret": self.settings.tiktok_app_secret.get_secret_value(),
                    "token": access_token,
                },
            )
        return response.status_code == 200

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        if not content.media_urls:
            raise PlatformAPIError("TikTok requires a video URL to publish")

        caption = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags)
            caption = f"{caption} {hashtag_str}"

        async with self._get_client(access_token) as client:
            init_response = await client.post(
                "/post/publish/video/init/",
                json={
                    "post_info": {
                        "title": caption[:150],
                        "description": caption,
                        "privacy_level": content.platform_specific.get("privacy_level", "SELF_ONLY"),
                        "disable_comment": content.platform_specific.get("disable_comment", False),
                        "disable_duet": content.platform_specific.get("disable_duet", False),
                        "disable_stitch": content.platform_specific.get("disable_stitch", False),
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": content.media_urls[0],
                    },
                },
            )

        self._handle_rate_limit(init_response)

        if init_response.status_code != 200:
            logger.error("tiktok_publish_failed", status=init_response.status_code, body=init_response.text)
            raise PlatformAPIError(f"Failed to publish to TikTok: {init_response.status_code}")

        data = init_response.json().get("data", {})
        publish_id = data.get("publish_id", "unknown")

        return PostResult(
            platform_post_id=publish_id,
            url=None,
            published_at=datetime.now(UTC),
            raw_response=init_response.json(),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        async with self._get_client(access_token) as client:
            response = await client.post(
                "/video/query/",
                json={
                    "filters": {"video_ids": [post_id]},
                    "fields": ["id", "title", "like_count", "comment_count", "share_count", "view_count"],
                },
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get TikTok analytics: {response.status_code}")

        videos = response.json().get("data", {}).get("videos", [])
        video = videos[0] if videos else {}

        return AnalyticsData(
            post_id=post_id,
            platform="tiktok",
            metrics=EngagementMetrics(
                likes=video.get("like_count", 0),
                comments=video.get("comment_count", 0),
                shares=video.get("share_count", 0),
                video_views=video.get("view_count", 0),
            ),
            collected_at=datetime.now(UTC),
            raw=video,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                "/user/info/",
                params={"fields": "follower_count,following_count,likes_count,video_count,display_name"},
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get TikTok audience: {response.status_code}")

        data = response.json().get("data", {}).get("user", {})
        return AudienceData(
            total_followers=data.get("follower_count", 0),
            demographics={
                "following": data.get("following_count", 0),
                "total_likes": data.get("likes_count", 0),
                "video_count": data.get("video_count", 0),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "TikTok doesn't support native scheduling via API. Use OrchestraAI's scheduler instead."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        logger.warning("tiktok_delete_unsupported", post_id=post_id)
        raise PlatformAPIError("TikTok Content Posting API does not support video deletion via API")

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        return RateLimitStatus(
            remaining=self.PLATFORM_LIMITS.rate_limit_per_minute,
            limit=self.PLATFORM_LIMITS.rate_limit_per_minute,
            reset_at=datetime.now(UTC) + timedelta(minutes=1),
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 60))
            logger.warning("tiktok_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("TikTok rate limit exceeded", retry_after=retry_after)

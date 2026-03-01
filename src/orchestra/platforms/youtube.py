"""YouTube / Google platform connector (full implementation).

Uses YouTube Data API v3 with Google OAuth 2.0 flow.
Free tier available; instant access.
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

logger = structlog.get_logger("platform.youtube")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


class YouTubePlatform(PlatformBase):
    PLATFORM_NAME = "youtube"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=5000,
        max_media_count=1,
        max_hashtags=60,
        supported_media_types=["video/mp4", "video/quicktime", "video/x-msvideo"],
        rate_limit_per_minute=60,
        rate_limit_per_day=10000,
    )

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=YOUTUBE_API_BASE,
            headers=headers,
            timeout=60.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret.get_secret_value(),
                },
            )

        if response.status_code != 200:
            logger.error("youtube_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Google OAuth failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 3600)),
            scopes=data.get("scope", "").split(),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret.get_secret_value(),
                },
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Google token refresh failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=refresh_token,
            expires_at=datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 3600)),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": access_token},
            )
        return response.status_code == 200

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        """Upload a video to YouTube (requires video in media_urls)."""
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        if not content.media_urls:
            raise PlatformAPIError("YouTube publish requires a video URL in media_urls")

        tags = [h.lstrip("#") for h in content.hashtags] if content.hashtags else []

        metadata = {
            "snippet": {
                "title": content.platform_specific.get("title", content.text[:100]),
                "description": content.text,
                "tags": tags,
                "categoryId": content.platform_specific.get("category_id", "22"),
            },
            "status": {
                "privacyStatus": content.platform_specific.get("privacy", "public"),
                "selfDeclaredMadeForKids": False,
            },
        }

        if content.scheduled_at:
            metadata["status"]["privacyStatus"] = "private"
            metadata["status"]["publishAt"] = content.scheduled_at.isoformat()

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                YOUTUBE_UPLOAD_URL,
                params={"part": "snippet,status", "uploadType": "resumable"},
                json=metadata,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )

        self._handle_errors(response)

        video_id = response.json().get("id", "pending")
        return PostResult(
            platform_post_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}" if video_id != "pending" else None,
            published_at=datetime.now(UTC),
            raw_response=response.json(),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                "/videos",
                params={
                    "part": "statistics,snippet",
                    "id": post_id,
                },
            )

        self._handle_errors(response)

        items = response.json().get("items", [])
        if not items:
            raise PlatformAPIError(f"Video {post_id} not found")

        stats = items[0].get("statistics", {})

        return AnalyticsData(
            post_id=post_id,
            platform="youtube",
            metrics=EngagementMetrics(
                impressions=0,
                video_views=int(stats.get("viewCount", 0)),
                likes=int(stats.get("likeCount", 0)),
                comments=int(stats.get("commentCount", 0)),
                shares=0,
                saves=int(stats.get("favoriteCount", 0)),
            ),
            collected_at=datetime.now(UTC),
            raw=items[0],
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                "/channels",
                params={"part": "statistics,snippet", "mine": "true"},
            )

        self._handle_errors(response)

        items = response.json().get("items", [])
        if not items:
            raise PlatformAPIError("No YouTube channel found for this account")

        stats = items[0].get("statistics", {})

        return AudienceData(
            total_followers=int(stats.get("subscriberCount", 0)),
            demographics={
                "total_views": int(stats.get("viewCount", 0)),
                "total_videos": int(stats.get("videoCount", 0)),
            },
            raw=items[0],
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        """YouTube supports native scheduling via publishAt in upload metadata."""
        if not content.scheduled_at:
            raise PlatformAPIError("scheduled_at is required for YouTube scheduling")

        content.platform_specific["privacy"] = "private"
        result = await self.publish(content, access_token)

        return ScheduleResult(
            platform_schedule_id=result.platform_post_id,
            scheduled_at=content.scheduled_at,
            raw_response=result.raw_response,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete("/videos", params={"id": post_id})

        return response.status_code in (200, 204)

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        return RateLimitStatus(
            remaining=self.PLATFORM_LIMITS.rate_limit_per_day,
            limit=self.PLATFORM_LIMITS.rate_limit_per_day,
            reset_at=None,
        )

    def _handle_errors(self, response: httpx.Response) -> None:
        if response.status_code == 403:
            body = response.json()
            errors = body.get("error", {}).get("errors", [])
            if any(e.get("reason") == "rateLimitExceeded" for e in errors):
                raise PlatformRateLimitError("YouTube API rate limit exceeded", retry_after=60)
            raise PlatformAPIError(f"YouTube API forbidden: {response.text}")

        if response.status_code == 401:
            raise PlatformAuthError("YouTube token expired or invalid")

        if response.status_code >= 400:
            raise PlatformAPIError(f"YouTube API error {response.status_code}: {response.text}")

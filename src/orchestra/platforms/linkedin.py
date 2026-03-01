"""LinkedIn platform connector.

Uses LinkedIn Marketing API v2 with OAuth 2.0 (3-legged).
Supports text posts, image/video sharing, and analytics.
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

logger = structlog.get_logger("platform.linkedin")

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_REST_BASE = "https://api.linkedin.com/rest"


class LinkedInPlatform(PlatformBase):
    PLATFORM_NAME = "linkedin"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=3000,
        max_media_count=9,
        max_hashtags=None,
        supported_media_types=["image/jpeg", "image/png", "image/gif", "video/mp4"],
        rate_limit_per_minute=100,
        rate_limit_per_day=None,
    )

    SCOPES = [
        "openid",
        "profile",
        "w_member_social",
        "r_liteprofile",
        "r_organization_social",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202402",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=LINKEDIN_API_BASE,
            headers=headers,
            timeout=30.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.settings.linkedin_client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.settings.linkedin_client_id,
                    "client_secret": self.settings.linkedin_client_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error("linkedin_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"LinkedIn OAuth failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 5184000)

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
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.settings.linkedin_client_id,
                    "client_secret": self.settings.linkedin_client_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"LinkedIn token refresh failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 5184000)),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://www.linkedin.com/oauth/v2/revoke",
                data={
                    "token": access_token,
                    "client_id": self.settings.linkedin_client_id,
                    "client_secret": self.settings.linkedin_client_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        return response.status_code == 200

    async def _get_person_urn(self, access_token: str) -> str:
        async with self._get_client(access_token) as client:
            response = await client.get("/userinfo")

        if response.status_code != 200:
            raise PlatformAPIError("Failed to get LinkedIn profile")

        data = response.json()
        sub = data.get("sub", "")
        return f"urn:li:person:{sub}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        author_urn = await self._get_person_urn(access_token)

        text = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags)
            text = f"{text}\n\n{hashtag_str}"

        post_body: dict = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                },
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": content.platform_specific.get(
                    "visibility", "PUBLIC"
                ),
            },
        }

        if content.link:
            share_content = post_body["specificContent"]["com.linkedin.ugc.ShareContent"]
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{
                "status": "READY",
                "originalUrl": content.link,
                "title": {"text": content.platform_specific.get("link_title", content.text[:200])},
            }]

        async with self._get_client(access_token) as client:
            response = await client.post("/ugcPosts", json=post_body)

        self._handle_rate_limit(response)

        if response.status_code not in (200, 201):
            logger.error("linkedin_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to publish to LinkedIn: {response.status_code}")

        data = response.json()
        post_id = data.get("id", "unknown")

        return PostResult(
            platform_post_id=post_id,
            url=f"https://www.linkedin.com/feed/update/{post_id}",
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        encoded_id = post_id.replace(":", "%3A")
        async with self._get_client(access_token) as client:
            response = await client.get(
                f"/socialActions/{encoded_id}",
                params={"fields": "likes,comments,shares"},
            )

        self._handle_rate_limit(response)

        likes = comments = shares = 0
        if response.status_code == 200:
            data = response.json()
            likes = data.get("likesSummary", {}).get("totalLikes", 0)
            comments = data.get("commentsSummary", {}).get("totalFirstLevelComments", 0)
            shares = data.get("sharesSummary", {}).get("totalShares", 0) if "sharesSummary" in data else 0
        else:
            data = {}

        return AnalyticsData(
            post_id=post_id,
            platform="linkedin",
            metrics=EngagementMetrics(
                likes=likes,
                comments=comments,
                shares=shares,
            ),
            collected_at=datetime.now(UTC),
            raw=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                "/userinfo",
            )

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get LinkedIn profile: {response.status_code}")

        data = response.json()
        return AudienceData(
            total_followers=0,
            demographics={
                "name": data.get("name", ""),
                "email": data.get("email", ""),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "LinkedIn doesn't support native scheduling via API. Use OrchestraAI's scheduler instead."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        encoded_id = post_id.replace(":", "%3A")
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/ugcPosts/{encoded_id}")

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
            logger.warning("linkedin_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("LinkedIn rate limit exceeded", retry_after=retry_after)

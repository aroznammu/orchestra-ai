"""X/Twitter platform connector (full implementation).

Uses Twitter API v2 with OAuth 2.0 PKCE flow.
Paid API tier ($100/mo Basic) required for posting.
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

logger = structlog.get_logger("platform.twitter")

TWITTER_API_BASE = "https://api.twitter.com/2"
TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"


class TwitterPlatform(PlatformBase):
    PLATFORM_NAME = "twitter"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=280,
        max_media_count=4,
        max_hashtags=None,
        supported_media_types=["image/jpeg", "image/png", "image/gif", "video/mp4"],
        rate_limit_per_minute=30,
        rate_limit_per_day=500,
    )

    SCOPES = [
        "tweet.read", "tweet.write", "users.read",
        "offline.access", "like.read", "like.write",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=TWITTER_API_BASE,
            headers=headers,
            timeout=30.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.settings.twitter_api_key.get_secret_value(),
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "code_challenge": "challenge",
            "code_challenge_method": "plain",
        }
        return f"{TWITTER_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TWITTER_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.settings.twitter_api_key.get_secret_value(),
                    "code_verifier": "challenge",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error("twitter_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Twitter OAuth failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 7200)

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
                TWITTER_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.settings.twitter_api_key.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Twitter token refresh failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 7200)

        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TWITTER_API_BASE}/oauth2/revoke",
                data={
                    "token": access_token,
                    "client_id": self.settings.twitter_api_key.get_secret_value(),
                },
            )
        return response.status_code == 200

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        tweet_text = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags)
            if len(tweet_text) + len(hashtag_str) + 1 <= 280:
                tweet_text = f"{tweet_text} {hashtag_str}"

        payload: dict = {"text": tweet_text}

        if content.link:
            if len(tweet_text) + len(content.link) + 1 <= 280:
                payload["text"] = f"{tweet_text} {content.link}"

        async with self._get_client(access_token) as client:
            response = await client.post("/tweets", json=payload)

        self._handle_rate_limit(response)

        if response.status_code not in (200, 201):
            logger.error("twitter_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to publish tweet: {response.status_code}")

        data = response.json()["data"]
        return PostResult(
            platform_post_id=data["id"],
            url=f"https://x.com/i/web/status/{data['id']}",
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        fields = "public_metrics,non_public_metrics,organic_metrics"
        async with self._get_client(access_token) as client:
            response = await client.get(f"/tweets/{post_id}", params={"tweet.fields": fields})

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get tweet analytics: {response.status_code}")

        data = response.json()["data"]
        public = data.get("public_metrics", {})

        return AnalyticsData(
            post_id=post_id,
            platform="twitter",
            metrics=EngagementMetrics(
                impressions=public.get("impression_count", 0),
                likes=public.get("like_count", 0),
                comments=public.get("reply_count", 0),
                shares=public.get("retweet_count", 0) + public.get("quote_count", 0),
                clicks=data.get("non_public_metrics", {}).get("url_link_clicks", 0),
            ),
            collected_at=datetime.now(UTC),
            raw=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        async with self._get_client(access_token) as client:
            response = await client.get("/users/me", params={"user.fields": "public_metrics,description"})

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Twitter audience: {response.status_code}")

        data = response.json()["data"]
        metrics = data.get("public_metrics", {})

        return AudienceData(
            total_followers=metrics.get("followers_count", 0),
            demographics={"following": metrics.get("following_count", 0)},
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        """Twitter API v2 doesn't support native scheduling; handled by our scheduler."""
        from orchestra.core.exceptions import PlatformAPIError
        raise PlatformAPIError(
            "Twitter doesn't support native scheduling. Use OrchestraAI's scheduler instead."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/tweets/{post_id}")

        self._handle_rate_limit(response)
        return response.status_code == 200

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        async with self._get_client(access_token) as client:
            response = await client.get("/users/me")

        remaining = int(response.headers.get("x-rate-limit-remaining", 0))
        limit = int(response.headers.get("x-rate-limit-limit", 0))
        reset_ts = int(response.headers.get("x-rate-limit-reset", 0))

        return RateLimitStatus(
            remaining=remaining,
            limit=limit,
            reset_at=datetime.fromtimestamp(reset_ts, tz=UTC) if reset_ts else None,
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 60))
            logger.warning("twitter_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError(
                "Twitter rate limit exceeded",
                retry_after=retry_after,
            )

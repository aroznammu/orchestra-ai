"""Instagram platform connector.

Uses Meta Graph API (Instagram Graph API) with OAuth 2.0.
Content publishing uses the container-based media upload flow.
Requires Meta business verification and connected Instagram Business/Creator account.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
import asyncio

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from orchestra.config import get_settings
from orchestra.core.exceptions import PlatformAPIError, PlatformAuthError, PlatformRateLimitError
from orchestra.platforms.base import (
    AnalyticsData,
    AudienceData,
    AudienceSegment,
    EngagementMetrics,
    PlatformBase,
    PlatformLimits,
    PostContent,
    PostResult,
    RateLimitStatus,
    ScheduleResult,
    TokenPair,
)

logger = structlog.get_logger("platform.instagram")

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
IG_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"


class InstagramPlatform(PlatformBase):
    PLATFORM_NAME = "instagram"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=2200,
        max_media_count=10,
        max_hashtags=30,
        supported_media_types=["image/jpeg", "image/png", "video/mp4"],
        rate_limit_per_minute=30,
        rate_limit_per_day=25,
    )

    SCOPES = [
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_insights",
        "pages_show_list",
        "pages_read_engagement",
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
        return f"{IG_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "client_id": self.settings.meta_app_id,
                    "client_secret": self.settings.meta_app_secret.get_secret_value(),
                    "redirect_uri": redirect_uri,
                    "code": oauth_code,
                },
            )

        if response.status_code != 200:
            logger.error("instagram_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Instagram OAuth failed: {response.status_code}")

        data = response.json()
        if "error" in data:
            raise PlatformAuthError(f"Instagram OAuth error: {data['error'].get('message')}")

        expires_in = data.get("expires_in", 5184000)
        return TokenPair(
            access_token=data["access_token"],
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.settings.meta_app_id,
                    "client_secret": self.settings.meta_app_secret.get_secret_value(),
                    "fb_exchange_token": refresh_token,
                },
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Instagram token refresh failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            expires_at=datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 5184000)),
            raw=data,
        )

    async def revoke_token(self, access_token: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{GRAPH_API_BASE}/me/permissions",
                params={"access_token": access_token},
            )
        return response.status_code == 200

    async def _get_ig_user_id(self, access_token: str) -> str:
        """Resolve the Instagram Business account ID via the connected Facebook page."""
        async with self._get_client(access_token) as client:
            response = await client.get("/me/accounts", params={"fields": "instagram_business_account"})

        if response.status_code != 200:
            raise PlatformAPIError("Failed to retrieve Instagram business account")

        pages = response.json().get("data", [])
        for page in pages:
            ig_account = page.get("instagram_business_account", {})
            if ig_account.get("id"):
                return ig_account["id"]

        raise PlatformAPIError("No Instagram Business account found. Connect one via Facebook Page settings.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        if not content.media_urls:
            raise PlatformAPIError("Instagram requires at least one image or video")

        ig_user_id = await self._get_ig_user_id(access_token)

        caption = content.text
        if content.hashtags:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in content.hashtags[:30])
            caption = f"{caption}\n\n{hashtag_str}"

        is_video = any(url.lower().endswith((".mp4", ".mov")) for url in content.media_urls)

        if len(content.media_urls) > 1:
            post_result = await self._publish_carousel(ig_user_id, access_token, content.media_urls, caption)
        elif is_video:
            post_result = await self._publish_single(ig_user_id, access_token, content.media_urls[0], caption, "VIDEO")
        else:
            post_result = await self._publish_single(ig_user_id, access_token, content.media_urls[0], caption, "IMAGE")

        return post_result

    async def _publish_single(
        self, ig_user_id: str, access_token: str, media_url: str, caption: str, media_type: str
    ) -> PostResult:
        container_params: dict = {"caption": caption, "access_token": access_token}
        if media_type == "VIDEO":
            container_params["media_type"] = "VIDEO"
            container_params["video_url"] = media_url
        else:
            container_params["image_url"] = media_url

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=60.0) as client:
            container_resp = await client.post(f"/{ig_user_id}/media", params=container_params)

        self._handle_rate_limit(container_resp)
        if container_resp.status_code != 200:
            raise PlatformAPIError(f"Failed to create Instagram media container: {container_resp.status_code}")

        container_id = container_resp.json().get("id")

        if media_type == "VIDEO":
            await self._wait_for_container(ig_user_id, container_id, access_token)

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=30.0) as client:
            publish_resp = await client.post(
                f"/{ig_user_id}/media_publish",
                params={"creation_id": container_id, "access_token": access_token},
            )

        self._handle_rate_limit(publish_resp)
        if publish_resp.status_code != 200:
            raise PlatformAPIError(f"Failed to publish Instagram media: {publish_resp.status_code}")

        data = publish_resp.json()
        media_id = data.get("id", "unknown")

        return PostResult(
            platform_post_id=media_id,
            url=f"https://www.instagram.com/p/{media_id}/",
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    async def _publish_carousel(
        self, ig_user_id: str, access_token: str, media_urls: list[str], caption: str
    ) -> PostResult:
        children_ids = []
        for url in media_urls[:10]:
            is_video = url.lower().endswith((".mp4", ".mov"))
            params: dict = {"access_token": access_token, "is_carousel_item": "true"}
            if is_video:
                params["media_type"] = "VIDEO"
                params["video_url"] = url
            else:
                params["image_url"] = url

            async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=60.0) as client:
                resp = await client.post(f"/{ig_user_id}/media", params=params)

            self._handle_rate_limit(resp)
            if resp.status_code != 200:
                raise PlatformAPIError(f"Failed to create carousel item: {resp.status_code}")

            children_ids.append(resp.json()["id"])

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=30.0) as client:
            carousel_resp = await client.post(
                f"/{ig_user_id}/media",
                params={
                    "media_type": "CAROUSEL",
                    "caption": caption,
                    "children": ",".join(children_ids),
                    "access_token": access_token,
                },
            )

        self._handle_rate_limit(carousel_resp)
        if carousel_resp.status_code != 200:
            raise PlatformAPIError(f"Failed to create carousel container: {carousel_resp.status_code}")

        container_id = carousel_resp.json()["id"]

        async with httpx.AsyncClient(base_url=GRAPH_API_BASE, timeout=30.0) as client:
            publish_resp = await client.post(
                f"/{ig_user_id}/media_publish",
                params={"creation_id": container_id, "access_token": access_token},
            )

        self._handle_rate_limit(publish_resp)
        if publish_resp.status_code != 200:
            raise PlatformAPIError(f"Failed to publish carousel: {publish_resp.status_code}")

        data = publish_resp.json()
        return PostResult(
            platform_post_id=data.get("id", "unknown"),
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    async def _wait_for_container(self, ig_user_id: str, container_id: str, access_token: str, max_wait: int = 120) -> None:
        """Poll until a video container is ready for publishing."""
        elapsed = 0
        while elapsed < max_wait:
            async with self._get_client(access_token) as client:
                resp = await client.get(f"/{container_id}", params={"fields": "status_code"})
            status = resp.json().get("status_code", "")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise PlatformAPIError("Instagram video processing failed")
            await asyncio.sleep(5)
            elapsed += 5
        raise PlatformAPIError("Instagram video processing timed out")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        async with self._get_client(access_token) as client:
            response = await client.get(
                f"/{post_id}",
                params={"fields": "like_count,comments_count,timestamp,media_type"},
            )

        self._handle_rate_limit(response)
        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Instagram post data: {response.status_code}")

        post_data = response.json()

        async with self._get_client(access_token) as client:
            insights_resp = await client.get(
                f"/{post_id}/insights",
                params={"metric": "impressions,reach,saved,shares"},
            )

        impressions = reach = saves = shares = 0
        if insights_resp.status_code == 200:
            for metric in insights_resp.json().get("data", []):
                name = metric.get("name", "")
                value = metric.get("values", [{}])[0].get("value", 0)
                if name == "impressions":
                    impressions = value
                elif name == "reach":
                    reach = value
                elif name == "saved":
                    saves = value
                elif name == "shares":
                    shares = value

        return AnalyticsData(
            post_id=post_id,
            platform="instagram",
            metrics=EngagementMetrics(
                impressions=impressions,
                reach=reach,
                likes=post_data.get("like_count", 0),
                comments=post_data.get("comments_count", 0),
                saves=saves,
                shares=shares,
            ),
            collected_at=datetime.now(UTC),
            raw=post_data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        ig_user_id = await self._get_ig_user_id(access_token)

        async with self._get_client(access_token) as client:
            response = await client.get(
                f"/{ig_user_id}",
                params={"fields": "followers_count,follows_count,media_count,name,biography"},
            )

        self._handle_rate_limit(response)
        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Instagram audience: {response.status_code}")

        data = response.json()

        segments: list[AudienceSegment] = []
        async with self._get_client(access_token) as client:
            insights_resp = await client.get(
                f"/{ig_user_id}/insights",
                params={
                    "metric": "audience_city,audience_gender_age",
                    "period": "lifetime",
                },
            )
        if insights_resp.status_code == 200:
            for metric in insights_resp.json().get("data", []):
                if metric.get("name") == "audience_gender_age":
                    values = metric.get("values", [{}])[0].get("value", {})
                    total = sum(values.values()) or 1
                    for key, count in sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]:
                        segments.append(AudienceSegment(name=key, size=count, percentage=count / total * 100))

        return AudienceData(
            total_followers=data.get("followers_count", 0),
            demographics={
                "following": data.get("follows_count", 0),
                "media_count": data.get("media_count", 0),
            },
            top_segments=segments,
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "Instagram doesn't support native scheduling via Graph API. Use OrchestraAI's scheduler instead."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        async with self._get_client(access_token) as client:
            response = await client.delete(f"/{post_id}")

        self._handle_rate_limit(response)
        return response.status_code == 200

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        return RateLimitStatus(
            remaining=self.PLATFORM_LIMITS.rate_limit_per_minute,
            limit=self.PLATFORM_LIMITS.rate_limit_per_minute,
            reset_at=datetime.now(UTC) + timedelta(minutes=1),
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 600))
            logger.warning("instagram_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("Instagram rate limit exceeded", retry_after=retry_after)

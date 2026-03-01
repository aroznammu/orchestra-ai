"""Google Ads platform connector.

Uses Google Ads API v16 with OAuth 2.0.
Supports campaign management, ad creation, and performance analytics.
Reuses Google OAuth credentials; additionally requires a Developer Token.
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

logger = structlog.get_logger("platform.google_ads")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ADS_API_BASE = "https://googleads.googleapis.com/v16"


class GoogleAdsPlatform(PlatformBase):
    PLATFORM_NAME = "google_ads"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=90,
        max_media_count=20,
        max_hashtags=None,
        supported_media_types=["image/jpeg", "image/png", "image/gif", "video/mp4"],
        rate_limit_per_minute=60,
        rate_limit_per_day=15000,
    )

    SCOPES = [
        "https://www.googleapis.com/auth/adwords",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "developer-token": self.settings.google_ads_developer_token.get_secret_value(),
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(
            base_url=GOOGLE_ADS_API_BASE,
            headers=headers,
            timeout=30.0,
        )

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.settings.google_ads_client_id or self.settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        client_id = self.settings.google_ads_client_id or self.settings.google_client_id
        client_secret = (
            self.settings.google_ads_client_secret.get_secret_value()
            or self.settings.google_client_secret.get_secret_value()
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error("google_ads_auth_failed", status=response.status_code, body=response.text)
            raise PlatformAuthError(f"Google Ads OAuth failed: {response.status_code}")

        data = response.json()
        expires_in = data.get("expires_in", 3600)

        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            scopes=data.get("scope", "").split(),
            raw=data,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        client_id = self.settings.google_ads_client_id or self.settings.google_client_id
        client_secret = (
            self.settings.google_ads_client_secret.get_secret_value()
            or self.settings.google_client_secret.get_secret_value()
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            raise PlatformAuthError(f"Google Ads token refresh failed: {response.status_code}")

        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
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

    async def _get_customer_id(self, access_token: str) -> str:
        """List accessible customer accounts and return the first."""
        async with self._get_client(access_token) as client:
            response = await client.get("/customers:listAccessibleCustomers")

        if response.status_code != 200:
            raise PlatformAPIError("Failed to list Google Ads customers")

        resource_names = response.json().get("resourceNames", [])
        if not resource_names:
            raise PlatformAPIError("No Google Ads customer accounts found")

        return resource_names[0].split("/")[-1]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        """Create a responsive search ad in the specified campaign."""
        errors = self.validate_content(content)
        if errors:
            raise PlatformAPIError(f"Content validation failed: {'; '.join(errors)}")

        customer_id = await self._get_customer_id(access_token)
        campaign_id = content.platform_specific.get("campaign_id")
        ad_group_id = content.platform_specific.get("ad_group_id")

        if not campaign_id or not ad_group_id:
            raise PlatformAPIError("campaign_id and ad_group_id are required in platform_specific")

        headlines = content.platform_specific.get("headlines", [content.text[:30]])
        descriptions = content.platform_specific.get("descriptions", [content.text[:90]])

        ad_operation = {
            "operations": [{
                "create": {
                    "adGroup": f"customers/{customer_id}/adGroups/{ad_group_id}",
                    "ad": {
                        "responsiveSearchAd": {
                            "headlines": [{"text": h[:30]} for h in headlines[:15]],
                            "descriptions": [{"text": d[:90]} for d in descriptions[:4]],
                        },
                        "finalUrls": [content.link or content.platform_specific.get("final_url", "https://example.com")],
                    },
                    "status": "ENABLED",
                },
            }],
        }

        async with self._get_client(access_token) as client:
            client.headers["login-customer-id"] = customer_id
            response = await client.post(
                f"/customers/{customer_id}/adGroupAds:mutate",
                json=ad_operation,
            )

        self._handle_rate_limit(response)

        if response.status_code not in (200, 201):
            logger.error("google_ads_publish_failed", status=response.status_code, body=response.text)
            raise PlatformAPIError(f"Failed to create Google Ads ad: {response.status_code}")

        data = response.json()
        results = data.get("results", [{}])
        resource_name = results[0].get("resourceName", "unknown") if results else "unknown"

        return PostResult(
            platform_post_id=resource_name,
            published_at=datetime.now(UTC),
            raw_response=data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        customer_id = await self._get_customer_id(access_token)

        query = """
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date DURING LAST_7_DAYS
            ORDER BY metrics.impressions DESC
            LIMIT 10
        """

        async with self._get_client(access_token) as client:
            client.headers["login-customer-id"] = customer_id
            response = await client.post(
                f"/customers/{customer_id}/googleAds:searchStream",
                json={"query": query},
            )

        self._handle_rate_limit(response)

        impressions = clicks = 0
        cost_micros = 0
        raw_data = {}

        if response.status_code == 200:
            results = response.json()
            if isinstance(results, list) and results:
                batch = results[0]
                for row in batch.get("results", []):
                    m = row.get("metrics", {})
                    impressions += m.get("impressions", 0)
                    clicks += m.get("clicks", 0)
                    cost_micros += m.get("costMicros", 0)
                raw_data = batch

        return AnalyticsData(
            post_id=post_id,
            platform="google_ads",
            metrics=EngagementMetrics(
                impressions=impressions,
                clicks=clicks,
                engagement_rate=clicks / impressions * 100 if impressions else 0,
            ),
            collected_at=datetime.now(UTC),
            raw=raw_data,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def get_audience(self, access_token: str) -> AudienceData:
        customer_id = await self._get_customer_id(access_token)

        async with self._get_client(access_token) as client:
            client.headers["login-customer-id"] = customer_id
            response = await client.get(f"/customers/{customer_id}")

        self._handle_rate_limit(response)

        if response.status_code != 200:
            raise PlatformAPIError(f"Failed to get Google Ads customer info: {response.status_code}")

        data = response.json()
        return AudienceData(
            total_followers=0,
            demographics={
                "customer_id": customer_id,
                "descriptive_name": data.get("descriptiveName", ""),
                "currency_code": data.get("currencyCode", ""),
                "time_zone": data.get("timeZone", ""),
            },
            raw=data,
        )

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise PlatformAPIError(
            "Google Ads scheduling is handled via campaign start/end dates. Use OrchestraAI's scheduler."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        """Remove an ad by setting its status to REMOVED."""
        customer_id = await self._get_customer_id(access_token)

        async with self._get_client(access_token) as client:
            client.headers["login-customer-id"] = customer_id
            response = await client.post(
                f"/customers/{customer_id}/adGroupAds:mutate",
                json={
                    "operations": [{
                        "remove": post_id,
                    }],
                },
            )

        self._handle_rate_limit(response)
        return response.status_code in (200, 201)

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        return RateLimitStatus(
            remaining=self.PLATFORM_LIMITS.rate_limit_per_minute,
            limit=self.PLATFORM_LIMITS.rate_limit_per_minute,
            reset_at=datetime.now(UTC) + timedelta(minutes=1),
        )

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 60))
            logger.warning("google_ads_rate_limited", retry_after=retry_after)
            raise PlatformRateLimitError("Google Ads rate limit exceeded", retry_after=retry_after)

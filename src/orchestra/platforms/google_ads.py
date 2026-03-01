"""Google Ads platform connector (stub -- requires Ads Manager + developer token)."""

from orchestra.platforms.base import (
    AnalyticsData,
    AudienceData,
    PlatformBase,
    PlatformLimits,
    PostContent,
    PostResult,
    RateLimitStatus,
    ScheduleResult,
    TokenPair,
)


class GoogleAdsPlatform(PlatformBase):
    PLATFORM_NAME = "google_ads"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=90,
        max_media_count=20,
        max_hashtags=None,
        supported_media_types=["image/jpeg", "image/png", "video/mp4"],
        rate_limit_per_minute=1000,
        rate_limit_per_day=None,
    )

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        raise NotImplementedError("Google Ads connector: awaiting developer token")

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        raise NotImplementedError("Google Ads connector stub")

    async def revoke_token(self, access_token: str) -> bool:
        raise NotImplementedError("Google Ads connector stub")

    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        raise NotImplementedError("Google Ads connector stub")

    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        raise NotImplementedError("Google Ads connector stub")

    async def get_audience(self, access_token: str) -> AudienceData:
        raise NotImplementedError("Google Ads connector stub")

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise NotImplementedError("Google Ads connector stub")

    async def delete_post(self, post_id: str, access_token: str) -> bool:
        raise NotImplementedError("Google Ads connector stub")

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        raise NotImplementedError("Google Ads connector stub")

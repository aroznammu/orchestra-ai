"""Pinterest platform connector (stub -- free, easy approval)."""

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


class PinterestPlatform(PlatformBase):
    PLATFORM_NAME = "pinterest"
    PLATFORM_LIMITS = PlatformLimits(
        max_text_length=500,
        max_media_count=1,
        max_hashtags=20,
        supported_media_types=["image/jpeg", "image/png"],
        rate_limit_per_minute=100,
        rate_limit_per_day=None,
    )

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        raise NotImplementedError("Pinterest connector: stub for Phase 2")

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        raise NotImplementedError("Pinterest connector stub")

    async def revoke_token(self, access_token: str) -> bool:
        raise NotImplementedError("Pinterest connector stub")

    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        raise NotImplementedError("Pinterest connector stub")

    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        raise NotImplementedError("Pinterest connector stub")

    async def get_audience(self, access_token: str) -> AudienceData:
        raise NotImplementedError("Pinterest connector stub")

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise NotImplementedError("Pinterest connector stub")

    async def delete_post(self, post_id: str, access_token: str) -> bool:
        raise NotImplementedError("Pinterest connector stub")

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        raise NotImplementedError("Pinterest connector stub")

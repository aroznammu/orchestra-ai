"""TikTok platform connector (stub -- requires developer portal approval)."""

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

    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        raise NotImplementedError("TikTok connector: awaiting developer portal approval")

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        raise NotImplementedError("TikTok connector stub")

    async def revoke_token(self, access_token: str) -> bool:
        raise NotImplementedError("TikTok connector stub")

    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        raise NotImplementedError("TikTok connector stub")

    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        raise NotImplementedError("TikTok connector stub")

    async def get_audience(self, access_token: str) -> AudienceData:
        raise NotImplementedError("TikTok connector stub")

    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        raise NotImplementedError("TikTok connector stub")

    async def delete_post(self, post_id: str, access_token: str) -> bool:
        raise NotImplementedError("TikTok connector stub")

    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        raise NotImplementedError("TikTok connector stub")

"""Abstract platform interface that all connectors implement."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Shared types ---


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    token_type: str = "Bearer"
    scopes: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class PostContent(BaseModel):
    text: str
    media_urls: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    link: str | None = None
    scheduled_at: datetime | None = None
    platform_specific: dict[str, Any] = Field(default_factory=dict)


class PostResult(BaseModel):
    platform_post_id: str
    url: str | None = None
    published_at: datetime | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ScheduleResult(BaseModel):
    platform_schedule_id: str
    scheduled_at: datetime
    raw_response: dict[str, Any] = Field(default_factory=dict)


class EngagementMetrics(BaseModel):
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    saves: int = 0
    video_views: int = 0
    engagement_rate: float = 0.0


class AnalyticsData(BaseModel):
    post_id: str
    platform: str
    metrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    collected_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AudienceSegment(BaseModel):
    name: str
    size: int = 0
    percentage: float = 0.0


class AudienceData(BaseModel):
    total_followers: int = 0
    demographics: dict[str, Any] = Field(default_factory=dict)
    top_segments: list[AudienceSegment] = Field(default_factory=list)
    active_hours: list[int] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class PlatformLimits(BaseModel):
    max_text_length: int
    max_media_count: int = 1
    max_hashtags: int | None = None
    supported_media_types: list[str] = Field(default_factory=lambda: ["image/jpeg", "image/png"])
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int | None = None


class RateLimitStatus(BaseModel):
    remaining: int
    limit: int
    reset_at: datetime | None = None


# --- Abstract base ---


class PlatformBase(ABC):
    """Abstract interface for all platform connectors.

    Every platform (Twitter, YouTube, Facebook, etc.) implements this interface.
    """

    PLATFORM_NAME: str = ""
    PLATFORM_LIMITS: PlatformLimits

    @abstractmethod
    async def authenticate(self, oauth_code: str, redirect_uri: str) -> TokenPair:
        """Exchange OAuth code for access + refresh tokens."""
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh an expired access token."""
        ...

    @abstractmethod
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke access (disconnect platform)."""
        ...

    @abstractmethod
    async def publish(self, content: PostContent, access_token: str) -> PostResult:
        """Publish content to the platform."""
        ...

    @abstractmethod
    async def get_analytics(self, post_id: str, access_token: str) -> AnalyticsData:
        """Get engagement analytics for a specific post."""
        ...

    @abstractmethod
    async def get_audience(self, access_token: str) -> AudienceData:
        """Get audience demographics and insights."""
        ...

    @abstractmethod
    async def schedule(self, content: PostContent, access_token: str) -> ScheduleResult:
        """Schedule content for future publishing."""
        ...

    @abstractmethod
    async def delete_post(self, post_id: str, access_token: str) -> bool:
        """Delete a published post."""
        ...

    @abstractmethod
    async def get_rate_limit_status(self, access_token: str) -> RateLimitStatus:
        """Check current rate limit status."""
        ...

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL. Override per platform."""
        raise NotImplementedError(f"{self.PLATFORM_NAME} auth URL not implemented")

    def validate_content(self, content: PostContent) -> list[str]:
        """Validate content against platform limits. Returns list of errors."""
        errors = []
        limits = self.PLATFORM_LIMITS

        if len(content.text) > limits.max_text_length:
            errors.append(
                f"Text exceeds {self.PLATFORM_NAME} limit: "
                f"{len(content.text)}/{limits.max_text_length} chars"
            )

        if len(content.media_urls) > limits.max_media_count:
            errors.append(
                f"Too many media items: {len(content.media_urls)}/{limits.max_media_count}"
            )

        if limits.max_hashtags and len(content.hashtags) > limits.max_hashtags:
            errors.append(
                f"Too many hashtags: {len(content.hashtags)}/{limits.max_hashtags}"
            )

        return errors

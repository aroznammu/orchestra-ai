"""Machine-readable Terms of Service rules per platform.

Each platform's ToS constraints are encoded as structured data so the
compliance engine can validate actions programmatically.
"""

from typing import Any

from pydantic import BaseModel, Field


class RateLimitRule(BaseModel):
    endpoint: str
    requests_per_window: int
    window_seconds: int
    buffer_pct: float = 0.15  # stay 15% below limit


class ContentRule(BaseModel):
    max_text_length: int
    max_media_count: int
    max_hashtags: int | None = None
    allows_links: bool = True
    allows_mentions: bool = True
    max_mentions: int | None = None
    requires_media: bool = False
    allowed_media_types: list[str] = Field(default_factory=lambda: ["image", "video"])
    max_video_duration_seconds: int | None = None


class AutomationRule(BaseModel):
    allows_automated_posting: bool = True
    requires_disclosure: bool = False
    disclosure_text: str = ""
    max_posts_per_day: int = 50
    min_interval_seconds: int = 60
    allows_automated_engagement: bool = False
    allows_automated_dm: bool = False


class TargetingRule(BaseModel):
    allows_age_targeting: bool = True
    min_age: int = 18
    prohibited_categories: list[str] = Field(default_factory=list)
    requires_special_approval: list[str] = Field(default_factory=list)


class PlatformToS(BaseModel):
    """Complete ToS ruleset for a platform."""

    platform: str
    version: str
    last_updated: str
    content: ContentRule
    rate_limits: list[RateLimitRule] = Field(default_factory=list)
    automation: AutomationRule = Field(default_factory=AutomationRule)
    targeting: TargetingRule = Field(default_factory=TargetingRule)
    prohibited_content: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)


PLATFORM_TOS: dict[str, PlatformToS] = {
    "twitter": PlatformToS(
        platform="twitter",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=280, max_media_count=4, max_hashtags=None,
        ),
        rate_limits=[
            RateLimitRule(endpoint="tweets", requests_per_window=300, window_seconds=900),
            RateLimitRule(endpoint="likes", requests_per_window=1000, window_seconds=86400),
            RateLimitRule(endpoint="follows", requests_per_window=400, window_seconds=86400),
        ],
        automation=AutomationRule(
            max_posts_per_day=100, min_interval_seconds=30,
            allows_automated_engagement=False, allows_automated_dm=False,
        ),
        prohibited_content=[
            "spam", "manipulation", "misleading claims", "synthetic media without label",
            "hateful conduct", "violent content", "private information",
        ],
        required_disclosures=["automated_account_label"],
    ),
    "youtube": PlatformToS(
        platform="youtube",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=5000, max_media_count=1, requires_media=True,
            allowed_media_types=["video"], max_video_duration_seconds=43200,
        ),
        rate_limits=[
            RateLimitRule(endpoint="upload", requests_per_window=50, window_seconds=86400),
            RateLimitRule(endpoint="data_api", requests_per_window=10000, window_seconds=86400),
        ],
        automation=AutomationRule(
            max_posts_per_day=50, min_interval_seconds=300,
        ),
        prohibited_content=[
            "misleading thumbnails", "artificial engagement", "spam",
            "harmful content", "dangerous challenges", "hate speech",
        ],
    ),
    "instagram": PlatformToS(
        platform="instagram",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=2200, max_media_count=10, max_hashtags=30,
            allows_links=False,
        ),
        rate_limits=[
            RateLimitRule(endpoint="content_publish", requests_per_window=25, window_seconds=86400),
            RateLimitRule(endpoint="graph_api", requests_per_window=200, window_seconds=3600),
        ],
        automation=AutomationRule(
            max_posts_per_day=25, min_interval_seconds=600,
            allows_automated_engagement=False,
        ),
        prohibited_content=[
            "misleading before/after", "false health claims",
            "spam", "hate speech", "nudity policy violations",
        ],
    ),
    "facebook": PlatformToS(
        platform="facebook",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=63206, max_media_count=10,
        ),
        rate_limits=[
            RateLimitRule(endpoint="graph_api", requests_per_window=200, window_seconds=3600),
            RateLimitRule(endpoint="pages_publish", requests_per_window=50, window_seconds=86400),
        ],
        targeting=TargetingRule(
            min_age=13,
            prohibited_categories=["housing_discrimination", "employment_discrimination", "credit_discrimination"],
            requires_special_approval=["political_ads", "social_issue_ads", "alcohol", "gambling"],
        ),
        prohibited_content=[
            "misinformation", "hate speech", "clickbait", "spam",
            "unauthorized data collection",
        ],
    ),
    "linkedin": PlatformToS(
        platform="linkedin",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=3000, max_media_count=9,
        ),
        rate_limits=[
            RateLimitRule(endpoint="shares", requests_per_window=100, window_seconds=86400),
            RateLimitRule(endpoint="api_calls", requests_per_window=1000, window_seconds=86400),
        ],
        automation=AutomationRule(
            max_posts_per_day=20, min_interval_seconds=600,
            allows_automated_engagement=False,
        ),
        prohibited_content=[
            "spam", "misleading content", "irrelevant promotions",
            "fake engagement", "scraping",
        ],
    ),
    "tiktok": PlatformToS(
        platform="tiktok",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=2200, max_media_count=1,
            requires_media=True, allowed_media_types=["video"],
            max_video_duration_seconds=600, allows_links=False,
        ),
        rate_limits=[
            RateLimitRule(endpoint="video_publish", requests_per_window=10, window_seconds=86400),
        ],
        automation=AutomationRule(
            max_posts_per_day=10, min_interval_seconds=3600,
        ),
        targeting=TargetingRule(min_age=18),
        prohibited_content=[
            "dangerous challenges", "misleading content",
            "hate speech", "harassment", "minor safety violations",
        ],
    ),
    "pinterest": PlatformToS(
        platform="pinterest",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=500, max_media_count=1, max_hashtags=20,
        ),
        rate_limits=[
            RateLimitRule(endpoint="pins", requests_per_window=50, window_seconds=3600),
        ],
        prohibited_content=[
            "spam pins", "misleading links", "adult content",
        ],
    ),
    "snapchat": PlatformToS(
        platform="snapchat",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=250, max_media_count=1,
        ),
        rate_limits=[
            RateLimitRule(endpoint="marketing_api", requests_per_window=100, window_seconds=3600),
        ],
        prohibited_content=[
            "exploitation", "dangerous activities", "deceptive practices",
        ],
    ),
    "google_ads": PlatformToS(
        platform="google_ads",
        version="2024.1",
        last_updated="2024-12-01",
        content=ContentRule(
            max_text_length=90, max_media_count=20,
        ),
        rate_limits=[
            RateLimitRule(endpoint="ads_api", requests_per_window=15000, window_seconds=86400),
        ],
        targeting=TargetingRule(
            prohibited_categories=["housing", "employment", "credit", "political_content"],
            requires_special_approval=["healthcare", "financial_services", "gambling", "alcohol"],
        ),
        prohibited_content=[
            "misleading claims", "counterfeit goods", "dangerous products",
            "inappropriate content", "trademarks abuse",
        ],
    ),
}


def get_tos(platform: str) -> PlatformToS | None:
    """Get ToS rules for a platform."""
    return PLATFORM_TOS.get(platform)


def get_all_platforms() -> list[str]:
    """Get all platforms with defined ToS rules."""
    return list(PLATFORM_TOS.keys())

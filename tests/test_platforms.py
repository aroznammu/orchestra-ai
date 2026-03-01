"""Tests for all platform connectors.

Validates instantiation, content validation, auth URL generation,
and structural correctness of every platform connector.
"""

import pytest

from orchestra.platforms.base import PlatformBase, PostContent
from orchestra.platforms.tiktok import TikTokPlatform
from orchestra.platforms.pinterest import PinterestPlatform
from orchestra.platforms.facebook import FacebookPlatform
from orchestra.platforms.instagram import InstagramPlatform
from orchestra.platforms.linkedin import LinkedInPlatform
from orchestra.platforms.snapchat import SnapchatPlatform
from orchestra.platforms.google_ads import GoogleAdsPlatform
from orchestra.platforms.twitter import TwitterPlatform
from orchestra.platforms.youtube import YouTubePlatform
from orchestra.platforms import PLATFORM_REGISTRY, get_platform
from orchestra.db.models import PlatformType


ALL_PLATFORM_CLASSES = [
    TwitterPlatform,
    YouTubePlatform,
    FacebookPlatform,
    InstagramPlatform,
    TikTokPlatform,
    LinkedInPlatform,
    GoogleAdsPlatform,
    SnapchatPlatform,
    PinterestPlatform,
]


@pytest.mark.parametrize("cls", ALL_PLATFORM_CLASSES, ids=lambda c: c.PLATFORM_NAME)
def test_platform_instantiation(cls):
    """Every connector can be instantiated without errors."""
    platform = cls()
    assert isinstance(platform, PlatformBase)
    assert platform.PLATFORM_NAME
    assert platform.PLATFORM_LIMITS is not None
    assert platform.PLATFORM_LIMITS.max_text_length > 0


@pytest.mark.parametrize("cls", ALL_PLATFORM_CLASSES, ids=lambda c: c.PLATFORM_NAME)
def test_platform_has_all_abstract_methods(cls):
    """Every connector implements all required methods from PlatformBase."""
    platform = cls()
    required = [
        "authenticate", "refresh_token", "revoke_token",
        "publish", "get_analytics", "get_audience",
        "schedule", "delete_post", "get_rate_limit_status",
    ]
    for method_name in required:
        assert hasattr(platform, method_name), f"{cls.PLATFORM_NAME} missing {method_name}"
        assert callable(getattr(platform, method_name))


@pytest.mark.parametrize("cls", ALL_PLATFORM_CLASSES, ids=lambda c: c.PLATFORM_NAME)
def test_content_validation_too_long(cls):
    """Content exceeding max_text_length should produce validation errors."""
    platform = cls()
    limit = platform.PLATFORM_LIMITS.max_text_length
    content = PostContent(text="x" * (limit + 100))
    errors = platform.validate_content(content)
    assert len(errors) > 0
    assert "exceeds" in errors[0].lower() or "limit" in errors[0].lower()


@pytest.mark.parametrize("cls", ALL_PLATFORM_CLASSES, ids=lambda c: c.PLATFORM_NAME)
def test_content_validation_valid(cls):
    """Short text should pass validation for any platform."""
    platform = cls()
    content = PostContent(text="Hello world")
    errors = platform.validate_content(content)
    assert len(errors) == 0


@pytest.mark.parametrize("cls", ALL_PLATFORM_CLASSES, ids=lambda c: c.PLATFORM_NAME)
def test_content_validation_too_many_media(cls):
    """Exceeding max_media_count should produce a validation error."""
    platform = cls()
    limit = platform.PLATFORM_LIMITS.max_media_count
    content = PostContent(text="test", media_urls=[f"https://example.com/img{i}.jpg" for i in range(limit + 5)])
    errors = platform.validate_content(content)
    assert len(errors) > 0
    assert "media" in errors[0].lower()


def test_registry_has_all_platforms():
    """Platform registry contains all 9 platform types."""
    expected_types = [
        PlatformType.TWITTER, PlatformType.YOUTUBE, PlatformType.FACEBOOK,
        PlatformType.INSTAGRAM, PlatformType.TIKTOK, PlatformType.LINKEDIN,
        PlatformType.GOOGLE_ADS, PlatformType.SNAPCHAT, PlatformType.PINTEREST,
    ]
    for pt in expected_types:
        assert pt in PLATFORM_REGISTRY, f"{pt} missing from registry"


def test_get_platform_factory():
    """get_platform() returns correct instance types."""
    twitter = get_platform(PlatformType.TWITTER)
    assert isinstance(twitter, TwitterPlatform)
    youtube = get_platform(PlatformType.YOUTUBE)
    assert isinstance(youtube, YouTubePlatform)
    tiktok = get_platform(PlatformType.TIKTOK)
    assert isinstance(tiktok, TikTokPlatform)


def test_get_platform_unknown_raises():
    """get_platform() raises ValueError for unknown platform."""
    with pytest.raises(ValueError, match="Unknown platform"):
        get_platform("nonexistent")


# --- Platform-specific auth URL tests ---

def test_tiktok_auth_url():
    platform = TikTokPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "tiktok.com" in url
    assert "state123" in url
    assert "video.publish" in url


def test_pinterest_auth_url():
    platform = PinterestPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "pinterest.com" in url
    assert "state123" in url
    assert "pins%3Awrite" in url or "pins:write" in url


def test_facebook_auth_url():
    platform = FacebookPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "facebook.com" in url
    assert "state123" in url


def test_instagram_auth_url():
    platform = InstagramPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "facebook.com" in url
    assert "instagram_content_publish" in url


def test_linkedin_auth_url():
    platform = LinkedInPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "linkedin.com" in url
    assert "state123" in url
    assert "w_member_social" in url


def test_snapchat_auth_url():
    platform = SnapchatPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "snapchat.com" in url
    assert "state123" in url


def test_google_ads_auth_url():
    platform = GoogleAdsPlatform()
    url = platform.get_auth_url("https://example.com/callback", "state123")
    assert "accounts.google.com" in url
    assert "state123" in url
    assert "adwords" in url


# --- Platform limits correctness ---

def test_tiktok_limits():
    p = TikTokPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 2200
    assert "video/mp4" in p.PLATFORM_LIMITS.supported_media_types


def test_pinterest_limits():
    p = PinterestPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 500
    assert p.PLATFORM_LIMITS.max_hashtags == 20


def test_facebook_limits():
    p = FacebookPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 63206
    assert p.PLATFORM_LIMITS.max_media_count == 10


def test_instagram_limits():
    p = InstagramPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 2200
    assert p.PLATFORM_LIMITS.max_hashtags == 30
    assert p.PLATFORM_LIMITS.rate_limit_per_day == 25


def test_linkedin_limits():
    p = LinkedInPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 3000
    assert p.PLATFORM_LIMITS.max_media_count == 9


def test_snapchat_limits():
    p = SnapchatPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 250


def test_google_ads_limits():
    p = GoogleAdsPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 90
    assert p.PLATFORM_LIMITS.rate_limit_per_day == 15000


def test_twitter_limits():
    p = TwitterPlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 280


def test_youtube_limits():
    p = YouTubePlatform()
    assert p.PLATFORM_LIMITS.max_text_length == 5000

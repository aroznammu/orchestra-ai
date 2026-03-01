"""Platform connector registry."""

from orchestra.db.models import PlatformType
from orchestra.platforms.base import PlatformBase
from orchestra.platforms.facebook import FacebookPlatform
from orchestra.platforms.google_ads import GoogleAdsPlatform
from orchestra.platforms.instagram import InstagramPlatform
from orchestra.platforms.linkedin import LinkedInPlatform
from orchestra.platforms.pinterest import PinterestPlatform
from orchestra.platforms.snapchat import SnapchatPlatform
from orchestra.platforms.tiktok import TikTokPlatform
from orchestra.platforms.twitter import TwitterPlatform
from orchestra.platforms.youtube import YouTubePlatform

PLATFORM_REGISTRY: dict[PlatformType, type[PlatformBase]] = {
    PlatformType.TWITTER: TwitterPlatform,
    PlatformType.YOUTUBE: YouTubePlatform,
    PlatformType.FACEBOOK: FacebookPlatform,
    PlatformType.INSTAGRAM: InstagramPlatform,
    PlatformType.TIKTOK: TikTokPlatform,
    PlatformType.LINKEDIN: LinkedInPlatform,
    PlatformType.GOOGLE_ADS: GoogleAdsPlatform,
    PlatformType.SNAPCHAT: SnapchatPlatform,
    PlatformType.PINTEREST: PinterestPlatform,
}


def get_platform(platform_type: PlatformType) -> PlatformBase:
    """Get a platform connector instance by type."""
    cls = PLATFORM_REGISTRY.get(platform_type)
    if not cls:
        raise ValueError(f"Unknown platform: {platform_type}")
    return cls()

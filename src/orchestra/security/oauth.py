"""OAuth2 flow helpers and encrypted token storage."""

from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestra.db.models import PlatformConnection, PlatformType
from orchestra.platforms.base import TokenPair
from orchestra.security.encryption import decrypt_token, encrypt_token

logger = structlog.get_logger("oauth")


async def store_tokens(
    db: AsyncSession,
    tenant_id: str,
    platform: PlatformType,
    tokens: TokenPair,
    platform_user_id: str | None = None,
) -> PlatformConnection:
    """Store OAuth tokens with encryption."""
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.tenant_id == tenant_id,
            PlatformConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()

    encrypted_access = encrypt_token(tokens.access_token)
    encrypted_refresh = encrypt_token(tokens.refresh_token) if tokens.refresh_token else None

    if conn:
        conn.access_token_encrypted = encrypted_access
        conn.refresh_token_encrypted = encrypted_refresh
        conn.token_expires_at = tokens.expires_at
        conn.is_active = True
        conn.platform_user_id = platform_user_id
        conn.platform_metadata = tokens.raw
        logger.info("tokens_updated", platform=platform.value, tenant_id=tenant_id)
    else:
        conn = PlatformConnection(
            tenant_id=tenant_id,
            platform=platform,
            access_token_encrypted=encrypted_access,
            refresh_token_encrypted=encrypted_refresh,
            token_expires_at=tokens.expires_at,
            is_active=True,
            platform_user_id=platform_user_id,
            platform_metadata=tokens.raw,
        )
        db.add(conn)
        logger.info("tokens_stored", platform=platform.value, tenant_id=tenant_id)

    await db.flush()
    return conn


async def get_tokens(
    db: AsyncSession,
    tenant_id: str,
    platform: PlatformType,
) -> TokenPair | None:
    """Retrieve and decrypt stored tokens."""
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.tenant_id == tenant_id,
            PlatformConnection.platform == platform,
            PlatformConnection.is_active == True,  # noqa: E712
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return None

    return TokenPair(
        access_token=decrypt_token(conn.access_token_encrypted),
        refresh_token=decrypt_token(conn.refresh_token_encrypted) if conn.refresh_token_encrypted else None,
        expires_at=conn.token_expires_at,
        raw=conn.platform_metadata or {},
    )


def is_token_expired(tokens: TokenPair, buffer_seconds: int = 300) -> bool:
    """Check if token is expired or will expire within buffer period."""
    if not tokens.expires_at:
        return False
    return datetime.now(UTC) >= tokens.expires_at.replace(
        tzinfo=UTC if tokens.expires_at.tzinfo is None else tokens.expires_at.tzinfo
    )


async def disconnect_platform(
    db: AsyncSession,
    tenant_id: str,
    platform: PlatformType,
) -> bool:
    """Mark a platform connection as inactive."""
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.tenant_id == tenant_id,
            PlatformConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return False

    conn.is_active = False
    await db.flush()
    logger.info("platform_disconnected", platform=platform.value, tenant_id=tenant_id)
    return True

"""Platform connection API routes (OAuth connect/disconnect/list)."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from orchestra.api.deps import AdminUser, CurrentUser, DbSession
from orchestra.db.models import PlatformConnection, PlatformType
from orchestra.platforms import PLATFORM_REGISTRY, get_platform
from orchestra.security.oauth import disconnect_platform, get_tokens, store_tokens

router = APIRouter(prefix="/platforms", tags=["platforms"])
logger = structlog.get_logger("api.platforms")


class PlatformAuthRequest(BaseModel):
    platform: PlatformType
    redirect_uri: str


class PlatformAuthResponse(BaseModel):
    auth_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    platform: PlatformType
    code: str
    redirect_uri: str


class PlatformConnectionResponse(BaseModel):
    id: str
    platform: str
    is_active: bool
    platform_user_id: str | None
    connected_at: str


class PlatformListResponse(BaseModel):
    connections: list[PlatformConnectionResponse]
    available: list[str]


@router.get("/available")
async def list_available_platforms() -> dict[str, Any]:
    """List all supported platforms and their status."""
    platforms = []
    for ptype, cls in PLATFORM_REGISTRY.items():
        instance = cls()
        platforms.append({
            "platform": ptype.value,
            "name": instance.PLATFORM_NAME,
            "limits": instance.PLATFORM_LIMITS.model_dump(),
            "is_stub": "stub" in (instance.__class__.__module__ or ""),
        })
    return {"platforms": platforms}


@router.post("/auth/init", response_model=PlatformAuthResponse)
async def init_platform_auth(
    request: PlatformAuthRequest,
    current_user: CurrentUser,
) -> PlatformAuthResponse:
    """Generate OAuth authorization URL for a platform."""
    platform = get_platform(request.platform)
    state = str(uuid.uuid4())

    try:
        auth_url = platform.get_auth_url(request.redirect_uri, state)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        ) from e

    logger.info(
        "platform_auth_initiated",
        platform=request.platform.value,
        tenant_id=current_user.tenant_id,
    )
    return PlatformAuthResponse(auth_url=auth_url, state=state)


@router.post("/auth/callback")
async def handle_oauth_callback(
    request: OAuthCallbackRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Handle OAuth callback and store encrypted tokens."""
    platform = get_platform(request.platform)

    try:
        tokens = await platform.authenticate(request.code, request.redirect_uri)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        ) from e

    await store_tokens(
        db=db,
        tenant_id=current_user.tenant_id,
        platform=request.platform,
        tokens=tokens,
    )

    logger.info(
        "platform_connected",
        platform=request.platform.value,
        tenant_id=current_user.tenant_id,
    )
    return {"status": "connected", "platform": request.platform.value}


@router.get("/connections", response_model=PlatformListResponse)
async def list_connections(
    current_user: CurrentUser,
    db: DbSession,
) -> PlatformListResponse:
    """List all platform connections for the current tenant."""
    from sqlalchemy import select

    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.tenant_id == current_user.tenant_id,
        )
    )
    connections = result.scalars().all()

    connected = [
        PlatformConnectionResponse(
            id=str(conn.id),
            platform=conn.platform.value,
            is_active=conn.is_active,
            platform_user_id=conn.platform_user_id,
            connected_at=conn.created_at.isoformat(),
        )
        for conn in connections
    ]

    connected_platforms = {c.platform for c in connections if c.is_active}
    available = [
        p.value for p in PlatformType
        if p not in connected_platforms
    ]

    return PlatformListResponse(connections=connected, available=available)


@router.delete("/connections/{platform}")
async def disconnect(
    platform: PlatformType,
    current_user: AdminUser,
    db: DbSession,
) -> dict[str, str]:
    """Disconnect a platform (admin/owner only)."""
    tokens = await get_tokens(db, current_user.tenant_id, platform)
    if tokens:
        connector = get_platform(platform)
        try:
            await connector.revoke_token(tokens.access_token)
        except (NotImplementedError, Exception):
            pass

    success = await disconnect_platform(db, current_user.tenant_id, platform)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No connection found for {platform.value}",
        )

    logger.info(
        "platform_disconnected",
        platform=platform.value,
        tenant_id=current_user.tenant_id,
    )
    return {"status": "disconnected", "platform": platform.value}

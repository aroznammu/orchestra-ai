"""API key management endpoints.

Keys are hashed (SHA-256) before storage; the plaintext key is returned to
the caller exactly once at creation time. Subsequent reads only expose
metadata (id, name, role, is_active, last_used_at, expires_at, created_at).

Access is restricted to ``owner``/``admin`` roles. A key can never be
issued with a role that outranks the creator's own role.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from orchestra.api.deps import AdminUser, DbSession
from orchestra.api.middleware.auth import _hash_api_key
from orchestra.db.models import APIKey

logger = structlog.get_logger("api.api_keys")

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# ---------------------------------------------------------------------------
# Role hierarchy (local copy to avoid an import cycle with security.rbac)
# ---------------------------------------------------------------------------

_ROLE_RANK = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}
_ALLOWED_KEY_ROLES = {"viewer", "member", "admin"}

KEY_PREFIX = "oa_"
KEY_ENTROPY_BYTES = 32
MAX_KEY_NAME_LENGTH = 255
MAX_KEYS_PER_TENANT = 50


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_KEY_NAME_LENGTH)
    role: str = Field(default="member")
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class APIKeyOut(BaseModel):
    id: str
    name: str
    role: str
    is_active: bool
    last_used_at: str | None
    expires_at: str | None
    created_at: str


class APIKeyCreateResponse(APIKeyOut):
    key: str
    prefix: str


class APIKeyListResponse(BaseModel):
    keys: list[APIKeyOut]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_plaintext_key() -> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(KEY_ENTROPY_BYTES)}"


def _prefix_hint(plaintext: str) -> str:
    """First 8 chars so the UI can echo the key back without storing it."""
    return plaintext[:8]


def _to_out(row: APIKey) -> APIKeyOut:
    return APIKeyOut(
        id=str(row.id),
        name=row.name,
        role=row.role,
        is_active=row.is_active,
        last_used_at=row.last_used_at.isoformat() if row.last_used_at else None,
        expires_at=row.expires_at.isoformat() if row.expires_at else None,
        created_at=row.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(user: AdminUser, db: DbSession) -> APIKeyListResponse:
    """List all API keys for the caller's tenant (metadata only)."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.tenant_id == uuid.UUID(user.tenant_id))
        .order_by(APIKey.created_at.desc())
    )
    rows = list(result.scalars().all())
    return APIKeyListResponse(keys=[_to_out(r) for r in rows])


@router.post(
    "",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: AdminUser,
    db: DbSession,
) -> APIKeyCreateResponse:
    """Create a new API key. The plaintext value is returned exactly once."""
    requested_role = request.role.lower().strip()
    if requested_role not in _ALLOWED_KEY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid role '{request.role}'. "
                f"Allowed roles: {sorted(_ALLOWED_KEY_ROLES)}."
            ),
        )

    caller_rank = _ROLE_RANK.get(user.role, -1)
    requested_rank = _ROLE_RANK.get(requested_role, 99)
    if requested_rank > caller_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Role '{requested_role}' exceeds caller role '{user.role}'."
            ),
        )

    count_result = await db.execute(
        select(APIKey.id).where(APIKey.tenant_id == uuid.UUID(user.tenant_id))
    )
    existing = len(list(count_result.scalars().all()))
    if existing >= MAX_KEYS_PER_TENANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"API key limit reached ({MAX_KEYS_PER_TENANT}). "
                "Revoke an unused key before creating a new one."
            ),
        )

    plaintext = _generate_plaintext_key()
    key_hash = _hash_api_key(plaintext)
    expires_at: datetime | None = None
    if request.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

    row = APIKey(
        tenant_id=uuid.UUID(user.tenant_id),
        user_id=uuid.UUID(user.sub),
        name=request.name,
        key_hash=key_hash,
        role=requested_role,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)

    logger.info(
        "api_key_created",
        key_id=str(row.id),
        tenant_id=user.tenant_id,
        created_by=user.sub,
        role=requested_role,
    )

    out = _to_out(row)
    return APIKeyCreateResponse(
        **out.model_dump(),
        key=plaintext,
        prefix=_prefix_hint(plaintext),
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: str, user: AdminUser, db: DbSession) -> None:
    """Revoke (soft-delete) an API key. Subsequent requests with the key are rejected."""
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key id.",
        ) from exc

    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_uuid,
            APIKey.tenant_id == uuid.UUID(user.tenant_id),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found.",
        )

    if row.is_active:
        row.is_active = False
        await db.flush()

    logger.info(
        "api_key_revoked",
        key_id=str(row.id),
        tenant_id=user.tenant_id,
        revoked_by=user.sub,
    )

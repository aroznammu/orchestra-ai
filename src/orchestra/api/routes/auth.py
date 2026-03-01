"""Authentication API routes -- login, register, token refresh."""

import re
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from orchestra.api.deps import CurrentUser
from orchestra.api.middleware.auth import (
    TokenPayload,
    create_access_token,
    hash_password,
    verify_password,
)
from orchestra.db.models import Tenant, User, UserRole

logger = structlog.get_logger("api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    tenant_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    tenant_id: str
    role: str


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower().strip())
    return re.sub(r"[-\s]+", "-", slug) or "org"


async def _get_session():
    """Get a DB session, returning None if unavailable."""
    try:
        from orchestra.db.session import async_session_factory
        return async_session_factory()
    except Exception:
        return None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> TokenResponse:
    """Register a new user and tenant, persisting to PostgreSQL when available."""
    try:
        session_ctx = await _get_session()
        if session_ctx is None:
            raise RuntimeError("No DB")
        async with session_ctx as db:
            existing = await db.execute(select(User).where(User.email == request.email))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Email already registered")

            tenant = Tenant(
                name=request.tenant_name,
                slug=f"{_slugify(request.tenant_name)}-{uuid.uuid4().hex[:6]}",
            )
            db.add(tenant)
            await db.flush()

            hashed = hash_password(request.password)
            user = User(
                tenant_id=tenant.id,
                email=request.email,
                hashed_password=hashed,
                full_name=request.full_name,
                role=UserRole.OWNER,
            )
            db.add(user)
            await db.flush()

            token = create_access_token(user.id, tenant.id, role="owner")
            await db.commit()
            logger.info("user_registered_db", user_id=str(user.id), email=request.email)
            return TokenResponse(access_token=token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("register_db_unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again later.",
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate against PostgreSQL and receive a JWT."""
    try:
        session_ctx = await _get_session()
        if session_ctx is None:
            raise RuntimeError("No DB")
        async with session_ctx as db:
            result = await db.execute(select(User).where(User.email == request.email))
            user = result.scalar_one_or_none()

            if user and verify_password(request.password, user.hashed_password):
                if not user.is_active:
                    raise HTTPException(status_code=403, detail="Account deactivated")
                token = create_access_token(user.id, user.tenant_id, role=user.role.value)
                logger.info("user_logged_in_db", email=request.email)
                return TokenResponse(access_token=token)

            if user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            raise RuntimeError("User not found, fallback to token generation")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_db_unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again later.",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current authenticated user info, enriched from DB when available."""
    try:
        session_ctx = await _get_session()
        if session_ctx is None:
            raise RuntimeError("No DB")
        async with session_ctx as db:
            result = await db.execute(
                select(User).where(User.id == uuid.UUID(current_user.sub))
            )
            user = result.scalar_one_or_none()
            if user:
                return UserResponse(
                    user_id=str(user.id),
                    email=user.email,
                    full_name=user.full_name,
                    tenant_id=str(user.tenant_id),
                    role=user.role.value,
                )
    except Exception:
        pass

    return UserResponse(
        user_id=current_user.sub,
        email="",
        full_name="",
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )

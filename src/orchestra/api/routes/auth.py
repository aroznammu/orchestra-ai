"""Authentication API routes -- login, register, token refresh."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from orchestra.api.middleware.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    TokenPayload,
)

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


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> TokenResponse:
    """Register a new user and tenant.

    In production, this creates DB records. Currently returns a JWT for the new user.
    """
    import uuid

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    logger.info(
        "user_registered",
        user_id=str(user_id),
        email=request.email,
        tenant_id=str(tenant_id),
    )

    token = create_access_token(user_id, tenant_id, role="owner")
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate and receive a JWT.

    In production, this validates against DB. Currently a placeholder.
    """
    import uuid

    # Placeholder: in production, query DB for user by email
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    token = create_access_token(user_id, tenant_id, role="owner")

    logger.info("user_logged_in", email=request.email)

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user info."""
    return UserResponse(
        user_id=current_user.sub,
        email="",  # Would come from DB lookup
        full_name="",
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )

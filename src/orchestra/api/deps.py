"""FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from orchestra.api.middleware.auth import TokenPayload, get_current_user, require_role
from orchestra.config import Settings, get_settings
from orchestra.db.session import get_db

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser = Annotated[TokenPayload, Depends(require_role("owner", "admin"))]

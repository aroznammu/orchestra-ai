"""GDPR/CCPA compliance API routes."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from orchestra.api.deps import CurrentUser
from orchestra.security.gdpr import get_gdpr_manager
from orchestra.security.rbac import Permission, check_permission

logger = structlog.get_logger("api.gdpr")

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class ExportResponse(BaseModel):
    request_id: str
    status: str
    download_url: str | None = None


class DeletionResponse(BaseModel):
    request_id: str
    status: str
    confirmation_token: str | None = None


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool


class ConsentResponse(BaseModel):
    consent_type: str
    granted: bool
    recorded_at: str


@router.post("/export", response_model=ExportResponse)
async def request_data_export(
    user: dict = Depends(CurrentUser),
) -> ExportResponse:
    """Request a full data export (GDPR Article 20)."""
    check_permission(user.get("role", "viewer"), Permission.DATA_EXPORT)

    manager = get_gdpr_manager()
    request = await manager.request_data_export(
        tenant_id=user.get("tenant_id", ""),
        requested_by=user.get("sub", ""),
    )

    return ExportResponse(
        request_id=request.id,
        status=request.status,
    )


@router.post("/export/{request_id}/process", response_model=ExportResponse)
async def process_data_export(
    request_id: str,
    user: dict = Depends(CurrentUser),
) -> ExportResponse:
    """Process a pending data export request."""
    check_permission(user.get("role", "viewer"), Permission.DATA_EXPORT)

    manager = get_gdpr_manager()
    result = await manager.process_data_export(request_id)

    if not result:
        raise HTTPException(status_code=404, detail="Export request not found or already processed")

    return ExportResponse(
        request_id=result.id,
        status=result.status,
        download_url=result.download_url,
    )


@router.post("/delete", response_model=DeletionResponse)
async def request_data_deletion(
    user: dict = Depends(CurrentUser),
) -> DeletionResponse:
    """Request full data deletion (GDPR Article 17 -- right to erasure)."""
    check_permission(user.get("role", "viewer"), Permission.DATA_DELETE)

    manager = get_gdpr_manager()
    request = await manager.request_data_deletion(
        tenant_id=user.get("tenant_id", ""),
        requested_by=user.get("sub", ""),
    )

    return DeletionResponse(
        request_id=request.id,
        status=request.status,
        confirmation_token=request.confirmation_token,
    )


@router.post("/delete/{request_id}/confirm", response_model=DeletionResponse)
async def confirm_data_deletion(
    request_id: str,
    confirmation_token: str,
    user: dict = Depends(CurrentUser),
) -> DeletionResponse:
    """Confirm and execute data deletion."""
    check_permission(user.get("role", "viewer"), Permission.DATA_DELETE)

    manager = get_gdpr_manager()
    result = await manager.process_data_deletion(request_id, confirmation_token)

    if not result:
        raise HTTPException(status_code=404, detail="Deletion request not found or invalid token")

    return DeletionResponse(
        request_id=result.id,
        status=result.status,
    )


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    request: ConsentRequest,
    user: dict = Depends(CurrentUser),
) -> ConsentResponse:
    """Record a consent decision."""
    manager = get_gdpr_manager()
    record = manager.record_consent(
        tenant_id=user.get("tenant_id", ""),
        user_id=user.get("sub", ""),
        consent_type=request.consent_type,
        granted=request.granted,
    )

    return ConsentResponse(
        consent_type=record.consent_type,
        granted=record.granted,
        recorded_at=record.granted_at,
    )


@router.get("/consent/status")
async def get_consent_status(
    user: dict = Depends(CurrentUser),
) -> dict[str, bool]:
    """Get current consent status for the authenticated user."""
    manager = get_gdpr_manager()
    return manager.get_consent_status(
        tenant_id=user.get("tenant_id", ""),
        user_id=user.get("sub", ""),
    )

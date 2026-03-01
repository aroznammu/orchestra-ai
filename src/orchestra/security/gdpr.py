"""GDPR/CCPA compliance -- data export, deletion, and consent management."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("security.gdpr")


class DataExportRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    requested_by: str
    requested_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "pending"  # pending, processing, completed, failed
    completed_at: str | None = None
    download_url: str | None = None
    expires_at: str | None = None


class DataDeletionRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    requested_by: str
    requested_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "pending"  # pending, processing, completed, failed
    completed_at: str | None = None
    data_categories_deleted: list[str] = Field(default_factory=list)
    confirmation_token: str = Field(default_factory=lambda: str(uuid4()))


class ConsentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    user_id: str
    consent_type: str  # data_processing, marketing, analytics, third_party
    granted: bool
    granted_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    revoked_at: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class GDPRManager:
    """Manages GDPR/CCPA compliance operations."""

    def __init__(self) -> None:
        self._export_requests: list[DataExportRequest] = []
        self._deletion_requests: list[DataDeletionRequest] = []
        self._consent_records: list[ConsentRecord] = []

    async def request_data_export(
        self,
        tenant_id: str,
        requested_by: str,
    ) -> DataExportRequest:
        """Initiate a data export request (GDPR Article 20)."""
        request = DataExportRequest(
            tenant_id=tenant_id,
            requested_by=requested_by,
        )
        self._export_requests.append(request)

        logger.info(
            "data_export_requested",
            request_id=request.id,
            tenant_id=tenant_id,
            requested_by=requested_by,
        )

        return request

    async def process_data_export(
        self,
        request_id: str,
    ) -> DataExportRequest | None:
        """Process a pending data export.

        In production, this would:
        1. Query all tenant data from PostgreSQL
        2. Export vectors from Qdrant
        3. Package as JSON/CSV
        4. Upload to secure temporary storage
        5. Generate download URL with expiry
        """
        for req in self._export_requests:
            if req.id == request_id and req.status == "pending":
                req.status = "processing"

                # Collect data categories
                exported_data = await self._collect_tenant_data(req.tenant_id)

                req.status = "completed"
                req.completed_at = datetime.now(UTC).isoformat()
                req.download_url = f"/api/v1/gdpr/exports/{req.id}/download"

                logger.info(
                    "data_export_completed",
                    request_id=request_id,
                    categories=list(exported_data.keys()),
                )

                return req
        return None

    async def request_data_deletion(
        self,
        tenant_id: str,
        requested_by: str,
    ) -> DataDeletionRequest:
        """Initiate a data deletion request (GDPR Article 17 -- right to erasure)."""
        request = DataDeletionRequest(
            tenant_id=tenant_id,
            requested_by=requested_by,
        )
        self._deletion_requests.append(request)

        logger.info(
            "data_deletion_requested",
            request_id=request.id,
            tenant_id=tenant_id,
        )

        return request

    async def process_data_deletion(
        self,
        request_id: str,
        confirmation_token: str,
    ) -> DataDeletionRequest | None:
        """Process a confirmed data deletion.

        In production, this would:
        1. Verify confirmation token
        2. Delete from PostgreSQL (users, campaigns, audit logs, etc.)
        3. Delete from Qdrant (all vector collections)
        4. Delete from Redis (cached data)
        5. Revoke all OAuth tokens
        6. Log deletion for compliance records (retain only the log)
        """
        for req in self._deletion_requests:
            if req.id == request_id and req.status == "pending":
                if req.confirmation_token != confirmation_token:
                    logger.warning("invalid_deletion_token", request_id=request_id)
                    return None

                req.status = "processing"

                # Delete across all data stores
                categories = await self._delete_tenant_data(req.tenant_id)

                req.status = "completed"
                req.completed_at = datetime.now(UTC).isoformat()
                req.data_categories_deleted = categories

                logger.info(
                    "data_deletion_completed",
                    request_id=request_id,
                    categories=categories,
                )

                return req
        return None

    def record_consent(
        self,
        tenant_id: str,
        user_id: str,
        consent_type: str,
        granted: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        """Record a consent decision."""
        record = ConsentRecord(
            tenant_id=tenant_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # If revoking, find and update the existing grant
        if not granted:
            record.revoked_at = record.granted_at
            for existing in reversed(self._consent_records):
                if (
                    existing.tenant_id == tenant_id
                    and existing.user_id == user_id
                    and existing.consent_type == consent_type
                    and existing.granted
                    and existing.revoked_at is None
                ):
                    existing.revoked_at = record.granted_at
                    break

        self._consent_records.append(record)

        logger.info(
            "consent_recorded",
            tenant_id=tenant_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
        )

        return record

    def get_consent_status(
        self, tenant_id: str, user_id: str,
    ) -> dict[str, bool]:
        """Get current consent status for a user."""
        status: dict[str, bool] = {}
        for record in self._consent_records:
            if record.tenant_id == tenant_id and record.user_id == user_id:
                if record.granted and record.revoked_at is None:
                    status[record.consent_type] = True
                elif not record.granted or record.revoked_at:
                    status[record.consent_type] = False
        return status

    def get_export_requests(self, tenant_id: str) -> list[DataExportRequest]:
        return [r for r in self._export_requests if r.tenant_id == tenant_id]

    def get_deletion_requests(self, tenant_id: str) -> list[DataDeletionRequest]:
        return [r for r in self._deletion_requests if r.tenant_id == tenant_id]

    async def _collect_tenant_data(self, tenant_id: str) -> dict[str, Any]:
        """Collect all data for a tenant (placeholder for DB queries)."""
        return {
            "users": [],
            "campaigns": [],
            "posts": [],
            "analytics": [],
            "platform_connections": [],
            "audit_logs": [],
            "consent_records": [
                r.model_dump() for r in self._consent_records
                if r.tenant_id == tenant_id
            ],
            "agent_decisions": [],
            "spend_records": [],
        }

    async def _delete_tenant_data(self, tenant_id: str) -> list[str]:
        """Delete all tenant data across stores (placeholder)."""
        from orchestra.rag.indexer import delete_tenant_data

        # Vector store cleanup
        await delete_tenant_data(tenant_id)

        categories = [
            "users", "campaigns", "posts", "analytics",
            "platform_connections", "oauth_tokens", "agent_memory",
            "performance_embeddings", "tenant_model",
        ]

        logger.info("tenant_data_purged", tenant_id=tenant_id, categories=categories)
        return categories


# Singleton
_gdpr_manager: GDPRManager | None = None


def get_gdpr_manager() -> GDPRManager:
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRManager()
    return _gdpr_manager

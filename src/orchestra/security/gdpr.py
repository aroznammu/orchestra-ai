"""GDPR/CCPA compliance -- data export, deletion, and consent management."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

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
        self._export_data: dict[str, dict[str, Any]] = {}

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
        db: AsyncSession | None = None,
    ) -> DataExportRequest | None:
        """Process a pending data export by querying PostgreSQL."""
        for req in self._export_requests:
            if req.id == request_id and req.status == "pending":
                req.status = "processing"

                exported_data = await self._collect_tenant_data(req.tenant_id, db=db)

                req.status = "completed"
                req.completed_at = datetime.now(UTC).isoformat()
                req.download_url = f"/api/v1/gdpr/exports/{req.id}/download"

                self._export_data[req.id] = exported_data

                logger.info(
                    "data_export_completed",
                    request_id=request_id,
                    categories=list(exported_data.keys()),
                    total_records=sum(len(v) for v in exported_data.values() if isinstance(v, list)),
                )

                return req
        return None

    def get_export_data(self, request_id: str) -> dict[str, Any] | None:
        """Return the collected export data for a completed request."""
        return self._export_data.get(request_id)

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
        db: AsyncSession | None = None,
    ) -> DataDeletionRequest | None:
        """Process a confirmed data deletion.

        Deletes from PostgreSQL (cascade), Qdrant (vectors), and logs for compliance.
        """
        for req in self._deletion_requests:
            if req.id == request_id and req.status == "pending":
                if req.confirmation_token != confirmation_token:
                    logger.warning("invalid_deletion_token", request_id=request_id)
                    return None

                req.status = "processing"

                categories = await self._delete_tenant_data(req.tenant_id, db=db)

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

    async def _collect_tenant_data(
        self, tenant_id: str, db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Collect all data for a tenant from PostgreSQL."""
        from sqlalchemy import select as sa_select

        data: dict[str, Any] = {
            "consent_records": [
                r.model_dump() for r in self._consent_records
                if r.tenant_id == tenant_id
            ],
        }

        if db is None:
            return data

        import uuid as _uuid

        from orchestra.db.models import (
            AuditLog,
            Campaign,
            CampaignPost,
            ChatMessage,
            ChatSession,
            Experiment,
            PlatformConnection,
            SpendRecord,
            Tenant,
            User,
        )

        tid = _uuid.UUID(tenant_id)

        tenant_row = (await db.execute(sa_select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
        data["tenant"] = {
            "id": str(tenant_row.id), "name": tenant_row.name, "slug": tenant_row.slug,
        } if tenant_row else None

        users = (await db.execute(sa_select(User).where(User.tenant_id == tid))).scalars().all()
        data["users"] = [
            {"id": str(u.id), "email": u.email, "full_name": u.full_name,
             "role": u.role.value, "created_at": str(u.created_at)}
            for u in users
        ]

        campaigns = (await db.execute(sa_select(Campaign).where(Campaign.tenant_id == tid))).scalars().all()
        campaign_ids = [c.id for c in campaigns]
        data["campaigns"] = [
            {"id": str(c.id), "name": c.name, "status": c.status.value if hasattr(c.status, "value") else str(c.status),
             "platforms": c.platforms, "budget": float(c.budget) if c.budget else 0,
             "created_at": str(c.created_at)}
            for c in campaigns
        ]

        if campaign_ids:
            posts = (await db.execute(
                sa_select(CampaignPost).where(CampaignPost.campaign_id.in_(campaign_ids))
            )).scalars().all()
            data["posts"] = [
                {"id": str(p.id), "campaign_id": str(p.campaign_id), "platform": p.platform,
                 "content": p.content, "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                 "created_at": str(p.created_at)}
                for p in posts
            ]

            experiments = (await db.execute(
                sa_select(Experiment).where(Experiment.campaign_id.in_(campaign_ids))
            )).scalars().all()
            data["experiments"] = [
                {"id": str(e.id), "campaign_id": str(e.campaign_id), "name": e.name,
                 "status": e.status.value if hasattr(e.status, "value") else str(e.status),
                 "hypothesis": e.hypothesis, "variants": e.variants}
                for e in experiments
            ]
        else:
            data["posts"] = []
            data["experiments"] = []

        connections = (await db.execute(
            sa_select(PlatformConnection).where(PlatformConnection.tenant_id == tid)
        )).scalars().all()
        data["platform_connections"] = [
            {"id": str(pc.id), "platform": pc.platform, "created_at": str(pc.created_at)}
            for pc in connections
        ]

        spend = (await db.execute(
            sa_select(SpendRecord).where(SpendRecord.tenant_id == tid)
        )).scalars().all()
        data["spend_records"] = [
            {"id": str(s.id), "campaign_id": str(s.campaign_id) if s.campaign_id else None,
             "platform": s.platform, "amount": float(s.amount),
             "recorded_at": str(s.recorded_at)}
            for s in spend
        ]

        audit = (await db.execute(
            sa_select(AuditLog).where(AuditLog.tenant_id == tid)
        )).scalars().all()
        data["audit_logs"] = [
            {"id": str(a.id), "action": a.action, "resource_type": a.resource_type,
             "details": a.details, "created_at": str(a.created_at)}
            for a in audit
        ]

        sessions = (await db.execute(
            sa_select(ChatSession).where(ChatSession.tenant_id == tid)
        )).scalars().all()
        session_ids = [s.id for s in sessions]
        data["chat_sessions"] = [
            {"id": str(s.id), "title": s.title, "status": s.status,
             "created_at": str(s.created_at)}
            for s in sessions
        ]

        if session_ids:
            messages = (await db.execute(
                sa_select(ChatMessage).where(ChatMessage.session_id.in_(session_ids))
            )).scalars().all()
            data["chat_messages"] = [
                {"id": str(m.id), "session_id": str(m.session_id), "role": m.role,
                 "content": m.content, "created_at": str(m.created_at)}
                for m in messages
            ]
        else:
            data["chat_messages"] = []

        return data

    async def _delete_tenant_data(
        self, tenant_id: str, db: AsyncSession | None = None,
    ) -> list[str]:
        """Delete all tenant data from PostgreSQL and Qdrant."""
        import uuid as _uuid

        from orchestra.db.models import (
            APIKey,
            AuditLog,
            Campaign,
            CampaignPost,
            ChatMessage,
            ChatSession,
            Experiment,
            KillSwitchEventLog,
            PlatformConnection,
            SpendRecord,
            Tenant,
            User,
        )

        categories: list[str] = []
        tid = _uuid.UUID(tenant_id)

        if db is not None:
            session_ids_result = await db.execute(
                sa_delete(ChatMessage).where(
                    ChatMessage.session_id.in_(
                        ChatSession.__table__.select()
                        .where(ChatSession.tenant_id == tid)
                        .with_only_columns(ChatSession.id)
                    )
                )
            )
            categories.append(f"chat_messages:{session_ids_result.rowcount}")

            for model, label in [
                (ChatSession, "chat_sessions"),
            ]:
                result = await db.execute(
                    sa_delete(model).where(model.tenant_id == tid)
                )
                categories.append(f"{label}:{result.rowcount}")

            campaign_ids_result = await db.execute(
                Campaign.__table__.select()
                .where(Campaign.tenant_id == tid)
                .with_only_columns(Campaign.id)
            )
            campaign_ids = [row[0] for row in campaign_ids_result.fetchall()]

            if campaign_ids:
                for model, label in [
                    (CampaignPost, "campaign_posts"),
                    (Experiment, "experiments"),
                ]:
                    result = await db.execute(
                        sa_delete(model).where(model.campaign_id.in_(campaign_ids))
                    )
                    categories.append(f"{label}:{result.rowcount}")

            for model, label in [
                (Campaign, "campaigns"),
                (SpendRecord, "spend_records"),
                (AuditLog, "audit_logs"),
                (APIKey, "api_keys"),
                (PlatformConnection, "platform_connections"),
            ]:
                result = await db.execute(
                    sa_delete(model).where(model.tenant_id == tid)
                )
                categories.append(f"{label}:{result.rowcount}")

            ks_result = await db.execute(
                sa_delete(KillSwitchEventLog).where(
                    KillSwitchEventLog.tenant_id == tenant_id
                )
            )
            categories.append(f"kill_switch_events:{ks_result.rowcount}")

            user_result = await db.execute(
                sa_delete(User).where(User.tenant_id == tid)
            )
            categories.append(f"users:{user_result.rowcount}")

            tenant_result = await db.execute(
                sa_delete(Tenant).where(Tenant.id == tid)
            )
            categories.append(f"tenant:{tenant_result.rowcount}")

            await db.flush()

        try:
            from orchestra.rag.indexer import delete_tenant_data
            await delete_tenant_data(tenant_id)
            categories.append("vector_store")
        except Exception as e:
            logger.warning("qdrant_cleanup_failed", tenant_id=tenant_id, error=str(e))

        logger.info("tenant_data_purged", tenant_id=tenant_id, categories=categories)
        return categories


# Singleton
_gdpr_manager: GDPRManager | None = None


def get_gdpr_manager() -> GDPRManager:
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRManager()
    return _gdpr_manager

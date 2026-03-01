"""SQLAlchemy models for OrchestraAI.

All tables include tenant_id for multi-tenant isolation.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict: JSONB,
    }


class TimestampMixin:
    """Adds created_at and updated_at to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# --- Enums ---


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class PlatformType(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    GOOGLE_ADS = "google_ads"
    LINKEDIN = "linkedin"
    SNAPCHAT = "snapchat"
    PINTEREST = "pinterest"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BiddingPhase(str, enum.Enum):
    HARD_GUARDRAIL = "hard_guardrail"
    SEMI_AUTONOMOUS = "semi_autonomous"
    CONTROLLED_AUTONOMOUS = "controlled_autonomous"


# --- Models ---


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    bidding_phase: Mapped[BiddingPhase] = mapped_column(
        Enum(BiddingPhase), default=BiddingPhase.HARD_GUARDRAIL
    )
    daily_spend_cap: Mapped[float] = mapped_column(Float, default=100.0)
    monthly_spend_cap: Mapped[float] = mapped_column(Float, default=3000.0)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    platform_connections: Mapped[list["PlatformConnection"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    __table_args__ = (Index("ix_users_tenant_email", "tenant_id", "email"),)


class PlatformConnection(TimestampMixin, Base):
    __tablename__ = "platform_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    platform_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    tenant: Mapped["Tenant"] = relationship(back_populates="platform_connections")

    __table_args__ = (
        Index("ix_platform_conn_tenant_platform", "tenant_id", "platform", unique=True),
    )


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    platforms: Mapped[list[str]] = mapped_column(JSONB, default=list)
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    target_audience: Mapped[dict] = mapped_column(JSONB, default=dict)

    tenant: Mapped["Tenant"] = relationship(back_populates="campaigns")
    posts: Mapped[list["CampaignPost"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_campaigns_tenant_status", "tenant_id", "status"),)


class CampaignPost(TimestampMixin, Base):
    __tablename__ = "campaign_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(JSONB, default=list)
    hashtags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.DRAFT)
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analytics: Mapped[dict] = mapped_column(JSONB, default=dict)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="posts")

    __table_args__ = (Index("ix_posts_campaign_platform", "campaign_id", "platform"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_audit_tenant_action", "tenant_id", "action"),
        Index("ix_audit_created", "created_at"),
    )


class Experiment(TimestampMixin, Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    variants: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[ExperimentStatus] = mapped_column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT)
    winner_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="experiments")


class KillSwitchEventLog(Base):
    """Persisted kill switch event history."""

    __tablename__ = "kill_switch_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    affected_platforms: Mapped[list[str]] = mapped_column(JSONB, default=list)
    affected_campaigns: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class APIKey(TimestampMixin, Base):
    """Hashed API keys for non-JWT authentication."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_api_keys_tenant", "tenant_id"),
    )


class SpendRecord(TimestampMixin, Base):
    """Tracks every spend event for financial audit trail."""

    __tablename__ = "spend_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(50), default="system")
    was_anomalous: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_spend_tenant_date", "tenant_id", "created_at"),
        Index("ix_spend_campaign", "campaign_id"),
    )

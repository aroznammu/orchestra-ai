"""Campaign CRUD endpoints with strict tenant isolation."""

import uuid
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from orchestra.api.deps import CurrentUser, DbSession
from orchestra.db.models import Campaign, CampaignPost, CampaignStatus, PlatformType

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
logger = structlog.get_logger("api.campaigns")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    platforms: list[str] = Field(default_factory=list)
    budget: float = 0.0
    start_date: datetime | None = None
    end_date: datetime | None = None
    target_audience: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    platforms: list[str] | None = None
    budget: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    target_audience: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None


class PostResponse(BaseModel):
    id: str
    platform: str
    content: str
    status: str
    scheduled_at: str | None = None
    published_at: str | None = None
    analytics: dict[str, Any] = Field(default_factory=dict)


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    platforms: list[str]
    budget: float
    spent: float
    start_date: str | None = None
    end_date: str | None = None
    target_audience: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class CampaignDetailResponse(CampaignResponse):
    posts: list[PostResponse] = Field(default_factory=list)


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _campaign_to_response(c: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=str(c.id),
        name=c.name,
        description=c.description,
        status=c.status.value,
        platforms=c.platforms or [],
        budget=c.budget,
        spent=c.spent,
        start_date=c.start_date.isoformat() if c.start_date else None,
        end_date=c.end_date.isoformat() if c.end_date else None,
        target_audience=c.target_audience or {},
        settings=c.settings or {},
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


async def _get_tenant_campaign(
    db, campaign_id: str, tenant_id: str, *, load_posts: bool = False,
) -> Campaign:
    """Fetch a campaign that belongs to the given tenant. Raises 404 if not found."""
    try:
        cid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    query = select(Campaign).where(Campaign.id == cid, Campaign.tenant_id == uuid.UUID(tenant_id))
    if load_posts:
        query = query.options(selectinload(Campaign.posts))
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignResponse:
    campaign = Campaign(
        tenant_id=uuid.UUID(current_user.tenant_id),
        name=body.name,
        description=body.description,
        platforms=body.platforms,
        budget=body.budget,
        start_date=body.start_date,
        end_date=body.end_date,
        target_audience=body.target_audience,
        settings=body.settings,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    logger.info("campaign_created", campaign_id=str(campaign.id), tenant_id=current_user.tenant_id)
    return _campaign_to_response(campaign)


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    current_user: CurrentUser,
    db: DbSession,
    status_filter: CampaignStatus | None = None,
) -> CampaignListResponse:
    query = select(Campaign).where(Campaign.tenant_id == uuid.UUID(current_user.tenant_id))
    if status_filter:
        query = query.where(Campaign.status == status_filter)
    query = query.order_by(Campaign.created_at.desc())

    result = await db.execute(query)
    campaigns = result.scalars().all()
    return CampaignListResponse(
        campaigns=[_campaign_to_response(c) for c in campaigns],
        total=len(campaigns),
    )


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignDetailResponse:
    campaign = await _get_tenant_campaign(db, campaign_id, current_user.tenant_id, load_posts=True)

    posts = [
        PostResponse(
            id=str(p.id),
            platform=p.platform.value,
            content=p.content,
            status=p.status.value,
            scheduled_at=p.scheduled_at.isoformat() if p.scheduled_at else None,
            published_at=p.published_at.isoformat() if p.published_at else None,
            analytics=p.analytics or {},
        )
        for p in (campaign.posts or [])
    ]

    base = _campaign_to_response(campaign)
    return CampaignDetailResponse(**base.model_dump(), posts=posts)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    body: CampaignUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignResponse:
    campaign = await _get_tenant_campaign(db, campaign_id, current_user.tenant_id)

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(campaign, field, value)

    await db.flush()
    await db.refresh(campaign)
    logger.info("campaign_updated", campaign_id=campaign_id, fields=list(updates.keys()))
    return _campaign_to_response(campaign)


@router.post("/{campaign_id}/launch", response_model=CampaignResponse)
async def launch_campaign(
    campaign_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignResponse:
    campaign = await _get_tenant_campaign(db, campaign_id, current_user.tenant_id)

    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot launch campaign in '{campaign.status.value}' status",
        )

    campaign.status = CampaignStatus.ACTIVE
    await db.flush()
    await db.refresh(campaign)
    logger.info("campaign_launched", campaign_id=campaign_id, tenant_id=current_user.tenant_id)
    return _campaign_to_response(campaign)


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> CampaignResponse:
    campaign = await _get_tenant_campaign(db, campaign_id, current_user.tenant_id)

    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot pause campaign in '{campaign.status.value}' status",
        )

    campaign.status = CampaignStatus.PAUSED
    await db.flush()
    await db.refresh(campaign)
    logger.info("campaign_paused", campaign_id=campaign_id, tenant_id=current_user.tenant_id)
    return _campaign_to_response(campaign)

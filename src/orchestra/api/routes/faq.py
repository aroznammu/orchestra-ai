"""API routes for FAQ management."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from orchestra.api.deps import AdminUser, CurrentUser, DbSession
from orchestra.db.models import FAQEntry

logger = structlog.get_logger("api.faq")

router = APIRouter(prefix="/faq", tags=["faq"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class FAQOut(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    sort_order: int
    is_published: bool
    created_at: str
    updated_at: str


class FAQGroupOut(BaseModel):
    category: str
    entries: list[FAQOut]


class CreateFAQRequest(BaseModel):
    category: str = Field(default="General", max_length=100)
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=5)
    sort_order: int = 0
    is_published: bool = True


class UpdateFAQRequest(BaseModel):
    category: str | None = None
    question: str | None = None
    answer: str | None = None
    sort_order: int | None = None
    is_published: bool | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _faq_to_out(faq: FAQEntry) -> FAQOut:
    return FAQOut(
        id=str(faq.id),
        category=faq.category,
        question=faq.question,
        answer=faq.answer,
        sort_order=faq.sort_order,
        is_published=faq.is_published,
        created_at=faq.created_at.isoformat(),
        updated_at=faq.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[FAQGroupOut])
async def list_faqs(user: CurrentUser, db: DbSession) -> list[FAQGroupOut]:
    """List all published FAQs grouped by category.

    Returns global FAQs (tenant_id IS NULL) and tenant-specific FAQs.
    """
    tid = uuid.UUID(user.tenant_id)
    result = await db.execute(
        select(FAQEntry)
        .where(
            FAQEntry.is_published.is_(True),
            (FAQEntry.tenant_id == tid) | (FAQEntry.tenant_id.is_(None)),
        )
        .order_by(FAQEntry.category, FAQEntry.sort_order, FAQEntry.created_at)
    )
    faqs = result.scalars().all()

    groups: dict[str, list[FAQOut]] = {}
    for faq in faqs:
        groups.setdefault(faq.category, []).append(_faq_to_out(faq))

    return [FAQGroupOut(category=cat, entries=entries) for cat, entries in groups.items()]


@router.post("", response_model=FAQOut, status_code=status.HTTP_201_CREATED)
async def create_faq(
    request: CreateFAQRequest,
    user: AdminUser,
    db: DbSession,
) -> FAQOut:
    """Create a new FAQ entry (admin/owner only)."""
    faq = FAQEntry(
        tenant_id=uuid.UUID(user.tenant_id),
        category=request.category,
        question=request.question,
        answer=request.answer,
        sort_order=request.sort_order,
        is_published=request.is_published,
    )
    db.add(faq)
    await db.flush()
    await db.refresh(faq)

    logger.info("faq_created", faq_id=str(faq.id), tenant_id=user.tenant_id)
    return _faq_to_out(faq)


@router.patch("/{faq_id}", response_model=FAQOut)
async def update_faq(
    faq_id: str,
    request: UpdateFAQRequest,
    user: AdminUser,
    db: DbSession,
) -> FAQOut:
    """Update an existing FAQ entry (admin/owner only)."""
    result = await db.execute(
        select(FAQEntry).where(
            FAQEntry.id == uuid.UUID(faq_id),
            (FAQEntry.tenant_id == uuid.UUID(user.tenant_id)) | (FAQEntry.tenant_id.is_(None)),
        )
    )
    faq = result.scalar_one_or_none()
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found")

    if faq.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global FAQ entries cannot be modified by tenants.",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)

    logger.info("faq_updated", faq_id=faq_id, tenant_id=user.tenant_id)
    return _faq_to_out(faq)


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: str,
    user: AdminUser,
    db: DbSession,
) -> None:
    """Delete a FAQ entry (admin/owner only). Global FAQs cannot be deleted."""
    result = await db.execute(
        select(FAQEntry).where(
            FAQEntry.id == uuid.UUID(faq_id),
            FAQEntry.tenant_id == uuid.UUID(user.tenant_id),
        )
    )
    faq = result.scalar_one_or_none()
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found")

    await db.delete(faq)
    logger.info("faq_deleted", faq_id=faq_id, tenant_id=user.tenant_id)

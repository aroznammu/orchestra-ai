"""A/B experiment CRUD endpoints scoped to campaigns."""

import uuid

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from orchestra.api.deps import CurrentUser, DbSession, PaidUser
from orchestra.db.models import Campaign, Experiment, ExperimentStatus

logger = structlog.get_logger("api.experiments")

router = APIRouter(prefix="/campaigns/{campaign_id}/experiments", tags=["experiments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateExperimentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hypothesis: str | None = None
    variants: dict = Field(default_factory=dict)


class UpdateExperimentRequest(BaseModel):
    name: str | None = None
    hypothesis: str | None = None
    variants: dict | None = None
    status: ExperimentStatus | None = None
    winner_variant: str | None = None
    results: dict | None = None
    confidence_level: float | None = None


class ExperimentOut(BaseModel):
    id: str
    campaign_id: str
    name: str
    hypothesis: str | None
    variants: dict
    status: str
    winner_variant: str | None
    results: dict
    confidence_level: float | None
    created_at: str
    updated_at: str


def _to_out(exp: Experiment) -> ExperimentOut:
    return ExperimentOut(
        id=str(exp.id),
        campaign_id=str(exp.campaign_id),
        name=exp.name,
        hypothesis=exp.hypothesis,
        variants=exp.variants,
        status=exp.status.value,
        winner_variant=exp.winner_variant,
        results=exp.results,
        confidence_level=exp.confidence_level,
        created_at=exp.created_at.isoformat(),
        updated_at=exp.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_campaign(db: DbSession, campaign_id: str, tenant_id: str) -> Campaign:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == uuid.UUID(campaign_id),
            Campaign.tenant_id == uuid.UUID(tenant_id),
        )
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


async def _get_experiment(db: DbSession, campaign_id: str, experiment_id: str, tenant_id: str) -> Experiment:
    await _get_campaign(db, campaign_id, tenant_id)
    result = await db.execute(
        select(Experiment).where(
            Experiment.id == uuid.UUID(experiment_id),
            Experiment.campaign_id == uuid.UUID(campaign_id),
        )
    )
    experiment = result.scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    campaign_id: str,
    request: CreateExperimentRequest,
    user: PaidUser,
    db: DbSession,
) -> ExperimentOut:
    """Create an A/B experiment for a campaign."""
    await _get_campaign(db, campaign_id, user.tenant_id)

    experiment = Experiment(
        campaign_id=uuid.UUID(campaign_id),
        name=request.name,
        hypothesis=request.hypothesis,
        variants=request.variants,
        status=ExperimentStatus.DRAFT,
    )
    db.add(experiment)
    await db.flush()
    await db.refresh(experiment)

    logger.info("experiment_created", experiment_id=str(experiment.id), campaign_id=campaign_id)
    return _to_out(experiment)


@router.get("/", response_model=list[ExperimentOut])
async def list_experiments(
    campaign_id: str,
    user: CurrentUser,
    db: DbSession,
) -> list[ExperimentOut]:
    """List all experiments for a campaign."""
    await _get_campaign(db, campaign_id, user.tenant_id)

    result = await db.execute(
        select(Experiment)
        .where(Experiment.campaign_id == uuid.UUID(campaign_id))
        .order_by(Experiment.created_at.desc())
    )
    return [_to_out(exp) for exp in result.scalars().all()]


@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(
    campaign_id: str,
    experiment_id: str,
    user: CurrentUser,
    db: DbSession,
) -> ExperimentOut:
    """Get a single experiment."""
    experiment = await _get_experiment(db, campaign_id, experiment_id, user.tenant_id)
    return _to_out(experiment)


@router.patch("/{experiment_id}", response_model=ExperimentOut)
async def update_experiment(
    campaign_id: str,
    experiment_id: str,
    request: UpdateExperimentRequest,
    user: PaidUser,
    db: DbSession,
) -> ExperimentOut:
    """Update an experiment's fields."""
    experiment = await _get_experiment(db, campaign_id, experiment_id, user.tenant_id)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(experiment, field, value)

    await db.flush()
    await db.refresh(experiment)

    logger.info("experiment_updated", experiment_id=experiment_id, fields=list(update_data.keys()))
    return _to_out(experiment)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    campaign_id: str,
    experiment_id: str,
    user: PaidUser,
    db: DbSession,
) -> None:
    """Delete a draft experiment."""
    experiment = await _get_experiment(db, campaign_id, experiment_id, user.tenant_id)

    if experiment.status != ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft experiments can be deleted.",
        )

    await db.delete(experiment)
    await db.flush()

    logger.info("experiment_deleted", experiment_id=experiment_id, campaign_id=campaign_id)

"""Data flywheel pipeline.

Campaign execution -> engagement data -> normalization -> embedding -> model update.

This is the core feedback loop that makes OrchestraAI's intelligence compound:
  more campaigns -> more data -> better embeddings -> better recommendations -> better campaigns
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from orchestra.moat.performance_embed import index_performance
from orchestra.moat.signals import normalize_engagement
from orchestra.rag.indexer import index_campaign, update_campaign_metrics

logger = structlog.get_logger("moat.flywheel")


class FlywheelPipeline:
    """Orchestrates the data flywheel: execute -> measure -> learn -> improve."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._iteration_count = 0

    async def on_campaign_created(
        self,
        campaign_id: str,
        title: str,
        content: str,
        platform: str,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Step 1: Campaign enters the flywheel. Index for future retrieval."""
        await index_campaign(
            campaign_id=campaign_id,
            tenant_id=self.tenant_id,
            title=title,
            content=content,
            platform=platform,
            category=category,
            metadata=metadata,
        )

        logger.info("flywheel_campaign_created", campaign_id=campaign_id)
        return {"stage": "created", "campaign_id": campaign_id}

    async def on_engagement_received(
        self,
        campaign_id: str,
        platform: str,
        raw_metrics: dict[str, int],
        content_text: str = "",
    ) -> dict[str, Any]:
        """Step 2: Engagement data arrives. Normalize and re-embed."""
        # Normalize raw signals
        score = normalize_engagement(platform, raw_metrics, post_id=campaign_id)

        # Update campaign index with fresh metrics
        await update_campaign_metrics(
            campaign_id=campaign_id,
            tenant_id=self.tenant_id,
            metrics={
                "engagement_rate": score.normalized_score / 100.0,
                "weighted_score": score.weighted_score,
                "raw_signals": score.raw_signals,
                "last_updated": datetime.now(UTC).isoformat(),
            },
        )

        # Re-index with performance weighting
        if content_text:
            await index_performance(
                campaign_id=campaign_id,
                tenant_id=self.tenant_id,
                content_text=content_text,
                platform=platform,
                performance_metrics={
                    "engagement_rate": score.normalized_score / 100.0,
                    "weighted_score": score.weighted_score,
                },
            )

        self._iteration_count += 1

        logger.info(
            "flywheel_engagement_processed",
            campaign_id=campaign_id,
            normalized_score=score.normalized_score,
            iteration=self._iteration_count,
        )

        return {
            "stage": "engagement_processed",
            "campaign_id": campaign_id,
            "normalized_score": score.normalized_score,
            "weighted_score": score.weighted_score,
            "iteration": self._iteration_count,
        }

    async def on_optimization_applied(
        self,
        campaign_id: str,
        optimization_type: str,
        change_description: str,
        expected_improvement: float,
    ) -> dict[str, Any]:
        """Step 3: An optimization was applied. Log for learning."""
        from orchestra.rag.indexer import index_decision

        decision_id = str(uuid4())
        await index_decision(
            decision_id=decision_id,
            tenant_id=self.tenant_id,
            context=f"Campaign {campaign_id}: {optimization_type}",
            decision=change_description,
            outcome="pending",
            confidence=expected_improvement,
            agent="optimizer",
        )

        logger.info(
            "flywheel_optimization_logged",
            campaign_id=campaign_id,
            optimization_type=optimization_type,
        )

        return {
            "stage": "optimization_logged",
            "decision_id": decision_id,
            "campaign_id": campaign_id,
        }

    def get_flywheel_stats(self) -> dict[str, Any]:
        """Get current flywheel metrics for this tenant."""
        return {
            "tenant_id": self.tenant_id,
            "iterations": self._iteration_count,
            "status": "active" if self._iteration_count > 0 else "cold_start",
            "maturity": _compute_maturity(self._iteration_count),
        }


def _compute_maturity(iterations: int) -> str:
    if iterations == 0:
        return "cold_start"
    elif iterations < 10:
        return "warming"
    elif iterations < 50:
        return "learning"
    elif iterations < 200:
        return "maturing"
    else:
        return "optimized"

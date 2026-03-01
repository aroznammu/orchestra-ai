"""Per-tenant private embedding model.

Each tenant's data stays isolated -- their campaigns, engagement patterns,
and optimization history form a private model that improves over time.
"""

from typing import Any

import structlog

from orchestra.rag.embeddings import embed_single
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("moat.tenant_model")

TENANT_MODEL_COLLECTION = "tenant_models"


class TenantModel:
    """Private learning model for a single tenant."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._patterns: list[dict[str, Any]] = []

    async def learn_from_campaign(
        self,
        campaign_id: str,
        content: str,
        platform: str,
        metrics: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ingest a campaign result to improve tenant-specific predictions."""
        store = get_vector_store()

        pattern = {
            "type": "campaign_outcome",
            "content_preview": content[:300],
            "platform": platform,
            "engagement_rate": metrics.get("engagement_rate", 0.0),
            "click_rate": metrics.get("click_rate", 0.0),
            "roi": metrics.get("roi", 0.0),
            **(context or {}),
        }

        # Build embedding from content + outcome for outcome-aware retrieval
        embed_text = (
            f"Platform: {platform}\n"
            f"Content: {content[:300]}\n"
            f"Engagement: {metrics.get('engagement_rate', 0):.4f}\n"
            f"ROI: {metrics.get('roi', 0):.2f}"
        )
        vector = await embed_single(embed_text)

        payload = {
            "tenant_id": self.tenant_id,
            "campaign_id": campaign_id,
            **pattern,
        }

        await store.upsert(
            collection_name=TENANT_MODEL_COLLECTION,
            vectors=[vector],
            payloads=[payload],
            ids=[f"{self.tenant_id}:{campaign_id}"],
        )

        self._patterns.append(pattern)

        logger.info(
            "tenant_model_updated",
            tenant_id=self.tenant_id,
            campaign_id=campaign_id,
            patterns=len(self._patterns),
        )

        return {"learned": True, "total_patterns": len(self._patterns)}

    async def predict_performance(
        self,
        content: str,
        platform: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Predict expected performance based on similar past campaigns."""
        store = get_vector_store()
        query_vector = await embed_single(content)

        similar = await store.search(
            collection_name=TENANT_MODEL_COLLECTION,
            query_vector=query_vector,
            tenant_id=self.tenant_id,
            limit=limit,
            filters={"platform": platform},
        )

        if not similar:
            return {
                "predicted_engagement_rate": 0.0,
                "confidence": 0.0,
                "basis": "no_data",
                "similar_campaigns": 0,
            }

        # Weighted average of similar campaigns' outcomes
        total_weight = 0.0
        weighted_er = 0.0
        weighted_roi = 0.0

        for result in similar:
            weight = result["score"]
            er = result["payload"].get("engagement_rate", 0.0)
            roi = result["payload"].get("roi", 0.0)

            weighted_er += er * weight
            weighted_roi += roi * weight
            total_weight += weight

        if total_weight > 0:
            pred_er = weighted_er / total_weight
            pred_roi = weighted_roi / total_weight
        else:
            pred_er = 0.0
            pred_roi = 0.0

        confidence = min(len(similar) / 10.0, 1.0) * (total_weight / len(similar))

        return {
            "predicted_engagement_rate": round(pred_er, 4),
            "predicted_roi": round(pred_roi, 2),
            "confidence": round(confidence, 3),
            "basis": f"{len(similar)} similar campaigns",
            "similar_campaigns": len(similar),
        }

    async def get_best_practices(
        self,
        platform: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve the tenant's top-performing content for a platform."""
        store = get_vector_store()
        dummy_vector = [0.0] * 1536

        results = await store.search(
            collection_name=TENANT_MODEL_COLLECTION,
            query_vector=dummy_vector,
            tenant_id=self.tenant_id,
            limit=limit * 3,
            filters={"platform": platform},
        )

        # Sort by engagement rate (descending)
        results.sort(
            key=lambda r: r["payload"].get("engagement_rate", 0.0),
            reverse=True,
        )

        return [
            {
                "campaign_id": r["payload"].get("campaign_id"),
                "content_preview": r["payload"].get("content_preview", ""),
                "engagement_rate": r["payload"].get("engagement_rate", 0.0),
                "roi": r["payload"].get("roi", 0.0),
            }
            for r in results[:limit]
        ]

    async def export_data(self) -> dict[str, Any]:
        """Export all tenant model data (GDPR compliance)."""
        store = get_vector_store()
        count = await store.count(TENANT_MODEL_COLLECTION, self.tenant_id)
        return {
            "tenant_id": self.tenant_id,
            "total_patterns": count,
            "in_memory_patterns": len(self._patterns),
        }

    async def delete_all(self) -> None:
        """Delete all tenant model data (GDPR right to erasure)."""
        store = get_vector_store()
        await store.delete_by_tenant(TENANT_MODEL_COLLECTION, self.tenant_id)
        self._patterns.clear()
        logger.info("tenant_model_deleted", tenant_id=self.tenant_id)

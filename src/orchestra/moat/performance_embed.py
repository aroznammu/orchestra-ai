"""Performance embedding engine.

Encodes campaigns as vectors that incorporate performance outcomes,
enabling retrieval like "find content similar to X that performed well."
"""

from typing import Any

import structlog

from orchestra.rag.embeddings import embed_single
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("moat.performance_embed")

PERFORMANCE_COLLECTION = "performance_embeddings"


class PerformanceVector:
    """Combines content embedding with performance weighting."""

    @staticmethod
    async def encode(
        content_text: str,
        performance_metrics: dict[str, float],
        platform: str,
        tenant_id: str,
    ) -> list[float]:
        """Create a performance-weighted embedding.

        The base content embedding is adjusted by performance signals
        so that high-performing content clusters together.
        """
        base_vector = await embed_single(content_text)

        # Compute performance modifier (scales embedding magnitude)
        er = performance_metrics.get("engagement_rate", 0.0)
        ctr = performance_metrics.get("click_rate", 0.0)
        roi = performance_metrics.get("roi", 0.0)

        performance_score = (
            er * 0.4 +
            ctr * 0.3 +
            max(min(roi / 10.0, 1.0), 0.0) * 0.3
        )

        # Scale vector magnitude by performance (1.0 = neutral, up to 1.5)
        scale = 1.0 + min(performance_score, 0.5)

        return [v * scale for v in base_vector]


async def index_performance(
    campaign_id: str,
    tenant_id: str,
    content_text: str,
    platform: str,
    performance_metrics: dict[str, float],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Index a campaign with performance-weighted embedding."""
    store = get_vector_store()

    vector = await PerformanceVector.encode(
        content_text=content_text,
        performance_metrics=performance_metrics,
        platform=platform,
        tenant_id=tenant_id,
    )

    payload = {
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
        "platform": platform,
        "content_preview": content_text[:500],
        "engagement_rate": performance_metrics.get("engagement_rate", 0.0),
        "click_rate": performance_metrics.get("click_rate", 0.0),
        "roi": performance_metrics.get("roi", 0.0),
        "impressions": performance_metrics.get("impressions", 0),
        **(metadata or {}),
    }

    await store.upsert(
        collection_name=PERFORMANCE_COLLECTION,
        vectors=[vector],
        payloads=[payload],
        ids=[campaign_id],
    )

    logger.info(
        "performance_indexed",
        campaign_id=campaign_id,
        engagement_rate=payload["engagement_rate"],
    )
    return campaign_id


async def find_high_performers(
    query_text: str,
    tenant_id: str,
    platform: str | None = None,
    min_engagement_rate: float = 0.02,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find high-performing campaigns similar to a query."""
    store = get_vector_store()
    query_vector = await embed_single(query_text)

    filters: dict[str, Any] = {}
    if platform:
        filters["platform"] = platform

    results = await store.search(
        collection_name=PERFORMANCE_COLLECTION,
        query_vector=query_vector,
        tenant_id=tenant_id,
        limit=limit * 2,
        filters=filters,
    )

    # Filter by minimum engagement
    filtered = [
        r for r in results
        if r["payload"].get("engagement_rate", 0.0) >= min_engagement_rate
    ]

    return filtered[:limit]


async def cluster_campaigns(
    tenant_id: str,
    platform: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Cluster campaigns by performance similarity.

    Returns groupings of similar high/medium/low performers.
    """
    store = get_vector_store()

    # Retrieve all campaign embeddings for tenant
    dummy_vector = [0.0] * 1536
    all_campaigns = await store.search(
        collection_name=PERFORMANCE_COLLECTION,
        query_vector=dummy_vector,
        tenant_id=tenant_id,
        limit=limit,
        filters={"platform": platform} if platform else {},
    )

    # Simple tier-based clustering
    high = [c for c in all_campaigns if c["payload"].get("engagement_rate", 0) >= 0.05]
    medium = [
        c for c in all_campaigns
        if 0.02 <= c["payload"].get("engagement_rate", 0) < 0.05
    ]
    low = [c for c in all_campaigns if c["payload"].get("engagement_rate", 0) < 0.02]

    return {
        "tenant_id": tenant_id,
        "total_campaigns": len(all_campaigns),
        "clusters": {
            "high_performers": {
                "count": len(high),
                "avg_engagement": _avg(high, "engagement_rate"),
                "campaigns": [c["payload"].get("campaign_id") for c in high],
            },
            "medium_performers": {
                "count": len(medium),
                "avg_engagement": _avg(medium, "engagement_rate"),
                "campaigns": [c["payload"].get("campaign_id") for c in medium],
            },
            "low_performers": {
                "count": len(low),
                "avg_engagement": _avg(low, "engagement_rate"),
                "campaigns": [c["payload"].get("campaign_id") for c in low],
            },
        },
    }


def _avg(items: list[dict[str, Any]], key: str) -> float:
    if not items:
        return 0.0
    values = [i["payload"].get(key, 0.0) for i in items]
    return round(sum(values) / len(values), 4)

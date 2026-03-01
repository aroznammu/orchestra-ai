"""Semantic retriever.

"Find campaigns similar to X that performed well on Instagram in the fitness vertical."

Supports filtered semantic search with re-ranking by engagement score.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.rag.embeddings import embed_single
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("rag.retriever")

CAMPAIGNS_COLLECTION = "campaigns"
CONTENT_COLLECTION = "content_templates"
DECISIONS_COLLECTION = "decisions"


class RetrievalQuery(BaseModel):
    query: str
    tenant_id: str
    collection: str = CAMPAIGNS_COLLECTION
    platform: str | None = None
    category: str | None = None
    min_engagement_rate: float | None = None
    limit: int = 10


class RetrievalResult(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    query: str
    total_found: int = 0


async def retrieve(query: RetrievalQuery) -> RetrievalResult:
    """Semantic search + optional re-ranking by performance."""
    store = get_vector_store()

    query_vector = await embed_single(query.query)

    filters: dict[str, Any] = {}
    if query.platform:
        filters["platform"] = query.platform
    if query.category:
        filters["category"] = query.category

    raw_results = await store.search(
        collection_name=query.collection,
        query_vector=query_vector,
        tenant_id=query.tenant_id,
        limit=query.limit * 2,  # over-fetch for re-ranking
        filters=filters,
    )

    # Re-rank by engagement if requested
    if query.min_engagement_rate is not None:
        raw_results = [
            r for r in raw_results
            if r["payload"].get("engagement_rate", 0.0) >= query.min_engagement_rate
        ]

    # Sort by composite score: semantic similarity * engagement boost
    ranked = _rerank(raw_results)

    return RetrievalResult(
        items=ranked[: query.limit],
        query=query.query,
        total_found=len(ranked),
    )


async def find_similar_campaigns(
    campaign_text: str,
    tenant_id: str,
    platform: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find campaigns similar to the given text."""
    query = RetrievalQuery(
        query=campaign_text,
        tenant_id=tenant_id,
        collection=CAMPAIGNS_COLLECTION,
        platform=platform,
        limit=limit,
    )
    result = await retrieve(query)
    return result.items


async def find_content_templates(
    topic: str,
    tenant_id: str,
    platform: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find high-performing content templates for a topic."""
    query = RetrievalQuery(
        query=topic,
        tenant_id=tenant_id,
        collection=CONTENT_COLLECTION,
        platform=platform,
        min_engagement_rate=0.02,
        limit=limit,
    )
    result = await retrieve(query)
    return result.items


async def find_past_decisions(
    context: str,
    tenant_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve past orchestrator decisions for context."""
    query = RetrievalQuery(
        query=context,
        tenant_id=tenant_id,
        collection=DECISIONS_COLLECTION,
        limit=limit,
    )
    result = await retrieve(query)
    return result.items


def _rerank(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-rank by composite score: semantic_similarity * performance_boost."""
    for r in results:
        semantic_score = r.get("score", 0.0)
        engagement = r["payload"].get("engagement_rate", 0.0)
        performance_boost = 1.0 + min(engagement * 10, 1.0)  # cap at 2x
        r["composite_score"] = semantic_score * performance_boost

    results.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
    return results

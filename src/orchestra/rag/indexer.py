"""Auto-indexer pipeline.

Automatically indexes every campaign and its outcomes into the vector store.
Runs on campaign creation, post publishing, and periodic analytics refresh.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from orchestra.rag.embeddings import embed_single, prepare_campaign_text
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("rag.indexer")

CAMPAIGNS_COLLECTION = "campaigns"
CONTENT_COLLECTION = "content_templates"
DECISIONS_COLLECTION = "decisions"


async def index_campaign(
    campaign_id: str,
    tenant_id: str,
    title: str,
    content: str,
    platform: str,
    category: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Index a campaign into the vector store."""
    store = get_vector_store()

    text = prepare_campaign_text(title, content, platform, metadata)
    vector = await embed_single(text)

    payload = {
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
        "title": title,
        "content_preview": content[:500],
        "platform": platform,
        "category": category or "general",
        "indexed_at": datetime.now(UTC).isoformat(),
        "engagement_rate": 0.0,
        "impressions": 0,
        "clicks": 0,
        "spend": 0.0,
        **(metadata or {}),
    }

    await store.upsert(
        collection_name=CAMPAIGNS_COLLECTION,
        vectors=[vector],
        payloads=[payload],
        ids=[campaign_id],
    )

    logger.info("campaign_indexed", campaign_id=campaign_id, platform=platform)
    return campaign_id


async def update_campaign_metrics(
    campaign_id: str,
    tenant_id: str,
    metrics: dict[str, Any],
) -> None:
    """Update an already-indexed campaign with fresh performance metrics.

    Re-embeds with metrics appended so performance-weighted retrieval works.
    """
    store = get_vector_store()

    existing = await store.search(
        collection_name=CAMPAIGNS_COLLECTION,
        query_vector=[0.0] * 1536,  # dummy; we filter by ID below
        tenant_id=tenant_id,
        limit=1,
        filters={"campaign_id": campaign_id},
    )

    if not existing:
        logger.warning("campaign_not_found_for_update", campaign_id=campaign_id)
        return

    payload = existing[0]["payload"]
    payload.update(metrics)
    payload["updated_at"] = datetime.now(UTC).isoformat()

    text = prepare_campaign_text(
        title=payload.get("title", ""),
        content=payload.get("content_preview", ""),
        platform=payload.get("platform", ""),
        metadata=metrics,
    )
    vector = await embed_single(text)

    await store.upsert(
        collection_name=CAMPAIGNS_COLLECTION,
        vectors=[vector],
        payloads=[payload],
        ids=[campaign_id],
    )

    logger.info("campaign_metrics_updated", campaign_id=campaign_id)


async def index_content_template(
    template_id: str,
    tenant_id: str,
    content: str,
    platform: str,
    engagement_rate: float = 0.0,
    category: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Index a high-performing content template for future retrieval."""
    store = get_vector_store()
    vector = await embed_single(content)

    payload = {
        "tenant_id": tenant_id,
        "template_id": template_id,
        "content": content,
        "platform": platform,
        "engagement_rate": engagement_rate,
        "category": category or "general",
        "tags": tags or [],
        "indexed_at": datetime.now(UTC).isoformat(),
    }

    await store.upsert(
        collection_name=CONTENT_COLLECTION,
        vectors=[vector],
        payloads=[payload],
        ids=[template_id],
    )

    logger.info("content_template_indexed", template_id=template_id)
    return template_id


async def index_decision(
    decision_id: str,
    tenant_id: str,
    context: str,
    decision: str,
    outcome: str,
    confidence: float = 0.0,
    agent: str = "orchestrator",
) -> str:
    """Index an orchestrator decision for long-term memory."""
    store = get_vector_store()

    text = f"Context: {context}\nDecision: {decision}\nOutcome: {outcome}"
    vector = await embed_single(text)

    payload = {
        "tenant_id": tenant_id,
        "decision_id": decision_id,
        "context": context,
        "decision": decision,
        "outcome": outcome,
        "confidence": confidence,
        "agent": agent,
        "indexed_at": datetime.now(UTC).isoformat(),
    }

    await store.upsert(
        collection_name=DECISIONS_COLLECTION,
        vectors=[vector],
        payloads=[payload],
        ids=[decision_id],
    )

    logger.info("decision_indexed", decision_id=decision_id, agent=agent)
    return decision_id


async def delete_tenant_data(tenant_id: str) -> None:
    """Delete all indexed data for a tenant (GDPR/CCPA compliance)."""
    store = get_vector_store()
    for collection in [CAMPAIGNS_COLLECTION, CONTENT_COLLECTION, DECISIONS_COLLECTION]:
        await store.delete_by_tenant(collection, tenant_id)

    logger.info("tenant_data_deleted", tenant_id=tenant_id)

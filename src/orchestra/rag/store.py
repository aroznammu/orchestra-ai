"""Qdrant vector store wrapper.

Manages collections, upserts, and queries against the Qdrant instance.
Supports multi-tenant isolation via payload filtering.
"""

from typing import Any
from uuid import uuid4

import structlog
from qdrant_client import AsyncQdrantClient, models

from orchestra.config import get_settings

logger = structlog.get_logger("rag.store")

EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small default


class VectorStore:
    """Async wrapper around Qdrant for OrchestraAI."""

    def __init__(self, client: AsyncQdrantClient | None = None) -> None:
        self._client = client
        self._initialized_collections: set[str] = set()

    async def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            settings = get_settings()
            self._client = AsyncQdrantClient(url=settings.qdrant_url)
        return self._client

    async def ensure_collection(
        self,
        collection_name: str,
        dimension: int = EMBEDDING_DIM,
    ) -> None:
        """Create collection if it doesn't exist."""
        if collection_name in self._initialized_collections:
            return

        client = await self._get_client()
        collections = await client.get_collections()
        existing = {c.name for c in collections.collections}

        if collection_name not in existing:
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            # Tenant isolation index
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="tenant_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            logger.info("collection_created", name=collection_name, dim=dimension)

        self._initialized_collections.add(collection_name)

    async def upsert(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> int:
        """Insert or update vectors with payloads. Returns count upserted."""
        await self.ensure_collection(collection_name)
        client = await self._get_client()

        if ids is None:
            ids = [str(uuid4()) for _ in vectors]

        points = [
            models.PointStruct(id=uid, vector=vec, payload=payload)
            for uid, vec, payload in zip(ids, vectors, payloads)
        ]

        await client.upsert(collection_name=collection_name, points=points)
        logger.info("vectors_upserted", collection=collection_name, count=len(points))
        return len(points)

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        tenant_id: str,
        limit: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors, scoped to a tenant."""
        await self.ensure_collection(collection_name)
        client = await self._get_client()

        must_conditions = [
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id),
            )
        ]

        if filters:
            for key, value in filters.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )

        results = await client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=models.Filter(must=must_conditions),
            limit=limit,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload or {},
            }
            for hit in results
        ]

    async def delete(
        self,
        collection_name: str,
        ids: list[str],
    ) -> None:
        """Delete vectors by ID."""
        client = await self._get_client()
        await client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=ids),
        )
        logger.info("vectors_deleted", collection=collection_name, count=len(ids))

    async def delete_by_tenant(
        self,
        collection_name: str,
        tenant_id: str,
    ) -> None:
        """Delete all vectors for a tenant (GDPR compliance)."""
        client = await self._get_client()
        await client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="tenant_id",
                            match=models.MatchValue(value=tenant_id),
                        )
                    ]
                )
            ),
        )
        logger.info("tenant_vectors_deleted", collection=collection_name, tenant_id=tenant_id)

    async def count(self, collection_name: str, tenant_id: str | None = None) -> int:
        """Count vectors in a collection, optionally filtered by tenant."""
        client = await self._get_client()
        if tenant_id:
            result = await client.count(
                collection_name=collection_name,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="tenant_id",
                            match=models.MatchValue(value=tenant_id),
                        )
                    ]
                ),
            )
        else:
            result = await client.count(collection_name=collection_name)
        return result.count

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store

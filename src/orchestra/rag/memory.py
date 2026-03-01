"""Long-term memory layer.

3-layer architecture:
  1. Redis -- short-term (conversation context, recent actions)
  2. PostgreSQL -- structured (campaigns, users, settings)
  3. Qdrant -- vector (semantic search over decisions, content, performance)

This module manages the vector + Redis layers for agent memory.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from orchestra.rag.embeddings import embed_single
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("rag.memory")

MEMORY_COLLECTION = "agent_memory"


class AgentMemory:
    """Per-tenant long-term memory for agents."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._short_term: list[dict[str, Any]] = []
        self._max_short_term = 50

    async def remember(
        self,
        content: str,
        memory_type: str = "observation",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a memory (both short-term cache and long-term vector)."""
        memory_id = str(uuid4())
        entry = {
            "id": memory_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "timestamp": datetime.now(UTC).isoformat(),
            **(metadata or {}),
        }

        # Short-term (in-memory ring buffer)
        self._short_term.append(entry)
        if len(self._short_term) > self._max_short_term:
            self._short_term = self._short_term[-self._max_short_term:]

        # Long-term (vector store) for important memories
        if importance >= 0.3:
            store = get_vector_store()
            vector = await embed_single(content)

            payload = {
                "tenant_id": self.tenant_id,
                "memory_id": memory_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "stored_at": entry["timestamp"],
                **(metadata or {}),
            }

            await store.upsert(
                collection_name=MEMORY_COLLECTION,
                vectors=[vector],
                payloads=[payload],
                ids=[memory_id],
            )

        logger.debug(
            "memory_stored",
            tenant_id=self.tenant_id,
            memory_type=memory_type,
            importance=importance,
        )
        return memory_id

    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Recall relevant memories via semantic search."""
        store = get_vector_store()
        query_vector = await embed_single(query)

        filters: dict[str, Any] = {}
        if memory_type:
            filters["memory_type"] = memory_type

        results = await store.search(
            collection_name=MEMORY_COLLECTION,
            query_vector=query_vector,
            tenant_id=self.tenant_id,
            limit=limit,
            filters=filters,
        )

        return [
            {
                "id": r["payload"].get("memory_id", r["id"]),
                "content": r["payload"].get("content", ""),
                "memory_type": r["payload"].get("memory_type", ""),
                "importance": r["payload"].get("importance", 0.0),
                "score": r["score"],
                "stored_at": r["payload"].get("stored_at", ""),
            }
            for r in results
        ]

    def get_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent short-term memories (no embedding needed)."""
        return list(reversed(self._short_term[-limit:]))

    async def forget_all(self) -> None:
        """Clear all memories for this tenant (GDPR compliance)."""
        self._short_term.clear()
        store = get_vector_store()
        await store.delete_by_tenant(MEMORY_COLLECTION, self.tenant_id)
        logger.info("memory_cleared", tenant_id=self.tenant_id)

    async def summarize_context(self, query: str, max_items: int = 5) -> str:
        """Build a context string from recent + relevant memories."""
        recent = self.get_recent(3)
        relevant = await self.recall(query, limit=max_items)

        parts: list[str] = []
        if recent:
            parts.append("Recent context:")
            for m in recent:
                parts.append(f"  - {m['content']}")

        if relevant:
            parts.append("Relevant past experience:")
            for m in relevant:
                parts.append(f"  - [{m['memory_type']}] {m['content']} (relevance: {m['score']:.2f})")

        return "\n".join(parts) if parts else "No relevant context found."

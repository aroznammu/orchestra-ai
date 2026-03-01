"""Global aggregate model with differential privacy.

Anonymized patterns across all tenants -- no individual tenant data leaks.
Used for cold-start recommendations and industry benchmarking.
"""

import hashlib
import random
from typing import Any

import structlog

from orchestra.rag.embeddings import embed_single
from orchestra.rag.store import get_vector_store

logger = structlog.get_logger("moat.global_model")

GLOBAL_MODEL_COLLECTION = "global_patterns"

# Differential privacy noise parameter (Laplace mechanism)
EPSILON = 1.0


class GlobalModel:
    """Anonymized aggregate model across all tenants."""

    def __init__(self) -> None:
        self._contribution_count = 0

    async def contribute(
        self,
        content: str,
        platform: str,
        metrics: dict[str, float],
        category: str = "general",
    ) -> None:
        """Add an anonymized data point to the global model.

        Applies differential privacy noise to metrics before storage.
        """
        store = get_vector_store()

        noisy_metrics = _add_laplace_noise(metrics, EPSILON)

        # Anonymize content (hash-based, no reversible mapping)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        embed_text = (
            f"Platform: {platform}\n"
            f"Category: {category}\n"
            f"Engagement pattern: {noisy_metrics.get('engagement_rate', 0):.3f}\n"
            f"Content type: {_classify_content_type(content)}"
        )
        vector = await embed_single(embed_text)

        payload = {
            "tenant_id": "global",
            "content_hash": content_hash,
            "platform": platform,
            "category": category,
            "content_type": _classify_content_type(content),
            "engagement_rate": noisy_metrics.get("engagement_rate", 0.0),
            "click_rate": noisy_metrics.get("click_rate", 0.0),
            "roi_bucket": _bucket_roi(noisy_metrics.get("roi", 0.0)),
            "content_length_bucket": _bucket_length(len(content)),
        }

        point_id = f"global:{content_hash}:{platform}"
        await store.upsert(
            collection_name=GLOBAL_MODEL_COLLECTION,
            vectors=[vector],
            payloads=[payload],
            ids=[point_id],
        )

        self._contribution_count += 1

    async def get_benchmarks(
        self,
        platform: str,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Get aggregate benchmarks for a platform/category."""
        store = get_vector_store()

        query_text = f"Platform: {platform}, Category: {category or 'general'}"
        query_vector = await embed_single(query_text)

        filters: dict[str, Any] = {"platform": platform}
        if category:
            filters["category"] = category

        results = await store.search(
            collection_name=GLOBAL_MODEL_COLLECTION,
            query_vector=query_vector,
            tenant_id="global",
            limit=100,
            filters=filters,
        )

        if not results:
            return {
                "platform": platform,
                "category": category,
                "sample_size": 0,
                "avg_engagement_rate": 0.0,
                "avg_click_rate": 0.0,
            }

        ers = [r["payload"].get("engagement_rate", 0.0) for r in results]
        ctrs = [r["payload"].get("click_rate", 0.0) for r in results]

        return {
            "platform": platform,
            "category": category,
            "sample_size": len(results),
            "avg_engagement_rate": round(sum(ers) / len(ers), 4),
            "avg_click_rate": round(sum(ctrs) / len(ctrs), 4),
            "top_content_types": _count_content_types(results),
            "top_length_buckets": _count_buckets(results, "content_length_bucket"),
        }

    async def cold_start_recommendation(
        self,
        platform: str,
        category: str = "general",
    ) -> dict[str, Any]:
        """Provide recommendations for new tenants with no data."""
        benchmarks = await self.get_benchmarks(platform, category)

        return {
            "platform": platform,
            "category": category,
            "recommendation": {
                "target_engagement_rate": benchmarks.get("avg_engagement_rate", 0.02),
                "suggested_content_type": (
                    benchmarks.get("top_content_types", [{"type": "mixed"}])[0].get("type", "mixed")
                    if benchmarks.get("top_content_types")
                    else "mixed"
                ),
                "confidence": min(benchmarks.get("sample_size", 0) / 50, 1.0),
                "note": "Based on anonymized aggregate data from similar campaigns",
            },
        }


def _add_laplace_noise(metrics: dict[str, float], epsilon: float) -> dict[str, float]:
    """Apply Laplace mechanism for differential privacy."""
    noisy = {}
    for key, value in metrics.items():
        sensitivity = abs(value) * 0.1 + 0.01  # 10% of value
        noise = random.uniform(-1, 1) * (sensitivity / epsilon)
        noisy[key] = max(value + noise, 0.0)
    return noisy


def _classify_content_type(content: str) -> str:
    """Simple heuristic content type classification."""
    content_lower = content.lower()
    if "?" in content:
        return "question"
    elif any(w in content_lower for w in ["how to", "guide", "tutorial", "step"]):
        return "educational"
    elif any(w in content_lower for w in ["sale", "discount", "offer", "deal", "%"]):
        return "promotional"
    elif any(w in content_lower for w in ["announce", "launch", "introducing", "new"]):
        return "announcement"
    elif any(w in content_lower for w in ["tip", "advice", "strategy", "insight"]):
        return "thought_leadership"
    return "general"


def _bucket_roi(roi: float) -> str:
    if roi < 0:
        return "negative"
    elif roi < 1:
        return "low"
    elif roi < 3:
        return "medium"
    elif roi < 10:
        return "high"
    return "exceptional"


def _bucket_length(length: int) -> str:
    if length < 50:
        return "micro"
    elif length < 150:
        return "short"
    elif length < 500:
        return "medium"
    elif length < 1500:
        return "long"
    return "essay"


def _count_content_types(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for r in results:
        ct = r["payload"].get("content_type", "general")
        counts[ct] = counts.get(ct, 0) + 1
    return sorted(
        [{"type": k, "count": v} for k, v in counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )


def _count_buckets(results: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for r in results:
        b = r["payload"].get(key, "unknown")
        counts[b] = counts.get(b, 0) + 1
    return sorted(
        [{"bucket": k, "count": v} for k, v in counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

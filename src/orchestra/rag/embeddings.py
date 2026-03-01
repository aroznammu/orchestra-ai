"""Embedding pipeline.

Converts text (campaign content, metadata, performance data) into vectors.
Supports OpenAI, Ollama (local), and a fallback hash-based embedding for testing.
"""

import hashlib
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.config import get_settings

logger = structlog.get_logger("rag.embeddings")

EMBEDDING_DIM = 1536


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    HASH = "hash"  # deterministic fallback for testing


class EmbeddingRequest(BaseModel):
    texts: list[str]
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingResult(BaseModel):
    vectors: list[list[float]]
    model: str
    dimensions: int
    token_usage: int = 0


async def embed_texts(
    texts: list[str],
    provider: EmbeddingProvider | None = None,
) -> EmbeddingResult:
    """Embed a batch of texts using the configured provider.

    Auto-selects provider based on available API keys if not specified.
    """
    if provider is None:
        provider = _select_provider()

    if provider == EmbeddingProvider.OPENAI:
        return await _embed_openai(texts)
    elif provider == EmbeddingProvider.OLLAMA:
        return await _embed_ollama(texts)
    else:
        return _embed_hash(texts)


async def embed_single(
    text: str,
    provider: EmbeddingProvider | None = None,
) -> list[float]:
    """Convenience: embed a single text, return the vector."""
    result = await embed_texts([text], provider)
    return result.vectors[0]


def _select_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.has_openai:
        return EmbeddingProvider.OPENAI
    return EmbeddingProvider.OLLAMA


async def _embed_openai(texts: list[str]) -> EmbeddingResult:
    """Embed via OpenAI text-embedding-3-small."""
    import httpx

    settings = get_settings()
    api_key = settings.openai_api_key.get_secret_value()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "text-embedding-3-small",
                "input": texts,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

    vectors = [item["embedding"] for item in data["data"]]
    usage = data.get("usage", {}).get("total_tokens", 0)

    logger.info("openai_embedding", count=len(texts), tokens=usage)

    return EmbeddingResult(
        vectors=vectors,
        model="text-embedding-3-small",
        dimensions=len(vectors[0]) if vectors else EMBEDDING_DIM,
        token_usage=usage,
    )


async def _embed_ollama(texts: list[str]) -> EmbeddingResult:
    """Embed via local Ollama (nomic-embed-text or similar)."""
    import httpx

    settings = get_settings()
    ollama_url = settings.ollama_url.rstrip("/")
    model = "nomic-embed-text"

    vectors = []
    async with httpx.AsyncClient() as client:
        for text in texts:
            response = await client.post(
                f"{ollama_url}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            vectors.append(data["embedding"])

    dim = len(vectors[0]) if vectors else 768

    logger.info("ollama_embedding", count=len(texts), model=model)

    return EmbeddingResult(
        vectors=vectors,
        model=model,
        dimensions=dim,
        token_usage=0,
    )


def _embed_hash(texts: list[str]) -> EmbeddingResult:
    """Deterministic hash-based embedding for testing (not for production)."""
    vectors = []
    for text in texts:
        digest = hashlib.sha512(text.encode()).digest()
        # Expand hash to fill EMBEDDING_DIM floats in [-1, 1]
        vec: list[float] = []
        for i in range(EMBEDDING_DIM):
            byte_idx = i % len(digest)
            vec.append((digest[byte_idx] / 127.5) - 1.0)
        vectors.append(vec)

    return EmbeddingResult(
        vectors=vectors,
        model="hash-fallback",
        dimensions=EMBEDDING_DIM,
        token_usage=0,
    )


def prepare_campaign_text(
    title: str,
    content: str,
    platform: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Build a structured text representation of a campaign for embedding."""
    parts = [
        f"Campaign: {title}",
        f"Platform: {platform}",
        f"Content: {content}",
    ]
    if metadata:
        for key, value in metadata.items():
            parts.append(f"{key}: {value}")
    return "\n".join(parts)

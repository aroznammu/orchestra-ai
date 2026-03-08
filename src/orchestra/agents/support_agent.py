"""AI-powered customer support agent.

Handles multi-turn customer conversations with:
- RAG-backed knowledge retrieval from the support_kb Qdrant collection
- FAQ matching from PostgreSQL
- Strict guardrails against leaking proprietary/credential information
- Response sanitization before returning to users
"""

import re
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from orchestra.config import get_settings
from orchestra.core.cost_router import ModelTier, TaskComplexity, route_model

logger = structlog.get_logger("agents.support")

SUPPORT_KB_COLLECTION = "support_kb"
MAX_CONTEXT_MESSAGES = 20
MAX_RAG_RESULTS = 5

_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"postgresql(\+asyncpg)?://\S+"),
    re.compile(r"redis://\S+"),
    re.compile(r"mongodb(\+srv)?://\S+"),
    re.compile(r"https?://\S*:[^@\s]+@\S+"),
    re.compile(r"fernet_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"jwt_secret\S*\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"encryption_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{30,}"),
    re.compile(r"OPENAI_API_KEY\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"ANTHROPIC_API_KEY\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"FAL_KEY\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"STRIPE_\w+\s*[:=]\s*\S+", re.IGNORECASE),
]

SYSTEM_PROMPT = """\
You are OrchestraAI Support, a helpful and friendly customer support assistant \
for OrchestraAI — an AI-Native Marketing Orchestration Platform.

You help customers with:
- Getting started and onboarding
- Understanding features (campaigns, analytics, kill switch, billing, platform connections)
- Troubleshooting common issues
- Explaining pricing plans (Starter $99/mo, Agency $999/mo)
- Guiding them through platform connections and campaign setup

STRICT RULES — you MUST follow these at all times:
1. NEVER reveal API keys, database credentials, JWT secrets, encryption keys, or any \
   system configuration values.
2. NEVER disclose internal architecture details such as database schemas, internal service \
   names, LangGraph node names, agent implementation details, or codebase structure.
3. NEVER reveal pricing algorithms, bidding logic internals, moat/competitive data, or \
   proprietary optimization strategies.
4. NEVER share contents of .env files, configuration files, or any server-side secrets.
5. If a user asks about internal implementation, system internals, or credentials, respond \
   with: "I can help you with product features and usage questions. For technical \
   architecture details, please contact our engineering team."
6. Keep responses concise, helpful, and professional.
7. If you don't know the answer, say so honestly and suggest contacting support@orchestraai.dev.
"""


class SupportResponse(BaseModel):
    reply: str
    sources: list[str] = Field(default_factory=list)
    faq_matches: list[dict[str, str]] = Field(default_factory=list)


def sanitize_response(text: str) -> str:
    """Strip any accidentally leaked credentials or sensitive data."""
    sanitized = text
    for pattern in _SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


async def _retrieve_knowledge(query: str, tenant_id: str) -> list[dict[str, Any]]:
    """Query the support_kb Qdrant collection for relevant docs."""
    try:
        from orchestra.rag.embeddings import embed_single
        from orchestra.rag.store import get_vector_store

        store = get_vector_store()
        query_vector = await embed_single(query)
        results = await store.search(
            collection_name=SUPPORT_KB_COLLECTION,
            query_vector=query_vector,
            tenant_id=tenant_id,
            limit=MAX_RAG_RESULTS,
            score_threshold=0.65,
        )
        return results
    except Exception as e:
        logger.warning("support_rag_retrieval_failed", error=str(e))
        return []


def _build_messages(
    user_message: str,
    chat_history: list[dict[str, str]],
    rag_context: list[dict[str, Any]],
    faq_context: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Assemble the LLM message list with system prompt, context, and history."""
    context_parts: list[str] = []

    if rag_context:
        kb_text = "\n\n".join(
            f"- {r['payload'].get('text', r['payload'].get('content', ''))}"
            for r in rag_context
            if r.get("payload")
        )
        if kb_text.strip():
            context_parts.append(f"Relevant knowledge base articles:\n{kb_text}")

    if faq_context:
        faq_text = "\n\n".join(
            f"Q: {f['question']}\nA: {f['answer']}" for f in faq_context
        )
        context_parts.append(f"Matching FAQ entries:\n{faq_text}")

    system_content = SYSTEM_PROMPT
    if context_parts:
        system_content += (
            "\n\nUse the following context to answer the user's question. "
            "Only reference information from this context — do not invent facts.\n\n"
            + "\n\n---\n\n".join(context_parts)
        )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]

    for msg in chat_history[-MAX_CONTEXT_MESSAGES:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    return messages


async def _call_openai(api_key: str, model: str, messages: list[dict[str, str]]) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 800,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("support_openai_failed", error=str(e))
        return None


async def _call_anthropic(api_key: str, model: str, messages: list[dict[str, str]]) -> str | None:
    try:
        system_msg = ""
        conv_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                conv_messages.append(m)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 800,
                    "system": system_msg,
                    "messages": conv_messages,
                },
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.warning("support_anthropic_failed", error=str(e))
        return None


async def _call_ollama(base_url: str, model: str, messages: list[dict[str, str]]) -> str | None:
    try:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning("support_ollama_failed", error=str(e))
        return None


async def get_support_reply(
    user_message: str,
    tenant_id: str,
    chat_history: list[dict[str, str]] | None = None,
    faq_entries: list[dict[str, str]] | None = None,
) -> SupportResponse:
    """Generate an AI support reply with RAG context and guardrails.

    Args:
        user_message: The customer's question.
        tenant_id: For tenant-scoped RAG retrieval.
        chat_history: Previous messages as [{"role": "user"|"assistant", "content": "..."}].
        faq_entries: Matching FAQ rows as [{"question": "...", "answer": "..."}].

    Returns:
        SupportResponse with sanitized reply, sources, and matched FAQs.
    """
    if chat_history is None:
        chat_history = []
    if faq_entries is None:
        faq_entries = []

    rag_results = await _retrieve_knowledge(user_message, tenant_id)
    sources = [
        r["payload"].get("source", "knowledge_base") for r in rag_results if r.get("payload")
    ]

    messages = _build_messages(user_message, chat_history, rag_results, faq_entries)

    model_name, tier = route_model(TaskComplexity.SIMPLE)
    settings = get_settings()
    reply: str | None = None

    if tier == ModelTier.FAST and settings.has_openai:
        reply = await _call_openai(
            settings.openai_api_key.get_secret_value(), model_name, messages
        )

    if reply is None and settings.has_anthropic:
        cap_model = settings.default_capable_model
        reply = await _call_anthropic(
            settings.anthropic_api_key.get_secret_value(), cap_model, messages
        )

    if reply is None:
        reply = await _call_ollama(
            settings.ollama_url, settings.default_local_model, messages
        )

    if reply is None:
        reply = (
            "I'm sorry, I'm unable to process your request right now. "
            "Please try again shortly or contact support@orchestraai.dev for assistance."
        )

    reply = sanitize_response(reply)

    logger.info(
        "support_reply_generated",
        tenant_id=tenant_id,
        model_tier=tier.value,
        rag_sources=len(sources),
        faq_matches=len(faq_entries),
    )

    return SupportResponse(
        reply=reply,
        sources=sources,
        faq_matches=faq_entries,
    )


# ---------------------------------------------------------------------------
# Default FAQ seed data
# ---------------------------------------------------------------------------

DEFAULT_FAQS: list[dict[str, Any]] = [
    {
        "category": "Getting Started",
        "question": "What is OrchestraAI?",
        "answer": (
            "OrchestraAI is an AI-Native Marketing Orchestration Platform that connects "
            "nine major advertising platforms (Twitter, YouTube, TikTok, Pinterest, Facebook, "
            "Instagram, LinkedIn, Snapchat, and Google Ads) under a single intelligent orchestrator. "
            "You issue natural language commands and OrchestraAI handles intent classification, "
            "compliance checking, content generation, publishing, and analytics."
        ),
        "sort_order": 0,
    },
    {
        "category": "Getting Started",
        "question": "How do I create my first campaign?",
        "answer": (
            "Navigate to Campaigns in the sidebar, click 'Create Campaign', fill in the name, "
            "select target platforms, set your budget, and click Create. You can then launch it "
            "from the campaign list. Alternatively, use the AI Orchestrator and type something "
            "like 'Create a summer sale campaign on Instagram and TikTok with a $500 budget.'"
        ),
        "sort_order": 1,
    },
    {
        "category": "Getting Started",
        "question": "How do I connect my social media accounts?",
        "answer": (
            "Go to Settings > Platforms and click 'Connect' next to the platform you want to add. "
            "You will be redirected to the platform's OAuth flow to authorize OrchestraAI. "
            "Once connected, the platform appears as active in your dashboard."
        ),
        "sort_order": 2,
    },
    {
        "category": "AI Orchestrator",
        "question": "What can the AI Orchestrator do?",
        "answer": (
            "The AI Orchestrator accepts natural language commands and can: create and launch campaigns, "
            "generate content (text, images, video), publish or schedule posts across platforms, "
            "run analytics reports, optimize campaign performance, check compliance, and reallocate budgets. "
            "Simply type your instruction and the AI handles the multi-step workflow automatically."
        ),
        "sort_order": 0,
    },
    {
        "category": "AI Orchestrator",
        "question": "What AI models does OrchestraAI use?",
        "answer": (
            "OrchestraAI uses a cost-aware routing system that selects the best model for each task. "
            "Cloud providers include OpenAI and Anthropic, and there is support for self-hosted models "
            "via Ollama for organizations that prefer local inference. The system automatically "
            "routes simple tasks to faster, cheaper models and complex tasks to more capable ones."
        ),
        "sort_order": 1,
    },
    {
        "category": "Campaigns",
        "question": "How do I pause or resume a campaign?",
        "answer": (
            "Open the Campaigns page, find the campaign in the list, and click the Pause or Launch "
            "button in the actions column. Pausing immediately stops all scheduled posts and ad spend "
            "for that campaign across all platforms."
        ),
        "sort_order": 0,
    },
    {
        "category": "Campaigns",
        "question": "Can I run campaigns on multiple platforms simultaneously?",
        "answer": (
            "Yes. When creating a campaign, select multiple platforms (e.g., Instagram, TikTok, LinkedIn). "
            "OrchestraAI automatically adapts content for each platform's requirements and publishes "
            "across all of them. Cross-platform analytics are available in the Analytics dashboard."
        ),
        "sort_order": 1,
    },
    {
        "category": "Billing & Pricing",
        "question": "What pricing plans are available?",
        "answer": (
            "OrchestraAI offers two plans: Starter at $99/month and Agency at $999/month. "
            "The Starter plan is designed for small teams and includes core features. "
            "The Agency plan includes advanced features, higher limits, and priority support. "
            "OrchestraAI is also open-core with an Apache 2.0 license, so you can self-host for free."
        ),
        "sort_order": 0,
    },
    {
        "category": "Billing & Pricing",
        "question": "How do I upgrade or change my subscription?",
        "answer": (
            "Go to Settings > Billing, where you can see your current plan and click 'Upgrade' "
            "or 'Manage Subscription'. This opens the Stripe customer portal where you can change "
            "plans, update payment methods, or cancel."
        ),
        "sort_order": 1,
    },
    {
        "category": "Safety & Compliance",
        "question": "What is the Kill Switch?",
        "answer": (
            "The Kill Switch is an emergency feature that instantly halts all ad spend across every "
            "connected platform with a single click. It's available in the sidebar and is designed "
            "for situations where you need to immediately stop all campaigns — for example, if you "
            "detect anomalous spending or need to respond to a brand safety incident."
        ),
        "sort_order": 0,
    },
    {
        "category": "Safety & Compliance",
        "question": "How does OrchestraAI prevent overspending?",
        "answer": (
            "OrchestraAI enforces three-tier spend caps: daily, weekly, and monthly limits that cannot "
            "be overridden by the AI. It also uses statistical anomaly detection (Z-scores and IQR) "
            "to flag unusual spending patterns. The three-phase bidding system starts fully "
            "human-approved and gradually earns autonomy over time."
        ),
        "sort_order": 1,
    },
    {
        "category": "Safety & Compliance",
        "question": "Is my data safe with OrchestraAI?",
        "answer": (
            "Yes. OrchestraAI encrypts all platform tokens at rest, enforces tenant isolation so your "
            "data is never mixed with other organizations, provides full GDPR compliance tools "
            "(data export and deletion), and maintains a complete audit trail of all actions. "
            "API keys are stored using industry-standard hashing."
        ),
        "sort_order": 2,
    },
    {
        "category": "Analytics",
        "question": "What analytics does OrchestraAI provide?",
        "answer": (
            "OrchestraAI provides cross-platform analytics including impressions, engagement, clicks, "
            "spend, ROI, and engagement rates for each connected platform. The dashboard shows "
            "aggregated metrics and per-platform breakdowns. You can also ask the AI Orchestrator "
            "for detailed reports by typing something like 'Show me analytics for last 30 days.'"
        ),
        "sort_order": 0,
    },
    {
        "category": "Troubleshooting",
        "question": "My platform connection shows as inactive. What should I do?",
        "answer": (
            "Platform connections can become inactive if the OAuth token expires. Go to Settings > "
            "Platforms, disconnect the inactive platform, and reconnect it. This will refresh your "
            "authorization tokens. If the issue persists, contact support@orchestraai.dev."
        ),
        "sort_order": 0,
    },
    {
        "category": "Troubleshooting",
        "question": "The AI Orchestrator returned an error. What should I do?",
        "answer": (
            "First, try rephrasing your request more specifically. If the error persists, check that "
            "you have an active subscription (Settings > Billing) and that your platform connections "
            "are active. For persistent issues, contact support@orchestraai.dev with your trace ID "
            "(shown in the error response)."
        ),
        "sort_order": 1,
    },
]


async def seed_default_faqs(db_session: Any) -> int:
    """Populate the faq_entries table with default global FAQs.

    Skips entries whose question already exists (idempotent).
    Returns the number of new entries created.
    """
    from sqlalchemy import select as sa_select
    from orchestra.db.models import FAQEntry as FAQModel

    created = 0
    for faq_data in DEFAULT_FAQS:
        existing = await db_session.execute(
            sa_select(FAQModel.id).where(FAQModel.question == faq_data["question"])
        )
        if existing.scalar_one_or_none() is not None:
            continue

        entry = FAQModel(
            tenant_id=None,
            category=faq_data["category"],
            question=faq_data["question"],
            answer=faq_data["answer"],
            sort_order=faq_data["sort_order"],
            is_published=True,
        )
        db_session.add(entry)
        created += 1

    if created:
        await db_session.flush()
        logger.info("default_faqs_seeded", count=created)

    return created

# OrchestraAI -- Architecture

> AI-Native Marketing Orchestration Platform

## System Overview

OrchestraAI is a multi-agent AI system that orchestrates marketing campaigns across 9 social and search platforms. It uses LangGraph for stateful agent workflows, Qdrant for vector-based knowledge retrieval, and a guardrailed bidding engine for financially bounded automation.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI + Uvicorn | Async REST API, ORJSONResponse |
| Agents | LangGraph + LangChain | Multi-agent orchestration, tool calling |
| Vector DB | Qdrant | Embeddings, RAG, performance retrieval |
| Relational DB | PostgreSQL 16 | Users, campaigns, audit logs |
| Cache / Bus | Redis 7 (Streams) | Caching, real-time event bus |
| Durable Bus | Apache Kafka 3.8 (KRaft) | Durable events, financial audit |
| Local LLM | Ollama | Self-hosted model serving |
| ORM | SQLAlchemy 2.0 (async) | Database abstraction |
| Migrations | Alembic | Schema versioning |
| CLI | Typer | Developer/operator interface |
| Validation | Pydantic v2 | Data contracts, settings |
| HTTP Client | httpx | Async platform API calls |
| Encryption | cryptography (Fernet) | Token encryption at rest |
| Scheduling | APScheduler | Campaign scheduling |
| Logging | structlog | Structured JSON logging |

## Execution Graph

```
User Request (API / CLI)
        |
   [Orchestrator]
        |
   classify_intent
        |
   compliance_gate  <-- FIRST GATE (always runs)
        |
   route_after_compliance
      /    |    \
content  analytics  optimize
      \    |    /
       respond
        |
   Return Result
```

### Agent Roles

1. **Orchestrator** -- LangGraph state machine, routes intent through agent graph
2. **Compliance Agent** -- Validates content/actions against ToS and internal policies
3. **Policy Agent** -- Per-platform content rules validation
4. **Content Agent** -- Multi-variant content generation with LLM
5. **Optimizer Agent** -- Thompson Sampling for A/B testing, Bayesian budget allocation
6. **Analytics Agent** -- Cross-platform metric aggregation and insights
7. **Platform Agent** -- Dispatches actions to platform connectors

### Safety System

Every agent transition passes through safety checks:
- **Max depth**: 10 (prevents infinite recursion)
- **Max calls per trace**: 50 (prevents runaway loops)
- **Self-call detection**: >3 calls to same agent triggers error
- **Trace timeout**: 120 seconds

## Data Flow

```
Platform APIs --> Connectors --> EventBus --> Agents --> Vector Store
                                   |                       |
                               PostgreSQL              Qdrant
                              (structured)           (embeddings)
                                   |
                                 Redis
                               (cache)
```

### Event Bus (Hybrid)

- **Redis Streams**: Real-time events (analytics updates, status changes)
- **Kafka**: Durable events (financial transactions, audit entries)
- Auto-routing based on event type

## Multi-Tenant Architecture

Every data access is scoped by `tenant_id`:
- PostgreSQL: `tenant_id` column on every table, enforced in queries
- Qdrant: Payload filter on `tenant_id` for every search
- Redis: Key prefixing with `tenant:{id}:`
- Agent memory: Per-tenant `AgentMemory` instances

## Cost-Aware Model Routing

```
Task Complexity     Model Selection
─────────────────   ──────────────────────────
SIMPLE              GPT-4o-mini / Ollama local
MODERATE            GPT-4o / Claude Haiku
COMPLEX             Claude Sonnet / GPT-4o
```

Fallback chain: Cloud -> Self-hosted -> Error

## Failure Recovery

| Failure Mode | Recovery Strategy |
|-------------|-------------------|
| LLM timeout | Fallback to next tier, then local model |
| Platform API error | Exponential backoff (tenacity), max 3 retries |
| Database connection | Connection pool with health checks |
| Qdrant unavailable | Graceful degradation (skip RAG, use defaults) |
| Kafka down | Redis Streams as fallback for durable events |
| Budget exceeded | Immediate halt, alert, rollback recent changes |
| Agent loop | Safety system kills trace, logs error |
| Kill switch | All spend operations halt immediately |

## Token Optimization

- **Embedding reuse**: Campaign embeddings cached, re-embedded only on metric updates
- **Prompt compression**: Platform style guides pre-built, not regenerated per request
- **Model routing**: Simple tasks use cheap models (GPT-4o-mini: $0.15/1M tokens)
- **Local fallback**: Ollama for development and cost-sensitive deployments
- **Batch embedding**: Multiple texts embedded in single API call

## Directory Structure

```
src/orchestra/
├── api/           # FastAPI routes + middleware
├── agents/        # LangGraph orchestrator + 6 specialized agents
├── bidding/       # Guardrailed bidding engine
├── cli/           # Typer CLI
├── compliance/    # Platform ToS rules, content validation
├── core/          # Event bus, scheduler, cost router, exceptions
├── db/            # SQLAlchemy models, Alembic migrations
├── intelligence/  # Cross-platform ROI, attribution, allocation
├── moat/          # Data flywheel, signals, performance embedding
├── platforms/     # 9 platform connectors (2 full, 7 stubbed)
├── rag/           # Qdrant store, embeddings, retriever, memory
├── risk/          # Spend caps, anomaly detection, alerts, rollback
└── security/      # RBAC, GDPR, encryption, audit trail
```

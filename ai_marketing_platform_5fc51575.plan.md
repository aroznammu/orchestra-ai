---
name: AI Marketing Platform
overview: Build a production-grade, AI-native marketing orchestration platform in Python (FastAPI + LangGraph + CLI) that integrates with 9 social/search platforms, features multi-agent AI orchestration with RAG, guardrailed phased-autonomy bidding, strict ToS compliance engine, financial risk containment, and cross-platform intelligence layer. Includes all documentation artifacts.
todos:
  - id: phase0-scaffold
    content: "Phase 0: Create project scaffold -- pyproject.toml, directory structure, Docker Compose, .env.example, .gitignore, Makefile"
    status: pending
  - id: phase1-core
    content: "Phase 1: Core infrastructure -- FastAPI app, config, PostgreSQL models, Alembic, Redis, JWT auth, audit middleware, CLI skeleton"
    status: pending
  - id: phase2-platforms
    content: "Phase 2: Platform integrations -- Abstract base, OAuth2 flows, X/Twitter + YouTube connectors (full), remaining platforms (stubbed)"
    status: pending
  - id: phase3-agents
    content: "Phase 3: AI agent system -- LangGraph orchestrator, 6 specialized agents (including Compliance Agent), tool-calling framework, cost-aware model routing"
    status: pending
  - id: phase3b-bidding
    content: "Phase 3B: Guardrailed bidding system -- 3-phase autonomy model (Hard Guardrail -> Semi-Autonomous -> Controlled Autonomous), approval workflows, kill switch"
    status: pending
  - id: phase3c-compliance
    content: "Phase 3C: Platform Compliance Engine -- Per-platform ToS rule encoding, rate-limit buffers, policy drift monitoring, content risk scoring"
    status: pending
  - id: phase3d-financial
    content: "Phase 3D: Financial Risk Containment -- Global/platform/campaign spend caps, anomaly detection, spend velocity monitoring, alert thresholds, emergency stop"
    status: pending
  - id: phase3e-crossplatform
    content: "Phase 3E: Cross-Platform Intelligence Layer -- ROI normalization, marginal return comparison, dynamic budget reallocation, channel saturation detection, unified attribution"
    status: pending
  - id: phase4-rag
    content: "Phase 4: RAG layer -- Qdrant vector store, embedding pipeline, retriever, indexer, long-term memory"
    status: pending
  - id: phase5-moat
    content: "Phase 5: Data moat engine -- Flywheel pipeline, signal layer, performance embeddings, tenant + global models"
    status: pending
  - id: phase6-security
    content: "Phase 6: Security and compliance -- Token encryption, multi-tenant isolation, RBAC, GDPR endpoints, policy enforcement layer"
    status: pending
  - id: phase7-docs
    content: "Phase 7: Documentation artifacts -- All 10 strategic documents including new Guardrailed Bidding & Compliance Architecture doc"
    status: pending
  - id: phase8-launch
    content: "Phase 8: GitHub launch package -- README, CONTRIBUTING, issue templates, CI/CD, one-click deploy, license"
    status: pending
isProject: false
---

# AI-Native Marketing Orchestration Platform -- Full Implementation Plan

## Project Name: **OrchestraAI** (working title)

All code lives in `C:\Users\ai958071\Documents\Automation\myprojects\experiment1\`

---

## Phase 0: Project Foundation

### Repository Structure

```
experiment1/
├── README.md                          # Viral README with badges, GIFs, comparison table
├── LICENSE                            # Apache 2.0 (open-core friendly)
├── pyproject.toml                     # Project config (Poetry)
├── Makefile                           # Developer convenience commands
├── Dockerfile                         # Production container
├── docker-compose.yml                 # Full local stack (app + postgres + redis + qdrant)
├── .env.example                       # Template for secrets (never committed)
├── .gitignore
├── docs/
│   ├── architecture.md                # Section 4: AI-native architecture
│   ├── viral-strategy.md              # Sections 1-3: Viral + growth loops + GitHub package
│   ├── data-moat.md                   # Sections 1-10 of Data Moat Addendum
│   ├── due-diligence.md               # Sections 1-12 of Technical DD Package
│   ├── cost-analysis.md               # Section 6: Cost structure
│   ├── security-compliance.md         # Section 8: Security & compliance
│   ├── user-procedures.md             # Section 9: All user procedures
│   ├── launch-strategy.md             # Section 10: Go-to-market
│   ├── differentiation.md             # Section 5: Competitive positioning
│   └── guardrailed-bidding.md         # Addendum: Bidding, compliance, financial risk, cross-platform intelligence
├── src/
│   └── orchestra/
│       ├── __init__.py
│       ├── main.py                    # FastAPI application entry point
│       ├── config.py                  # Settings via pydantic-settings (.env loading)
│       ├── cli/
│       │   ├── __init__.py
│       │   └── app.py                 # Typer CLI (campaign, optimize, report, connect)
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── campaigns.py       # CRUD + launch + optimize
│       │   │   ├── platforms.py       # OAuth connect/disconnect
│       │   │   ├── analytics.py       # Cross-platform analytics
│       │   │   ├── reports.py         # AI-generated reports
│       │   │   └── health.py          # Health + readiness probes
│       │   ├── middleware/
│       │   │   ├── auth.py            # JWT + API key auth
│       │   │   ├── rate_limit.py      # Per-tenant rate limiting
│       │   │   └── audit.py           # Audit log middleware
│       │   └── deps.py               # Dependency injection
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── orchestrator.py        # LangGraph multi-agent orchestrator
│       │   ├── policy.py              # Policy agent (ToS compliance, content rules)
│       │   ├── compliance.py          # Platform Compliance Agent (ToS encoding, policy drift)
│       │   ├── optimizer.py           # Optimization agent (A/B, bandit, Bayesian)
│       │   ├── content.py             # Content generation agent
│       │   ├── analytics_agent.py     # Analytics + insight agent
│       │   ├── platform_agent.py      # Platform integration dispatcher
│       │   └── tools/
│       │       ├── __init__.py
│       │       ├── social_tools.py    # Tool definitions for platform APIs
│       │       ├── analytics_tools.py # Tool definitions for data retrieval
│       │       └── content_tools.py   # Tool definitions for content ops
│       ├── bidding/
│       │   ├── __init__.py
│       │   ├── engine.py             # Phased autonomy bidding engine
│       │   ├── guardrails.py         # Hard guardrail mode (Phase 1 default)
│       │   ├── semi_auto.py          # Semi-autonomous mode (Phase 2)
│       │   ├── autonomous.py         # Controlled autonomous mode (Phase 3)
│       │   ├── approval.py           # Human approval workflow
│       │   └── kill_switch.py        # Emergency stop mechanism
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── spend_caps.py         # Global/platform/campaign budget caps
│       │   ├── anomaly.py            # Spend anomaly detection
│       │   ├── velocity.py           # Spend velocity monitoring
│       │   ├── alerts.py             # Alert thresholds (50%, 75%, 90%)
│       │   └── rollback.py           # Automatic rollback mechanism
│       ├── compliance/
│       │   ├── __init__.py
│       │   ├── tos_rules.py          # Per-platform ToS rule definitions
│       │   ├── content_validator.py   # Content policy validation + risk scoring
│       │   ├── rate_limiter.py        # Conservative rate-limit buffers (10-20% below max)
│       │   ├── policy_monitor.py      # API change monitoring + auto-disable
│       │   └── restrictions.py        # Hard-coded prohibited actions list
│       ├── intelligence/
│       │   ├── __init__.py
│       │   ├── cross_platform.py     # Cross-platform ROI normalization
│       │   ├── allocator.py          # Dynamic budget allocation across platforms
│       │   ├── saturation.py         # Channel saturation detection
│       │   ├── attribution.py        # Unified attribution intelligence
│       │   └── marginal_return.py    # Marginal return per dollar comparison
│       ├── platforms/
│       │   ├── __init__.py
│       │   ├── base.py               # Abstract platform interface
│       │   ├── facebook.py
│       │   ├── instagram.py
│       │   ├── tiktok.py
│       │   ├── twitter.py            # X/Twitter
│       │   ├── youtube.py
│       │   ├── google_ads.py
│       │   ├── linkedin.py
│       │   ├── snapchat.py
│       │   └── pinterest.py
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── embeddings.py          # Embedding generation + caching
│       │   ├── vector_store.py        # Qdrant vector DB interface
│       │   ├── retriever.py           # RAG retrieval pipeline
│       │   └── indexer.py             # Document/campaign indexing
│       ├── moat/
│       │   ├── __init__.py
│       │   ├── flywheel.py            # Data flywheel pipeline
│       │   ├── signals.py             # Proprietary signal layer
│       │   ├── performance_embed.py   # Campaign-to-vector encoding
│       │   ├── global_model.py        # Anonymized global meta-model
│       │   └── tenant_model.py        # Per-tenant private model
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py             # SQLAlchemy models (campaigns, users, platforms, etc.)
│       │   ├── session.py            # Async DB session management
│       │   └── migrations/           # Alembic migrations
│       ├── security/
│       │   ├── __init__.py
│       │   ├── oauth.py              # OAuth2 flows per platform
│       │   ├── encryption.py         # Token encryption (Fernet/AES)
│       │   └── rbac.py               # Role-based access control
│       └── core/
│           ├── __init__.py
│           ├── events.py             # Event bus (Redis Streams)
│           ├── scheduler.py          # Campaign scheduling (APScheduler)
│           ├── cost_router.py        # LLM cost-aware model routing
│           └── exceptions.py         # Custom exception hierarchy
├── tests/
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_platforms/
│   ├── test_api/
│   └── test_rag/
├── plugins/
│   └── example_plugin/              # Plugin template for ecosystem
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CONTRIBUTING.md
│   └── workflows/
│       ├── ci.yml                    # Lint + test on PR
│       └── release.yml               # Auto-release on tag
└── scripts/
    ├── setup_dev.sh                  # One-command dev setup
    └── demo.py                       # Interactive demo script
```

### Core Tech Stack

- **Python 3.12+**
- **FastAPI** -- async REST API framework
- **LangGraph** -- multi-agent orchestration (preferred over raw LangChain for stateful agent graphs)
- **LangChain** -- tool calling, LLM abstraction, RAG components
- **Qdrant** -- vector database (open-source, self-hostable)
- **PostgreSQL** -- primary relational database
- **Redis** -- caching, event bus (Redis Streams), rate limiting
- **SQLAlchemy 2.0** -- async ORM
- **Alembic** -- database migrations
- **Typer** -- CLI framework
- **Pydantic v2** -- data validation and settings
- **httpx** -- async HTTP client for platform APIs
- **cryptography** -- token encryption (Fernet)
- **APScheduler** -- campaign scheduling
- **Poetry** -- dependency management

---

## Phase 1: Core Infrastructure (Weeks 1-2)

Build the skeleton that everything else plugs into.

- **FastAPI app** with health routes, CORS, structured error handling
- **Config system** via pydantic-settings loading from `.env`
- **PostgreSQL models**: User, Tenant, PlatformConnection, Campaign, CampaignPost, AuditLog, Experiment
- **Alembic migration** setup
- **Redis connection** for caching and event bus
- **Docker Compose** stack: app + postgres + redis + qdrant
- **JWT + API key authentication** middleware
- **Audit log middleware** that records all API calls
- **CLI skeleton** with Typer (subcommands: `campaign`, `connect`, `optimize`, `report`)

---

## Phase 2: Platform Integrations (Weeks 2-4)

Each platform connector implements an abstract `PlatformBase` interface:

```python
class PlatformBase(ABC):
    async def authenticate(self, oauth_code: str) -> TokenPair
    async def refresh_token(self, refresh_token: str) -> TokenPair
    async def publish(self, content: PostContent) -> PostResult
    async def get_analytics(self, post_id: str) -> AnalyticsData
    async def get_audience(self) -> AudienceData
    async def schedule(self, content: PostContent, time: datetime) -> ScheduleResult
```

- **Priority order** (based on API accessibility without business verification):
  1. X/Twitter (paid API, instant access)
  2. YouTube/Google (free, instant)
  3. Pinterest (free, easy approval)
  4. TikTok (developer portal, moderate approval)
  5. Facebook/Instagram (requires Meta business verification)
  6. LinkedIn (requires partner approval)
  7. Snapchat (marketing API approval)
  8. Google Ads (separate from YouTube)
- **OAuth2 flows** for each platform with encrypted token storage
- **Rate limit handling** with exponential backoff per platform
- **Webhook receivers** where supported (Meta, YouTube)

---

## Phase 3: AI Agent System (Weeks 3-6)

The core differentiator. Built on **LangGraph** for stateful multi-agent orchestration.

### Agent Architecture (LangGraph State Machine)

```
User Request
    |
    v
[Orchestrator Agent] -- routes to specialized agents
    |
    +---> [Compliance Agent] -- FIRST GATE: ToS check, content risk scoring, rate-limit validation
    +---> [Policy Agent] -- content rules, prohibited category enforcement
    +---> [Content Agent] -- generates/optimizes content per platform
    +---> [Bidding Engine] -- guardrailed bid/budget recommendations (phased autonomy)
    +---> [Platform Agent] -- dispatches to platform connectors
    +---> [Optimization Agent] -- A/B testing, Bayesian optimization
    +---> [Analytics Agent] -- cross-platform insights, reports
    +---> [Cross-Platform Intelligence] -- ROI normalization, budget allocation
```

- **Orchestrator** (`orchestrator.py`): LangGraph graph that routes user intent to the right agent(s), handles failures, retries, and parallel execution
- **Compliance Agent** (`compliance.py`): **First gate for every action.** Encodes per-platform ToS rules, applies stricter internal buffers than platform minimums, monitors API changes, auto-disables features on policy shifts
- **Policy Agent** (`policy.py`): Validates content against each platform's ToS, character limits, media requirements, banned content, prohibited demographics, restricted interest combinations
- **Content Agent** (`content.py`): Generates platform-optimized content variants (different tone for LinkedIn vs TikTok), hashtag optimization, caption generation. All output passes through compliance validation before publish
- **Optimization Agent** (`optimizer.py`): Multi-armed bandit for content variant selection, Bayesian optimization for posting time, exploration vs exploitation logic
- **Analytics Agent** (`analytics_agent.py`): Aggregates cross-platform metrics, generates natural language insights, ROI calculations
- **Platform Agent** (`platform_agent.py`): Dispatches publish/schedule/analytics calls to the correct platform connector

### Tool-Calling Framework

Each agent has access to typed tools:

- `social_tools.py`: publish_post, schedule_post, get_post_analytics, get_audience_insights
- `analytics_tools.py`: get_cross_platform_metrics, get_campaign_performance, generate_report
- `content_tools.py`: generate_caption, optimize_hashtags, resize_media, check_compliance

### Cost-Aware Model Routing (`cost_router.py`)

- Routes simple tasks (classification, extraction) to cheaper models (GPT-4o-mini, Claude Haiku)
- Routes complex tasks (content generation, strategy) to capable models (GPT-4o, Claude Sonnet)
- Tracks token usage per tenant for billing
- Falls back gracefully if primary provider is down

---

## Phase 3B: Guardrailed AI-Assisted Bidding System

**Core principle: "Compliant, conservative, explainable, and financially bounded."**
Autonomy increases only with data maturity and verified profitability.

### Three-Phase Autonomy Model

**Phase 1 -- Hard Guardrail Mode (DEFAULT for all new accounts)**

- Human approval required before: campaign creation, budget changes > X%, bid increases > Y%
- Daily spend caps enforced at system + campaign level
- Hard per-account max budget
- Automatic pause on anomaly detection
- Read-only recommendation mode available
- AI may recommend (bid adjustments, budget reallocations, audience segments, A/B experiments) but cannot execute large financial actions without approval

**Phase 2 -- Semi-Autonomous Mode (after profit threshold)**

- Activation requires: 90+ days stable performance, positive ROI for N cycles, validated anomaly detection, customer opt-in
- Auto-adjust bids within capped % ranges
- Auto-pause underperforming ads
- Auto-allocate budget within daily caps
- Still enforced: absolute daily spend ceiling, per-platform max allocation, kill switch, real-time alerting

**Phase 3 -- Controlled Autonomous Optimization (advanced users only)**

- Requires: sustained profitability, verified stable ROI, manual enabling by account owner, explicit legal acknowledgement
- Even here: no override of platform policy restrictions, no targeting outside allowed parameters, no policy-edge experimentation, no scraping, no non-official endpoints

### Implementation

- `bidding/engine.py`: State machine managing phase transitions with audit trail
- `bidding/guardrails.py`: Hard limits, approval gates, conservative defaults
- `bidding/approval.py`: Async approval workflow (email/webhook/CLI notification)
- `bidding/kill_switch.py`: Immediate halt of all spend across all platforms

---

## Phase 3C: Platform Compliance Engine

A dedicated subsystem that acts as the **first gate** before any action reaches a platform API.

- `compliance/tos_rules.py`: Machine-readable ToS rules per platform, updated manually or via policy monitor
- `compliance/content_validator.py`: Content risk scoring (0-100), platform-specific policy validation, optional human review mode
- `compliance/rate_limiter.py`: Conservative rate-limit buffers at 10-20% below platform maximum, conservative pacing algorithms
- `compliance/policy_monitor.py`: Monitors platform API changelog feeds, auto-disables features if policy shifts detected
- `compliance/restrictions.py`: Hard-coded list of things the system must NEVER do:
  - Bypass rate limits
  - Mask automation as human behavior
  - Circumvent review processes
  - Exploit loopholes
  - Automate prohibited ad categories
  - Generate ads violating platform content rules
  - Target prohibited demographics
  - Use restricted interest combinations
  - Attempt platform gaming strategies

---

## Phase 3D: Financial Risk Containment Architecture

Mandatory financial safety layer that wraps all spend operations.

- `risk/spend_caps.py`: Three-tier cap system -- global hard ceiling per account, per-platform budget cap, per-campaign cap
- `risk/anomaly.py`: Real-time anomaly detection on spend patterns (sudden spikes, unusual velocity)
- `risk/velocity.py`: Spend velocity monitoring -- flags if spend rate deviates from historical baseline
- `risk/alerts.py`: Alert thresholds at 50%, 75%, 90% of budget with notifications via webhook/email
- `risk/rollback.py`: Automatic rollback mechanism -- reverts bid/budget changes if anomaly confirmed
- Maximum daily exposure limit for new accounts (conservative default)
- Multi-factor approval required for large budget increases

---

## Phase 3E: Cross-Platform Intelligence Layer

**This is the moat.** Not competing with Google Smart Bidding or Meta Advantage+ (single-platform algorithms can't see cross-platform performance). Instead, this provides what no single platform can:

- `intelligence/cross_platform.py`: Normalize ROI across platforms into a unified metric
- `intelligence/marginal_return.py`: Compare marginal returns per dollar across all connected networks
- `intelligence/allocator.py`: Dynamically reallocate budget across platforms based on marginal return curves
- `intelligence/saturation.py`: Detect channel saturation (diminishing returns on a specific platform)
- `intelligence/attribution.py`: Unified attribution intelligence across all platforms

Why this is defensible:

- Single-platform algorithms are blind to cross-platform performance
- Cross-network intelligence creates structural advantage that compounds with more data
- More platforms connected = richer signal = better allocation = better ROI = more usage

---

## Phase 4: RAG Layer (Weeks 4-5)

- **Qdrant** vector store for campaign embeddings, content templates, performance data
- **Embedding pipeline**: Campaign content + metadata + performance outcome -> vector
- **Retriever**: "Find campaigns similar to X that performed well on Instagram in the fitness vertical"
- **Indexer**: Automatically indexes every campaign and its outcomes
- **Long-term memory**: Per-tenant conversation and decision history stored as vectors

---

## Phase 5: Data Moat Engine (Weeks 5-7)

The proprietary intelligence layer.

- **Flywheel pipeline** (`flywheel.py`): Campaign execution -> engagement data -> normalization -> embedding -> model update loop
- **Signal layer** (`signals.py`): Cross-platform engagement normalization, time-of-day intelligence, attention decay curves, content structure scoring
- **Performance embedding engine** (`performance_embed.py`): Campaign-to-vector encoding with outcome weighting, similar campaign retrieval, performance clustering
- **Dual-layer model**:
  - `tenant_model.py`: Per-customer private embeddings and performance tuning
  - `global_model.py`: Anonymized aggregate patterns with differential privacy

---

## Phase 6: Security and Compliance (Ongoing)

- **OAuth2 token encryption** using Fernet symmetric encryption at rest
- **Multi-tenant isolation** at the database level (tenant_id on every table, enforced in queries)
- **RBAC** with roles: owner, admin, member, viewer
- **Audit logs** for every API call, agent action, bid change, budget modification, and approval decision
- **GDPR/CCPA**: Data export endpoint, data deletion endpoint, consent tracking
- **Policy enforcement layer**: Hard-coded restrictions that cannot be overridden by any agent or user configuration
- **Financial audit trail**: Every spend decision logged with reasoning, approval status, and outcome
- **Kill switch integration**: Emergency stop accessible via API, CLI, and future dashboard

---

## Phase 7: Documentation Artifacts (Weeks 6-8)

Generate all the strategic documents required by the prompt:

- `docs/architecture.md` -- Full AI-native architecture with execution graph, failure recovery, token optimization
- `docs/viral-strategy.md` -- Viral architecture, growth loops, GitHub optimization package
- `docs/data-moat.md` -- All 10 sections of the Defensible Data Moat addendum
- `docs/due-diligence.md` -- All 12 sections of the Technical DD package with scorecard
- `docs/cost-analysis.md` -- Per-platform API costs, infra costs at 1k/10k/100k/1M users, LLM token estimates
- `docs/security-compliance.md` -- OAuth flows, encryption, SOC2 roadmap, GDPR/CCPA
- `docs/user-procedures.md` -- Installation, deployment, Docker, connecting accounts, campaigns, troubleshooting
- `docs/launch-strategy.md` -- Product Hunt, HN, Twitter thread, LinkedIn template, demo video outline
- `docs/differentiation.md` -- Competitive comparison, moat mechanisms
- `docs/guardrailed-bidding.md` -- **NEW**: Phased autonomy model, compliance engine design, financial risk containment, policy enforcement layer, cross-platform intelligence moat, risk mitigation table (ToS Violation, Budget Overspend, Policy Drift, API Dependency, Algorithm Underperformance)

---

## Phase 8: GitHub Launch Package (Week 8)

- **README.md**: Viral headline, badges, one-line install, feature comparison table, architecture diagram (ASCII/Mermaid), GIF demo script
- **CONTRIBUTING.md**: How to contribute, code style, PR process
- **Issue templates**: Bug report, feature request
- **CI/CD**: GitHub Actions for lint (ruff), test (pytest), release
- **One-click deploy**: Docker Compose for local, plus deploy-to-Railway/Render buttons
- **Apache 2.0 license** with open-core strategy (community edition is full-featured; enterprise adds SSO, advanced analytics, SLA)

---

## Estimated Effort, Token Consumption, and Cost

### Development effort (AI-driven, autonomous build):

- Phase 0-1 (Foundation): ~3-4 days
- Phase 2 (Platform integrations): ~5-7 days (2 platforms fully, rest stubbed)
- Phase 3 (Agent system): ~5-7 days
- Phase 3B (Guardrailed bidding): ~3-4 days
- Phase 3C (Compliance engine): ~2-3 days
- Phase 3D (Financial risk containment): ~2-3 days
- Phase 3E (Cross-platform intelligence): ~3-4 days
- Phase 4 (RAG): ~2-3 days
- Phase 5 (Data moat): ~3-4 days
- Phase 6 (Security): ~2-3 days (woven throughout)
- Phase 7 (Docs -- 10 documents): ~4-5 days
- Phase 8 (Launch package): ~1-2 days
- **Total: ~35-49 days of AI-driven build time**

---

### Token Consumption Estimate (to build + test the entire platform)

**What generates tokens:**

- Each AI interaction (prompt + response): ~4K-10K tokens average
- Code generation interactions (writing files): ~6K-12K tokens
- Debugging / test-fix cycles: ~3K-8K tokens
- Documentation generation (long-form): ~8K-15K tokens per doc

**Estimated interactions by phase:**


| Phase                                        | Interactions   | Avg Tokens/Interaction | Input Tokens | Output Tokens |
| -------------------------------------------- | -------------- | ---------------------- | ------------ | ------------- |
| Phase 0-1: Foundation                        | ~60-80         | ~6K                    | ~240K        | ~240K         |
| Phase 2: Platform integrations (9 platforms) | ~120-160       | ~8K                    | ~640K        | ~640K         |
| Phase 3: Agent system (6 agents + tools)     | ~100-140       | ~8K                    | ~560K        | ~560K         |
| Phase 3B: Guardrailed bidding                | ~50-70         | ~7K                    | ~245K        | ~245K         |
| Phase 3C: Compliance engine                  | ~40-60         | ~7K                    | ~210K        | ~210K         |
| Phase 3D: Financial risk containment         | ~40-60         | ~7K                    | ~210K        | ~210K         |
| Phase 3E: Cross-platform intelligence        | ~50-70         | ~8K                    | ~280K        | ~280K         |
| Phase 4: RAG layer                           | ~40-60         | ~7K                    | ~210K        | ~210K         |
| Phase 5: Data moat engine                    | ~50-70         | ~8K                    | ~280K        | ~280K         |
| Phase 6: Security                            | ~40-60         | ~7K                    | ~210K        | ~210K         |
| Phase 7: Docs (10 documents)                 | ~80-120        | ~12K                   | ~600K        | ~600K         |
| Phase 8: Launch package                      | ~30-40         | ~8K                    | ~160K        | ~160K         |
| Testing + debugging cycles                   | ~150-250       | ~6K                    | ~600K        | ~600K         |
| **TOTAL**                                    | **~850-1,240** |                        | **~4.4M**    | **~4.4M**     |


**Total estimated token consumption: ~8.8M tokens (4.4M input + 4.4M output)**

Conservative high estimate (more debugging, iteration): **~12M tokens (6M input + 6M output)**

---

### Cost Comparison: Claude Opus 4.6 vs Google Gemini 3.1 Pro

**Model pricing (as of February 2026):**


| Model                         | Input (per 1M tokens) | Output (per 1M tokens) |
| ----------------------------- | --------------------- | ---------------------- |
| Claude Opus 4.6               | $5.00                 | $25.00                 |
| Google Gemini 3.1 Pro Preview | $2.00                 | $12.00                 |


**Estimated cost to build the ENTIRE platform (code + tests + docs):**


| Scenario                           | Input Tokens | Output Tokens | Claude Opus 4.6 | Gemini 3.1 Pro |
| ---------------------------------- | ------------ | ------------- | --------------- | -------------- |
| **Base estimate**                  | 4.4M         | 4.4M          | **$132**        | **$62**        |
| **High estimate**                  | 6M           | 6M            | **$180**        | **$84**        |
| **Worst case** (lots of iteration) | 8M           | 8M            | **$240**        | **$112**       |


**Breakdown (base estimate):**

- Claude Opus 4.6: (4.4M x $5/1M) + (4.4M x $25/1M) = $22 + $110 = **$132**
- Gemini 3.1 Pro: (4.4M x $2/1M) + (4.4M x $12/1M) = $8.80 + $52.80 = **$62**

**Claude Opus 4.6 is ~2.1x more expensive than Gemini 3.1 Pro.**

---

### BUT: If You're Using Cursor (Recommended)

If you build this through Cursor IDE (which you're using now), you do NOT pay per-token directly. Cursor subscription pricing:


| Plan  | Monthly Cost | What You Get                                  |
| ----- | ------------ | --------------------------------------------- |
| Pro   | $20/mo       | 500 fast premium requests + unlimited slow    |
| Pro+  | $60/mo       | 3x usage (effectively ~1,500 fast requests)   |
| Ultra | $200/mo      | 20x usage (effectively ~10,000 fast requests) |


At ~850-1,240 total interactions to build this project:

- **Cursor Pro ($20/mo)**: Would take ~2-3 months (500 fast requests/mo), some in slow queue. **Total: ~$40-60**
- **Cursor Pro+ ($60/mo)**: Would complete in ~1 month. **Total: ~$60**
- **Cursor Ultra ($200/mo)**: Would complete in ~1 month with zero queuing. **Total: ~$200**

**Using Cursor is dramatically cheaper than direct API calls** because the subscription absorbs the per-token cost. The model choice (Claude vs Gemini) is handled by Cursor's routing -- you get access to both.

---

### Runtime LLM costs (per user per month, once the platform is deployed):

These are the costs YOUR USERS will generate when they use the platform (paid via your OpenAI/Anthropic API key):

- Light usage (10 campaigns/mo): ~$2-5/mo in LLM tokens
- Medium usage (50 campaigns/mo): ~$10-25/mo
- Heavy usage (200+ campaigns/mo): ~$50-100/mo


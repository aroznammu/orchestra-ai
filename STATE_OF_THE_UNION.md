# OrchestraAI -- State of the Union

**Generated:** 2026-02-28
**Reference Plan:** `ai_marketing_platform_5fc51575.plan.md`
**Test Suite:** 145 tests, all passing

---

## 1. Executive Summary

OrchestraAI is a **functional MVP with genuine depth in several subsystems, but critical integration seams remain incomplete**. The project has moved well past the "skeleton" stage -- there is a real LangGraph multi-agent orchestrator with conditional routing, 9 fully-implemented platform connectors making real HTTP calls to production APIs, a working Qdrant-backed RAG pipeline, statistical optimization algorithms (Thompson Sampling, UCB, Bayesian budget allocation), and a 3-phase autonomy bidding engine. The documentation layer is strong: 10 substantial strategy and architecture documents, real CI/CD workflows, a multi-stage Dockerfile, and developer-facing scripts.

However, several key integration points that would make this a production system are broken or stubbed. The most impactful: `request.state.user` is never populated by the auth middleware, which silently breaks the audit trail (every request logs `user_id=None`), tenant-based rate limiting (always falls back to IP-based), and GDPR scoping. The encryption layer uses Fernet (AES-128-CBC + HMAC) rather than the AES-256-GCM specified in the plan. GDPR export and deletion endpoints operate on in-memory stores rather than PostgreSQL. The scheduler is an empty APScheduler shell with no registered jobs. Intent classification in the orchestrator is keyword-based substring matching, not the LLM-based classification the plan calls for. The analytics agent and all analytics tools return placeholder zeros.

The codebase has 145 passing tests, but the test structure is flat (all in `tests/`) rather than the domain-grouped subdirectories (`test_agents/`, `test_platforms/`, `test_api/`, `test_rag/`) specified in the plan. Three API route modules from the plan -- `campaigns.py`, `analytics.py`, `reports.py` -- are missing entirely; those flows are partially absorbed by the orchestrator endpoint. There is no `plugins/example_plugin/` directory.

---

## 2. Implementation Matrix (Phase by Phase)

| Phase | Description | Status | Key Evidence |
|-------|-------------|--------|-------------|
| **Phase 0** | Project Foundation | **Complete** | `pyproject.toml`, `docker-compose.yml`, `Makefile`, `.env.example`, `.gitignore` all present and functional |
| **Phase 1** | Core Infrastructure | **Complete (with gaps)** | FastAPI app, config, models, Alembic, Redis, JWT auth, audit middleware, CLI all exist. Gaps: `request.state.user` never set; API key auth passes key to JWT decoder (will fail for non-JWT keys); DB pool sizes hardcoded |
| **Phase 2** | Platform Integrations | **Complete** | All 9 connectors implemented with real OAuth2 flows, HTTP calls, retry logic, and rate limit handling. Twitter and YouTube original; TikTok, Pinterest, Facebook, Instagram, LinkedIn, Snapchat, Google Ads newly implemented |
| **Phase 3** | AI Agent System | **Partial** | LangGraph `StateGraph` with 8 nodes and conditional routing is real. Intent classification is keyword-based (not LLM). Content agent makes real LLM calls (OpenAI/Anthropic/Ollama with fallback). Analytics agent logic is real but returns placeholder zeros. Content tools (`generate_caption`, `optimize_hashtags`) and all analytics tools are stubs |
| **Phase 3B** | Guardrailed Bidding | **Partial** | 3-phase autonomy model works in `engine.py`. `guardrails.py` and `kill_switch.py` are real. `approval.py` has real workflow but stub notifications (webhook/email only log). Files `semi_auto.py` and `autonomous.py` do not exist (logic consolidated into `engine.py`). Logic bug at lines 134-140 of `engine.py`: `elif` branches are unreachable |
| **Phase 3C** | Compliance Engine | **Partial** | `tos_rules.py` has real per-platform rules for all 9 platforms. `content_validator.py` does real keyword-based risk scoring. `rate_limiter.py` works but is in-memory only. `policy_monitor.py` has manual change recording but no automated changelog fetching. `restrictions.py` defines restrictions but enforcement depends on call-site integration |
| **Phase 3D** | Financial Risk | **Partial** | `spend_caps.py` has real 3-tier cap enforcement. `anomaly.py` has real z-score and IQR detection. `velocity.py` has real spike detection but baseline update is never scheduled. `alerts.py` fires at correct thresholds but delivers to logs only. `rollback.py` tracks rollback records but does not revert platform state |
| **Phase 3E** | Cross-Platform Intelligence | **Complete** | All 5 modules contain real algorithmic logic: ROI normalization with platform-specific CPM baselines, marginal return curves (logarithmic model), budget allocation with constraints, channel saturation detection, and multi-touch attribution (5 models including position-based and time-decay) |
| **Phase 4** | RAG Layer | **Complete** | Real Qdrant `AsyncQdrantClient` integration. Embedding pipeline with OpenAI/Ollama/hash fallback. Semantic retriever with re-ranking. Campaign indexer with GDPR deletion. Long-term memory (short-term in-memory ring buffer + long-term Qdrant). Redis layer mentioned in docstring is not implemented |
| **Phase 5** | Data Moat Engine | **Complete** | Real flywheel pipeline wired to RAG and signals. Per-platform engagement normalization with attention decay curves. Tenant-specific model learning from campaign embeddings. Global model with Laplace noise differential privacy (epsilon=1). Performance-weighted embeddings with tier clustering |
| **Phase 6** | Security & Compliance | **Partial** | Encryption is Fernet (AES-128-CBC + HMAC), not AES-256-GCM. `encryption_key` config field is defined but never used. Encryption only applied to OAuth tokens in `security/oauth.py`. RBAC works but role comes from JWT, not synced from DB. GDPR export/deletion operates on in-memory stores; PostgreSQL data is not cleaned. Audit trail does fire-and-forget DB writes (errors logged at debug). Auth fallback returns owner-level JWT when DB is unavailable |
| **Phase 7** | Documentation | **Complete** | 10 substantial documents covering architecture, viral strategy, data moat, due diligence, cost analysis, security compliance, user procedures, launch strategy, differentiation, and guardrailed bidding |
| **Phase 8** | GitHub Launch Package | **Complete** | README with feature table and quick start. CONTRIBUTING guide. Issue templates (YAML). CI/CD workflows (lint, test, release, Docker). Multi-stage Dockerfile. Apache 2.0 license. Setup scripts (bash + PowerShell). Demo script |

---

## 3. Deep Dive: What is Actually Built

### 3.1 The Agent Graph

The orchestrator (`src/orchestra/agents/orchestrator.py`) is a **genuine LangGraph `StateGraph`**, not a linear script. It defines 8 nodes and uses conditional edges to route between them:

```
classify -> compliance_gate -> [content_node | analytics_node | optimize_node | respond]
content_node -> policy_node -> [platform_node | respond]
platform_node -> respond -> END
analytics_node -> respond -> END
optimize_node -> respond -> END
```

**What works:**
- `StateGraph` compilation with proper `add_node` and `add_conditional_edges`
- Compliance gate runs before any action (real rule-based checks: prohibited content, targeting, budget)
- Content agent makes real LLM calls via OpenAI, Anthropic, and Ollama with automatic fallback
- Platform agent dispatches to real platform connectors via the registry
- Safety module enforces max depth (10), max calls per trace (50), same-agent loop detection (>3), and timeout (120s)
- Execution tracing records duration, cost, tokens, and agents involved

**What is stubbed or missing:**
- **Intent classification** uses `INTENT_KEYWORDS` dictionary with simple substring matching. The plan specifies LLM-based classification. The code includes the comment "LLM upgrade later."
- **Analytics agent** has correct aggregation and insight-generation logic but initializes all platform metrics to zero. It never calls platform connectors to fetch real data.
- **Content tools** `generate_caption` and `optimize_hashtags` return empty results with notes like "LLM will generate the actual caption using this spec." They do not invoke any LLM.
- **Analytics tools** `get_cross_platform_metrics`, `get_campaign_performance`, and `generate_report` return hardcoded placeholder objects.

### 3.2 Database and Config

**Models (`src/orchestra/db/models.py`):** 9 SQLAlchemy models with proper indexes:
- `Tenant`, `User`, `PlatformConnection`, `Campaign`, `CampaignPost`, `AuditLog`, `Experiment`, `KillSwitchEventLog`, `SpendRecord`
- Relationships defined for Tenant -> users/campaigns/connections, Campaign -> posts/experiments
- Gaps: `AuditLog.tenant_id` is nullable; `KillSwitchEventLog.tenant_id` is `String(255)` instead of a UUID foreign key; `CampaignPost` has no direct `tenant_id` (isolation must traverse through `Campaign`)

**Session (`src/orchestra/db/session.py`):** Async engine with `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`. Properly yields sessions with commit/rollback/close. Pool sizes are hardcoded rather than configurable via env.

**Config (`src/orchestra/config.py`):** Pydantic Settings loads all `.env` vars correctly. All Tier 1-4 fields are present. The field `encryption_key` is defined as `SecretStr` but is never referenced by any other module -- only `fernet_key` is used.

### 3.3 Security Layer

**Encryption (`src/orchestra/security/encryption.py`):** Uses `cryptography.fernet.Fernet`, which is **AES-128-CBC with HMAC-SHA256** -- not the AES-256-GCM that the plan implies. The `encryption_key` config field (which could be used for AES-256) is unused. A critical behavior: if `fernet_key` starts with `"CHANGE-ME"`, a new key is generated at runtime. This means tokens encrypted before a restart cannot be decrypted after restart if the default config is used. The production `.env` has a real Fernet key, so this is only a risk in misconfigured environments.

**Encryption coverage:** Only OAuth access and refresh tokens are encrypted (via `security/oauth.py`). No other database fields (user data, audit entries, campaign content) are encrypted at rest.

**Auth middleware (`src/orchestra/api/middleware/auth.py`):**
- JWT creation and validation work correctly with bcrypt password hashing
- `get_current_user` accepts both Bearer token and `X-API-Key`, but both are passed to `decode_access_token()` which expects a JWT. Non-JWT API keys will always fail
- **`request.state.user` is never set.** The auth dependency returns a `TokenPayload`, but no middleware populates `request.state`. This means the audit middleware (`audit.py`) always logs `user_id=None` and `tenant_id=None`, and the rate limiter always falls back to IP-based limiting

**Auth fallback:** In `api/routes/auth.py`, if the database is unavailable during `/register` or `/login`, the code falls back to returning a JWT for a random UUID with role `"owner"`. This means anyone can obtain owner-level access during a database outage.

**GDPR (`src/orchestra/security/gdpr.py`):** Export and deletion request tracking is in-memory (lost on restart). `_collect_tenant_data` returns empty lists for all data categories. `_delete_tenant_data` only calls the Qdrant indexer cleanup -- PostgreSQL tables (users, campaigns, connections, audit logs, spend records) are not touched.

### 3.4 Platform Connectors

All 9 connectors are **real implementations** making actual HTTP calls to production APIs:

| Connector | API | OAuth | Publish | Analytics | Audience |
|-----------|-----|-------|---------|-----------|----------|
| **Twitter** | Twitter API v2 | OAuth 2.0 PKCE | Tweet creation | Public/non-public metrics | Follower counts |
| **YouTube** | YouTube Data API v3 | Google OAuth | Resumable video upload | View/like/comment counts | Subscriber/view counts |
| **TikTok** | TikTok API v2 | OAuth 2.0 | Video publish (pull-from-URL) | Like/comment/share/view counts | Follower/following/likes |
| **Pinterest** | Pinterest API v5 | OAuth 2.0 + Basic Auth | Pin creation with board | 30-day impressions/clicks/saves | Follower/pin/monthly views |
| **Facebook** | Meta Graph API v19.0 | OAuth 2.0 (long-lived) | Page posts/photos/videos + scheduling | Post insights (impressions/reach/clicks) | Page follower data |
| **Instagram** | Instagram Graph API v19.0 | OAuth 2.0 via Meta | Container-based upload (image/video/carousel) | Impressions/reach/saves/shares | Demographics (gender/age segments) |
| **LinkedIn** | LinkedIn API v2 | OAuth 2.0 (3-legged) | UGC posts with article sharing | Social actions (likes/comments/shares) | OIDC profile info |
| **Snapchat** | Marketing API v1 | OAuth 2.0 | Snap Ad creative creation | Campaign impressions/swipes/video views | Organization metadata |
| **Google Ads** | Google Ads API v16 | Google OAuth 2.0 | Responsive Search Ad creation | GAQL campaign queries | Customer account info |

All connectors share: retry with exponential backoff (tenacity, 3 attempts, 2-30s), rate limit detection (429 + retry-after), content validation against platform limits, structured logging via structlog.

---

## 4. Architectural Drift and Technical Debt

### 4.1 Encryption: Fernet vs AES-256-GCM

The plan references AES-256-GCM encryption. The implementation uses Fernet (AES-128-CBC + HMAC-SHA256). The `encryption_key` config field exists and is populated in `.env` but is never imported or used by any module.

### 4.2 Missing Files from Plan

| Planned Path | Status |
|-------------|--------|
| `bidding/semi_auto.py` | Does not exist (logic consolidated into `engine.py`) |
| `bidding/autonomous.py` | Does not exist (logic consolidated into `engine.py`) |
| `api/routes/campaigns.py` | Does not exist (partially handled by orchestrator route) |
| `api/routes/analytics.py` | Does not exist (partially handled by orchestrator route) |
| `api/routes/reports.py` | Does not exist (partially handled by orchestrator route) |
| `plugins/example_plugin/` | Entire directory missing |
| `tests/test_agents/` | Does not exist (tests are in flat `tests/` dir) |
| `tests/test_platforms/` | Does not exist |
| `tests/test_api/` | Does not exist |
| `tests/test_rag/` | Does not exist |

### 4.3 Intent Classification: Keywords vs LLM

The plan specifies intelligent intent routing. The orchestrator uses a static `INTENT_KEYWORDS` dictionary with substring matching (line 41-60 of `orchestrator.py`). Unknown inputs default to `GET_ANALYTICS`. The content agent has a working LLM call chain (OpenAI -> Anthropic -> Ollama) that could be reused for intent classification but is not.

### 4.4 Scheduler: Empty Shell

`src/orchestra/core/scheduler.py` creates an `AsyncIOScheduler` and exposes `start_scheduler()`/`stop_scheduler()`, but **no jobs are ever registered**. No scheduled tasks exist for:
- Daily spend cap resets (`risk/spend_caps.py` has `reset_daily()` but nothing calls it)
- Velocity baseline updates (`risk/velocity.py` has `update_baseline()` but nothing calls it)
- Token refresh cycles
- Scheduled post publishing
- Policy monitor checks

### 4.5 Auth Pipeline Broken Seam

`request.state.user` is never populated. The `get_current_user` dependency returns a `TokenPayload` to individual route handlers, but the ASGI middleware layer (`audit.py`, `rate_limit.py`) checks `request.state.user` which is always `None`. This means:
- Every API request is logged in the audit trail with `user_id=None`
- Rate limiting always uses IP-based keys, never tenant-based
- GDPR endpoints cannot scope data to the authenticated tenant

### 4.6 Bidding Engine Logic Bug

In `bidding/engine.py` lines 134-140:
```python
auto_approved = False
if not requires_approval:
    auto_approved = True
elif self.phase == AutonomyPhase.SEMI_AUTONOMOUS and not requires_approval:
    auto_approved = True
elif self.phase == AutonomyPhase.CONTROLLED_AUTONOMOUS:
    auto_approved = not requires_approval
```
The first `if` catches all cases where `not requires_approval`, making the `elif` branches unreachable. The semi-autonomous and controlled-autonomous phases never execute their own approval logic.

### 4.7 Cost Router: No Tiered Video Pipeline

`src/orchestra/core/cost_router.py` routes by `TaskComplexity` (SIMPLE/MODERATE/COMPLEX) to model names from config. There is no "Tiered Video Pipeline" or special handling for video/media content as the plan implies. Routing is by capability tier, not by content type.

### 4.8 GDPR: In-Memory Only

GDPR export requests, deletion requests, and consent records are stored in Python dictionaries within the `GDPRManager` instance. A process restart loses all records. The actual data export returns empty lists for every category. The actual data deletion only cleans Qdrant vectors -- no PostgreSQL rows are touched.

### 4.9 Hardcoded Values

| Location | Value | Should Be |
|----------|-------|-----------|
| `db/session.py` | `pool_size=20`, `max_overflow=10` | Configurable via env |
| `agents/safety.py` | `max_calls=50`, `timeout=120`, `loop_threshold=3` | Configurable |
| `compliance/rate_limiter.py` | `buffer_pct=0.15` (15% below platform max) | Configurable per tenant |
| `risk/anomaly.py` | `z_threshold=2.5`, `iqr_multiplier=1.5` | Configurable |

---

## 5. The Upgrade Roadmap (Next 3 Steps)

### Step 1: Wire `request.state.user` and Fix the Auth Pipeline

**Priority:** Critical -- this single fix unlocks tenant isolation across audit, rate limiting, and GDPR.

**Prompt for Cursor:**

> In `src/orchestra/main.py`, add an ASGI middleware (or modify the existing middleware stack) that runs AFTER the request is received but BEFORE the audit and rate-limit middleware. This middleware should:
>
> 1. Extract the Bearer token or X-API-Key from the request headers.
> 2. If present, decode it via `decode_access_token()` from `api/middleware/auth.py`.
> 3. If decoding succeeds, set `request.state.user` to the resulting `TokenPayload`.
> 4. If decoding fails or no token is present, leave `request.state.user` as `None` (unauthenticated requests should still pass through to public endpoints).
>
> Then update `api/middleware/audit.py` and `api/middleware/rate_limit.py` to safely read `request.state.user` (they may already do this -- verify they handle `None` gracefully).
>
> Also fix the API key path in `get_current_user`: add a separate API key lookup (check a database table or config list) instead of passing the raw API key string to `decode_access_token()`.
>
> Also remove the auth fallback in `api/routes/auth.py` that returns an owner-level JWT when the database is unavailable. Return a 503 Service Unavailable instead.
>
> Write tests that verify: (a) `request.state.user` is populated for authenticated requests, (b) audit log entries include the real `user_id` and `tenant_id`, (c) rate limiting uses tenant-based keys when authenticated, (d) unauthenticated requests to public endpoints still work.

### Step 2: Replace Keyword Intent Classification with LLM-Based

**Priority:** High -- the orchestrator is the core product; keyword matching cannot handle real user input.

**Prompt for Cursor:**

> In `src/orchestra/agents/orchestrator.py`, replace the `classify_intent` function. Currently it uses `INTENT_KEYWORDS` dictionary with substring matching (lines 41-80). Replace it with an LLM-based classifier that:
>
> 1. Uses the existing `route_model()` from `core/cost_router.py` to select a model (SIMPLE tier -- use `gpt-4o-mini` or Ollama fallback).
> 2. Uses the same LLM call pattern already proven in `agents/content.py` (`_call_openai`, `_call_ollama`, `_call_anthropic` with fallback chain).
> 3. Sends a structured prompt with the list of `IntentType` enum values and asks the LLM to classify the user's input.
> 4. Parses the response to extract the `IntentType`.
> 5. Falls back to the existing keyword matching if all LLM providers fail (network error, timeout, etc.).
> 6. Caches recent classifications in-memory to avoid redundant LLM calls for identical inputs.
>
> Keep the `INTENT_KEYWORDS` as the fallback. Add the `classify_intent` function as an async function (it currently is sync).
>
> Update `tests/test_orchestrator.py` to test: (a) LLM classification returns correct intents for natural language inputs, (b) fallback to keyword matching works when LLM is unavailable, (c) caching prevents duplicate LLM calls.

### Step 3: Implement Campaign, Analytics, and Reports Routes with Real Data

**Priority:** High -- without these, the platform has no CRUD API for its core domain objects.

**Prompt for Cursor:**

> Create three new route modules in `src/orchestra/api/routes/`:
>
> **`campaigns.py`** -- CRUD endpoints for campaigns:
> - `POST /campaigns` -- create a campaign (name, platforms, budget, targets, schedule)
> - `GET /campaigns` -- list campaigns for the authenticated tenant
> - `GET /campaigns/{id}` -- get campaign details with posts and status
> - `PATCH /campaigns/{id}` -- update campaign settings
> - `POST /campaigns/{id}/launch` -- launch a campaign (triggers orchestrator)
> - `POST /campaigns/{id}/pause` -- pause a running campaign
> - All endpoints require auth via `Depends(get_current_user)` and enforce tenant isolation
> - Use the `Campaign` and `CampaignPost` models from `db/models.py`
>
> **`analytics.py`** -- cross-platform analytics endpoints:
> - `GET /analytics/overview` -- aggregated metrics across all platforms for the tenant
> - `GET /analytics/platform/{platform}` -- platform-specific metrics
> - `GET /analytics/campaign/{id}` -- campaign-level metrics
> - Wire these to actually call `connector.get_analytics()` on each connected platform via `PlatformConnection` records in the DB, instead of returning placeholder zeros
>
> **`reports.py`** -- AI-generated report endpoints:
> - `POST /reports/generate` -- trigger an AI-generated performance report using the content agent
> - `GET /reports/{id}` -- retrieve a generated report
>
> Register all three routers in `src/orchestra/main.py`. Update the analytics agent (`agents/analytics_agent.py`) to fetch real platform data by iterating over the tenant's `PlatformConnection` records and calling each connector's `get_analytics()` method.
>
> Write tests for: (a) campaign CRUD lifecycle, (b) analytics returns real structure (even if platforms aren't connected, it should return zeros gracefully), (c) tenant isolation (user A cannot see user B's campaigns).

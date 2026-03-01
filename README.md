# OrchestraAI

**AI-Native Marketing Orchestration Platform**

> One AI brain. Nine platforms. Zero guesswork.

OrchestraAI is an open-source, self-hostable platform that uses multi-agent AI to orchestrate marketing campaigns across 9 social and search platforms simultaneously. It sees what no single platform can: where your next dollar produces the best return -- everywhere.

<!--
NOTE: This repository is currently PRIVATE (stealth mode).
Badges, deploy buttons, and public links will be added before public launch.
-->

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent AI** | LangGraph orchestrator with 6 specialized agents (compliance, content, optimization, analytics, policy, platform) |
| **9 Platform Connectors** | Twitter/X, YouTube, Facebook, Instagram, LinkedIn, TikTok, Pinterest, Snapchat, Google Ads |
| **Cross-Platform Intelligence** | Unified ROI, marginal return analysis, multi-touch attribution -- what no single platform can see |
| **Guardrailed Bidding** | 3-phase autonomy model: Hard Guardrail -> Semi-Autonomous -> Controlled Autonomous |
| **Data Flywheel** | Every campaign makes the system smarter (performance-weighted embeddings) |
| **Kill Switch** | Instant halt of all spend via API, CLI, or dashboard |
| **GDPR/CCPA Ready** | Data export, deletion, consent tracking built-in |
| **Self-Hostable** | Docker Compose for local, full production deployment support |

## Architecture

```
User Request (API / CLI)
        |
   [Orchestrator]
        |
   classify_intent
        |
   compliance_gate  ← always runs first
        |
   ┌────┴────────────┐
content    analytics    optimize
   └────┬────────────┘
        |
     respond
```

### Tech Stack

- **Python 3.12+** / **FastAPI** / **Pydantic v2**
- **LangGraph** + **LangChain** -- multi-agent orchestration
- **Qdrant** -- vector database for RAG and performance embeddings
- **PostgreSQL 16** -- relational data with multi-tenant isolation
- **Redis 7** -- caching + real-time event bus (Streams)
- **Apache Kafka 3.8** -- durable event bus (KRaft, no Zookeeper)
- **Ollama** -- local LLM serving (free, no API key needed)
- **SQLAlchemy 2.0** (async) / **Alembic** -- ORM + migrations

## Quick Start

```bash
# Clone and configure
git clone <repository-url>
cd orchestra-ai
cp .env.example .env

# Start infrastructure
docker compose up -d

# Install dependencies
pip install poetry
poetry install

# Run migrations
poetry run alembic upgrade head

# Start the API
poetry run uvicorn orchestra.main:app --reload
```

API available at `http://localhost:8000`
Docs at `http://localhost:8000/docs` (debug mode)

### Using the CLI

```bash
poetry run orchestra version
poetry run orchestra status
poetry run orchestra campaign list
poetry run orchestra connect add twitter
```

## Platform Support

| Platform | Status | API Access |
|----------|--------|-----------|
| X/Twitter | Full | Paid ($100/mo Basic) |
| YouTube | Full | Free (Google Cloud project) |
| Pinterest | Stub | Free, easy approval |
| TikTok | Stub | Developer portal |
| Facebook | Stub | Meta business verification |
| Instagram | Stub | Meta business verification |
| LinkedIn | Stub | Partner approval |
| Snapchat | Stub | Marketing API approval |
| Google Ads | Stub | Developer token |

## Project Structure

```
src/orchestra/
├── api/           # FastAPI routes + middleware (auth, audit, rate limit)
├── agents/        # LangGraph orchestrator + 6 specialized agents + tools
├── bidding/       # 3-phase guardrailed bidding engine
├── cli/           # Typer CLI (campaign, connect, optimize, report)
├── compliance/    # Platform ToS rules, content validation, restrictions
├── core/          # Event bus, scheduler, cost router, exceptions
├── db/            # SQLAlchemy models, Alembic migrations
├── intelligence/  # Cross-platform ROI, attribution, budget allocation
├── moat/          # Data flywheel, signals, performance embeddings
├── platforms/     # 9 platform connectors (abstract base + implementations)
├── rag/           # Qdrant store, embeddings, retriever, agent memory
├── risk/          # Spend caps, anomaly detection, alerts, rollback
└── security/      # RBAC, GDPR/CCPA, encryption, audit trail
docs/
├── architecture.md
├── cost-analysis.md
├── data-moat.md
├── differentiation.md
├── due-diligence.md
├── guardrailed-bidding.md
├── launch-strategy.md
├── security-compliance.md
├── user-procedures.md
└── viral-strategy.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe (checks DB) |
| `/api/v1/auth/register` | POST | Register user + tenant |
| `/api/v1/auth/login` | POST | Authenticate, get JWT |
| `/api/v1/orchestrator` | POST | Run AI agent orchestration |
| `/api/v1/platforms/connections` | GET | List connected platforms |
| `/api/v1/platforms/auth/init` | POST | Start OAuth flow |
| `/api/v1/gdpr/export` | POST | Request data export |
| `/api/v1/gdpr/delete` | POST | Request data deletion |
| `/api/v1/audit` | GET | Query audit log |
| `/api/v1/kill-switch/activate` | POST | Emergency spend halt |

## Safety & Guardrails

- **14 hard-coded restrictions** that cannot be overridden by any agent or configuration
- **3-tier spend caps**: global, per-platform, per-campaign
- **Anomaly detection**: Z-score + IQR on spend patterns
- **Kill switch**: Global + per-tenant, instant halt
- **Content validation**: Risk scoring 0-100, human review mode
- **Compliance engine**: Machine-readable ToS for all 9 platforms
- **Full audit trail**: Every action logged with reasoning and outcome

## Documentation

See the [`docs/`](docs/) folder for detailed documentation:

- [Architecture](docs/architecture.md)
- [User Procedures](docs/user-procedures.md)
- [Security & Compliance](docs/security-compliance.md)
- [Guardrailed Bidding](docs/guardrailed-bidding.md)
- [Data Moat](docs/data-moat.md)
- [Cost Analysis](docs/cost-analysis.md)
- [Differentiation](docs/differentiation.md)

## License

Apache License 2.0 -- see [LICENSE](LICENSE) for details.

Open-core model: Community edition is full-featured. Enterprise adds SSO, advanced analytics, and SLA.

---

*Built with LangGraph, FastAPI, and a belief that marketing AI should be transparent, guardrailed, and open.*

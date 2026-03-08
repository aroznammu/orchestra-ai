# User Procedures & Operations Guide

**OrchestraAI** — AI-Native Marketing Orchestration Platform

---

## 1. Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ (3.12 recommended) | Runtime |
| Docker Desktop | Latest | Infrastructure services |
| Git | 2.x+ | Source control |
| pip / Poetry | pip 23+ or Poetry 1.7+ | Package management |

Optional but recommended:
- **Ollama** — local LLM inference (fallback when OpenAI/Anthropic unavailable)
- **curl** or **httpx** — for direct API testing

---

## 2. Installation

### Clone the Repository

```bash
git clone https://github.com/orchestraai/orchestraai.git
cd orchestraai
```

### Install Python Dependencies

```bash
# Using pip (editable install)
pip install -e ".[dev]"

# Or using Poetry
poetry install --with dev
```

This installs the `orchestra` CLI globally (registered via `pyproject.toml` entry point `orchestra = "orchestra.cli.app:app"`).

### Start Infrastructure with Docker Compose

```bash
docker compose up -d
```

This starts 6 services:

| Service | Port | Purpose |
|---------|------|---------|
| **app** | 8000 | FastAPI server |
| **postgres** | 5432 | Primary database |
| **redis** | 6379 | Cache + rate limiting |
| **qdrant** | 6333 | Vector database (RAG) |
| **kafka** | 9092 | Event bus |
| **ollama** | 11434 | Local LLM inference |

---

## 3. Environment Configuration

Copy the example environment file and configure credentials:

```bash
cp .env.example .env
```

### Key Variable Groups

| Group | Variables | Notes |
|-------|----------|-------|
| **Core** | `APP_ENV`, `DEBUG`, `SECRET_KEY` | |
| **Database** | `DATABASE_URL` | `postgresql+asyncpg://...` |
| **Redis** | `REDIS_URL` | `redis://localhost:6379/0` |
| **JWT** | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Min 32-char secret |
| **Encryption** | `FERNET_KEY` | Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| **AI (Tier 1-3)** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL` | Fallback chain |
| **Vector DB** | `QDRANT_URL` | `http://localhost:6333` |
| **Platform OAuth** | `TWITTER_CLIENT_ID/SECRET`, `FACEBOOK_APP_ID/SECRET`, `GOOGLE_CLIENT_ID/SECRET`, ... | See `.env.example` for all 9 |

---

## 4. Starting the Server

### Option A: Docker (recommended for production-like setup)

```bash
docker compose up -d
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs` (debug mode only).

### Option B: Local uvicorn (for development)

```bash
# Ensure Postgres, Redis, and Qdrant are running (via Docker or locally)
uvicorn orchestra.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify the Server

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "0.1.0"}
```

---

## 5. CLI Quick Start

The `orchestra` CLI is a Typer application (`src/orchestra/cli/app.py`) with Rich output formatting. Configuration is stored at `~/.orchestra/config.json`.

### Register a New Account

```bash
$ orchestra auth register

  Email: alice@example.com
  Password (min 8 chars): ********
  Full name: Alice Johnson
  Organization name: Acme Corp

  Registration successful! You are now logged in.
```

### Log In

```bash
$ orchestra auth login
  Email: alice@example.com
  Password: ********
  Login successful! Token saved to ~/.orchestra/config.json

# Or with flags: --email, --password, --api-key, --url
```

### Other Auth Commands

```bash
$ orchestra auth whoami    # Show current user (ID, email, role, tenant)
$ orchestra auth logout    # Clear stored credentials
```

---

## 6. Campaign Management

### Create a Campaign

```bash
$ orchestra campaign create

  Campaign name: Q1 Product Launch
  Description (optional): Cross-platform launch for new SaaS product
  Platforms (comma-separated): twitter,linkedin,instagram
  Budget (USD): 5000

  ╭──────────────── New Campaign ────────────────╮
  │ Campaign created!                             │
  │                                               │
  │   ID:        a1b2c3d4-e5f6-7890-abcd-...     │
  │   Name:      Q1 Product Launch                │
  │   Status:    draft                            │
  │   Platforms: twitter, linkedin, instagram     │
  │   Budget:    $5,000.00                        │
  ╰───────────────────────────────────────────────╯
```

### List Campaigns

```bash
$ orchestra campaign list

  ┌──────────────────── Campaigns (3) ────────────────────┐
  │ Name               │ Status │ Platforms  │ Budget     │
  ├────────────────────┼────────┼────────────┼────────────┤
  │ Q1 Product Launch  │ draft  │ tw, li, ig │ $5,000.00  │
  │ Blog Promotion     │ active │ twitter    │ $1,200.00  │
  │ Brand Awareness    │ paused │ fb, ig     │ $3,000.00  │
  └────────────────────┴────────┴────────────┴────────────┘
```

### Get Campaign Details

```bash
$ orchestra campaign get a1b2c3d4
```

### Launch / Pause a Campaign

```bash
$ orchestra campaign launch a1b2c3d4
  Campaign launched! Status: active

$ orchestra campaign pause a1b2c3d4
  Campaign paused. Status: paused
```

---

## 7. Analytics Dashboard

```bash
$ orchestra analytics --days 30
```

Displays a Rich-formatted panel with total impressions, engagement, clicks, spend, and average engagement rate, plus a per-platform breakdown table.

---

## 8. AI Assistant

The `orchestra ask` command sends natural-language instructions to the LangGraph orchestrator agent, which classifies intent and routes to the appropriate agent (content, analytics, optimization, or platform).

```bash
$ orchestra ask "Write a Twitter thread about our Q1 results"

  You: Write a Twitter thread about our Q1 results

  Intent: GENERATE_CONTENT
  Compliance: passed

  ╭──────────── Generated Content ────────────╮
  │ 1/ Q1 was a record quarter for us.        │
  │ Revenue up 45%, customer base grew 3x.    │
  │                                           │
  │ Here's the thread on what we learned...   │
  ╰───────────────────────────────────────────╯

  trace_id: tr_a1b2c3d4
```

### Example Prompts

| Prompt | Routed To |
|--------|-----------|
| `"Write a LinkedIn post about hiring"` | Content Agent |
| `"What's our best performing platform?"` | Analytics Agent |
| `"Optimize budget allocation for next week"` | Optimization Agent |
| `"Publish the draft campaign to Twitter"` | Platform Agent |
| `"Generate a video ad for our summer sale"` | Video Agent |

---

## 9. Video Generation

The orchestrator includes an AI video generation pipeline powered by **Seedance 2.0** (ByteDance) via fal.ai.

### Generating a Video

Use natural-language prompts that include words like *video*, *video ad*, or *video clip*:

```bash
$ orchestra ask "Generate a video ad for our summer collection launch"
```

Or from the web dashboard, type the same prompt in the AI Orchestrator chat interface. The pipeline:

1. **Content node** generates supporting copy based on your prompt
2. **Video node** sends the prompt to Seedance 2.0 (text-to-video or image-to-video) and receives an MP4 URL
3. **Visual Compliance Gate** extracts keyframes from the video and scans them with GPT-4o Vision for IP violations

### What the Compliance Gate Checks

| Category | Examples |
|----------|----------|
| Celebrity likenesses | Faces resembling public figures |
| Copyrighted characters | Cartoon/anime characters, movie characters |
| Trademarked logos | Brand logos, product packaging |

### Outcomes

- **Safe**: The video player renders inline with playback controls. Download the video or use it in a campaign.
- **Blocked**: A red warning card appears listing the detected violations (category, description, confidence). The video URL is withheld. Rephrase your prompt to avoid the flagged content and try again.

### Tips

- Be specific about the scene you want: *"A cinematic drone shot of a beach resort at golden hour"* works better than *"Make a video"*.
- Avoid mentioning real brands, celebrities, or fictional characters in your prompt to reduce compliance blocks.
- Videos are 5 seconds long at 720p by default.

---

## 10. System Health

```bash
$ orchestra status

  ┌─────────── OrchestraAI System Status ───────────┐
  │ Service     │ Status │ Detail                    │
  ├─────────────┼────────┼───────────────────────────┤
  │ API Server  │   OK   │ healthy                   │
  │ PostgreSQL  │   OK   │ PostgreSQL 16.2           │
  │ Redis       │   OK   │ v7.2.4                    │
  │ Ollama      │   OK   │ 3 model(s)                │
  └─────────────┴────────┴───────────────────────────┘

  All 4 services operational.
```

The status command checks API, PostgreSQL, Redis, and Ollama with 5-second timeouts per service.

---

## 11. Connecting Platform Accounts

Platform connections use OAuth2. The flow is initiated via the API:

1. **Initiate:** `POST /api/v1/platforms/auth/init` with `{"platform": "twitter"}` → returns `auth_url` and `state`
2. **Authorize:** User visits `auth_url` in browser, grants permissions
3. **Callback:** `POST /api/v1/platforms/auth/callback` with `{"platform": "twitter", "code": "AUTH_CODE", "state": "..."}` → server exchanges code, encrypts tokens with Fernet, stores in `platform_connections`

---

## 12. API Usage Examples

All API endpoints are prefixed with `/api/v1`. Authentication is via `Authorization: Bearer <JWT>` or `X-API-Key: <key>`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/campaigns` | GET | List campaigns |
| `/api/v1/campaigns` | POST | Create campaign `{"name": "...", "platforms": [...], "budget": 2000}` |
| `/api/v1/campaigns/{id}/launch` | POST | Launch a campaign |
| `/api/v1/campaigns/{id}/pause` | POST | Pause a campaign |
| `/api/v1/analytics/overview?days=30` | GET | Cross-platform analytics |
| `/api/v1/analytics/platform/{name}` | GET | Per-platform metrics |
| `/api/v1/orchestrator` | POST | AI agent `{"input": "Write a LinkedIn post..."}` |
| `/api/v1/kill-switch/activate` | POST | Emergency halt (owner only) |
| `/api/v1/gdpr/export` | POST | GDPR data export |

All endpoints require `Authorization: Bearer <JWT>` or `X-API-Key: <key>`.

---

## 13. Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `503 Service Unavailable` | PostgreSQL is down or unreachable | Check `docker compose ps`, verify `DATABASE_URL` in `.env` |
| `401 Invalid or expired token` | JWT has expired or is malformed | Run `orchestra auth login` to refresh |
| `429 Rate limit exceeded` | Too many requests in the window | Wait for the rate limit window to reset; check `rate_limit_per_minute` in settings |
| `402 Spend cap exceeded` | Spend operation would violate tier 1/2/3 caps | Review caps via analytics; contact admin to adjust |
| `403 Role not authorized` | User role lacks required permission | Check role with `orchestra auth whoami`; admin can change roles |
| Connection refused on port 8000 | Server not running | Start with `docker compose up -d` or `uvicorn` |
| `Ollama: 0 model(s)` | No models pulled | Run `ollama pull llama3.2` |

### Log Inspection

OrchestraAI uses `structlog` for structured JSON logging. Check Docker logs:

```bash
docker compose logs -f app
```

Key log events: `auth_context`, `audit_log`, `bidding_decision`, `spend_anomaly_detected`, `kill_switch_activated`.

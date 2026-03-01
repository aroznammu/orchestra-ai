# OrchestraAI -- User Procedures

## Installation

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Poetry (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/orchestra-ai.git
cd orchestra-ai

# Copy environment template
cp .env.example .env

# Edit .env with your API keys (at minimum, set one LLM provider)
# OPENAI_API_KEY=sk-...
# or use Ollama for free local LLM

# Start infrastructure (Postgres, Redis, Kafka, Qdrant, Ollama)
make docker-up

# Install Python dependencies
make install

# Run database migrations
make migrate

# Start the API server
make run
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs` (debug mode only).

### Using Docker Only

```bash
# Start everything including the app
docker compose up -d

# Check health
curl http://localhost:8000/health
```

### Using the CLI

```bash
# Check version
orchestra version

# Check system status
orchestra status

# Campaign management
orchestra campaign list
orchestra campaign create --name "Q1 Launch" --platform twitter
orchestra campaign status <campaign-id>

# Platform connections
orchestra connect add twitter
orchestra connect list
orchestra connect remove twitter

# Run optimization
orchestra optimize run --campaign <id>

# Generate reports
orchestra report summary
orchestra report generate --campaign <id> --format json
```

## Deployment

### Development (Docker Compose)

The included `docker-compose.yml` starts all infrastructure:

| Service | Port | Purpose |
|---------|------|---------|
| app | 8000 | FastAPI application |
| postgres | 5432 | Relational database |
| redis | 6379 | Cache + event bus |
| kafka | 9092 | Durable event bus |
| qdrant | 6333 | Vector database |
| ollama | 11434 | Local LLM serving |

### Production

```bash
# Build production image
docker build -t orchestra-ai:latest .

# Run with external services
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  orchestra-ai:latest
```

**Production checklist**:
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Use managed PostgreSQL (e.g., AWS RDS, Supabase)
- [ ] Use managed Redis (e.g., AWS ElastiCache, Upstash)
- [ ] Set strong `JWT_SECRET_KEY` and `FERNET_KEY`
- [ ] Configure CORS origins for your domain
- [ ] Enable HTTPS (reverse proxy: Nginx, Caddy, or cloud LB)
- [ ] Set up log aggregation (e.g., Datadog, Loki)

## Connecting Accounts

### Step 1: Initialize OAuth

```bash
POST /api/v1/platforms/auth/init
{
  "platform": "twitter"
}
```

Response includes an `auth_url` -- redirect the user to this URL.

### Step 2: Handle Callback

After the user authorizes, the platform redirects to your callback URL:

```bash
POST /api/v1/platforms/auth/callback
{
  "platform": "twitter",
  "code": "abc123...",
  "state": "..."
}
```

Tokens are encrypted and stored automatically.

### Step 3: Verify Connection

```bash
GET /api/v1/platforms/connections
```

### Supported Platforms

| Platform | Status | Requirements |
|----------|--------|-------------|
| X/Twitter | Full | Paid API ($100/mo Basic) |
| YouTube | Full | Google Cloud project |
| Pinterest | Stub | Free, easy approval |
| TikTok | Stub | Developer portal |
| Facebook | Stub | Meta business verification |
| Instagram | Stub | Meta business verification |
| LinkedIn | Stub | Partner approval |
| Snapchat | Stub | Marketing API approval |
| Google Ads | Stub | Developer token |

## Running Campaigns

### Create a Campaign

```bash
POST /api/v1/orchestrator
{
  "input": "Create a campaign about AI productivity tips",
  "payload": {
    "platform": "twitter",
    "topic": "AI productivity tips",
    "tone": "professional",
    "num_variants": 3
  }
}
```

### Publish Content

```bash
POST /api/v1/orchestrator
{
  "input": "Publish a post about our new feature launch",
  "payload": {
    "platform": "twitter",
    "content": "Excited to announce our new AI-powered scheduling feature!",
    "hashtags": ["#AI", "#Marketing", "#Automation"]
  }
}
```

### Get Analytics

```bash
POST /api/v1/orchestrator
{
  "input": "Show me analytics for the last 30 days",
  "payload": {
    "platforms": ["twitter", "youtube"],
    "date_range_days": 30
  }
}
```

## Troubleshooting

### Common Issues

**"Kill switch is active"**
- The kill switch has been activated. Check `/api/v1/kill-switch/status`.
- Only owners can deactivate: `POST /api/v1/kill-switch/deactivate`.

**"Budget exceeded"**
- Daily or monthly spend cap reached. Check utilization via the spend tracker.
- Adjust caps in tenant settings or wait for daily reset (midnight UTC).

**"Rate limited" on platform API**
- OrchestraAI maintains 15% buffer below platform limits.
- Wait for the rate limit window to reset (check `resets_in_seconds`).

**"Compliance violation"**
- Content failed ToS validation. Check the `violations` array in the response.
- Common: content too long, prohibited keywords, missing required media.

**Database connection errors**
- Verify PostgreSQL is running: `docker compose ps`
- Check connection string in `.env`: `DATABASE_URL`

**Ollama not responding**
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Pull a model: `docker compose exec ollama ollama pull llama3.1`

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/health

# Readiness probe (checks database)
curl http://localhost:8000/ready
```

### Logs

OrchestraAI uses structured JSON logging (structlog). Filter by component:

```bash
# All logs
docker compose logs app

# Filter by component
docker compose logs app | grep "agent.orchestrator"
docker compose logs app | grep "risk.anomaly"
docker compose logs app | grep "compliance"
```

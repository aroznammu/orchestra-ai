# OrchestraAI -- Cost Analysis

## Per-Platform API Costs

### Social Platforms

| Platform | API Tier | Monthly Cost | Rate Limits | Notes |
|----------|---------|-------------|-------------|-------|
| X/Twitter | Basic | $100/mo | 10K tweets/mo, 50K reads/mo | Instant access |
| X/Twitter | Pro | $5,000/mo | 300K tweets/mo, 1M reads/mo | For scale |
| YouTube | Free | $0 | 10K units/day | Google Cloud project required |
| Pinterest | Free | $0 | 1K calls/day | Easy approval |
| TikTok | Free | $0 | Varies by endpoint | Developer portal approval |
| Facebook/Instagram | Free | $0 | 200 calls/hour | Meta business verification |
| LinkedIn | Free (limited) | $0 | 1K calls/day | Partner approval required |
| Snapchat | Free | $0 | 100 calls/hour | Marketing API approval |
| Google Ads | Free | $0 | 15K ops/day | Developer token required |

### LLM Costs

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) | Use Case |
|----------|-------|----------------------|----------------------|----------|
| OpenAI | GPT-4o-mini | $0.15 | $0.60 | Classification, simple tasks |
| OpenAI | GPT-4o | $2.50 | $10.00 | Content generation |
| OpenAI | text-embedding-3-small | $0.02 | - | Embeddings |
| Anthropic | Claude 3.5 Haiku | $0.25 | $1.25 | Fast reasoning |
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 | Complex strategy |
| Ollama | Llama 3.1 (local) | $0 | $0 | Self-hosted fallback |

### Estimated Monthly LLM Costs by Scale

| Scale | Campaigns/mo | Embeddings | Content Gen | Analysis | Total LLM |
|-------|-------------|-----------|------------|---------|-----------|
| Solo (1 user) | 20 | $0.10 | $2.00 | $0.50 | ~$3/mo |
| Small team (5) | 100 | $0.50 | $10.00 | $2.50 | ~$13/mo |
| Agency (20) | 500 | $2.50 | $50.00 | $12.50 | ~$65/mo |
| Enterprise (100) | 5,000 | $25.00 | $500.00 | $125.00 | ~$650/mo |

## Infrastructure Costs

### Self-Hosted (Docker Compose)

| Component | Resource | Monthly Cost |
|-----------|---------|-------------|
| VPS (4 vCPU, 8GB) | All services | $40-80 |
| Storage (100GB SSD) | DB + vectors | $10-20 |
| **Total** | | **$50-100/mo** |

### Cloud-Hosted (Production)

| Scale | Users | Compute | Database | Redis | Qdrant | Kafka | Total |
|-------|-------|---------|----------|-------|--------|-------|-------|
| 1K users | Startup | $100 | $50 | $30 | $50 | $50 | ~$280/mo |
| 10K users | Growth | $400 | $200 | $100 | $150 | $150 | ~$1,000/mo |
| 100K users | Scale | $2,000 | $800 | $400 | $600 | $500 | ~$4,300/mo |
| 1M users | Enterprise | $10,000 | $4,000 | $2,000 | $3,000 | $2,500 | ~$21,500/mo |

### Cost Optimization Strategies

1. **Model routing**: Use GPT-4o-mini ($0.15/1M) for 80% of tasks, expensive models only for complex content
2. **Ollama local**: Self-host Llama for development and cost-sensitive customers
3. **Embedding cache**: Don't re-embed unchanged content
4. **Batch processing**: Group API calls to reduce overhead
5. **Qdrant quantization**: Enable scalar quantization for 4x memory reduction
6. **Kafka retention**: 7-day retention for event streams (reduce storage)

## Revenue Model (Open-Core)

| Tier | Price | Features |
|------|-------|---------|
| Community | Free | Full platform, self-hosted, community support |
| Pro | $49/mo | Managed hosting, priority support, advanced analytics |
| Team | $199/mo | SSO, team management, custom integrations |
| Enterprise | Custom | SLA, dedicated support, on-premise deployment |

### Unit Economics (Pro tier)

| Metric | Value |
|--------|-------|
| Monthly revenue | $49 |
| Infrastructure cost | ~$5 |
| LLM cost | ~$13 |
| Support allocation | ~$5 |
| **Gross margin** | **~53%** |

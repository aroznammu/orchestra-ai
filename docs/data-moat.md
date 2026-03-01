# OrchestraAI -- Defensible Data Moat

## 1. Overview

OrchestraAI's moat is not code -- it's the compounding intelligence that emerges from cross-platform campaign data. Every campaign executed, every engagement measured, and every optimization applied makes the system measurably better.

## 2. Data Flywheel

```
Campaign Creation
       |
  [Index in Qdrant]
       |
  Platform Publishing
       |
  Engagement Data
       |
  Signal Normalization
       |
  Performance Embedding
       |
  Model Update
       |
  Better Recommendations
       |
  Campaign Creation (improved)
```

**Implementation**: `moat/flywheel.py` -- `FlywheelPipeline` with stages:
- `on_campaign_created()` -- index for retrieval
- `on_engagement_received()` -- normalize, re-embed
- `on_optimization_applied()` -- log decision for learning

**Maturity tracking**: cold_start -> warming -> learning -> maturing -> optimized

## 3. Cross-Platform Signal Normalization

Not all engagements are equal. A LinkedIn comment is worth more than a Twitter impression.

**Platform-specific weights** (`moat/signals.py`):

| Signal | Twitter | YouTube | Instagram | LinkedIn | TikTok |
|--------|---------|---------|-----------|----------|--------|
| Impression | 0.01 | - | 0.01 | 0.02 | - |
| View | - | 0.05 | - | - | 0.02 |
| Like | 0.5 | 0.3 | 0.3 | 0.5 | 0.2 |
| Comment | 2.0 | 3.0 | 2.5 | 3.0 | 2.0 |
| Share | 3.0 | 2.0 | 3.0 | 4.0 | 3.0 |
| Save | 1.0 | 1.5 | 2.5 | 1.5 | 2.0 |

**Output**: Unified 0-100 engagement score for cross-platform comparison.

## 4. Attention Decay Curves

Each platform has different content longevity:

| Platform | Half-Life | Peak Hour | 24h Capture |
|----------|-----------|-----------|-------------|
| Twitter | 4 hours | 0 | 95% |
| YouTube | 168 hours (7 days) | 24 | 30% |
| Instagram | 12 hours | 2 | 85% |
| TikTok | 48 hours | 6 | 55% |
| LinkedIn | 24 hours | 4 | 75% |

This data informs optimal posting schedules and content lifespan expectations.

## 5. Performance Embedding Engine

Standard embeddings capture content similarity. Performance embeddings capture content + outcome similarity.

**Method** (`moat/performance_embed.py`):
1. Generate base content embedding (OpenAI/Ollama)
2. Compute performance score: `ER * 0.4 + CTR * 0.3 + ROI * 0.3`
3. Scale vector magnitude: `vector * (1.0 + min(score, 0.5))`

**Result**: High-performing campaigns cluster together in vector space, enabling retrieval like "find content similar to X that actually performed well."

## 6. Per-Tenant Private Model

Each tenant's data is isolated and never leaks to other tenants.

**`moat/tenant_model.py`**:
- `learn_from_campaign()` -- ingest outcome, build private embedding
- `predict_performance()` -- weighted average of similar past campaigns
- `get_best_practices()` -- top content by engagement for a platform
- `export_data()` / `delete_all()` -- GDPR compliance

**Prediction method**: Similarity-weighted average of outcomes from the tenant's own history.

## 7. Global Aggregate Model (with Differential Privacy)

Anonymized patterns across all tenants for cold-start recommendations and benchmarking.

**Privacy mechanism** (`moat/global_model.py`):
- Laplace noise injection (epsilon = 1.0)
- Content hashing (SHA-256, no reversible mapping)
- Category bucketing (content type, length, ROI tier)

**Use cases**:
- Cold-start recommendations for new tenants
- Industry benchmark comparisons
- Content type effectiveness by platform

## 8. Cross-Platform Intelligence

The structural moat: what no single platform can provide.

**`intelligence/cross_platform.py`**: Unified ROI normalization
**`intelligence/marginal_return.py`**: Diminishing returns modeling
**`intelligence/allocator.py`**: Dynamic budget allocation
**`intelligence/saturation.py`**: Channel saturation detection
**`intelligence/attribution.py`**: Multi-touch attribution (5 models)

**Key insight**: Google Smart Bidding can't see your Twitter data. Meta Advantage+ can't see your LinkedIn. OrchestraAI sees everything.

## 9. Compounding Advantage

```
Phase 1 (0-30 days):   Cold start, using global model benchmarks
Phase 2 (30-90 days):  Tenant model warming, basic predictions
Phase 3 (90-180 days): Meaningful optimization, cross-platform insights
Phase 4 (180+ days):   Compounding advantage, hard to replicate
```

The longer a tenant uses the system, the harder it is to switch -- not because of lock-in, but because the intelligence is genuinely valuable and impossible to export (it's emergent from the data pattern, not the data itself).

## 10. Defensibility Analysis

| Moat Type | Strength | Mechanism |
|-----------|----------|-----------|
| Data network effect | Strong | More data -> better models -> better results |
| Cross-platform intelligence | Very strong | No competitor sees all platforms simultaneously |
| Performance embeddings | Strong | Outcome-weighted retrieval is unique |
| Tenant private models | Moderate | Switching cost increases with data maturity |
| Global aggregate model | Moderate | Differential privacy enables safe aggregation |
| Open-source community | Moderate | Contributors add connectors, increasing value |

**Why this is hard to copy**:
1. Requires multi-platform API access (business verification barriers)
2. Performance embeddings need months of real campaign data
3. Cross-platform normalization weights are empirically derived
4. Global model improves with every tenant (network effect)

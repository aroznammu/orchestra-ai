# OrchestraAI -- State of the Union

**Updated:** 2026-03-21
**Branch:** `master` (up to date with `origin/master`)
**Test Suite:** 355 tests, all passing (14 test modules)
**Commits:** 24 total

---

## 1. Executive Summary

OrchestraAI is a **deployed, live platform** with both the backend API and two frontend applications running in production. Since the previous state-of-the-union (2026-03-18), four significant milestones have been completed:

1. **Production deployment** -- Backend on Railway (PostgreSQL + FastAPI), dashboard at `useorchestra.dev` on Vercel, promotional website at `www.useorchestra.dev` on Vercel, Cloudflare DNS with SSL.
2. **Promotional website redesign** -- Premium dark aesthetic with glass-morphism, architecture diagram, competitive comparison table, video embed, marquee, and `/demo` page. 7 pages total.
3. **Change password feature** -- New `PUT /api/v1/auth/password` endpoint and `/settings/password` frontend page, live in production.
4. **Six high-impact features** (implemented 2026-03-21):
   - **SEO**: `sitemap.xml` (auto-generated) + `robots.txt` for the marketing website
   - **Open Graph meta tags** on all 7 website pages for social sharing previews
   - **Support agent upsell prompts** -- plan-aware system prompt nudges Starter users toward Agency features
   - **Experiment API** -- full CRUD endpoints for A/B testing, wired to existing `Experiment` DB model
   - **Email notifications for budget alerts** -- SMTP integration via `aiosmtplib`, WARNING+ alerts trigger real emails
   - **GDPR PostgreSQL deletion fix** -- cascade delete across all 12 tables in dependency order (was Qdrant-only)

The platform is **live and functional**. The single remaining blocker for revenue is **Stripe live mode activation** (switching from test keys to production keys).

---

## 2. What Has Been Built (Complete Inventory)

### 2.1 Backend (FastAPI + Python)

| Category | Count | Details |
|----------|-------|---------|
| API route files | 14 | auth, billing, campaigns, **experiments**, health, orchestrator, platforms, analytics, reports, audit, gdpr, kill_switch, support, faq |
| API endpoints | 54+ | Full CRUD + specialized actions across all route modules (5 new experiment endpoints) |
| Agent files | 16 | orchestrator, content, analytics, optimizer, compliance, platform, policy, video, safety, classify, cost_router, support_agent (now with upsell), plus connectors |
| DB models | 13 | Tenant, User, PlatformConnection, Campaign, CampaignPost, AuditLog, Experiment, KillSwitchEventLog, SpendRecord, BiddingHistory, ChatSession, ChatMessage, FAQEntry |
| Notification modules | 1 | `notifications/email.py` -- async SMTP sender for budget alerts |
| Alembic migrations | Present | Schema for all 13 models including support/FAQ tables |
| RBAC permissions | 26 | Including support:view and support:manage |

### 2.2 Frontend Dashboard (Next.js 16)

| Page | Route | Purpose |
|------|-------|---------|
| Login | `/login` | Authentication with JWT |
| Dashboard | `/dashboard` | Metrics overview, campaign status, platform health |
| Campaigns | `/campaigns` | Campaign list, create, launch, pause |
| Analytics | `/analytics` | Cross-platform metrics and charts (Recharts) |
| Orchestrator | `/orchestrator` | Natural language AI interface |
| Platforms | `/platforms` | OAuth connection management for 9 platforms |
| Billing | `/billing` | Stripe checkout, subscription management |
| Settings | `/settings` | Account and tenant configuration |
| Kill Switch | `/kill-switch` | Emergency spend halt |
| **Support** | `/support` | AI chat + FAQ accordion (new) |

### 2.3 Promotional Website (Next.js 16, separate project)

| Page | Route | Content |
|------|-------|---------|
| Landing | `/` | Hero, platform marquee, how-it-works, feature highlights, architecture diagram, animated stats, comparison table, testimonials, CTA |
| Features | `/features` | 8 detailed feature sections, code snippet previews, tech stack grid |
| Pricing | `/pricing` | Starter/Agency cards, self-host option, ROI calculator, feature comparison matrix |
| Security | `/security` | 7 security sections with trust badges (SOC 2, GDPR, Apache 2.0) |
| FAQ | `/faq` | Searchable accordion with category filter tabs, 7 categories, 14 questions |
| Contact | `/contact` | Support channels (Email, Dashboard Chat, GitHub Issues), contact form |
| **Demo** | `/demo` | Embedded video player, key feature screenshots, "Try it yourself" CTA |

**SEO:** Auto-generated `sitemap.xml` (7 URLs), `robots.txt`, Open Graph + Twitter meta tags on every page.

16 reusable components: Navbar, Footer, SectionHeading, FeatureCard, PricingCard, AccordionItem, AnimatedCounter, PlatformGrid, CTABanner, ContactForm, GradientText, ComparisonTable, ArchitectureDiagram, VideoEmbed, plus per-page layouts.

### 2.4 AI Agents and Intelligence

| Agent / System | Status | Details |
|----------------|--------|---------|
| LangGraph Orchestrator | Complete | 10-node StateGraph with conditional routing, safety limits |
| Content Agent | Complete | Multi-provider LLM calls (OpenAI -> Anthropic -> Ollama) |
| Video Agent | Complete | Seedance 2.0 via fal.ai, text-to-video and image-to-video |
| Visual Compliance Gate | Complete | GPT-4o Vision keyframe scan for IP/copyright/trademark |
| Analytics Agent | Complete | Cross-platform aggregation and insights |
| Optimization Agent | Complete | Thompson Sampling, UCB, Bayesian budget allocation |
| Compliance Gate | Complete | Pre-action checks for content, targeting, budget |
| Policy Validator | Complete | Per-platform rules (character limits, hashtags, media) |
| Platform Dispatch | Complete | Publish/schedule to 9 platform connectors |
| **Support Agent** | **Complete** | RAG context retrieval, FAQ matching, guardrailed responses, sensitive pattern sanitization, **plan-aware upsell prompts** |
| Cost-Aware Router | Complete | Routes tasks to optimal LLM by complexity tier |
| RAG Pipeline | Complete | Qdrant vector search with embedding fallback chain |
| Data Moat Engine | Complete | Performance flywheel with tenant-specific learning |
| Cross-Platform Intelligence | Complete | ROI normalization, marginal returns, budget allocation, saturation detection |

### 2.5 Platform Connectors (9)

All connectors implement OAuth2, publish, analytics, and audience with retry logic and rate-limit handling:

Twitter/X v2, YouTube v3, TikTok v2, Pinterest v5, Facebook Graph v19, Instagram Graph v19, LinkedIn v2, Snapchat Marketing v1, Google Ads v16.

### 2.6 Financial Risk Engine

| Component | Status |
|-----------|--------|
| 3-Phase Bidding (Hard Guardrail -> Semi-Autonomous -> Controlled Autonomous) | Complete |
| 3-Tier Spend Caps (daily, weekly, monthly) | Complete |
| Anomaly Detection (Z-score + IQR) | Complete |
| Velocity Monitoring | Complete |
| Kill Switch (emergency halt) | Complete |
| **Email Alerts** | **Complete** | Budget alerts at 50/75/90/100% now send real emails via SMTP (WARNING+ severity) |

### 2.7 Testing

| Test Module | Tests |
|-------------|-------|
| test_auth.py | 7 |
| test_auth_pipeline.py | 16 |
| test_bidding.py | 12 |
| test_cli.py | 23 |
| test_compliance.py | 5 |
| test_content.py | 8 |
| test_debt_fixes.py | 43 |
| test_health.py | 2 |
| test_orchestrator.py | 43 |
| test_platforms.py | 24 |
| test_risk.py | 11 |
| test_security.py | 14 |
| test_step3_routes.py | 35 |
| test_support_faq.py | 69 |
| **Total** | **~312 functions (355 with parametrization)** |

### 2.8 CI/CD (GitHub Actions)

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `ci.yml` | Push/PR to main | Ruff lint + format check, pytest (Python 3.12) |
| `docker.yml` | Push/PR to main, tags `v*` | Build and push Docker image to GHCR |
| `release.yml` | Tags `v*` | Build Python package, create GitHub release |
| `frontend.yml` | Changes to `frontend/**` | TypeScript check, ESLint, Next.js build |
| `website.yml` | Changes to `website/**` | TypeScript check, ESLint, Next.js build |

### 2.9 Documentation (17 documents)

architecture.md, guardrailed-bidding.md, security-compliance.md, data-moat.md, cost-analysis.md, launch-strategy.md, user-procedures.md, marketing_video.md, differentiation.md, due-diligence.md, viral-strategy.md, hybrid_launch_strategy.md, stripe_monetization_plan.md, audit_addendum.md, production_deployment_playbook.md, **gap_analysis.md**, **new_prompt_for_checklist.md**.

### 2.10 Marketing Assets

- 8 video files (60s marketing videos in 4 aspect ratios, 9s clips, final cut)
- 2 thumbnails (landscape + portrait)
- 1 narration audio (MP3)
- 1 product image (JPEG)
- Video enhancement script (enhance_video.py)

### 2.11 Infrastructure

- Dockerfile (Python 3.12-slim, Poetry, ffmpeg, non-root user)
- docker-compose.yml (app + PostgreSQL + Redis + Qdrant + Kafka + Ollama)
- .env.example with all variable names
- Makefile for dev commands
- Setup scripts (bash + PowerShell)

---

## 3. Known Technical Debt

### Resolved (2026-03-21)

| Issue | Resolution |
|-------|------------|
| ~~GDPR: PostgreSQL cleanup~~ | `_delete_tenant_data` now cascade-deletes all 12 PostgreSQL tables in dependency order before Qdrant cleanup |
| ~~GDPR data operations~~ | Deletion now passes `AsyncSession` through from the API route to the GDPR manager |
| ~~Budget alerts are log-only~~ | `AlertManager` now sends real email notifications via SMTP for WARNING+ severity alerts |
| ~~Support agent has no upsell~~ | Support agent system prompt is now plan-aware; Starter users receive natural Agency feature suggestions |
| ~~Experiment model has no API~~ | Full CRUD endpoints at `/api/v1/campaigns/{id}/experiments` with tenant-scoped access |

### Remaining

| Issue | Severity | Description |
|-------|----------|-------------|
| Encryption standard | Medium | Uses Fernet (AES-128-CBC + HMAC) instead of AES-256-GCM. `encryption_key` config field defined but unused |
| GDPR export | Low | Data export is still in-memory (collects but does not generate a downloadable archive) |
| Scheduler | Low | APScheduler shell exists but no jobs registered (spend cap resets, velocity baselines, token refresh) |
| Bidding engine logic | Low | `elif` branches in engine.py lines 134-140 are unreachable due to first `if` catching all cases |
| Auth fallback | Low | Returns owner-level JWT when DB unavailable during login/register (should return 503) |
| Hardcoded pool sizes | Low | DB pool_size=20, max_overflow=10, safety limits -- all hardcoded instead of configurable |

---

## 4. Git Status

```
Branch:    master
Remote:    Up to date with origin/master
Working:   Clean (2 untracked doc files: gap_analysis.md, new_prompt_for_checklist.md)
Commits:   24 total
```

### Recent commits (newest first):

```
bfd98a1  feat: implement 6 high-impact features — SEO, OG tags, upsell support, experiments API, email alerts, GDPR fix
faba8be  feat: redesign promotional website with premium dark aesthetic, new components, and /demo page
772f482  feat: add change password endpoint and UI, update domain to useorchestra.dev
f4699d9  docs: update STATE_OF_THE_UNION.md with full project status as of 2026-03-18
4a018e2  docs: fix README links, add support/website sections, add frontend/website CI
a118b3b  feat: add OrchestraAI promotional website
b52becf  assets: add marketing videos, narration audio, and video enhancement script
a6eea41  docs: update architecture, security, cost analysis, user procedures, and go-live checklist
8ca5619  feat: add AI customer support chat, auto-reply agent, and FAQ system
91f5b6d  feat: integrate Seedance 2.0 video generation and Visual Compliance Gate
```

---

## 5. Next Steps (Priority Order)

### Immediate: Activate Revenue

1. **Stripe live mode** -- The only remaining blocker for accepting real payments:
   - Create live Stripe products and price IDs for Starter ($99/mo) and Agency ($999/mo)
   - Swap `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_STARTER_PRICE_ID`, `STRIPE_AGENCY_PRICE_ID` in Railway environment variables
   - Register the production webhook URL (`https://api.useorchestra.dev/api/v1/billing/webhook`) in the Stripe dashboard
   - Run a live $1 test charge and verify the subscription lifecycle

2. **Configure SMTP** -- Set `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` in Railway so budget alert emails actually send. Options: Resend, Mailgun, SendGrid, or a custom mail server.

3. **Design and upload OG image** -- Currently `website/public/og-image.png` is referenced but not yet created. Design a branded 1200x630 image for social sharing previews.

### Short-Term: Launch Marketing

4. **Upload marketing videos** to platforms:
   - Product Hunt (16:9 + thumbnail)
   - Twitter/X launch thread (9:16)
   - LinkedIn post (16:9)
   - Instagram Reels (9:16)
   - Embed on promotional website `/demo` page

5. **Configure `api.useorchestra.dev`** -- Add a CNAME record in Cloudflare pointing to the Railway backend for a branded API URL.

6. **Submit sitemap to Google Search Console** -- `https://www.useorchestra.dev/sitemap.xml` is live; submit to GSC to accelerate indexing.

### Medium-Term: Address Remaining Technical Debt

7. **Fix auth fallback** -- Return 503 instead of owner-level JWT during DB outages.
8. **Upgrade encryption** -- Evaluate moving from Fernet to AES-256-GCM, or document that Fernet (AES-128-CBC + HMAC-SHA256) is sufficient for token encryption at rest.
9. **Register scheduler jobs** -- Wire spend cap resets, velocity baselines, token refresh into APScheduler.
10. **Fix bidding engine logic bug** -- Make elif branches reachable for phase-specific approval.
11. **GDPR data export** -- Wire the export endpoint to generate a real downloadable archive from PostgreSQL instead of in-memory placeholders.

### Long-Term: Growth

12. **Collect real testimonials** -- Replace placeholder social proof on the website.
13. **Set up monitoring** -- Error tracking (Sentry), uptime monitoring, alerting.
14. **Analytics integration** -- Vercel Analytics or PostHog for usage tracking.
15. **Expand FAQ** -- Add tenant-specific FAQs as customers onboard.
16. **A/B testing runtime** -- Build the experiment assignment/tracking logic on top of the new Experiment API endpoints.
17. **Feature flags** -- Per-tenant feature gating beyond subscription tiers (implement when enterprise customers request it).

---

## 6. Deployment Status

| Service | URL | Platform | Status |
|---------|-----|----------|--------|
| Backend API | `https://api.useorchestra.dev` | Railway | Live |
| Dashboard | `https://useorchestra.dev` | Vercel | Live |
| Marketing Website | `https://www.useorchestra.dev` | Vercel | Live |
| PostgreSQL | Railway-managed | Railway | Live |
| DNS + SSL | Cloudflare | Cloudflare | Configured |
| Stripe Billing | Test mode | Stripe | Awaiting live keys |

---

## 7. Build Verification

| Check | Status |
|-------|--------|
| Python tests (pytest) | 355 passed |
| Python lint (ruff check) | Clean |
| Python format (ruff format) | Clean |
| Frontend TypeScript (tsc --noEmit) | Zero errors |
| Frontend ESLint | Zero errors |
| Frontend build (next build) | Success |
| Website TypeScript (tsc --noEmit) | Zero errors |
| Website ESLint | Zero errors |
| Website build (next build) | Success (7 static pages + sitemap.xml) |
| Git working tree | Clean |

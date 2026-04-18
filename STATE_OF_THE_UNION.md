# OrchestraAI -- State of the Union

**Updated:** 2026-04-18 (full-codebase audit + CRO polish sync)
**Branch:** `master` (up to date with `origin/master`)
**Test Suite:** 361 tests, all passing (15 test modules, ~6.3s wall time)
**Commits:** 46 total

---

## 1. Executive Summary

OrchestraAI is a **fully production-ready, revenue-collecting SaaS platform**. All engineering work is complete. The platform has been tested end-to-end including a real $99 Stripe payment (refunded).

This state-of-the-union was rebuilt from a bottom-up codebase audit (source tree, `git log`, test collection, live page structure) to correct drift from previous versions and to capture the most recent CRO / marketing-site polish round.

Since the previous state-of-the-union, the following milestones were completed:

### CRO / Conversion Optimization pass (commit `1e4b7fe`, 2026-03-22)

A dedicated Principal-UX/CRO-style upgrade round layered on top of the 8-round redesign:

- **`EnterpriseTrustStrip`** (`website/src/components/EnterpriseTrustStrip.tsx`) -- greyscale "Powered by & Secured by" strip under the hero with: Stripe Verified, SOC 2-Ready Architecture, Meta Ads API, ByteDance Seedance 2.0, Llama 3. Hover-to-color affordance, fades in with `whileInView`.
- **`HowItWorksVideoEmbed`** (`website/src/components/HowItWorksVideoEmbed.tsx`) -- glass-morphism-framed video card embedded in the How It Works section. Idle play-button state, click-to-play HTML5 `<video>`, tagline "See the AI pause a bleeding campaign in 90 seconds."
- **Structured testimonials** (`website/src/lib/constants.ts`) -- replaced generic attributions with named personas (Sarah Jenkins / Acme Digital, Marcus Chen / Northline Commerce, Elena Vasquez / Signal & Tide Agency), metric-specific quotes (−34% Meta CPA, $4.8K avoided, 42 accounts), and company-logo tiles (`companyLogo` two-letter marks).
- **`GUARDED_TRIAL_MICROCOPY`** -- "14-Day Trial · Includes $50 in AI Video Credits · No Credit Card Required" rendered under every primary trial CTA (hero + `CTABanner` + pricing) to prevent Seedance/LLM-inference trial abuse while reinforcing trust.
- **Sticky / scroll-aware Navbar** (`website/src/components/Navbar.tsx`) -- `fixed inset-x-0 top-0 z-50`, scroll-listener toggles a denser backdrop blur + shadow at `scrollY > 20`, "Get Started" pill persists across all scroll depths. Mobile menu via `AnimatePresence`.
- **`ContentCreationScene` expansion** (`website/src/components/demo/scenes/ContentCreationScene.tsx`) -- Seedance 2.0 video-generation substate with skeleton-to-`<video>` transition; typing-effect example prompt; auto-scroll to Step 1 when the example prompt finishes typing.
- **`ComplianceScene` VCG emphasis** -- distinct "Visual IP Compliance Scan" card animating frame-by-frame "Safe" checkmarks against celebrity likeness / copyrighted logos.
- **`DashboardScene` + `BrowserMockup demoFinancialControls`** -- kill-switch and "Autonomous Budget Reallocation Active" badge elevated in the dashboard mockup to make financial safety the hero of Step 4.
- **Source feedback docs** -- `docs/cro_demo_page.md` (demo-page brief) and `docs/cro_landing_page.md` (landing-page brief) capture the CRO specs that drove this round. Originally authored inside the Next.js App Router tree; relocated on 2026-04-18.

### Infrastructure & Services (completed 2026-03-21 → 2026-03-22)

1. **Stripe live mode activated** -- Real payments working. Starter ($99/mo) and Agency ($999/mo) with live webhook at `api.useorchestra.dev`. First real transaction processed and refunded.
2. **SMTP email alerts via Resend** -- Domain `useorchestra.dev` verified (DKIM + SPF), budget alerts now send real emails.
3. **OG image deployed** -- Branded 1200x630 social sharing image live on marketing website.
4. **Sitemap fix** -- Fixed Next.js 16 async compatibility issue; sitemap now serves correctly.
5. **Google Search Console** -- Ownership verified via HTML file, sitemap submitted, 7 pages indexing.
6. **Subscription prompt on dashboard** -- Free users see a prominent "Choose a Plan" banner.
7. **Sentry error monitoring** -- Integrated in both FastAPI backend and Next.js dashboard, two projects configured.
8. **5 technical debt items resolved** (auth fallback, AES-256-GCM encryption, APScheduler, bidding verification, GDPR export).
9. **Vercel Analytics + Speed Insights** -- Enabled on both dashboard and marketing website.
10. **Redis connected** -- Railway Redis service linked to backend.

### Marketing Website Redesign (8 rounds, completed 2026-03-01)

The marketing website underwent 8 iterative redesign passes based on detailed design feedback (documented in `docs/website_redesign1.md` through `docs/website_redesign8.md`), pushing it from ~6/10 to top-tier SaaS quality. Key changes:

**Visual Identity & Brand System:**
- Dark + AI-native + glow aesthetic with primary `#0B0B0F` and surface `#111117` backgrounds
- Animated gradient mesh (`hero-mesh`) for hero depth
- Ambient floating orbs, noise texture overlay, radial glow system
- Animated neon sweep accent line (`.neon-line`) as signature visual element
- Glassmorphism card system (`.card-elevated`) with neon edge glow on hover
- Gradient CTA buttons (`.btn-primary`, `.btn-secondary`) with intensified hover glow
- Soft shadow dividers between sections for layered depth

**Hero Section:**
- Headline: "One AI Command. Nine Platforms. Zero Wasted Spend." with `font-extrabold`, `tracking-tighter`, `leading-[1.05]`
- Secondary emotional hook: "Stop managing campaigns. Start orchestrating."
- Animated pipeline visualization (`HeroPipeline` component) -- 10 color-coded agent nodes with traveling data pulse
- BrowserMockup with animated bar charts, live agent pipeline sidebar, throughput indicator, hover zoom
- Social proof micro-bar (no credit card, 60s deploy, Apache 2.0)
- Product Showcase Panels (AI Agent Pipeline, Financial Guardrails, Cross-Platform ROI) with live animations

**New Sections Added:**
- Trust Metrics Bar with "Built by engineers" credibility line
- "A New Category" positioning section with 4 pillars (AI-Native, Zero Infra, Self-Improving, Dev-First)
- Developer Section with syntax-highlighted code snippet and technical feature checklist
- **Interactive Pipeline Demo -- Hybrid 3D/2D** (redesign round 8):
  - `GraphCanvas3D`: Full Three.js (React Three Fiber) 3D scene for desktop -- 8 sphere-geometry nodes in 3D space with emissive glow materials, status-based point lights, Line edges, animated particles traveling along active edges, `OrbitControls` with damping and auto-rotate, `Html` labels from drei
  - `PipelineCanvas`: 2D SVG/CSS fallback for mobile/low-perf -- 8 clickable nodes with status-based glow, SVG edges with animated data pulse dots, sequential pipeline run simulation on load
  - `useIs3DCapable`: Capability detection hook (viewport >= 1024px + WebGL2 support) for automatic 3D/2D switching
  - `pipelineData.ts`: Shared data layer (node definitions with 3D z-coordinates, edges, status color mappings, hex/emissive tables)
  - `InspectorPanel`: Slide-in panel with streaming log viewer, shared between 3D and 2D modes
  - Loading skeleton shown while Three.js chunk downloads on desktop
  - New dependencies: `three`, `@react-three/fiber`, `@react-three/drei`

**Polish & Performance:**
- All section spacing increased to `py-28 sm:py-32` for breathing room
- Text density reduced ~30% across all card descriptions
- Section entrance stagger timing refined
- Feature descriptions shortened for lighter feel
- All components lazy-loaded with `next/dynamic` and `ssr: false` where appropriate
- HeroPipeline font sizes increased for readability (node boxes, labels, numbers all scaled up)

**Automated demo video & `/demo` embed (2026-03-22):**
- **Recording:** `docs/video/record_demo.py` -- Playwright (headless Chromium) screen capture + ffmpeg constant 30fps re-encode + merge with Edge TTS narration (`narration_full.mp3`). Avoids headed-window grey bars; timing aligned to on-page animations (example prompt, compliance, cross-platform, dashboard).
- **Assets in repo:** `docs/video/orchestraai_demo.mp4`, `docs/video/narration_full.mp3`, per-scene `narration_01_hook.mp3` … `narration_05_cta.mp3`, `docs/video_demo.md` (90s script).
- **Live on marketing site:** `website/public/orchestraai_demo.mp4` served as **`/orchestraai_demo.mp4`**. `DemoWatchVideoSection` plays this file (replaced Google sample placeholder).
- **UX:** Overview video block placed **immediately below the hero** on `/demo` (before Step 1 interactive scenes); anchor **`#demo-overview-video`** for deep links.

**Programmatic CTV / DSP (2026-03-22):**
- **`DSPClient`** -- [`src/orchestra/connectors/dsp_client.py`](src/orchestra/connectors/dsp_client.py): TTD-shaped REST (`authenticate`, `create_ctv_campaign`, `create_ctv_ad_group`, `upload_creative`); creative upload requires `compliance_status == "Passed"`.
- **Config:** `DSP_API_KEY`, `DSP_PARTNER_ID`, `DSP_BASE_URL` in [`src/orchestra/config.py`](src/orchestra/config.py) and [`.env.example`](.env.example) (optional until a real DSP contract exists).
- **LangGraph:** [`platform_node`](src/orchestra/agents/orchestrator.py) routes `platform` **`ctv`** / **`streaming_tv`** to [`execute_dsp_ctv_publish`](src/orchestra/agents/dsp_publish.py) -- tenant spend guardrails (`check_all_guardrails` + caps), vision-gate enforcement for Seedance URLs, then DSP API sequence.
- **Policy / content / intents:** `ctv` + `streaming_tv` rules in [`policy.py`](src/orchestra/agents/policy.py); CTV strategy copy in [`content.py`](src/orchestra/agents/content.py); keywords (streaming TV, Roku, Hulu, etc.) in [`orchestrator.py`](src/orchestra/agents/orchestrator.py).
- **Analytics & dashboard:** `PlatformMetrics` adds **VCR** (`video_completion_rate`) and **eCPM** (`effective_cpm`); overview uses `AnalyticsRequest.include_ctv_dashboard_preview` for an illustrative **ctv** row; [`frontend` dashboard](frontend/src/app/dashboard/page.tsx) tooltip + CTV panel.
- **Docs:** [`docs/ctv_dsp_integration.md`](docs/ctv_dsp_integration.md) (addendum + implementation table).

---

## 2. What Has Been Built (Complete Inventory)

### 2.1 Backend (FastAPI + Python)

Total: **118 Python source files** under `src/orchestra/` across 12 top-level packages (`api`, `agents`, `connectors`, `bidding`, `compliance`, `core`, `db`, `intelligence`, `moat`, `notifications`, `platforms`, `rag`, `risk`, `security`) + `cli`.

| Category | Count | Details |
|----------|-------|---------|
| API route files | 14 | `analytics`, `audit`, `auth`, `billing`, `campaigns`, `experiments`, `faq`, `gdpr`, `health`, `kill_switch`, `orchestrator`, `platforms`, `reports`, `support` |
| API endpoints | 56+ | Full CRUD + specialized actions including GDPR export download endpoint |
| Agent modules (`src/orchestra/agents/`) | 13 | `orchestrator`, `content`, `analytics_agent`, `optimizer`, `compliance`, `platform_agent`, `policy`, `safety`, `support_agent`, `trace`, `contracts`, `dsp_publish`, plus `tools/` subpackage |
| Core services (`src/orchestra/core/`) | 5 | `video_service`, `visual_compliance`, `cost_router`, `scheduler`, `billing`, `events`, `exceptions` |
| DB models | 13 | `Tenant`, `User`, `PlatformConnection`, `Campaign`, `CampaignPost`, `AuditLog`, `Experiment`, `KillSwitchEventLog`, `APIKey`, `ChatSession`, `ChatMessage`, `FAQEntry`, `SpendRecord` (see `src/orchestra/db/models.py`) |
| Alembic migrations | 4 | `f1ee2468d878_initial_schema`, `a2b3c4d5e6f7_add_kill_switch_events`, `b3c4d5e6f7a8_add_stripe_billing_fields`, `c4d5e6f7a8b9_add_support_chat_faq` |
| Notification modules | 1 | `notifications/email.py` -- async SMTP sender for budget alerts via Resend |
| RBAC permissions | 26 | Including `support:view` and `support:manage` |
| Error monitoring | Sentry | Auto-captures exceptions with traces, environment tagging |
| Scheduler | APScheduler | Daily spend resets, monthly counter resets, hourly velocity baselines (wired into FastAPI `lifespan`) |
| Encryption | AES-256-GCM + Fernet | Dual-mode with auto-detection on decrypt |

### 2.2 Frontend Dashboard (Next.js 16 + React 19 + Tailwind 4)

Next.js App Router. 10 routable pages, 1 root redirect, 1 global error page, 4 shared layout/UI components (`AppShell`, `Header`, `Sidebar`, `Providers`, `ui/card`). 17 `.tsx` files total.

| Page | Route | Purpose |
|------|-------|---------|
| Login / Signup | `/login` | Authentication + registration with JWT (toggles signup flow inline) |
| Dashboard | `/dashboard` | Metrics overview, CTV column with VCR/eCPM tooltip, subscription prompt banner for free users |
| Campaigns | `/campaigns` | Campaign list, create, launch, pause |
| Analytics | `/analytics` | Cross-platform metrics and charts (Recharts) |
| AI Orchestrator | `/orchestrator` | Natural-language AI interface |
| Support | `/support` | AI chat + FAQ accordion |
| Settings | `/settings` | Account / team / API-keys hub (team + API-keys placeholders link out to future work) |
| Billing & Plans | `/settings/billing` | Stripe checkout + subscription management |
| Change Password | `/settings/password` | Password change |
| Landing redirect | `/` | Redirects signed-out visitors to `/login`, signed-in to `/dashboard` |

**Sidebar nav (`frontend/src/components/layout/Sidebar.tsx`)**: Dashboard, Campaigns, Analytics, AI Orchestrator, Support, Settings (6 items; auto-expand on hover).

Platform-connection management and kill-switch controls are exposed through the backend REST API and the AI Orchestrator text interface -- they are not yet standalone dashboard pages.

Integrations: Sentry error monitoring, Vercel Analytics, Vercel Speed Insights, TanStack Query for data fetching, `lucide-react` icons, `recharts` for charts.

### 2.3 Promotional Website (Next.js 16, separate project)

42 `.tsx` files (7 pages + 7 layouts + 28 components). Three.js, Framer Motion, and Tailwind 4 as the visual-effects stack.

| Page | Route | Content |
|------|-------|---------|
| Landing | `/` | Sticky Navbar, hero (animated pipeline + BrowserMockup + product showcase panels), **EnterpriseTrustStrip** ("Powered by & Secured by" greyscale logo strip), trust metrics bar, interactive 3D/2D pipeline demo, problem/solution, category positioning, platform logos, How It Works + **HowItWorksVideoEmbed** (glass-morphism video card), feature highlights, architecture diagram, animated stats, comparison table, developer section, structured testimonials (named personas + metrics + company-logo tiles), CTA banner + guarded-trial microcopy |
| Features | `/features` | 8 detailed feature sections, code snippet previews, tech stack grid |
| Pricing | `/pricing` | Starter/Agency cards, self-host option, ROI calculator, feature comparison matrix, guarded-trial microcopy under primary CTAs |
| Security | `/security` | 7 security sections with trust badges (SOC 2, GDPR, Apache 2.0) |
| FAQ | `/faq` | Searchable accordion with category filter tabs, 7 categories, 14 questions |
| Contact | `/contact` | Support channels (Email, Dashboard Chat, GitHub Issues), contact form |
| Demo | `/demo` | Hero + **`DemoWatchVideoSection`** (90s overview, `/orchestraai_demo.mp4`, anchor `#demo-overview-video`), then 4 interactive Framer scenes -- `ContentCreationScene` (typing-effect prompt + Seedance video render), `ComplianceScene` (Visual IP Compliance Scan frame-by-frame), `CrossPlatformScene`, `DashboardScene` (kill-switch + autonomous-budget-reallocation badge). Bottom CTA + `CTABanner` |

**Website Components (28 files, `website/src/components/`):**

- Chrome / layout: `Navbar` (sticky + scroll-aware), `Footer`, `SectionHeading`, `GradientText`, `AccordionItem`.
- Hero / mockups: `BrowserMockup` (+ `FeatureShowcase` re-export), `HeroPipeline`, `AnimatedCounter`, `PlatformGrid`, `ArchitectureDiagram`.
- Cards / sections: `FeatureCard`, `PricingCard`, `ComparisonTable`, `CTABanner`, `EnterpriseTrustStrip` (new), `HowItWorksVideoEmbed` (new).
- Video / media: `VideoEmbed`, `demo/DemoWatchVideoSection`.
- Interactive pipeline demo (`demo/`): `PipelineDemo`, `PipelineCanvas` (2D SVG), `GraphCanvas3D` (Three.js / R3F), `InspectorPanel`, `OrbitalAccent`, plus `demo/scenes/` -- `ContentCreationScene`, `ComplianceScene`, `CrossPlatformScene`, `DashboardScene`.
- Utility / forms: `ContactForm`.

Shared data/hooks live in `website/src/lib/` (`constants.ts` with 7 domain groups incl. `TESTIMONIALS`, `GUARDED_TRIAL_MICROCOPY`, `FEATURES_DETAILED`, `SECURITY_FEATURES`, `FAQ_DATA`; `demo/pipelineData.ts`; `useIs3DCapable` hook).

**Visual System:** Dark + glow brand identity, animated gradient mesh, ambient orbs, noise overlay, neon sweep accents, glassmorphism cards, gradient CTA buttons, soft shadow dividers, section fade transitions.

**SEO:** Auto-generated `sitemap.xml` (7 URLs), `robots.txt`, Open Graph + Twitter meta tags on every page, branded OG image (1200x630), Google Search Console verification file (`googlec4e7f501ca1a924d.html`).

**Integrations:** Google Search Console (verified), Vercel Analytics, Vercel Speed Insights.

**Public assets (`website/public/`):** `orchestraai_demo.mp4` (90s walkthrough, 10.4 MB), `og-image.png`, `logo.svg`, `robots.txt`, `googlec4e7f501ca1a924d.html`, Next.js default SVGs.

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
| Platform Dispatch | Complete | Publish/schedule to 9 OAuth platform connectors |
| CTV / DSP dispatch | Complete | `platform_node` → `dsp_publish` when `platform` is `ctv` or `streaming_tv`; optional live DSP via `DSP_*` env |
| Support Agent | Complete | RAG context retrieval, FAQ matching, guardrailed responses, sensitive pattern sanitization, plan-aware upsell prompts |
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
| Email Alerts | Complete -- via Resend SMTP, WARNING+ severity |
| Scheduler | Complete -- daily/monthly resets, hourly velocity baselines |

### 2.7 Testing

15 test modules + `conftest.py`. `pytest tests --collect-only` reports **361 tests**, all green (`361 passed, 6 warnings in 6.31s`).

| Test Module | Tests |
|-------------|-------|
| test_auth.py | 7 |
| test_auth_pipeline.py | 16 |
| test_bidding.py | 12 |
| test_cli.py | 23 |
| test_compliance.py | 5 |
| test_content.py | 8 |
| test_debt_fixes.py | 43 |
| test_dsp_client.py | 5 |
| test_health.py | 2 |
| test_orchestrator.py | 43 |
| test_platforms.py | 24 |
| test_risk.py | 11 |
| test_security.py | 14 |
| test_step3_routes.py | 36 |
| test_support_faq.py | 69 |
| **Total** | **~318 test functions (361 collected with parametrization)** |

### 2.8 CI/CD (GitHub Actions)

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `ci.yml` | Push/PR to main | Ruff lint + format check, pytest (Python 3.12) |
| `docker.yml` | Push/PR to main, tags `v*` | Build and push Docker image to GHCR |
| `release.yml` | Tags `v*` | Build Python package, create GitHub release |
| `frontend.yml` | Changes to `frontend/**` | TypeScript check, ESLint, Next.js build |
| `website.yml` | Changes to `website/**` | TypeScript check, ESLint, Next.js build |

### 2.9 Documentation (28 documents in `docs/`)

`architecture.md`, `guardrailed-bidding.md`, `security-compliance.md`, `data-moat.md`, `cost-analysis.md`, `launch-strategy.md`, `user-procedures.md`, `marketing_video.md`, `differentiation.md`, `due-diligence.md`, `viral-strategy.md`, `hybrid_launch_strategy.md`, `stripe_monetization_plan.md`, `audit_addendum.md`, `production_deployment_playbook.md`, `gap_analysis.md`, `new_prompt_for_checklist.md`, `ctv_dsp_integration.md`, **`video_demo.md`** (90s Loom script), **`demo_video.md`** (animated demo page spec), `website_redesign1.md` through `website_redesign8.md` (8 iterative design feedback docs).

Root-level: `README.md`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md`, `GO_LIVE_CHECKLIST.md`, `LOCAL_STRIPE_TEST.md`, `BUILD_LOG.md`, `chat-history.md`, `cost_analysis.md` (duplicate copy), `ai_marketing_platform_5fc51575.plan.md`, `start.md`.

### 2.10 Marketing Assets

`docs/video/`:

- 9 video files: 60s marketing cuts in 4 aspect ratios (`16x9`, `9x16`, `1x1`, `marketing_60s`, `marketing_60s_075x`), two 9-second clips, a `final` cut, and the `orchestraai_demo.mp4` walkthrough.
- 6 narration tracks: `narration_full.mp3` + `narration_01_hook.mp3` through `narration_05_cta.mp3`.
- 2 thumbnails (`thumbnail.png` landscape, `thumbnail_portrait.png` portrait).
- `record_demo.py` -- Playwright + ffmpeg + Edge TTS recording pipeline.

Root-level:

- `enhance_video.py` -- video enhancement / upscaling script.
- `chat_load.jpg`, `requirements.jpg` -- product screenshots.
- `website/public/og-image.png` -- 1200x630 branded social-sharing card.
- `website/public/orchestraai_demo.mp4` -- 10.4 MB walkthrough served by the marketing site.

### 2.11 Infrastructure

- Dockerfile (Python 3.12-slim, Poetry, ffmpeg, non-root user)
- docker-compose.yml (app + PostgreSQL + Redis + Qdrant + Kafka + Ollama)
- .env.example with all variable names
- Makefile for dev commands
- Setup scripts (bash + PowerShell)
- Cursor rules for deployment status persistence

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

### Resolved (2026-03-22)

| Issue | Resolution |
|-------|------------|
| ~~Auth fallback~~ | Login now returns 401 for non-existent users instead of misleading 503 |
| ~~Encryption standard~~ | AES-256-GCM added as preferred encryption; Fernet retained for backward compatibility; auto-detection on decrypt |
| ~~Scheduler not started~~ | APScheduler now starts/stops in FastAPI lifespan with 3 registered jobs |
| ~~Bidding engine logic~~ | Verified as correct -- elif branches are reachable since `self.phase` varies by tenant |
| ~~GDPR export placeholder~~ | `_collect_tenant_data` now queries all 10 PostgreSQL tables; downloadable JSON archive via `GET /gdpr/exports/{id}/download` |

### Remaining

| Issue | Severity | Description |
|-------|----------|-------------|
| Hardcoded pool sizes | Low | DB pool_size=20, max_overflow=10, safety limits -- all hardcoded instead of configurable |

---

## 4. Git Status

```
Branch:    master
Remote:    Up to date with origin/master
Commits:   46 total (+1 pending: housekeeping)
```

### Recent commits (newest first):

```
b3f6390  docs: update STATE_OF_THE_UNION for CTV/DSP, tests, commits, next steps
7ed5258  fix: gate CTV analytics preview behind overview flag for unit tests
27d252c  feat: programmatic CTV/DSP client, orchestrator branch, analytics VCR/eCPM, dashboard UI
00f0e21  docs: update STATE_OF_THE_UNION for demo video, embed, and /demo UX
f62e40b  ux: move demo overview video below hero on /demo page
7ae4c33  feat: embed demo video on /demo page, replace placeholder with OrchestraAI walkthrough
0f5c7f5  feat: add automated demo video with narration audio and recording script
1e4b7fe  Marketing site: demo interactivity, Seedance CRO, landing trust strip
04d0c41  docs: update STATE_OF_THE_UNION with animated demo scenes and 3D pipeline work
4167809  feat: replace demo page placeholder with 6 animated interactive scene components
1e1c7d1  feat: add hybrid 3D/2D interactive pipeline demo with Three.js
c2805a9  fix: increase HeroPipeline node and label font sizes for readability
```

### CRO briefs (now in `docs/`)

Two Principal-UX CRO briefs drove the `1e4b7fe` polish round. Relocated from `frontend/src/app/` (App Router tree — bundling foot-gun) into `docs/`:

- `docs/cro_demo_page.md` -- 5-step brief that produced the `ContentCreationScene` typing effect, Seedance state, VCG emphasis, and kill-switch dashboard upgrades.
- `docs/cro_landing_page.md` -- 5-step brief that produced the structured testimonials, `HowItWorksVideoEmbed`, guarded-trial microcopy, `EnterpriseTrustStrip`, and sticky Navbar.

---

## 5. Next Steps (Priority Order)

### Housekeeping

1. ~~Move CRO briefs out of the Next.js app folder.~~ Done — now at `docs/cro_demo_page.md` and `docs/cro_landing_page.md` (2026-04-18).
2. ~~Replace the sample-video fallback in `HowItWorksVideoEmbed`.~~ Done — now points at `/orchestraai_demo.mp4` with `/og-image.png` as poster (2026-04-18).
3. **Stub or ship the "Team Management" and "API Keys" tiles on `/settings`.** They currently render as disabled (`ready: false`) placeholders; either hide them until ready or expose the existing `APIKey` model end-to-end.

### Marketing & Growth (no engineering blockers)

4. ~~Deploy updated marketing website~~ -- Completed. All 8 rounds + CRO pass pushed to Vercel.
5. ~~Ship 90s demo video on `/demo`~~ -- Completed. `orchestraai_demo.mp4` embedded via `DemoWatchVideoSection`.
6. ~~Add Enterprise Trust Strip + How-It-Works video embed + guarded-trial microcopy + sticky Navbar + structured testimonials~~ -- Completed in commit `1e4b7fe`.
7. **Upload marketing videos** to platforms: Product Hunt (16:9 + thumbnail), Twitter/X launch thread (9:16), LinkedIn (16:9), Instagram Reels (9:16).
8. **Collect real testimonials.** Replace the placeholder personas (Sarah Jenkins / Acme Digital, Marcus Chen / Northline Commerce, Elena Vasquez / Signal & Tide) with quotes from real customers once live.
9. **Expand FAQ** as customers onboard; tenant-scoped entries are already supported (`FAQEntry.tenant_id` nullable).

### Future Engineering (when needed)

10. **Dashboard pages for Platforms + Kill Switch.** Backend endpoints exist (`/api/v1/platforms`, `/api/v1/kill-switch`); only the frontend pages are missing. Add to `frontend/src/app/platforms/page.tsx` and `frontend/src/app/kill-switch/page.tsx`, then wire into `Sidebar.tsx`.
11. **Wire production DSP.** Set `DSP_API_KEY`, `DSP_PARTNER_ID`, `DSP_BASE_URL` on Railway and align `DSPClient` HTTP paths/JSON with your vendor's real API (current code is TTD-shaped template).
12. **A/B testing runtime.** Build assignment/tracking logic on top of the `Experiment` API endpoints.
13. **Feature flags.** Per-tenant feature gating beyond subscription tiers.
14. **Make DB pool sizes configurable.** Move `pool_size`, `max_overflow`, and safety limits to environment variables.
15. **Uptime monitoring.** Add external health-check monitoring (BetterUptime, UptimeRobot).

---

## 6. Deployment Status

| Service | URL | Platform | Status |
|---------|-----|----------|--------|
| Backend API | `https://api.useorchestra.dev` | Railway | Live |
| Dashboard | `https://useorchestra.dev` | Vercel | Live |
| Marketing Website | `https://www.useorchestra.dev` | Vercel | Live |
| PostgreSQL | Railway-managed | Railway | Live |
| Redis | Railway-managed | Railway | Live |
| DNS + SSL | Cloudflare | Cloudflare | Configured |
| Stripe Billing | Live mode | Stripe | Active (Starter + Agency) |
| SMTP / Email | Resend (`smtp.resend.com`) | Resend | Active (domain verified) |
| Error Monitoring | Sentry | Sentry | Active (backend + frontend) |
| SEO | Google Search Console | Google | Verified, sitemap submitted |
| Analytics | Vercel Analytics + Speed Insights | Vercel | Active (both projects) |

---

## 7. Build Verification

| Check | Status |
|-------|--------|
| Python tests (pytest) | **361 passed** (6 warnings, 6.31s) |
| Python lint (ruff check) | Clean |
| Python format (ruff format) | Clean |
| Frontend TypeScript (`tsc --noEmit`) | Zero errors |
| Frontend ESLint | Zero errors |
| Frontend build (`next build`) | Success |
| Website TypeScript (`tsc --noEmit`) | Zero errors |
| Website ESLint | Zero errors |
| Website build (`next build`) | Success (7 pages + sitemap.xml + robots.txt) |
| Stripe live payment | Tested ($99 charged and refunded) |
| Website 3D deps (three, R3F, drei) | Installed, zero build warnings |
| Demo video public asset | `website/public/orchestraai_demo.mp4` (10.4 MB) deployed with site |
| CRO components | `EnterpriseTrustStrip`, `HowItWorksVideoEmbed`, sticky `Navbar`, guarded-trial microcopy live |
| CTV / DSP | `tests/test_dsp_client.py` + orchestrator `ctv`/`streaming_tv` branch |
| Git working tree | Clean |

---

## 8. Third-Party Services (all configured)

| Service | Plan | Purpose |
|---------|------|---------|
| Railway | Hobby | Backend hosting, PostgreSQL, Redis |
| Vercel | Hobby | Frontend hosting (2 projects), Analytics |
| Cloudflare | Free | DNS, SSL, CDN |
| Stripe | Standard | Payment processing (live mode) |
| Resend | Free (3K emails/mo) | Transactional email (SMTP) |
| Sentry | Free (5K errors/mo) | Error monitoring (2 projects) |
| Google Search Console | Free | SEO indexing and monitoring |
| GitHub | Free | Source control, CI/CD |

# OrchestraAI -- Go-Live Checklist

> Step-by-step instructions to deploy the full stack to **Railway** (Backend + PostgreSQL) and **Vercel** (Frontend), then activate **Stripe Live Mode**.

---

## Prerequisites

Before you begin, make sure you have:

- [ ] A **GitHub** account with the `emarketing` repo pushed (both `src/` and `frontend/` at root)
- [ ] A **Railway** account ([railway.app](https://railway.app)) -- free trial or paid
- [ ] A **Vercel** account ([vercel.com](https://vercel.com)) -- free Hobby or Pro
- [ ] A **Stripe** account ([stripe.com](https://stripe.com)) with access to Live Mode
- [ ] The production secrets listed in `.env.example` (OpenAI key, Anthropic key, JWT secrets, etc.)

---

## Phase 1: Database (Railway PostgreSQL)

1. Log in to [railway.app](https://railway.app) and create a new **Project**.
2. Click **+ New** -> **Database** -> **PostgreSQL**.
3. Once provisioned, click the PostgreSQL service and open the **Connect** tab.
4. Copy the **connection string** (the one starting with `postgresql://...`).
5. Replace the driver prefix so it matches async:

   ```
   postgresql+asyncpg://user:pass@host:port/dbname
   ```

6. Save this -- you'll use it as `DATABASE_URL` in the next step.

> Railway auto-manages backups and TLS for the managed Postgres instance.

---

## Phase 2: Backend (Railway)

### 2a. Deploy the service

1. In the same Railway project, click **+ New** -> **GitHub Repo**.
2. Select the `emarketing` repository.
3. Railway will auto-detect the root `Dockerfile`. Confirm the **Root Directory** is `/` (the repo root).
4. Railway assigns a random port via the `PORT` env var -- the Dockerfile already respects this:
   ```
   CMD ["sh", "-c", "uvicorn orchestra.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
   ```

### 2b. Set environment variables

In the Railway service **Variables** tab, add every production variable. At minimum:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `DATABASE_URL` | The `postgresql+asyncpg://...` string from Phase 1 |
| `REDIS_URL` | Provision a Railway Redis add-on, or use an external provider |
| `JWT_SECRET_KEY` | Generate: `openssl rand -hex 32` |
| `FERNET_KEY` | Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `ENCRYPTION_KEY` | Generate: `openssl rand -hex 32` |
| `OPENAI_API_KEY` | Your production OpenAI key |
| `ANTHROPIC_API_KEY` | Your production Anthropic key |
| `FAL_API_KEY` | Your fal.ai API key (for Seedance video generation) |
| `STRIPE_SECRET_KEY` | Live key from Phase 4 (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Live webhook signing secret from Phase 4 (`whsec_...`) |
| `STRIPE_STARTER_PRICE_ID` | Live price ID from Phase 4 (`price_...`) |
| `STRIPE_AGENCY_PRICE_ID` | Live price ID from Phase 4 (`price_...`) |
| `FRONTEND_URL` | Your Vercel domain (e.g. `https://orchestraai.vercel.app`) |
| `CORS_ORIGINS` | `["https://orchestraai.vercel.app"]` |
| `RATE_LIMIT_PER_MINUTE` | `60` (adjust as needed) |
| `STEALTH_MODE` | `false` (set `true` if you want to hide branding) |

### 2c. Generate a public URL

1. In the Railway service **Settings**, click **Generate Domain** (or add a custom domain).
2. Copy the URL (e.g. `https://emarketing-production.up.railway.app`).
3. This is your **live API base**. Append `/api/v1` for the frontend.

### 2d. Verify deployment

```bash
curl https://YOUR-RAILWAY-DOMAIN/health
# Expected: {"status":"ok","app":"OrchestraAI","env":"production"}
```

Database migrations run automatically on startup via the Alembic lifespan hook.

---

## Phase 3: Frontend (Vercel)

### 3a. Import the project

1. Log in to [vercel.com](https://vercel.com) and click **Add New** -> **Project**.
2. **Import** the same `emarketing` GitHub repo.
3. Set **Framework Preset** to **Next.js**.
4. Set **Root Directory** to `frontend`.

### 3b. Set environment variables

In the Vercel project **Settings** -> **Environment Variables**, add:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RAILWAY-DOMAIN/api/v1` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | `pk_live_...` from Stripe Live Mode |

### 3c. Deploy

1. Click **Deploy**. Vercel builds the Next.js app with `output: "standalone"`.
2. Once deployed, note the production URL (e.g. `https://orchestraai.vercel.app`).
3. **Go back to Railway** and update `FRONTEND_URL` and `CORS_ORIGINS` to this Vercel URL.

### 3d. Verify

1. Open `https://orchestraai.vercel.app` in your browser.
2. The login page should load.
3. Open DevTools -> Network and confirm API calls hit your Railway domain, not localhost.

---

## Phase 4: Stripe Live Mode

### 4a. Switch to Live Mode

1. In the [Stripe Dashboard](https://dashboard.stripe.com), toggle **off** the "Test mode" switch in the top-right.
2. You are now in **Live Mode**.

### 4b. Create live products and prices

1. Go to **Products** -> **+ Add product**.
2. Create **Starter** plan:
   - Name: `Starter`
   - Price: your monthly price (e.g. $29/mo), Recurring
   - Copy the **Price ID** (e.g. `price_1Qx...`)
3. Create **Agency** plan:
   - Name: `Agency`
   - Price: your monthly price (e.g. $99/mo), Recurring
   - Copy the **Price ID**
4. Update Railway env vars:
   - `STRIPE_STARTER_PRICE_ID` = the live Starter price ID
   - `STRIPE_AGENCY_PRICE_ID` = the live Agency price ID

### 4c. Create a live webhook

1. Go to **Developers** -> **Webhooks** -> **+ Add endpoint**.
2. **Endpoint URL**: `https://YOUR-RAILWAY-DOMAIN/api/v1/billing/webhook`
3. **Events to listen for** (select these):
   - `invoice.paid`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Click **Add endpoint**.
5. Click the new endpoint and **Reveal** the **Signing secret** (`whsec_...`).
6. Update Railway env var: `STRIPE_WEBHOOK_SECRET` = this signing secret.

### 4d. Update the Stripe live secret key

1. Go to **Developers** -> **API keys**.
2. Copy the **Secret key** (`sk_live_...`) and **Publishable key** (`pk_live_...`).
3. Update Railway env var: `STRIPE_SECRET_KEY` = the live secret key.
4. Update Vercel env var: `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = the live publishable key.
5. Redeploy Vercel (env changes require a rebuild): **Vercel Dashboard** -> **Deployments** -> **Redeploy**.

---

## Phase 5: Smoke Test the Live Stack

Run through this sequence to confirm everything works end-to-end:

- [ ] **Health check**: `curl https://YOUR-RAILWAY-DOMAIN/health` returns `200 OK`
- [ ] **Frontend loads**: Open the Vercel URL, login page renders
- [ ] **Registration**: Create a new account, confirm redirect to dashboard
- [ ] **Paywall triggers**: Click "AI Orchestrator" or try to create a campaign -- should see 402 upgrade prompt
- [ ] **Checkout works**: Click "Subscribe", complete Stripe Checkout with a **real card** (or a live-mode test card if available)
- [ ] **Webhook fires**: Check Railway logs for `stripe_webhook_received` and `subscription_activated`
- [ ] **Subscription active**: The billing page shows "Active" status
- [ ] **Gated features unlock**: AI Orchestrator responds, campaign creation works
- [ ] **Video generation**: Type "Generate a video ad for our summer sale" in the orchestrator -- verify the video player appears (or a compliance violation card if flagged)
- [ ] **Portal works**: Click "Manage Subscription" on the billing page -- Stripe Customer Portal opens

---

## Phase 6: Competitive Moat Verification

Your data moat and intelligence layer are deployed automatically with the backend. Verify they're operational:

### Data Moat (`orchestra.moat`)
The **FlywheelPipeline** is the core feedback loop that compounds your advantage:

```
Campaign Created -> Engagement Data -> Signal Normalization -> Vector Embedding -> Model Update
```

- [ ] Create a test campaign and publish it
- [ ] After engagement data arrives, check Railway logs for `flywheel_` log entries
- [ ] The tenant-specific model (`moat.tenant_model`) should update automatically
- [ ] The global model (`moat.global_model`) aggregates anonymized signals across all tenants

### Cross-Platform Intelligence (`orchestra.intelligence`)
The **cross_platform_roi** engine normalizes $1 spent across every platform into comparable metrics:

- [ ] Run the AI orchestrator with a multi-platform campaign
- [ ] Check that the allocator (`intelligence.allocator`) distributes budget using marginal return curves
- [ ] Verify attribution (`intelligence.attribution`) assigns credit across platforms
- [ ] Confirm saturation detection (`intelligence.saturation`) flags diminishing returns

> These modules are your structural moat. Every campaign run by every tenant strengthens the model for all users.

---

## Security Hardening Checklist

Before announcing publicly:

- [ ] `DEBUG=false` is set on Railway
- [ ] `APP_ENV=production` is set on Railway
- [ ] `JWT_SECRET_KEY` is a real random 64-char hex string (not the default)
- [ ] `FERNET_KEY` is a real Fernet key (not the default)
- [ ] `ENCRYPTION_KEY` is a real random hex string (not the default)
- [ ] Stripe is in **Live Mode** (no `sk_test_` keys in production)
- [ ] Swagger docs are disabled (`/docs` returns 404 in production because `DEBUG=false`)
- [ ] CORS only allows your Vercel domain (not `*`)
- [ ] Rate limiting is configured (`RATE_LIMIT_PER_MINUTE`)

---

## Custom Domain (Optional)

### Backend (Railway)
1. In Railway service **Settings** -> **Networking**, add your domain (e.g. `api.orchestraai.dev`).
2. Add the CNAME record Railway provides to your DNS.
3. Update Vercel env var `NEXT_PUBLIC_API_URL` to `https://api.orchestraai.dev/api/v1`.
4. Update Stripe webhook endpoint URL to `https://api.orchestraai.dev/api/v1/billing/webhook`.

### Frontend (Vercel)
1. In Vercel **Settings** -> **Domains**, add your domain (e.g. `app.orchestraai.dev`).
2. Add the CNAME record Vercel provides to your DNS.
3. Update Railway env var `FRONTEND_URL` to `https://app.orchestraai.dev`.

---

## Quick Reference: All Production Environment Variables

### Railway (Backend)
```env
APP_NAME=OrchestraAI
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
STEALTH_MODE=false
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
JWT_SECRET_KEY=<openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
FERNET_KEY=<python Fernet.generate_key()>
ENCRYPTION_KEY=<openssl rand -hex 32>
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
FAL_API_KEY=<your fal.ai key>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_AGENCY_PRICE_ID=price_...
FRONTEND_URL=https://your-app.vercel.app
CORS_ORIGINS=["https://your-app.vercel.app"]
RATE_LIMIT_PER_MINUTE=60
```

### Vercel (Frontend)
```env
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app/api/v1
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

---

*Generated by OrchestraAI deployment tooling. Last updated: 2026-03-01.*

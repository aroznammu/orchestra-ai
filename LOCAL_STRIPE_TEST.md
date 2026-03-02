# Local Stripe End-to-End Test Playbook

This document walks through a complete payment-loop test on localhost:
register, hit the paywall, subscribe via Stripe test checkout, and verify
the tenant transitions from `trialing` to `active`.

---

## Prerequisites

| Component          | Expected State                                         |
| ------------------ | ------------------------------------------------------ |
| Docker Compose     | All services running (`docker compose ps` -- all Up)   |
| Backend (FastAPI)  | Listening on `http://localhost:8000`                    |
| Frontend (Next.js) | Listening on `http://localhost:3000`                    |
| Stripe CLI         | Forwarding webhooks (see Step 2 below)                 |
| Database           | Migrations applied (`alembic_version = b3c4d5e6f7a8`)  |

---

## Step 1 -- Boot the Infrastructure

If the stack is not already running:

```bash
# Terminal 1: Start all backend services (Postgres, Redis, Kafka, Qdrant, Ollama, FastAPI)
docker compose up -d

# Terminal 2: Start the Next.js frontend
cd frontend
npm run dev
```

Verify:
- `http://localhost:8000/health` returns `{"status": "ok"}`
- `http://localhost:3000` loads the OrchestraAI login page

---

## Step 2 -- Start the Stripe CLI Webhook Forwarder

In a **new terminal**, run:

```bash
stripe listen --forward-to http://localhost:8000/api/v1/billing/webhook
```

The CLI will print a webhook signing secret like:

```
Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important:** If the printed secret differs from the `STRIPE_WEBHOOK_SECRET`
in your `.env` file, update `.env` to match, then restart the backend:

```bash
docker compose restart app
```

The current `.env` value should already match because the Stripe CLI was
previously authenticated with this account.

---

## Step 3 -- Register a Fresh Test Account

Open `http://localhost:3000/login` in your browser.

Since you may not remember existing test-user passwords, register a brand-new
account via curl. Run this in a terminal:

```bash
curl -s http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "stripe-test@orchestraai.dev",
    "password": "TestPass123!",
    "full_name": "Stripe Tester",
    "tenant_name": "Stripe Test Org"
  }'
```

The response returns an `access_token`. You can ignore it -- you will log in
via the UI next.

---

## Step 4 -- Log In via the UI

1. Open `http://localhost:3000/login`
2. Enter email: `stripe-test@orchestraai.dev`
3. Enter password: `TestPass123!`
4. Click **Sign in** -- you should land on `/dashboard`

---

## Step 5 -- Hit the 402 Paywall

The new account starts with `subscription_status = trialing` and
`subscription_plan = free`. Gated actions should still work during trial.
To observe the paywall, we first need to expire the trial:

```bash
docker exec emarketing-postgres-1 psql -U orchestra -d orchestraai \
  -c "UPDATE tenants SET subscription_status = 'expired'
      WHERE slug = (SELECT slug FROM tenants
                    JOIN users ON users.tenant_id = tenants.id
                    WHERE users.email = 'stripe-test@orchestraai.dev');"
```

Now test the paywall:

### Option A: Orchestrator Paywall
1. Navigate to `http://localhost:3000/orchestrator`
2. Type any message and press Enter
3. A fullscreen **"Upgrade to Enterprise Cloud"** modal should appear
4. Click **"View Plans & Upgrade"** -- you should land on `/settings/billing`

### Option B: Campaigns Paywall
1. Navigate to `http://localhost:3000/campaigns`
2. Click **"New Campaign"**, fill in a name, and click **Create Campaign**
3. The same upgrade modal should appear inside the creation dialog

---

## Step 6 -- Subscribe via Stripe Test Checkout

1. Go to `http://localhost:3000/settings/billing`
2. You should see two plan cards: **Starter ($99/mo)** and **Agency ($999/mo)**
3. Click **Subscribe** on either plan (Starter is fine for testing)
4. You will be redirected to a Stripe Checkout page

### Fill in Stripe test card details:

| Field            | Value                                    |
| ---------------- | ---------------------------------------- |
| Card number      | `4242 4242 4242 4242`                    |
| Expiry           | Any future date (e.g. `12/30`)           |
| CVC              | Any 3 digits (e.g. `123`)               |
| Name on card     | Any name                                 |
| Country/ZIP      | United States / Any ZIP (e.g. `10001`)   |

5. Click **Subscribe** on the Stripe page
6. You will be redirected back to `/settings/billing?status=success`
7. A green banner should read: **"Subscription activated successfully!"**

### What happens behind the scenes:

```
Browser -> Stripe Checkout -> Stripe sends invoice.paid webhook
                                  |
                                  v
Stripe CLI --forward-to--> POST /api/v1/billing/webhook
                                  |
                                  v
                           billing.py handles event:
                           - Sets subscription_status = "active"
                           - Sets subscription_plan = "starter"
                           - Stores stripe_subscription_id
```

---

## Step 7 -- Verify Subscription Activation

### Via the UI

The billing page should now show:
- **Current plan:** `starter` (or `agency`)
- **Status:** `active` (green)
- A **"Manage Subscription"** button should appear

### Via the Database

```bash
docker exec emarketing-postgres-1 psql -U orchestra -d orchestraai \
  -c "SELECT t.name, t.subscription_status, t.subscription_plan,
             t.stripe_customer_id, t.stripe_subscription_id
      FROM tenants t JOIN users u ON u.tenant_id = t.id
      WHERE u.email = 'stripe-test@orchestraai.dev';"
```

Expected output:

```
      name        | subscription_status | subscription_plan | stripe_customer_id | stripe_subscription_id
------------------+---------------------+-------------------+--------------------+------------------------
 Stripe Test Org  | active              | starter           | cus_xxxxxxxxxxxxx  | sub_xxxxxxxxxxxxx
```

### Via the API

```bash
# First, get a token
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "stripe-test@orchestraai.dev", "password": "TestPass123!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Check billing status
curl -s http://localhost:8000/api/v1/billing/status \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Expected response:

```json
{
    "plan": "starter",
    "status": "active",
    "stripe_customer_id": "cus_xxxxxxxxxxxxx",
    "has_subscription": true,
    "plan_expires_at": null
}
```

---

## Step 8 -- Verify Paywall Is Lifted

1. Navigate to `http://localhost:3000/orchestrator`
2. Type a message and press Enter
3. Instead of the paywall modal, you should see the AI agent respond
   (or a timeout/error if LLM keys are not configured -- but **not** a 402)

4. Navigate to `http://localhost:3000/campaigns`
5. Click **New Campaign**, fill the form, and click **Create Campaign**
6. The campaign should be created successfully (no paywall modal)

---

## Step 9 -- Test Subscription Cancellation (Optional)

1. Go to `http://localhost:3000/settings/billing`
2. Click **"Manage Subscription"** -- opens the Stripe Customer Portal
3. Click **Cancel plan** in the portal
4. After returning, verify via DB:

```bash
docker exec emarketing-postgres-1 psql -U orchestra -d orchestraai \
  -c "SELECT subscription_status, subscription_plan
      FROM tenants t JOIN users u ON u.tenant_id = t.id
      WHERE u.email = 'stripe-test@orchestraai.dev';"
```

Expected: `subscription_status = cancelled`, `subscription_plan = free`

---

## Troubleshooting

### Webhook not arriving
- Check the Stripe CLI terminal for forwarded events
- Ensure the CLI webhook secret matches `.env` `STRIPE_WEBHOOK_SECRET`
- Run `docker compose logs app --tail 50` to check backend logs

### 402 not appearing / appearing unexpectedly
- Check `subscription_status` in the database with the SQL above
- Status must be `active` or `trialing` to pass the paywall

### Checkout redirect fails
- Ensure `FRONTEND_URL=http://localhost:3000` in `.env`
- Ensure `STRIPE_STARTER_PRICE_ID` and `STRIPE_AGENCY_PRICE_ID` match real
  Price IDs from your Stripe dashboard (Test mode)

### Frontend cannot reach backend
- Ensure CORS allows `http://localhost:3000` (check `.env` `CORS_ORIGINS`)
- Ensure `NEXT_PUBLIC_API_URL` is not set (defaults to `http://localhost:8000/api/v1`)

---

## Stripe Test Card Reference

| Scenario              | Card Number           | Behavior                  |
| --------------------- | --------------------- | ------------------------- |
| Success               | `4242 4242 4242 4242` | Payment succeeds          |
| Requires auth (3DS)   | `4000 0025 0000 3155` | Triggers 3D Secure modal  |
| Declined              | `4000 0000 0000 0002` | Card is declined          |
| Insufficient funds    | `4000 0000 0000 9995` | Insufficient funds error  |

Use any future expiry, any 3-digit CVC, and any US ZIP code.

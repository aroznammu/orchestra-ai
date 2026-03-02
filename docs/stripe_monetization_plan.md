# Addendum: Stripe Monetization & Subscription Gating

## Objective
To implement a professional B2B subscription layer for the "Enterprise Cloud Edition." This ensures that the AI Orchestrator and Platform Connectors are only accessible to paying tenants.

## Instructions for Cursor AI

Please act as a Senior Full-Stack Engineer and implement the following monetization architecture:

### 1. Database & Schema Updates
- **Models (`src/orchestra/db/models.py`):** Add the following fields to the `Tenant` model:
  - `stripe_customer_id`: String (nullable)
  - `stripe_subscription_id`: String (nullable)
  - `subscription_status`: String (default="trialing")
  - `subscription_plan`: String (default="free")
  - `plan_expires_at`: DateTime (nullable)

### 2. Backend: Stripe Integration & Gating
- **Dependencies:** Ensure `stripe` is added to `pyproject.toml`.
- **Stripe Service (`src/orchestra/core/billing.py`):** Create a service to:
  - Create Stripe Checkout sessions for "Starter" ($99/mo) and "Agency" ($999/mo) plans.
  - Handle the Stripe Webhook (`/api/v1/billing/webhook`) to update `subscription_status` on `invoice.paid` or `customer.subscription.deleted`.
- **Subscription Middleware:**
  - Create a dependency `check_active_subscription` in `src/orchestra/api/deps.py`.
  - Apply this dependency to the `/orchestrator/ask` route and all `POST` routes in `campaigns.py`.
  - If a tenant is not "active," return a `402 Payment Required` error with the message: "Subscription required to access AI agents."

### 3. Frontend: Billing UI & Checkout
- **Pricing Page (`frontend/src/app/settings/billing/page.tsx`):**
  - Create a clean "Pricing Plans" UI with two tiers: **Starter** and **Agency**.
  - Add "Subscribe" buttons that call the backend to initiate a Stripe Checkout session.
- **Billing Portal:** Add a "Manage Subscription" button that opens the Stripe Customer Portal so users can update cards or cancel.
- **Paywall UX:** Update the `OrchestratorPage` to catch the `402` error. If caught, display a professional overlay: "Upgrade to Enterprise Cloud to unlock AI Orchestration."

### 4. Security
- Verify Stripe Webhook signatures using `STRIPE_WEBHOOK_SECRET` from `.env`.
- Ensure all billing operations are scoped to the `current_user.tenant_id`.

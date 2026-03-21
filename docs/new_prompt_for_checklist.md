# 🚀 Ultimate AI Startup Platform - Cursor AI Prompt Pack

This prompt pack instructs Cursor AI to manage, develop, and optimize a fully autonomous, multi-tenant SaaS platform with:

- FastAPI backend on Cloud Run
- Supabase/Postgres multi-tenant database
- BigQuery analytics
- Stripe subscriptions
- Firebase notifications
- AI personalization agents
- Enterprise SSO/SAML onboarding
- Mobile SDK auto-generation
- Growth, acquisition, and monetization automation
- Security & compliance (JWT, RBAC, audit logging)

---

## 1 AI Startup Factory

### Objective
- Autonomously manage backend, frontend, and mobile codebase
- Continuously refactor, optimize, and extend features
- Generate new features from user feedback and analytics

### Tasks
- Refactor Python backend for performance and maintainability
- Generate and deploy FastAPI endpoints with feature flags
- Create multi-tenant database models
- Generate CI/CD pipelines for Cloud Run deployments
- Auto-generate Swift/Kotlin SDKs for mobile apps

### Outputs
- `BACKEND_TEMPLATE.md`
- `API_SPEC.md`
- `MOBILE_SDK.md`
- `FEATURE_ROADMAP.md`

### Automation
- Suggest new features based on analytics
- Generate implementation plans
- Flag major changes for review
- Auto-deploy minor improvements

---

## 2 User Feedback → Feature System

### Objective
Convert user feedback (App Store, Play Store, in-app, support tickets) into actionable features

### Pipeline
1. Collect feedback
2. Clean and normalize
3. Cluster by topic
4. Categorize: Bug / Feature Request / UX Issue
5. Prioritize by impact (frequency, severity, user impact)
6. Generate implementation tasks and feature flags

### Outputs
- `USER_FEEDBACK_INSIGHTS.md`
- `TOP_FEATURE_REQUESTS.md`

### Automation
- Generate code changes for minor features
- Suggest feature flag rollout percentages
- Require validation for major features

---

## 3️ Revenue Optimization Engine

### Objective
Maximize revenue via subscription, pricing experiments, and conversion optimization

### Tasks
- Dynamic pricing A/B experiments
- Feature gating per subscription tier
- Track conversion rates, revenue per user, churn
- Promote winning pricing, disable poor performers

### Outputs
- `REVENUE_REPORT.md`
- `PRICING_EXPERIMENT_RESULTS.md`

### Automation
- Recommend pricing changes weekly
- Suggest feature bundles for upsell

---

## 4️ BigQuery Data Warehouse + AI Analytics

### Objective
Build scalable analytics to inform AI decisions

### Pipeline
- Event schema: user_id, event_type, timestamp, metadata
- Event logging → BigQuery
- Analytics queries: DAU/MAU, retention, funnels
- AI insights: drop-offs, engagement trends, feature usage

### Outputs
- `ANALYTICS_DASHBOARD.md`
- `INSIGHTS_REPORT.md`

### Automation
- Generate weekly feature recommendations
- Detect patterns for growth experiments

---

## 5️ AI Decision Engine (Master Brain)

### Objective
Central brain for feature rollout, revenue, and personalization

### Decision Loop
1. Collect inputs from analytics, feedback, revenue metrics
2. Rank opportunities by impact, effort, risk
3. Generate execution plan
4. Assign to AI agents

### Outputs
- `MASTER_ROADMAP.md`
- `WEEKLY_EXECUTION_PLAN.md`

### Automation
- Execute top 3 tasks per cycle
- Monitor KPIs and adjust future suggestions

---

## 6️⃣ Multi-Tenant SaaS Architecture

### Database
- Tenants, users, tenant_feature_flags
- Role-based access per tenant
- Isolation of data

### Backend
- FastAPI endpoints accept tenant_id
- Feature flags per tenant

### Security
- JWT auth
- RBAC
- Audit logging
- SSO/SAML onboarding

---

## 7️⃣ Stripe Billing & Subscription Engine

### Features
- Create checkout sessions for subscription
- Webhook for payment success
- Update subscription status in DB
- Track revenue per tenant/user

### Outputs
- `SUBSCRIPTION_STATUS.md`
- `MRR_REPORT.md`

---

## 8️⃣ Push Notifications (Firebase)

### Features
- Send notifications per user or tenant
- Trigger onboarding, engagement, upsell, renewal alerts
- Personalized content

### Outputs
- `NOTIFICATION_LOG.md`
- `ENGAGEMENT_REPORT.md`

---

## 9️⃣ Mobile SDK Generation (OpenAPI)

### Objective
Generate client SDKs automatically to sync backend and mobile apps

``bash
openapi-generator-cli generate -i http://localhost:8080/openapi.json -g swift5 -o ios_sdk
openapi-generator-cli generate -i http://localhost:8080/openapi.json -g kotlin -o android_sdk

Automation
Auto-update SDKs with every backend change
Reduce API mismatch bugs
---

## 10 Growth, Acquisition, & ASO Engine
Channels
App Store / Play Store optimization
Paid Ads (Google, Meta)
SEO (blogs, landing pages)
Funnel optimization
Outputs
AD_CAMPAIGNS.md
SEO_CONTENT_PLAN.md
FUNNEL_ANALYSIS.md
ASO_REPORT.md
Automation
Suggest campaigns weekly
Optimize screenshots, descriptions, CTAs
Track conversion improvements

## 11 AI Chatbot (Support + Upsell)
Features
Handle FAQs
Troubleshoot issues
Recommend premium features
Link to subscription & personalization engine
Outputs
CHATBOT_LOG.md
USER_INTERACTION_REPORT.md

## 12️ Security & Compliance System
Features
Scan for vulnerabilities
Enforce JWT + RBAC
Audit logging
GDPR / privacy compliance
Outputs
SECURITY_REPORT.md
VULNERABILITY_LIST.md
Automation
Suggest fixes for critical vulnerabilities
Auto-fix minor issues

## 13️ AI Personalization Engine
Features
Personalized onboarding
Recommended features
Dynamic pricing based on usage
Tenant-specific feature rollout
Outputs
PERSONALIZATION_REPORT.md
TENANT_RECOMMENDATIONS.md
Automation
Auto-generate feature suggestions per user/tenant
Track engagement improvement

## 14️ Auto-Scaling & CI/CD
Cloud Run auto-scaling (min=0, max=depends on traffic)
CI/CD via GitHub Actions
Terraform provisioning:
Cloud Run
BigQuery datasets
IAM / service accounts
Supabase/Postgres
Outputs
DEPLOYMENT_STATUS.md
SCALING_LOG.md

## 15️ Full System Architecture
Users (Web + iOS + Android)
        ↓
FastAPI Backend (Cloud Run, auto-scaling)
        ↓
Supabase/Postgres (Multi-tenant + Analytics)
        ↓
Stripe (Billing + Revenue)
        ↓
BigQuery (Analytics + Insights)
        ↓
Firebase (Push Notifications)
        ↓
Cursor AI:
    - Dev / Refactor / Growth / Personalization
    - Enterprise Agent (SSO, onboarding)
    - Scaling Agent
    - Decision Engine
 ↓
CI/CD (GitHub Actions)
✅ Recommended Rollout
Backend + Multi-tenant DB
Analytics + Feedback
Stripe Billing + Webhooks
Firebase Notifications
Mobile SDKs
Cursor AI Agents (manual → gradually autonomous)
Enable feature automation and personalization
⚠️ Guardrails
Validate major feature deployments manually initially
Monitor cost and scale gradually
Respect privacy and compliance regulations
Avoid aggressive monetization without user consent

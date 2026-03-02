# Addendum: Hybrid Open-Core Launch Strategy

## Objective
To realign the AI's contextual understanding of the "OrchestraAI" Go-To-Market and Monetization strategy. We are executing a **Hybrid Open-Core (PLG)** model as defined in Phase 8 of the original `.plan.md` file. 

## Instructions for Cursor AI
Moving forward, all architectural decisions, feature additions, and documentation must explicitly support a two-tiered product ecosystem. You must design the system so that the "Community Engine" remains free and open, while the "Enterprise Cloud" remains proprietary and monetizable.

### Tier 1: The Community Edition (Free / Open Source)
This is the code currently sitting in our GitHub repository. Its primary purpose is developer-led growth, building trust, and proving that our financial guardrails work.
* **Target Audience:** Solo developers, technical marketers, and small agencies.
* **Delivery:** Self-hosted via Docker Compose.
* **Interface:** The Typer+Rich CLI (`orchestra ask...`).
* **Limitations:** Single-tenant by default (running locally), manual scaling, community support only.
* **License:** Apache 2.0.

### Tier 2: The Enterprise Managed Cloud (Proprietary / Monetized)
This is the closed-source SaaS layer that we will build *on top* of the open-source core. Its purpose is to generate recurring B2B revenue.
* **Target Audience:** Mid-to-large marketing agencies and corporate marketing directors.
* **Delivery:** Fully managed cloud hosting (we pay the infrastructure bills).
* **Interface:** A premium Next.js / React Web Dashboard (No CLI required).
* **Premium Features (Paywalled):**
  - Single Sign-On (SAML/SSO).
  - Multi-player collaboration and RBAC (Role-Based Access Control) enforced via web UI.
  - Advanced cross-platform analytics dashboards.
  - White-labeling for agencies.
  - Guaranteed SLAs and SOC2 Compliance.
  - Managed API key proxying (so they don't have to manage their own OpenAI/Anthropic limits).

## Next Development Directives
When generating new code or planning the next phases, adhere to these rules:
1. **API First:** The FastAPI backend must remain decoupled. It must be able to serve the Open-Source CLI just as flawlessly as it serves the upcoming Proprietary Web Dashboard.
2. **Feature Flags:** Any enterprise-only features added to the core backend must be safely gated behind license keys or enterprise tenant flags.
3. **Documentation:** The README and docs must clearly pitch the Enterprise Managed Cloud as the "upgrade path" for teams that outgrow the CLI.

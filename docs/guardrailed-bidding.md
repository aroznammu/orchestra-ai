# OrchestraAI -- Guardrailed Bidding System

## Core Principle

> "Compliant, conservative, explainable, and financially bounded."

Autonomy increases only with data maturity and verified profitability. The system is designed to be maximally safe by default, with progressively unlocked capabilities.

## Phased Autonomy Model

### Phase 1: Hard Guardrail Mode (DEFAULT)

Every new account starts here. No exceptions.

| Capability | Allowed | Requires Approval |
|-----------|---------|-------------------|
| Create campaign | - | Yes (always) |
| Decrease budget | Auto (< 50%) | Yes (> 50%) |
| Increase budget | - | Yes (> 10% change) |
| Adjust bids | - | Yes (> 15% change) |
| Pause campaign | Auto | - |
| Reallocate budget | - | Yes (always) |
| Change audience | - | Yes (always) |

**Caps**: $500/day global, $200/day per platform, $5,000 per campaign

**AI role**: Recommend only. Cannot execute financial actions without human approval.

### Phase 2: Semi-Autonomous Mode

**Activation requirements** (ALL must be met):
- 90+ days of stable performance
- Positive ROI for 3+ consecutive cycles
- Anomaly detection validated (no false positives in 30 days)
- Explicit customer opt-in

| Capability | Allowed | Requires Approval |
|-----------|---------|-------------------|
| Auto-adjust bids | Within 20% | > 20% |
| Auto-allocate budget | Within 25% | > 25% |
| Auto-pause underperformers | Yes | - |
| Create campaign | < $10K budget | > $10K budget |
| Budget reallocation | Within daily caps | Exceeds caps |

**Still enforced**: Absolute daily ceiling, per-platform max allocation, kill switch, real-time alerting.

### Phase 3: Controlled Autonomous Optimization

**Activation requirements** (ALL must be met):
- Sustained profitability (180+ days)
- Verified stable ROI (6+ cycles)
- Manual enabling by account owner
- Explicit legal acknowledgement signed

**Even in this phase, NEVER**:
- Override platform policy restrictions
- Target outside allowed parameters
- Experiment on policy edges
- Use unofficial APIs or scraping
- Exceed absolute hard limits

## Compliance Engine Design

### Architecture

```
Any Platform Action
        |
   [Restrictions Check]  <-- 14 NEVER-do rules
        |
   [Content Validator]   <-- Risk score 0-100
        |
   [ToS Rules Check]     <-- Per-platform rules
        |
   [Rate Limiter]         <-- 15% below platform max
        |
   [Policy Monitor]       <-- Auto-disable on shifts
        |
   Proceed to Platform API
```

### Content Risk Scoring

| Score Range | Action | Description |
|------------|--------|-------------|
| 0-39 | Auto-approve | Low risk, within all policies |
| 40-69 | Human review | Borderline, requires manual check |
| 70-100 | Auto-reject | High risk, policy violations detected |

### Machine-Readable ToS Rules

Each platform has structured rules for:
- **Content**: Max length, media count, hashtag limits, link policy
- **Rate limits**: Per-endpoint limits with safety buffer
- **Automation**: Max posts/day, min interval between posts
- **Targeting**: Age restrictions, prohibited categories
- **Prohibited content**: Platform-specific banned topics

## Financial Risk Containment

### Three-Tier Spend Caps

```
Tier 1: Global            Tier 2: Per-Platform      Tier 3: Per-Campaign
─────────────────────      ──────────────────────     ─────────────────────
Daily cap: $500            Twitter: $200/day          Campaign A: $1,000
Monthly cap: $10,000       YouTube: $200/day          Campaign B: $2,000
Lifetime: optional         LinkedIn: $200/day         Campaign C: $500
```

All three tiers must pass for any spend operation.

### Anomaly Detection

**Methods**:
- Z-score analysis (threshold: 2.5 standard deviations)
- IQR (Interquartile Range) outlier detection
- Per-platform pattern tracking

**On detection**:
1. Block the anomalous operation
2. Fire alert (severity based on deviation)
3. Log to financial audit trail
4. Optionally trigger automatic rollback

### Spend Velocity Monitoring

- Tracks $/hour rate over sliding windows
- Maintains 7-day hourly baseline
- Flags spikes at 3x baseline velocity
- Scheduler-friendly baseline update hook

### Budget Alerts

| Utilization | Severity | Action |
|------------|----------|--------|
| 50% | Info | Log + optional notification |
| 75% | Warning | Alert via configured channels |
| 90% | Critical | Alert + prepare for cap enforcement |
| 100% | Emergency | Block all further spend |

### Automatic Rollback

When an anomaly is confirmed:
1. Identify recent changes (bid adjustments, budget changes)
2. Revert to previous values
3. Log rollback with reason
4. Alert team

Supports:
- Single change rollback
- Batch rollback (N most recent)
- Platform-specific rollback (revert all changes on one platform)

## Policy Enforcement Layer

### 14 Absolute Restrictions

These cannot be overridden by any agent, configuration, or autonomy phase:

1. Never bypass rate limits
2. Never mask automation as human behavior
3. Never circumvent review processes
4. Never exploit platform loopholes
5. Never automate prohibited ad categories
6. Never generate policy-violating ads
7. Never target prohibited demographics
8. Never attempt platform gaming
9. Never scrape platform data
10. Never use unofficial endpoints
11. Never create deceptive content
12. Never target minors without compliance
13. Never expose credentials in plaintext
14. Never use data without consent

### Kill Switch

- **Global**: Halts ALL spend for ALL tenants instantly
- **Per-tenant**: Halts spend for a specific tenant
- **Access**: API endpoint, CLI command, future dashboard button
- **Deactivation**: Manual only (no auto-deactivation)
- **Audit**: Every activation/deactivation logged with reason

## Risk Mitigation Table

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ToS Violation | Low | High | Machine-readable ToS rules, content validator, 14 restrictions |
| Budget Overspend | Low | High | 3-tier caps, anomaly detection, kill switch, automatic rollback |
| Policy Drift | Medium | Medium | Policy monitor, auto-disable, changelog tracking |
| API Dependency | Medium | Medium | Graceful degradation, stub connectors, local LLM fallback |
| Algorithm Underperformance | Medium | Low | Thompson Sampling with exploration, conservative defaults |
| Data Breach | Low | Critical | Encryption at rest, RBAC, audit trail, GDPR compliance |
| Agent Loop | Low | Low | Depth limits, call tracking, timeout, safety system |
| False Positive (Anomaly) | Medium | Low | Configurable thresholds, human review, alert-only mode |

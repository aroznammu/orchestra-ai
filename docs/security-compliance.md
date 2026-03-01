# OrchestraAI -- Security & Compliance

## OAuth2 Flows

### Token Lifecycle

```
User clicks "Connect Platform"
        |
   [Generate auth URL with PKCE]
        |
   Redirect to platform
        |
   User authorizes
        |
   Platform redirects with code
        |
   [Exchange code for tokens]
        |
   [Encrypt tokens (Fernet)]
        |
   [Store in PostgreSQL]
        |
   Access token used for API calls
        |
   [Auto-refresh when expired]
```

### Supported Flows

| Platform | OAuth Type | PKCE | Notes |
|----------|-----------|------|-------|
| Twitter | OAuth 2.0 | Yes | PKCE required since 2023 |
| YouTube | OAuth 2.0 | No | Google OAuth standard |
| Facebook | OAuth 2.0 | No | Meta business verification |
| Instagram | OAuth 2.0 | No | Via Facebook app |
| LinkedIn | OAuth 2.0 | No | Partner program required |
| TikTok | OAuth 2.0 | No | Developer portal |
| Pinterest | OAuth 2.0 | No | Free, easy approval |
| Snapchat | OAuth 2.0 | No | Marketing API |
| Google Ads | OAuth 2.0 | No | Developer token |

## Encryption

### Token Encryption at Rest

- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Key management**: Via `FERNET_KEY` environment variable
- **Scope**: All OAuth tokens encrypted before database storage
- **Implementation**: `security/encryption.py`

### Password Hashing

- **Algorithm**: bcrypt (via passlib)
- **Work factor**: Auto-adjusted (deprecated rounds auto-upgraded)

### JWT Tokens

- **Algorithm**: HS256 (configurable)
- **Expiry**: 30 minutes default (configurable)
- **Claims**: sub (user_id), tenant_id, role, exp, iat

## Role-Based Access Control (RBAC)

### Role Hierarchy

```
OWNER (all 28 permissions)
  |
ADMIN (inherits viewer + member + admin-specific)
  |
MEMBER (inherits viewer + member-specific)
  |
VIEWER (read-only: 6 permissions)
```

### Permission Matrix

| Permission | Viewer | Member | Admin | Owner |
|-----------|--------|--------|-------|-------|
| View campaigns | Y | Y | Y | Y |
| Create campaigns | - | Y | Y | Y |
| Delete campaigns | - | - | Y | Y |
| Connect platforms | - | Y | Y | Y |
| Disconnect platforms | - | - | Y | Y |
| Edit budget | - | - | Y | Y |
| Approve budget | - | - | Y | Y |
| View users | - | - | Y | Y |
| Remove users | - | - | - | Y |
| Change roles | - | - | - | Y |
| Activate kill switch | - | - | - | Y |
| Delete data (GDPR) | - | - | - | Y |
| View audit log | - | - | Y | Y |
| Run orchestrator | - | Y | Y | Y |

## GDPR/CCPA Compliance

### Data Subject Rights

| Right | Endpoint | Implementation |
|-------|----------|---------------|
| Right to access (Art. 15) | `GET /api/v1/gdpr/consent/status` | Consent status query |
| Right to portability (Art. 20) | `POST /api/v1/gdpr/export` | Full data export (JSON) |
| Right to erasure (Art. 17) | `POST /api/v1/gdpr/delete` | Cascade delete across all stores |
| Right to withdraw consent | `POST /api/v1/gdpr/consent` | Per-type consent revocation |

### Data Deletion Cascade

When a tenant exercises right to erasure:
1. PostgreSQL: Users, campaigns, posts, audit logs, connections
2. Qdrant: All vector collections filtered by tenant_id
3. Redis: All cached keys with tenant prefix
4. Agent memory: Short-term buffer + long-term vectors
5. Performance embeddings: Tenant model data
6. Confirmation: Deletion log retained (without PII) for compliance proof

### Consent Types

- `data_processing` -- Required for service operation
- `marketing` -- OrchestraAI marketing communications
- `analytics` -- Usage analytics and product improvement
- `third_party` -- Sharing anonymized data with global model

## SOC 2 Roadmap

### Type I (Target: Month 6)

| Control | Status | Implementation |
|---------|--------|---------------|
| Access control | Implemented | JWT + RBAC with 28 permissions |
| Audit logging | Implemented | Every API call and agent action logged |
| Encryption at rest | Implemented | Fernet for tokens, bcrypt for passwords |
| Change management | Partial | Alembic migrations, BUILD_LOG tracking |
| Incident response | Partial | Kill switch, anomaly alerts |

### Type II (Target: Month 12)

| Control | Status | Gap |
|---------|--------|-----|
| Continuous monitoring | Planned | Need Prometheus/Grafana stack |
| Penetration testing | Planned | Need third-party assessment |
| Business continuity | Partial | Need backup/restore procedures |
| Vendor management | Planned | Need platform API risk assessments |
| Employee training | N/A | Post-hire requirement |

## Audit Trail

Every operation is logged with:
- **Who**: user_id, role, IP address
- **What**: action, resource type, resource ID
- **When**: ISO 8601 timestamp
- **Why**: reasoning (for AI decisions), approval status
- **Outcome**: success, failure, pending
- **Risk**: numerical risk score (0-10)

Financial operations additionally log:
- Platform, campaign ID, amount, currency
- Previous value, new value, change percentage
- Budget utilization percentage
- Approval status and approver

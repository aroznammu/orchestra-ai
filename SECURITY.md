# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in OrchestraAI, please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

### How to Report

Email security concerns to: **[security contact to be configured before public launch]**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix/Patch**: Based on severity (Critical: 48h, High: 1 week, Medium: 2 weeks)

### Scope

The following are in scope:
- API authentication/authorization bypass
- Data leakage between tenants
- SQL injection or command injection
- Credential exposure
- Kill switch bypass
- Spend limit bypass
- GDPR/CCPA compliance failures

### Out of Scope

- Vulnerabilities in dependencies (report upstream, but notify us)
- Issues requiring physical access
- Social engineering

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes      |

## Security Architecture

See [docs/security-compliance.md](docs/security-compliance.md) for details on:
- JWT + API key authentication
- Role-based access control (4 roles, 28 permissions)
- Fernet symmetric encryption for credentials
- Multi-tenant data isolation
- GDPR/CCPA compliance features
- Audit trail for all operations

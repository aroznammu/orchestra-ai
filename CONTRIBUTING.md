# Contributing to OrchestraAI

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Poetry (`pip install poetry`)

### Setup

```bash
# Clone the repo
git clone <repository-url>
cd orchestra-ai

# Copy environment config
cp .env.example .env

# Start infrastructure
docker compose up -d

# Install dependencies (including dev tools)
poetry install

# Run migrations
poetry run alembic upgrade head

# Verify everything works
poetry run pytest
```

## Code Style

We use **Ruff** for linting and formatting, **Mypy** for type checking.

```bash
# Lint
poetry run ruff check src/

# Format
poetry run ruff format src/

# Type check
poetry run mypy src/orchestra/
```

### Style Guidelines

- **Type hints**: Required on all public functions
- **Docstrings**: Required on modules and public classes/functions
- **Pydantic models**: Use for all data contracts
- **Async**: Use async/await for all I/O operations
- **Logging**: Use `structlog` with contextual fields
- **Secrets**: Always use `SecretStr` or env vars, never hardcode

## Making Changes

### Branch Naming

```
feature/short-description
fix/short-description
docs/short-description
```

### Commit Messages

Use conventional commits:

```
feat: add Pinterest full connector
fix: handle rate limit on Twitter analytics
docs: update deployment guide
refactor: extract common OAuth logic
test: add compliance agent unit tests
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure linting passes (`make lint`)
4. Ensure tests pass (`make test`)
5. Update documentation if needed
6. Submit a PR with a clear description

### PR Template

```markdown
## What

Brief description of the change.

## Why

Motivation and context.

## How

Implementation approach.

## Testing

How you tested the changes.

## Checklist

- [ ] Linting passes
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] No hardcoded secrets
```

## Adding a Platform Connector

Platform connectors are the most common contribution. Here's how:

1. Create `src/orchestra/platforms/<platform_name>.py`
2. Implement the `PlatformBase` abstract interface (9 methods)
3. Add platform limits in the connector
4. Register in `src/orchestra/platforms/__init__.py`
5. Add ToS rules in `src/orchestra/compliance/tos_rules.py`
6. Update documentation

See `platforms/twitter.py` (full implementation) or `platforms/pinterest.py` (stub) as examples.

## Architecture Decisions

Before making significant architectural changes, please open an issue to discuss:

- New dependencies
- Database schema changes
- API contract changes
- Agent workflow modifications
- Security-related changes

## Restricted Changes

The following cannot be modified without owner review:

- `compliance/restrictions.py` -- The 14 NEVER-do rules
- `bidding/kill_switch.py` -- Kill switch logic
- `security/encryption.py` -- Token encryption
- `risk/spend_caps.py` -- Absolute spend limits

## Getting Help

- Open an issue for bugs or feature requests
- Use discussions for questions and ideas

## Code of Conduct

Be respectful, constructive, and inclusive. We're building something meaningful together.

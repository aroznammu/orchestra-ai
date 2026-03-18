# Contributing to OrchestraAI

Thanks for your interest in contributing. This guide covers everything you need
to get a development environment running and submit a pull request.

## Getting Started

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/orchestraai.git
cd orchestraai

# 2. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Install pre-commit hooks
pre-commit install
```

## Development Setup

### Infrastructure

OrchestraAI depends on PostgreSQL, Redis, Qdrant, Kafka, and (optionally)
Ollama. The easiest way to run them is Docker Compose:

```bash
docker compose up -d
```

This starts:

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL 16 | 5432 | Primary database |
| Redis 7 | 6379 | Cache, rate limiting, events |
| Qdrant | 6333 | Vector DB for RAG |
| Kafka | 9092 | Event bus |
| Ollama | 11434 | Local LLM (optional) |

### Environment Variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

At minimum, set `JWT_SECRET_KEY` and `FERNET_KEY`. Platform API keys are only
needed if you're working on specific connectors.

### Running the API

```bash
uvicorn orchestra.main:app --reload --port 8000
```

### Using the CLI

```bash
orchestra status          # Check infrastructure health
orchestra auth register   # Create a test account
orchestra ask "hello"     # Test the orchestrator
```

## Code Style

We use **Ruff** for linting and formatting, configured in `pyproject.toml`:

```bash
# Lint
ruff check src/

# Auto-fix
ruff check src/ --fix

# Format
ruff format src/

# Type checking (strict mode)
mypy src/orchestra/ --ignore-missing-imports
```

Key Ruff settings (from `pyproject.toml`):

- **Target:** Python 3.12
- **Line length:** 120
- **Rules:** E, F, W, I, N, UP, S, B, A, C4, PT, RET, SIM
- **Ignored:** S101 (assert in tests), S104 (bind to all interfaces)
- **isort:** `orchestra` as first-party

## Testing

```bash
# Run the full suite
pytest

# With verbose output
pytest -v --tb=short

# Run a specific test file
pytest tests/test_orchestrator.py

# Run with coverage
pytest --cov=orchestra --cov-report=html
```

The test suite has **273+ tests** using `pytest-asyncio` with `asyncio_mode = auto`.
All async test functions are automatically detected -- no need for
`@pytest.mark.asyncio`.

### Writing Tests

- Place tests in `tests/` with the `test_` prefix
- Use `pytest-asyncio` for async tests (mode is `auto`)
- Use `httpx.AsyncClient` with FastAPI's `TestClient` for API tests
- Mock external services (platform APIs, LLM providers) -- never make real HTTP calls in tests
- Use `faker` for generating test data

## PR Process

### Branch Naming

```
feature/short-description
fix/issue-number-description
docs/what-changed
refactor/what-changed
```

### Commit Messages

Use clear, imperative-mood messages:

```
Add Twitter analytics endpoint
Fix spend cap reset not triggering on schedule
Update RAG pipeline to support multi-tenant isolation
```

### Submitting a PR

1. Create a branch from `main`
2. Make your changes
3. Ensure all checks pass: `ruff check src/ && pytest`
4. Push your branch and open a PR against `main`
5. Fill out the PR template (summary, type, testing, checklist)
6. Wait for CI to pass and a maintainer to review

### What We Look For

- Tests for new functionality
- No regressions in existing tests
- Clean Ruff output (no lint errors)
- Docstrings for public functions
- No hardcoded secrets or credentials
- Tenant isolation maintained (multi-tenant queries must filter by `tenant_id`)

## Architecture Overview

The project follows this structure:

```
src/orchestra/
├── agents/          # LangGraph orchestrator, content, analytics, optimizer agents
├── api/             # FastAPI routes and middleware
├── bidding/         # 3-phase guardrailed bidding engine
├── cli/             # Typer CLI (orchestra command)
├── compliance/      # ToS rules, content validation, rate limiting
├── core/            # Cost router, scheduler, exceptions
├── db/              # SQLAlchemy models, session, migrations
├── intelligence/    # Cross-platform ROI, budget allocation, attribution
├── platforms/       # 9 platform connectors (Twitter, YouTube, etc.)
├── rag/             # Qdrant RAG pipeline, embeddings, retriever
├── risk/            # Spend caps, anomaly detection, velocity, kill switch
├── security/        # Encryption, GDPR, OAuth token management
└── main.py          # FastAPI app entry point
```

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Code of Conduct

Be respectful. Be constructive. Assume good intent.

- Treat all contributors with respect regardless of experience level
- Provide actionable feedback in code reviews
- No harassment, discrimination, or personal attacks
- Focus on the code, not the person
- If something is unclear, ask -- don't assume

Violations can be reported to hello@useorchestra.dev. Reports are handled
confidentially.

## Questions?

- Open a [Discussion](https://github.com/orchestraai/orchestraai/discussions) for general questions
- Open an [Issue](https://github.com/orchestraai/orchestraai/issues) for bugs or feature requests
- Check existing issues before creating new ones

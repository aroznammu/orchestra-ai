.PHONY: help setup install test lint run dev clean docker-up docker-down migrate format check

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## First-time project setup (install deps + copy env + run migrations)
	@echo "Setting up OrchestraAI..."
	cp -n .env.example .env 2>/dev/null || true
	poetry install
	@echo "Setup complete. Edit .env with your API keys, then run: make docker-up"

install: ## Install dependencies
	poetry install

test: ## Run test suite
	poetry run pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	poetry run pytest tests/ -v --cov=orchestra --cov-report=term-missing --cov-report=html

lint: ## Run linter (ruff)
	poetry run ruff check src/ tests/
	poetry run ruff format --check src/ tests/

format: ## Auto-format code
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

check: ## Run all checks (lint + type check + tests)
	poetry run ruff check src/ tests/
	poetry run mypy src/
	poetry run pytest tests/ -v --tb=short

run: ## Run the FastAPI server locally
	poetry run uvicorn orchestra.main:app --reload --host 0.0.0.0 --port 8000

dev: docker-up ## Start full dev environment (Docker + app)
	@echo "Infrastructure running. Start app with: make run"

docker-up: ## Start infrastructure services (PostgreSQL, Redis, Kafka, Qdrant, Ollama)
	docker compose up -d postgres redis kafka qdrant ollama
	@echo "Waiting for services to be healthy..."
	docker compose ps

docker-down: ## Stop all Docker services
	docker compose down

docker-clean: ## Stop services and remove volumes
	docker compose down -v

migrate: ## Run database migrations
	poetry run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="add users table")
	poetry run alembic revision --autogenerate -m "$(msg)"

cli: ## Run the OrchestraAI CLI
	poetry run orchestra --help

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/ *.egg-info

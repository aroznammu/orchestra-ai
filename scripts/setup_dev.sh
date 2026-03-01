#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

info "OrchestraAI Development Setup"
echo "=============================="

# Check Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.12+"
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python version: $PYTHON_VERSION"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
    info "Python version OK"
else
    warn "Python 3.12+ recommended (found $PYTHON_VERSION)"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker Desktop."
fi
info "Docker: $(docker --version)"

# Check Docker Compose
if docker compose version &> /dev/null; then
    info "Docker Compose: $(docker compose version --short)"
else
    error "Docker Compose not found. Install Docker Desktop (includes Compose v2)."
fi

# Install Poetry
if ! command -v poetry &> /dev/null; then
    info "Installing Poetry..."
    pip install poetry
fi
info "Poetry: $(poetry --version)"

# Copy .env if not exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        info "Created .env from .env.example"
        warn "Review .env and update secrets before running in production!"
    else
        error ".env.example not found"
    fi
else
    info ".env already exists"
fi

# Start infrastructure
info "Starting infrastructure services..."
docker compose up -d

info "Waiting for services to be healthy..."
sleep 5

# Check service health
for service in postgres redis qdrant; do
    if docker compose ps "$service" 2>/dev/null | grep -q "running\|Up"; then
        info "$service: running"
    else
        warn "$service: may not be running (check with 'docker compose ps')"
    fi
done

# Install dependencies
info "Installing Python dependencies..."
poetry install

# Run migrations
info "Running database migrations..."
poetry run alembic upgrade head

# Verify
info "Checking API startup..."
timeout 10 poetry run python -c "from orchestra.config import Settings; s = Settings(); print(f'Config loaded: {s.APP_NAME}')" 2>/dev/null || warn "Config check skipped (may need env vars)"

echo ""
echo "=============================="
info "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and update .env with your settings"
echo "  2. Start the API:       poetry run uvicorn orchestra.main:app --reload"
echo "  3. Open API docs:       http://localhost:8000/docs"
echo "  4. Run CLI:             poetry run orchestra --help"
echo ""

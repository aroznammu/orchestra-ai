$ErrorActionPreference = "Stop"

function Write-Info  { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

Write-Info "OrchestraAI Development Setup"
Write-Host "=============================="

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Info "Python: $pyVersion"
} catch {
    Write-Err "Python is not installed. Please install Python 3.12+"
}

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    Write-Info "Docker: $dockerVersion"
} catch {
    Write-Err "Docker is not installed. Please install Docker Desktop."
}

# Check Docker Compose
try {
    $composeVersion = docker compose version 2>&1
    Write-Info "Docker Compose: $composeVersion"
} catch {
    Write-Err "Docker Compose not found."
}

# Install Poetry
try {
    $poetryVersion = poetry --version 2>&1
    Write-Info "Poetry: $poetryVersion"
} catch {
    Write-Info "Installing Poetry..."
    pip install poetry
}

# Copy .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Info "Created .env from .env.example"
        Write-Warn "Review .env and update secrets before production use!"
    } else {
        Write-Err ".env.example not found"
    }
} else {
    Write-Info ".env already exists"
}

# Start infrastructure
Write-Info "Starting infrastructure services..."
docker compose up -d

Write-Info "Waiting for services..."
Start-Sleep -Seconds 5

# Install dependencies
Write-Info "Installing Python dependencies..."
poetry install

# Run migrations
Write-Info "Running database migrations..."
poetry run alembic upgrade head

Write-Host ""
Write-Host "=============================="
Write-Info "Setup complete!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review and update .env with your settings"
Write-Host "  2. Start the API:       poetry run uvicorn orchestra.main:app --reload"
Write-Host "  3. Open API docs:       http://localhost:8000/docs"
Write-Host "  4. Run CLI:             poetry run orchestra --help"
Write-Host ""

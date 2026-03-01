FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

FROM base AS deps

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

FROM deps AS production

COPY src/ ./src/
COPY alembic.ini* ./
COPY pyproject.toml ./

ENV PYTHONPATH=/app/src

RUN poetry install --only main

RUN useradd --create-home --shell /bin/bash orchestra
USER orchestra

EXPOSE 8000

CMD ["uvicorn", "orchestra.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

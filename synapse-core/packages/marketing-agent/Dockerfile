# Synapse Core - Marketing Agent
# Multi-stage Dockerfile for development and production

# ============================================
# Base stage with Python and Poetry
# ============================================
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# ============================================
# Development stage
# ============================================
FROM base AS development

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies including dev dependencies
RUN poetry install --no-root

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Production stage
# ============================================
FROM base AS production

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install only production dependencies
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 synapse && chown -R synapse:synapse /app
USER synapse

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

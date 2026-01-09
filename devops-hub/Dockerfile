# DevOps Hub - Agent Library Service
# Production Docker image

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY factory/ ./factory/
COPY service/ ./service/
COPY core/ ./core/
COPY sdk/ ./sdk/
COPY built_in_agents/ ./built_in_agents/
COPY AGENT_REGISTRY.json .

# Create data directory for database
RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start command
CMD ["python", "-m", "uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8100"]

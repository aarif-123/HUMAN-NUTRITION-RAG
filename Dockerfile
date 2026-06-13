# ============================================================
# Nutri-RAG Backend — Production Dockerfile
# ============================================================
# Build:  docker build -t nutri-rag-backend .
# Run:    docker run -p 8000:8000 --env-file ../.env nutri-rag-backend
# ============================================================

# --- Stage 1: dependency builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools (needed for some compiled wheels, e.g. numpy)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: lean runtime image ---
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Nutri-RAG Backend"
LABEL org.opencontainers.image.description="FastAPI + LangGraph RAG API for Human Nutrition Research"
LABEL org.opencontainers.image.version="4.1.0"

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Ensure frontend directory is accessible (mounted via docker-compose volume)
RUN mkdir -p /app/frontend

# Drop privileges
USER appuser

EXPOSE 8000

# PROMETHEUS_MULTIPROC_DIR must be writable by the process
ENV PROMETHEUS_MULTIPROC_DIR=/tmp

# Healthcheck — allows Docker/compose to restart unhealthy containers
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Use --workers 1 to keep MemorySaver conversation state consistent.
# For horizontal scale, swap MemorySaver for a Redis/Postgres checkpointer.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# TaskMate Backend — Production Multi-Platform Dockerfile
# Base Python runtime: minimal slim Debian image
FROM python:3.11-slim as runtime

# Security & Python optimization environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    DEBUG=false \
    HOST=0.0.0.0 \
    PORT=8000

# Set workspace working directory
WORKDIR /app

# Install security updates and curl for health check
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged system user for container security hardening
RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --shell /bin/false --no-create-home appuser

# Copy production requirements first for efficient layer caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install backend production dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend/app /app/backend/app

# Set Python path to /app so `backend.app.main:app` resolves properly
ENV PYTHONPATH=/app

# Change ownership of application files to unprivileged user
RUN chown -R appuser:appgroup /app

# Switch to unprivileged runtime user
USER appuser

# Expose backend service port
EXPOSE 8000

# Health check probe against production health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch production server via Uvicorn (binds to dynamic cloud PORT if set)
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

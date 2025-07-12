# Multi-stage Dockerfile for FastAPI backend
# Optimized for both development and production

# Base stage with Python and common system dependencies
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    git-lfs \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Setup Git LFS
RUN git lfs install

WORKDIR /app

# Development stage with all dependencies and hot reloading
FROM base AS development

# Install netcat for entrypoint script
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Install Python development dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p /workspace

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]

# Builder stage for production dependencies
FROM base AS builder

# Install production dependencies only
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# Production stage - minimal runtime
FROM python:3.11-slim AS production

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Setup Git LFS
RUN git lfs install

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create workspace directory
RUN mkdir -p /workspace && chown -R appuser:appuser /workspace

# Update PATH for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Use non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start production server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Multi-stage build for the Code Development Assistant
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY web_ui/ ./web_ui/
COPY web_ui_runner.py ./

# Install dependencies (creates lockfile and installs)
RUN uv sync

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Create directories with proper permissions
RUN mkdir -p /app/logs /app/code_rag_db /app/workspace && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 5000 8080

# Health check script
COPY --chown=appuser:appgroup healthcheck.py ./

# Default command (will be overridden by docker-compose)
CMD ["python", "web_ui_runner.py", "--host", "0.0.0.0", "--port", "5000"]

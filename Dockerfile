# Multi-stage build for smaller image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM ollama/ollama:latest as ollama-base

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Ollama binary from ollama image
COPY --from=ollama-base /bin/ollama /usr/local/bin/ollama

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user with specific UID/GID
RUN groupadd -r -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Create directories with proper permissions
RUN mkdir -p /app/models /home/appuser/.ollama /app/logs && \
    chown -R appuser:appgroup /app /home/appuser/.ollama

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup scripts/start.sh /start.sh

# Set executable permissions
RUN chmod +x /start.sh

# Switch to non-root user for security
USER appuser

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=0.0.0.0

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start script that runs both Ollama and the FastAPI app
CMD ["/start.sh"]

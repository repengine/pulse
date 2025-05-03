# Dockerfile for Pulse Retrodiction Training System
# Containerizes the ParallelTrainingCoordinator for execution in AWS Batch

FROM python:3.11-slim

LABEL maintainer="Pulse Team"
LABEL description="Container for Pulse Retrodiction Training System"
LABEL version="0.3.4"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    DASK_DISTRIBUTED__DASHBOARD__LINK="127.0.0.1:8787/status" \
    S3_DATA_BUCKET="pulse-retrodiction-data-poc" \
    S3_RESULTS_BUCKET="pulse-retrodiction-results-poc"

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with explicit UID/GID
RUN groupadd -g 10001 pulseuser && \
    useradd -u 10001 -g pulseuser -s /bin/bash -m pulseuser

# Copy just the requirements file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/recursive_training && \
    mkdir -p /app/logs && \
    chown -R pulseuser:pulseuser /app

# Switch to non-root user
USER pulseuser

# Define entrypoint script
ENTRYPOINT ["/app/cloud/docker/entrypoint.sh"]

# Default command (can be overridden)
CMD ["python", "-m", "recursive_training.run_training"]
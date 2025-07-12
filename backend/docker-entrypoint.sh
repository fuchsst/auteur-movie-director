#!/bin/bash
# Docker entrypoint script for Auteur Movie Director backend

set -e

echo "Starting Auteur Movie Director Backend..."

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  echo "Redis is not ready - waiting..."
  sleep 1
done
echo "Redis is ready!"

# Create workspace directory if it doesn't exist
mkdir -p /workspace

# Start FastAPI with uvicorn
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-config=null
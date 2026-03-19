#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔨 Starting Celery Worker..."

# Wait for the main app to be ready
sleep 10

# Create logs directory
mkdir -p /app/logs
chmod 755 /app/logs

# Print configuration
echo "👷 Celery Worker Configuration:"
echo "   🔄 Concurrency: Auto-detect"
echo "   📊 Log Level: INFO"
echo "   🏷️  Queue: celery (default)"

# Start Celery Worker with optimized settings for Docker Swarm
exec celery -A project worker \
    --loglevel=info \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=1000
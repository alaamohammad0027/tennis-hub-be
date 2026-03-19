#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🌸 Starting Celery Flower monitoring..."

# Wait for worker to be ready
sleep 20

echo "🌸 Flower Configuration:"
echo "   🔄 Auto Refresh: 30s"

# Start Flower with optimizations
exec celery -A project flower \
    --port=5555 \
    --auto_refresh=true \
    --refresh_interval=30 \
    --max_workers=10000 \
    --persistent=true \
    --db=/app/celery/flower.db
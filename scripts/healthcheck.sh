#!/bin/bash
# Health check script - restarts containers if down
# Cron: */5 * * * * ~/daily-ai-webhook/scripts/healthcheck.sh >> ~/logs/health.log 2>&1

PROJECT_DIR=~/daily-ai-webhook
cd "$PROJECT_DIR" || exit 1

# Count unhealthy/stopped containers
UNHEALTHY=$(docker-compose ps 2>/dev/null | grep -Ev "Up|NAME|^$" | wc -l)

if [ "$UNHEALTHY" -gt 0 ]; then
    echo "[$(date)] WARNING: $UNHEALTHY container(s) not running"
    docker-compose ps

    echo "[$(date)] Attempting restart..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

    echo "[$(date)] Restart complete"
else
    # Silent success - uncomment for verbose logging
    # echo "[$(date)] OK: All containers healthy"
    :
fi

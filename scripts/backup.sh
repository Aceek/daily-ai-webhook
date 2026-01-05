#!/bin/bash
# Daily backup script for PostgreSQL and n8n data
# Cron: 0 3 * * * ~/daily-ai-webhook/scripts/backup.sh >> ~/backups/backup.log 2>&1

set -e

BACKUP_DIR=~/backups
PROJECT_DIR=~/daily-ai-webhook
DATE=$(date +%Y%m%d_%H%M)

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# PostgreSQL dump
docker exec ai-news-postgres pg_dump -U ainews ainews | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
echo "[$(date)] PostgreSQL backup: db_$DATE.sql.gz"

# n8n workflows
tar -czf "$BACKUP_DIR/n8n_$DATE.tar.gz" -C "$PROJECT_DIR" n8n-data
echo "[$(date)] n8n backup: n8n_$DATE.tar.gz"

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm
ls -t "$BACKUP_DIR"/n8n_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "[$(date)] Backup complete. Kept last 7 backups."

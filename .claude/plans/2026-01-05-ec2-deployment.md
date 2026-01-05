# EC2 Deployment Plan

**Context:** Single t2.micro, SSH tunnel access, zero public ports

## Pre-Deployment Fixes

| ID | Issue | File | Fix |
|----|-------|------|-----|
| SEC-010 | SQL interpolation | `mcp_tools/repositories/article.py` | Use `make_interval(days => %s)` |
| PROD-01 | No resource limits | `docker-compose.prod.yml` | Add `mem_limit` |
| PROD-02 | Ports on 0.0.0.0 | `docker-compose.prod.yml` | Bind `127.0.0.1` |
| PROD-03 | No log rotation | `docker-compose.prod.yml` | Add logging config |

## Files to Create

### docker-compose.prod.yml

```yaml
services:
  postgres:
    ports:
      - "127.0.0.1:5434:5432"
    mem_limit: 256m
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  n8n:
    ports:
      - "127.0.0.1:5678:5678"
    mem_limit: 256m
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  claude-service:
    ports: []  # Remove public exposure
    mem_limit: 384m
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  discord-bot:
    ports: []  # Remove public exposure
    mem_limit: 128m
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### scripts/backup.sh

```bash
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M)
mkdir -p $BACKUP_DIR

docker exec postgres pg_dump -U ainews ainews | gzip > $BACKUP_DIR/db_$DATE.sql.gz
tar -czf $BACKUP_DIR/n8n_$DATE.tar.gz ~/daily-ai-webhook/n8n-data

# Keep 7 days
ls -t $BACKUP_DIR/db_*.sql.gz | tail -n +8 | xargs -r rm
ls -t $BACKUP_DIR/n8n_*.tar.gz | tail -n +8 | xargs -r rm
```

### scripts/healthcheck.sh

```bash
#!/bin/bash
cd ~/daily-ai-webhook
UNHEALTHY=$(docker-compose ps | grep -v "Up" | grep -v "NAME" | wc -l)

if [ "$UNHEALTHY" -gt 0 ]; then
    echo "[$(date)] Container(s) down - restarting"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi
```

## EC2 Setup

### Security Group

| Type | Port | Source |
|------|------|--------|
| SSH | 22 | Your IP only |

### Instance Init

```bash
# Packages
sudo yum update -y
sudo yum install -y docker git
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Swap (critical for t2.micro)
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

## Deploy Steps

```bash
# 1. Clone
git clone <repo> ~/daily-ai-webhook
cd ~/daily-ai-webhook

# 2. Config
cp .env.example .env
nano .env  # Fill values

# 3. Launch
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Claude auth
docker exec -it claude-service claude login

# 5. Verify
docker-compose ps
docker stats --no-stream
```

## Cron Jobs

```bash
crontab -e
```

```cron
# Backup daily 3am
0 3 * * * ~/daily-ai-webhook/scripts/backup.sh >> ~/backups/backup.log 2>&1

# Health check every 5min
*/5 * * * * ~/daily-ai-webhook/scripts/healthcheck.sh >> ~/logs/health.log 2>&1
```

## SSH Tunnel Access

```bash
# From local PC
ssh -L 5678:localhost:5678 -L 5434:localhost:5434 ec2-user@<EC2_IP>

# Then browse: http://localhost:5678 (n8n)
```

## Restore Procedures

```bash
# Database
gunzip -c ~/backups/db_YYYYMMDD.sql.gz | docker exec -i postgres psql -U ainews ainews

# n8n workflows
tar -xzf ~/backups/n8n_YYYYMMDD.tar.gz -C ~/
docker-compose restart n8n
```

## Checklist

- [ ] SEC-010: Fix SQL interpolation
- [ ] Create `docker-compose.prod.yml`
- [ ] Create `scripts/backup.sh`
- [ ] Create `scripts/healthcheck.sh`
- [ ] EC2: Security group SSH only
- [ ] EC2: Install docker + compose
- [ ] EC2: Setup swap
- [ ] Deploy + verify
- [ ] Setup cron jobs
- [ ] Test SSH tunnel access
- [ ] Test backup/restore

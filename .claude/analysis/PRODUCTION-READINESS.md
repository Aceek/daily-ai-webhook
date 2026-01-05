# Production Readiness Report - Daily AI Webhook

Date: 2026-01-05
Scope: Deploiement AWS du bot de veille AI/ML

---

## Executive Summary

| Categorie | Score | Status |
|-----------|-------|--------|
| Infrastructure Docker | 75% | **Partiellement pret** |
| Robustesse applicative | 60% | **Gaps significatifs** |
| Observabilite | 65% | **A renforcer** |
| Persistance & Backup | 50% | **Gaps critiques** |
| CI/CD | 30% | **Manquant** |
| Configuration production | 70% | **Partiellement pret** |
| Scalabilite | 55% | **Limitations** |

**Verdict global: Non pret pour production AWS sans ameliorations**

---

## 1. Infrastructure Docker

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Health checks | [+] | Tous services avec health checks |
| Restart policies | [+] | `unless-stopped` sur tous |
| Depends_on conditions | [+] | `service_healthy` utilise |
| Resource limits | [x] | **ABSENT** - Aucune limite CPU/RAM |
| Network isolation | [!] | Reseau par defaut Docker |
| Image tags | [!] | postgres:16-alpine ok, n8n:2.0.3 ok |
| Non-root users | [!] | claude-service et bot root |
| Multi-stage builds | [x] | **ABSENT** |

### Details

**docker-compose.yml** (lignes 1-116):
- PostgreSQL: health check via `pg_isready`, volume nomme `postgres-data`
- n8n: health check HTTP, data sur bind mount `./n8n-data`
- claude-service: health check HTTP port 8080, start_period 60s
- discord-bot: health check HTTP port 8000

**Gaps identifies**:
1. **Resource limits absents** - Risque OOM en production
2. **Containers root** - Vulnerabilite securite
3. **Pas de multi-stage** - Images plus lourdes que necessaire

### Recommandations

```yaml
# Ajouter a chaque service:
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.25'
      memory: 256M
```

---

## 2. Robustesse Applicative

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Retry logic | [!] | Claude CLI uniquement (1 retry) |
| Exponential backoff | [x] | **ABSENT** |
| Circuit breaker | [x] | **ABSENT** |
| Timeouts | [+] | 600s Claude, 660s bot client |
| Graceful shutdown | [!] | Partiel - DB close ok |
| Connection pooling | [+] | SQLAlchemy + asyncpg pools |
| Error handling | [!] | Catch-all `Exception` frequent |

### Details

**claude-service/services/claude_service.py** (ligne 67-73):
```python
for attempt in range(settings.retry_count + 1):
    result = await _execute_cli(cmd, prompt, exec_dir, settings, attempt)
    if result is not None:
        return result
```
- Retry simple, pas de backoff
- `retry_count=1` par defaut

**claude-service/database.py** (lignes 40-68):
```python
_engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
```
- Pool pre-ping bon pour reconnexion
- Pas de circuit breaker si DB down

**bot/main.py** (lignes 127-151):
```python
done, pending = await asyncio.wait(
    [bot_task, api_task],
    return_when=asyncio.FIRST_COMPLETED,
)
# Cancel pending tasks
```
- Shutdown propre des tasks
- Pas de signal handlers explicites

### Gaps identifies

1. **Pas de backoff exponentiel** - Surcharge en cas de retry storm
2. **Pas de circuit breaker** - Cascade failures possible
3. **Error handling generique** - `except Exception` masque les bugs
4. **Pas de rate limiting** - Vulnerable aux abus

### Recommandations

```python
# Utiliser tenacity pour retry
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def call_claude_cli(...):
    ...
```

---

## 3. Observabilite

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Health endpoints | [+] | /health sur tous services |
| Structured logging | [!] | basicConfig, pas JSON |
| Request tracing | [!] | execution_id partiel |
| Metrics | [x] | **ABSENT** |
| Alerting | [x] | **ABSENT** |
| Log aggregation | [x] | **ABSENT** |
| Error reporting | [x] | **ABSENT** (pas Sentry) |

### Details

**Health endpoints**:
- claude-service: `GET /health` -> `{"status": "healthy", "version": "1.0.0"}`
- discord-bot: `GET /health` -> `{"status": "healthy", "discord_connected": true, "guild_count": N}`

**Logging** (claude-service/config.py ligne 148):
```python
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
```
- Format texte, pas JSON structure
- Pas de correlation ID

**Execution logging** (claude-service/loggers/unified_logger.py):
- Logs riches par execution (SUMMARY.md, timeline.json)
- Pas d'export vers monitoring externe

### Gaps identifies

1. **Pas de metriques** - Prometheus/CloudWatch inexistant
2. **Logs non structures** - Difficile a parser
3. **Pas de tracing distribue** - Correlation partielle
4. **Pas d'alerting** - Aucune notification d'erreur

### Recommandations

```python
# Ajouter structlog pour JSON logging
import structlog
logger = structlog.get_logger()
logger.info("request_received", path="/summarize", correlation_id=req_id)
```

```yaml
# Pour AWS CloudWatch
services:
  claude-service:
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/ai-news-bot
        awslogs-region: eu-west-1
        awslogs-stream-prefix: claude-service
```

---

## 4. Persistance & Backup

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Data volumes | [+] | postgres-data nomme |
| Backup strategy | [x] | **ABSENT** |
| Migrations | [!] | SQL manuel, pas Alembic |
| Point-in-time recovery | [x] | **ABSENT** |
| Data encryption at rest | [x] | **ABSENT** |
| Volume backup | [x] | **ABSENT** |

### Details

**Volumes** (docker-compose.yml lignes 111-115):
```yaml
volumes:
  postgres-data:
    name: ai-news-postgres-data
  claude-runtime:
    name: ai-news-claude-runtime
```

**Migrations** (migrations/001_add_article_status.sql):
- Migration SQL brute
- Pas de tracking de versions
- Pas de rollback automatise

**n8n data** (bind mount):
```yaml
volumes:
  - ./n8n-data:/home/node/.n8n
```
- Donnees n8n sur filesystem local
- Non sauvegarde

### Gaps critiques

1. **AUCUNE strategie de backup** - Perte de donnees possible
2. **Migrations manuelles** - Risque d'erreur humaine
3. **n8n data vulnerable** - Bind mount sans backup
4. **Pas de PITR** - Recovery limite

### Recommandations AWS

| Service local | Service AWS | Avantage |
|---------------|-------------|----------|
| PostgreSQL container | RDS PostgreSQL | Backups auto, Multi-AZ, PITR |
| postgres-data volume | RDS | Snapshots automatiques |
| n8n-data bind mount | EFS | Backup AWS Backup |

```bash
# Backup PostgreSQL avant migration
docker exec ai-news-postgres pg_dump -U ainews ainews > backup_$(date +%Y%m%d).sql
```

---

## 5. CI/CD

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| GitHub Actions | [x] | **ABSENT** |
| Tests automatises | [!] | Tests presents, pas CI |
| Build reproductible | [!] | Pas de lock files |
| Image registry | [x] | **ABSENT** |
| Deployment automation | [x] | **ABSENT** |
| Rollback strategy | [x] | **ABSENT** |

### Details

**Tests existants** (claude-service/tests/, bot/tests/):
- Tests unitaires presents
- pytest + pytest-asyncio configures
- Pas d'integration CI

**Requirements** (requirements.txt):
```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
```
- Ranges de versions, pas de lock
- Builds non reproductibles

### Gaps critiques

1. **Aucun pipeline CI/CD** - Deploiement manuel uniquement
2. **Pas d'image registry** - Rebuild a chaque deploy
3. **Lock files absents** - Versions non pinees
4. **Pas de rollback** - Risque en production

### Recommandations

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd claude-service && pip install -r requirements.txt && pytest
          cd ../bot && pip install -r requirements.txt && pytest

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Build and push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -t $ECR_REGISTRY/claude-service:${{ github.sha }} ./claude-service
          docker push $ECR_REGISTRY/claude-service:${{ github.sha }}
```

---

## 6. Configuration Production

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Env vars separation | [+] | .env.example present |
| Secrets management | [!] | .env file local |
| Default values | [+] | Fallbacks presents |
| Validation | [+] | pydantic-settings |
| Dev/Prod differentiation | [x] | **ABSENT** |

### Details

**Configuration** (claude-service/config.py):
```python
class Settings(BaseSettings):
    claude_model: str = "sonnet"
    claude_timeout: int = 600
    retry_count: int = 1
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
```
- Validation Pydantic
- Defaults raisonnables

**Secrets** (.gitignore):
```
.env
*.credentials.json
```
- Secrets non commites

### Gaps identifies

1. **Pas de profils dev/prod** - Meme config partout
2. **Secrets en .env** - Pas de secrets manager
3. **Pas de feature flags** - Deploiement all-or-nothing

### Recommandations AWS

```python
# Utiliser AWS Secrets Manager
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# En ECS, utiliser secrets dans task definition
```

---

## 7. Scalabilite

### Checklist

| Element | Status | Details |
|---------|--------|---------|
| Stateless services | [!] | claude-service avec logs locaux |
| Horizontal scaling | [!] | n8n single-instance |
| Database connections | [+] | Pool sizing ok |
| Bottlenecks | [!] | Claude CLI serialise |
| Cache layer | [x] | **ABSENT** |
| Queue system | [x] | **ABSENT** |

### Details

**SPOF identifies**:
1. **n8n single instance** - Pas de HA natif
2. **PostgreSQL single instance** - Pas de replica
3. **Claude CLI serialise** - 1 requete a la fois

**Stateful components**:
- `claude-runtime` volume - Donnees Claude CLI
- `./logs` bind mount - Logs d'execution
- `./n8n-data` bind mount - Workflows n8n

### Gaps identifies

1. **n8n non scalable** - Architecture single-master
2. **Pas de queue** - Pics de charge mal geres
3. **Logs locaux** - Perte si instance terminee
4. **Claude rate limits** - Pas de gestion

### Recommandations

```yaml
# Pour AWS ECS avec scaling
services:
  claude-service:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

---

## Recommandations AWS Specifiques

### Architecture Cible

```
                    +-----------------+
                    |  Application    |
                    |  Load Balancer  |
                    +--------+--------+
                             |
            +----------------+----------------+
            |                                 |
    +-------v-------+               +---------v--------+
    |   ECS Fargate |               |   ECS Fargate    |
    | claude-service|               |   discord-bot    |
    +-------+-------+               +---------+--------+
            |                                 |
            +----------------+----------------+
                             |
                    +--------v--------+
                    |   RDS PostgreSQL |
                    |   (Multi-AZ)     |
                    +-----------------+
```

### Services AWS Recommandes

| Composant | Service AWS | Justification |
|-----------|-------------|---------------|
| PostgreSQL | RDS PostgreSQL | Backups auto, Multi-AZ, PITR |
| Containers | ECS Fargate | Serverless, auto-scaling |
| n8n | EC2 t3.medium | Persistance necessaire |
| Logs | CloudWatch Logs | Centralisation, retention |
| Secrets | Secrets Manager | Rotation, audit |
| Images | ECR | Registry prive |
| Load Balancing | ALB | Health checks, SSL |
| DNS | Route 53 | Failover |

### Estimation Couts Mensuels

| Service | Specs | Cout estime |
|---------|-------|-------------|
| RDS db.t3.micro | 20GB, Multi-AZ | ~$30 |
| ECS Fargate | 2 services x 0.5 vCPU | ~$20 |
| EC2 t3.medium (n8n) | 1 instance | ~$30 |
| ALB | 1 LCU | ~$20 |
| ECR | 5GB | ~$0.50 |
| CloudWatch | 5GB logs | ~$3 |
| **Total** | | **~$100-110/mois** |

---

## Plan de Deploiement AWS

### Phase 1: Preparation (1-2 jours)

| Tache | Priorite | Effort |
|-------|----------|--------|
| Creer compte AWS / IAM | Critique | 2h |
| Setup VPC avec subnets publics/prives | Critique | 2h |
| Creer RDS PostgreSQL Multi-AZ | Critique | 1h |
| Migrer schema DB vers RDS | Critique | 1h |
| Creer ECR repos | Critique | 30min |

### Phase 2: Containerisation (1-2 jours)

| Tache | Priorite | Effort |
|-------|----------|--------|
| Ajouter resource limits docker-compose | Haute | 30min |
| Multi-stage Dockerfiles | Moyenne | 2h |
| Push images vers ECR | Critique | 1h |
| Creer ECS cluster | Critique | 1h |
| Task definitions ECS | Critique | 2h |

### Phase 3: Deploiement (1 jour)

| Tache | Priorite | Effort |
|-------|----------|--------|
| Deployer services ECS | Critique | 2h |
| Configurer ALB | Haute | 1h |
| Configurer Secrets Manager | Haute | 1h |
| Deployer n8n sur EC2 | Critique | 2h |
| Tests de connectivite | Critique | 2h |

### Phase 4: Observabilite (1 jour)

| Tache | Priorite | Effort |
|-------|----------|--------|
| CloudWatch Logs | Haute | 1h |
| CloudWatch Alarms | Haute | 2h |
| Dashboard CloudWatch | Moyenne | 2h |
| SNS Notifications | Haute | 1h |

### Phase 5: CI/CD (1-2 jours)

| Tache | Priorite | Effort |
|-------|----------|--------|
| GitHub Actions workflow | Haute | 2h |
| Tests automatises | Haute | 2h |
| Build et push ECR | Critique | 2h |
| Deploy to ECS | Critique | 2h |

**Duree totale estimee: 5-8 jours**

---

## Matrice des Priorites

### Corrections Bloquantes (Avant Production)

| Item | Impact | Effort | Fichier |
|------|--------|--------|---------|
| Resource limits Docker | Stabilite | Faible | docker-compose.yml |
| Backup PostgreSQL | Data safety | Faible | script a creer |
| Secrets Manager | Securite | Moyen | config.py, ECS task def |
| Health check plus profonds | Fiabilite | Moyen | api/routes.py |

### Corrections Recommandees (Sprint 1)

| Item | Impact | Effort | Fichier |
|------|--------|--------|---------|
| Structured logging JSON | Debug | Moyen | config.py, tous services |
| Retry avec backoff | Resilience | Moyen | claude_service.py |
| GitHub Actions CI | Quality | Moyen | .github/workflows/ |
| Multi-stage Dockerfiles | Performance | Moyen | Dockerfile |

### Corrections Futures (Sprint 2+)

| Item | Impact | Effort | Fichier |
|------|--------|--------|---------|
| Circuit breaker | Resilience | Eleve | services/ |
| Metriques Prometheus | Observabilite | Eleve | nouveau |
| Alembic migrations | Maintenabilite | Moyen | migrations/ |
| Feature flags | Deploiement | Eleve | nouveau |

---

## Conclusion

Le projet daily-ai-webhook est **fonctionnel mais pas pret pour production AWS** dans son etat actuel.

**Points forts**:
- Architecture bien structuree (layered)
- Health checks complets
- Connection pooling correct
- Tests unitaires presents

**Gaps critiques**:
- Aucune strategie de backup
- Pas de CI/CD
- Resource limits absents
- Secrets en fichiers locaux

**Effort estime pour production-ready**: 5-8 jours

**Recommandation**: Prioriser Phase 1 (RDS + backups) et Phase 2 (containerisation) avant tout deploiement production.

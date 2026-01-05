# Security Audit Report - daily-ai-webhook

**Date:** 2026-01-05
**Scope:** Production deployment on AWS
**Stack:** n8n + Claude + PostgreSQL + Discord

---

## Executive Summary

| Severity | Count | Critical Items |
|----------|-------|----------------|
| **CRITICAL** | 1 | OAuth tokens committed in repo |
| **HIGH** | 5 | No API auth, exposed ports, SQL string formatting |
| **MEDIUM** | 6 | No rate limiting, CORS absent, deps outdated |
| **LOW** | 4 | Chromium --no-sandbox, verbose logging |

**Recommendation:** Ne pas deployer en production avant remediation des issues CRITICAL et HIGH.

---

## Findings Detail

### 1. Secrets & Credentials

#### [CRITICAL] SEC-001: OAuth Tokens Committed in Repository

**Fichier:** `claude-service/config/.credentials.json`

```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1766442696335
  }
}
```

**Impact:** Acces complet au compte Claude (inference, profile, sessions). Tokens valides jusqu'en 2025.

**Remediation:**
1. Revoquer immediatement les tokens via console Anthropic
2. Supprimer le fichier du repo avec `git filter-branch`
3. Ajouter `.credentials.json` au `.gitignore` (deja present mais fichier commis avant)
4. Utiliser AWS Secrets Manager ou env vars pour les credentials runtime

---

#### [MEDIUM] SEC-002: .gitignore Incomplet

**Analyse du `.gitignore`:**

| Pattern | Status | Risque |
|---------|--------|--------|
| `.env` | OK | - |
| `*.credentials.json` | OK mais fichier deja commis | HIGH |
| `.mcp.json` (root) | OK | - |
| `claude-service/config/.mcp.json` | Exclu (template) | Low |
| `n8n-data/` | OK | - |

**Remediation:**
- Verifier que tous les fichiers sensibles sont bien ignores avant le commit initial
- Ajouter pre-commit hook pour detecter les patterns de secrets

---

### 2. Configuration Docker

#### [HIGH] SEC-003: Ports Exposes sur 0.0.0.0

**docker-compose.yml:**

```yaml
ports:
  - "5434:5432"   # PostgreSQL - accessible depuis l'exterieur
  - "5678:5678"   # n8n - interface web
  - "8080:8080"   # claude-service API
  - "8000:8000"   # discord-bot API
```

**Impact:** Tous les services accessibles depuis n'importe quelle interface reseau.

**Remediation:**

```yaml
# Bind uniquement sur localhost pour dev
ports:
  - "127.0.0.1:5434:5432"
  - "127.0.0.1:5678:5678"

# En production AWS: utiliser Docker network interne + ALB
# Ne pas exposer PostgreSQL publiquement
```

---

#### [MEDIUM] SEC-004: Dockerfile Bot - Chromium sans Sandbox

**bot/Dockerfile:**

```dockerfile
ENV CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage"
```

**Impact:** Chromium s'execute sans isolation, permettant des exploits si du contenu malveillant est rendu.

**Remediation:**
- Utiliser un user non-root dans le container
- Configurer seccomp profile
- Considerer puppeteer-core avec sandbox en production

---

#### [LOW] SEC-005: Base Images Sans Version Pinned

**Dockerfiles:**

```dockerfile
FROM python:3.12-slim  # OK - version mineure specifiee
```

**Remediation:** Acceptable, mais considerer pin sur digest pour builds reproductibles:
```dockerfile
FROM python:3.12-slim@sha256:abc123...
```

---

### 3. Securite Reseau

#### [HIGH] SEC-006: Endpoints API Sans Authentification

**claude-service endpoints:**

| Endpoint | Auth | Rate Limit | Risk |
|----------|------|------------|------|
| `POST /summarize` | None | None | HIGH |
| `POST /analyze-weekly` | None | None | HIGH |
| `POST /check-urls` | None | None | MEDIUM |
| `POST /log-workflow` | None | None | LOW |
| `GET /health` | None | None | OK |

**discord-bot endpoints:**

| Endpoint | Auth | Rate Limit | Risk |
|----------|------|------------|------|
| `POST /publish` | None | None | HIGH |
| `POST /callback` | None | None | MEDIUM |

**Impact:** N'importe qui peut:
- Declencher des appels Claude ($$$)
- Publier sur Discord
- Engorger les services (DoS)

**Remediation:**

```python
# Ajouter API key auth
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.post("/summarize", dependencies=[Depends(verify_api_key)])
async def summarize(...):
    ...
```

---

#### [MEDIUM] SEC-007: Pas de Configuration CORS

**Analyse:** Aucune configuration CORS dans `main.py`.

**Impact:** En cas d'exposition web, XSS possible depuis autres origines.

**Remediation:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5678"],  # n8n only
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key"],
)
```

---

#### [MEDIUM] SEC-008: Pas de Rate Limiting

**Impact:** Vulnerable au DoS et abus des API Claude (couts).

**Remediation:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/summarize")
@limiter.limit("5/minute")  # Max 5 appels/min par IP
async def summarize(request: Request, ...):
    ...
```

---

### 4. Base de Donnees

#### [HIGH] SEC-009: PostgreSQL Accessible Externement

**docker-compose.yml:**

```yaml
ports:
  - "5434:5432"  # Expose publiquement
```

**Impact:** Acces potentiel a la base si credentials compromis.

**Remediation:**
- Ne pas exposer le port PostgreSQL
- Utiliser Docker network interne uniquement
- En production: AWS RDS avec security groups

---

#### [HIGH] SEC-010: SQL String Formatting dans MCP Repository

**claude-service/mcp_tools/repositories/article.py:**

```python
cur.execute(
    """
    SELECT ... FROM articles a
    WHERE a.mission_id = %s
      AND a.status = 'selected'
      AND a.created_at >= NOW() - INTERVAL '%s days'
    """,
    (mission_id, days),
)
```

**Analyse:** Le parametre `days` est interpole directement dans la string SQL avec `%s`. Bien que psycopg2 utilise des placeholders, le format `'%s days'` peut etre mal interprete.

**Impact:** Potentiel SQL injection si le parametre n'est pas valide.

**Remediation:**

```python
# Utiliser make_interval() qui est parametre-safe
cur.execute(
    """
    SELECT ... FROM articles a
    WHERE a.mission_id = %s
      AND a.status = 'selected'
      AND a.created_at >= NOW() - make_interval(days => %s)
    """,
    (mission_id, days),
)
```

Note: Le fichier `article_repository.py` utilise deja `make_interval()` correctement.

---

#### [LOW] SEC-011: Credentials DB dans URL

**docker-compose.yml:**

```yaml
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

**Status:** OK - utilise env vars, pas de hardcode.

---

### 5. Dependances

#### [MEDIUM] SEC-012: Dependances Sans Version Maximale

**claude-service/requirements.txt:**

```
fastapi>=0.115.0      # OK mais pas de max
sqlmodel>=0.0.22      # Pre-1.0, API instable
asyncpg>=0.30.0
psycopg2-binary>=2.9.10
```

**bot/requirements.txt:**

```
discord.py>=2.4.0
html2image>=2.0.4
Pillow>=10.0.0        # Historique de CVE
```

**Impact:** Mises a jour automatiques peuvent casser ou introduire vulnerabilites.

**Remediation:**

```
# Pin les versions en production
fastapi==0.115.6
Pillow==10.4.0  # Verifier CVE avant
```

---

#### [LOW] SEC-013: psycopg2-binary en Production

**Impact:** Package pre-compile, peut avoir des incompatibilites.

**Remediation:** Utiliser `psycopg2` compile depuis source en production.

---

### 6. Code

#### [MEDIUM] SEC-014: Subprocess sans Validation Stricte du Prompt

**claude-service/services/claude_service.py:**

```python
full_cmd = cmd + ["-p", prompt]
process = await asyncio.create_subprocess_exec(
    *full_cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env,
)
```

**Analyse:** Le prompt est passe directement au CLI. Si un attaquant controle le prompt, il pourrait potentiellement injecter des commandes.

**Status:** LOW - Le prompt est construit internement, pas depuis l'input utilisateur direct.

**Remediation:**
- Valider/sanitizer le prompt avant execution
- Logger les prompts pour audit

---

#### [LOW] SEC-015: Error Messages Exposes

**claude-service/api/routes.py:**

```python
return WorkflowLogResponse(success=False, error=str(e))
```

**Impact:** Stack traces et details internes exposes aux clients.

**Remediation:**

```python
import logging
logger.exception("Error in workflow log")
return WorkflowLogResponse(success=False, error="Internal error")
```

---

#### [LOW] SEC-016: Logging Verbose

**Observation:** Le logging inclut beaucoup de details (paths, IDs, etc.) ce qui peut faciliter le reconnaissance.

**Remediation:** En production, reduire le niveau de log a WARNING.

---

#### [LOW] SEC-017: Validation Input Adequate

**claude-service/api/models.py:**

```python
class CheckUrlsRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)
    days: int = Field(default=7, ge=1, le=30)
```

**Status:** OK - Pydantic valide les inputs.

---

## Checklist de Remediation

### Pre-Production (Bloquant)

- [ ] **SEC-001**: Revoquer tokens OAuth et supprimer du repo history
- [ ] **SEC-003**: Ne pas exposer PostgreSQL publiquement
- [ ] **SEC-006**: Implementer authentification API (API key ou JWT)
- [ ] **SEC-009**: Configurer Docker network interne pour DB
- [ ] **SEC-010**: Corriger SQL string interpolation dans article.py

### Recommande (Avant Production)

- [ ] **SEC-007**: Configurer CORS restrictif
- [ ] **SEC-008**: Implementer rate limiting (slowapi)
- [ ] **SEC-012**: Pin versions des dependances
- [ ] **SEC-004**: Configurer user non-root dans containers

### Nice-to-Have

- [ ] **SEC-005**: Pin images Docker sur digest
- [ ] **SEC-013**: Compiler psycopg2 depuis source
- [ ] **SEC-015**: Masquer errors details en production
- [ ] **SEC-016**: Reduire verbosity des logs

---

## Configuration AWS Recommandee

### Architecture Securisee

```
                    Internet
                        |
                    [ALB/API Gateway]
                        |
                   +----+----+
                   |         |
             [claude-svc] [discord-bot]
                   |         |
             [Internal VPC Network]
                   |
              [RDS PostgreSQL]
              (security group: only from ECS tasks)
```

### Services AWS

| Composant | Service AWS | Configuration |
|-----------|-------------|---------------|
| Secrets | Secrets Manager | OAuth, API keys, DB password |
| Database | RDS PostgreSQL | Private subnet, security group |
| Containers | ECS Fargate | Private subnet, task roles |
| Load Balancer | ALB | HTTPS only, WAF enabled |
| Logs | CloudWatch | Encrypted, retention policy |

### IAM Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:daily-ai-webhook/*"
    }
  ]
}
```

---

## Annexes

### A. Fichiers Analyses

| Path | Type | Issues |
|------|------|--------|
| `docker-compose.yml` | Config | SEC-003, SEC-009 |
| `claude-service/config/.credentials.json` | Credential | SEC-001 |
| `claude-service/api/routes.py` | Code | SEC-006, SEC-015 |
| `claude-service/mcp_tools/repositories/article.py` | Code | SEC-010 |
| `bot/api.py` | Code | SEC-006 |
| `bot/Dockerfile` | Config | SEC-004 |
| `*/requirements.txt` | Deps | SEC-012 |

### B. Commandes de Verification

```bash
# Chercher secrets hardcodes
grep -r "sk-ant\|api_key\|password" --include="*.py" --include="*.json"

# Verifier .gitignore
git ls-files --cached | grep -E "\.(env|credentials|secret)"

# Scanner vulnerabilites deps
pip install safety
safety check -r requirements.txt
```

### C. Pre-commit Hook Suggere

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

*Rapport genere le 2026-01-05 par Claude Security Audit*

# Plan Directeur : Batch C - Workflow n8n + Claude Service + Discord

**Date de creation** : 2025-12-21
**Derniere mise a jour** : 2025-12-21
**Complexite Globale** : Moyenne
**Duree Estimee Totale** : 4h - 6h

---

## Vue d'Ensemble

### Description

Ce batch implemente le flux complet du MVP : n8n collecte les articles RSS, les envoie au service Claude (sidecar HTTP) pour analyse/resume, puis publie le resultat sur Discord via webhook.

L'architecture utilise un **service sidecar** qui wrappe Claude Code CLI dans un container Docker avec une API HTTP. Cela permet d'utiliser l'abonnement Claude Pro/Max existant tout en gardant une architecture propre et decouplée.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Network                                   │
│                                                                          │
│  ┌──────────────┐     POST /summarize      ┌──────────────────────┐     │
│  │     n8n      │ ───────────────────────▶ │   claude-service     │     │
│  │   :5678      │                          │   (FastAPI + CLI)    │     │
│  │              │ ◀─────────────────────── │       :8080          │     │
│  │  - Schedule  │      JSON response       │                      │     │
│  │  - RSS Feed  │                          │  - /summarize        │     │
│  │  - Merge     │                          │  - /health           │     │
│  │  - HTTP Req  │                          │                      │     │
│  └──────┬───────┘                          └──────────────────────┘     │
│         │                                                                │
│         │ POST webhook                                                   │
│         ▼                                                                │
│  ┌──────────────┐                                                       │
│  │   Discord    │                                                       │
│  └──────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Decisions Techniques

| Question | Decision | Justification |
|----------|----------|---------------|
| Integration Claude | **Sidecar HTTP** | Utilise l'abonnement Pro/Max, decouple, testable |
| Auth Claude CLI | **Mount auth.json** | Simple, reutilise l'auth existante |
| Langage wrapper | **Python + FastAPI** | Async, config Pydantic, Swagger auto |
| Configuration | **YAML + env vars** | Flexible, 12-factor app |
| Format articles | **JSON structure** | Standard, facile a manipuler |
| Limite par source | **10 articles** | 30 max avant dedup, suffisant pour MVP |
| Logique dedup | **URL puis titre** | URL unique, titre en fallback normalise |
| Retry | **Parametrable (defaut: 1)** | Configurable dans config.yaml |
| Fallback 0 articles | **Claude decide** | Inclus dans les instructions du prompt |
| Healthcheck | **Endpoint /health** | Standard, Docker healthcheck |
| Logging | **Stdout** | Docker logs natif |
| Rate limiting | **Non** | 1 appel/jour, pas necessaire |
| Metriques | **Non pour MVP** | A ajouter en Sprint 2 si besoin |

### Dependances

**Prerequis utilisateur :**
- Claude Code CLI authentifie sur l'hote (`claude /login` deja fait)
- Fichier `~/.config/claude-code/auth.json` existant

**Modules existants impactes :**
- `docker-compose.yml` : Ajout du service claude-service
- `.env.example` : Ajout des variables de config

### Risques Identifies

| Risque | Impact | Mitigation |
|--------|--------|------------|
| RSS feeds indisponibles | Moyen | 3 sources, continuer si 1+ disponible |
| Claude CLI timeout | Eleve | Timeout configurable, retry |
| auth.json expire | Moyen | Documenter la procedure de refresh |
| Format RSS variable | Moyen | Code node flexible |
| Discord webhook down | Faible | Logging erreur |

---

## Structure des Fichiers a Creer

```
daily-ai-webhook/
├── docker-compose.yml          # MODIFIER: ajouter claude-service
├── .env.example                 # MODIFIER: ajouter nouvelles variables
├── claude-service/              # NOUVEAU: service wrapper
│   ├── Dockerfile
│   ├── main.py                  # FastAPI application
│   ├── config.yaml              # Configuration par defaut
│   └── requirements.txt
├── scripts/
│   └── summarize.sh             # NOUVEAU: script reference (optionnel)
└── workflows/
    └── daily-news-workflow.json # NOUVEAU: export n8n backup
```

---

## Plan d'Implementation

### Phase 1 : Service Claude (Sidecar HTTP)

**Duree Estimee** : 1h30 - 2h

**Objectif** : Creer le service FastAPI qui wrappe Claude Code CLI.

---

#### Etape 1.1 : Creer la structure claude-service/

**Description :**

Creer le dossier `claude-service/` avec les fichiers de base.

**Fichiers a creer :**

1. `claude-service/requirements.txt`
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pyyaml==6.0.2
pydantic==2.10.3
pydantic-settings==2.7.0
```

2. `claude-service/config.yaml`
```yaml
# Claude Service Configuration

claude:
  model: "sonnet"           # Model Claude a utiliser
  timeout: 120              # Timeout en secondes
  retry_count: 1            # Nombre de retries en cas d'echec
  max_tokens: 4096          # Limite de tokens pour la reponse

server:
  host: "0.0.0.0"
  port: 8080
  log_level: "info"

paths:
  rules: "/app/config/rules.md"
  editorial_guide: "/app/config/editorial-guide.md"
```

**Complexite :** Faible
**Duree Estimee :** 10 min

---

#### Etape 1.2 : Creer main.py (FastAPI)

**Description :**

Implementer l'application FastAPI avec les endpoints `/health` et `/summarize`.

**Fichier :** `claude-service/main.py`

```python
#!/usr/bin/env python3
"""
Claude Service - HTTP wrapper for Claude Code CLI
Provides /summarize endpoint for n8n integration
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Configuration
class Settings(BaseSettings):
    claude_model: str = "sonnet"
    claude_timeout: int = 120
    retry_count: int = 1
    rules_path: str = "/app/config/rules.md"
    editorial_guide_path: str = "/app/config/editorial-guide.md"
    log_level: str = "info"

    class Config:
        env_prefix = "CLAUDE_"


settings = Settings()

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("claude-service")

# FastAPI app
app = FastAPI(
    title="Claude Service",
    description="HTTP wrapper for Claude Code CLI",
    version="1.0.0"
)


# Models
class Article(BaseModel):
    title: str
    url: str
    description: str = ""
    pub_date: str = ""
    source: str = ""


class SummarizeRequest(BaseModel):
    articles: list[Article] = Field(..., min_length=0)


class SummarizeResponse(BaseModel):
    summary: str
    article_count: int
    success: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


# Helpers
def load_file(path: str) -> str:
    """Load content from a file."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
        return ""


def build_prompt(articles: list[Article]) -> str:
    """Build the prompt for Claude CLI."""
    rules = load_file(settings.rules_path)
    guide = load_file(settings.editorial_guide_path)

    articles_text = "\n---\n".join([
        f"[{i+1}] {a.title}\n"
        f"Source: {a.source}\n"
        f"URL: {a.url}\n"
        f"Date: {a.pub_date}\n"
        f"Summary: {a.description[:500]}"
        for i, a in enumerate(articles)
    ])

    return f"""You are an AI/ML news editor. Your task is to analyze the following articles and produce a daily news summary.

=== SELECTION RULES ===
{rules}

=== EDITORIAL GUIDELINES ===
{guide}

=== ARTICLES TO ANALYZE ({len(articles)} articles) ===
{articles_text if articles else "No articles provided today."}

=== INSTRUCTIONS ===
1. Analyze all articles according to the selection rules
2. If no articles are relevant or provided, write a brief message explaining there's no significant AI news today
3. Select the most relevant and important news
4. Write the summary following the editorial guidelines exactly
5. Use the exact format specified (TOP HEADLINES, etc.)
6. Keep it under 2000 characters total
7. Output ONLY the formatted summary, nothing else

Generate the summary now:"""


async def call_claude_cli(prompt: str) -> str:
    """Call Claude Code CLI with the prompt."""
    cmd = ["claude", "-p", prompt, "--no-input"]

    for attempt in range(settings.retry_count + 1):
        try:
            logger.info(f"Calling Claude CLI (attempt {attempt + 1})")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.claude_timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Claude CLI error: {error_msg}")
                if attempt < settings.retry_count:
                    await asyncio.sleep(2)
                    continue
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            return stdout.decode().strip()

        except asyncio.TimeoutError:
            logger.error(f"Claude CLI timeout after {settings.claude_timeout}s")
            if attempt < settings.retry_count:
                continue
            raise RuntimeError(f"Claude CLI timeout after {settings.claude_timeout}s")

    raise RuntimeError("All retry attempts failed")


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """Generate a news summary from articles using Claude CLI."""
    logger.info(f"Received {len(request.articles)} articles to summarize")

    try:
        prompt = build_prompt(request.articles)
        summary = await call_claude_cli(prompt)

        logger.info("Summary generated successfully")
        return SummarizeResponse(
            summary=summary,
            article_count=len(request.articles),
            success=True
        )

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return SummarizeResponse(
            summary="",
            article_count=len(request.articles),
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Complexite :** Moyenne
**Duree Estimee :** 45 min - 1h

---

#### Etape 1.3 : Creer le Dockerfile

**Description :**

Creer le Dockerfile pour le service Claude.

**Fichier :** `claude-service/Dockerfile`

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY config.yaml .

# Create config directory (will be mounted)
RUN mkdir -p /app/config

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Complexite :** Moyenne
**Duree Estimee :** 20 min

---

#### Etape 1.4 : Mettre a jour docker-compose.yml

**Description :**

Ajouter le service claude-service au docker-compose existant.

**Modifications :** `docker-compose.yml`

```yaml
services:
  n8n:
    image: n8nio/n8n:2.0.3
    container_name: ai-news-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - GENERIC_TIMEZONE=Europe/Paris
      - TZ=Europe/Paris
    volumes:
      - ./n8n-data:/home/node/.n8n
      - ./config:/home/node/config:ro
      - ./scripts:/home/node/scripts:ro
    depends_on:
      claude-service:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  claude-service:
    build: ./claude-service
    container_name: ai-news-claude
    restart: unless-stopped
    environment:
      - CLAUDE_MODEL=${CLAUDE_MODEL:-sonnet}
      - CLAUDE_TIMEOUT=${CLAUDE_TIMEOUT:-120}
      - CLAUDE_RETRY_COUNT=${CLAUDE_RETRY_COUNT:-1}
      - CLAUDE_LOG_LEVEL=${CLAUDE_LOG_LEVEL:-info}
    volumes:
      # Mount Claude auth (read-only)
      - ${HOME}/.config/claude-code:/root/.config/claude-code:ro
      # Mount config files (read-only)
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    # Internal network only - no external port needed
    # Uncomment for debugging:
    # ports:
    #   - "8080:8080"
```

**Complexite :** Faible
**Duree Estimee :** 15 min

---

#### Etape 1.5 : Mettre a jour .env.example

**Description :**

Ajouter les nouvelles variables d'environnement.

**Modifications :** `.env.example`

```bash
# n8n Configuration
N8N_USER=admin
N8N_PASSWORD=changeme

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Claude Service Configuration
CLAUDE_MODEL=sonnet
CLAUDE_TIMEOUT=120
CLAUDE_RETRY_COUNT=1
CLAUDE_LOG_LEVEL=info
```

**Complexite :** Faible
**Duree Estimee :** 5 min

---

### Phase 2 : Workflow n8n

**Duree Estimee** : 1h30 - 2h

**Objectif** : Creer le workflow n8n qui collecte les RSS, appelle claude-service, et publie sur Discord.

---

#### Etape 2.1 : Creer le workflow avec Schedule Trigger

**Description :**

Dans l'interface n8n (http://localhost:5678), creer un nouveau workflow nomme "Daily AI News - MVP".

1. Ajouter un node **Schedule Trigger**
   - Cron: `0 8 * * *` (8h tous les jours, Europe/Paris)

**Complexite :** Faible
**Duree Estimee :** 5 min

---

#### Etape 2.2 : Configurer les 3 nodes RSS Feed

**Description :**

Ajouter 3 nodes "RSS Feed" connectes au Schedule Trigger :

1. **Anthropic Blog** : `https://www.anthropic.com/feed.xml`
2. **OpenAI Blog** : `https://openai.com/blog/rss/`
3. **Hugging Face Blog** : `https://huggingface.co/blog/feed.xml`

Configuration de chaque node :
- URL : l'URL du feed
- Ignore SSL Issues : false

**Complexite :** Faible
**Duree Estimee :** 15 min

---

#### Etape 2.3 : Ajouter le node Merge

**Description :**

Ajouter un node "Merge" apres les 3 nodes RSS.

Configuration :
- Mode : "Append"
- Nombre d'inputs : 3

**Complexite :** Faible
**Duree Estimee :** 5 min

---

#### Etape 2.4 : Creer le node Code pour Dedup et Formatage

**Description :**

Ajouter un node "Code" (JavaScript) pour deduplication et formatage.

```javascript
// Dedup and format articles for Claude Service
const articles = $input.all();
const seen = new Set();
const now = new Date();
const cutoff = new Date(now.getTime() - 48 * 60 * 60 * 1000); // 48h ago

const unique = [];

for (const item of articles) {
  const data = item.json;

  // Extract fields (handle RSS structure variations)
  const url = data.link || data.guid || '';
  const title = data.title || '';
  const pubDate = data.pubDate || data.isoDate || data.date || '';
  const description = data.description || data.summary || data.content || '';
  const source = extractDomain(url);

  // Dedup key: URL or normalized title
  const dedupKey = url || normalizeTitle(title);

  if (!dedupKey || seen.has(dedupKey)) continue;
  seen.add(dedupKey);

  // Filter articles older than 48h
  if (pubDate) {
    const articleDate = new Date(pubDate);
    if (articleDate < cutoff) continue;
  }

  unique.push({
    json: {
      title: cleanText(title),
      url: url,
      description: cleanText(description).substring(0, 500),
      pub_date: pubDate,
      source: source
    }
  });

  if (unique.length >= 20) break;
}

return unique;

// Helper functions
function normalizeTitle(title) {
  return title.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function cleanText(text) {
  return text.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return 'unknown';
  }
}
```

**Complexite :** Moyenne
**Duree Estimee :** 20 min

---

#### Etape 2.5 : Creer le node Code pour preparer le payload

**Description :**

Ajouter un node "Code" pour construire le payload JSON pour claude-service.

```javascript
// Prepare payload for Claude Service
const articles = $input.all().map(item => item.json);

return [{
  json: {
    articles: articles
  }
}];
```

**Complexite :** Faible
**Duree Estimee :** 5 min

---

#### Etape 2.6 : Configurer le node HTTP Request pour Claude Service

**Description :**

Ajouter un node "HTTP Request" pour appeler claude-service.

Configuration :
- Method : **POST**
- URL : `http://claude-service:8080/summarize`
- Headers :
  - `Content-Type`: `application/json`
- Body : JSON
- Specify Body : Using JSON
- JSON : `{{ $json }}`
- Options :
  - Timeout : 180000 (3 minutes)

**Complexite :** Faible
**Duree Estimee :** 15 min

---

#### Etape 2.7 : Creer le node Code pour formater Discord

**Description :**

Ajouter un node "Code" pour formater la reponse en embed Discord.

```javascript
// Format response for Discord
const response = $input.first().json;

if (!response.success) {
  // Error case - send error notification
  return [{
    json: {
      content: `**AI News Bot Error**\n\nFailed to generate summary.\nError: ${response.error || 'Unknown error'}\nTime: ${new Date().toISOString()}`
    }
  }];
}

// Success case - send embed
return [{
  json: {
    embeds: [{
      title: "Daily AI/ML News Digest",
      description: response.summary,
      color: 5814783,
      timestamp: new Date().toISOString(),
      footer: {
        text: `Powered by Claude | ${response.article_count} articles analyzed`
      }
    }]
  }
}];
```

**Complexite :** Faible
**Duree Estimee :** 10 min

---

#### Etape 2.8 : Configurer le node HTTP Request pour Discord

**Description :**

Ajouter un node "HTTP Request" pour envoyer le message Discord.

Configuration :
- Method : **POST**
- URL : `{{ $env.DISCORD_WEBHOOK_URL }}` ou URL directe depuis .env
- Headers :
  - `Content-Type`: `application/json`
- Body : JSON
- Specify Body : Using JSON
- JSON : `{{ $json }}`

**Complexite :** Faible
**Duree Estimee :** 10 min

---

### Phase 3 : Tests et Validation

**Duree Estimee** : 45 min - 1h

**Objectif** : Valider le flux complet et corriger les problemes.

---

#### Etape 3.1 : Build et demarrage des services

**Description :**

Construire et demarrer les services Docker.

```bash
# Build claude-service
docker-compose build claude-service

# Start all services
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

**Complexite :** Faible
**Duree Estimee :** 10 min

---

#### Etape 3.2 : Test du service Claude independamment

**Description :**

Tester le service Claude avant de tester le workflow complet.

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test summarize endpoint (optionnel - si port expose)
curl -X POST http://localhost:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{"articles": [{"title": "Test", "url": "https://example.com", "description": "Test article", "pub_date": "", "source": "test"}]}'
```

**Complexite :** Faible
**Duree Estimee :** 10 min

---

#### Etape 3.3 : Test manuel du workflow n8n

**Description :**

1. Ouvrir n8n (http://localhost:5678)
2. Ouvrir le workflow "Daily AI News - MVP"
3. Cliquer sur "Execute Workflow"
4. Verifier chaque etape :
   - RSS feeds retournent des articles
   - Merge combine les resultats
   - Dedup reduit le nombre d'articles
   - Claude Service repond avec un resume
   - Discord recoit le message

**Complexite :** Faible
**Duree Estimee :** 15 min

---

#### Etape 3.4 : Debug et ajustements

**Description :**

Corriger les problemes identifies :
- Ajuster le code de dedup si necessaire
- Modifier le prompt si le resume n'est pas satisfaisant
- Ajuster le formatage Discord

**Complexite :** Variable
**Duree Estimee :** 15 min

---

### Phase 4 : Activation Production

**Duree Estimee** : 15 min

**Objectif** : Activer le workflow et exporter le backup.

---

#### Etape 4.1 : Exporter le workflow en JSON

**Description :**

1. Dans n8n, ouvrir le workflow
2. Menu (3 points) → Download
3. Sauvegarder dans `workflows/daily-news-workflow.json`

**Fichier cree :** `workflows/daily-news-workflow.json`

**Complexite :** Faible
**Duree Estimee :** 5 min

---

#### Etape 4.2 : Activer le workflow

**Description :**

1. Dans n8n, ouvrir le workflow
2. Basculer le toggle "Active" en haut a droite
3. Verifier que le status passe a "Active"

**Complexite :** Faible
**Duree Estimee :** 5 min

---

#### Etape 4.3 : Creer le script summarize.sh (reference)

**Description :**

Creer un script shell comme reference pour tests manuels en dehors de n8n.

**Fichier :** `scripts/summarize.sh`

```bash
#!/bin/bash
set -euo pipefail

# summarize.sh - Script reference pour tests manuels
# Utilisation: cat articles.json | ./summarize.sh
# Ou: ./summarize.sh articles.json

CONFIG_DIR="${CONFIG_DIR:-./config}"
ARTICLES_FILE="${1:-/dev/stdin}"

# Build prompt
prompt="You are an AI/ML news editor.

=== SELECTION RULES ===
$(cat "$CONFIG_DIR/rules.md")

=== EDITORIAL GUIDELINES ===
$(cat "$CONFIG_DIR/editorial-guide.md")

=== ARTICLES ===
$(cat "$ARTICLES_FILE")

=== INSTRUCTIONS ===
1. Analyze articles according to selection rules
2. If no significant news, say so briefly
3. Write summary following editorial guidelines
4. Output ONLY the formatted summary
"

# Call Claude CLI
claude -p "$prompt" --no-input
```

Rendre executable : `chmod +x scripts/summarize.sh`

**Complexite :** Faible
**Duree Estimee :** 5 min

---

## Points de Vigilance

- **Auth Claude** : Le fichier `~/.config/claude-code/auth.json` doit exister sur l'hote
- **Network Docker** : Les services communiquent via le nom de service (`claude-service:8080`)
- **Timeout** : 180s dans n8n pour laisser le temps a Claude de repondre
- **Healthcheck** : n8n attend que claude-service soit healthy avant de demarrer
- **Logs** : `docker-compose logs claude-service` pour debugger

---

## Dependances Entre Etapes

```
Phase 1 (Service Claude)
  1.1 → 1.2 → 1.3 → 1.4 → 1.5
                      ↓
Phase 2 (Workflow n8n)
  2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7 → 2.8
                                              ↓
Phase 3 (Tests)
  3.1 → 3.2 → 3.3 → 3.4
                      ↓
Phase 4 (Production)
  4.1 → 4.2 → 4.3
```

---

## Checklist Finale

| Etape | Description | Statut |
|-------|-------------|--------|
| 1.1 | Structure claude-service | ⬜ |
| 1.2 | main.py FastAPI | ⬜ |
| 1.3 | Dockerfile | ⬜ |
| 1.4 | docker-compose.yml | ⬜ |
| 1.5 | .env.example | ⬜ |
| 2.1 | Schedule Trigger | ⬜ |
| 2.2 | RSS Feeds x3 | ⬜ |
| 2.3 | Merge | ⬜ |
| 2.4 | Code Dedup | ⬜ |
| 2.5 | Code Payload | ⬜ |
| 2.6 | HTTP Claude Service | ⬜ |
| 2.7 | Code Discord Format | ⬜ |
| 2.8 | HTTP Discord | ⬜ |
| 3.1 | Build & Start | ⬜ |
| 3.2 | Test Claude Service | ⬜ |
| 3.3 | Test Workflow | ⬜ |
| 3.4 | Debug | ⬜ |
| 4.1 | Export JSON | ⬜ |
| 4.2 | Activer Workflow | ⬜ |
| 4.3 | Script reference | ⬜ |

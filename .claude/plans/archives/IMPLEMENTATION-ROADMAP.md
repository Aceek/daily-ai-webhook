# Implementation Roadmap - Intelligent News Agent

> **Référence:** [INTELLIGENT-NEWS-AGENT.md](./INTELLIGENT-NEWS-AGENT.md)
> **Date:** 22 décembre 2025
> **Estimation totale:** 3-5 jours

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASES D'IMPLÉMENTATION                             │
│                                                                          │
│   Phase 0          Phase 1          Phase 2          Phase 3             │
│   VALIDATION       CONFIG           AGENT            SOURCES             │
│   ──────────       ──────           ─────            ───────             │
│   Test CLI         claude-config/   Prompt enrichi   Reddit/HN           │
│   Task tool        Agents           Sub-agents       RSS +5              │
│                    Logs research    Doc recherche                        │
│                                                                          │
│   ~2h              ~4h              ~8h              ~4h                 │
│                                                                          │
│   ════════════════════════════════════════════════════════════════      │
│                                                                          │
│   Phase 4          Phase 5                                               │
│   INTÉGRATION      OPTIMISATION                                          │
│   ───────────      ────────────                                          │
│   docker-compose   Monitoring                                            │
│   main.py          Fine-tuning                                           │
│   Tests E2E        Documentation                                         │
│                                                                          │
│   ~6h              ~4h                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Validation Technique (2h)

### Objectif
Valider que Claude CLI supporte bien les fonctionnalités nécessaires en mode non-interactif.

### Étapes

#### 0.1 Test WebSearch en mode -p

```bash
# Depuis ton terminal local (pas Docker)
claude -p "Recherche les dernières news AI d'aujourd'hui et liste les 3 plus importantes" \
  --allowedTools "WebSearch" \
  --output-format json
```

**Résultat attendu:** Claude effectue des recherches web et retourne un résultat structuré.

#### 0.2 Test Write tool

```bash
# Créer un fichier temporaire
mkdir -p /tmp/claude-test

claude -p "Écris un fichier /tmp/claude-test/test.md avec le contenu 'Hello World'" \
  --allowedTools "Write" \
  --output-format json

# Vérifier
cat /tmp/claude-test/test.md
```

**Résultat attendu:** Le fichier est créé avec le contenu demandé.

#### 0.3 Test Task tool (sub-agent)

Créer un agent de test minimal:

```bash
mkdir -p ~/.claude/agents

cat > ~/.claude/agents/test-agent.md << 'EOF'
---
name: test-agent
description: Agent de test qui retourne simplement "OK"
tools:
model: haiku
---

Tu es un agent de test. Retourne simplement "TEST OK" suivi de l'input reçu.
EOF
```

Tester:

```bash
claude -p "Utilise le sub-agent test-agent pour vérifier qu'il fonctionne" \
  --allowedTools "Task" \
  --output-format json
```

**Résultat attendu:** Le sub-agent est appelé et retourne une réponse.

#### 0.4 Test combiné

```bash
claude -p "Fais une recherche web sur 'Claude AI news', puis écris un résumé dans /tmp/claude-test/summary.md" \
  --allowedTools "WebSearch,Write" \
  --output-format json
```

**Résultat attendu:** Recherche effectuée ET fichier créé.

### Checklist Phase 0

- [ ] WebSearch fonctionne en mode `-p`
- [ ] Write tool crée des fichiers
- [ ] Task tool appelle les sub-agents
- [ ] Combinaison de tools fonctionne

### Blockers potentiels

| Problème | Solution |
|----------|----------|
| WebSearch ne s'active pas | Vérifier que le prompt encourage explicitement la recherche |
| Write échoue | Vérifier permissions du dossier cible |
| Task tool ignoré | Vérifier que l'agent existe dans ~/.claude/agents/ |

---

## Phase 1: Configuration Claude (4h)

### Objectif
Créer la configuration dédiée pour l'instance Docker.

### Étapes

#### 1.1 Créer la structure

```bash
mkdir -p claude-config/agents
mkdir -p claude-config/docs
mkdir -p logs/research
```

#### 1.2 Créer settings.json

```bash
cat > claude-config/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch",
      "Write(/app/logs/**)",
      "Read(/app/config/**)",
      "Task"
    ],
    "deny": [
      "Bash",
      "Edit"
    ]
  },
  "preferences": {
    "model": "sonnet",
    "verbose": true
  }
}
EOF
```

#### 1.3 Créer CLAUDE.md (instructions agent)

```bash
cat > claude-config/CLAUDE.md << 'EOF'
# AI News Research Agent

Tu es un agent de veille AI/ML intelligent opérant en mode autonome.

## Tes Capacités

| Outil | Usage |
|-------|-------|
| WebSearch | Recherche web - TOUJOURS utiliser (3-5 recherches min) |
| WebFetch | Récupérer le contenu d'une URL spécifique |
| Write | Écrire le document de recherche (OBLIGATOIRE) |
| Task | Déléguer aux sub-agents fact-checker et topic-diver |

## Sub-Agents Disponibles

### fact-checker
**Quand l'utiliser:**
- Source non reconnue (pas Anthropic, OpenAI, Google, Meta, HuggingFace, MIT, arXiv)
- Information qui semble peu crédible ou sensationnaliste
- Contradiction entre plusieurs sources

**Ce qu'il retourne:** `{verified, confidence, sources}`

### topic-diver
**Quand l'utiliser:**
- Annonce majeure d'un grand lab (nouveau modèle, acquisition)
- Tendance émergente importante
- Maximum 1-2 sujets par exécution

**Ce qu'il retourne:** `{background, reactions, implications}`

## Workflow Obligatoire

### Phase 1: Analyse
- Parcours tous les articles fournis
- Identifie les sujets majeurs
- Repère les sources douteuses
- Note les hot topics potentiels

### Phase 2: Recherche Web (OBLIGATOIRE)
- Effectue 3-5 recherches web minimum
- Objectifs: breaking news, validation, enrichissement
- Queries suggérées: "[topic] news today", "[company] announcement", "AI news [date]"

### Phase 3: Sub-Agents (si nécessaire)
- fact-checker: pour sources douteuses ou infos non confirmées
- topic-diver: pour 1-2 sujets majeurs max

### Phase 4: Documentation
- OBLIGATOIRE: Écris le document de recherche
- Chemin: /app/logs/research/{date}_{id}_research.md
- Inclure: articles analysés, recherches effectuées, décisions, confiances

### Phase 5: Rédaction
- Produis le JSON final selon le format demandé
- Respecte les guidelines éditoriales

## Règles Absolues

1. TOUJOURS effectuer des recherches web (minimum 3)
2. TOUJOURS écrire le document de recherche avant la réponse finale
3. NE JAMAIS inclure une news non vérifiée sans le mentionner
4. LIMITER les sub-agents (max 2 fact-checks, max 2 deep-dives)
5. RESPECTER le format de sortie JSON

## Sources Fiables (pas besoin de fact-check)

- Anthropic (anthropic.com)
- OpenAI (openai.com)
- Google AI (ai.google, blog.google)
- Meta AI (ai.meta.com)
- HuggingFace (huggingface.co)
- MIT (mit.edu)
- Stanford (stanford.edu)
- arXiv (arxiv.org)
EOF
```

#### 1.4 Créer les agents

**fact-checker.md:**
```bash
cat > claude-config/agents/fact-checker.md << 'EOF'
---
name: fact-checker
description: Vérifie la véracité d'une information. Utilisé pour sources non reconnues ou infos douteuses.
tools: WebSearch, WebFetch
model: haiku
---

# Fact Checker

Tu vérifies la véracité d'une affirmation.

## Process

1. Recherche la source primaire (blog officiel, communiqué)
2. Cherche une confirmation indépendante
3. Évalue la crédibilité

## Output JSON

```json
{
  "claim": "L'affirmation vérifiée",
  "verified": true|false,
  "confidence": "high|medium|low",
  "primary_source": "URL ou null",
  "secondary_sources": ["URLs"],
  "notes": "Observations"
}
```

## Règles

- Max 3 recherches
- Pas de source primaire → confidence: low
- Source primaire + confirmation → confidence: high
EOF
```

**topic-diver.md:**
```bash
cat > claude-config/agents/topic-diver.md << 'EOF'
---
name: topic-diver
description: Approfondit un sujet majeur. Utilisé pour annonces importantes (max 1-2/run).
tools: WebSearch, WebFetch
model: sonnet
---

# Topic Deep Diver

Tu approfondis un sujet AI/ML important.

## Process

1. Recherche contexte et background
2. Trouve réactions communauté (Twitter, Reddit, HN)
3. Identifie implications
4. Synthétise

## Output JSON

```json
{
  "topic": "Le sujet",
  "background": "Contexte (2-3 phrases)",
  "key_reactions": [
    {"source": "Platform", "summary": "Point clé"}
  ],
  "implications": ["Implication 1", "Implication 2"],
  "related_developments": ["Développement connexe"]
}
```

## Règles

- Max 5 recherches
- Focus 24-48h
- Privilégier experts reconnus
EOF
```

#### 1.5 Déplacer/copier les docs

```bash
# Copier les guides existants dans claude-config/docs/
cp config/editorial-guide.md claude-config/docs/
cp config/rules.md claude-config/docs/selection-rules.md

# Créer le schéma de sortie
cat > claude-config/docs/output-schema.md << 'EOF'
# Output Schema

Le JSON de sortie doit suivre ce format:

```json
{
  "headlines": [
    {
      "title": "Titre de la news",
      "summary": "Résumé 2-3 phrases",
      "url": "URL source",
      "source": "Nom de la source",
      "category": "research|product|business|regulation",
      "confidence": "high|medium",
      "deep_dive": null | { ... }  // Si topic-diver utilisé
    }
  ],
  "metadata": {
    "date": "2024-12-22",
    "articles_analyzed": 24,
    "web_searches": 4,
    "fact_checks": 1,
    "deep_dives": 1,
    "research_doc": "/app/logs/research/2024-12-22_xxx_research.md"
  }
}
```
EOF
```

### Checklist Phase 1

- [ ] Structure claude-config/ créée
- [ ] settings.json configuré
- [ ] CLAUDE.md avec instructions complètes
- [ ] fact-checker.md créé
- [ ] topic-diver.md créé
- [ ] Docs de référence copiés
- [ ] logs/research/ créé

---

## Phase 2: Agent Principal (8h)

### Objectif
Modifier le prompt et tester le comportement agentique.

### Étapes

#### 2.1 Nouveau build_prompt dans main.py

```python
def build_prompt(articles: list[Article], execution_id: str) -> str:
    """Build the enriched prompt for agentic Claude CLI."""

    # Charger les instructions depuis CLAUDE.md (sera dans le volume)
    instructions = load_file("/root/.claude/CLAUDE.md")
    selection_rules = load_file("/root/.claude/docs/selection-rules.md")
    editorial_guide = load_file("/root/.claude/docs/editorial-guide.md")
    output_schema = load_file("/root/.claude/docs/output-schema.md")

    # Formater les articles
    articles_text = "\n---\n".join([
        f"[{i + 1}] {a.title}\n"
        f"Source: {a.source}\n"
        f"URL: {a.url}\n"
        f"Date: {a.pub_date}\n"
        f"Description: {a.description[:500]}"
        for i, a in enumerate(articles)
    ])

    # Générer le chemin du document de recherche
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    research_path = f"/app/logs/research/{timestamp}_{execution_id}_research.md"

    return f"""
{instructions}

=== RÈGLES DE SÉLECTION ===
{selection_rules}

=== GUIDE ÉDITORIAL ===
{editorial_guide}

=== SCHÉMA DE SORTIE ===
{output_schema}

=== ARTICLES À ANALYSER ({len(articles)} articles) ===
{articles_text if articles else "Aucun article fourni par les sources primaires."}

=== PARAMÈTRES D'EXÉCUTION ===
- Execution ID: {execution_id}
- Research Document Path: {research_path}
- Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

=== INSTRUCTIONS FINALES ===

1. Analyse tous les articles ci-dessus
2. Effectue 3-5 recherches web pour compléter/valider (OBLIGATOIRE)
3. Utilise les sub-agents si nécessaire (fact-checker, topic-diver)
4. Écris le document de recherche dans: {research_path}
5. Retourne le JSON final selon le schéma

IMPORTANT:
- Le document de recherche DOIT être écrit AVANT ta réponse finale
- Ta réponse finale doit être UNIQUEMENT le JSON structuré
"""
```

#### 2.2 Modifier call_claude_cli

```python
async def call_claude_cli(prompt: str) -> ClaudeResult:
    """Call Claude Code CLI with agentic capabilities."""

    # Allowed tools for agentic workflow
    allowed_tools = "WebSearch,WebFetch,Write,Task"

    cmd = [
        "claude",
        "-p", prompt,
        "--allowedTools", allowed_tools,
        "--output-format", "stream-json",
        "--verbose"
    ]

    # Increase timeout for agentic workflow (5-10 min expected)
    timeout = 600  # 10 minutes

    # ... rest of the function
```

#### 2.3 Test local

```bash
# Build et run le service en local pour tester
cd claude-service
docker build -t claude-service-test .

# Test avec articles mockés
curl -X POST http://localhost:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Test Article",
        "url": "https://example.com",
        "description": "Test description",
        "pub_date": "2024-12-22",
        "source": "Test Source"
      }
    ],
    "workflow_execution_id": "test-001"
  }'
```

#### 2.4 Vérifier les outputs

```bash
# Vérifier que le document de recherche a été créé
ls -la logs/research/

# Lire le document
cat logs/research/*_research.md
```

### Checklist Phase 2

- [ ] build_prompt modifié avec instructions complètes
- [ ] call_claude_cli modifié avec allowedTools
- [ ] Timeout augmenté (600s)
- [ ] Test local passé
- [ ] Document de recherche généré
- [ ] JSON de sortie valide

---

## Phase 3: Sources Enrichies (4h)

### Objectif
Ajouter Reddit, HN et RSS supplémentaires dans n8n.

### Étapes

#### 3.1 Ajouter les nodes RSS dans n8n

Ouvrir n8n (http://localhost:5678) et ajouter:

| Node | URL |
|------|-----|
| RSS Google AI | https://blog.google/technology/ai/rss/ |
| RSS The Batch | https://www.deeplearning.ai/the-batch/feed/ |
| RSS MIT Tech | https://www.technologyreview.com/topic/artificial-intelligence/feed |
| RSS Papers With Code | https://paperswithcode.com/rss |
| RSS BAIR | https://bair.berkeley.edu/blog/feed.xml |

#### 3.2 Ajouter Reddit via HTTP Request

**Node: HTTP Request - Reddit ML**
```
Method: GET
URL: https://www.reddit.com/r/MachineLearning/hot.json
Query Parameters:
  - limit: 25
Headers:
  - User-Agent: AI-News-Bot/1.0
```

**Node: Code - Transform Reddit**
```javascript
// Transformer le JSON Reddit en format Article
return items[0].json.data.children
  .filter(post => post.data.score > 100)  // Filtrer par score
  .map(post => ({
    json: {
      title: post.data.title,
      url: `https://reddit.com${post.data.permalink}`,
      description: post.data.selftext?.substring(0, 500) || post.data.title,
      pub_date: new Date(post.data.created_utc * 1000).toISOString(),
      source: "Reddit r/MachineLearning"
    }
  }));
```

#### 3.3 Ajouter Hacker News via HTTP Request

**Node: HTTP Request - HN**
```
Method: GET
URL: https://hn.algolia.com/api/v1/search
Query Parameters:
  - query: AI OR "machine learning" OR LLM OR GPT OR Claude
  - tags: story
  - numericFilters: created_at_i>${Math.floor(Date.now()/1000) - 86400}
```

**Node: Code - Transform HN**
```javascript
// Transformer le JSON HN en format Article
return items[0].json.hits
  .filter(hit => hit.points > 50)  // Filtrer par points
  .map(hit => ({
    json: {
      title: hit.title,
      url: hit.url || `https://news.ycombinator.com/item?id=${hit.objectID}`,
      description: hit.title,
      pub_date: hit.created_at,
      source: "Hacker News"
    }
  }));
```

#### 3.4 Mettre à jour le Merge node

Configurer le node Merge pour combiner toutes les sources:
- Mode: Append
- Inputs: Tous les nodes RSS + Reddit + HN

#### 3.5 Ajouter déduplication

**Node: Code - Deduplicate**
```javascript
// Dédupliquer par URL et titre similaire
const seen = new Set();
const unique = [];

for (const item of items) {
  const url = item.json.url;
  const titleKey = item.json.title.toLowerCase().substring(0, 50);

  if (!seen.has(url) && !seen.has(titleKey)) {
    seen.add(url);
    seen.add(titleKey);
    unique.push(item);
  }
}

return unique;
```

### Checklist Phase 3

- [ ] 5 RSS supplémentaires ajoutés
- [ ] Reddit r/MachineLearning intégré
- [ ] Reddit r/LocalLLaMA intégré (optionnel)
- [ ] Hacker News intégré
- [ ] Transformations JSON correctes
- [ ] Merge node configuré
- [ ] Déduplication fonctionnelle
- [ ] Workflow testé end-to-end

---

## Phase 4: Intégration Docker (6h)

### Objectif
Intégrer tous les composants dans l'environnement Docker.

### Étapes

#### 4.1 Modifier docker-compose.yml

```yaml
services:
  n8n:
    # ... existant inchangé

  claude-service:
    build: ./claude-service
    container_name: ai-news-claude
    restart: unless-stopped
    environment:
      - CLAUDE_MODEL=${CLAUDE_MODEL:-sonnet}
      - CLAUDE_TIMEOUT=600  # Augmenté pour workflow agentique
      - CLAUDE_RETRY_COUNT=${CLAUDE_RETRY_COUNT:-1}
      - CLAUDE_LOG_LEVEL=${CLAUDE_LOG_LEVEL:-info}
    volumes:
      # Config Claude dédiée (remplace CLAUDE_HOME)
      - ./claude-config:/root/.claude
      # Logs avec research/
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # Augmenté
    ports:
      - "8080:8080"
```

#### 4.2 Créer logs/research/

```bash
mkdir -p logs/research
touch logs/research/.gitkeep
```

#### 4.3 Mettre à jour .gitignore

```bash
cat >> .gitignore << 'EOF'

# Research documents (generated)
logs/research/*.md
logs/research/*.json
!logs/research/.gitkeep
EOF
```

#### 4.4 Rebuild et test

```bash
# Arrêter les services
docker-compose down

# Rebuild
docker-compose build claude-service

# Relancer
docker-compose up -d

# Vérifier les logs
docker-compose logs -f claude-service
```

#### 4.5 Test end-to-end

```bash
# Déclencher manuellement le workflow n8n
# Ou attendre le prochain trigger

# Vérifier les logs
ls -la logs/
ls -la logs/research/
ls -la logs/workflows/

# Lire le dernier document de recherche
cat $(ls -t logs/research/*.md | head -1)
```

### Checklist Phase 4

- [ ] docker-compose.yml mis à jour
- [ ] Volumes correctement montés
- [ ] logs/research/ créé
- [ ] .gitignore mis à jour
- [ ] Build réussi
- [ ] Service healthy
- [ ] Test end-to-end passé
- [ ] Document de recherche généré dans Docker

---

## Phase 5: Optimisation (4h)

### Objectif
Affiner le système et documenter.

### Étapes

#### 5.1 Monitoring des coûts

Ajouter dans execution_logger.py un tracking des coûts cumulés:

```python
# Dans ExecutionMetrics
class ExecutionMetrics(BaseModel):
    # ... existant
    web_searches_count: int = 0
    fact_checks_count: int = 0
    deep_dives_count: int = 0
```

#### 5.2 Alertes Discord en cas d'erreur

Modifier le workflow n8n pour envoyer une alerte si le workflow échoue:

```javascript
// Dans Error Trigger node
const errorEmbed = {
  title: "⚠️ AI News Bot Error",
  color: 0xFF0000,
  fields: [
    { name: "Error", value: $json.error_message },
    { name: "Node", value: $json.error_node },
    { name: "Time", value: new Date().toISOString() }
  ]
};
```

#### 5.3 Fine-tuning des instructions

Après quelques exécutions, ajuster:
- Nombre de recherches web (3-5 → ajuster selon qualité)
- Seuils de fact-check
- Critères de deep-dive

#### 5.4 Documentation finale

Mettre à jour:
- README.md avec les nouvelles fonctionnalités
- config/sources.md avec toutes les sources
- .claude/CLAUDE.md (dev) avec les infos sur le nouveau système

### Checklist Phase 5

- [ ] Monitoring des coûts implémenté
- [ ] Alertes d'erreur configurées
- [ ] Instructions affinées après tests
- [ ] Documentation mise à jour
- [ ] Workflow stable sur 3+ exécutions

---

## Résumé des Fichiers à Créer/Modifier

### Nouveaux fichiers

| Fichier | Phase |
|---------|-------|
| `claude-config/settings.json` | 1 |
| `claude-config/CLAUDE.md` | 1 |
| `claude-config/agents/fact-checker.md` | 1 |
| `claude-config/agents/topic-diver.md` | 1 |
| `claude-config/docs/output-schema.md` | 1 |
| `logs/research/.gitkeep` | 4 |

### Fichiers à modifier

| Fichier | Phase | Modification |
|---------|-------|--------------|
| `claude-service/main.py` | 2 | build_prompt, call_claude_cli |
| `docker-compose.yml` | 4 | Volumes, timeout |
| `.gitignore` | 4 | logs/research/ |
| Workflow n8n | 3 | Nouvelles sources |

### Fichiers à copier

| Source | Destination | Phase |
|--------|-------------|-------|
| `config/editorial-guide.md` | `claude-config/docs/` | 1 |
| `config/rules.md` | `claude-config/docs/selection-rules.md` | 1 |

---

## Validation Finale

### Tests à effectuer

1. **Test unitaire agents**
   ```bash
   claude -p "Test fact-checker" --allowedTools "Task"
   ```

2. **Test WebSearch**
   ```bash
   claude -p "Recherche AI news" --allowedTools "WebSearch"
   ```

3. **Test Write**
   ```bash
   claude -p "Écris test.md" --allowedTools "Write"
   ```

4. **Test intégration Docker**
   ```bash
   docker-compose up -d
   curl http://localhost:8080/summarize -d '{"articles":[]}'
   ```

5. **Test end-to-end n8n**
   - Déclencher workflow manuellement
   - Vérifier Discord
   - Vérifier logs/research/

### Critères de succès

| Critère | Validation |
|---------|------------|
| Document de recherche créé | `ls logs/research/*.md` |
| JSON valide retourné | Parse sans erreur |
| Temps < 10 min | Vérifier logs |
| Coût < $0.50/run | Vérifier metrics |
| Discord reçoit le message | Vérifier le channel |

---

## Rollback

En cas de problème majeur:

```bash
# Revenir à l'ancienne config
git checkout HEAD~1 -- docker-compose.yml
git checkout HEAD~1 -- claude-service/main.py

# Ou utiliser l'ancien CLAUDE_HOME
# Dans docker-compose.yml:
# - ${CLAUDE_HOME}:/root/.claude  # Au lieu de ./claude-config
```

---

*Document créé le 22 décembre 2025*

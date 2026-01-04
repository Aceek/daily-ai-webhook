# Plan : Architecture Multi-Mission

> **Version:** 1.0
> **Date:** 22 décembre 2025
> **Statut:** En attente de validation

---

## 1. Résumé

Transformer le système de veille en une architecture multi-mission où Claude CLI va chercher lui-même ses instructions selon la mission demandée.

### Avant / Après

```
AVANT                                 APRÈS
─────                                 ─────
main.py build_prompt()                main.py écrit articles.json
         │                                    │
         ▼                                    ▼
Méga-prompt (22k tokens)              Prompt minimal (500 tokens)
- CLAUDE.md                           "Mission: ai-news
- selection-rules.md                   Articles: /app/data/articles.json
- editorial-guide.md                   Exec ID: abc123"
- output-schema.md                            │
- articles                                    ▼
         │                            Claude lit automatiquement CLAUDE.md
         ▼                                    │
Claude exécute                                ▼
                                      Claude Read() les fichiers mission
                                      /app/missions/ai-news/
                                              │
                                              ▼
                                      Claude exécute avec contexte complet
```

---

## 2. Analyse d'impact complète

### 2.1 Fichiers à modifier

| Fichier | Type de modification | Complexité |
|---------|---------------------|------------|
| `claude-service/main.py` | Majeure | Élevée |
| `docker-compose.yml` | Mineure | Faible |
| `claude-config/CLAUDE.md` | Réécriture complète | Moyenne |
| `workflows/daily-news-workflow.json` | Mineure | Faible |
| `claude-service/execution_logger.py` | Mineure | Faible |

### 2.2 Fichiers à créer

| Fichier | Description |
|---------|-------------|
| `missions/ai-news/selection-rules.md` | Règles spécifiques AI news |
| `missions/ai-news/editorial-guide.md` | Guide éditorial AI news |
| `missions/ai-news/output-schema.md` | Schéma de sortie |
| `missions/_common/quality-rules.md` | Règles partagées |
| `missions/_common/mcp-usage.md` | Instructions MCP communes |

### 2.3 Fichiers à supprimer/déplacer

| Fichier actuel | Action |
|----------------|--------|
| `claude-config/docs/selection-rules.md` | Déplacer → `missions/ai-news/` |
| `claude-config/docs/editorial-guide.md` | Déplacer → `missions/ai-news/` |
| `claude-config/docs/output-schema.md` | Déplacer → `missions/ai-news/` |
| `claude-config/docs/research-template.md` | Déplacer → `missions/_common/` |

### 2.4 Dépendances entre modifications

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORDRE D'IMPLÉMENTATION                          │
│                                                                     │
│  ┌─────────────┐                                                    │
│  │   PHASE 1   │  Structure fichiers (pas de code)                  │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 2   │  CLAUDE.md dispatcher                              │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 3   │  docker-compose.yml (volumes)                      │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 4   │  main.py (logique mission)                         │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 5   │  execution_logger.py (champ mission)               │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 6   │  Workflow n8n (payload mission)                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │   PHASE 7   │  Tests et validation                               │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Nouvelle structure de fichiers

```
daily-ai-webhook/
├── docker-compose.yml
├── claude-service/
│   ├── main.py                    # Modifié
│   ├── execution_logger.py        # Modifié (champ mission)
│   └── ...
│
├── claude-config/
│   ├── CLAUDE.md                  # Réécrit → Dispatcher
│   ├── .credentials.json
│   ├── .mcp.json
│   └── agents/                    # Inchangé (génériques)
│       ├── fact-checker.md
│       └── topic-diver.md
│
├── missions/                      # NOUVEAU
│   ├── _common/
│   │   ├── quality-rules.md       # Règles qualité partagées
│   │   ├── mcp-usage.md           # Instructions submit_digest
│   │   └── research-template.md   # Template recherche
│   │
│   └── ai-news/
│       ├── mission.md             # Description mission
│       ├── selection-rules.md     # Règles sélection AI
│       ├── editorial-guide.md     # Guide éditorial AI
│       └── output-schema.md       # Schéma sortie
│
├── mcp-server/                    # Inchangé
│   └── server.py
│
└── logs/
    └── ...
```

---

## 4. Modifications détaillées

### 4.1 PHASE 1 : Structure missions/

**Créer l'arborescence :**
```bash
missions/
├── _common/
│   ├── quality-rules.md
│   ├── mcp-usage.md
│   └── research-template.md
└── ai-news/
    ├── mission.md
    ├── selection-rules.md
    ├── editorial-guide.md
    └── output-schema.md
```

**Fichier `missions/ai-news/mission.md` :**
```markdown
# Mission: AI News Daily Digest

Tu es un agent de veille spécialisé en AI/ML.

## Objectif
Produire un digest quotidien des actualités AI/ML de qualité.

## Sources fiables (pas de fact-check)
- Anthropic, OpenAI, Google DeepMind, Meta AI
- arXiv, HuggingFace, MIT, Stanford, Berkeley

## Workflow
1. Analyser tous les articles dans /app/data/articles.json
2. Effectuer 3-5 recherches web complémentaires
3. Utiliser sub-agents si nécessaire (fact-checker, topic-diver)
4. Écrire le document de recherche
5. Soumettre via submit_digest

## Langue
Digest final en anglais.
```

### 4.2 PHASE 2 : CLAUDE.md Dispatcher

**Nouveau `claude-config/CLAUDE.md` :**
```markdown
# Agent Multi-Mission

Tu es un agent de veille capable d'opérer sur différents domaines.

## Protocole de démarrage OBLIGATOIRE

Chaque exécution te fournit :
- `mission` : Nom de la mission (ex: "ai-news")
- `articles_path` : Chemin vers les données
- `execution_id` : ID unique de l'exécution
- `research_path` : Où écrire le document de recherche

### Étape 1 : Chargement mission (BLOQUANT)

Tu DOIS lire ces fichiers DANS L'ORDRE avant toute analyse.
NE COMMENCE PAS l'analyse avant d'avoir terminé toutes les lectures.

1. `Read(/app/data/articles.json)` - Données à traiter
2. `Read(/app/missions/_common/quality-rules.md)` - Règles qualité
3. `Read(/app/missions/_common/mcp-usage.md)` - Instructions MCP
4. `Read(/app/missions/{mission}/mission.md)` - Description mission
5. `Read(/app/missions/{mission}/selection-rules.md)` - Règles sélection
6. `Read(/app/missions/{mission}/editorial-guide.md)` - Guide éditorial
7. `Read(/app/missions/{mission}/output-schema.md)` - Format sortie

Après lecture, CONFIRME en listant les fichiers lus.

### Étape 2 : Exécution

Suis les instructions de la mission lue.
Utilise les outils disponibles : WebSearch, WebFetch, Write, Task, submit_digest.

### Étape 3 : Finalisation

TOUJOURS utiliser `submit_digest` pour soumettre le résultat.
NE JAMAIS retourner le JSON en texte libre.

## Outils disponibles

| Outil | Usage |
|-------|-------|
| Read | Lire fichiers mission et données |
| WebSearch | Recherche web complémentaire |
| WebFetch | Récupérer contenu URL |
| Write | Écrire document de recherche |
| Task | Déléguer aux sub-agents |
| submit_digest | Soumettre résultat final (MCP) |

## Sub-agents disponibles

- `fact-checker` : Vérifier sources douteuses
- `topic-diver` : Approfondir sujet majeur
```

### 4.3 PHASE 3 : docker-compose.yml

**Modifications :**
```yaml
claude-service:
  volumes:
    # Runtime Claude
    - claude-runtime:/root/.claude

    # Config Claude (dispatcher)
    - ./claude-config/CLAUDE.md:/app/claude-config/CLAUDE.md:ro
    - ./claude-config/agents:/app/claude-config/agents:ro
    - ./claude-config/.credentials.json:/app/claude-config/.credentials.json:ro
    - ./claude-config/.mcp.json:/app/claude-config/.mcp.json:ro
    - ./claude-config/.mcp.json:/app/.mcp.json:ro

    # NOUVEAU: Missions (read-only)
    - ./missions:/app/missions:ro

    # NOUVEAU: Data interchange (read-write)
    - ./data:/app/data

    # MCP server
    - ./mcp-server:/app/mcp-server:ro

    # Logs
    - ./logs:/app/logs
```

**Créer dossier data/ :**
```bash
mkdir -p data
echo "data/" >> .gitignore  # Données temporaires
```

### 4.4 PHASE 4 : main.py

**4.4.1 Nouveau modèle de requête :**
```python
class SummarizeRequest(BaseModel):
    articles: list[Article] = Field(..., min_length=0)
    mission: str = Field(default="ai-news", description="Mission to execute")
    workflow_execution_id: str | None = None

# Missions valides
VALID_MISSIONS = ["ai-news"]  # Extensible
```

**4.4.2 Nouvelle fonction build_prompt() :**
```python
def build_prompt(
    mission: str,
    articles_path: str,
    execution_id: str,
    research_path: str,
    workflow_execution_id: str | None = None,
) -> str:
    """Build minimal prompt for multi-mission architecture."""
    return f"""Mission: {mission}
Articles: {articles_path}
Execution ID: {execution_id}
Research path: {research_path}
Workflow ID: {workflow_execution_id or "standalone"}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Suis le protocole de démarrage de ton CLAUDE.md.
Lis les fichiers de mission dans l'ordre indiqué avant de commencer."""
```

**4.4.3 Écriture des articles :**
```python
def write_articles_file(articles: list[Article], path: Path) -> None:
    """Write articles to JSON file for Claude to read."""
    data = [
        {
            "title": a.title,
            "url": a.url,
            "description": a.description[:500] if a.description else "",
            "pub_date": a.pub_date,
            "source": a.source,
        }
        for a in articles
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

**4.4.4 Validation mission :**
```python
def validate_mission(mission: str) -> tuple[bool, str | None]:
    """Validate that mission exists and has required files."""
    if mission not in VALID_MISSIONS:
        return False, f"Unknown mission: {mission}. Valid: {VALID_MISSIONS}"

    mission_path = Path(f"/app/missions/{mission}")
    required_files = ["mission.md", "selection-rules.md", "editorial-guide.md", "output-schema.md"]

    for f in required_files:
        if not (mission_path / f).exists():
            return False, f"Missing mission file: {mission_path / f}"

    return True, None
```

**4.4.5 Nouveau Settings :**
```python
class Settings(BaseSettings):
    # ... existing ...

    # Nouveau: paths pour architecture multi-mission
    missions_path: str = "/app/missions"
    data_path: str = "/app/data"

    # Outils autorisés (ajout de Read)
    allowed_tools: str = "Read,WebSearch,WebFetch,Write,Task,mcp__submit-digest__submit_digest"
```

**4.4.6 Endpoint /summarize modifié :**
```python
@app.post("/summarize")
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    # Validation mission
    valid, error = validate_mission(request.mission)
    if not valid:
        return SummarizeResponse(success=False, error=error, article_count=0)

    # Générer IDs
    execution_id = uuid.uuid4().hex[:12]
    exec_dir = execution_logger.create_execution_dir(execution_id)

    # Écrire articles dans fichier
    articles_path = Path(settings.data_path) / "articles.json"
    write_articles_file(request.articles, articles_path)

    # Construire prompt minimal
    prompt = build_prompt(
        mission=request.mission,
        articles_path=str(articles_path),
        execution_id=execution_id,
        research_path=str(exec_dir.research_path),
        workflow_execution_id=request.workflow_execution_id,
    )

    # Appeler Claude CLI (inchangé)
    claude_result = await call_claude_cli(prompt, exec_dir)

    # ... reste inchangé ...
```

### 4.5 PHASE 5 : execution_logger.py

**Ajouter champ mission aux logs :**
```python
class ExecutionLog(BaseModel):
    execution_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.now)
    mission: str = "ai-news"  # NOUVEAU
    success: bool = False
    # ... reste inchangé ...

class ExecutionMetrics(BaseModel):
    # ... existing ...
    mission: str = ""  # NOUVEAU
    files_read: list[str] = Field(default_factory=list)  # NOUVEAU - traçabilité
```

**Modifier _format_summary() pour afficher la mission :**
```python
def _format_summary(...) -> str:
    # ...
    md = f"""# Execution {log.execution_id}

**Mission:** {log.mission}  # NOUVEAU
**Status:** {status_emoji} {status}
**Date:** {log.timestamp.strftime("%Y-%m-%d %H:%M")}
# ...
```

### 4.6 PHASE 6 : Workflow n8n

**Modifier node "Prepare Payload" :**
```javascript
// Prepare payload for Claude Service with mission
const articles = $input.all().map(item => item.json);
const initData = $('Init Execution').first().json;

return [{
  json: {
    articles: articles,
    mission: "ai-news",  // NOUVEAU - fixe pour ce workflow
    workflow_execution_id: initData.workflow_execution_id
  }
}];
```

### 4.7 PHASE 7 : Tests et validation

**7.1 Test unitaire validation mission :**
```python
def test_validate_mission_valid():
    valid, error = validate_mission("ai-news")
    assert valid is True
    assert error is None

def test_validate_mission_invalid():
    valid, error = validate_mission("unknown")
    assert valid is False
    assert "Unknown mission" in error
```

**7.2 Test intégration :**
```bash
# Depuis le host
curl -X POST http://localhost:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [{"title": "Test", "url": "https://example.com", "source": "Test"}],
    "mission": "ai-news"
  }'
```

**7.3 Vérification lectures fichiers :**
Après exécution, vérifier dans les logs que Claude a bien lu tous les fichiers requis :
```bash
# Vérifier timeline
cat logs/latest/raw/timeline.json | jq '.[] | select(.event_type == "tool_use") | .raw_data.name'
# Doit contenir plusieurs "Read"
```

---

## 5. Points de vigilance

### 5.1 Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Claude oublie de lire un fichier | Moyenne | Élevé | Instructions explicites + validation post-exec |
| Latence accrue (+ Read calls) | Certaine | Faible | Acceptable (~2-3s) |
| Fichier articles.json non trouvé | Faible | Élevé | Validation existence avant appel CLI |
| Chemins incorrects dans container | Moyenne | Élevé | Tests d'intégration |

### 5.2 Compatibilité arrière

**Non garantie.** L'ancien format de requête (sans `mission`) utilisera la valeur par défaut `"ai-news"`.

**Migration n8n requise :** Le workflow doit être mis à jour pour envoyer le champ `mission`.

### 5.3 Allowed tools

**CRITIQUE :** Ajouter `Read` aux outils autorisés.

Actuel :
```python
allowed_tools: str = "WebSearch,WebFetch,Write,Task,mcp__submit-digest__submit_digest"
```

Nouveau :
```python
allowed_tools: str = "Read,WebSearch,WebFetch,Write,Task,mcp__submit-digest__submit_digest"
```

---

## 6. Rollback

En cas de problème, rollback simple :

1. Restaurer `claude-config/docs/` (depuis git)
2. Restaurer `main.py` (depuis git)
3. Restaurer `docker-compose.yml` (depuis git)
4. Supprimer `missions/` et `data/`

---

## 7. Checklist pré-implémentation

- [ ] Créer branche `feature/multi-mission`
- [ ] Backup configuration actuelle
- [ ] Vérifier que les tests existants passent
- [ ] Préparer environnement de test

---

## 8. Estimation effort

| Phase | Durée estimée | Fichiers |
|-------|---------------|----------|
| Phase 1 - Structure | ~15 min | 6 fichiers markdown |
| Phase 2 - CLAUDE.md | ~20 min | 1 fichier |
| Phase 3 - docker-compose | ~5 min | 1 fichier |
| Phase 4 - main.py | ~30 min | 1 fichier |
| Phase 5 - logger | ~10 min | 1 fichier |
| Phase 6 - n8n | ~5 min | 1 fichier |
| Phase 7 - Tests | ~20 min | validation manuelle |
| **Total** | **~1h45** | **11 fichiers** |

---

## 9. Validation requise

Avant implémentation, confirmer :

1. ✅ Structure `missions/` correcte ?
2. ✅ CLAUDE.md dispatcher suffisamment explicite ?
3. ✅ Ajout de `Read` aux allowed tools ?
4. ✅ Champ `mission` dans requête API ?
5. ✅ Écriture articles dans `/app/data/` ?

---

*Plan créé le 22 décembre 2025*

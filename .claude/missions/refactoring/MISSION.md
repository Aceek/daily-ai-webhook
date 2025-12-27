# Mission: Codebase Refactoring

## Meta

- **Objectif**: Refactorer la codebase pour atteindre un niveau professionnel
- **Format docs**: Optimisé AI (compact, dense, pas de verbosité)
- **Langue commits**: Anglais, conventional commits, JAMAIS mentionner "Claude Code"

---

## 1. Standards Obligatoires

### 1.1 Clean Code

| Règle | Critère |
|-------|---------|
| Fichiers | Max 200-300 lignes (sauf exceptions justifiées) |
| Fonctions | Max 30 lignes, une seule responsabilité |
| Noms | Explicites, pas d'abbréviations obscures |
| Comments | Seulement si logique non-évidente |

### 1.2 SoC (Separation of Concerns)

```
SERVICE/
├── models/          # Pydantic models (request/response/domain)
├── services/        # Business logic
├── repositories/    # Data access (DB queries)
├── api/             # Routes/endpoints seulement
├── utils/           # Helpers purs (sans état)
└── config.py        # Configuration centralisée
```

**Règles strictes:**
- Un fichier = une responsabilité
- Pas de logique métier dans les routes
- Pas de SQL dans les services (repository pattern)
- Pas de models dans les fichiers d'API

### 1.3 DRY (Don't Repeat Yourself)

- Identifier patterns répétés → extraire en fonction/classe
- Si code copié 2x → refactorer immédiatement
- Utiliser héritage/composition pour variations mineures

### 1.4 Sécurité

| Aspect | Exigence |
|--------|----------|
| SQL | Queries paramétrées UNIQUEMENT |
| Secrets | Env vars, jamais hardcodés |
| Input | Validation Pydantic sur toutes les entrées |
| Errors | Ne pas exposer stack traces en prod |

### 1.5 Qualité Code Python

- Type hints sur TOUTES les fonctions
- Docstrings sur fonctions publiques (format Google)
- Imports organisés: stdlib → third-party → local
- Pas de `# type: ignore` sans justification
- Async/await cohérent (pas de mixing sync/async)

---

## 2. Workflow de Mission

### 2.1 Architecture Agents

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                           │
│                   (Chat Principal)                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ ANALYZER      │   │ ANALYZER      │   │ ANALYZER      │
│ claude-service│   │ bot           │   │ mcp-server    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│              analysis/*.md (plans correctifs)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    IMPLEMENTER                              │
│            (Implémente les correctifs)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     VERIFIER                                │
│              (Validation finale)                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Phase 1: Analyse Parallèle

**Lancer 3 subagents EN PARALLÈLE** (Task tool, un seul message):

> ⚠️ **IMPORTANT**: Utiliser `subagent_type="general-purpose"` (PAS `Explore`)
> Les agents doivent ÉCRIRE leurs rapports dans les fichiers output.

#### Agent 1: claude-service
```
Scope: /claude-service/
Fichiers critiques: main.py (1171L), execution_logger.py (753L)
Output: .claude/missions/refactoring/analysis/claude-service.md
```

#### Agent 2: bot
```
Scope: /bot/
Fichiers critiques: services/card_generator.py, services/embed_builder.py
Output: .claude/missions/refactoring/analysis/bot.md
```

#### Agent 3: mcp-server
```
Scope: /claude-service/mcp/
Fichiers critiques: server.py (968L)
Output: .claude/missions/refactoring/analysis/mcp-server.md
```

**Prompt template pour analyzers:**
```
MISSION: Analyse refactoring pour [SERVICE]
LIRE: .claude/missions/refactoring/MISSION.md (section 1 - Standards)
SCOPE: [PATHS]

TÂCHES:
1. Lire tous les fichiers du scope
2. Identifier violations des standards (section 1)
3. Proposer plan de refactoring

OUTPUT FORMAT (écrire dans [OUTPUT_PATH]):
---
# Analysis: [SERVICE]

## Violations Identifiées
[Liste: fichier:ligne - violation - sévérité (HIGH/MED/LOW)]

## Plan de Refactoring
### Phase 1: [titre]
- [ ] Action 1 (fichier concerné)
- [ ] Action 2
[...]

### Phase 2: [titre]
[...]

## Nouvelle Structure Proposée
[Arborescence cible]

## Dépendances
[Ordre d'exécution si dépendances entre actions]
---

CONTRAINTES:
- Format compact (optimisé tokens)
- Prioriser par impact
- Inclure TOUS les fichiers du scope
```

### 2.3 Phase 2: Implémentation

**Après réception des 3 analyses**, lancer agent IMPLEMENTER:

```
MISSION: Implémenter refactoring
LIRE:
- .claude/missions/refactoring/MISSION.md
- .claude/missions/refactoring/analysis/claude-service.md
- .claude/missions/refactoring/analysis/bot.md
- .claude/missions/refactoring/analysis/mcp-server.md

WORKFLOW:
1. Consolider les 3 plans en ordre d'exécution
2. Implémenter action par action
3. Après chaque groupe logique de changements:
   - Vérifier que le code fonctionne (imports, syntax)
   - Commit avec message conventionnel
4. Documenter progrès dans roadmap.md

COMMITS:
- Format: type(scope): description
- Types: refactor, feat, fix, chore
- Scope: claude-service, bot, mcp
- NO mention of "Claude Code" or AI
- English only

EXEMPLE:
refactor(claude-service): extract models to dedicated module
refactor(bot): consolidate embed formatters into single function
```

### 2.4 Phase 3: Vérification

**Après implémentation**, lancer agent VERIFIER:

```
MISSION: Vérification post-refactoring
LIRE: .claude/missions/refactoring/MISSION.md (section 1)

TÂCHES:
1. Scanner tous les fichiers Python
2. Vérifier conformité aux standards
3. Identifier violations restantes
4. Générer rapport final

OUTPUT: .claude/missions/refactoring/VERIFICATION.md

FORMAT:
---
# Verification Report

## Conformité Standards
| Standard | Status | Notes |
|----------|--------|-------|
| File size | ✅/⚠️/❌ | |
| SoC | ✅/⚠️/❌ | |
| DRY | ✅/⚠️/❌ | |
| Security | ✅/⚠️/❌ | |
| Types | ✅/⚠️/❌ | |

## Issues Restantes
[Liste si applicable]

## Verdict
[PASS/PARTIAL/FAIL]
---
```

---

## 3. Instructions Orchestrator

### Démarrage

```
1. Lire ce document entièrement
2. Lire .claude/CLAUDE.md pour contexte projet
3. Créer roadmap.md avec template vide
4. Lancer Phase 1 (3 analyzers EN PARALLÈLE - un seul message Task)
5. Attendre complétion des 3 analyses
6. Mettre à jour roadmap.md
7. Lancer Phase 2 (implementer)
8. Mettre à jour roadmap.md
9. Lancer Phase 3 (verifier)
10. Finaliser roadmap.md
```

### Gestion Roadmap

Après chaque phase, ajouter dans `roadmap.md`:
```markdown
## Phase N: [Nom] - [STATUS]
- Started: [timestamp]
- Completed: [timestamp]
- Actions: [count]
- Commits: [list]
- Issues: [if any]
```

### Gestion Erreurs

- Si analyzer échoue → relancer avec scope réduit
- Si implementer bloqué → demander clarification user
- Si tests cassés → rollback + fix avant continuer

---

## 4. Contraintes Documents

**TOUS les documents générés doivent:**
- Être compacts (optimisés pour AI, pas humains)
- Utiliser tables/listes plutôt que prose
- Aucune perte d'information
- Pas de répétition
- Markdown valide
- Encodage UTF-8

---

## 5. Services à Analyser

| Service | Path | Fichiers Critiques | Lignes |
|---------|------|-------------------|--------|
| claude-service | `/claude-service/` | main.py, execution_logger.py | ~2000 |
| bot | `/bot/` | services/*.py, cogs/*.py | ~1800 |
| mcp-server | `/claude-service/mcp/` | server.py | ~970 |

---

## 6. Checklist Finale

- [ ] Aucun fichier > 300 lignes
- [ ] SoC respecté (models/services/repos/api séparés)
- [ ] DRY (pas de code dupliqué)
- [ ] Types hints partout
- [ ] Imports organisés
- [ ] Commits conventionnels
- [ ] roadmap.md complète
- [ ] VERIFICATION.md généré

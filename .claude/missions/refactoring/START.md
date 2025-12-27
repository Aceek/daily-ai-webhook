# Quick Start - Refactoring Mission

## Pour démarrer la mission

Ouvrir un nouveau chat Claude et envoyer:

```
Lis et exécute la mission de refactoring:
- .claude/missions/refactoring/MISSION.md
- .claude/CLAUDE.md (contexte projet)

Tu es l'ORCHESTRATOR. Suis le workflow décrit section 2.
Lance les 3 analyzers EN PARALLÈLE (un seul message avec 3 Task tools).
```

---

## Workflow Automatique

L'orchestrator va:

1. **Phase 1** - Lancer 3 agents analyzers en parallèle:
   - `claude-service` → analysis/claude-service.md
   - `bot` → analysis/bot.md
   - `mcp-server` → analysis/mcp-server.md

2. **Phase 2** - Lancer agent implementer:
   - Lit les 3 analyses
   - Implémente les correctifs
   - Commit au fur et à mesure

3. **Phase 3** - Lancer agent verifier:
   - Vérifie conformité standards
   - Génère VERIFICATION.md

4. **Tout au long** - Met à jour roadmap.md

---

## En cas de problème

- **Agent bloqué**: L'orchestrator demandera clarification
- **Erreur syntax**: Rollback automatique + fix
- **Besoin intervention**: Répondre à la question de l'orchestrator

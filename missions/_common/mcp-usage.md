# MCP Usage - submit_digest

## Outil obligatoire

Tu DOIS utiliser l'outil `submit_digest` pour soumettre le résultat final.
NE JAMAIS retourner le JSON en texte libre.

## Paramètres

```
submit_digest(
    execution_id: str,      # ID fourni dans les paramètres d'exécution
    headlines: list[dict],  # News majeures (au moins 1 requis)
    research: list[dict],   # Papers/recherches (peut être vide)
    industry: list[dict],   # Business/produits (peut être vide)
    watching: list[dict],   # Tendances à suivre (peut être vide)
    metadata: dict          # Métriques d'exécution
)
```

## Format des news items

Chaque item dans headlines/research/industry/watching :

```json
{
    "title": "Titre concis (max 100 chars)",
    "summary": "Résumé factuel 2-3 phrases (max 300 chars)",
    "url": "https://source-primaire.com/article",
    "source": "Nom de la source",
    "category": "headlines|research|industry|watching",
    "confidence": "high|medium",
    "deep_dive": null
}
```

## Format metadata

```json
{
    "articles_analyzed": 24,
    "web_searches": 4,
    "fact_checks": 1,
    "deep_dives": 1,
    "research_doc": "/chemin/vers/research.md",
    "total_news_included": 6,
    "total_news_excluded": 4
}
```

## Workflow

1. Effectue toute ton analyse
2. Écris le document de recherche (Write)
3. Appelle submit_digest UNE SEULE FOIS avec le digest complet
4. Le système récupère automatiquement le résultat

## Erreurs courantes

- Oublier un champ requis dans les items
- Ne pas appeler submit_digest (le workflow échoue)
- Appeler submit_digest plusieurs fois (seul le dernier compte)
- Mettre confidence: "low" (interdit, exclure plutôt)

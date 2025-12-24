# Weekly Analysis Rules

## Identification des tendances

### Qu'est-ce qu'une tendance?

Une tendance est un pattern récurrent observé sur plusieurs articles/jours de la semaine.

### Critères de sélection

| Critère | Seuil minimum |
|---------|---------------|
| Articles liés | 3+ articles sur le sujet |
| Sources distinctes | 2+ sources différentes |
| Jours couverts | 2+ jours de la semaine |

### Types de tendances

| Type | Exemple | Direction typique |
|------|---------|-------------------|
| Lancement | Nouveau modèle, produit | `rising` |
| Adoption | Framework gagne en popularité | `rising` |
| Débat | Controverse AI safety | `stable` |
| Déclin | Tech remplacée | `declining` |
| Régulation | Nouvelle loi votée | `rising` ou `stable` |

### Format tendance

```json
{
  "name": "Open-source AI momentum",
  "description": "Major labs releasing more open-weight models, with Meta, Mistral, and now Google contributing",
  "evidence": [
    "Meta releases Llama 3.1 405B",
    "Google open-sources Gemma 2",
    "Mistral Large 2 released"
  ],
  "direction": "rising"
}
```

### Règles de rédaction

- **name**: Court, accrocheur, 3-6 mots
- **description**: 1-2 phrases, factuel, avec exemples concrets
- **evidence**: 2-5 articles/faits supportant la tendance
- **direction**: Basé sur comparaison avec semaines précédentes si possible

---

## Sélection des Top Stories

### Critères de priorité

1. **Impact majeur** - Affecte l'industrie entière
2. **Source officielle** - Annonce directe d'un lab/entreprise
3. **Nouveauté** - Premier du genre, breakthrough
4. **Adoption large** - Millions d'utilisateurs affectés
5. **Régulation** - Loi/règlement ayant force légale

### Hiérarchie des sources

| Priorité | Source type | Exemples |
|----------|-------------|----------|
| 1 | Annonces officielles | Blog Anthropic, OpenAI News |
| 2 | Papers avec résultats | arXiv avec benchmarks |
| 3 | Régulateurs | EU, US Gov, UK AI Safety |
| 4 | Journalisme tech | TechCrunch, The Verge |
| 5 | Communauté | Reddit, HN avec >500 pts |

### Format top story

```json
{
  "title": "OpenAI releases GPT-5 with 1M context window",
  "summary": "OpenAI announced GPT-5, featuring a 1 million token context window and improved reasoning capabilities. The model shows 40% improvement on MMLU benchmark.",
  "url": "https://openai.com/blog/gpt-5",
  "impact": "Sets new standard for context length in commercial LLMs, enabling full codebase and document analysis"
}
```

### Règles de rédaction

- **title**: Factuel, max 80 chars, pas de sensationalisme
- **summary**: 2-3 phrases, chiffres clés si disponibles
- **url**: Source primaire obligatoire
- **impact**: Pourquoi cette news compte, implications futures

---

## Analyse par catégorie

### Structure attendue

```json
{
  "headlines": {
    "count": 12,
    "summary": "Major announcements dominated by OpenAI's GPT-5 release and EU AI Act implementation timeline"
  },
  "research": {
    "count": 8,
    "summary": "Focus on efficiency: multiple papers on smaller, faster models matching larger ones"
  },
  "industry": {
    "count": 15,
    "summary": "Funding continues strong with 3 unicorn rounds; Microsoft and Google expanding enterprise AI"
  },
  "watching": {
    "count": 5,
    "summary": "Growing attention to AI agents and autonomous systems; safety concerns rising"
  }
}
```

### Règles

- Résumé par catégorie: 1-2 phrases max
- Mentionner les faits saillants
- Inclure le count pour chaque catégorie

---

## Résumé exécutif (summary)

### Structure recommandée

1. **Opening**: Phrase d'accroche sur l'événement majeur de la semaine
2. **Key developments**: 2-3 faits marquants
3. **Trends**: Mention des tendances principales
4. **Looking ahead**: Ce qui est à surveiller

### Exemple

```
This week was marked by OpenAI's surprise release of GPT-5, setting a new benchmark for context length in commercial LLMs.

Key developments included Google's response with Gemini 2.0 announcement, the EU finalizing AI Act implementation dates for August 2025, and a record $2.3B funding round for Anthropic.

The open-source momentum continues with three major model releases, while enterprise AI adoption accelerates across Fortune 500 companies.

Looking ahead, all eyes are on the upcoming AI Safety Summit and potential US executive orders on AI regulation.
```

### Règles

- 2-3 paragraphes max
- Factuel, pas d'opinions
- Mentionner chiffres et dates concrètes
- Longueur: 150-300 mots

---

## Métriques de qualité

| Métrique | Minimum | Recommandé |
|----------|---------|------------|
| Tendances | 2 | 3-5 |
| Top Stories | 3 | 4-5 |
| Catégories analysées | 2 | Toutes actives |
| Longueur summary | 100 mots | 150-250 mots |
| Sources distinctes | 5 | 10+ |

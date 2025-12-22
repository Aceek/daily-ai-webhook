# Selection Rules - AI News

## Priorité haute (toujours inclure)

- Annonces officielles des grands labs (Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral)
- Nouveaux modèles (GPT-x, Claude, Gemini, Llama, etc.)
- Papers de recherche significatifs (nouvelles architectures, benchmarks)
- Régulations AI (EU AI Act, décisions gouvernementales)
- Acquisitions et funding >$100M

## Priorité moyenne (inclure si pertinent)

- Tutoriels techniques populaires (>500 upvotes Reddit)
- Nouvelles fonctionnalités d'outils existants
- Interviews de chercheurs/leaders
- Analyses de tendances de sources réputées

## Priorité basse (inclure si espace disponible)

- Projets open source intéressants
- Discussions communautaires notables
- Événements et conférences à venir

## Exclure systématiquement

- Contenu promotionnel sans substance
- Rumeurs non sourcées
- Clickbait sans information concrète
- Doublons (même news, sources différentes)
- Articles de plus de 48h (sauf événement majeur en cours)

## Déclencheurs de recherche web

Effectuer une recherche web additionnelle si :
- Moins de 5 articles pertinents après filtrage initial
- Une annonce majeure manque de détails
- Besoin de contexte sur une news importante
- Rumeur à vérifier/confirmer

## Déclencheurs de fact-check

Utiliser le sub-agent fact-checker si :
- Source non reconnue (pas dans la liste des sources fiables)
- Information qui semble sensationnaliste
- Contradiction entre plusieurs sources
- Chiffres ou dates inhabituels

## Déclencheurs de deep-dive

Utiliser le sub-agent topic-diver si :
- Annonce majeure d'un grand lab (nouveau modèle flagship)
- Acquisition >$500M
- Régulation significative
- Maximum 1-2 deep-dives par exécution

# Architecture Technique

## Flux d'Exécution

```
[Cron 8h] → n8n
              │
              ▼
        ┌──────────────────┐
        │ Collecte Données │
        │ • RSS Feeds (x6) │
        │ • Reddit API     │
        │ • HN API         │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Preprocessing    │
        │ • Merge          │
        │ • Dedup (URL)    │
        │ • Filter 24h     │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Claude Code CLI  │
        │ Input:           │
        │  • articles.json │
        │  • config/*.md   │
        │ Output:          │
        │  • résumé.txt    │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Discord Webhook  │
        │ • Embed formaté  │
        └──────────────────┘
```

## Composants n8n

| Node | Type | Rôle |
|------|------|------|
| Cron Trigger | Trigger | Déclenchement 8h |
| RSS Feed x6 | Input | Sources RSS |
| HTTP Request | Input | Reddit/HN APIs |
| Merge | Transform | Combine sources |
| Code | Transform | Dedup + filter |
| Execute Command | Action | Appel Claude CLI |
| HTTP Request | Action | Discord webhook |

## Script Claude CLI

```bash
#!/bin/bash
set -euo pipefail

claude -p "
$(cat config/rules.md)
$(cat config/editorial-guide.md)

=== ARTICLES ===
$(cat "$1")

Génère le résumé selon les règles.
"
```

## Environnement Docker

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    volumes:
      - ./config:/config:ro
      - ./scripts:/scripts:ro
    environment:
      - GENERIC_TIMEZONE=Europe/Paris
```

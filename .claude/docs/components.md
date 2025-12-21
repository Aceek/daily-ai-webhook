# Référence des Composants

## config/ (Production)

| Fichier | Rôle | Utilisé par |
|---------|------|-------------|
| `rules.md` | Critères sélection news | Claude CLI |
| `sources.md` | Liste feeds/APIs | n8n nodes |
| `editorial-guide.md` | Format et ton du résumé | Claude CLI |

## scripts/

| Script | Rôle | Appelé par |
|--------|------|------------|
| `summarize.sh` | Wrapper Claude CLI | n8n Execute Command |

## bot/ (Phase 2)

| Fichier | Rôle |
|---------|------|
| `bot.py` | Bot Discord principal |
| `requirements.txt` | Dépendances Python |
| `Dockerfile` | Container bot |

## Variables Environnement

| Variable | Description | Requis |
|----------|-------------|--------|
| `DISCORD_WEBHOOK_URL` | URL webhook Discord | Oui |
| `N8N_USER` | Auth n8n | Oui |
| `N8N_PASSWORD` | Auth n8n | Oui |
| `REDDIT_CLIENT_ID` | OAuth Reddit | Phase 2 |
| `REDDIT_SECRET` | OAuth Reddit | Phase 2 |

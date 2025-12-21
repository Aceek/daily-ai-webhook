# daily-ai-webhook

Automated daily AI/ML news digest delivered to Discord via n8n and Claude Code.

## Overview

This project automatically:
1. Collects AI/ML news from RSS feeds, Reddit, and Hacker News
2. Analyzes and filters content using Claude Code
3. Generates a curated daily summary
4. Posts to Discord

## Quick Start

```bash
# Clone the repo
git clone git@github.com:Aceek/daily-ai-webhook.git
cd daily-ai-webhook

# Copy environment file
cp .env.example .env

# Start n8n
docker-compose up -d

# Access n8n at http://localhost:5678
```

## Documentation

See [docs/VISION.md](docs/VISION.md) for the complete project vision and architecture.

## Stack

- **n8n** - Workflow orchestration
- **Claude Code** - AI-powered content analysis and summarization
- **Discord Webhook** - Message delivery

## License

MIT

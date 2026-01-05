# API Reference

## claude-service (port 8080)

### POST /summarize

Daily digest generation.

```json
// Request
{
  "mission": "ai-news",
  "articles": [
    {"title": "...", "url": "...", "description": "...", "pubDate": "ISO", "source": "..."}
  ],
  "execution_id": "optional-uuid"
}

// Response
{
  "success": true,
  "digest_id": 123,
  "digest": {
    "headlines": [...],
    "research": [...],
    "industry": [...],
    "watching": [...],
    "excluded": [...],
    "metadata": {...}
  },
  "log_file": "/logs/2024-12-20/..."
}
```

### POST /analyze-weekly

Weekly digest generation.

```json
// Request
{
  "mission": "ai-news",
  "week_start": "2024-12-16",
  "week_end": "2024-12-22",
  "theme": "optional: openai"
}

// Response
{
  "success": true,
  "digest_id": 456,
  "digest": {
    "summary": "...",
    "trends": [...],
    "top_stories": [...],
    "category_analysis": {...},
    "metadata": {...}
  }
}
```

### POST /check-urls

URL deduplication check.

```json
// Request
{"urls": ["https://...", "https://..."]}

// Response
{"duplicates": ["https://already-exists.com"], "new": ["https://new-url.com"]}
```

### POST /log-workflow

Log n8n execution.

```json
// Request
{
  "workflow_id": "...",
  "execution_id": "...",
  "nodes_executed": [...],
  "duration_ms": 5000,
  "success": true
}
```

---

## discord-bot (port 8000)

### POST /publish

Publish digest to Discord.

```json
// Request
{
  "type": "daily",
  "digest_id": 123,
  "content": {...},
  "date": "2024-12-20",
  "channel_id": 123456789  // optional
}

// Response
{"success": true, "message_id": "..."}
```

### GET /health

```json
{"status": "ok", "discord_connected": true, "guilds": 1}
```

---

## MCP Tools

### Query Tools

| Tool | Args | Returns |
|------|------|---------|
| `get_categories` | `mission_id`, `date_from?`, `date_to?` | `{categories: [{id, name}]}` |
| `get_articles` | `mission_id`, `categories?`, `date_from?`, `date_to?`, `limit=100` | `{articles: [{id, title, url, source, category}]}` |
| `get_article_stats` | `mission_id`, `date_from`, `date_to` | `{total, by_category, by_source, by_day}` |
| `get_recent_headlines` | `mission_id`, `days=3` | `{headlines: [{title, url, date}]}` |

### Submission Tools

| Tool | Args | Effect |
|------|------|--------|
| `submit_digest` | `execution_id`, `headlines`, `research`, `industry`, `watching`, `excluded`, `metadata` | INSERT daily_digest + articles |
| `submit_weekly_digest` | `execution_id`, `mission_id`, `week_start`, `week_end`, `summary`, `trends`, `top_stories`, `category_analysis`, `metadata` | INSERT weekly_digest |

### submit_digest Structure

```json
{
  "execution_id": "abc123",
  "headlines": [
    {
      "emoji": "🚀",
      "title": "...",
      "url": "https://...",
      "source": "TechCrunch",
      "summary": "2-3 phrases",
      "confidence": "high|medium",
      "importance": "breaking|major|standard",
      "category": "Models"
    }
  ],
  "research": [...],
  "industry": [...],
  "watching": [...],
  "excluded": [
    {
      "title": "...",
      "url": "...",
      "reason": "off_topic|duplicate|low_priority|outdated",
      "score": 3
    }
  ],
  "metadata": {
    "articles_analyzed": 50,
    "mission_id": "ai-news"
  }
}
```

### submit_weekly_digest Structure

```json
{
  "execution_id": "abc123",
  "mission_id": "ai-news",
  "week_start": "2024-12-16",
  "week_end": "2024-12-22",
  "summary": "Paragraphe synthèse",
  "trends": [
    {"name": "...", "description": "...", "evidence": [...], "direction": "rising|stable|declining"}
  ],
  "top_stories": [
    {"title": "...", "summary": "...", "url": "...", "impact": "...", "emoji": "🚀"}
  ],
  "category_analysis": {
    "headlines": {"count": 5, "summary": "..."}
  },
  "metadata": {
    "articles_analyzed": 150,
    "theme": null
  },
  "is_standard": true
}
```

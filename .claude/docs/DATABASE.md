# Database

PostgreSQL 16, port 5433.

## Schema

```sql
-- Core entities
missions (
  id VARCHAR(50) PK,
  name VARCHAR(100),
  description TEXT,
  created_at TIMESTAMP
)

categories (
  id SERIAL PK,
  mission_id VARCHAR(50) FK → missions,
  name VARCHAR(100),
  created_at TIMESTAMP,
  UNIQUE(mission_id, name)
)

articles (
  id SERIAL PK,
  mission_id VARCHAR(50) FK → missions,
  category_id INT FK → categories,
  daily_digest_id INT FK → daily_digests,
  title VARCHAR(500),
  url VARCHAR(2000) UNIQUE,
  source VARCHAR(100),
  description TEXT,
  pub_date TIMESTAMP,
  created_at TIMESTAMP,
  -- Analysis fields
  status VARCHAR(20) DEFAULT 'raw',      -- raw|selected|excluded
  exclusion_reason VARCHAR(50),          -- off_topic|duplicate|low_priority|outdated
  relevance_score INT                    -- 1-10
)

daily_digests (
  id SERIAL PK,
  mission_id VARCHAR(50) FK → missions,
  date DATE,
  content JSONB,
  generated_at TIMESTAMP,
  posted_to_discord BOOLEAN DEFAULT false,
  UNIQUE(mission_id, date)
)

weekly_digests (
  id SERIAL PK,
  mission_id VARCHAR(50) FK → missions,
  week_start DATE,
  week_end DATE,
  params JSONB,
  content JSONB,
  generated_at TIMESTAMP,
  is_standard BOOLEAN DEFAULT true,
  posted_to_discord BOOLEAN DEFAULT false
)
```

## Indexes

```sql
CREATE INDEX idx_articles_mission_created ON articles(mission_id, created_at);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_exclusion ON articles(exclusion_reason);
CREATE INDEX idx_daily_mission_date ON daily_digests(mission_id, date);
CREATE INDEX idx_weekly_mission_start ON weekly_digests(mission_id, week_start);
```

## Constraints

```sql
-- Article status
CHECK (status IN ('raw', 'selected', 'excluded'))
CHECK (exclusion_reason IS NULL OR exclusion_reason IN ('off_topic', 'duplicate', 'low_priority', 'outdated'))
CHECK (relevance_score IS NULL OR (relevance_score >= 1 AND relevance_score <= 10))
```

## Queries courantes

### Dernier daily digest

```sql
SELECT * FROM daily_digests
WHERE mission_id = 'ai-news'
ORDER BY date DESC LIMIT 1;
```

### Articles de la semaine

```sql
SELECT a.*, c.name as category_name
FROM articles a
JOIN categories c ON a.category_id = c.id
WHERE a.mission_id = 'ai-news'
  AND a.created_at BETWEEN '2024-12-16' AND '2024-12-22'
  AND a.status = 'selected';
```

### Stats par catégorie

```sql
SELECT c.name, COUNT(*) as count
FROM articles a
JOIN categories c ON a.category_id = c.id
WHERE a.mission_id = 'ai-news'
  AND a.created_at > NOW() - INTERVAL '7 days'
GROUP BY c.name
ORDER BY count DESC;
```

### URL dedup check

```sql
SELECT url FROM articles
WHERE url = ANY($1::text[]);
```

## Migrations

| File | Description |
|------|-------------|
| `001_add_article_status.sql` | Ajoute status, exclusion_reason, relevance_score |

## Connexion

```python
# Async (claude-service)
DATABASE_URL = "postgresql+asyncpg://ainews:pass@postgres:5432/ainews"

# Sync (MCP tools)
DATABASE_URL = "postgresql://ainews:pass@postgres:5432/ainews"
```

## Seed data

```sql
-- Mission initiale
INSERT INTO missions (id, name, description)
VALUES ('ai-news', 'AI News', 'Daily AI/ML news aggregation');
```

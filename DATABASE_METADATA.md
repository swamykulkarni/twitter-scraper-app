# Database Schema & Metadata Documentation

## Overview
PostgreSQL database for Social Listening Platform with 4 core tables optimized for AI/ML workloads.

---

## Table Relationships

```
┌─────────────┐
│  schedules  │
└─────────────┘
      │
      │ (triggers)
      ▼
┌─────────────┐       ┌──────────────────┐
│   reports   │◄──────│  deep_history    │
└─────────────┘  1:1  └──────────────────┘
      │                        │
      │                        │
      ▼                        ▼
┌──────────────────┐    (stores all data
│ historical_tweets│     for AI/ML)
└──────────────────┘
```

---

## Table: `schedules`

### Purpose
Stores scheduled scraping jobs with cron-like functionality.

### Columns

| Column | Type | Constraints | Description | Business Logic |
|--------|------|-------------|-------------|----------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique schedule identifier | System-generated |
| username | VARCHAR | NOT NULL | Twitter username to scrape | No @ symbol |
| keywords | JSON | NULL | Array of filter keywords | `["AI", "ML"]` |
| frequency | VARCHAR | NOT NULL | Schedule frequency | `once`, `hourly`, `daily`, `weekly` |
| start_datetime | DATETIME | NOT NULL | Start time (UTC) | Must be future time |
| day | VARCHAR | NULL | Day for weekly schedules | `monday` - `sunday` |
| enabled | BOOLEAN | DEFAULT TRUE | Active status | Can be disabled without deletion |
| last_run | DATETIME | NULL | Last execution timestamp | Updated after each run |
| next_run | DATETIME | NULL | Calculated next run time | Auto-calculated by scheduler |
| created_at | DATETIME | DEFAULT NOW() | Creation timestamp | Immutable |

### Indexes
- PRIMARY KEY: `id`
- INDEX: `username` (for quick lookup)
- INDEX: `enabled` (for active schedule queries)

### Sample Data
```sql
INSERT INTO schedules (username, keywords, frequency, start_datetime, enabled)
VALUES ('elonmusk', '["AI", "Tesla"]', 'daily', '2026-01-24 09:00:00', TRUE);
```

### Data Volume
- Expected: 10-100 schedules
- Growth: Slow (user-created)
- Retention: Indefinite (until user deletes)

---

## Table: `reports`

### Purpose
Stores summary metadata for each scraping report. Lightweight table for quick queries.

### Columns

| Column | Type | Constraints | Description | Business Logic |
|--------|------|-------------|-------------|----------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique report identifier | System-generated |
| platform | VARCHAR | DEFAULT 'twitter' | Source platform | `twitter` or `reddit` |
| username | VARCHAR | NOT NULL, INDEXED | Account username | Twitter: no @, Reddit: subreddit name |
| keywords | JSON | NULL | Search keywords used | `["AI", "ML"]` or NULL for all tweets |
| tweet_count | INTEGER | NULL | Number of tweets found | 0-100 (API limit) |
| account_type | VARCHAR | NULL | Account classification | `Business`, `Professional`, `Personal`, `Bot` |
| lead_score | INTEGER | NULL | Quality score | 0-7 scale |
| report_content | TEXT | NULL | Full text report | Human-readable format |
| tweets_data | JSON | NULL | Raw tweet data | Full API response |
| filters | JSON | NULL | Filters applied | `{"min_likes": 10, "has_links": true}` |
| created_at | DATETIME | DEFAULT NOW(), INDEXED | Report generation time | Immutable |

### Indexes
- PRIMARY KEY: `id`
- INDEX: `platform` (for filtering by source)
- INDEX: `username` (for account history)
- INDEX: `created_at` (for time-based queries)

### Sample Query
```sql
-- Get all reports for a user
SELECT id, platform, tweet_count, account_type, lead_score, created_at
FROM reports
WHERE username = 'elonmusk'
ORDER BY created_at DESC;

-- Get high-quality leads from last 7 days
SELECT username, account_type, lead_score, tweet_count
FROM reports
WHERE lead_score >= 5
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY lead_score DESC, tweet_count DESC;
```

### Data Volume
- Expected: 1,000-100,000 reports
- Growth: Fast (every scrape creates one)
- Retention: Indefinite (historical analysis)

---

## Table: `historical_tweets`

### Purpose
Stores individual tweets for deduplication and historical tracking.

### Columns

| Column | Type | Constraints | Description | Business Logic |
|--------|------|-------------|-------------|----------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique record identifier | System-generated |
| tweet_id | VARCHAR | NOT NULL, UNIQUE, INDEXED | Twitter's tweet ID | 19-digit snowflake ID |
| username | VARCHAR | NOT NULL, INDEXED | Tweet author | No @ symbol |
| text | TEXT | NULL | Tweet content | Max 280 chars (Twitter limit) |
| created_at | DATETIME | NULL, INDEXED | Tweet post time | From Twitter API |
| tweet_data | JSON | NULL | Full tweet metadata | Includes metrics, entities, etc. |
| collected_at | DATETIME | DEFAULT NOW() | When we collected it | Immutable |

### Indexes
- PRIMARY KEY: `id`
- UNIQUE INDEX: `tweet_id` (prevents duplicates)
- INDEX: `username` (for user timeline queries)
- INDEX: `created_at` (for time-based analysis)

### Sample Query
```sql
-- Check if tweet already exists
SELECT id FROM historical_tweets WHERE tweet_id = '1234567890123456789';

-- Get user's tweet history
SELECT tweet_id, text, created_at
FROM historical_tweets
WHERE username = 'elonmusk'
ORDER BY created_at DESC
LIMIT 100;

-- Find tweets in date range
SELECT username, COUNT(*) as tweet_count
FROM historical_tweets
WHERE created_at BETWEEN '2026-01-01' AND '2026-01-31'
GROUP BY username
ORDER BY tweet_count DESC;
```

### Data Volume
- Expected: 10,000-1,000,000 tweets
- Growth: Fast (100 tweets per scrape)
- Retention: Indefinite (deduplication requires history)

---

## Table: `deep_history` ⭐ (Core AI/ML Table)

### Purpose
**The foundation for all AI/ML features.** Stores complete scraping data in multiple formats with extracted entities and metadata for fast querying.

### Columns

| Column | Type | Constraints | Description | Use Case |
|--------|------|-------------|-------------|----------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique history record ID | System-generated |
| report_id | INTEGER | FK → reports.id, INDEXED | Link to summary report | Join for metadata |
| username | VARCHAR | NOT NULL, INDEXED | Account username | Primary entity |
| platform | VARCHAR | NOT NULL, INDEXED | Source platform | Filter by source |
| scraped_at | DATETIME | DEFAULT NOW(), INDEXED | Scrape timestamp | Time-series analysis |
| **raw_json** | JSON | NULL | Full structured data | ML training data |
| **raw_text** | TEXT | NULL | Plain text report | LLM context |
| raw_csv | TEXT | NULL | CSV format | Data export |
| **tweet_ids** | JSON | NULL | Array of tweet IDs | Deduplication |
| **keywords** | JSON | NULL | Search keywords | Topic tracking |
| **hashtags** | JSON | NULL | Extracted hashtags | Trend analysis |
| **mentions** | JSON | NULL | Extracted @mentions | Network analysis |
| **urls** | JSON | NULL | Extracted URLs | Link analysis |
| **account_snapshot** | JSON | NULL | Account state at scrape time | Growth tracking |
| total_tweets | INTEGER | DEFAULT 0 | Tweet count | Quick metric |
| total_engagement | INTEGER | DEFAULT 0 | Sum of interactions | Popularity metric |
| avg_sentiment | FLOAT | NULL | Sentiment score | -1 to 1 scale |
| lead_score | INTEGER | NULL | Quality score | 0-7 scale |
| account_type | VARCHAR | NULL | Account classification | Segmentation |
| **topics** | JSON | NULL | LLM-extracted topics | AI feature |
| **ai_analysis** | JSON | NULL | LLM analysis results | AI feature |
| **ai_summary** | TEXT | NULL | Natural language summary | AI feature |
| scrape_type | VARCHAR | NULL | Scrape method | `quick`, `scheduled`, `bulk`, `discovery` |
| filters_used | JSON | NULL | Applied filters | Reproducibility |
| **search_vector** | TSVECTOR | NULL, GIN INDEXED | Full-text search | Fast text search |

### Indexes
- PRIMARY KEY: `id`
- FOREIGN KEY: `report_id` → `reports.id`
- INDEX: `username` (B-tree)
- INDEX: `platform` (B-tree)
- INDEX: `scraped_at` (B-tree)
- **GIN INDEX**: `search_vector` (full-text search)
- Future: **IVFFLAT INDEX**: `embedding` (vector similarity)

### Sample Queries

#### Basic Queries
```sql
-- Get all scrapes for an account
SELECT id, username, platform, total_tweets, total_engagement, scraped_at
FROM deep_history
WHERE username = 'elonmusk'
ORDER BY scraped_at DESC;

-- Track account growth over time
SELECT 
    scraped_at,
    account_snapshot->>'followers_count' as followers,
    total_engagement
FROM deep_history
WHERE username = 'elonmusk'
ORDER BY scraped_at;
```

#### Full-Text Search
```sql
-- Search for AI-related accounts
SELECT username, platform, account_type, lead_score
FROM deep_history
WHERE search_vector @@ plainto_tsquery('english', 'AI machine learning')
ORDER BY scraped_at DESC
LIMIT 20;

-- Search with ranking
SELECT 
    username,
    ts_rank(search_vector, plainto_tsquery('english', 'startup founder')) as relevance
FROM deep_history
WHERE search_vector @@ plainto_tsquery('english', 'startup founder')
ORDER BY relevance DESC;
```

#### JSON Queries
```sql
-- Find accounts with specific hashtags
SELECT username, hashtags, total_engagement
FROM deep_history
WHERE hashtags @> '["AI"]'::jsonb
ORDER BY total_engagement DESC;

-- Extract account metrics
SELECT 
    username,
    account_snapshot->>'followers_count' as followers,
    account_snapshot->>'following_count' as following,
    account_snapshot->>'verified' as verified
FROM deep_history
WHERE account_snapshot IS NOT NULL;

-- Find high-engagement tweets
SELECT 
    username,
    jsonb_array_length(tweet_ids) as tweet_count,
    total_engagement,
    ROUND(total_engagement::numeric / NULLIF(jsonb_array_length(tweet_ids), 0), 2) as avg_engagement_per_tweet
FROM deep_history
WHERE total_engagement > 10000;
```

#### Aggregation Queries
```sql
-- Top hashtags across all scrapes
SELECT 
    hashtag,
    COUNT(*) as mention_count
FROM deep_history,
     jsonb_array_elements_text(hashtags::jsonb) as hashtag
GROUP BY hashtag
ORDER BY mention_count DESC
LIMIT 20;

-- Platform comparison
SELECT 
    platform,
    COUNT(*) as scrape_count,
    AVG(total_tweets) as avg_tweets,
    AVG(total_engagement) as avg_engagement
FROM deep_history
GROUP BY platform;

-- Daily scrape volume
SELECT 
    DATE(scraped_at) as date,
    COUNT(*) as scrapes,
    SUM(total_tweets) as total_tweets
FROM deep_history
WHERE scraped_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(scraped_at)
ORDER BY date DESC;
```

#### Time-Series Analysis
```sql
-- Account engagement trend
SELECT 
    username,
    DATE_TRUNC('day', scraped_at) as day,
    AVG(total_engagement) as avg_engagement,
    MAX(total_engagement) as max_engagement
FROM deep_history
WHERE username = 'elonmusk'
  AND scraped_at > NOW() - INTERVAL '90 days'
GROUP BY username, DATE_TRUNC('day', scraped_at)
ORDER BY day;
```

### Data Volume
- Expected: 10,000-1,000,000 records
- Growth: Fast (every scrape creates one)
- Retention: Indefinite (AI/ML training data)
- Size per record: 50-400 KB (depending on tweet count)

### Storage Estimates
| Records | Storage (approx) |
|---------|------------------|
| 1,000 | 100 MB |
| 10,000 | 1 GB |
| 100,000 | 10 GB |
| 1,000,000 | 100 GB |

---

## Data Dictionary

### Enumerations

#### platform
- `twitter` - Twitter/X data
- `reddit` - Reddit data

#### frequency
- `once` - One-time execution
- `hourly` - Every hour
- `daily` - Once per day
- `weekly` - Once per week

#### account_type
- `Business` - Company/organization account
- `Professional` - Individual professional
- `Personal` - Personal account
- `Bot` - Automated account

#### scrape_type
- `quick` - Manual quick scrape
- `scheduled` - Automated scheduled scrape
- `bulk` - Bulk scrape of multiple accounts
- `discovery` - Account discovery scrape

### Metrics

#### lead_score
- Scale: 0-7
- 0-2: Low quality
- 3-4: Medium quality
- 5-6: High quality
- 7: Excellent quality

#### avg_sentiment
- Scale: -1.0 to 1.0
- -1.0: Very negative
- 0.0: Neutral
- 1.0: Very positive

---

## Indexes Summary

| Table | Index Name | Type | Columns | Purpose |
|-------|-----------|------|---------|---------|
| schedules | schedules_pkey | PRIMARY KEY | id | Unique identifier |
| schedules | idx_schedules_username | B-TREE | username | User lookup |
| reports | reports_pkey | PRIMARY KEY | id | Unique identifier |
| reports | idx_reports_platform | B-TREE | platform | Platform filter |
| reports | idx_reports_username | B-TREE | username | User lookup |
| reports | idx_reports_created_at | B-TREE | created_at | Time-based queries |
| historical_tweets | historical_tweets_pkey | PRIMARY KEY | id | Unique identifier |
| historical_tweets | idx_historical_tweets_tweet_id | UNIQUE B-TREE | tweet_id | Deduplication |
| historical_tweets | idx_historical_tweets_username | B-TREE | username | User lookup |
| historical_tweets | idx_historical_tweets_created_at | B-TREE | created_at | Time-based queries |
| deep_history | deep_history_pkey | PRIMARY KEY | id | Unique identifier |
| deep_history | idx_deep_history_report_id | B-TREE | report_id | Foreign key |
| deep_history | idx_deep_history_username | B-TREE | username | User lookup |
| deep_history | idx_deep_history_platform | B-TREE | platform | Platform filter |
| deep_history | idx_deep_history_scraped_at | B-TREE | scraped_at | Time-based queries |
| deep_history | idx_deep_history_search_vector | GIN | search_vector | Full-text search |

---

## Foreign Key Relationships

```sql
-- deep_history → reports
ALTER TABLE deep_history
ADD CONSTRAINT fk_deep_history_report
FOREIGN KEY (report_id) REFERENCES reports(id)
ON DELETE SET NULL;
```

---

## Data Classification

| Classification | Tables | Purpose | Retention |
|----------------|--------|---------|-----------|
| **SYSTEM** | All `id` columns | Internal identifiers | Permanent |
| **PII** | `username` columns | User identifiers | Permanent |
| **CONTENT** | `raw_json`, `raw_text`, `tweets_data` | User-generated content | Permanent |
| **METRIC** | `tweet_count`, `total_engagement`, `lead_score` | Calculated metrics | Permanent |
| **TEMPORAL** | `created_at`, `scraped_at`, `last_run` | Timestamps | Permanent |
| **CONFIG** | `frequency`, `filters`, `enabled` | Configuration | Permanent |
| **CATEGORY** | `platform`, `account_type`, `scrape_type` | Classifications | Permanent |

---

## Future Schema Extensions

### Phase 3: Vector Embeddings
```sql
-- Add pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to deep_history
ALTER TABLE deep_history
ADD COLUMN embedding vector(1536);

-- Create IVFFLAT index for similarity search
CREATE INDEX idx_deep_history_embedding
ON deep_history
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Phase 4: Advanced Analytics
```sql
-- Add computed columns
ALTER TABLE deep_history
ADD COLUMN engagement_rate FLOAT GENERATED ALWAYS AS 
  (total_engagement::float / NULLIF(total_tweets, 0)) STORED;

-- Add partitioning by date (for large datasets)
CREATE TABLE deep_history_2026_01 PARTITION OF deep_history
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Maintenance Queries

### Vacuum & Analyze
```sql
-- Regular maintenance
VACUUM ANALYZE schedules;
VACUUM ANALYZE reports;
VACUUM ANALYZE historical_tweets;
VACUUM ANALYZE deep_history;
```

### Index Maintenance
```sql
-- Rebuild indexes if needed
REINDEX TABLE deep_history;
```

### Storage Analysis
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index sizes
SELECT 
    indexname,
    tablename,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## Export Queries

### CSV Export
```sql
-- Export deep_history to CSV
COPY (
    SELECT 
        id,
        username,
        platform,
        total_tweets,
        total_engagement,
        account_type,
        lead_score,
        scraped_at
    FROM deep_history
    ORDER BY scraped_at DESC
) TO '/tmp/deep_history_export.csv' WITH CSV HEADER;
```

### JSON Export
```sql
-- Export as JSON
SELECT json_agg(row_to_json(t))
FROM (
    SELECT * FROM deep_history
    WHERE scraped_at > NOW() - INTERVAL '7 days'
) t;
```

---

## Performance Tuning

### Recommended PostgreSQL Settings
```ini
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB
max_connections = 100
```

### Query Optimization Tips
1. Always use indexes for WHERE clauses
2. Use EXPLAIN ANALYZE to check query plans
3. Avoid SELECT * in production queries
4. Use LIMIT for large result sets
5. Create partial indexes for common filters
6. Use materialized views for complex aggregations

---

## Backup & Recovery

### Backup Command
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Restore Command
```bash
psql $DATABASE_URL < backup_20260123.sql
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-20 | Initial schema (schedules, reports, historical_tweets) |
| 2.0 | 2026-01-23 | Added deep_history table |
| 2.1 | 2026-01-23 | Added search_vector and GIN index |
| 3.0 | TBD | Add vector embeddings (pgvector) |

---

**Generated:** 2026-01-23  
**Database:** PostgreSQL 14+  
**Platform:** Railway  
**Schema Owner:** Social Listening Platform

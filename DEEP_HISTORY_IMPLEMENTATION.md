# Deep History Table - Implementation Summary

## Overview
Created `deep_history` table to store all scraping data in multiple formats, providing a rich dataset for future AI/ML/MCP features.

## Why Deep History?

### **Problem Solved:**
- Historical data was being lost between deployments
- No way to analyze trends over time
- No dataset for training ML models
- Limited ability to do semantic search or advanced analytics

### **Solution:**
- Comprehensive data storage in multiple formats (JSON, text, CSV)
- Extracted entities for quick queries (hashtags, mentions, URLs)
- Account snapshots at time of scrape
- Foundation for AI/ML features (embeddings, LLM analysis)

## Database Schema

### **Core Fields:**
- `id`: Primary key
- `report_id`: Foreign key to reports table
- `username`: Account username
- `platform`: 'twitter' or 'reddit'
- `scraped_at`: Timestamp (indexed)

### **Raw Data (Multiple Formats):**
- `raw_json`: Full structured data (JSONB)
- `raw_text`: Plain text report
- `raw_csv`: CSV format (for future use)

### **Extracted Entities:**
- `tweet_ids`: Array of tweet/post IDs (JSON)
- `keywords`: Keywords used in search (JSON)
- `hashtags`: Extracted hashtags (JSON)
- `mentions`: Extracted @mentions (JSON)
- `urls`: Extracted URLs (JSON)

### **Account Snapshot:**
- `account_snapshot`: Full account info at time of scrape (JSONB)
  - Followers, following, verified status
  - Bio, location, profile image
  - Account creation date

### **Metrics:**
- `total_tweets`: Number of tweets/posts
- `total_engagement`: Sum of likes + retweets + replies
- `avg_sentiment`: Average sentiment score
- `lead_score`: Quality score (0-7)
- `account_type`: Business/Professional/Personal/Bot

### **AI/ML Fields (For Future Use):**
- `topics`: LLM-extracted topics (JSON)
- `ai_analysis`: LLM analysis results (JSON)
- `ai_summary`: Natural language summary (Text)
- `embedding`: Vector embedding (will add pgvector extension later)

### **Metadata:**
- `scrape_type`: 'quick', 'scheduled', 'bulk', 'discovery'
- `filters_used`: Filters applied during scrape (JSON)

## Integration

### **Automatic Saving:**
All scraping operations now save to `deep_history`:
- ✅ Quick Scrape (Twitter)
- ✅ Quick Scrape (Reddit)
- ✅ Bulk Scrape
- ✅ Scheduled Scrapes (via scheduler)

### **Helper Function:**
```python
save_to_deep_history(
    username='elonmusk',
    platform='twitter',
    raw_json={...},
    raw_text='...',
    report_id=123,
    scrape_type='quick',
    filters_used={...}
)
```

### **Entity Extraction:**
Automatically extracts from raw_json:
- Tweet IDs
- Hashtags (deduplicated)
- Mentions (deduplicated)
- URLs (deduplicated)
- Total engagement metrics
- Account snapshot

## Use Cases

### **Current Benefits:**
1. **Data Preservation**: Never lose historical data
2. **Trend Analysis**: Track account changes over time
3. **Full-Text Search**: Search across all reports
4. **Quick Queries**: Pre-extracted entities for fast filtering

### **Future AI/ML Benefits:**

#### **Phase 1: LLM Integration**
- Store AI-generated summaries in `ai_summary`
- Store structured analysis in `ai_analysis`
- Store extracted topics in `topics`
- Query: "Show me all accounts LLM classified as high-quality leads"

#### **Phase 2: Vector Search**
- Add pgvector extension to PostgreSQL
- Store embeddings in `embedding` column
- Semantic similarity search across all historical data
- Query: "Find accounts similar to this one (by meaning, not keywords)"

#### **Phase 3: ML Models**
- Train lead scoring models on historical data
- Predict account quality based on patterns
- Detect emerging trends and topics
- Anomaly detection for viral content

#### **Phase 4: MCP Integration**
- Expose deep_history via MCP tools
- Natural language queries: "Find all B2B SaaS accounts from last month"
- Time-series analysis: "Show engagement trends for @username"
- Cross-platform insights: "Compare Twitter vs Reddit mentions"

## Example Queries

### **SQL Queries:**

```sql
-- Find all accounts scraped in last 7 days
SELECT username, platform, total_tweets, total_engagement, scraped_at
FROM deep_history
WHERE scraped_at > NOW() - INTERVAL '7 days'
ORDER BY total_engagement DESC;

-- Find accounts with specific hashtags
SELECT username, hashtags, total_engagement
FROM deep_history
WHERE hashtags @> '["AI", "ML"]'::jsonb
ORDER BY total_engagement DESC;

-- Track account growth over time
SELECT username, scraped_at, 
       account_snapshot->>'followers_count' as followers
FROM deep_history
WHERE username = 'elonmusk'
ORDER BY scraped_at;

-- Find high-engagement accounts
SELECT username, platform, total_engagement, account_type
FROM deep_history
WHERE total_engagement > 10000
  AND account_type = 'Business'
ORDER BY total_engagement DESC;
```

### **Future Semantic Queries (with embeddings):**

```sql
-- Find similar accounts (semantic search)
SELECT username, platform, ai_summary
FROM deep_history
ORDER BY embedding <-> (SELECT embedding FROM deep_history WHERE username = 'salesforce')
LIMIT 10;
```

## Data Growth Estimates

### **Storage per Record:**
- Small account (10 tweets): ~50 KB
- Medium account (50 tweets): ~200 KB
- Large account (100 tweets): ~400 KB

### **Monthly Estimates:**
- 100 scrapes/month: ~20 MB
- 1,000 scrapes/month: ~200 MB
- 10,000 scrapes/month: ~2 GB

**Railway PostgreSQL free tier**: 512 MB (good for ~2,500 scrapes)
**Paid tier**: 8 GB+ (good for 20,000+ scrapes)

## Maintenance

### **Cleanup Old Data (if needed):**
```sql
-- Delete records older than 6 months
DELETE FROM deep_history
WHERE scraped_at < NOW() - INTERVAL '6 months';

-- Archive to cold storage
-- (Export to S3/GCS before deleting)
```

### **Indexes for Performance:**
```sql
CREATE INDEX idx_deep_history_username ON deep_history(username);
CREATE INDEX idx_deep_history_platform ON deep_history(platform);
CREATE INDEX idx_deep_history_scraped_at ON deep_history(scraped_at);
CREATE INDEX idx_deep_history_hashtags ON deep_history USING GIN(hashtags);
```

## Migration Path

### **Phase 1: Basic Storage (✅ Complete)**
- Table created
- Automatic saving from all scrape endpoints
- Entity extraction working

### **Phase 2: Enhanced Search (Next)**
- Add full-text search (tsvector)
- Add GIN indexes for JSON fields
- Create views for common queries

### **Phase 3: Vector Extension (When Starting AI)**
- Install pgvector extension on Railway
- Add embedding column
- Populate embeddings for existing data
- Build semantic search API

### **Phase 4: Advanced Analytics (Future)**
- Time-series analysis views
- Trend detection algorithms
- ML model training pipelines
- Real-time dashboards

## Files Modified

- `twitter-scraper-app/database.py`: Added DeepHistory model and save_to_deep_history() function
- `twitter-scraper-app/app.py`: Updated all scrape endpoints to save to deep_history

## Testing

### **Manual Test:**
1. Run a quick scrape
2. Check PostgreSQL: `SELECT * FROM deep_history ORDER BY id DESC LIMIT 1;`
3. Verify all fields populated correctly
4. Check entity extraction (hashtags, mentions, etc.)

### **Automated Test:**
```python
# Test deep_history saving
from database import save_to_deep_history, get_db_session, DeepHistory

# Save test record
save_to_deep_history(
    username='test_user',
    platform='twitter',
    raw_json={'tweets': [{'id': '123', 'text': 'Test #AI'}]},
    raw_text='Test report',
    scrape_type='quick'
)

# Query it back
db = get_db_session()
record = db.query(DeepHistory).filter_by(username='test_user').first()
assert record is not None
assert 'AI' in record.hashtags
```

## Next Steps

1. ✅ Deploy to Railway (automatic)
2. ✅ Start collecting data
3. 📊 Monitor storage usage
4. 🤖 Plan AI/ML features (LLM integration, embeddings, etc.)
5. 🔍 Build query/analytics UI (optional)

## Summary

The `deep_history` table is now the foundation for all advanced features. Every scrape automatically builds your dataset, ready for:
- LLM-powered analysis
- Semantic search with embeddings
- ML model training
- MCP tool integration
- Advanced analytics and insights

**Data collection starts NOW** - while you decide which AI/ML features to build next!

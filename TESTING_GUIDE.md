# Testing Guide - Option A: Test What We Built

## Overview
Step-by-step guide to test all features including the new search API and deep_history functionality.

---

## Prerequisites

1. ✅ Railway deployment is live: https://web-twitter-scraper.up.railway.app/
2. ✅ PostgreSQL database connected
3. ✅ Twitter API credentials configured
4. ✅ Recent deployment with deep_history and search features

---

## Test 1: Run Quick Scrapes (Generate Data)

### Step 1.1: Quick Twitter Scrape

1. Go to: https://web-twitter-scraper.up.railway.app/
2. Navigate to **"Twitter Scraping"** tab
3. Fill in the form:
   - **Username**: `elonmusk` (or any active Twitter account)
   - **Keywords**: `AI, Tesla, SpaceX` (comma-separated)
   - **Min Keyword Mentions**: `1`
4. Click **"Generate Report"**
5. Wait for results (10-30 seconds)

**Expected Result:**
- ✅ Success message with tweet count
- ✅ Account type and lead score displayed
- ✅ Download buttons appear
- ✅ "View Report" button works

### Step 1.2: Run 2-3 More Scrapes

Scrape different accounts to build up data:
- `BillGates` with keywords: `health, technology`
- `sundarpichai` with keywords: `Google, AI`
- `satyanadella` with keywords: `Microsoft, cloud`

**Why?** We need multiple records in `deep_history` to test search functionality.

---

## Test 2: Verify Data in Database

### Option A: Via Railway Dashboard

1. Go to Railway dashboard
2. Click on your PostgreSQL service
3. Click **"Data"** tab
4. Run these queries:

```sql
-- Check reports table
SELECT id, username, platform, tweet_count, created_at 
FROM reports 
ORDER BY created_at DESC 
LIMIT 5;

-- Check deep_history table
SELECT id, username, platform, total_tweets, total_engagement, scraped_at
FROM deep_history
ORDER BY scraped_at DESC
LIMIT 5;

-- Check if search_vector is populated
SELECT 
    id, 
    username, 
    CASE 
        WHEN search_vector IS NOT NULL THEN 'YES' 
        ELSE 'NO' 
    END as has_search_vector
FROM deep_history
LIMIT 5;
```

### Option B: Via API Endpoint

Open in browser or use curl:

```bash
# Check reports
curl https://web-twitter-scraper.up.railway.app/reports

# Check health (includes database stats)
curl https://web-twitter-scraper.up.railway.app/health
```

**Expected Result:**
- ✅ Multiple records in both `reports` and `deep_history`
- ✅ `search_vector` column is populated (not NULL)
- ✅ Data matches your scrapes

---

## Test 3: Test Search API 🔍

### Test 3.1: Simple Search (via curl)

```bash
# Search for "AI"
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "limit": 10}'
```

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "username": "elonmusk",
      "platform": "twitter",
      "total_tweets": 50,
      "total_engagement": 150000,
      "account_type": "Business",
      "lead_score": 7,
      "keywords": ["AI", "Tesla"],
      "hashtags": ["AI", "Tech"],
      "scraped_at": "2026-01-23T10:30:00"
    }
  ],
  "total": 1,
  "query": "AI"
}
```

### Test 3.2: Multi-Word Search

```bash
# Search for "AI machine learning"
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "AI machine learning", "limit": 10}'
```

### Test 3.3: Platform-Specific Search

```bash
# Search only Twitter
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "technology", "platform": "twitter", "limit": 10}'
```

### Test 3.4: Search via Browser Console

1. Open https://web-twitter-scraper.up.railway.app/
2. Open browser console (F12)
3. Run this JavaScript:

```javascript
// Test search API
async function testSearch(query) {
    const response = await fetch('/search-history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, limit: 10 })
    });
    const data = await response.json();
    console.log('Search Results:', data);
    return data;
}

// Run searches
await testSearch('AI');
await testSearch('technology startup');
await testSearch('cloud computing');
```

**Expected Result:**
- ✅ Returns matching records
- ✅ Results ranked by relevance
- ✅ Fast response (< 100ms for small datasets)

---

## Test 4: Advanced Search Queries

### Test 4.1: Search by Hashtag

```bash
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "AI Tech Innovation", "limit": 20}'
```

### Test 4.2: Search by Username

```bash
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "elonmusk", "limit": 5}'
```

### Test 4.3: Search by Topic

```bash
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence robotics", "limit": 10}'
```

---

## Test 5: Verify Search Performance

### Test 5.1: Check Query Speed

Run this in Railway PostgreSQL console:

```sql
-- Enable timing
\timing on

-- Test full-text search speed
EXPLAIN ANALYZE
SELECT username, platform, total_tweets
FROM deep_history
WHERE search_vector @@ plainto_tsquery('english', 'AI machine learning')
LIMIT 10;
```

**Expected Result:**
- ✅ Query time < 50ms (with GIN index)
- ✅ Uses "Bitmap Index Scan" on search_vector
- ✅ No sequential scan

### Test 5.2: Compare with LIKE Query (Slow)

```sql
-- Slow query without index
EXPLAIN ANALYZE
SELECT username, platform, total_tweets
FROM deep_history
WHERE raw_text LIKE '%AI%'
LIMIT 10;
```

**Expected Result:**
- ❌ Much slower (100ms+)
- ❌ Uses "Sequential Scan"
- ✅ Proves GIN index is working!

---

## Test 6: Test Report History

### Step 6.1: View Reports in UI

1. Go to https://web-twitter-scraper.up.railway.app/
2. Click **"Report History"** tab
3. Verify you see all your scrapes

**Expected Result:**
- ✅ All reports listed with icons (🐦 for Twitter)
- ✅ Shows username, tweet count, account type, lead score
- ✅ Click "View" to see full report

### Step 6.2: Verify Persistence

1. Close browser
2. Reopen https://web-twitter-scraper.up.railway.app/
3. Go to Report History tab

**Expected Result:**
- ✅ All reports still there (PostgreSQL persistence working!)

---

## Test 7: Test Account Discovery with Search

### Step 7.1: Discover Accounts

1. Go to **"Account Discovery"** tab
2. Enter keywords: `AI, machine learning, startup`
3. Set filters:
   - Min Followers: 1000+
   - Verified Only: No
   - Has Links: Yes
4. Click **"Discover Accounts"**

**Expected Result:**
- ✅ Finds 10-50 accounts
- ✅ Shows quality scores
- ✅ Account type badges
- ✅ Pagination works

### Step 7.2: Bulk Scrape Discovered Accounts

1. Select 2-3 accounts
2. Click **"Bulk Scrape Selected"**
3. Wait for completion

**Expected Result:**
- ✅ All selected accounts scraped
- ✅ Reports saved to database
- ✅ Data appears in Report History
- ✅ Data searchable via search API

---

## Test 8: Test Similar Accounts Feature

### Step 8.1: Find Similar Accounts

1. Go to **"Account Discovery"** tab
2. Check **"Find accounts similar to a reference account"**
3. Enter reference: `elonmusk`
4. Click **"Discover Accounts"**

**Expected Result:**
- ✅ Shows reference account preview
- ✅ Displays extracted keywords
- ✅ Finds similar accounts (Tesla, SpaceX, tech CEOs)
- ✅ Quality scores displayed

---

## Test 9: Verify Deep History Data

### Test 9.1: Check Extracted Entities

```sql
-- Check hashtags extraction
SELECT 
    username,
    hashtags,
    array_length(hashtags::text[], 1) as hashtag_count
FROM deep_history
WHERE hashtags IS NOT NULL
LIMIT 5;

-- Check mentions extraction
SELECT 
    username,
    mentions,
    array_length(mentions::text[], 1) as mention_count
FROM deep_history
WHERE mentions IS NOT NULL
LIMIT 5;

-- Check account snapshots
SELECT 
    username,
    account_snapshot->>'followers_count' as followers,
    account_snapshot->>'verified' as verified,
    account_snapshot->>'description' as bio
FROM deep_history
WHERE account_snapshot IS NOT NULL
LIMIT 3;
```

**Expected Result:**
- ✅ Hashtags extracted and deduplicated
- ✅ Mentions extracted and deduplicated
- ✅ Account snapshots contain full profile data

---

## Test 10: End-to-End Search Test

### Complete Workflow Test

```bash
# 1. Run a scrape (via UI or API)
# 2. Wait 10 seconds for data to save
# 3. Search for content from that scrape

curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "Tesla SpaceX", "limit": 5}'

# 4. Verify the scraped account appears in results
```

**Expected Result:**
- ✅ Recently scraped account appears in search results
- ✅ Search finds content from bio, tweets, and keywords
- ✅ Results include all metadata (engagement, lead score, etc.)

---

## Troubleshooting

### Issue: Search returns empty results

**Check:**
```sql
-- Verify search_vector is populated
SELECT COUNT(*) FROM deep_history WHERE search_vector IS NOT NULL;

-- If 0, search_vector not populated
-- Solution: Run a new scrape (it will populate automatically)
```

### Issue: Search is slow

**Check:**
```sql
-- Verify GIN index exists
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'deep_history' 
  AND indexname LIKE '%search%';

-- If no index, create it:
CREATE INDEX idx_deep_history_search_vector 
ON deep_history 
USING gin(search_vector);
```

### Issue: No data in deep_history

**Check:**
```sql
-- Check if table exists
SELECT COUNT(*) FROM deep_history;

-- Check if reports exist but not deep_history
SELECT COUNT(*) FROM reports;

-- If reports > 0 but deep_history = 0:
-- Solution: Run new scrapes (old ones won't backfill automatically)
```

### Issue: PostgreSQL not connected

**Check:**
```bash
# Check health endpoint
curl https://web-twitter-scraper.up.railway.app/health

# Look for:
# "type": "PostgreSQL" (good)
# "type": "SQLite" (bad - using local DB)
```

**Solution:** Check Railway environment variables (see RAILWAY_POSTGRES_FIX.md)

---

## Success Criteria ✅

After completing all tests, you should have:

- ✅ 5+ scrapes in database
- ✅ All data in both `reports` and `deep_history` tables
- ✅ `search_vector` populated for all records
- ✅ Search API returns relevant results in < 100ms
- ✅ Full-text search finds content from bios, tweets, keywords
- ✅ Hashtags, mentions, URLs extracted correctly
- ✅ Account snapshots captured
- ✅ Reports persist across browser sessions
- ✅ GIN index working (fast queries)

---

## Next Steps After Testing

### If Everything Works:
- ✅ **Let data accumulate** - Run scrapes regularly
- ✅ **Monitor storage** - Check Railway database usage
- ✅ **Explore search patterns** - What queries are useful?
- ✅ **Ready for Phase 3** - AI/ML features can use this data

### If Issues Found:
- 🔧 Check Railway logs for errors
- 🔧 Verify PostgreSQL connection
- 🔧 Ensure latest deployment is active
- 🔧 Review troubleshooting section above

---

## Advanced Testing (Optional)

### Test Search Ranking

```sql
-- Search with ranking
SELECT 
    username,
    platform,
    ts_rank(search_vector, plainto_tsquery('english', 'AI startup')) as rank,
    total_engagement
FROM deep_history
WHERE search_vector @@ plainto_tsquery('english', 'AI startup')
ORDER BY rank DESC
LIMIT 10;
```

### Test JSON Queries

```sql
-- Find accounts with specific hashtags
SELECT username, hashtags, total_engagement
FROM deep_history
WHERE hashtags @> '["AI"]'::jsonb
ORDER BY total_engagement DESC;

-- Find high-engagement accounts
SELECT 
    username,
    total_engagement,
    total_tweets,
    ROUND(total_engagement::numeric / NULLIF(total_tweets, 0), 2) as avg_per_tweet
FROM deep_history
WHERE total_engagement > 1000
ORDER BY avg_per_tweet DESC;
```

### Test Time-Series Queries

```sql
-- Track account over time
SELECT 
    scraped_at,
    account_snapshot->>'followers_count' as followers,
    total_engagement
FROM deep_history
WHERE username = 'elonmusk'
ORDER BY scraped_at;
```

---

## Performance Benchmarks

### Expected Performance (with 1,000 records):

| Operation | Time | Notes |
|-----------|------|-------|
| Full-text search | < 50ms | With GIN index |
| JSON query | < 100ms | With GIN index on JSONB |
| Simple SELECT | < 10ms | With B-tree index |
| Aggregation | < 200ms | Depends on complexity |
| Insert (scrape) | < 500ms | Includes entity extraction |

### Storage Benchmarks:

| Records | Storage | Notes |
|---------|---------|-------|
| 100 | 10 MB | Small dataset |
| 1,000 | 100 MB | Medium dataset |
| 10,000 | 1 GB | Large dataset |
| 100,000 | 10 GB | Very large dataset |

---

## Testing Checklist

Print this and check off as you test:

- [ ] Run 5+ quick scrapes
- [ ] Verify data in `reports` table
- [ ] Verify data in `deep_history` table
- [ ] Confirm `search_vector` is populated
- [ ] Test simple search query
- [ ] Test multi-word search
- [ ] Test platform-specific search
- [ ] Test search via browser console
- [ ] Verify search performance (< 100ms)
- [ ] Check Report History UI
- [ ] Test Account Discovery
- [ ] Test Similar Accounts
- [ ] Verify hashtag extraction
- [ ] Verify mention extraction
- [ ] Verify account snapshots
- [ ] Test end-to-end workflow
- [ ] Check GIN index exists
- [ ] Verify PostgreSQL connection
- [ ] Monitor Railway logs
- [ ] Check storage usage

---

**Happy Testing! 🚀**

Once you've completed these tests, you'll have a solid foundation of data for Phase 3 (AI/ML features).

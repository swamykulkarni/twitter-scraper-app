# Social Listening Platform - API Endpoints Reference

## Base URL
```
https://web-twitter-scraper.up.railway.app
```

---

## 📊 Core Scraping Endpoints

### 1. Twitter Quick Scrape
**POST** `/scrape`

Scrape a Twitter account with keywords and filters.

**Request Body:**
```json
{
  "username": "elonmusk",
  "keywords": "AI, Tesla",
  "min_keyword_mentions": 1,
  "filters": {
    "min_likes": 100,
    "min_retweets": 10,
    "min_replies": 5,
    "has_links": true,
    "has_media": false,
    "is_retweet": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "report_id": 123,
  "tweet_count": 25,
  "account_type": "Business",
  "lead_score": 7,
  "report_content": "Full report text...",
  "report_file": "reports/twitter_report_elonmusk_20260126.txt",
  "json_file": "reports/twitter_report_elonmusk_20260126.json"
}
```

---

### 2. Reddit Quick Scrape
**POST** `/scrape-reddit`

Scrape a subreddit with keywords.

**Request Body:**
```json
{
  "subreddit": "technology",
  "keywords": "AI, machine learning",
  "time_filter": "week",
  "min_keyword_mentions": 1
}
```

**Response:**
```json
{
  "success": true,
  "report_id": 124,
  "post_count": 30,
  "report_content": "Full report text...",
  "report_file": "reports/reddit_report_technology_20260126.txt"
}
```

---

## 🔍 Account Discovery Endpoints

### 3. Discover Accounts (Keyword-Based)
**POST** `/discover-accounts`

Find Twitter accounts based on keywords.

**Request Body:**
```json
{
  "keywords": "GCC, manufacturing, Pune",
  "max_results": 100,
  "filters": {
    "min_followers": 1000,
    "verified_only": false,
    "has_links": true,
    "exclude_retweets": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "accounts": [
    {
      "username": "salesforce",
      "name": "Salesforce",
      "followers_count": 500000,
      "quality_score": 85,
      "account_type": "Business",
      "matching_tweets": 15,
      "verified": true
    }
  ],
  "total_accounts": 25,
  "tweets_searched": 100
}
```

---

### 4. Find Similar Accounts
**POST** `/find-similar-accounts`

Find accounts similar to a reference account.

**Request Body:**
```json
{
  "reference_username": "salesforce",
  "max_results": 100,
  "filters": {
    "min_followers": 1000,
    "verified_only": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "accounts": [...],
  "total_accounts": 20,
  "reference_account": {
    "username": "salesforce",
    "name": "Salesforce",
    "followers": 500000,
    "verified": true
  },
  "extracted_keywords": ["CRM", "sales", "cloud", "AI"],
  "tweets_searched": 100
}
```

---

### 5. Bulk Scrape
**POST** `/bulk-scrape`

Scrape multiple Twitter accounts at once.

**Request Body:**
```json
{
  "usernames": ["salesforce", "hubspot", "zendesk"],
  "keywords": "CRM, sales",
  "min_keyword_mentions": 1,
  "filters": {}
}
```

**Response:**
```json
{
  "success": true,
  "total_processed": 3,
  "successful": 3,
  "results": [
    {
      "username": "salesforce",
      "success": true,
      "tweet_count": 25,
      "account_type": "Business",
      "lead_score": 7
    }
  ],
  "errors": []
}
```

---

## 📅 Schedule Management Endpoints

### 6. Get All Schedules
**GET** `/schedules`

Get list of all scheduled scrapes.

**Response:**
```json
{
  "success": true,
  "schedules": [
    {
      "id": 1,
      "username": "elonmusk",
      "keywords": ["AI", "Tesla"],
      "frequency": "daily",
      "start_datetime": "2026-01-26T10:00:00",
      "next_run": "2026-01-27T10:00:00",
      "last_run": "2026-01-26T10:00:00",
      "enabled": true
    }
  ]
}
```

---

### 7. Create Schedule
**POST** `/schedules`

Create a new scheduled scrape.

**Request Body:**
```json
{
  "username": "elonmusk",
  "keywords": "AI, Tesla",
  "frequency": "daily",
  "start_datetime": "2026-01-27T10:00:00",
  "day": null
}
```

**Frequency Options:**
- `once` - One-time scrape
- `hourly` - Every hour
- `daily` - Every day at specified time
- `weekly` - Every week on specified day

**Response:**
```json
{
  "success": true,
  "schedule": {
    "id": 1,
    "username": "elonmusk",
    "frequency": "daily",
    "next_run": "2026-01-27T10:00:00"
  }
}
```

---

### 8. Delete Schedule
**DELETE** `/schedules/<schedule_id>`

Delete a scheduled scrape.

**Response:**
```json
{
  "success": true,
  "message": "Schedule deleted"
}
```

---

## 📝 Reports Endpoints

### 9. Get All Reports
**GET** `/reports`

Get list of all generated reports (last 50).

**Response:**
```json
{
  "success": true,
  "reports": [
    {
      "id": 123,
      "platform": "twitter",
      "username": "elonmusk",
      "keywords": ["AI", "Tesla"],
      "tweet_count": 25,
      "account_type": "Business",
      "lead_score": 7,
      "created_at": "2026-01-26T10:30:00"
    }
  ],
  "total": 50
}
```

---

### 10. Get Specific Report
**GET** `/reports/<report_id>`

Get a specific report by ID with full content.

**Response:**
```json
{
  "success": true,
  "report": {
    "id": 123,
    "username": "elonmusk",
    "tweet_count": 25
  },
  "report_content": "Full report text...",
  "tweets_data": {...}
}
```

---

## 🗄️ Deep History Endpoints

### 11. Get Deep History Records
**GET** `/deep-history`

Get historical scraping data with filters and pagination.

**Query Parameters:**
- `platform` - Filter by platform (twitter/reddit)
- `username` - Filter by username
- `scrape_type` - Filter by type (quick/scheduled/bulk/discovery)
- `limit` - Number of records (default: 50, max: 500)
- `offset` - Pagination offset (default: 0)
- `format` - Response format (summary/full, default: summary)

**Examples:**
```
/deep-history
/deep-history?platform=twitter
/deep-history?username=elonmusk
/deep-history?scrape_type=scheduled
/deep-history?format=full&limit=100
```

**Response:**
```json
{
  "success": true,
  "records": [
    {
      "id": 1,
      "username": "elonmusk",
      "platform": "twitter",
      "scraped_at": "2026-01-26T10:30:00",
      "scrape_type": "quick",
      "total_tweets": 25,
      "total_engagement": 15000,
      "lead_score": 7,
      "account_type": "Business",
      "keywords": ["AI", "Tesla"],
      "hashtags": ["AI", "ElectricVehicles"],
      "mentions": ["Tesla", "SpaceX"]
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "returned": 50
}
```

---

### 12. Get Specific Deep History Record
**GET** `/deep-history/<record_id>`

Get a specific deep_history record with full raw data.

**Response:**
```json
{
  "success": true,
  "record": {
    "id": 1,
    "username": "elonmusk",
    "raw_json": {...},
    "raw_text": "Full report...",
    "account_snapshot": {...},
    "tweet_ids": ["123", "456"],
    "hashtags": ["AI"],
    "mentions": ["Tesla"]
  }
}
```

---

### 13. Get Deep History Statistics
**GET** `/deep-history/stats`

Get comprehensive statistics about your data.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_records": 150,
    "total_tweets_collected": 3750,
    "total_engagement": 500000,
    "unique_accounts": 45,
    "by_platform": {
      "twitter": 120,
      "reddit": 30
    },
    "by_scrape_type": {
      "quick": 80,
      "scheduled": 40,
      "bulk": 25,
      "discovery": 5
    },
    "top_accounts": [
      {
        "username": "elonmusk",
        "platform": "twitter",
        "scrape_count": 15
      }
    ],
    "date_range": {
      "first_scrape": "2026-01-20T08:00:00",
      "last_scrape": "2026-01-26T15:30:00"
    }
  }
}
```

---

### 14. Export Deep History to CSV
**GET** `/deep-history/export`

Download deep_history data as CSV file.

**Query Parameters:**
- `platform` - Filter by platform
- `username` - Filter by username
- `scrape_type` - Filter by scrape type
- `limit` - Number of records (default: 100, max: 1000)

**Examples:**
```
/deep-history/export
/deep-history/export?platform=twitter
/deep-history/export?username=elonmusk&limit=500
```

**Response:** CSV file download

---

### 15. Search Deep History
**POST** `/search-history`

Full-text search across all deep_history records.

**Request Body:**
```json
{
  "query": "AI machine learning",
  "platform": "twitter",
  "limit": 50
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "username": "elonmusk",
      "platform": "twitter",
      "total_tweets": 25,
      "keywords": ["AI", "machine learning"]
    }
  ],
  "total": 15,
  "query": "AI machine learning"
}
```

---

## 🏥 System Health Endpoints

### 16. Health Check
**GET** `/health`

Check system health and database status.

**Response:**
```json
{
  "status": "healthy",
  "database": {
    "type": "PostgreSQL",
    "status": "connected",
    "connection_string": "postgresql://...",
    "url_set": true
  },
  "data": {
    "total_records": 150,
    "reports": 50,
    "schedules_total": 5,
    "schedules_enabled": 3,
    "historical_tweets": 1000
  }
}
```

---

### 17. Debug Schedules
**GET** `/debug/schedules`

View all schedules including legacy ones (for debugging).

**Response:**
```json
{
  "total_schedules": 5,
  "schedules": [...]
}
```

---

### 18. Cleanup Legacy Schedules
**POST** `/debug/cleanup-legacy-schedules`

Disable schedules without start_datetime.

**Response:**
```json
{
  "success": true,
  "disabled_count": 2,
  "message": "Disabled 2 legacy schedules"
}
```

---

## 📥 File Download Endpoints

### 19. Download Report File
**GET** `/download/<filename>`

Download a report file (txt or json).

**Example:**
```
/download/reports/twitter_report_elonmusk_20260126.txt
```

---

### 20. View Report Content
**GET** `/view-report/<filename>`

View report content as JSON.

**Response:**
```json
{
  "content": "Full report text..."
}
```

---

## 🎯 Quick Reference

### Most Used Endpoints

**Check System Status:**
```bash
curl https://web-twitter-scraper.up.railway.app/health
```

**View Statistics:**
```bash
curl https://web-twitter-scraper.up.railway.app/deep-history/stats
```

**Get Latest Reports:**
```bash
curl https://web-twitter-scraper.up.railway.app/reports
```

**Get Latest Deep History:**
```bash
curl https://web-twitter-scraper.up.railway.app/deep-history?limit=10
```

**Export Data:**
```bash
curl "https://web-twitter-scraper.up.railway.app/deep-history/export?limit=500" > data.csv
```

**Search Historical Data:**
```bash
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "platform": "twitter"}'
```

---

## 📊 Response Codes

- `200` - Success
- `400` - Bad Request (missing parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Server Error

---

## 🔐 Authentication

Currently, no authentication is required. For production use, consider adding:
- API keys
- OAuth
- Rate limiting
- IP whitelisting

---

## 📝 Notes

1. All timestamps are in UTC
2. Data persists in PostgreSQL
3. Pagination is available on list endpoints
4. CSV exports are limited to 1000 records per request
5. Full-text search uses simple LIKE queries (advanced search coming in Phase 2)
6. All POST endpoints require `Content-Type: application/json` header

---

## 🚀 Future Endpoints (Planned)

- `/deep-history/<id>/analyze` - AI analysis of a record
- `/deep-history/trends` - Trend detection
- `/deep-history/timeline` - Time-series data
- `/deep-history/compare` - Compare accounts
- `/ai/summarize` - LLM-powered summaries
- `/ai/topics` - Topic extraction
- `/embeddings/search` - Semantic search

---

## 📚 Related Documentation

- [Deep History API](./DEEP_HISTORY_API.md) - Detailed deep_history documentation
- [User Guide](./USER_GUIDE.md) - Web UI usage guide
- [Database Setup](./DATABASE_SETUP.md) - Database configuration
- [Similar Accounts Feature](./SIMILAR_ACCOUNTS_FEATURE.md) - Lookalike account discovery

---

**Last Updated:** January 27, 2026
**Version:** 2.5
**Base URL:** https://web-twitter-scraper.up.railway.app

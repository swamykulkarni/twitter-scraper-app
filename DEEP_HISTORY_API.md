# Deep History API Documentation

## Overview
The Deep History API provides direct access to all historical scraping data stored in the `deep_history` table. This data is the foundation for AI/ML features and provides rich insights into your social listening activities.

## Base URL
```
https://web-twitter-scraper.up.railway.app
```

## Endpoints

### 1. Get Deep History Records
**GET** `/deep-history`

Get a list of deep_history records with optional filtering and pagination.

**Query Parameters:**
- `platform` (optional): Filter by platform (`twitter` or `reddit`)
- `username` (optional): Filter by specific username
- `scrape_type` (optional): Filter by scrape type (`quick`, `scheduled`, `bulk`, `discovery`)
- `limit` (optional): Number of records to return (default: 50, max: 500)
- `offset` (optional): Pagination offset (default: 0)
- `format` (optional): Response format (`summary` or `full`, default: `summary`)

**Examples:**
```bash
# Get latest 50 records (summary)
https://web-twitter-scraper.up.railway.app/deep-history

# Get Twitter records only
https://web-twitter-scraper.up.railway.app/deep-history?platform=twitter

# Get records for specific user
https://web-twitter-scraper.up.railway.app/deep-history?username=elonmusk

# Get scheduled scrapes only
https://web-twitter-scraper.up.railway.app/deep-history?scrape_type=scheduled

# Get full data (includes raw_json and raw_text)
https://web-twitter-scraper.up.railway.app/deep-history?format=full

# Pagination - get next 50 records
https://web-twitter-scraper.up.railway.app/deep-history?limit=50&offset=50

# Combined filters
https://web-twitter-scraper.up.railway.app/deep-history?platform=twitter&scrape_type=bulk&limit=100
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
      "keywords": ["AI", "Tesla", "SpaceX"],
      "hashtags": ["AI", "ElectricVehicles", "Mars"],
      "mentions": ["Tesla", "SpaceX"],
      "avg_sentiment": 0.75
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "returned": 50,
  "filters": {
    "platform": null,
    "username": null,
    "scrape_type": null
  }
}
```

---

### 2. Get Specific Record
**GET** `/deep-history/<record_id>`

Get a specific deep_history record by ID with full data including raw JSON and text.

**Example:**
```bash
https://web-twitter-scraper.up.railway.app/deep-history/1
```

**Response:**
```json
{
  "success": true,
  "record": {
    "id": 1,
    "report_id": 5,
    "username": "elonmusk",
    "platform": "twitter",
    "scraped_at": "2026-01-26T10:30:00",
    "scrape_type": "quick",
    "total_tweets": 25,
    "total_engagement": 15000,
    "avg_sentiment": 0.75,
    "lead_score": 7,
    "account_type": "Business",
    "keywords": ["AI", "Tesla"],
    "hashtags": ["AI", "ElectricVehicles"],
    "mentions": ["Tesla", "SpaceX"],
    "urls": ["https://tesla.com"],
    "tweet_ids": ["123456789", "987654321"],
    "account_snapshot": {
      "followers_count": 150000000,
      "following_count": 500,
      "verified": true,
      "description": "CEO of Tesla and SpaceX"
    },
    "raw_json": {
      "tweets": [...],
      "account_info": {...}
    },
    "raw_text": "Full report text...",
    "raw_csv": null,
    "topics": null,
    "ai_analysis": null,
    "ai_summary": null,
    "filters_used": {
      "min_likes": 100
    }
  }
}
```

---

### 3. Get Statistics
**GET** `/deep-history/stats`

Get comprehensive statistics about your deep_history data.

**Example:**
```bash
https://web-twitter-scraper.up.railway.app/deep-history/stats
```

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
      },
      {
        "username": "salesforce",
        "platform": "twitter",
        "scrape_count": 12
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

### 4. Export to CSV
**GET** `/deep-history/export`

Export deep_history data as CSV file.

**Query Parameters:**
- `platform` (optional): Filter by platform
- `username` (optional): Filter by username
- `scrape_type` (optional): Filter by scrape type
- `limit` (optional): Number of records (default: 100, max: 1000)

**Examples:**
```bash
# Export all records (up to 100)
https://web-twitter-scraper.up.railway.app/deep-history/export

# Export Twitter records only
https://web-twitter-scraper.up.railway.app/deep-history/export?platform=twitter

# Export specific user's data
https://web-twitter-scraper.up.railway.app/deep-history/export?username=elonmusk

# Export 500 records
https://web-twitter-scraper.up.railway.app/deep-history/export?limit=500
```

**Response:**
Downloads a CSV file with columns:
- id
- username
- platform
- scraped_at
- scrape_type
- total_tweets
- total_engagement
- lead_score
- account_type
- keywords
- hashtags
- mentions
- avg_sentiment

---

### 5. Full-Text Search
**POST** `/search-history`

Search across all deep_history records using full-text search.

**Request Body:**
```json
{
  "query": "AI machine learning",
  "platform": "twitter",
  "limit": 50
}
```

**Example:**
```bash
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "AI machine learning", "platform": "twitter"}'
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
      "scraped_at": "2026-01-26T10:30:00",
      "total_tweets": 25,
      "keywords": ["AI", "machine learning"],
      "ai_summary": "Account focuses on AI and ML topics..."
    }
  ],
  "total": 15,
  "query": "AI machine learning"
}
```

---

## Use Cases

### 1. Data Analysis
```bash
# Get all your data for analysis
curl "https://web-twitter-scraper.up.railway.app/deep-history?limit=500&format=full" > data.json
```

### 2. Track Account Over Time
```bash
# See how an account has evolved
curl "https://web-twitter-scraper.up.railway.app/deep-history?username=salesforce"
```

### 3. Monitor Scraping Activity
```bash
# Check your scraping stats
curl "https://web-twitter-scraper.up.railway.app/deep-history/stats"
```

### 4. Export for ML Training
```bash
# Export data for training models
curl "https://web-twitter-scraper.up.railway.app/deep-history/export?limit=1000" > training_data.csv
```

### 5. Search Historical Data
```bash
# Find all mentions of a topic
curl -X POST "https://web-twitter-scraper.up.railway.app/search-history" \
  -H "Content-Type: application/json" \
  -d '{"query": "manufacturing GCC"}'
```

---

## Data Fields

### Summary Format
- `id`: Unique record ID
- `username`: Account username
- `platform`: Platform (twitter/reddit)
- `scraped_at`: When the scrape occurred
- `scrape_type`: Type of scrape (quick/scheduled/bulk/discovery)
- `total_tweets`: Number of tweets/posts collected
- `total_engagement`: Total engagement (likes + retweets + replies)
- `lead_score`: Quality score (0-7)
- `account_type`: Account classification
- `keywords`: Keywords used in search
- `hashtags`: Extracted hashtags
- `mentions`: Extracted mentions
- `avg_sentiment`: Average sentiment score

### Full Format (includes all above plus)
- `raw_json`: Complete structured data
- `raw_text`: Full report text
- `account_snapshot`: Account metrics at time of scrape
- `tweet_ids`: Array of tweet/post IDs
- `urls`: Extracted URLs
- `topics`: AI-extracted topics (future)
- `ai_analysis`: AI analysis results (future)
- `ai_summary`: Natural language summary (future)
- `filters_used`: Filters applied during scrape

---

## Rate Limiting

Currently no rate limiting is applied. For production use, consider:
- Caching responses
- Limiting export sizes
- Adding authentication

---

## Future Enhancements

1. **AI Analysis Endpoints**
   - `/deep-history/<id>/analyze` - Run AI analysis on a record
   - `/deep-history/trends` - Detect trends across records

2. **Advanced Filtering**
   - Date range filtering
   - Engagement thresholds
   - Sentiment filtering

3. **Aggregations**
   - `/deep-history/timeline` - Time-series data
   - `/deep-history/compare` - Compare accounts

4. **Webhooks**
   - Real-time notifications when new data is added

---

## Integration Examples

### Python
```python
import requests

# Get latest records
response = requests.get('https://web-twitter-scraper.up.railway.app/deep-history')
data = response.json()

for record in data['records']:
    print(f"{record['username']}: {record['total_tweets']} tweets")
```

### JavaScript
```javascript
// Get stats
fetch('https://web-twitter-scraper.up.railway.app/deep-history/stats')
  .then(res => res.json())
  .then(data => console.log(data.stats));
```

### cURL
```bash
# Search for AI-related content
curl -X POST https://web-twitter-scraper.up.railway.app/search-history \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "limit": 100}'
```

---

## Notes

- All timestamps are in UTC
- Data is stored permanently in PostgreSQL
- Export CSV is limited to 1000 records per request
- Full-text search requires PostgreSQL (falls back to simple search on SQLite)
- All endpoints return JSON except `/deep-history/export` which returns CSV

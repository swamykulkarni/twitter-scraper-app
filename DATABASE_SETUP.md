# Database Setup Guide

## Why Database is Required

Railway uses **ephemeral storage** - files are deleted on every restart. A database provides:
- ✅ Persistent schedules across deployments
- ✅ Historical tweet data that never gets lost
- ✅ Report history accessible anytime
- ✅ Proper data management and querying

## Railway PostgreSQL Setup (Recommended)

### Step 1: Add PostgreSQL to Your Railway Project

1. Go to your Railway project dashboard
2. Click "New" → "Database" → "Add PostgreSQL"
3. Railway will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Connect it to your app

### Step 2: Redeploy Your App

The app will automatically:
- Detect the `DATABASE_URL` environment variable
- Create all necessary tables on first run
- Start using PostgreSQL for persistence

### Step 3: Verify It's Working

1. Generate a report
2. Refresh the page
3. Go to "Report History" tab
4. Your report should still be there!

## Local Development Setup

For local testing, the app automatically uses SQLite (no setup needed).

If you want to use PostgreSQL locally:

1. Install PostgreSQL:
```bash
brew install postgresql  # macOS
# or
sudo apt-get install postgresql  # Linux
```

2. Create a database:
```bash
createdb twitter_scraper
```

3. Set environment variable in `.env`:
```
DATABASE_URL=postgresql://localhost/twitter_scraper
```

## Database Schema

The app creates three tables:

### 1. `schedules`
Stores scheduled scraping configurations
- username, keywords, frequency, time, day
- enabled status, last_run timestamp

### 2. `reports`
Stores generated reports
- username, keywords, tweet_count
- account_type, lead_score
- full report_content (text)
- tweets_data (JSON)
- filters used

### 3. `historical_tweets`
Stores individual tweets for historical tracking
- tweet_id (unique), username, text
- created_at, full tweet_data (JSON)
- collected_at timestamp

## Benefits of Database Persistence

### Before (File-based):
- ❌ Schedules lost on restart
- ❌ Reports deleted on redeploy
- ❌ Historical data disappears
- ❌ No way to query old data

### After (Database):
- ✅ Schedules persist forever
- ✅ All reports saved and searchable
- ✅ Historical tweets accumulate over time
- ✅ Query by username, date, keywords
- ✅ Export data anytime

## Troubleshooting

### "No module named 'psycopg2'"
Run: `pip install -r requirements.txt`

### "Database connection failed"
Check that Railway PostgreSQL is added to your project

### "Tables not found"
The app creates tables automatically on first run. Check logs for errors.

### Local SQLite file location
`twitter_scraper.db` in the app root directory

## Data Migration

If you have existing JSON files, you can migrate them:

1. The app will continue to work with SQLite locally
2. On Railway, it automatically switches to PostgreSQL
3. Old reports in files won't be migrated automatically
4. Re-run important scrapes to save them to database

## Cost

Railway PostgreSQL:
- **Free tier**: 512MB storage, 1GB RAM
- **Pro tier**: $5/month for 8GB storage
- Perfect for this use case (thousands of reports)

## Next Steps

1. Add PostgreSQL to Railway project
2. Redeploy app
3. Test by creating a schedule
4. Refresh page - schedule should persist!
5. Generate reports - they'll be saved forever

Your data is now safe and persistent! 🎉

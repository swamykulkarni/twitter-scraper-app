# Robust Scheduler Implementation

## Overview
Replaced the in-memory Python scheduler with **Railway Cron Jobs** for reliable, persistent scheduling that survives container restarts.

## Problem with Old System
- ❌ Scheduler ran as background thread in Flask app
- ❌ Stopped when container restarted (deployments, crashes, etc.)
- ❌ No way to recover without manual intervention
- ❌ Lost 6 days of scheduled scrapes (Jan 27 - Feb 2)

## New System Architecture

### **External Cron Job (Railway)**
```
Railway Cron → Calls /cron/run-schedules → Executes due schedules
     ↓              (every hour)                      ↓
Runs independently                            Saves to database
of container restarts                         Updates next_run
```

### **How It Works**

1. **Railway Cron Job** runs every hour (at minute 0)
2. **Calls** `POST /cron/run-schedules` endpoint
3. **Endpoint checks** database for schedules where `next_run <= now + 1 hour`
4. **Executes** each due schedule
5. **Updates** `last_run` and calculates new `next_run`
6. **Saves** reports to database and deep_history

## Benefits

✅ **Survives Restarts** - Cron runs independently of app container
✅ **Reliable** - Railway manages cron execution
✅ **Persistent** - Schedule state stored in PostgreSQL
✅ **Recoverable** - Missed runs are caught on next cron execution
✅ **Scalable** - Can add more cron jobs for different frequencies
✅ **Monitorable** - Cron endpoint returns execution results

## Configuration

### Railway Cron Job
Defined in `railway.toml`:
```toml
[[crons]]
schedule = "0 * * * *"  # Every hour at minute 0
command = "curl -X POST http://localhost:$PORT/cron/run-schedules"
```

### Cron Schedule Format
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

**Examples:**
- `0 * * * *` - Every hour at minute 0
- `*/15 * * * *` - Every 15 minutes
- `0 0 * * *` - Daily at midnight
- `0 9 * * 1` - Every Monday at 9 AM

## API Endpoint

### POST `/cron/run-schedules`

Executes all scheduled scrapes that are due.

**Response:**
```json
{
  "success": true,
  "timestamp": "2026-02-02T12:00:00",
  "results": {
    "executed": [
      {
        "schedule_id": 1,
        "username": "abhirammodak",
        "tweet_count": 25,
        "next_run": "2026-02-03T16:30:00"
      }
    ],
    "skipped": [
      {
        "schedule_id": 2,
        "username": "elonmusk",
        "reason": "Not yet time (next_run: 2026-02-02T18:00:00)"
      }
    ],
    "errors": []
  },
  "summary": {
    "executed": 1,
    "skipped": 1,
    "errors": 0
  }
}
```

## How Schedules Work Now

### Creating a Schedule (UI)
1. User creates schedule in "Scheduled Scraping" tab
2. Schedule saved to PostgreSQL with `next_run` time
3. Railway cron checks every hour
4. When `next_run` is reached, scrape executes
5. New `next_run` calculated based on frequency

### Schedule Frequencies
- **Once**: Runs once, then disabled
- **Hourly**: Runs every hour from start time
- **Daily**: Runs every day at specified time
- **Weekly**: Runs every week on specified day

### Next Run Calculation
```python
if frequency == 'hourly':
    next_run = now + timedelta(hours=1)
elif frequency == 'daily':
    next_run = now + timedelta(days=1)
elif frequency == 'weekly':
    next_run = now + timedelta(weeks=1)
```

## Monitoring

### Check Cron Execution
```bash
# View recent executions
curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules
```

### Check Schedule Status
```bash
# View all schedules
curl https://web-twitter-scraper.up.railway.app/schedules

# View debug info
curl https://web-twitter-scraper.up.railway.app/debug/schedules
```

### Check Recent Scrapes
```bash
# View deep_history stats
curl https://web-twitter-scraper.up.railway.app/deep-history/stats

# View latest reports
curl https://web-twitter-scraper.up.railway.app/reports
```

## Troubleshooting

### Schedules Not Running

**Check 1: Is cron job configured?**
```bash
# In Railway dashboard, check "Cron" tab
# Should see: "0 * * * *" schedule
```

**Check 2: Is next_run set correctly?**
```bash
curl https://web-twitter-scraper.up.railway.app/schedules
# Check "next_run" field for each schedule
```

**Check 3: Manual trigger**
```bash
# Manually trigger cron endpoint
curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules
```

**Check 4: View Railway logs**
```
# In Railway dashboard, view deployment logs
# Look for "[CRON]" messages
```

### Schedule Shows Wrong Time

**Issue**: Times are in UTC, not local time

**Solution**: 
- All schedules run in UTC
- For IST (UTC+5:30), subtract 5:30 from desired time
- Example: Want 10:00 PM IST → Set 4:30 PM UTC

See [TIMEZONE_GUIDE.md](./TIMEZONE_GUIDE.md) for conversion table.

## Migration from Old System

### What Changed
- ❌ Removed: `scheduler.py` background thread
- ✅ Added: `/cron/run-schedules` endpoint
- ✅ Added: `railway.toml` cron configuration
- ✅ Kept: All existing schedules in database
- ✅ Kept: UI for managing schedules

### Existing Schedules
All existing schedules continue to work:
- Schedule data stored in PostgreSQL (unchanged)
- `next_run` times preserved
- No data loss
- Just executed by cron instead of background thread

## Future Enhancements

### Multiple Cron Frequencies
Add more cron jobs for different frequencies:

```toml
# Hourly scrapes
[[crons]]
schedule = "0 * * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules?frequency=hourly"

# Daily scrapes
[[crons]]
schedule = "0 0 * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules?frequency=daily"

# Weekly scrapes
[[crons]]
schedule = "0 0 * * 0"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules?frequency=weekly"
```

### Retry Failed Scrapes
Add retry logic for failed scrapes:
```python
if error:
    schedule.retry_count += 1
    if schedule.retry_count < 3:
        schedule.next_run = now + timedelta(minutes=15)  # Retry in 15 min
```

### Notifications
Send notifications when scrapes complete:
- Email reports
- Slack/Discord webhooks
- SMS alerts

### Health Monitoring
Add monitoring endpoint:
```python
@app.route('/cron/health')
def cron_health():
    # Check if cron has run recently
    # Alert if no runs in last 2 hours
```

## Comparison: Old vs New

| Feature | Old System | New System |
|---------|-----------|------------|
| **Reliability** | ❌ Stops on restart | ✅ Always runs |
| **Persistence** | ❌ In-memory | ✅ PostgreSQL |
| **Recovery** | ❌ Manual restart | ✅ Automatic |
| **Monitoring** | ❌ No visibility | ✅ API endpoint |
| **Scalability** | ❌ Single thread | ✅ Multiple crons |
| **Maintenance** | ❌ High | ✅ Low |

## Testing

### Test Cron Endpoint
```bash
# Create a test schedule
curl -X POST https://web-twitter-scraper.up.railway.app/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_account",
    "keywords": "test",
    "frequency": "once",
    "start_datetime": "2026-02-02T12:00:00"
  }'

# Manually trigger cron
curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules

# Check if it ran
curl https://web-twitter-scraper.up.railway.app/reports
```

### Verify Cron Schedule
```bash
# In Railway dashboard:
# 1. Go to your service
# 2. Click "Cron" tab
# 3. Should see "0 * * * *" schedule
# 4. Check "Last Run" timestamp
```

## Notes

- Cron runs every hour, so schedules execute within 1 hour of `next_run` time
- For more frequent execution, change cron schedule to `*/15 * * * *` (every 15 min)
- Cron endpoint is idempotent - safe to call multiple times
- Failed scrapes don't block other schedules
- All scrape data saved to `deep_history` table

## Related Documentation

- [API Endpoints](./API_ENDPOINTS.md) - All API endpoints
- [Timezone Guide](./TIMEZONE_GUIDE.md) - UTC time conversion
- [Database Setup](./DATABASE_SETUP.md) - PostgreSQL configuration
- [User Guide](./USER_GUIDE.md) - How to use the UI

---

**Last Updated:** February 2, 2026
**Version:** 2.6
**Status:** ✅ Production Ready

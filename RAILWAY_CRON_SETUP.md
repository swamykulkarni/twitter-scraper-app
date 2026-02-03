# Railway Cron Setup Guide

## Quick Setup (5 minutes)

Railway should automatically detect the `railway.toml` file and configure the cron job. But if it doesn't, follow these steps:

### Step 1: Verify Deployment
1. Go to Railway dashboard: https://railway.app
2. Select your project: `social-listening-platform`
3. Wait for deployment to complete (2-3 minutes)

### Step 2: Check Cron Configuration
1. In Railway dashboard, click on your service
2. Look for "Cron" tab or "Cron Jobs" section
3. You should see:
   - **Schedule**: `0 * * * *` (every hour)
   - **Command**: `curl -X POST http://localhost:$PORT/cron/run-schedules`
   - **Status**: Active

### Step 3: Manual Test (Optional)
Test the cron endpoint manually:

```bash
curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules
```

Expected response:
```json
{
  "success": true,
  "timestamp": "2026-02-02T12:00:00",
  "results": {
    "executed": [...],
    "skipped": [...],
    "errors": []
  }
}
```

### Step 4: Verify Schedules Are Running
Wait 1 hour, then check:

```bash
curl https://web-twitter-scraper.up.railway.app/deep-history/stats
```

The `last_scrape` date should be recent (within last hour).

## If Cron Doesn't Auto-Configure

If Railway doesn't automatically set up the cron job:

### Option A: Use Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Add cron job
railway cron add "0 * * * *" "curl -X POST http://localhost:\$PORT/cron/run-schedules"
```

### Option B: Manual Configuration in Dashboard
1. Go to Railway dashboard
2. Click your service
3. Go to "Settings" → "Cron Jobs"
4. Click "Add Cron Job"
5. Enter:
   - **Schedule**: `0 * * * *`
   - **Command**: `curl -X POST http://localhost:$PORT/cron/run-schedules`
6. Click "Save"

### Option C: Use GitHub Actions (Alternative)
If Railway cron doesn't work, use GitHub Actions:

Create `.github/workflows/scheduler.yml`:
```yaml
name: Run Scheduled Scrapes

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Manual trigger

jobs:
  run-schedules:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cron Endpoint
        run: |
          curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules
```

## Monitoring

### Check Cron Execution
```bash
# View Railway logs
railway logs

# Look for "[CRON]" messages
```

### Check Schedule Status
```bash
# View all schedules
curl https://web-twitter-scraper.up.railway.app/schedules

# Check which ones ran recently
# Look at "last_run" field
```

### Check Recent Scrapes
```bash
# View stats
curl https://web-twitter-scraper.up.railway.app/deep-history/stats

# View latest reports
curl https://web-twitter-scraper.up.railway.app/reports
```

## Troubleshooting

### Cron Not Running

**Problem**: No scrapes after 1 hour

**Solution**:
1. Check Railway logs for errors
2. Manually trigger: `curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules`
3. Check response for errors
4. Verify schedules have `next_run` set: `curl https://web-twitter-scraper.up.railway.app/schedules`

### Cron Running But No Scrapes

**Problem**: Cron executes but schedules don't run

**Possible causes**:
1. **next_run in future**: Schedules not due yet
2. **Schedules disabled**: Check `enabled` field
3. **Twitter API error**: Check Railway logs for API errors
4. **Database connection**: Check `/health` endpoint

**Solution**:
```bash
# Check schedules
curl https://web-twitter-scraper.up.railway.app/debug/schedules

# Check health
curl https://web-twitter-scraper.up.railway.app/health

# Manual trigger to see errors
curl -X POST https://web-twitter-scraper.up.railway.app/cron/run-schedules
```

### Wrong Execution Time

**Problem**: Schedules run at wrong time

**Cause**: Timezone confusion (UTC vs IST)

**Solution**:
- All times are UTC
- For IST (UTC+5:30), subtract 5:30 from desired time
- Example: Want 10:00 PM IST → Set 4:30 PM UTC

See [TIMEZONE_GUIDE.md](./TIMEZONE_GUIDE.md)

## Changing Cron Frequency

### Every 15 Minutes
Edit `railway.toml`:
```toml
[[crons]]
schedule = "*/15 * * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules"
```

### Every 30 Minutes
```toml
[[crons]]
schedule = "*/30 * * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules"
```

### Daily at Midnight UTC
```toml
[[crons]]
schedule = "0 0 * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules"
```

After editing, commit and push:
```bash
git add railway.toml
git commit -m "Update cron frequency"
git push origin main
```

## Benefits of This System

✅ **Reliable**: Survives container restarts
✅ **Persistent**: Schedule state in PostgreSQL
✅ **Monitorable**: API endpoint shows execution status
✅ **Scalable**: Can add multiple cron jobs
✅ **Recoverable**: Missed runs caught on next execution

## Next Steps

1. ✅ Deploy to Railway (done automatically)
2. ✅ Verify cron is configured
3. ⏳ Wait 1 hour for first execution
4. ✅ Check deep_history/stats for new scrapes
5. ✅ Monitor Railway logs for "[CRON]" messages

## Support

If you encounter issues:
1. Check Railway logs
2. Test cron endpoint manually
3. Verify schedules in database
4. Check health endpoint
5. Review [ROBUST_SCHEDULER.md](./ROBUST_SCHEDULER.md)

---

**Status**: ✅ Deployed
**Cron Schedule**: Every hour (0 * * * *)
**Endpoint**: POST /cron/run-schedules
**Monitoring**: /deep-history/stats

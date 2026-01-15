# Persistence Checklist - CRITICAL

## ⚠️ IMPORTANT: Persistence Requires PostgreSQL

Without PostgreSQL properly connected, **ALL DATA IS LOST** on every deployment/restart.

## Quick Check: Is PostgreSQL Connected?

Visit: `https://your-app-url.railway.app/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "type": "PostgreSQL",
    "url_set": true
  }
}
```

**Bad Response (No Persistence):**
```json
{
  "database": {
    "type": "SQLite",
    "url_set": false
  }
}
```

## How to Fix: Connect PostgreSQL to Railway

### Step 1: Verify PostgreSQL Service Exists

1. Go to Railway dashboard
2. Open your project
3. You should see TWO services:
   - Your web app
   - PostgreSQL database

If you only see one service, PostgreSQL is NOT added!

### Step 2: Add PostgreSQL (if missing)

1. Click "New" in Railway project
2. Select "Database"
3. Choose "Add PostgreSQL"
4. Wait for provisioning

### Step 3: Connect Database to Web Service

Railway should auto-connect, but verify:

1. Click on your **PostgreSQL service**
2. Go to "Variables" tab
3. Copy the `DATABASE_URL` value
4. Click on your **web service**
5. Go to "Variables" tab
6. Verify `DATABASE_URL` exists with the same value

### Step 4: Check Variable Format

The `DATABASE_URL` should look like:
```
postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway
```

**Common Issues:**
- ❌ Variable is empty
- ❌ Variable uses `postgres://` instead of `postgresql://` (app handles this)
- ❌ Variable points to external URL instead of internal

### Step 5: Redeploy

After ensuring DATABASE_URL is set:

1. Go to your web service
2. Click "Deployments"
3. Click "Deploy" or wait for auto-deploy
4. Check logs for:
   ```
   [DATABASE] Using PostgreSQL database
   [DATABASE] ✓ Database engine created successfully
   Database initialized successfully
   ```

## Verification Steps

### 1. Check Health Endpoint

```bash
curl https://your-app-url.railway.app/health
```

Should show `"type": "PostgreSQL"`

### 2. Test Schedule Persistence

1. Create a schedule
2. Refresh page
3. Schedule should still be there

### 3. Test Report Persistence

1. Generate a report
2. Go to "Report History" tab
3. Report should be saved
4. Refresh page
5. Report should still be there

### 4. Check Logs

```bash
railway logs
```

Look for:
- `[DATABASE] Using PostgreSQL database` ✓
- NOT `Using SQLite for local development` ✗

## Why Persistence Breaks

### Common Causes:

1. **PostgreSQL not added to Railway**
   - Solution: Add PostgreSQL service

2. **DATABASE_URL not set**
   - Solution: Verify environment variable exists

3. **Wrong DATABASE_URL format**
   - Solution: Should be `postgresql://` not `postgres://`

4. **Database service stopped**
   - Solution: Check PostgreSQL service is running

5. **Connection timeout**
   - Solution: Check Railway service health

## Making Persistence Bulletproof

### 1. Always Check Logs After Deploy

```bash
railway logs --tail 20
```

Look for database connection confirmation.

### 2. Add Health Check to CI/CD

After each deployment, automatically check `/health` endpoint.

### 3. Monitor Database Status

Set up alerts if database type switches to SQLite.

### 4. Regular Backups

Even with PostgreSQL, take regular backups:

```bash
railway run pg_dump > backup.sql
```

## Emergency Recovery

If persistence is broken:

1. **Check `/health` endpoint** - Identify the issue
2. **Check Railway logs** - Look for database errors
3. **Verify DATABASE_URL** - Ensure it's set correctly
4. **Restart services** - Sometimes fixes connection issues
5. **Re-add PostgreSQL** - Last resort if database is corrupted

## Contact Points

- Railway Status: https://status.railway.app/
- Railway Docs: https://docs.railway.app/
- PostgreSQL Docs: https://www.postgresql.org/docs/

## Quick Commands

```bash
# Check if DATABASE_URL is set
railway variables

# View logs
railway logs

# Restart service
railway service restart

# Check database connection
curl https://your-app-url/health
```

---

**REMEMBER:** Without PostgreSQL properly connected, you're running on ephemeral storage and ALL DATA WILL BE LOST on every restart!

# 🚨 QUICK FIX: PostgreSQL Not Connecting

## The Problem
Your Railway logs show SQLite instead of PostgreSQL, meaning DATABASE_URL isn't being passed to your app.

## The Solution (5 minutes)

### Step 1: Delete Manual Variable
1. Go to Railway → Your web service → Variables tab
2. Find `DATABASE_URL` 
3. Delete it (trash icon)

### Step 2: Link PostgreSQL Service
1. Stay in Variables tab
2. Click "+ New Variable"
3. Click "Add Reference" (or look for service reference option)
4. Select your PostgreSQL service
5. Select `DATABASE_URL` variable
6. Should create: `${{Postgres.DATABASE_URL}}`

### Step 3: Wait for Auto-Deploy
Railway will automatically redeploy (1-2 minutes)

### Step 4: Check Logs
Look for:
```
[DATABASE] Using PostgreSQL database ✅
```

NOT:
```
[DATABASE] Using SQLite ❌
```

### Step 5: Test
Visit: `https://your-app.railway.app/health`

Should show:
```json
{
  "database": {
    "type": "PostgreSQL"
  }
}
```

## Still Not Working?

The new logs will show ALL database-related environment variables Railway is passing. Check the deployment logs after this push completes and look for:

```
[DATABASE] Environment variables containing 'DATABASE' or 'POSTGRES':
```

This will tell us exactly what Railway is providing.

## Need More Help?

See `RAILWAY_POSTGRES_FIX.md` for detailed troubleshooting.

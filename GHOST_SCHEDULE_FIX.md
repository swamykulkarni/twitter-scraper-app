# Ghost Schedule Fix

## The Problem

You had a "ghost schedule" - a schedule running daily but not showing in the UI. This was caused by a **legacy schedule** from before the database migration that doesn't have a `start_datetime` field.

## What Was Fixed

1. **UI Filter**: Schedules without `start_datetime` are now hidden from the UI
2. **Scheduler Filter**: Legacy schedules are skipped when loading schedules
3. **Debug Endpoints**: Added tools to diagnose and clean up legacy schedules

## How to Fix Your Ghost Schedule

### Step 1: Check for Legacy Schedules

Visit this URL in your browser:
```
https://social-listening-platform-production.up.railway.app/debug/schedules
```

You'll see all schedules in the database. Look for schedules with:
- `"has_start_datetime": false`
- `"enabled": true`

These are your ghost schedules!

### Step 2: Clean Up Legacy Schedules

Use this command (or visit in browser with POST):
```bash
curl -X POST https://social-listening-platform-production.up.railway.app/debug/cleanup-legacy-schedules
```

Or use a tool like Postman to send a POST request to:
```
https://social-listening-platform-production.up.railway.app/debug/cleanup-legacy-schedules
```

This will:
- Find all enabled schedules without `start_datetime`
- Disable them
- Return a list of disabled schedule IDs

### Step 3: Verify

1. Check `/debug/schedules` again - legacy schedules should now show `"enabled": false`
2. Wait 24 hours - no more ghost reports should appear
3. Check "Report History" - no new reports from the ghost schedule

## Alternative: Manual Database Cleanup

If you have database access, you can run this SQL:

```sql
-- See all schedules
SELECT id, username, frequency, enabled, start_datetime, last_run 
FROM schedules;

-- Disable legacy schedules
UPDATE schedules 
SET enabled = false 
WHERE start_datetime IS NULL AND enabled = true;
```

## Why This Happened

When we added the `start_datetime` field to the database schema, existing schedules didn't have this field (it was `NULL`). The old scheduler code still ran these schedules, but the new UI couldn't display them properly.

## Prevention

Going forward:
- All new schedules require `start_datetime`
- The scheduler skips schedules without `start_datetime`
- The UI filters out legacy schedules
- No more ghost schedules can be created

## Debug Endpoints

### `/debug/schedules` (GET)
Shows all schedules in the database with full details:
- ID, username, keywords
- Enabled status
- start_datetime (if exists)
- last_run, next_run
- `has_start_datetime` flag

### `/debug/cleanup-legacy-schedules` (POST)
Automatically disables all legacy schedules without `start_datetime`.

Returns:
```json
{
  "success": true,
  "message": "Disabled 1 legacy schedule(s)",
  "disabled_schedule_ids": [123]
}
```

## Verification

After cleanup, check `/health` endpoint:
```
https://social-listening-platform-production.up.railway.app/health
```

Should show:
```json
{
  "data": {
    "schedules_total": X,
    "schedules_enabled": Y
  }
}
```

If `schedules_enabled` is 0 and you have no active schedules, the ghost is gone! ✅

## Need Help?

If the ghost schedule persists after cleanup:
1. Check deployment logs for scheduler warnings
2. Verify the cleanup endpoint returned success
3. Check if new reports are still appearing in Report History
4. Share the output of `/debug/schedules` for further diagnosis

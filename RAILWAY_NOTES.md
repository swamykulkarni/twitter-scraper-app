# Railway Deployment Notes

## Important: Ephemeral Storage

Railway uses **ephemeral storage**, which means:
- Files are deleted when the app restarts/redeploys
- Schedules stored in `schedules.json` will be lost on restart
- Historical data in `historical_data/` will be lost on restart

## Solutions for Persistent Storage

### Option 1: Use Railway Database (Recommended)
Add a PostgreSQL database to your Railway project:
1. Go to your Railway project
2. Click "New" → "Database" → "Add PostgreSQL"
3. Update the app to use database instead of JSON files

### Option 2: Use External Storage
- AWS S3
- Google Cloud Storage
- Cloudflare R2

### Option 3: Use Railway Volumes (When Available)
Railway is working on persistent volumes feature.

## Current Workaround

For now, schedules need to be re-added after each deployment. To minimize this:
1. Keep a list of your schedules in a separate document
2. Re-add them after deployment
3. Consider using the CLI to automate schedule creation

## Environment Variables Set

- `TWITTER_BEARER_TOKEN` - Your Twitter API token (persists across deployments)

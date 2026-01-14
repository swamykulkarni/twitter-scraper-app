# Deploy to Railway

## Quick Deploy Steps

### Option 1: Deploy via Railway CLI

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Initialize and deploy:
```bash
railway init
railway up
```

4. Add environment variable:
```bash
railway variables set TWITTER_BEARER_TOKEN="your_bearer_token_here"
```

5. Get your public URL:
```bash
railway domain
```

### Option 2: Deploy via GitHub

1. Initialize git repository (if not already):
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Push to GitHub:
```bash
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

3. Go to Railway Dashboard:
   - Visit https://railway.app/
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect and deploy

4. Add Environment Variable:
   - Go to your project settings
   - Click "Variables"
   - Add: `TWITTER_BEARER_TOKEN` = `your_bearer_token`

5. Generate Domain:
   - Go to "Settings" tab
   - Click "Generate Domain"
   - Your app will be live at the generated URL

## Environment Variables Required

- `TWITTER_BEARER_TOKEN`: Your Twitter API Bearer Token

## Notes

- Railway automatically detects Python apps
- The app uses gunicorn for production
- Reports are stored temporarily (Railway has ephemeral storage)
- Free tier includes 500 hours/month

# Reddit API Setup Guide

## Getting Reddit API Credentials

To use Reddit scraping, you need to create a Reddit app and get API credentials.

### Step 1: Create a Reddit Account

If you don't have one, create a Reddit account at https://www.reddit.com/register

### Step 2: Create a Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Scroll to the bottom and click **"create another app..."** or **"are you a developer? create an app..."**
3. Fill in the form:
   - **name**: Social Listening Platform (or any name you want)
   - **App type**: Select **"script"**
   - **description**: (optional) Lead generation and market research tool
   - **about url**: (optional) Leave blank
   - **redirect uri**: http://localhost:8080 (required but not used)
4. Click **"create app"**

### Step 3: Get Your Credentials

After creating the app, you'll see:

```
personal use script
[THIS IS YOUR CLIENT_ID - a string like: abc123XYZ456]

secret
[THIS IS YOUR CLIENT_SECRET - a longer string]
```

### Step 4: Add to .env File

1. Open your `.env` file (or create one from `.env.example`)
2. Add these lines:

```env
# Reddit API Credentials
REDDIT_CLIENT_ID=abc123XYZ456
REDDIT_CLIENT_SECRET=your_secret_here_longer_string
REDDIT_USER_AGENT=SocialListeningPlatform/1.0
```

**Important:**
- `REDDIT_CLIENT_ID` is the short string under "personal use script"
- `REDDIT_CLIENT_SECRET` is the longer string under "secret"
- `REDDIT_USER_AGENT` can stay as is (identifies your app to Reddit)

### Step 5: Add to Railway

1. Go to Railway dashboard
2. Click on your web service
3. Go to **"Variables"** tab
4. Add three new variables:
   - `REDDIT_CLIENT_ID` = (your client ID)
   - `REDDIT_CLIENT_SECRET` = (your client secret)
   - `REDDIT_USER_AGENT` = SocialListeningPlatform/1.0
5. Railway will auto-redeploy

### Step 6: Test

1. Go to your app
2. Click **"Reddit Scraping"** tab
3. Enter a subreddit (e.g., "startups")
4. Add keywords (optional)
5. Click **"Generate Report"**

## Reddit API Limits

**Free Tier:**
- 60 requests per minute
- 100 posts per request
- No cost

**What you can scrape:**
- Public posts from any subreddit
- Post titles, content, scores, comments count
- Author information
- Timestamps and links

**What you CANNOT scrape:**
- Private subreddits (unless you're a member)
- Deleted posts
- Shadowbanned content

## Troubleshooting

### Error: "Reddit API credentials not found"

**Solution:** Make sure you added the credentials to your `.env` file (local) or Railway variables (production).

### Error: "403 Forbidden"

**Solution:** 
- Check your `REDDIT_USER_AGENT` is set correctly
- Make sure your credentials are correct
- Reddit may be rate limiting - wait a minute and try again

### Error: "Subreddit not found"

**Solution:**
- Check the subreddit name is correct (without r/)
- Make sure the subreddit is public
- Try a popular subreddit like "startups" or "technology"

### No posts found

**Solution:**
- Try a different time filter (week, month, all)
- Remove keywords to get all posts
- Check if the subreddit is active

## Popular Subreddits for Lead Generation

**B2B/SaaS:**
- startups
- SaaS
- Entrepreneur
- smallbusiness
- marketing

**Tech:**
- technology
- programming
- webdev
- artificial

**Industry-Specific:**
- sales
- consulting
- freelance
- digitalnomad

## Best Practices

1. **Start broad:** Use popular subreddits first to test
2. **Use time filters:** "week" or "month" for recent, relevant content
3. **Combine keywords:** Use 2-3 specific keywords for better targeting
4. **Check engagement:** High score + comments = quality leads
5. **Respect rate limits:** Don't scrape too frequently

## Example Searches

**Finding SaaS leads:**
- Subreddit: "SaaS"
- Keywords: "looking for, need, recommend"
- Time filter: week

**Market research:**
- Subreddit: "startups"
- Keywords: "AI, automation, B2B"
- Time filter: month

**Competitor analysis:**
- Subreddit: "technology"
- Keywords: "[competitor name], alternative"
- Time filter: month

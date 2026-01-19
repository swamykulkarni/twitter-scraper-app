# Reddit Scraping Feature Summary

## What's New

Added complete Reddit scraping functionality to your Social Listening Platform with a separate dedicated tab.

## Features

### 1. Reddit Scraping Tab
- New tab in the UI: "Reddit Scraping"
- Search posts from any public subreddit
- Keyword filtering (optional)
- Time filters: hour, day, week, month, year, all time
- Minimum keyword mentions threshold

### 2. Data Collection
- Post titles and content
- Author information
- Engagement metrics (score, upvote ratio, comments)
- Timestamps and permalinks
- Subreddit information (subscribers, description)

### 3. Analysis Features
- **Engagement Scoring**: Weighted formula (Score×1 + Comments×3 + Upvote Ratio×100)
- **Sentiment Analysis**: Positive/Negative/Neutral detection
- **Opportunity Signals**: Detects buying intent keywords ("looking for", "need", "recommend", etc.)
- **Keyword Ranking**: Shows most mentioned keywords with frequency
- **Top Posts**: Highlights top 5 posts by engagement

### 4. Reports
- Comprehensive text reports with all analysis
- JSON export with raw data
- View in-browser with scrollable modal
- Download options for both formats
- Saved to database (persists across deployments)

### 5. Database Integration
- Reports stored in PostgreSQL
- Platform field distinguishes Twitter vs Reddit
- Appears in "Report History" tab
- Full persistence support

## How to Use

### Step 1: Get Reddit API Credentials

Follow `REDDIT_SETUP.md` for detailed instructions:

1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (type: "script")
3. Get your Client ID and Client Secret
4. Add to Railway variables:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`

### Step 2: Use Reddit Scraping

1. Click **"Reddit Scraping"** tab
2. Enter subreddit name (without r/)
   - Example: "startups", "SaaS", "entrepreneur"
3. Add keywords (optional)
   - Example: "AI, B2B, funding"
4. Choose time filter
   - Recommended: "week" for recent content
5. Set minimum keyword mentions (default: 1)
6. Click **"Generate Report"**

### Step 3: View Results

- **View Report**: See full analysis in browser
- **Download .txt**: Get formatted text report
- **Download .json**: Get raw data for further analysis
- **Report History**: All reports saved and accessible

## Example Use Cases

### 1. Lead Generation
**Subreddit:** SaaS  
**Keywords:** looking for, need, recommend  
**Time Filter:** week  
**Result:** Find people actively seeking solutions

### 2. Market Research
**Subreddit:** startups  
**Keywords:** AI, automation, B2B  
**Time Filter:** month  
**Result:** Understand market trends and discussions

### 3. Competitor Analysis
**Subreddit:** technology  
**Keywords:** [competitor name], alternative  
**Time Filter:** month  
**Result:** See what people say about competitors

### 4. Product Feedback
**Subreddit:** webdev  
**Keywords:** [your product category]  
**Time Filter:** week  
**Result:** Gather user opinions and pain points

## Report Sections

1. **Subreddit Overview**
   - Subscriber count
   - Description
   - Total posts analyzed

2. **Keyword Analysis**
   - Qualified keywords (above threshold)
   - Disqualified keywords (below threshold)
   - Mention frequency and percentage

3. **Engagement Analysis**
   - Top 5 posts by engagement score
   - Score, comments, upvote ratio
   - Direct links to posts

4. **Sentiment Analysis**
   - Sentiment distribution (Positive/Negative/Neutral)
   - Lead opportunity posts with signals
   - Top 10 opportunities listed

5. **All Posts**
   - Complete list with details
   - Author, score, comments
   - Content preview
   - Sentiment classification

## API Limits

**Reddit Free API:**
- 60 requests per minute
- 100 posts per request
- No cost
- Public data only

**Best Practices:**
- Don't scrape too frequently
- Use appropriate time filters
- Start with popular subreddits
- Respect Reddit's terms of service

## Technical Details

**New Files:**
- `reddit_scraper.py` - Reddit API integration with PRAW
- `REDDIT_SETUP.md` - Setup instructions
- `REDDIT_FEATURE_SUMMARY.md` - This file

**Modified Files:**
- `app.py` - Added `/scrape-reddit` endpoint
- `database.py` - Added `platform` field to Report model
- `templates/index.html` - Added Reddit tab
- `static/js/script.js` - Added Reddit form handler
- `requirements.txt` - Added `praw==7.7.1`
- `.env.example` - Added Reddit credentials template

**Database Changes:**
- `platform` column added to `reports` table
- Values: 'twitter' or 'reddit'
- Backward compatible (defaults to 'twitter')

## Next Steps

1. **Set up Reddit API credentials** (see REDDIT_SETUP.md)
2. **Test with a popular subreddit** (e.g., "startups")
3. **Try different time filters** to find optimal data
4. **Combine with Twitter data** for comprehensive insights
5. **Schedule Reddit scrapes** (coming soon)

## Future Enhancements

Potential additions:
- Reddit scheduling support
- Multi-subreddit search
- Comment analysis
- User profile analysis
- Cross-platform comparison (Twitter vs Reddit)
- Advanced filters (min score, min comments)

## Troubleshooting

**"Reddit API credentials not found"**
- Add credentials to Railway variables
- Check spelling of variable names

**"No posts found"**
- Try different time filter
- Remove keywords to get all posts
- Check subreddit name is correct

**"403 Forbidden"**
- Check credentials are correct
- Wait a minute (rate limit)
- Verify user agent is set

See `REDDIT_SETUP.md` for detailed troubleshooting.

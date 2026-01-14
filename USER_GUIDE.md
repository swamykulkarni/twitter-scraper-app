# Twitter Scraper & Report Generator - User Guide

## 📋 Table of Contents
1. [Getting Started](#getting-started)
2. [Quick Scrape](#quick-scrape)
3. [Scheduled Scraping](#scheduled-scraping)
4. [Understanding Reports](#understanding-reports)
5. [Tips & Best Practices](#tips--best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### What This Tool Does
The Twitter Scraper analyzes tweets from any public Twitter/X account and generates detailed reports with engagement statistics, keyword analysis, and historical data tracking.

### Access the App
- **Live URL**: Your Railway deployment URL
- **Local**: http://localhost:5000

### Requirements
- Twitter API Bearer Token (already configured)
- Internet connection
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## ⚡ Quick Scrape

Use this for one-time analysis of any Twitter account.

### Step-by-Step Instructions

1. **Navigate to Quick Scrape Tab**
   - This is the default tab when you open the app
   - Look for the "Quick Scrape" button at the top

2. **Enter Twitter Handle**
   - Type the username WITHOUT the @ symbol
   - Example: `elonmusk` not `@elonmusk`

3. **Add Keywords (Optional)**
   - Enter keywords separated by commas
   - Example: `AI, technology, innovation`
   - Leave blank to get all recent tweets

4. **Generate Report**
   - Click the "Generate Report" button
   - Wait for analysis to complete (usually 5-10 seconds)

5. **View Results**
   - **👁️ View Report**: Opens report in scrollable window
   - **📄 Download Report (.txt)**: Save human-readable report
   - **📊 Download Raw Data (.json)**: Save data for further analysis

### What You'll Get
- Total tweets found (last 7 days)
- Summary statistics (likes, retweets, replies)
- Keyword frequency analysis
- Individual tweet details with engagement metrics
- Timestamps and performance data

---

## 📅 Scheduled Scraping

Build historical data beyond the 7-day API limit by scheduling automatic scrapes.

### Why Use Scheduled Scraping?
Twitter's free API only provides the last 7 days of tweets. By scheduling regular scrapes, you can:
- Build a historical database over time
- Track trends and patterns
- Avoid losing data as tweets age past 7 days

### Setting Up a Schedule

1. **Switch to Scheduled Scraping Tab**
   - Click "Scheduled Scraping" at the top

2. **Fill in Schedule Details**
   - **Twitter Handle**: Username to monitor (without @)
   - **Keywords**: Optional filter (comma-separated)
   - **Frequency**: Choose how often to scrape
     - **Every Hour**: Scrapes every 60 minutes
     - **Daily**: Once per day at specified time
     - **Weekly**: Once per week on specified day
   - **Day of Week**: (Only for weekly) Select Monday-Sunday
   - **Time**: (For daily/weekly) Set time in 24-hour format

3. **Add Schedule**
   - Click "➕ Add Schedule" button
   - Schedule appears in "Active Schedules" list

4. **Manage Schedules**
   - View all active schedules
   - See last run time
   - Delete schedules you no longer need

### Example Schedules

**Monitor Breaking News**
- Handle: `BBCBreaking`
- Keywords: `urgent, breaking`
- Frequency: Every Hour

**Daily Business Updates**
- Handle: `business`
- Keywords: `stocks, market, economy`
- Frequency: Daily at 09:00

**Weekly Competitor Analysis**
- Handle: `competitor_handle`
- Keywords: `product, launch, announcement`
- Frequency: Weekly on Monday at 08:00

### ⚠️ Important Note: Railway Deployment
If deployed on Railway, schedules are stored in ephemeral storage and will be lost when the app restarts. For persistent schedules, consider:
- Adding a PostgreSQL database
- Using external storage (AWS S3, Google Cloud)
- Re-adding schedules after deployments

---

## 📊 Understanding Reports

### Report Structure

**Header Section**
```
================================================================================
TWITTER ANALYSIS REPORT
Username: @username
Generated: 2026-01-15 10:30:00
Keywords: AI, technology
Total Tweets Found: 25
================================================================================
```

**Summary Statistics**
- Total Likes: Aggregate engagement
- Total Retweets: Share count
- Total Replies: Conversation level
- Averages: Per-tweet metrics

**Keyword Analysis**
- Shows how many times each keyword appears
- Helps identify trending topics

**Detailed Tweets**
- Individual tweet text
- Timestamp
- Engagement metrics (likes, retweets, replies)

### Report Formats

**Text Report (.txt)**
- Human-readable format
- Easy to share via email
- Can be opened in any text editor

**JSON Data (.json)**
- Machine-readable format
- Contains complete API response
- Use for custom analysis or integration

---

## 💡 Tips & Best Practices

### Choosing Keywords
✅ **Good Keywords**
- Specific terms: `iPhone`, `ChatGPT`, `climate`
- Brand names: `Tesla`, `Microsoft`
- Hashtags: `AI`, `tech`, `startup`

❌ **Avoid**
- Common words: `the`, `and`, `is`
- Too many keywords (keep it under 5)
- Overly broad terms

### Scheduling Strategy

**High-Value Accounts**
- Schedule hourly for breaking news sources
- Schedule daily for regular updates
- Schedule weekly for less active accounts

**Resource Management**
- Don't over-schedule (API rate limits apply)
- Start with daily schedules, adjust as needed
- Monitor "Last Run" times to ensure schedules work

### Data Management

**Local Storage**
- Reports saved in `reports/` folder
- Historical data in `historical_data/` folder
- Download important reports regularly

**Railway Deployment**
- Files are temporary (ephemeral storage)
- Download reports immediately after generation
- Consider external storage for long-term data

---

## 🔧 Troubleshooting

### "No tweets found or API error occurred"
**Causes:**
- Username doesn't exist or is private
- No tweets in last 7 days
- API rate limit reached

**Solutions:**
- Verify username is correct (no @ symbol)
- Check if account is public
- Wait 15 minutes if rate limited

### "TWITTER_BEARER_TOKEN not found"
**Cause:** Environment variable not set

**Solution:**
- For Railway: Add variable in project settings
- For local: Create `.env` file with token

### View Report Button Not Working
**Solutions:**
1. Open browser console (F12) to check for errors
2. Refresh the page and try again
3. Try downloading the report instead

### Schedules Disappearing After Restart
**Cause:** Railway uses ephemeral storage

**Solutions:**
- Keep a list of schedules in a separate document
- Re-add schedules after deployment
- Consider adding a database for persistence

### Slow Report Generation
**Causes:**
- Large number of tweets
- Network latency
- API response time

**Normal:** 5-15 seconds for most queries

---

## 📞 Support & Resources

### API Limitations (Free Tier)
- Last 7 days of tweets only
- 100 tweets per request
- Rate limits apply

### Upgrading API Access
For deeper history and more tweets:
- Basic: $200/month (30 days)
- Pro: $5,000/month (full archive)
- Enterprise: $42,000+/month

### Need Help?
- Check console logs (F12 in browser)
- Review error messages carefully
- Verify all inputs are correct

---

## 🎯 Quick Reference

| Task | Steps |
|------|-------|
| **One-time scrape** | Quick Scrape → Enter handle → Generate |
| **View report** | Generate → Click "View Report" |
| **Download report** | Generate → Click download button |
| **Schedule daily scrape** | Scheduled Scraping → Fill form → Add Schedule |
| **Delete schedule** | Scheduled Scraping → Click "Delete" on schedule |
| **Filter by keywords** | Enter keywords (comma-separated) in form |

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Platform:** Web Application (Flask + JavaScript)

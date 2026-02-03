# Twitter API Limitations & "No Tweets Found" Error

## The Problem

You're seeing "No tweets found" errors when running schedules, even though the accounts have recent tweets.

## Root Cause: Twitter API 7-Day Limitation

Twitter's **Free API tier** (`/tweets/search/recent` endpoint) has a critical limitation:

```
⚠️ Only returns tweets from the LAST 7 DAYS
```

This means:
- If an account hasn't tweeted in 7+ days → "No tweets found"
- If tweets exist but don't match your keywords → "No tweets found"
- If tweets are older than 7 days → "No tweets found"

## Why This Affects You

Looking at your schedules:

| Username | Keywords | Issue |
|----------|----------|-------|
| abhirammodak | GCC, Pune, Maharashtra | Tweets may not contain these keywords |
| Inductus_GCC | None | May not have tweeted in last 7 days |
| TheMahaIndex | AI, GCC | Tweets may not contain these keywords |
| CIIWestern | None | May not have tweeted in last 7 days |
| MIDC_Official | GCC, Manufacturing | Tweets may not contain these keywords |

## Solutions

### Solution 1: Remove or Broaden Keywords ✅ (Immediate)

**Problem:** Account tweets regularly but tweets don't contain your specific keywords.

**Fix:**
1. Go to Scheduled Scraping tab
2. Delete the schedule
3. Create new schedule WITHOUT keywords (or with broader keywords)
4. Test with "Run Now" button

**Example:**
- ❌ Keywords: "GCC", "Pune", "Maharashtra" (too specific)
- ✅ Keywords: None (get all tweets)
- ✅ Keywords: "GCC" (broader)

### Solution 2: Check Account Activity 📊 (Diagnostic)

Before adding a schedule, verify the account is active:

1. Visit Twitter directly: `https://twitter.com/[username]`
2. Check if they've tweeted in the last 7 days
3. If yes, check if tweets contain your keywords

### Solution 3: Use Different Accounts 🔄 (Alternative)

Focus on accounts that:
- Tweet frequently (daily or multiple times per week)
- Tweet about your topics regularly
- Are verified/official accounts (usually more active)

**Suggested Active Accounts:**
- News organizations
- Government official accounts
- Industry associations
- Tech companies
- Active influencers

### Solution 4: Adjust Expectations ⏰ (Reality Check)

**For B2B/GCC accounts:**
- Many don't tweet daily
- May tweet only during events/announcements
- Schedules will often return "No tweets found"
- This is NORMAL for these account types

**Recommendation:**
- Set schedules to run daily
- Accept that many runs will return empty
- Focus on collecting data over weeks/months
- The data you DO collect will be valuable

### Solution 5: Upgrade Twitter API 💰 (Long-term)

Twitter offers paid tiers with better access:

| Tier | Cost | Search Window | Best For |
|------|------|---------------|----------|
| Free | $0 | Last 7 days | Testing, active accounts |
| Basic | $100/month | Last 30 days | Small businesses |
| Pro | $5,000/month | Full archive | Enterprises |

**For your use case:** Free tier is fine if you:
- Focus on active accounts
- Remove restrictive keywords
- Accept occasional empty results

## Testing Your Schedules

### Test Each Schedule:

1. **Remove keywords temporarily:**
   ```
   Delete schedule → Create new without keywords → Test "Run Now"
   ```

2. **Check if tweets found:**
   - ✅ Tweets found → Keywords were too restrictive
   - ❌ No tweets → Account inactive in last 7 days

3. **Decide:**
   - If tweets found: Keep schedule without keywords
   - If no tweets: Remove schedule or wait for activity

## Recommended Schedule Configuration

### For Active Accounts (Tweet daily):
```
Username: [active_account]
Keywords: None (or very broad)
Frequency: Daily
```

### For Inactive Accounts (Tweet weekly/monthly):
```
Username: [inactive_account]
Keywords: None
Frequency: Daily (will often return empty, but catches tweets when they happen)
```

### For Keyword-Specific Research:
```
Username: [account]
Keywords: Single broad keyword (e.g., "GCC" not "GCC, Pune, Maharashtra")
Frequency: Daily
```

## Understanding "No Tweets Found"

This error means ONE of:

1. **Account hasn't tweeted in 7+ days** (most common)
2. **Tweets don't match your keywords** (second most common)
3. **Account is private/protected** (rare)
4. **Account doesn't exist** (rare)
5. **Twitter API rate limit** (temporary)

## Best Practices

### ✅ DO:
- Use schedules for active accounts
- Remove keywords or use broad ones
- Accept that some runs will be empty
- Focus on long-term data collection
- Use "Run Now" to test before scheduling

### ❌ DON'T:
- Expect tweets from every run
- Use multiple specific keywords
- Schedule inactive accounts expecting daily results
- Panic when you see "No tweets found"

## Quick Diagnostic

Run this for each schedule:

1. Visit: `https://twitter.com/[username]`
2. Check last tweet date
3. If < 7 days ago:
   - Remove keywords from schedule
   - Test "Run Now"
   - Should work now
4. If > 7 days ago:
   - Keep schedule (will catch future tweets)
   - Or remove if account is abandoned

## Alternative: Account Discovery

Instead of scheduling specific accounts, use **Account Discovery**:

1. Go to "Account Discovery" tab
2. Search by keywords: "GCC", "Manufacturing", etc.
3. Find ACTIVE accounts tweeting about your topics
4. Schedule those accounts (without keywords)

This ensures you're tracking accounts that actually tweet regularly.

## Summary

**The Issue:**
- Twitter Free API = Last 7 days only
- Many B2B accounts don't tweet daily
- Keywords make it worse

**The Fix:**
- Remove keywords from schedules
- Focus on active accounts
- Accept empty results as normal
- Collect data over time

**The Reality:**
- This is how Twitter API works
- All free tools have this limitation
- Paid API access is expensive
- Your current setup is fine for long-term data collection

---

**Need Help?**
- Test each schedule with "Run Now" button
- Remove keywords one by one
- Check Twitter directly to verify activity
- Focus on accounts that tweet frequently

---

Last Updated: February 3, 2026

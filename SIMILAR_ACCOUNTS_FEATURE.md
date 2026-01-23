# Similar Accounts Feature - Implementation Summary

## Overview
Added "Find Similar Accounts" feature that analyzes a reference Twitter account and discovers similar accounts based on their profile and tweet content.

## How It Works

### 1. Reference Account Analysis
When you provide a reference account (e.g., @elonmusk):
- Fetches the account's profile information (bio, followers, verified status)
- Retrieves their 10 most recent tweets (excluding retweets and replies)
- Extracts relevant keywords from both bio and tweets

### 2. Keyword Extraction
The system intelligently extracts keywords by:
- **From Bio**: Extracts meaningful words (3+ characters) from account description
- **From Tweets**: Analyzes recent tweet content for common topics
- **Hashtags**: Prioritizes hashtags as they indicate key topics
- **Stop Words Removal**: Filters out common words (the, and, for, etc.)
- **Frequency Analysis**: Ranks keywords by how often they appear
- **Top 20 Keywords**: Selects the most relevant keywords

### 3. Similar Account Discovery
Using the extracted keywords:
- Searches Twitter for accounts tweeting about those topics
- Applies the same quality filters (followers, verified, etc.)
- Calculates quality scores (0-100) for each account
- Filters out the reference account itself
- Returns sorted results (highest quality first)

## User Interface

### Toggle Mode
- **Default**: Keyword-based search (manual keywords)
- **Similar Mode**: Reference account-based search (automatic keyword extraction)
- Simple checkbox toggle: "Find accounts similar to a reference account"

### Reference Account Input
- Enter username with or without @ symbol
- Shows reference account preview after search:
  - Profile picture
  - Name and username
  - Follower count
  - Verified badge (if applicable)
  - Top 10 extracted keywords

### Results Display
- Same account card layout as keyword search
- Quality score badges (0-100)
- Account type labels (Business/Professional/Personal)
- Follower counts and matching tweets
- Select accounts for bulk scraping

## Use Cases

### 1. Competitor Analysis
**Example**: Reference account = @salesforce
- Finds similar CRM/SaaS companies
- Discovers competitors in the same space
- Identifies potential partners

### 2. Influencer Discovery
**Example**: Reference account = @garyvee
- Finds similar marketing influencers
- Discovers accounts with similar content style
- Identifies potential collaboration opportunities

### 3. Industry Research
**Example**: Reference account = @TeslaMotors
- Finds similar EV/automotive companies
- Discovers industry thought leaders
- Identifies potential customers/suppliers

### 4. Lead Generation
**Example**: Reference account = @HubSpot
- Finds similar B2B SaaS companies
- Discovers potential customers
- Identifies accounts with similar audience

## Technical Implementation

### Backend (Python)

#### New Method: `find_similar_accounts()`
```python
def find_similar_accounts(self, reference_username, max_results=100, filters=None):
    # 1. Fetch reference account info
    # 2. Get recent tweets from reference account
    # 3. Extract keywords using _extract_keywords_from_account()
    # 4. Use discover_accounts() with extracted keywords
    # 5. Filter out reference account from results
    # 6. Return similar accounts with metadata
```

#### New Method: `_extract_keywords_from_account()`
```python
def _extract_keywords_from_account(self, user_info, tweets):
    # 1. Extract words from bio/description
    # 2. Extract words from tweet text
    # 3. Extract hashtags from tweets
    # 4. Remove stop words
    # 5. Count frequency
    # 6. Return top 20 keywords
```

### API Endpoint

**POST** `/find-similar-accounts`

**Request Body**:
```json
{
  "reference_username": "elonmusk",
  "max_results": 100,
  "filters": {
    "min_followers": 1000,
    "verified_only": false,
    "has_links": true,
    "exclude_retweets": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "accounts": [...],
  "total_accounts": 25,
  "reference_account": {
    "username": "elonmusk",
    "name": "Elon Musk",
    "description": "...",
    "followers": 150000000,
    "verified": true,
    "profile_image_url": "..."
  },
  "extracted_keywords": ["tesla", "spacex", "mars", "ai", ...],
  "tweets_searched": 100
}
```

### Frontend (JavaScript)

#### Toggle Handler
- Switches between keyword and similar mode
- Shows/hides appropriate input sections
- Updates required field validation

#### Form Submission
- Detects current mode (keyword vs similar)
- Calls appropriate API endpoint
- Displays reference account preview
- Shows extracted keywords
- Renders discovered accounts

## Quality Filters (Applied to Similar Accounts)

All standard filters work with similar account search:
- ✓ Minimum Followers (50, 100, 500, 1K, 5K, 10K+)
- ✓ Verified Only
- ✓ Has Links in tweets
- ✓ Exclude Retweets

## Limitations

1. **Recent Tweets Only**: Analyzes only 10 most recent tweets (Twitter API limitation)
2. **Public Accounts**: Only works with public Twitter accounts
3. **Keyword Quality**: Results depend on how well keywords represent the account
4. **API Rate Limits**: Subject to Twitter API rate limits

## Future Enhancements

1. **Follower Overlap Analysis**: Find accounts followed by reference account's followers
2. **Engagement Pattern Matching**: Match accounts with similar engagement rates
3. **Content Style Analysis**: Analyze tweet sentiment, tone, and style
4. **Network Analysis**: Find accounts that interact with reference account
5. **Multiple Reference Accounts**: Combine keywords from multiple reference accounts

## Files Modified

- `twitter-scraper-app/twitter_scraper.py`: Added `find_similar_accounts()` and `_extract_keywords_from_account()`
- `twitter-scraper-app/app.py`: Added `/find-similar-accounts` endpoint
- `twitter-scraper-app/templates/index.html`: Added toggle and reference account input
- `twitter-scraper-app/static/js/script.js`: Added mode toggle and similar account search logic

## Testing Checklist

- [x] Toggle switches between keyword and similar mode
- [x] Reference account input accepts username with/without @
- [x] Backend extracts keywords from account bio and tweets
- [x] Similar accounts are discovered based on keywords
- [x] Reference account is filtered out from results
- [x] Reference account preview displays correctly
- [x] Extracted keywords are shown to user
- [x] Quality filters apply to similar account search
- [x] Results can be selected for bulk scraping
- [x] Pagination works with similar account results

## Example Workflow

1. User toggles "Find accounts similar to a reference account"
2. User enters "@salesforce" as reference
3. System analyzes @salesforce:
   - Bio: "We bring companies and customers together..."
   - Recent tweets about CRM, AI, customer success
   - Extracts: ["crm", "customer", "success", "ai", "sales", "cloud", ...]
4. System searches for accounts tweeting about those keywords
5. Results show: @HubSpot, @Zendesk, @Freshworks, etc.
6. User selects accounts and bulk scrapes them

## Deployment

Changes deployed to Railway: https://web-twitter-scraper.up.railway.app/

Ready to use in production!

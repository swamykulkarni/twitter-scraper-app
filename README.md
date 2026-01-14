# Twitter/X Scraper & Report Generator

Searches tweets from a specific Twitter handle, filters by keywords, and generates detailed reports.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your Twitter API credentials:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Bearer Token:
```
TWITTER_BEARER_TOKEN=your_actual_bearer_token
```

## Usage

Run the script:
```bash
python twitter_scraper.py
```

You'll be prompted to enter:
- Twitter username (without @)
- Keywords to filter by (comma-separated, or press Enter to get all tweets)

## Output

The script generates two files in the `reports/` directory:
- `.txt` file: Human-readable report with statistics and analysis
- `.json` file: Raw tweet data for further processing

## Features

- Search recent tweets from any public Twitter account
- Filter tweets by multiple keywords
- Generate detailed reports with:
  - Summary statistics (likes, retweets, replies)
  - Keyword frequency analysis
  - Individual tweet details with engagement metrics
- Export raw JSON data for custom analysis

## API Limitations

- Twitter API v2 free tier limits:
  - Recent search: Last 7 days only
  - Rate limit: 450 requests per 15 minutes
  - Max 100 tweets per request

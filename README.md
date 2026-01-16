# Social Listening Platform

A comprehensive social media intelligence platform for lead generation, market research, and competitive analysis.

**Version:** 1.0.1

## 🎯 Features

### Core Capabilities
- **Twitter/X Monitoring** - Track accounts, keywords, and conversations
- **Lead Generation** - Identify high-value prospects with lead scoring
- **Sentiment Analysis** - Understand audience sentiment and buying signals
- **Account Profiling** - Classify accounts (Enterprise/Business/Personal)
- **Engagement Scoring** - Prioritize high-performing content
- **Advanced Filtering** - Target specific content types and engagement levels

### Intelligence Features
- **Scheduled Monitoring** - Automated data collection
- **Historical Tracking** - Build datasets beyond 7-day API limits
- **Report History** - Persistent storage with PostgreSQL
- **Opportunity Detection** - Identify buying signals and business opportunities
- **Content Analysis** - Extract URLs, mentions, hashtags

## 🚀 Quick Start

### Web Application

1. **Access the platform:**
   - Local: http://localhost:5000
   - Production: Your Railway deployment URL

2. **Generate your first report:**
   - Enter a Twitter handle (without @)
   - Add keywords (optional)
   - Apply filters (optional)
   - Click "Generate Report"

### Command Line

```bash
python run_scraper.py <username> [keywords]
```

## 📦 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials
```bash
cp .env.example .env
```

Edit `.env` and add your Twitter Bearer Token:
```
TWITTER_BEARER_TOKEN=your_actual_bearer_token
```

### 3. Database Setup (Optional for Local)
For local development, SQLite is used automatically.

For production (Railway):
- Add PostgreSQL database in Railway dashboard
- `DATABASE_URL` is set automatically

### 4. Run the Application
```bash
python app.py
```

## 📊 Use Cases

- **B2B Lead Generation** - Find decision-makers and prospects
- **Competitive Intelligence** - Monitor competitor activity
- **Market Research** - Track industry trends and conversations
- **Brand Monitoring** - Analyze brand mentions and sentiment
- **Customer Discovery** - Identify pain points and opportunities

## 🔧 Advanced Features

### Lead Scoring
Automatically scores accounts based on:
- Verification status
- Follower count and ratios
- Business keywords in bio
- Content quality indicators

### Sentiment Analysis
Detects:
- Positive/Negative/Neutral sentiment
- Opportunity signals (buying intent)
- Business-related keywords

### Engagement Scoring
Weighted scoring system:
- Likes × 1
- Retweets × 3
- Replies × 2
- Quotes × 2

## 📈 API Limitations

**Twitter API v2 Free Tier:**
- Recent search: Last 7 days only
- Rate limit: 450 requests per 15 minutes
- Max 100 tweets per request

**Workaround:** Use scheduled scraping to build historical datasets

## 🗄️ Database Schema

- **schedules** - Automated monitoring configurations
- **reports** - Generated intelligence reports
- **historical_tweets** - Long-term tweet storage

## 📚 Documentation

- [User Guide](USER_GUIDE.md) - Complete usage instructions
- [Database Setup](DATABASE_SETUP.md) - PostgreSQL configuration
- [Railway Notes](RAILWAY_NOTES.md) - Deployment information

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Database:** PostgreSQL (production), SQLite (local)
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Railway
- **API:** Twitter/X API v2

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Support

For issues or questions, check the documentation or create an issue in the repository.

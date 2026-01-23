import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ARRAY, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get database URL from environment variable (Railway provides this automatically)
# Try multiple possible environment variable names
print(f"[DATABASE] Checking for database connection...")

# Option 1: Direct DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PRIVATE_URL') or os.getenv('POSTGRES_URL')

# Option 2: Build from individual components (Railway's preferred method)
if not DATABASE_URL:
    pghost = os.getenv('PGHOST')
    pgport = os.getenv('PGPORT', '5432')
    pguser = os.getenv('PGUSER')
    pgpassword = os.getenv('PGPASSWORD')
    pgdatabase = os.getenv('PGDATABASE')
    
    if all([pghost, pguser, pgpassword, pgdatabase]):
        DATABASE_URL = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
        print(f"[DATABASE] Built DATABASE_URL from individual components")

print(f"[DATABASE] Environment variables containing 'DATABASE' or 'POSTGRES':")
for key in os.environ.keys():
    if 'DATABASE' in key.upper() or 'POSTGRES' in key.upper() or 'PG' in key.upper():
        # Show key and first 20 chars of value for security
        value = os.environ[key]
        display_value = value[:20] + '...' if len(value) > 20 else value
        print(f"[DATABASE]   {key} = {display_value}")
print(f"[DATABASE] DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")
print(f"[DATABASE] DATABASE_PRIVATE_URL exists: {bool(os.getenv('DATABASE_PRIVATE_URL'))}")
print(f"[DATABASE] POSTGRES_URL exists: {bool(os.getenv('POSTGRES_URL'))}")
print(f"[DATABASE] DATABASE_PUBLIC_URL exists: {bool(os.getenv('DATABASE_PUBLIC_URL'))}")
print(f"[DATABASE] PGHOST exists: {bool(os.getenv('PGHOST'))}")

# Handle Railway's postgres:// vs postgresql:// URL format
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print(f"[DATABASE] Using PostgreSQL database")
    print(f"[DATABASE] Connection string: {DATABASE_URL[:30]}...")  # Only show first 30 chars for security
else:
    DATABASE_URL = 'sqlite:///twitter_scraper.db'
    print("[DATABASE] ⚠️ WARNING: Using SQLite for local development")
    print("[DATABASE] ⚠️ Data will NOT persist on Railway!")
    print("[DATABASE] ⚠️ Please ensure PostgreSQL is properly connected")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print("[DATABASE] ✓ Database engine created successfully")
except Exception as e:
    print(f"[DATABASE] ✗ Error creating database engine: {e}")
    raise

# Database Models

class Schedule(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    keywords = Column(JSON)  # Store as JSON array
    frequency = Column(String, nullable=False)  # once, hourly, daily, weekly
    start_datetime = Column(DateTime, nullable=False)  # When to start (UTC)
    day = Column(String)  # For weekly schedules
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)  # Calculated next run time
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'keywords': self.keywords,
            'frequency': self.frequency,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'day': self.day,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, default='twitter', index=True)  # 'twitter' or 'reddit'
    username = Column(String, nullable=False, index=True)  # Twitter handle or subreddit name
    keywords = Column(JSON)
    tweet_count = Column(Integer)  # or post_count for Reddit
    account_type = Column(String)
    lead_score = Column(Integer)
    report_content = Column(Text)  # Full text report
    tweets_data = Column(JSON)  # Raw tweet/post data as JSON
    filters = Column(JSON)  # Filters used
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': getattr(self, 'platform', 'twitter'),  # Default to twitter if field missing
            'username': self.username,
            'keywords': self.keywords,
            'tweet_count': self.tweet_count,
            'account_type': self.account_type,
            'lead_score': self.lead_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HistoricalTweet(Base):
    __tablename__ = 'historical_tweets'
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, nullable=False, index=True)  # Twitter's tweet ID
    username = Column(String, nullable=False, index=True)
    text = Column(Text)
    created_at = Column(DateTime, index=True)
    tweet_data = Column(JSON)  # Full tweet data
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tweet_id': self.tweet_id,
            'username': self.username,
            'text': self.text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tweet_data': self.tweet_data,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None
        }


class DeepHistory(Base):
    """
    Deep History table - stores all scraping data in multiple formats
    Foundation for AI/ML/MCP features
    """
    __tablename__ = 'deep_history'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Metadata
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=True, index=True)
    username = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False, index=True)  # 'twitter', 'reddit'
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Raw Data (Multiple Formats for flexibility)
    raw_json = Column(JSON)  # Full structured data
    raw_text = Column(Text)  # Plain text report
    raw_csv = Column(Text)   # CSV format
    
    # Extracted Entities (for quick queries without parsing JSON)
    tweet_ids = Column(JSON)  # Array of tweet/post IDs
    keywords = Column(JSON)   # Keywords used in search
    hashtags = Column(JSON)   # Extracted hashtags
    mentions = Column(JSON)   # Extracted mentions
    urls = Column(JSON)       # Extracted URLs
    
    # Account Snapshot (at time of scrape)
    account_snapshot = Column(JSON)  # {followers, following, verified, bio, location, etc.}
    
    # Metrics (for quick analysis)
    total_tweets = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)  # Sum of likes + retweets + replies
    avg_sentiment = Column(Float)  # Average sentiment score
    lead_score = Column(Integer)   # Quality score
    account_type = Column(String)  # Business/Professional/Personal/Bot
    
    # For Future AI/ML Features
    # embedding = Column(Vector(1536))  # Will add pgvector extension later
    topics = Column(JSON)      # LLM-extracted topics
    ai_analysis = Column(JSON) # LLM analysis results
    ai_summary = Column(Text)  # Natural language summary
    
    # Metadata
    scrape_type = Column(String)  # 'quick', 'scheduled', 'bulk', 'discovery'
    filters_used = Column(JSON)   # Filters applied during scrape
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'username': self.username,
            'platform': self.platform,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'total_tweets': self.total_tweets,
            'total_engagement': self.total_engagement,
            'avg_sentiment': self.avg_sentiment,
            'lead_score': self.lead_score,
            'account_type': self.account_type,
            'keywords': self.keywords,
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'scrape_type': self.scrape_type,
            'ai_summary': self.ai_summary
        }


# Database helper functions

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get database session (non-generator version)"""
    return SessionLocal()


def save_to_deep_history(
    username, 
    platform, 
    raw_json, 
    raw_text, 
    report_id=None,
    scrape_type='quick',
    filters_used=None
):
    """
    Save scraping data to deep_history table
    
    Args:
        username: Account username
        platform: 'twitter' or 'reddit'
        raw_json: Full structured data (dict)
        raw_text: Plain text report content
        report_id: Optional reference to reports table
        scrape_type: 'quick', 'scheduled', 'bulk', 'discovery'
        filters_used: Dict of filters applied
    
    Returns:
        DeepHistory object
    """
    session = get_db_session()
    
    try:
        # Extract entities from raw_json
        tweet_ids = []
        hashtags = []
        mentions = []
        urls = []
        total_engagement = 0
        
        if raw_json and 'tweets' in raw_json:
            for tweet in raw_json['tweets']:
                # Tweet IDs
                if 'id' in tweet:
                    tweet_ids.append(tweet['id'])
                
                # Engagement
                metrics = tweet.get('public_metrics', {})
                total_engagement += (
                    metrics.get('like_count', 0) +
                    metrics.get('retweet_count', 0) +
                    metrics.get('reply_count', 0)
                )
                
                # Entities
                entities = tweet.get('entities', {})
                if 'hashtags' in entities:
                    hashtags.extend([h['tag'] for h in entities['hashtags']])
                if 'mentions' in entities:
                    mentions.extend([m['username'] for m in entities['mentions']])
                if 'urls' in entities:
                    urls.extend([u['expanded_url'] for u in entities['urls']])
        
        # Remove duplicates
        hashtags = list(set(hashtags))
        mentions = list(set(mentions))
        urls = list(set(urls))
        
        # Extract account snapshot
        account_snapshot = None
        if raw_json and 'account_info' in raw_json:
            account_snapshot = raw_json['account_info']
        
        # Create deep_history record
        deep_record = DeepHistory(
            report_id=report_id,
            username=username,
            platform=platform,
            scraped_at=datetime.utcnow(),
            raw_json=raw_json,
            raw_text=raw_text,
            raw_csv=None,  # Can add CSV generation later
            tweet_ids=tweet_ids,
            keywords=raw_json.get('keywords', []) if raw_json else [],
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
            account_snapshot=account_snapshot,
            total_tweets=len(tweet_ids),
            total_engagement=total_engagement,
            avg_sentiment=raw_json.get('avg_sentiment') if raw_json else None,
            lead_score=raw_json.get('lead_score') if raw_json else None,
            account_type=raw_json.get('account_type') if raw_json else None,
            scrape_type=scrape_type,
            filters_used=filters_used
        )
        
        session.add(deep_record)
        session.commit()
        session.refresh(deep_record)
        
        print(f"[DEEP_HISTORY] Saved record for @{username} ({platform}) - {len(tweet_ids)} tweets")
        
        return deep_record
        
    except Exception as e:
        session.rollback()
        print(f"[DEEP_HISTORY] Error saving to deep_history: {e}")
        raise
    finally:
        session.close()


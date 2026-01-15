import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get database URL from environment variable (Railway provides this automatically)
# Try multiple possible environment variable names
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PRIVATE_URL') or os.getenv('POSTGRES_URL')

print(f"[DATABASE] Checking for database connection...")
print(f"[DATABASE] DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")
print(f"[DATABASE] DATABASE_PRIVATE_URL exists: {bool(os.getenv('DATABASE_PRIVATE_URL'))}")

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
    frequency = Column(String, nullable=False)  # hourly, daily, weekly
    time = Column(String)  # HH:MM format
    day = Column(String)  # For weekly schedules
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'keywords': self.keywords,
            'frequency': self.frequency,
            'time': self.time,
            'day': self.day,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    keywords = Column(JSON)
    tweet_count = Column(Integer)
    account_type = Column(String)
    lead_score = Column(Integer)
    report_content = Column(Text)  # Full text report
    tweets_data = Column(JSON)  # Raw tweet data as JSON
    filters = Column(JSON)  # Filters used
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
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

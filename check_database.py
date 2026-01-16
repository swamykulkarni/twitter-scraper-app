#!/usr/bin/env python3
"""
Database inspection script to verify data persistence
"""
import os
from database import get_db_session, Report, Schedule, HistoricalTweet, engine
from sqlalchemy import inspect

def check_database():
    print("=" * 80)
    print("DATABASE INSPECTION REPORT")
    print("=" * 80)
    
    # Check database type
    db_url = str(engine.url)
    if 'postgresql' in db_url:
        print("✓ Database Type: PostgreSQL")
        print(f"✓ Connection: {db_url[:50]}...")
    else:
        print("⚠️  Database Type: SQLite (ephemeral storage)")
        print(f"⚠️  Connection: {db_url}")
    
    print("\n" + "=" * 80)
    print("SCHEMA VERIFICATION")
    print("=" * 80)
    
    # Check if tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nTables found: {len(tables)}")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\n  Table: {table}")
        print(f"  Columns: {len(columns)}")
        for col in columns:
            print(f"    - {col['name']}: {col['type']}")
    
    print("\n" + "=" * 80)
    print("DATA VERIFICATION")
    print("=" * 80)
    
    db = get_db_session()
    try:
        # Check Schedules
        schedules = db.query(Schedule).all()
        print(f"\n📅 SCHEDULES: {len(schedules)} found")
        for schedule in schedules:
            print(f"  #{schedule.id}: @{schedule.username}")
            print(f"    Frequency: {schedule.frequency}")
            print(f"    Keywords: {schedule.keywords}")
            print(f"    Created: {schedule.created_at}")
            print(f"    Last Run: {schedule.last_run or 'Never'}")
        
        # Check Reports
        reports = db.query(Report).order_by(Report.created_at.desc()).limit(10).all()
        print(f"\n📊 REPORTS: {len(reports)} found (showing last 10)")
        for report in reports:
            print(f"  #{report.id}: @{report.username}")
            print(f"    Tweets: {report.tweet_count}")
            print(f"    Account Type: {report.account_type}")
            print(f"    Lead Score: {report.lead_score}/7")
            print(f"    Keywords: {report.keywords}")
            print(f"    Created: {report.created_at}")
        
        # Check Historical Tweets
        tweets = db.query(HistoricalTweet).count()
        print(f"\n🐦 HISTORICAL TWEETS: {tweets} found")
        
        if tweets > 0:
            # Show sample by username
            usernames = db.query(HistoricalTweet.username).distinct().all()
            print(f"  Tracking {len(usernames)} accounts:")
            for (username,) in usernames:
                count = db.query(HistoricalTweet).filter(HistoricalTweet.username == username).count()
                print(f"    @{username}: {count} tweets")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        total_records = len(schedules) + len(reports) + tweets
        
        if 'postgresql' in db_url:
            print(f"✓ PostgreSQL is connected and working")
            print(f"✓ Total records: {total_records}")
            print(f"✓ Data is persistent and will survive restarts")
        else:
            print(f"⚠️  Using SQLite - data will be lost on restart!")
            print(f"⚠️  Total records: {total_records} (temporary)")
            print(f"⚠️  Please connect PostgreSQL for persistence")
        
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database()

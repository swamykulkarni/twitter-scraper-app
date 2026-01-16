import schedule
import time
import json
import os
from datetime import datetime
from twitter_scraper import TwitterScraper
from threading import Thread

class ScheduledScraper:
    def __init__(self):
        self.scraper = TwitterScraper()
        self.schedules = []
        self.load_schedules()
    
    def load_schedules(self):
        """Load scheduled scrapes from database"""
        try:
            from database import get_db_session, Schedule as DBSchedule
            db = get_db_session()
            try:
                db_schedules = db.query(DBSchedule).filter(DBSchedule.enabled == True).all()
                self.schedules = [s.to_dict() for s in db_schedules]
                print(f"Loaded {len(self.schedules)} schedules from database")
            finally:
                db.close()
        except Exception as e:
            print(f"Error loading schedules from database: {e}")
            self.schedules = []
    
    def add_schedule_from_dict(self, schedule_dict):
        """Add a schedule from dictionary (already saved to DB)"""
        self.schedules.append(schedule_dict)
        self.setup_schedule(schedule_dict)
        return schedule_dict
    
    def remove_schedule(self, schedule_id):
        """Remove a scheduled scrape"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        schedule.clear()
        self.setup_all_schedules()
    
    def run_scrape(self, schedule_config):
        """Execute a scheduled scrape"""
        try:
            from database import get_db_session, Schedule as DBSchedule, HistoricalTweet
            
            username = schedule_config['username']
            keywords = schedule_config.get('keywords')
            
            print(f"Running scheduled scrape for @{username}...")
            tweets_data = self.scraper.search_user_tweets(username, keywords=keywords, max_results=100)
            
            if tweets_data and 'data' in tweets_data:
                # Generate report
                report_file = self.scraper.generate_report(tweets_data, username, keywords)
                
                # Save to historical data in database
                self.save_historical_data(username, tweets_data)
                
                # Update last run time in database
                db = get_db_session()
                try:
                    schedule_db = db.query(DBSchedule).filter(DBSchedule.id == schedule_config['id']).first()
                    if schedule_db:
                        schedule_db.last_run = datetime.utcnow()
                        db.commit()
                        
                        # Update in-memory schedule
                        for s in self.schedules:
                            if s['id'] == schedule_config['id']:
                                s['last_run'] = datetime.utcnow().isoformat()
                finally:
                    db.close()
                
                print(f"✓ Scheduled scrape completed: {report_file}")
            else:
                print(f"✗ No tweets found for @{username}")
        
        except Exception as e:
            print(f"Error in scheduled scrape: {e}")
    
    def save_historical_data(self, username, tweets_data):
        """Save tweets to database"""
        try:
            from database import get_db_session, HistoricalTweet
            
            db = get_db_session()
            try:
                new_count = 0
                for tweet in tweets_data['data']:
                    # Check if tweet already exists
                    existing = db.query(HistoricalTweet).filter(
                        HistoricalTweet.tweet_id == tweet['id']
                    ).first()
                    
                    if not existing:
                        historical_tweet = HistoricalTweet(
                            tweet_id=tweet['id'],
                            username=username,
                            text=tweet['text'],
                            created_at=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                            tweet_data=tweet
                        )
                        db.add(historical_tweet)
                        new_count += 1
                
                db.commit()
                print(f"Added {new_count} new tweets to historical database")
            finally:
                db.close()
        except Exception as e:
            print(f"Error saving historical data: {e}")
    
    def setup_schedule(self, schedule_config):
        """Setup a single schedule with start datetime"""
        if not schedule_config.get('enabled'):
            return
        
        frequency = schedule_config['frequency']
        start_datetime_str = schedule_config.get('start_datetime')
        day = schedule_config.get('day')
        
        if not start_datetime_str:
            print(f"Warning: Schedule {schedule_config.get('id')} has no start_datetime")
            return
        
        # Parse start datetime
        try:
            start_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00').replace('+00:00', ''))
        except (ValueError, AttributeError) as e:
            print(f"Error parsing start_datetime: {e}")
            return
        
        # Check if start time has passed
        now = datetime.utcnow()
        if start_datetime > now:
            # Schedule hasn't started yet - schedule the first run
            time_str = start_datetime.strftime('%H:%M')
            
            if frequency == 'once':
                # One-time schedule
                schedule.every().day.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
            elif frequency == 'hourly':
                # For hourly, schedule at the start time, then every hour
                schedule.every().hour.at(f":{start_datetime.strftime('%M')}").do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
            elif frequency == 'daily':
                schedule.every().day.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
            elif frequency == 'weekly':
                if day == 'monday':
                    schedule.every().monday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'tuesday':
                    schedule.every().tuesday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'wednesday':
                    schedule.every().wednesday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'thursday':
                    schedule.every().thursday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'friday':
                    schedule.every().friday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'saturday':
                    schedule.every().saturday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif day == 'sunday':
                    schedule.every().sunday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                else:
                    schedule.every().week.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
            
            print(f"Scheduled: @{schedule_config['username']} - {frequency} starting at {start_datetime}")
        else:
            # Start time has passed - check if we should still run based on frequency
            if frequency == 'once':
                # One-time schedule that already passed - disable it
                print(f"One-time schedule {schedule_config['id']} has passed, disabling")
                self.disable_schedule(schedule_config['id'])
            else:
                # Recurring schedule - set it up normally
                time_str = start_datetime.strftime('%H:%M')
                
                if frequency == 'hourly':
                    schedule.every().hour.at(f":{start_datetime.strftime('%M')}").do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif frequency == 'daily':
                    schedule.every().day.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                elif frequency == 'weekly':
                    if day == 'monday':
                        schedule.every().monday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'tuesday':
                        schedule.every().tuesday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'wednesday':
                        schedule.every().wednesday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'thursday':
                        schedule.every().thursday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'friday':
                        schedule.every().friday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'saturday':
                        schedule.every().saturday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    elif day == 'sunday':
                        schedule.every().sunday.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                    else:
                        schedule.every().week.at(time_str).do(self.run_scrape, schedule_config).tag(f"schedule_{schedule_config['id']}")
                
                print(f"Scheduled (recurring): @{schedule_config['username']} - {frequency} at {time_str}")
    
    def disable_schedule(self, schedule_id):
        """Disable a schedule in the database"""
        try:
            from database import get_db_session, Schedule as DBSchedule
            db = get_db_session()
            try:
                schedule_db = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
                if schedule_db:
                    schedule_db.enabled = False
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error disabling schedule: {e}")
    
    def setup_all_schedules(self):
        """Setup all schedules"""
        for schedule_config in self.schedules:
            self.setup_schedule(schedule_config)
    
    def start(self):
        """Start the scheduler in a background thread"""
        self.setup_all_schedules()
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        thread = Thread(target=run_scheduler, daemon=True)
        thread.start()
        print("Scheduler started!")

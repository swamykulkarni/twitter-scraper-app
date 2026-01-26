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
                
                # Filter out legacy schedules without start_datetime
                valid_schedules = []
                for s in db_schedules:
                    if s.start_datetime:
                        valid_schedules.append(s.to_dict())
                    else:
                        print(f"[SCHEDULER] Skipping legacy schedule without start_datetime: ID={s.id}, username={s.username}")
                
                self.schedules = valid_schedules
                print(f"Loaded {len(self.schedules)} valid schedules from database")
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
            from database import get_db_session, Schedule as DBSchedule, HistoricalTweet, Report, save_to_deep_history
            
            username = schedule_config['username']
            keywords = schedule_config.get('keywords')
            frequency = schedule_config.get('frequency')
            
            print(f"Running scheduled scrape for @{username}...")
            tweets_data = self.scraper.search_user_tweets(username, keywords=keywords, max_results=100)
            
            if tweets_data and 'data' in tweets_data:
                # Generate report file
                report_file = self.scraper.generate_report(tweets_data, username, keywords)
                
                # Read report content
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                # Get account analysis
                user_profile = tweets_data.get('user_profile', {})
                account_analysis = self.scraper.analyze_account_type(user_profile) if user_profile else {}
                
                # Save to historical data in database
                self.save_historical_data(username, tweets_data)
                
                # Save report to database
                db = get_db_session()
                try:
                    # Save report
                    db_report = Report(
                        platform='twitter',
                        username=username,
                        keywords=keywords,
                        tweet_count=len(tweets_data['data']),
                        account_type=account_analysis.get('type'),
                        lead_score=account_analysis.get('score'),
                        report_content=report_content,
                        tweets_data=tweets_data,
                        filters={}
                    )
                    db.add(db_report)
                    db.commit()
                    report_id = db_report.id
                    
                    # Save to deep_history for AI/ML features
                    try:
                        save_to_deep_history(
                            username=username,
                            platform='twitter',
                            raw_json={
                                'tweets': tweets_data['data'],
                                'account_info': user_profile,
                                'keywords': keywords,
                                'lead_score': account_analysis.get('score'),
                                'account_type': account_analysis.get('type'),
                                'avg_sentiment': account_analysis.get('avg_sentiment')
                            },
                            raw_text=report_content,
                            report_id=report_id,
                            scrape_type='scheduled',
                            filters_used={}
                        )
                        print(f"✓ Saved to deep_history for @{username}")
                    except Exception as dh_error:
                        print(f"[WARNING] Failed to save to deep_history: {dh_error}")
                    
                    # Update schedule last run time and next run time
                    schedule_db = db.query(DBSchedule).filter(DBSchedule.id == schedule_config['id']).first()
                    if schedule_db:
                        now = datetime.utcnow()
                        schedule_db.last_run = now
                        
                        # Calculate next run time based on frequency
                        if frequency == 'once':
                            # One-time schedule - disable it
                            schedule_db.enabled = False
                            schedule_db.next_run = None
                            print(f"One-time schedule completed, disabling schedule {schedule_config['id']}")
                        else:
                            # Calculate next run for recurring schedules
                            next_run = self.calculate_next_run(schedule_db.start_datetime, frequency, schedule_db.day)
                            schedule_db.next_run = next_run
                            print(f"Next run scheduled for: {next_run}")
                        
                        # Update in-memory schedule
                        for s in self.schedules:
                            if s['id'] == schedule_config['id']:
                                s['last_run'] = now.isoformat()
                                if frequency == 'once':
                                    s['enabled'] = False
                                    s['next_run'] = None
                                else:
                                    s['next_run'] = next_run.isoformat() if next_run else None
                    
                    db.commit()
                    print(f"✓ Scheduled scrape completed and saved to database: {report_file}")
                finally:
                    db.close()
            else:
                print(f"✗ No tweets found for @{username}")
        
        except Exception as e:
            print(f"Error in scheduled scrape: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_next_run(self, start_datetime, frequency, day=None):
        """Calculate the next run time based on frequency"""
        now = datetime.utcnow()
        
        if frequency == 'hourly':
            # Next run is at the same minute of the next hour
            next_run = now.replace(second=0, microsecond=0)
            next_run = next_run.replace(minute=start_datetime.minute)
            if next_run <= now:
                next_run = next_run.replace(hour=next_run.hour + 1)
            return next_run
        
        elif frequency == 'daily':
            # Next run is at the same time tomorrow
            next_run = now.replace(
                hour=start_datetime.hour,
                minute=start_datetime.minute,
                second=0,
                microsecond=0
            )
            if next_run <= now:
                # If time has passed today, schedule for tomorrow
                from datetime import timedelta
                next_run = next_run + timedelta(days=1)
            return next_run
        
        elif frequency == 'weekly':
            # Next run is on the specified day at the specified time
            from datetime import timedelta
            days_of_week = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            target_day = days_of_week.get(day.lower(), 0)
            current_day = now.weekday()
            
            days_ahead = target_day - current_day
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=start_datetime.hour,
                minute=start_datetime.minute,
                second=0,
                microsecond=0
            )
            return next_run
        
        return None
    
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

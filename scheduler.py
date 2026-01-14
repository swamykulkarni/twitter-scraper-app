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
        """Load scheduled scrapes from config file"""
        if os.path.exists('schedules.json'):
            with open('schedules.json', 'r') as f:
                self.schedules = json.load(f)
    
    def save_schedules(self):
        """Save scheduled scrapes to config file"""
        with open('schedules.json', 'w') as f:
            json.dump(self.schedules, f, indent=2)
    
    def add_schedule(self, username, keywords=None, frequency='daily', time_str='09:00', day=None):
        """Add a new scheduled scrape"""
        schedule_config = {
            'id': len(self.schedules) + 1,
            'username': username,
            'keywords': keywords,
            'frequency': frequency,
            'time': time_str,
            'day': day,
            'enabled': True,
            'last_run': None
        }
        self.schedules.append(schedule_config)
        self.save_schedules()
        self.setup_schedule(schedule_config)
        return schedule_config
    
    def remove_schedule(self, schedule_id):
        """Remove a scheduled scrape"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.save_schedules()
        schedule.clear()
        self.setup_all_schedules()
    
    def run_scrape(self, schedule_config):
        """Execute a scheduled scrape"""
        try:
            username = schedule_config['username']
            keywords = schedule_config.get('keywords')
            
            print(f"Running scheduled scrape for @{username}...")
            tweets_data = self.scraper.search_user_tweets(username, keywords=keywords, max_results=100)
            
            if tweets_data and 'data' in tweets_data:
                # Generate report with timestamp
                report_file = self.scraper.generate_report(tweets_data, username, keywords)
                
                # Save to historical data
                self.save_historical_data(username, tweets_data)
                
                # Update last run time
                for s in self.schedules:
                    if s['id'] == schedule_config['id']:
                        s['last_run'] = datetime.now().isoformat()
                self.save_schedules()
                
                print(f"✓ Scheduled scrape completed: {report_file}")
            else:
                print(f"✗ No tweets found for @{username}")
        
        except Exception as e:
            print(f"Error in scheduled scrape: {e}")
    
    def save_historical_data(self, username, tweets_data):
        """Append tweets to historical data file"""
        os.makedirs('historical_data', exist_ok=True)
        history_file = f'historical_data/{username}_history.json'
        
        # Load existing history
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        # Add new tweets (avoid duplicates)
        existing_ids = {tweet['id'] for tweet in history}
        new_tweets = [tweet for tweet in tweets_data['data'] if tweet['id'] not in existing_ids]
        
        history.extend(new_tweets)
        
        # Sort by date (newest first)
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Added {len(new_tweets)} new tweets to history. Total: {len(history)}")
    
    def setup_schedule(self, schedule_config):
        """Setup a single schedule"""
        if not schedule_config.get('enabled'):
            return
        
        frequency = schedule_config['frequency']
        time_str = schedule_config.get('time', '09:00')
        day = schedule_config.get('day')
        
        if frequency == 'hourly':
            schedule.every().hour.do(self.run_scrape, schedule_config)
        elif frequency == 'daily':
            schedule.every().day.at(time_str).do(self.run_scrape, schedule_config)
        elif frequency == 'weekly':
            if day == 'monday':
                schedule.every().monday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'tuesday':
                schedule.every().tuesday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'wednesday':
                schedule.every().wednesday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'thursday':
                schedule.every().thursday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'friday':
                schedule.every().friday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'saturday':
                schedule.every().saturday.at(time_str).do(self.run_scrape, schedule_config)
            elif day == 'sunday':
                schedule.every().sunday.at(time_str).do(self.run_scrape, schedule_config)
            else:
                schedule.every().week.at(time_str).do(self.run_scrape, schedule_config)
    
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

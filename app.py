from flask import Flask, render_template, request, send_file, jsonify
import os
import json
from datetime import datetime
from twitter_scraper import TwitterScraper
from reddit_scraper import RedditScraper
from scheduler import ScheduledScraper
from database import init_db, get_db_session, Report, Schedule as DBSchedule, HistoricalTweet, engine

app = Flask(__name__)

# Initialize database
init_db()

scheduler = ScheduledScraper()

# Start scheduler on app startup
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint to verify database connection"""
    try:
        db = get_db_session()
        try:
            # Try to query database - use text() for SQLAlchemy 2.0
            from sqlalchemy import text
            db.execute(text('SELECT 1'))
            db_status = 'connected'
            db_type = 'PostgreSQL' if 'postgresql' in str(engine.url) else 'SQLite'
            
            # Count records
            schedules_count = db.query(DBSchedule).count()
            enabled_schedules_count = db.query(DBSchedule).filter(DBSchedule.enabled == True).count()
            reports_count = db.query(Report).count()
            tweets_count = db.query(HistoricalTweet).count()
            
        except Exception as e:
            db_status = f'error: {str(e)}'
            db_type = 'unknown'
            schedules_count = 0
            enabled_schedules_count = 0
            reports_count = 0
            tweets_count = 0
        finally:
            db.close()
        
        return jsonify({
            'status': 'healthy',
            'database': {
                'status': db_status,
                'type': db_type,
                'url_set': bool(os.getenv('DATABASE_URL')),
                'connection_string': str(engine.url)[:50] + '...'
            },
            'data': {
                'schedules_total': schedules_count,
                'schedules_enabled': enabled_schedules_count,
                'reports': reports_count,
                'historical_tweets': tweets_count,
                'total_records': schedules_count + reports_count + tweets_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/debug/schedules')
def debug_schedules():
    """Debug endpoint to see all schedules in database"""
    try:
        db = get_db_session()
        try:
            all_schedules = db.query(DBSchedule).all()
            schedules_data = []
            for s in all_schedules:
                schedules_data.append({
                    'id': s.id,
                    'username': s.username,
                    'keywords': s.keywords,
                    'frequency': s.frequency,
                    'enabled': s.enabled,
                    'start_datetime': s.start_datetime.isoformat() if s.start_datetime else None,
                    'next_run': s.next_run.isoformat() if s.next_run else None,
                    'last_run': s.last_run.isoformat() if s.last_run else None,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    'has_start_datetime': s.start_datetime is not None
                })
            
            return jsonify({
                'total_schedules': len(all_schedules),
                'schedules': schedules_data
            })
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/cleanup-legacy-schedules', methods=['POST'])
def cleanup_legacy_schedules():
    """Disable schedules without start_datetime (legacy schedules)"""
    try:
        db = get_db_session()
        try:
            # Find all enabled schedules without start_datetime
            legacy_schedules = db.query(DBSchedule).filter(
                DBSchedule.enabled == True,
                DBSchedule.start_datetime == None
            ).all()
            
            disabled_count = 0
            disabled_ids = []
            
            for schedule in legacy_schedules:
                schedule.enabled = False
                disabled_ids.append(schedule.id)
                disabled_count += 1
                print(f"[CLEANUP] Disabled legacy schedule: ID={schedule.id}, username={schedule.username}")
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Disabled {disabled_count} legacy schedule(s)',
                'disabled_schedule_ids': disabled_ids
            })
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/reports')
def debug_reports():
    """Debug endpoint to see all reports in database"""
    try:
        db = get_db_session()
        try:
            all_reports = db.query(Report).order_by(Report.created_at.desc()).all()
            reports_data = []
            for r in all_reports:
                reports_data.append({
                    'id': r.id,
                    'platform': getattr(r, 'platform', 'twitter'),  # Handle missing platform field
                    'username': r.username,
                    'keywords': r.keywords,
                    'tweet_count': r.tweet_count,
                    'account_type': r.account_type,
                    'lead_score': r.lead_score,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'has_report_content': bool(r.report_content),
                    'has_tweets_data': bool(r.tweets_data)
                })
            
            return jsonify({
                'total_reports': len(all_reports),
                'reports': reports_data
            })
        finally:
            db.close()
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/fix-platform-field', methods=['GET', 'POST'])
def fix_platform_field():
    """Add platform field to existing reports that don't have it"""
    try:
        db = get_db_session()
        try:
            # Update all reports without platform field
            updated = db.execute(
                "UPDATE reports SET platform = 'twitter' WHERE platform IS NULL"
            )
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Updated {updated.rowcount} reports with platform field',
                'updated_count': updated.rowcount
            })
        finally:
            db.close()
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/raw-reports')
def raw_reports():
    """Show raw database records from reports table"""
    try:
        db = get_db_session()
        try:
            # Check what database we're actually using
            db_type = 'PostgreSQL' if 'postgresql' in str(engine.url) else 'SQLite'
            
            if db_type == 'SQLite':
                return jsonify({
                    'warning': 'Currently using SQLite (ephemeral storage)',
                    'message': 'Data will be lost on restart. Check DATABASE_URL configuration.',
                    'database_type': db_type,
                    'connection_string': str(engine.url),
                    'reports_in_sqlite': db.query(Report).count()
                })
            
            # Get raw SQL results from PostgreSQL
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT 
                    id, 
                    platform, 
                    username, 
                    keywords, 
                    tweet_count, 
                    account_type, 
                    lead_score, 
                    created_at,
                    LENGTH(report_content) as content_length,
                    CASE WHEN tweets_data IS NULL THEN 'NULL' ELSE 'EXISTS' END as tweets_data_status
                FROM reports 
                ORDER BY created_at DESC 
                LIMIT 50
            """))
            
            rows = []
            for row in result:
                rows.append({
                    'id': row[0],
                    'platform': row[1],
                    'username': row[2],
                    'keywords': row[3],
                    'tweet_count': row[4],
                    'account_type': row[5],
                    'lead_score': row[6],
                    'created_at': str(row[7]),
                    'content_length': row[8],
                    'tweets_data_status': row[9]
                })
            
            return jsonify({
                'success': True,
                'total_rows': len(rows),
                'database_type': db_type,
                'connection_string': str(engine.url)[:60] + '...',
                'reports': rows
            })
        finally:
            db.close()
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'database_type': 'PostgreSQL' if 'postgresql' in str(engine.url) else 'SQLite',
            'connection_string': str(engine.url)
        }), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        username = data.get('username', '').strip()
        keywords_input = data.get('keywords', '').strip()
        filters = data.get('filters', {})
        min_keyword_mentions = data.get('min_keyword_mentions', 1)
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        scraper = TwitterScraper()
        tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100, filters=filters)
        
        if not tweets_data or 'data' not in tweets_data:
            return jsonify({'error': 'No tweets found or API error occurred'}), 404
        
        report_file = scraper.generate_report(tweets_data, username, keywords, min_keyword_mentions)
        
        json_file = report_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tweets_data, f, indent=2)
        
        # Read report content for display
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Get account analysis
        user_profile = tweets_data.get('user_profile', {})
        account_analysis = scraper.analyze_account_type(user_profile) if user_profile else {}
        
        # Save to database
        db = get_db_session()
        try:
            db_report = Report(
                platform='twitter',
                username=username,
                keywords=keywords,
                tweet_count=len(tweets_data['data']),
                account_type=account_analysis.get('type'),
                lead_score=account_analysis.get('score'),
                report_content=report_content,
                tweets_data=tweets_data,
                filters=filters
            )
            db.add(db_report)
            db.commit()
            report_id = db_report.id
        finally:
            db.close()
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report_file': report_file,
            'json_file': json_file,
            'tweet_count': len(tweets_data['data']),
            'report_content': report_content,
            'tweets_data': tweets_data['data'],
            'account_type': account_analysis.get('type'),
            'lead_score': account_analysis.get('score')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape-reddit', methods=['POST'])
def scrape_reddit():
    try:
        data = request.json
        subreddit = data.get('subreddit', '').strip()
        keywords_input = data.get('keywords', '').strip()
        time_filter = data.get('time_filter', 'week')
        min_keyword_mentions = data.get('min_keyword_mentions', 1)
        
        if not subreddit:
            return jsonify({'error': 'Subreddit is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        scraper = RedditScraper()
        posts_data = scraper.search_subreddit(subreddit, keywords=keywords, max_results=100, time_filter=time_filter)
        
        if not posts_data or 'data' not in posts_data:
            return jsonify({'error': 'No posts found or API error occurred'}), 404
        
        report_file = scraper.generate_report(posts_data, subreddit, keywords, min_keyword_mentions)
        
        json_file = report_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, indent=2)
        
        # Read report content for display
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Save to database
        db = get_db_session()
        try:
            db_report = Report(
                platform='reddit',
                username=subreddit,
                keywords=keywords,
                tweet_count=len(posts_data['data']),
                report_content=report_content,
                tweets_data=posts_data,
                filters={'time_filter': time_filter}
            )
            db.add(db_report)
            db.commit()
            report_id = db_report.id
        finally:
            db.close()
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report_file': report_file,
            'json_file': json_file,
            'post_count': len(posts_data['data']),
            'report_content': report_content,
            'posts_data': posts_data['data']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/discover-accounts', methods=['POST'])
def discover_accounts():
    """Discover Twitter accounts based on keywords"""
    try:
        data = request.json
        keywords_input = data.get('keywords', '').strip()
        max_results = data.get('max_results', 100)
        filters = data.get('filters', {})
        
        if not keywords_input:
            return jsonify({'error': 'Keywords are required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')]
        
        scraper = TwitterScraper()
        accounts_data = scraper.discover_accounts(keywords, max_results=max_results, filters=filters)
        
        if not accounts_data:
            return jsonify({'error': 'No accounts found'}), 404
        
        return jsonify({
            'success': True,
            'accounts': accounts_data['accounts'],
            'total_accounts': accounts_data['total_accounts'],
            'search_keywords': accounts_data['search_keywords'],
            'tweets_searched': accounts_data['tweets_searched']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bulk-scrape', methods=['POST'])
def bulk_scrape():
    """Scrape multiple Twitter accounts at once"""
    try:
        data = request.json
        usernames = data.get('usernames', [])
        keywords_input = data.get('keywords', '').strip()
        filters = data.get('filters', {})
        min_keyword_mentions = data.get('min_keyword_mentions', 1)
        
        if not usernames or len(usernames) == 0:
            return jsonify({'error': 'At least one username is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        scraper = TwitterScraper()
        results = []
        errors = []
        
        for username in usernames:
            try:
                tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100, filters=filters)
                
                if tweets_data and 'data' in tweets_data:
                    report_file = scraper.generate_report(tweets_data, username, keywords, min_keyword_mentions)
                    
                    # Read report content
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    
                    # Get account analysis
                    user_profile = tweets_data.get('user_profile', {})
                    account_analysis = scraper.analyze_account_type(user_profile) if user_profile else {}
                    
                    # Save to database
                    db = get_db_session()
                    try:
                        db_report = Report(
                            platform='twitter',
                            username=username,
                            keywords=keywords,
                            tweet_count=len(tweets_data['data']),
                            account_type=account_analysis.get('type'),
                            lead_score=account_analysis.get('score'),
                            report_content=report_content,
                            tweets_data=tweets_data,
                            filters=filters
                        )
                        db.add(db_report)
                        db.commit()
                        report_id = db_report.id
                    finally:
                        db.close()
                    
                    results.append({
                        'username': username,
                        'success': True,
                        'report_id': report_id,
                        'tweet_count': len(tweets_data['data']),
                        'account_type': account_analysis.get('type'),
                        'lead_score': account_analysis.get('score')
                    })
                else:
                    errors.append({
                        'username': username,
                        'error': 'No tweets found'
                    })
            except Exception as e:
                errors.append({
                    'username': username,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'errors': errors,
            'total_processed': len(usernames),
            'successful': len(results),
            'failed': len(errors)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reports', methods=['GET'])
def get_reports():
    """Get list of all reports"""
    try:
        db = get_db_session()
        try:
            reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
            reports_list = [r.to_dict() for r in reports]
            
            print(f"[REPORTS] Returning {len(reports_list)} reports")
            
            return jsonify({
                'success': True,
                'reports': reports_list,
                'total': len(reports_list)
            })
        finally:
            db.close()
    except Exception as e:
        print(f"[REPORTS] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get specific report by ID"""
    try:
        db = get_db_session()
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                return jsonify({'error': 'Report not found'}), 404
            
            return jsonify({
                'success': True,
                'report': report.to_dict(),
                'report_content': report.report_content,
                'tweets_data': report.tweets_data
            })
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/view-report/<path:filename>')
def view_report(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/schedules', methods=['GET'])
def get_schedules():
    """Get all schedules from database"""
    try:
        db = get_db_session()
        try:
            # Get all enabled schedules
            schedules = db.query(DBSchedule).filter(DBSchedule.enabled == True).all()
            
            # Filter out schedules without start_datetime (legacy schedules)
            valid_schedules = []
            for s in schedules:
                schedule_dict = s.to_dict()
                # Only include schedules with start_datetime
                if schedule_dict.get('start_datetime'):
                    valid_schedules.append(schedule_dict)
                else:
                    # Log legacy schedule found
                    print(f"[WARNING] Found legacy schedule without start_datetime: ID={s.id}, username={s.username}")
            
            return jsonify({'schedules': valid_schedules})
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedules', methods=['POST'])
def add_schedule():
    try:
        data = request.json
        username = data.get('username', '').strip()
        keywords_input = data.get('keywords', '').strip()
        frequency = data.get('frequency', 'daily')
        start_datetime_str = data.get('start_datetime')
        day = data.get('day')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        if not start_datetime_str:
            return jsonify({'error': 'Start date/time is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        # Parse start datetime (comes as YYYY-MM-DDTHH:MM from datetime-local input)
        try:
            start_datetime = datetime.fromisoformat(start_datetime_str)
        except ValueError:
            return jsonify({'error': 'Invalid date/time format'}), 400
        
        # Validate start datetime is in the future
        if start_datetime <= datetime.utcnow():
            return jsonify({'error': 'Start date/time must be in the future'}), 400
        
        # Save to database
        db = get_db_session()
        try:
            db_schedule = DBSchedule(
                username=username,
                keywords=keywords,
                frequency=frequency,
                start_datetime=start_datetime,
                next_run=start_datetime,  # First run is the start time
                day=day,
                enabled=True
            )
            db.add(db_schedule)
            db.commit()
            schedule_dict = db_schedule.to_dict()
        finally:
            db.close()
        
        # Add to scheduler
        scheduler.add_schedule_from_dict(schedule_dict)
        
        return jsonify({'success': True, 'schedule': schedule_dict})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    try:
        db = get_db_session()
        try:
            schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            if schedule:
                db.delete(schedule)
                db.commit()
        finally:
            db.close()
        
        scheduler.remove_schedule(schedule_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historical/<username>')
def get_historical(username):
    try:
        db = get_db_session()
        try:
            tweets = db.query(HistoricalTweet).filter(
                HistoricalTweet.username == username
            ).order_by(HistoricalTweet.created_at.desc()).all()
            
            if not tweets:
                return jsonify({'error': 'No historical data found'}), 404
            
            return jsonify({
                'success': True,
                'tweets': [t.to_dict() for t in tweets],
                'count': len(tweets)
            })
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

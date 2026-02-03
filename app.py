from flask import Flask, render_template, request, send_file, jsonify
import os
import json
from datetime import datetime
from twitter_scraper import TwitterScraper
from reddit_scraper import RedditScraper
from scheduler import ScheduledScraper
from database import init_db, get_db_session, Report, Schedule as DBSchedule, HistoricalTweet, DeepHistory, engine, save_to_deep_history, search_deep_history

# Social Listening Platform - v2.6 (Report History Pagination + Scheduler Fix)
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

@app.route('/cron/run-schedules', methods=['POST'])
def cron_run_schedules():
    """
    Cron endpoint to run scheduled scrapes
    Called by Railway Cron Jobs every hour
    
    This replaces the in-memory scheduler with external cron jobs
    """
    try:
        from datetime import datetime, timedelta
        
        db = get_db_session()
        results = {
            'executed': [],
            'skipped': [],
            'errors': []
        }
        
        try:
            # Get current time
            now = datetime.utcnow()
            
            # Find schedules that should run now
            # Check schedules where next_run is in the past or within the next hour
            schedules_to_run = db.query(DBSchedule).filter(
                DBSchedule.enabled == True,
                DBSchedule.next_run <= now + timedelta(hours=1)
            ).all()
            
            print(f"[CRON] Found {len(schedules_to_run)} schedules to check")
            
            for schedule in schedules_to_run:
                try:
                    # Check if it's actually time to run (within 5 minutes of scheduled time)
                    if schedule.next_run and schedule.next_run <= now + timedelta(minutes=5):
                        print(f"[CRON] Running schedule {schedule.id} for @{schedule.username}")
                        
                        # Run the scrape
                        scraper = TwitterScraper()
                        tweets_data = scraper.search_user_tweets(
                            schedule.username, 
                            keywords=schedule.keywords, 
                            max_results=100
                        )
                        
                        if tweets_data and 'data' in tweets_data:
                            # Generate report
                            report_file = scraper.generate_report(
                                tweets_data, 
                                schedule.username, 
                                schedule.keywords
                            )
                            
                            # Read report content
                            with open(report_file, 'r', encoding='utf-8') as f:
                                report_content = f.read()
                            
                            # Get account analysis
                            user_profile = tweets_data.get('user_profile', {})
                            account_analysis = scraper.analyze_account_type(user_profile) if user_profile else {}
                            
                            # Save to database
                            db_report = Report(
                                platform='twitter',
                                username=schedule.username,
                                keywords=schedule.keywords,
                                tweet_count=len(tweets_data['data']),
                                account_type=account_analysis.get('type'),
                                lead_score=account_analysis.get('score'),
                                report_content=report_content,
                                tweets_data=tweets_data,
                                filters={}
                            )
                            db.add(db_report)
                            db.flush()
                            
                            # Save to deep_history
                            try:
                                save_to_deep_history(
                                    username=schedule.username,
                                    platform='twitter',
                                    raw_json={
                                        'tweets': tweets_data['data'],
                                        'account_info': user_profile,
                                        'keywords': schedule.keywords,
                                        'lead_score': account_analysis.get('score'),
                                        'account_type': account_analysis.get('type')
                                    },
                                    raw_text=report_content,
                                    report_id=db_report.id,
                                    scrape_type='scheduled',
                                    filters_used={}
                                )
                            except Exception as dh_error:
                                print(f"[CRON] Warning: Failed to save to deep_history: {dh_error}")
                            
                            # Update schedule
                            schedule.last_run = now
                            
                            # Calculate next run based on frequency
                            if schedule.frequency == 'once':
                                schedule.enabled = False
                                schedule.next_run = None
                            elif schedule.frequency == 'hourly':
                                schedule.next_run = now + timedelta(hours=1)
                            elif schedule.frequency == 'daily':
                                schedule.next_run = now + timedelta(days=1)
                            elif schedule.frequency == 'weekly':
                                schedule.next_run = now + timedelta(weeks=1)
                            
                            db.commit()
                            
                            results['executed'].append({
                                'schedule_id': schedule.id,
                                'username': schedule.username,
                                'tweet_count': len(tweets_data['data']),
                                'next_run': schedule.next_run.isoformat() if schedule.next_run else None
                            })
                            
                            print(f"[CRON] ✓ Completed schedule {schedule.id} for @{schedule.username}")
                        else:
                            results['skipped'].append({
                                'schedule_id': schedule.id,
                                'username': schedule.username,
                                'reason': 'No tweets found'
                            })
                            print(f"[CRON] ✗ No tweets found for @{schedule.username}")
                    else:
                        results['skipped'].append({
                            'schedule_id': schedule.id,
                            'username': schedule.username,
                            'reason': f'Not yet time (next_run: {schedule.next_run})'
                        })
                        
                except Exception as e:
                    results['errors'].append({
                        'schedule_id': schedule.id,
                        'username': schedule.username,
                        'error': str(e)
                    })
                    print(f"[CRON] ✗ Error running schedule {schedule.id}: {e}")
                    db.rollback()
            
            return jsonify({
                'success': True,
                'timestamp': now.isoformat(),
                'results': results,
                'summary': {
                    'executed': len(results['executed']),
                    'skipped': len(results['skipped']),
                    'errors': len(results['errors'])
                }
            })
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"[CRON] Fatal error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/cron/check-stale-schedules', methods=['POST'])
def cron_check_stale_schedules():
    """
    Cron endpoint to check for stale schedules (not run for 2+ days)
    Sends email notification if any schedules are stale
    Called by Railway Cron Jobs daily
    """
    try:
        from datetime import datetime, timedelta
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        db = get_db_session()
        
        try:
            now = datetime.utcnow()
            two_days_ago = now - timedelta(days=2)
            
            # Find enabled schedules that haven't run in 2+ days
            stale_schedules = db.query(DBSchedule).filter(
                DBSchedule.enabled == True,
                DBSchedule.last_run < two_days_ago
            ).all()
            
            # Also check schedules that have never run and were created 2+ days ago
            never_run_schedules = db.query(DBSchedule).filter(
                DBSchedule.enabled == True,
                DBSchedule.last_run == None,
                DBSchedule.created_at < two_days_ago
            ).all()
            
            all_stale = stale_schedules + never_run_schedules
            
            print(f"[STALE_CHECK] Found {len(all_stale)} stale schedule(s)")
            
            if len(all_stale) == 0:
                return jsonify({
                    'success': True,
                    'message': 'No stale schedules found',
                    'stale_count': 0
                })
            
            # Get email configuration from environment
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            notification_email = os.getenv('NOTIFICATION_EMAIL')
            
            if not all([smtp_user, smtp_password, notification_email]):
                print("[STALE_CHECK] Email not configured. Set SMTP_USER, SMTP_PASSWORD, and NOTIFICATION_EMAIL environment variables.")
                return jsonify({
                    'success': False,
                    'error': 'Email configuration missing',
                    'stale_count': len(all_stale),
                    'stale_schedules': [
                        {
                            'id': s.id,
                            'username': s.username,
                            'last_run': s.last_run.isoformat() if s.last_run else 'Never',
                            'days_since_run': (now - s.last_run).days if s.last_run else 'N/A'
                        }
                        for s in all_stale
                    ]
                })
            
            # Build email content
            email_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">⚠️ Stale Schedule Alert</h2>
    <p>The following schedule(s) have not run for 2 or more days:</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f8f9fa;">
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Schedule ID</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Username</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Frequency</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Last Run</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Days Since Run</th>
            </tr>
        </thead>
        <tbody>
"""
            
            for schedule in all_stale:
                last_run_text = schedule.last_run.strftime('%Y-%m-%d %H:%M UTC') if schedule.last_run else 'Never'
                days_since = (now - schedule.last_run).days if schedule.last_run else 'N/A'
                
                email_body += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 12px;">{schedule.id}</td>
                <td style="border: 1px solid #ddd; padding: 12px;">@{schedule.username}</td>
                <td style="border: 1px solid #ddd; padding: 12px;">{schedule.frequency}</td>
                <td style="border: 1px solid #ddd; padding: 12px;">{last_run_text}</td>
                <td style="border: 1px solid #ddd; padding: 12px;">{days_since}</td>
            </tr>
"""
            
            email_body += """
        </tbody>
    </table>
    
    <p><strong>Action Required:</strong></p>
    <ul>
        <li>Check if Railway Cron Jobs are running properly</li>
        <li>Verify the <code>/cron/run-schedules</code> endpoint is accessible</li>
        <li>Review Railway deployment logs for errors</li>
        <li>Consider manually running schedules using the "Run Now" button</li>
    </ul>
    
    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This is an automated notification from your Social Listening Platform.<br>
        Timestamp: """ + now.strftime('%Y-%m-%d %H:%M:%S UTC') + """
    </p>
</body>
</html>
"""
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⚠️ Stale Schedule Alert - {len(all_stale)} Schedule(s) Not Running'
            msg['From'] = smtp_user
            msg['To'] = notification_email
            
            html_part = MIMEText(email_body, 'html')
            msg.attach(html_part)
            
            # Send email
            try:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                
                print(f"[STALE_CHECK] ✓ Email notification sent to {notification_email}")
                
                return jsonify({
                    'success': True,
                    'message': f'Email notification sent for {len(all_stale)} stale schedule(s)',
                    'stale_count': len(all_stale),
                    'notification_sent_to': notification_email
                })
                
            except Exception as email_error:
                print(f"[STALE_CHECK] ✗ Failed to send email: {email_error}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to send email: {str(email_error)}',
                    'stale_count': len(all_stale),
                    'stale_schedules': [
                        {
                            'id': s.id,
                            'username': s.username,
                            'last_run': s.last_run.isoformat() if s.last_run else 'Never'
                        }
                        for s in all_stale
                    ]
                }), 500
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"[STALE_CHECK] Fatal error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/debug/test-schedules', methods=['GET'])
def test_schedules():
    """Test all schedules to see which ones can find tweets"""
    try:
        db = get_db_session()
        results = []
        
        try:
            schedules = db.query(DBSchedule).filter(DBSchedule.enabled == True).all()
            scraper = TwitterScraper()
            
            for schedule in schedules:
                print(f"[TEST] Testing schedule {schedule.id}: @{schedule.username}")
                
                # Test without keywords first
                tweets_no_keywords = scraper.search_user_tweets(
                    schedule.username,
                    keywords=None,
                    max_results=10
                )
                
                # Test with keywords if they exist
                tweets_with_keywords = None
                if schedule.keywords:
                    tweets_with_keywords = scraper.search_user_tweets(
                        schedule.username,
                        keywords=schedule.keywords,
                        max_results=10
                    )
                
                result = {
                    'schedule_id': schedule.id,
                    'username': schedule.username,
                    'keywords': schedule.keywords,
                    'without_keywords': {
                        'found': bool(tweets_no_keywords and 'data' in tweets_no_keywords),
                        'count': len(tweets_no_keywords.get('data', [])) if tweets_no_keywords else 0
                    },
                    'with_keywords': {
                        'found': bool(tweets_with_keywords and 'data' in tweets_with_keywords),
                        'count': len(tweets_with_keywords.get('data', [])) if tweets_with_keywords else 0
                    } if schedule.keywords else None,
                    'recommendation': ''
                }
                
                # Generate recommendation
                if result['without_keywords']['found']:
                    if schedule.keywords and not result['with_keywords']['found']:
                        result['recommendation'] = '⚠️ Remove keywords - account is active but tweets don\'t match keywords'
                    else:
                        result['recommendation'] = '✅ Working fine'
                else:
                    result['recommendation'] = '❌ No recent tweets (last 7 days) - keep schedule to catch future tweets'
                
                results.append(result)
                print(f"[TEST] Result: {result['recommendation']}")
            
            return jsonify({
                'success': True,
                'total_schedules': len(schedules),
                'results': results,
                'summary': {
                    'working': len([r for r in results if '✅' in r['recommendation']]),
                    'needs_keyword_removal': len([r for r in results if '⚠️' in r['recommendation']]),
                    'inactive': len([r for r in results if '❌' in r['recommendation']])
                }
            })
            
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/test-twitter-api/<username>', methods=['GET'])
def test_twitter_api(username):
    """Test Twitter API directly for a specific username with detailed error info"""
    try:
        import requests
        
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            return jsonify({
                'error': 'TWITTER_BEARER_TOKEN not configured',
                'solution': 'Add TWITTER_BEARER_TOKEN to Railway environment variables'
            }), 500
        
        headers = {"Authorization": f"Bearer {bearer_token}"}
        base_url = "https://api.twitter.com/2"
        
        # Test 1: Get user info
        user_endpoint = f"{base_url}/users/by/username/{username}"
        user_params = {"user.fields": "public_metrics,created_at,description,verified"}
        user_response = requests.get(user_endpoint, headers=headers, params=user_params)
        
        user_result = {
            'status_code': user_response.status_code,
            'success': user_response.status_code == 200,
            'data': user_response.json() if user_response.status_code == 200 else None,
            'error': user_response.json() if user_response.status_code != 200 else None
        }
        
        # Test 2: Search recent tweets (no keywords)
        search_endpoint = f"{base_url}/tweets/search/recent"
        search_params = {
            "query": f"from:{username}",
            "max_results": 10,
            "tweet.fields": "created_at,public_metrics,text"
        }
        search_response = requests.get(search_endpoint, headers=headers, params=search_params)
        
        search_result = {
            'status_code': search_response.status_code,
            'success': search_response.status_code == 200,
            'query': search_params['query'],
            'data': search_response.json() if search_response.status_code == 200 else None,
            'error': search_response.json() if search_response.status_code != 200 else None,
            'tweet_count': len(search_response.json().get('data', [])) if search_response.status_code == 200 else 0
        }
        
        # Diagnosis
        diagnosis = []
        if not user_result['success']:
            if user_result['status_code'] == 429:
                diagnosis.append('🚫 RATE LIMIT: Twitter API rate limit exceeded. Wait 15 minutes.')
            elif user_result['status_code'] == 401:
                diagnosis.append('🔑 AUTH ERROR: Invalid or expired Twitter Bearer Token')
            elif user_result['status_code'] == 404:
                diagnosis.append('❌ USER NOT FOUND: Account does not exist or username is wrong')
            else:
                diagnosis.append(f'⚠️ API ERROR: Status {user_result["status_code"]}')
        elif not search_result['success']:
            if search_result['status_code'] == 429:
                diagnosis.append('🚫 RATE LIMIT: Twitter API rate limit exceeded. Wait 15 minutes.')
            elif search_result['status_code'] == 401:
                diagnosis.append('🔑 AUTH ERROR: Invalid or expired Twitter Bearer Token')
            else:
                diagnosis.append(f'⚠️ SEARCH ERROR: Status {search_result["status_code"]}')
        elif search_result['tweet_count'] == 0:
            diagnosis.append('📭 NO TWEETS: Account exists but no tweets found in last 7 days')
            diagnosis.append('   Possible reasons:')
            diagnosis.append('   - Account hasn\'t tweeted in 7+ days')
            diagnosis.append('   - Account is protected/private')
            diagnosis.append('   - Tweets were deleted')
        else:
            diagnosis.append(f'✅ SUCCESS: Found {search_result["tweet_count"]} tweets')
        
        return jsonify({
            'username': username,
            'user_lookup': user_result,
            'tweet_search': search_result,
            'diagnosis': diagnosis,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
                    scrape_type='quick',
                    filters_used=filters
                )
            except Exception as dh_error:
                print(f"[WARNING] Failed to save to deep_history: {dh_error}")
                # Don't fail the request if deep_history fails
                
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
            
            # Save to deep_history for AI/ML features
            try:
                save_to_deep_history(
                    username=subreddit,
                    platform='reddit',
                    raw_json={
                        'posts': posts_data['data'],
                        'keywords': keywords,
                        'time_filter': time_filter
                    },
                    raw_text=report_content,
                    report_id=report_id,
                    scrape_type='quick',
                    filters_used={'time_filter': time_filter}
                )
            except Exception as dh_error:
                print(f"[WARNING] Failed to save to deep_history: {dh_error}")
                
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

@app.route('/find-similar-accounts', methods=['POST'])
def find_similar_accounts():
    """Find accounts similar to a reference account"""
    try:
        data = request.json
        reference_username = data.get('reference_username', '').strip().replace('@', '')
        max_results = data.get('max_results', 100)
        filters = data.get('filters', {})
        
        if not reference_username:
            return jsonify({'error': 'Reference username is required'}), 400
        
        scraper = TwitterScraper()
        similar_data = scraper.find_similar_accounts(reference_username, max_results=max_results, filters=filters)
        
        if not similar_data:
            return jsonify({'error': 'Could not analyze reference account'}), 404
        
        return jsonify({
            'success': True,
            'accounts': similar_data['accounts'],
            'total_accounts': similar_data['total_accounts'],
            'reference_account': similar_data['reference_account'],
            'extracted_keywords': similar_data['extracted_keywords'],
            'tweets_searched': similar_data.get('tweets_searched', 0),
            'message': similar_data.get('message', '')
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
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
                                    'account_type': account_analysis.get('type')
                                },
                                raw_text=report_content,
                                report_id=report_id,
                                scrape_type='bulk',
                                filters_used=filters
                            )
                        except Exception as dh_error:
                            print(f"[WARNING] Failed to save to deep_history: {dh_error}")
                            
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

@app.route('/search-history', methods=['POST'])
def search_history():
    """Full-text search across deep_history"""
    try:
        data = request.json
        query_text = data.get('query', '').strip()
        platform = data.get('platform')  # Optional: 'twitter' or 'reddit'
        limit = data.get('limit', 50)
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = search_deep_history(query_text, platform=platform, limit=limit)
        
        results_list = [r.to_dict() for r in results]
        
        return jsonify({
            'success': True,
            'results': results_list,
            'total': len(results_list),
            'query': query_text
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/deep-history', methods=['GET'])
def get_deep_history():
    """
    Get deep_history records with optional filters
    
    Query parameters:
    - platform: Filter by platform ('twitter' or 'reddit')
    - username: Filter by username
    - scrape_type: Filter by scrape type ('quick', 'scheduled', 'bulk', 'discovery')
    - limit: Number of records to return (default: 50, max: 500)
    - offset: Pagination offset (default: 0)
    - format: Response format ('summary' or 'full', default: 'summary')
    """
    try:
        from database import DeepHistory
        
        # Get query parameters
        platform = request.args.get('platform')
        username = request.args.get('username')
        scrape_type = request.args.get('scrape_type')
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))
        response_format = request.args.get('format', 'summary')
        
        db = get_db_session()
        try:
            # Build query
            query = db.query(DeepHistory)
            
            # Apply filters
            if platform:
                query = query.filter(DeepHistory.platform == platform)
            if username:
                query = query.filter(DeepHistory.username == username)
            if scrape_type:
                query = query.filter(DeepHistory.scrape_type == scrape_type)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            records = query.order_by(DeepHistory.scraped_at.desc()).offset(offset).limit(limit).all()
            
            # Format response based on requested format
            if response_format == 'full':
                # Full data including raw_json and raw_text
                records_list = []
                for r in records:
                    record_dict = r.to_dict()
                    record_dict['raw_json'] = r.raw_json
                    record_dict['raw_text'] = r.raw_text[:500] + '...' if r.raw_text and len(r.raw_text) > 500 else r.raw_text
                    record_dict['account_snapshot'] = r.account_snapshot
                    records_list.append(record_dict)
            else:
                # Summary format (default)
                records_list = [r.to_dict() for r in records]
            
            return jsonify({
                'success': True,
                'records': records_list,
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'returned': len(records_list),
                'filters': {
                    'platform': platform,
                    'username': username,
                    'scrape_type': scrape_type
                }
            })
        finally:
            db.close()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deep-history/<int:record_id>', methods=['GET'])
def get_deep_history_record(record_id):
    """Get a specific deep_history record by ID with full data"""
    try:
        from database import DeepHistory
        
        db = get_db_session()
        try:
            record = db.query(DeepHistory).filter(DeepHistory.id == record_id).first()
            
            if not record:
                return jsonify({'error': 'Record not found'}), 404
            
            # Return full record with all data
            record_dict = {
                'id': record.id,
                'report_id': record.report_id,
                'username': record.username,
                'platform': record.platform,
                'scraped_at': record.scraped_at.isoformat() if record.scraped_at else None,
                'scrape_type': record.scrape_type,
                'total_tweets': record.total_tweets,
                'total_engagement': record.total_engagement,
                'avg_sentiment': record.avg_sentiment,
                'lead_score': record.lead_score,
                'account_type': record.account_type,
                'keywords': record.keywords,
                'hashtags': record.hashtags,
                'mentions': record.mentions,
                'urls': record.urls,
                'tweet_ids': record.tweet_ids,
                'account_snapshot': record.account_snapshot,
                'raw_json': record.raw_json,
                'raw_text': record.raw_text,
                'raw_csv': record.raw_csv,
                'topics': record.topics,
                'ai_analysis': record.ai_analysis,
                'ai_summary': record.ai_summary,
                'filters_used': record.filters_used
            }
            
            return jsonify({
                'success': True,
                'record': record_dict
            })
        finally:
            db.close()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deep-history/stats', methods=['GET'])
def get_deep_history_stats():
    """Get statistics about deep_history data"""
    try:
        from database import DeepHistory
        from sqlalchemy import func
        
        db = get_db_session()
        try:
            # Total records
            total_records = db.query(func.count(DeepHistory.id)).scalar()
            
            # Records by platform
            platform_stats = db.query(
                DeepHistory.platform,
                func.count(DeepHistory.id).label('count')
            ).group_by(DeepHistory.platform).all()
            
            # Records by scrape type
            scrape_type_stats = db.query(
                DeepHistory.scrape_type,
                func.count(DeepHistory.id).label('count')
            ).group_by(DeepHistory.scrape_type).all()
            
            # Top accounts by scrape count
            top_accounts = db.query(
                DeepHistory.username,
                DeepHistory.platform,
                func.count(DeepHistory.id).label('scrape_count')
            ).group_by(DeepHistory.username, DeepHistory.platform).order_by(
                func.count(DeepHistory.id).desc()
            ).limit(10).all()
            
            # Total tweets/posts collected
            total_tweets = db.query(func.sum(DeepHistory.total_tweets)).scalar() or 0
            
            # Total engagement
            total_engagement = db.query(func.sum(DeepHistory.total_engagement)).scalar() or 0
            
            # Date range
            first_scrape = db.query(func.min(DeepHistory.scraped_at)).scalar()
            last_scrape = db.query(func.max(DeepHistory.scraped_at)).scalar()
            
            # Unique accounts
            unique_accounts = db.query(func.count(func.distinct(DeepHistory.username))).scalar()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_records': total_records,
                    'total_tweets_collected': total_tweets,
                    'total_engagement': total_engagement,
                    'unique_accounts': unique_accounts,
                    'by_platform': {p: c for p, c in platform_stats},
                    'by_scrape_type': {st: c for st, c in scrape_type_stats},
                    'top_accounts': [
                        {'username': u, 'platform': p, 'scrape_count': c}
                        for u, p, c in top_accounts
                    ],
                    'date_range': {
                        'first_scrape': first_scrape.isoformat() if first_scrape else None,
                        'last_scrape': last_scrape.isoformat() if last_scrape else None
                    }
                }
            })
        finally:
            db.close()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deep-history/export', methods=['GET'])
def export_deep_history():
    """
    Export deep_history data as CSV
    
    Query parameters:
    - platform: Filter by platform
    - username: Filter by username
    - scrape_type: Filter by scrape type
    - limit: Number of records (default: 100, max: 1000)
    """
    try:
        from database import DeepHistory
        import csv
        from io import StringIO
        
        # Get query parameters
        platform = request.args.get('platform')
        username = request.args.get('username')
        scrape_type = request.args.get('scrape_type')
        limit = min(int(request.args.get('limit', 100)), 1000)
        
        db = get_db_session()
        try:
            # Build query
            query = db.query(DeepHistory)
            
            if platform:
                query = query.filter(DeepHistory.platform == platform)
            if username:
                query = query.filter(DeepHistory.username == username)
            if scrape_type:
                query = query.filter(DeepHistory.scrape_type == scrape_type)
            
            records = query.order_by(DeepHistory.scraped_at.desc()).limit(limit).all()
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'id', 'username', 'platform', 'scraped_at', 'scrape_type',
                'total_tweets', 'total_engagement', 'lead_score', 'account_type',
                'keywords', 'hashtags', 'mentions', 'avg_sentiment'
            ])
            
            # Write data
            for r in records:
                writer.writerow([
                    r.id,
                    r.username,
                    r.platform,
                    r.scraped_at.isoformat() if r.scraped_at else '',
                    r.scrape_type,
                    r.total_tweets,
                    r.total_engagement,
                    r.lead_score,
                    r.account_type,
                    ','.join(r.keywords) if r.keywords else '',
                    ','.join(r.hashtags[:10]) if r.hashtags else '',  # Limit to 10
                    ','.join(r.mentions[:10]) if r.mentions else '',  # Limit to 10
                    r.avg_sentiment
                ])
            
            # Create response
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=deep_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
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
    """Get all schedules from database (both active and paused)"""
    try:
        db = get_db_session()
        try:
            # Get ALL schedules (enabled and disabled)
            schedules = db.query(DBSchedule).all()
            
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

@app.route('/schedules/<int:schedule_id>/pause', methods=['POST'])
def pause_schedule(schedule_id):
    """Pause a schedule (disable it temporarily)"""
    try:
        db = get_db_session()
        try:
            schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            
            if not schedule:
                return jsonify({'error': 'Schedule not found'}), 404
            
            if not schedule.enabled:
                return jsonify({'error': 'Schedule is already paused'}), 400
            
            schedule.enabled = False
            db.commit()
            
            print(f"[PAUSE] Schedule {schedule_id} (@{schedule.username}) paused")
            
            return jsonify({
                'success': True,
                'message': f'Schedule for @{schedule.username} paused',
                'schedule': schedule.to_dict()
            })
            
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedules/<int:schedule_id>/resume', methods=['POST'])
def resume_schedule(schedule_id):
    """Resume a paused schedule (enable it)"""
    try:
        db = get_db_session()
        try:
            schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            
            if not schedule:
                return jsonify({'error': 'Schedule not found'}), 404
            
            if schedule.enabled:
                return jsonify({'error': 'Schedule is already active'}), 400
            
            schedule.enabled = True
            db.commit()
            
            print(f"[RESUME] Schedule {schedule_id} (@{schedule.username}) resumed")
            
            return jsonify({
                'success': True,
                'message': f'Schedule for @{schedule.username} resumed',
                'schedule': schedule.to_dict()
            })
            
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedules/<int:schedule_id>/run', methods=['POST'])
def run_schedule_now(schedule_id):
    """
    Manually trigger a schedule to run immediately
    Does not affect the regular schedule timing
    """
    try:
        db = get_db_session()
        try:
            # Get the schedule
            schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            
            if not schedule:
                return jsonify({'error': 'Schedule not found'}), 404
            
            if not schedule.enabled:
                return jsonify({'error': 'Schedule is disabled'}), 400
            
            print(f"[MANUAL_RUN] Running schedule {schedule_id} for @{schedule.username}")
            
            # Run the scrape
            scraper = TwitterScraper()
            tweets_data = scraper.search_user_tweets(
                schedule.username, 
                keywords=schedule.keywords, 
                max_results=100
            )
            
            if tweets_data and 'data' in tweets_data:
                # Generate report
                report_file = scraper.generate_report(
                    tweets_data, 
                    schedule.username, 
                    schedule.keywords
                )
                
                # Read report content
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                # Get account analysis
                user_profile = tweets_data.get('user_profile', {})
                account_analysis = scraper.analyze_account_type(user_profile) if user_profile else {}
                
                # Save to database
                db_report = Report(
                    platform='twitter',
                    username=schedule.username,
                    keywords=schedule.keywords,
                    tweet_count=len(tweets_data['data']),
                    account_type=account_analysis.get('type'),
                    lead_score=account_analysis.get('score'),
                    report_content=report_content,
                    tweets_data=tweets_data,
                    filters={}
                )
                db.add(db_report)
                db.flush()
                
                # Save to deep_history
                try:
                    save_to_deep_history(
                        username=schedule.username,
                        platform='twitter',
                        raw_json={
                            'tweets': tweets_data['data'],
                            'account_info': user_profile,
                            'keywords': schedule.keywords,
                            'lead_score': account_analysis.get('score'),
                            'account_type': account_analysis.get('type')
                        },
                        raw_text=report_content,
                        report_id=db_report.id,
                        scrape_type='manual',
                        filters_used={}
                    )
                except Exception as dh_error:
                    print(f"[MANUAL_RUN] Warning: Failed to save to deep_history: {dh_error}")
                
                # Update last_run but don't change next_run (preserve schedule)
                schedule.last_run = datetime.utcnow()
                db.commit()
                
                print(f"[MANUAL_RUN] ✓ Completed manual run for @{schedule.username}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully scraped @{schedule.username}',
                    'tweet_count': len(tweets_data['data']),
                    'report_id': db_report.id,
                    'account_type': account_analysis.get('type'),
                    'lead_score': account_analysis.get('score')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No tweets found'
                }), 404
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"[MANUAL_RUN] Error: {e}")
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

from flask import Flask, render_template, request, send_file, jsonify
import os
import json
from datetime import datetime
from twitter_scraper import TwitterScraper
from scheduler import ScheduledScraper
from database import init_db, get_db_session, Report, Schedule as DBSchedule, HistoricalTweet

app = Flask(__name__)

# Initialize database
init_db()

scheduler = ScheduledScraper()

# Start scheduler on app startup
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        username = data.get('username', '').strip()
        keywords_input = data.get('keywords', '').strip()
        filters = data.get('filters', {})
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        scraper = TwitterScraper()
        tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100, filters=filters)
        
        if not tweets_data or 'data' not in tweets_data:
            return jsonify({'error': 'No tweets found or API error occurred'}), 404
        
        report_file = scraper.generate_report(tweets_data, username, keywords)
        
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

@app.route('/reports', methods=['GET'])
def get_reports():
    """Get list of all reports"""
    try:
        db = get_db_session()
        try:
            reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
            return jsonify({
                'success': True,
                'reports': [r.to_dict() for r in reports]
            })
        finally:
            db.close()
    except Exception as e:
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
            schedules = db.query(DBSchedule).filter(DBSchedule.enabled == True).all()
            return jsonify({'schedules': [s.to_dict() for s in schedules]})
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
        time_str = data.get('time', '09:00')
        day = data.get('day')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        # Save to database
        db = get_db_session()
        try:
            db_schedule = DBSchedule(
                username=username,
                keywords=keywords,
                frequency=frequency,
                time=time_str,
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

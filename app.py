from flask import Flask, render_template, request, send_file, jsonify
import os
import json
from datetime import datetime
from twitter_scraper import TwitterScraper
from scheduler import ScheduledScraper

app = Flask(__name__)
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
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else None
        
        scraper = TwitterScraper()
        tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100)
        
        if not tweets_data or 'data' not in tweets_data:
            return jsonify({'error': 'No tweets found or API error occurred'}), 404
        
        report_file = scraper.generate_report(tweets_data, username, keywords)
        
        json_file = report_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tweets_data, f, indent=2)
        
        # Read report content for display
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return jsonify({
            'success': True,
            'report_file': report_file,
            'json_file': json_file,
            'tweet_count': len(tweets_data['data']),
            'report_content': report_content,
            'tweets_data': tweets_data['data']
        })
    
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
    return jsonify({'schedules': scheduler.schedules})

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
        
        schedule_config = scheduler.add_schedule(username, keywords, frequency, time_str, day)
        return jsonify({'success': True, 'schedule': schedule_config})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    try:
        scheduler.remove_schedule(schedule_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historical/<username>')
def get_historical(username):
    try:
        history_file = f'historical_data/{username}_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
            return jsonify({'success': True, 'tweets': history, 'count': len(history)})
        else:
            return jsonify({'error': 'No historical data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

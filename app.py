from flask import Flask, render_template, request, send_file, jsonify
import os
import json
from datetime import datetime
from twitter_scraper import TwitterScraper

app = Flask(__name__)

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
        
        return jsonify({
            'success': True,
            'report_file': report_file,
            'json_file': json_file,
            'tweet_count': len(tweets_data['data'])
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

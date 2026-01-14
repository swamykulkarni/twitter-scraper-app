import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TwitterScraper:
    def __init__(self):
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found in .env file")
        
        self.base_url = "https://api.x.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
    
    def search_user_tweets(self, username, keywords=None, max_results=100):
        """
        Search tweets from a specific user, optionally filtered by keywords
        
        Args:
            username: Twitter handle (without @)
            keywords: List of keywords to filter by
            max_results: Maximum number of tweets to retrieve (10-100)
        """
        # First, get the user ID from username
        user_id = self._get_user_id(username)
        if not user_id:
            return None
        
        # Build query
        query = f"from:{username}"
        if keywords:
            keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])
            query = f"({query}) ({keyword_query})"
        
        # Search tweets
        endpoint = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,text",
            "expansions": "author_id",
            "user.fields": "username,name"
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    
    def _get_user_id(self, username):
        """Get user ID from username"""
        endpoint = f"{self.base_url}/users/by/username/{username}"
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()['data']['id']
        else:
            print(f"Error getting user ID: {response.status_code}")
            return None
    
    def filter_by_keywords(self, tweets_data, keywords):
        """Filter tweets that contain any of the keywords"""
        if not tweets_data or 'data' not in tweets_data:
            return []
        
        filtered = []
        for tweet in tweets_data['data']:
            text_lower = tweet['text'].lower()
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    filtered.append(tweet)
                    break
        
        return filtered
    
    def generate_report(self, tweets_data, username, keywords=None):
        """Generate a formatted report from tweet data"""
        if not tweets_data or 'data' not in tweets_data:
            return "No tweets found."
        
        tweets = tweets_data['data']
        
        # Create reports directory
        os.makedirs('reports', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/twitter_report_{username}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"TWITTER ANALYSIS REPORT\n")
            f.write(f"Username: @{username}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if keywords:
                f.write(f"Keywords: {', '.join(keywords)}\n")
            f.write(f"Total Tweets Found: {len(tweets)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            total_likes = sum(tweet.get('public_metrics', {}).get('like_count', 0) for tweet in tweets)
            total_retweets = sum(tweet.get('public_metrics', {}).get('retweet_count', 0) for tweet in tweets)
            total_replies = sum(tweet.get('public_metrics', {}).get('reply_count', 0) for tweet in tweets)
            
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Likes: {total_likes}\n")
            f.write(f"Total Retweets: {total_retweets}\n")
            f.write(f"Total Replies: {total_replies}\n")
            f.write(f"Average Likes per Tweet: {total_likes/len(tweets):.2f}\n")
            f.write(f"Average Retweets per Tweet: {total_retweets/len(tweets):.2f}\n\n")
            
            # Keyword analysis
            if keywords:
                f.write("KEYWORD ANALYSIS\n")
                f.write("-" * 80 + "\n")
                for keyword in keywords:
                    count = sum(1 for tweet in tweets if keyword.lower() in tweet['text'].lower())
                    f.write(f"'{keyword}': {count} mentions\n")
                f.write("\n")
            
            # Individual tweets
            f.write("DETAILED TWEETS\n")
            f.write("-" * 80 + "\n\n")
            
            for i, tweet in enumerate(tweets, 1):
                f.write(f"Tweet #{i}\n")
                f.write(f"Date: {tweet.get('created_at', 'N/A')}\n")
                f.write(f"Text: {tweet['text']}\n")
                metrics = tweet.get('public_metrics', {})
                f.write(f"Likes: {metrics.get('like_count', 0)} | ")
                f.write(f"Retweets: {metrics.get('retweet_count', 0)} | ")
                f.write(f"Replies: {metrics.get('reply_count', 0)}\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"Report saved to: {filename}")
        return filename


def main():
    # Example usage
    scraper = TwitterScraper()
    
    # Configuration
    username = input("Enter Twitter username (without @): ")
    keywords_input = input("Enter keywords separated by commas (or press Enter to skip): ")
    keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else None
    
    print(f"\nSearching tweets from @{username}...")
    if keywords:
        print(f"Filtering by keywords: {', '.join(keywords)}")
    
    # Search tweets
    tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100)
    
    if tweets_data:
        # Generate report
        report_file = scraper.generate_report(tweets_data, username, keywords)
        print(f"\n✓ Analysis complete! Report saved to: {report_file}")
        
        # Save raw JSON data
        json_file = report_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tweets_data, f, indent=2)
        print(f"✓ Raw data saved to: {json_file}")
    else:
        print("No tweets found or error occurred.")


if __name__ == "__main__":
    main()

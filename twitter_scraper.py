import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import re

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
    
    def search_user_tweets(self, username, keywords=None, max_results=100, filters=None):
        """
        Search tweets from a specific user, optionally filtered by keywords and advanced filters
        
        Args:
            username: Twitter handle (without @)
            keywords: List of keywords to filter by
            max_results: Maximum number of tweets to retrieve (10-100)
            filters: Dict with advanced filters (min_likes, verified_only, has_links, etc.)
        """
        # First, get the user ID and profile info
        user_data = self._get_user_info(username)
        if not user_data:
            return None
        
        user_id = user_data['id']
        
        # Build query
        query = f"from:{username}"
        if keywords:
            keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])
            query = f"({query}) ({keyword_query})"
        
        # Add advanced filters to query
        if filters:
            if filters.get('has_links'):
                query += " has:links"
            if filters.get('has_media'):
                query += " has:media"
            if filters.get('is_retweet') == False:
                query += " -is:retweet"
            if filters.get('min_replies'):
                query += f" min_replies:{filters['min_replies']}"
            if filters.get('min_likes'):
                query += f" min_faves:{filters['min_likes']}"
            if filters.get('min_retweets'):
                query += f" min_retweets:{filters['min_retweets']}"
        
        # Search tweets
        endpoint = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,text,entities,referenced_tweets",
            "expansions": "author_id,referenced_tweets.id",
            "user.fields": "username,name,verified,public_metrics,description,location"
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Add user profile info to response
            data['user_profile'] = user_data
            return data
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    
    def _get_user_info(self, username):
        """Get detailed user profile information"""
        endpoint = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type"
        }
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"Error getting user info: {response.status_code}")
            return None
    
    def discover_accounts(self, keywords, max_results=100, filters=None):
        """
        Discover Twitter accounts by searching tweets with keywords
        Returns unique accounts that have tweeted about the keywords
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of tweets to search through
            filters: Dict with filters (min_followers, verified_only, location, etc.)
        """
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found in .env file")
        
        # Build query from keywords
        keyword_query = " OR ".join([f'"{k}"' for k in keywords])
        
        # Add filters to query
        if filters:
            if filters.get('verified_only'):
                keyword_query += " is:verified"
            if filters.get('has_links'):
                keyword_query += " has:links"
            if filters.get('exclude_retweets'):
                keyword_query += " -is:retweet"
        
        # Search tweets
        endpoint = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": keyword_query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics,description,location,profile_image_url,created_at"
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        tweets_data = response.json()
        
        if not tweets_data or 'data' not in tweets_data:
            return None
        
        # Extract unique accounts with quality scoring
        accounts = {}
        for tweet in tweets_data['data']:
            author_id = tweet.get('author_id')
            if author_id and author_id not in accounts:
                # Get user info from includes
                user_info = None
                if 'includes' in tweets_data and 'users' in tweets_data['includes']:
                    for user in tweets_data['includes']['users']:
                        if user['id'] == author_id:
                            user_info = user
                            break
                
                if user_info:
                    followers = user_info.get('public_metrics', {}).get('followers_count', 0)
                    
                    # Apply follower filter
                    if filters and filters.get('min_followers'):
                        if followers < filters['min_followers']:
                            continue
                    
                    # Count tweets from this user in results
                    tweet_count = sum(1 for t in tweets_data['data'] if t.get('author_id') == author_id)
                    
                    # Calculate quality score
                    quality_score = self._calculate_account_quality_score(user_info, tweet_count)
                    
                    # Detect account type
                    account_type = self._detect_account_type(user_info)
                    
                    accounts[author_id] = {
                        'id': user_info['id'],
                        'username': user_info['username'],
                        'name': user_info['name'],
                        'description': user_info.get('description', ''),
                        'followers_count': followers,
                        'following_count': user_info.get('public_metrics', {}).get('following_count', 0),
                        'tweet_count': user_info.get('public_metrics', {}).get('tweet_count', 0),
                        'verified': user_info.get('verified', False),
                        'created_at': user_info.get('created_at', ''),
                        'profile_image_url': user_info.get('profile_image_url', ''),
                        'matching_tweets': tweet_count,
                        'location': user_info.get('location', ''),
                        'quality_score': quality_score,
                        'account_type': account_type
                    }
        
        # Sort by quality score (highest first)
        sorted_accounts = sorted(accounts.values(), key=lambda x: x['quality_score'], reverse=True)
        
        return {
            'accounts': sorted_accounts,
            'total_accounts': len(accounts),
            'search_keywords': keywords,
            'tweets_searched': len(tweets_data['data'])
        }
    
    def _calculate_account_quality_score(self, user_info, matching_tweets):
        """
        Calculate quality score for discovered accounts
        Score 0-100 based on multiple factors
        """
        score = 0
        
        metrics = user_info.get('public_metrics', {})
        followers = metrics.get('followers_count', 0)
        following = metrics.get('following_count', 0)
        total_tweets = metrics.get('tweet_count', 0)
        
        # Follower score (0-30 points)
        if followers >= 10000:
            score += 30
        elif followers >= 5000:
            score += 25
        elif followers >= 1000:
            score += 20
        elif followers >= 500:
            score += 15
        elif followers >= 100:
            score += 10
        elif followers >= 50:
            score += 5
        
        # Follower/Following ratio (0-15 points) - higher is better
        if following > 0:
            ratio = followers / following
            if ratio >= 2:
                score += 15
            elif ratio >= 1:
                score += 10
            elif ratio >= 0.5:
                score += 5
        
        # Verified account (20 points)
        if user_info.get('verified'):
            score += 20
        
        # Matching tweets relevance (0-20 points)
        score += min(matching_tweets * 5, 20)
        
        # Account activity (0-10 points)
        if total_tweets >= 1000:
            score += 10
        elif total_tweets >= 500:
            score += 7
        elif total_tweets >= 100:
            score += 5
        elif total_tweets >= 50:
            score += 3
        
        # Has description (5 points)
        if user_info.get('description'):
            score += 5
        
        return min(score, 100)
    
    def _detect_account_type(self, user_info):
        """
        Detect if account is Business, Personal, or Bot
        """
        description = user_info.get('description', '').lower()
        name = user_info.get('name', '').lower()
        metrics = user_info.get('public_metrics', {})
        
        # Bot indicators
        bot_keywords = ['bot', 'automated', 'auto tweet', 'rss feed']
        if any(keyword in description or keyword in name for keyword in bot_keywords):
            return 'Bot'
        
        # Business/Enterprise indicators
        business_keywords = [
            'ceo', 'founder', 'company', 'official', 'corp', 'inc', 'ltd',
            'enterprise', 'business', 'organization', 'industry', 'manufacturer',
            'solutions', 'services', 'consulting', 'technology', 'software'
        ]
        business_count = sum(1 for keyword in business_keywords if keyword in description or keyword in name)
        
        if business_count >= 2:
            return 'Business'
        elif business_count >= 1 and metrics.get('followers_count', 0) > 500:
            return 'Business'
        
        # Professional indicators
        professional_keywords = ['professional', 'expert', 'specialist', 'consultant', 'engineer', 'manager', 'director']
        if any(keyword in description for keyword in professional_keywords):
            return 'Professional'
        
        return 'Personal'
    
    def analyze_account_type(self, user_data):
        """Determine if account is enterprise/business/personal"""
        description = user_data.get('description', '').lower()
        name = user_data.get('name', '').lower()
        metrics = user_data.get('public_metrics', {})
        
        # Enterprise indicators
        enterprise_keywords = ['ceo', 'founder', 'company', 'official', 'corp', 'inc', 'ltd', 
                              'enterprise', 'business', 'organization', 'team']
        
        is_verified = user_data.get('verified', False)
        follower_count = metrics.get('followers_count', 0)
        following_count = metrics.get('following_count', 0)
        
        # Scoring system
        score = 0
        indicators = []
        
        if is_verified:
            score += 3
            indicators.append('Verified Account')
        
        if follower_count > 10000:
            score += 2
            indicators.append(f'High Followers ({follower_count:,})')
        
        if follower_count > 1000 and following_count < follower_count * 0.5:
            score += 1
            indicators.append('Good Follower Ratio')
        
        for keyword in enterprise_keywords:
            if keyword in description or keyword in name:
                score += 1
                indicators.append(f'Business Keyword: {keyword}')
                break
        
        # Determine type
        if score >= 4:
            account_type = 'Enterprise/Business'
        elif score >= 2:
            account_type = 'Professional/Influencer'
        else:
            account_type = 'Personal'
        
        return {
            'type': account_type,
            'score': score,
            'indicators': indicators,
            'is_verified': is_verified,
            'follower_count': follower_count
        }
    
    def calculate_engagement_score(self, tweet):
        """Calculate engagement score for lead prioritization"""
        metrics = tweet.get('public_metrics', {})
        
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)
        quotes = metrics.get('quote_count', 0)
        
        # Weighted engagement score
        score = (likes * 1) + (retweets * 3) + (replies * 2) + (quotes * 2)
        
        return {
            'score': score,
            'likes': likes,
            'retweets': retweets,
            'replies': replies,
            'quotes': quotes
        }
    
    def extract_entities(self, tweet):
        """Extract URLs, mentions, hashtags from tweet"""
        entities = tweet.get('entities', {})
        
        urls = []
        if 'urls' in entities:
            urls = [url['expanded_url'] for url in entities['urls'] if 'expanded_url' in url]
        
        mentions = []
        if 'mentions' in entities:
            mentions = [mention['username'] for mention in entities['mentions']]
        
        hashtags = []
        if 'hashtags' in entities:
            hashtags = [tag['tag'] for tag in entities['hashtags']]
        
        return {
            'urls': urls,
            'mentions': mentions,
            'hashtags': hashtags,
            'has_links': len(urls) > 0,
            'has_mentions': len(mentions) > 0,
            'has_hashtags': len(hashtags) > 0
        }
    
    def perform_sentiment_analysis(self, text):
        """Basic sentiment analysis"""
        # Positive indicators
        positive_words = ['great', 'excellent', 'amazing', 'love', 'best', 'awesome', 
                         'fantastic', 'wonderful', 'excited', 'happy', 'success', 'win']
        
        # Negative indicators
        negative_words = ['bad', 'terrible', 'worst', 'hate', 'awful', 'disappointed',
                         'fail', 'problem', 'issue', 'broken', 'poor', 'sad']
        
        # Business opportunity indicators
        opportunity_words = ['looking for', 'need', 'seeking', 'hiring', 'opportunity',
                           'help', 'recommend', 'suggestion', 'advice', 'question']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        opportunity_count = sum(1 for word in opportunity_words if word in text_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = 'Positive'
        elif negative_count > positive_count:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count,
            'opportunity_signals': opportunity_count,
            'is_opportunity': opportunity_count > 0
        }
    
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
    
    def generate_report(self, tweets_data, username, keywords=None, min_keyword_mentions=1):
        """Generate a formatted report from tweet data with advanced analytics"""
        if not tweets_data or 'data' not in tweets_data:
            return "No tweets found."
        
        tweets = tweets_data['data']
        user_profile = tweets_data.get('user_profile', {})
        
        # Analyze account type
        account_analysis = self.analyze_account_type(user_profile)
        
        # Create reports directory
        os.makedirs('reports', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/twitter_report_{username}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"TWITTER LEAD GENERATION REPORT\n")
            f.write(f"Username: @{username}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if keywords:
                f.write(f"Keywords: {', '.join(keywords)}\n")
            f.write(f"Total Tweets Found: {len(tweets)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Account Profile Analysis
            f.write("ACCOUNT PROFILE ANALYSIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Account Type: {account_analysis['type']}\n")
            f.write(f"Lead Quality Score: {account_analysis['score']}/7\n")
            f.write(f"Verified: {'Yes' if account_analysis['is_verified'] else 'No'}\n")
            f.write(f"Followers: {account_analysis['follower_count']:,}\n")
            f.write(f"Bio: {user_profile.get('description', 'N/A')}\n")
            f.write(f"Location: {user_profile.get('location', 'N/A')}\n")
            if user_profile.get('url'):
                f.write(f"Website: {user_profile.get('url')}\n")
            f.write(f"\nQuality Indicators:\n")
            for indicator in account_analysis['indicators']:
                f.write(f"  • {indicator}\n")
            f.write("\n")
            
            # Engagement Summary
            total_likes = sum(tweet.get('public_metrics', {}).get('like_count', 0) for tweet in tweets)
            total_retweets = sum(tweet.get('public_metrics', {}).get('retweet_count', 0) for tweet in tweets)
            total_replies = sum(tweet.get('public_metrics', {}).get('reply_count', 0) for tweet in tweets)
            
            # Calculate engagement scores
            engagement_scores = [self.calculate_engagement_score(tweet) for tweet in tweets]
            avg_engagement = sum(e['score'] for e in engagement_scores) / len(engagement_scores) if engagement_scores else 0
            
            f.write("ENGAGEMENT SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Likes: {total_likes:,}\n")
            f.write(f"Total Retweets: {total_retweets:,}\n")
            f.write(f"Total Replies: {total_replies:,}\n")
            f.write(f"Average Likes per Tweet: {total_likes/len(tweets):.2f}\n")
            f.write(f"Average Retweets per Tweet: {total_retweets/len(tweets):.2f}\n")
            f.write(f"Average Engagement Score: {avg_engagement:.2f}\n\n")
            
            # Content Analysis
            tweets_with_links = sum(1 for tweet in tweets if self.extract_entities(tweet)['has_links'])
            tweets_with_mentions = sum(1 for tweet in tweets if self.extract_entities(tweet)['has_mentions'])
            
            f.write("CONTENT ANALYSIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Tweets with Links: {tweets_with_links} ({tweets_with_links/len(tweets)*100:.1f}%)\n")
            f.write(f"Tweets with Mentions: {tweets_with_mentions} ({tweets_with_mentions/len(tweets)*100:.1f}%)\n")
            
            # Sentiment Analysis
            sentiments = [self.perform_sentiment_analysis(tweet['text']) for tweet in tweets]
            positive_count = sum(1 for s in sentiments if s['sentiment'] == 'Positive')
            negative_count = sum(1 for s in sentiments if s['sentiment'] == 'Negative')
            neutral_count = sum(1 for s in sentiments if s['sentiment'] == 'Neutral')
            opportunity_count = sum(1 for s in sentiments if s['is_opportunity'])
            
            f.write(f"\nSentiment Distribution:\n")
            f.write(f"  Positive: {positive_count} ({positive_count/len(tweets)*100:.1f}%)\n")
            f.write(f"  Neutral: {neutral_count} ({neutral_count/len(tweets)*100:.1f}%)\n")
            f.write(f"  Negative: {negative_count} ({negative_count/len(tweets)*100:.1f}%)\n")
            f.write(f"  Opportunity Signals: {opportunity_count} tweets\n\n")
            
            # Keyword analysis with ranking and threshold
            if keywords:
                f.write("KEYWORD ANALYSIS\n")
                f.write("-" * 80 + "\n")
                
                # Count mentions for each keyword
                keyword_counts = []
                for keyword in keywords:
                    count = sum(1 for tweet in tweets if keyword.lower() in tweet['text'].lower())
                    keyword_counts.append((keyword, count))
                
                # Sort by count (descending) - Ranking
                keyword_counts.sort(key=lambda x: x[1], reverse=True)
                
                # Filter by minimum threshold
                qualified_keywords = [(kw, count) for kw, count in keyword_counts if count >= min_keyword_mentions]
                
                if qualified_keywords:
                    f.write(f"Minimum mentions threshold: {min_keyword_mentions}\n")
                    f.write(f"Qualified keywords: {len(qualified_keywords)} of {len(keywords)}\n\n")
                    
                    for rank, (keyword, count) in enumerate(qualified_keywords, 1):
                        percentage = (count / len(tweets)) * 100
                        f.write(f"#{rank}. '{keyword}': {count} mentions ({percentage:.1f}% of tweets)\n")
                    
                    # Show disqualified keywords if any
                    disqualified = [(kw, count) for kw, count in keyword_counts if count < min_keyword_mentions]
                    if disqualified:
                        f.write(f"\nBelow threshold ({min_keyword_mentions} mentions):\n")
                        for keyword, count in disqualified:
                            f.write(f"  '{keyword}': {count} mentions\n")
                else:
                    f.write(f"⚠️ No keywords met the minimum threshold of {min_keyword_mentions} mentions.\n")
                    f.write(f"\nAll keyword counts:\n")
                    for keyword, count in keyword_counts:
                        f.write(f"  '{keyword}': {count} mentions\n")
                
                f.write("\n")
            
            # Top Performing Tweets (by engagement score)
            tweets_with_scores = [(tweet, self.calculate_engagement_score(tweet)) for tweet in tweets]
            top_tweets = sorted(tweets_with_scores, key=lambda x: x[1]['score'], reverse=True)[:5]
            
            f.write("TOP 5 PERFORMING TWEETS\n")
            f.write("-" * 80 + "\n")
            for i, (tweet, score) in enumerate(top_tweets, 1):
                f.write(f"\n#{i} - Engagement Score: {score['score']}\n")
                f.write(f"Date: {tweet.get('created_at', 'N/A')}\n")
                f.write(f"Text: {tweet['text'][:200]}{'...' if len(tweet['text']) > 200 else ''}\n")
                f.write(f"Likes: {score['likes']} | Retweets: {score['retweets']} | Replies: {score['replies']}\n")
                
                entities = self.extract_entities(tweet)
                if entities['urls']:
                    f.write(f"Links: {', '.join(entities['urls'][:2])}\n")
                f.write("-" * 80 + "\n")
            
            # Opportunity Tweets (tweets with buying signals)
            opportunity_tweets = [(tweet, self.perform_sentiment_analysis(tweet['text'])) 
                                 for tweet in tweets 
                                 if self.perform_sentiment_analysis(tweet['text'])['is_opportunity']]
            
            if opportunity_tweets:
                f.write("\nLEAD OPPORTUNITY TWEETS\n")
                f.write("-" * 80 + "\n")
                for tweet, sentiment in opportunity_tweets[:5]:
                    f.write(f"\nDate: {tweet.get('created_at', 'N/A')}\n")
                    f.write(f"Text: {tweet['text']}\n")
                    f.write(f"Opportunity Signals: {sentiment['opportunity_signals']}\n")
                    metrics = tweet.get('public_metrics', {})
                    f.write(f"Engagement: {metrics.get('like_count', 0)} likes, {metrics.get('reply_count', 0)} replies\n")
                    f.write("-" * 80 + "\n")
            
            # Detailed tweets section
            f.write("\n\nDETAILED TWEET ANALYSIS\n")
            f.write("-" * 80 + "\n\n")
            
            for i, tweet in enumerate(tweets, 1):
                sentiment = self.perform_sentiment_analysis(tweet['text'])
                entities = self.extract_entities(tweet)
                engagement = self.calculate_engagement_score(tweet)
                
                f.write(f"Tweet #{i}\n")
                f.write(f"Date: {tweet.get('created_at', 'N/A')}\n")
                f.write(f"Text: {tweet['text']}\n")
                f.write(f"Sentiment: {sentiment['sentiment']}")
                if sentiment['is_opportunity']:
                    f.write(" 🎯 OPPORTUNITY")
                f.write("\n")
                f.write(f"Engagement Score: {engagement['score']}\n")
                metrics = tweet.get('public_metrics', {})
                f.write(f"Likes: {metrics.get('like_count', 0)} | ")
                f.write(f"Retweets: {metrics.get('retweet_count', 0)} | ")
                f.write(f"Replies: {metrics.get('reply_count', 0)}\n")
                
                if entities['urls']:
                    f.write(f"Links: {', '.join(entities['urls'])}\n")
                if entities['mentions']:
                    f.write(f"Mentions: @{', @'.join(entities['mentions'])}\n")
                if entities['hashtags']:
                    f.write(f"Hashtags: #{', #'.join(entities['hashtags'])}\n")
                
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

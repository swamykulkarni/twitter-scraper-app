import os
import praw
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

class RedditScraper:
    def __init__(self):
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'SocialListeningPlatform/1.0')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials not found in .env file")
        
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
    
    def search_subreddit(self, subreddit_name, keywords=None, max_results=100, time_filter='week'):
        """
        Search posts in a subreddit
        
        Args:
            subreddit_name: Name of subreddit (without r/)
            keywords: List of keywords to search for
            max_results: Maximum number of posts to retrieve
            time_filter: Time filter (hour, day, week, month, year, all)
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []
            
            if keywords:
                # Search with keywords
                search_query = ' OR '.join(keywords)
                posts = subreddit.search(search_query, time_filter=time_filter, limit=max_results)
            else:
                # Get hot posts
                posts = subreddit.hot(limit=max_results)
            
            for post in posts:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'text': post.selftext,
                    'author': str(post.author) if post.author else '[deleted]',
                    'subreddit': str(post.subreddit),
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                    'url': post.url,
                    'permalink': f"https://reddit.com{post.permalink}",
                    'is_self': post.is_self,
                    'link_flair_text': post.link_flair_text,
                }
                posts_data.append(post_data)
            
            # Get subreddit info
            subreddit_info = {
                'name': subreddit.display_name,
                'subscribers': subreddit.subscribers,
                'description': subreddit.public_description,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc).isoformat()
            }
            
            return {
                'data': posts_data,
                'subreddit_info': subreddit_info,
                'search_params': {
                    'subreddit': subreddit_name,
                    'keywords': keywords,
                    'time_filter': time_filter,
                    'max_results': max_results
                }
            }
        
        except Exception as e:
            print(f"Error searching Reddit: {e}")
            return None
    
    def analyze_post_engagement(self, post):
        """Calculate engagement score for a Reddit post"""
        score = post.get('score', 0)
        num_comments = post.get('num_comments', 0)
        upvote_ratio = post.get('upvote_ratio', 0)
        
        # Weighted engagement score
        engagement_score = (score * 1) + (num_comments * 3) + (upvote_ratio * 100)
        return round(engagement_score, 2)
    
    def perform_sentiment_analysis(self, text):
        """Simple sentiment analysis based on keywords"""
        if not text:
            return {'sentiment': 'Neutral', 'signals': []}
        
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['great', 'excellent', 'amazing', 'love', 'best', 'awesome', 'fantastic', 'perfect']
        # Negative indicators
        negative_words = ['bad', 'terrible', 'worst', 'hate', 'awful', 'poor', 'disappointing', 'issue', 'problem']
        # Opportunity signals
        opportunity_words = ['looking for', 'need', 'want', 'seeking', 'recommend', 'suggestion', 'help', 'advice']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        signals = [word for word in opportunity_words if word in text_lower]
        
        if positive_count > negative_count:
            sentiment = 'Positive'
        elif negative_count > positive_count:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'
        
        return {
            'sentiment': sentiment,
            'signals': signals
        }
    
    def generate_report(self, posts_data, subreddit_name, keywords=None, min_keyword_mentions=1):
        """Generate analysis report from Reddit posts"""
        if not posts_data or 'data' not in posts_data:
            return None
        
        posts = posts_data['data']
        subreddit_info = posts_data.get('subreddit_info', {})
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/reddit_report_{subreddit_name}_{timestamp}.txt"
        
        os.makedirs('reports', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REDDIT ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Subreddit: r/{subreddit_name}\n")
            f.write(f"Subscribers: {subreddit_info.get('subscribers', 'N/A'):,}\n")
            if subreddit_info.get('description'):
                f.write(f"Description: {subreddit_info['description']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"Total Posts Analyzed: {len(posts)}\n")
            if keywords:
                f.write(f"Keywords: {', '.join(keywords)}\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            # Keyword Analysis
            if keywords:
                f.write("KEYWORD ANALYSIS\n")
                f.write("-" * 80 + "\n")
                keyword_counts = {}
                for keyword in keywords:
                    count = sum(1 for post in posts 
                              if keyword.lower() in post.get('title', '').lower() 
                              or keyword.lower() in post.get('text', '').lower())
                    keyword_counts[keyword] = count
                
                # Sort by frequency
                sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
                
                qualified_keywords = [(k, c) for k, c in sorted_keywords if c >= min_keyword_mentions]
                disqualified_keywords = [(k, c) for k, c in sorted_keywords if c < min_keyword_mentions]
                
                f.write(f"\nQualified Keywords (≥{min_keyword_mentions} mentions):\n")
                for keyword, count in qualified_keywords:
                    percentage = (count / len(posts)) * 100
                    f.write(f"  • {keyword}: {count} mentions ({percentage:.1f}% of posts)\n")
                
                if disqualified_keywords:
                    f.write(f"\nDisqualified Keywords (<{min_keyword_mentions} mentions):\n")
                    for keyword, count in disqualified_keywords:
                        f.write(f"  • {keyword}: {count} mentions\n")
                
                f.write("\n")
            
            # Engagement Analysis
            f.write("ENGAGEMENT ANALYSIS\n")
            f.write("-" * 80 + "\n")
            
            # Calculate engagement scores
            for post in posts:
                post['engagement_score'] = self.analyze_post_engagement(post)
            
            # Top posts by engagement
            top_posts = sorted(posts, key=lambda x: x['engagement_score'], reverse=True)[:5]
            
            f.write("\nTop 5 Posts by Engagement:\n")
            for i, post in enumerate(top_posts, 1):
                f.write(f"\n{i}. {post['title']}\n")
                f.write(f"   Score: {post['score']} | Comments: {post['num_comments']} | ")
                f.write(f"Upvote Ratio: {post['upvote_ratio']:.0%}\n")
                f.write(f"   Engagement Score: {post['engagement_score']}\n")
                f.write(f"   Link: {post['permalink']}\n")
            
            # Sentiment Analysis
            f.write("\n" + "=" * 80 + "\n")
            f.write("SENTIMENT ANALYSIS\n")
            f.write("-" * 80 + "\n")
            
            sentiments = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
            opportunity_posts = []
            
            for post in posts:
                combined_text = f"{post.get('title', '')} {post.get('text', '')}"
                analysis = self.perform_sentiment_analysis(combined_text)
                post['sentiment'] = analysis['sentiment']
                post['signals'] = analysis['signals']
                
                sentiments[analysis['sentiment']] += 1
                
                if analysis['signals']:
                    opportunity_posts.append(post)
            
            f.write(f"\nSentiment Distribution:\n")
            for sentiment, count in sentiments.items():
                percentage = (count / len(posts)) * 100
                f.write(f"  • {sentiment}: {count} posts ({percentage:.1f}%)\n")
            
            # Opportunity signals
            if opportunity_posts:
                f.write(f"\n\nLead Opportunity Posts ({len(opportunity_posts)} found):\n")
                f.write("-" * 80 + "\n")
                for post in opportunity_posts[:10]:  # Top 10
                    f.write(f"\n• {post['title']}\n")
                    f.write(f"  Signals: {', '.join(post['signals'])}\n")
                    f.write(f"  Score: {post['score']} | Comments: {post['num_comments']}\n")
                    f.write(f"  Link: {post['permalink']}\n")
            
            # All Posts
            f.write("\n" + "=" * 80 + "\n")
            f.write("ALL POSTS\n")
            f.write("-" * 80 + "\n\n")
            
            for i, post in enumerate(posts, 1):
                f.write(f"{i}. {post['title']}\n")
                f.write(f"   Author: u/{post['author']} | Score: {post['score']} | ")
                f.write(f"Comments: {post['num_comments']}\n")
                if post.get('text'):
                    preview = post['text'][:200] + "..." if len(post['text']) > 200 else post['text']
                    f.write(f"   {preview}\n")
                f.write(f"   Link: {post['permalink']}\n")
                f.write(f"   Sentiment: {post.get('sentiment', 'N/A')}\n")
                f.write("\n")
        
        print(f"Report generated: {report_file}")
        return report_file

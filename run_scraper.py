import sys
from twitter_scraper import TwitterScraper

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_scraper.py <username> [keyword1,keyword2,...]")
        sys.exit(1)
    
    username = sys.argv[1]
    keywords = None
    
    if len(sys.argv) > 2:
        keywords = [k.strip() for k in sys.argv[2].split(",")]
    
    scraper = TwitterScraper()
    
    print(f"\nSearching tweets from @{username}...")
    if keywords:
        print(f"Filtering by keywords: {', '.join(keywords)}")
    
    tweets_data = scraper.search_user_tweets(username, keywords=keywords, max_results=100)
    
    if tweets_data:
        report_file = scraper.generate_report(tweets_data, username, keywords)
        print(f"\n✓ Analysis complete! Report saved to: {report_file}")
        
        json_file = report_file.replace('.txt', '.json')
        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tweets_data, f, indent=2)
        print(f"✓ Raw data saved to: {json_file}")
    else:
        print("No tweets found or error occurred.")

if __name__ == "__main__":
    main()

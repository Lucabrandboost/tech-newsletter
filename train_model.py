from newsletter_generator import NewsletterGenerator
from article_tracker import ArticleTracker
import json
from datetime import datetime, timedelta
import sqlite3
import requests
import random
from collections import Counter

class ModelTrainer:
    def __init__(self):
        self.newsletter = NewsletterGenerator()
        self.tracker = ArticleTracker()
        
        # Define source weights (higher = more preferred)
        self.source_weights = {
            # VC & Investment Sources (highest priority)
            'pitchbook.com': 2.0,
            'avcj.com': 2.0,                    # Asian Venture Capital Journal
            'dealroom.co': 1.9,
            'sifted.eu': 1.9,                   # European startups/VC
            'techinasia.com': 1.9,              # Asian tech/startup news
            'afr.com/technology': 1.9,          # Australian Financial Review Tech
            'techbusinessnews.com.au': 1.8,
            'startupdaily.net': 1.8,
            
            # Premium News Sources
            'ft.com': 1.8,
            'sciencenews.org': 1.8,
            
            # Specialized VC Blogs
            'avc.com': 1.7,                     # Fred Wilson's blog
            'bothsidesofthetable.com': 1.7,     # Mark Suster's blog
            'tomtunguz.com': 1.7,               # Tomasz Tunguz
            'feld.com': 1.7,                    # Brad Feld's blog
            'sequoiacap.com/blog': 1.7,         # Sequoia Capital blog
            'a16z.com': 1.7,                    # Andreessen Horowitz
            
            # Tech-specific news
            'theinformation.com': 1.6,
            'infoq.com': 1.5,
            'thehackernews.com': 1.5,
            'arstechnica.com': 1.4,
            
            # Tech business news
            'techcrunch.com/category/venture': 1.5,
            'venturebeat.com/category/venture': 1.4,
            'techcrunch.com': 0.9,
            'venturebeat.com': 0.9,
            
            # General business news (lowest priority)
            'reuters.com': 0.7,
            'bloomberg.com': 0.7
        }

    def fetch_training_articles(self):
        """Fetch a diverse set of articles for training with source weighting and recency"""
        all_articles = []
        
        # Calculate date range (last 3 days)
        now = datetime.now()
        three_days_ago = (now - timedelta(days=3)).isoformat()
        
        tech_queries = [
            {
                'q': ('venture capital OR series A OR series B OR '
                     'startup funding OR term sheet OR venture round'),
                'domains': 'pitchbook.com,avcj.com,dealroom.co,ft.com',
                'pageSize': 5
            },
            {
                'q': ('australian startup OR asia pacific venture OR '
                     'australian tech investment OR asia funding'),
                'domains': 'techbusinessnews.com.au,avcj.com,techinasia.com,afr.com',
                'pageSize': 4
            },
            {
                'q': ('european startup OR european venture capital OR '
                     'european tech investment'),
                'domains': 'sifted.eu,dealroom.co,ft.com',
                'pageSize': 3
            },
            {
                'q': ('venture partner insights OR vc strategy OR '
                     'startup valuation OR venture thesis'),
                'domains': 'avc.com,bothsidesofthetable.com,tomtunguz.com,a16z.com',
                'pageSize': 4
            },
            {
                'q': ('deep tech OR frontier technology OR '
                     'emerging technology investment'),
                'domains': 'sciencenews.org,theinformation.com,ft.com',
                'pageSize': 3
            },
            {
                'q': ('startup exit OR IPO OR M&A OR '
                     'acquisition OR venture exit'),
                'domains': 'pitchbook.com,dealroom.co,techcrunch.com',
                'pageSize': 3
            },
            {
                'q': ('venture capital analysis OR startup metrics OR '
                     'investment trends OR funding analysis'),
                'domains': 'tomtunguz.com,sequoiacap.com,a16z.com',
                'pageSize': 3
            }
        ]
        
        for query in tech_queries:
            params = {
                'apiKey': self.newsletter.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'from': three_days_ago,
                **query
            }
            
            try:
                response = requests.get(self.newsletter.news_api_url, params=params)
                articles = response.json().get('articles', [])
                
                for article in articles:
                    # Calculate article age score (newer = higher score)
                    pub_date = datetime.fromisoformat(article.get('publishedAt', now.isoformat())[:-1])
                    age_hours = (now - pub_date).total_seconds() / 3600
                    age_score = max(0, 1 - (age_hours / (72 * 1.5)))  # Decay over 72 hours
                    
                    # Get source weight
                    domain = self.extract_domain(article.get('url', ''))
                    source_weight = self.source_weights.get(domain, 1.0)
                    
                    # Calculate combined score
                    relevance_score = age_score * source_weight
                    
                    all_articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': {'name': article.get('source', {}).get('name', '')},
                        'url': article.get('url', ''),
                        'category': 'tech',
                        'publishedAt': article.get('publishedAt'),
                        'relevance_score': relevance_score,
                        'age_hours': age_hours,
                        'source_weight': source_weight
                    })
            except Exception as e:
                print(f"Error fetching articles for query '{query['q']}': {e}")
                continue
        
        # Sort by relevance score and take top results
        all_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        all_articles = all_articles[:15]  # Keep top 15 most relevant articles
        
        # Print summary of training set
        print("\n=== Training Set Summary ===")
        print(f"Total articles: {len(all_articles)}")
        print("\nSources:")
        categories = Counter(article.get('source', {}).get('name', '') for article in all_articles)
        for source, count in categories.most_common():
            print(f"- {source}: {count} articles")
        
        print("\nAge Distribution:")
        age_ranges = Counter(
            "0-24h" if a['age_hours'] <= 24 else
            "24-48h" if a['age_hours'] <= 48 else
            "48-72h"
            for a in all_articles
        )
        for age_range, count in age_ranges.most_common():
            print(f"- {age_range}: {count} articles")
        print()
        
        return all_articles

    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            return url.split('/')[2].replace('www.', '')
        except:
            return ''

    def train_model(self):
        articles = self.fetch_training_articles()
        
        print("\n=== Article Training Session ===")
        print("For each article, enter 'y' if you'd read it, 'n' if you wouldn't.")
        print("Enter 'q' to quit the training session.\n")

        for i, article in enumerate(articles, 1):
            print(f"\nArticle {i}/{len(articles)}")
            print(f"Title: {article['title']}")
            print(f"Source: {article['source']['name']}")
            print(f"Age: {article['age_hours']:.1f} hours old")
            print(f"Description: {article['description']}\n")

            while True:
                response = input("Would you read this? (y/n/q): ").lower()
                if response in ['y', 'n', 'q']:
                    break
                print("Please enter 'y', 'n', or 'q'")

            if response == 'q':
                break
            
            if response == 'y':
                self.tracker.track_article(article)
                self.tracker.record_click(article['url'])
                print(f"✓ Added to interests (Score: {article['relevance_score']:.2f})")
            else:
                print("✗ Skipped")

        print("\nTraining session completed!")
        self.show_learned_preferences()

    def show_learned_preferences(self):
        """Display what the model has learned"""
        conn = sqlite3.connect(self.tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT keyword, weight 
            FROM keyword_weights 
            ORDER BY weight DESC 
            LIMIT 10
        ''')
        
        top_keywords = cursor.fetchall()
        
        print("\n=== Your Top Interest Keywords ===")
        for keyword, weight in top_keywords:
            print(f"{keyword}: {weight:.2f}")
        
        conn.close()

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_model() 
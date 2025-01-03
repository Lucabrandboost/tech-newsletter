import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import random
from typing import List, Dict
from article_tracker import ArticleTracker
import urllib.parse

# Load environment variables
load_dotenv()

class NewsletterGenerator:
    def __init__(self):
        self.news_api_key = 'ee69246904ab49f8b08638763bce878f'
        self.news_api_url = 'https://newsapi.org/v2/everything'
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_receiver = os.getenv('EMAIL_RECEIVER')
        
        # Updated Substack URLs with tech and science focus
        self.substack_urls = [
            'https://www.platformer.news',          # Tech news
            'https://garymarcus.substack.com',      # AI commentary
            'https://artificialintelligence.substack.com', # AI news
            'https://www.importai.net',             # AI newsletter
            'https://thealgorithm.substack.com',    # MIT Tech Review
            'https://www.oneusefulthing.org',       # AI and tech
            'https://mooreinsights.substack.com',   # Tech analysis
            'https://www.hottakes.space/',          # Your existing subscription
            'https://www.readsuperfluid.com/',      # Your existing subscription
        ]
        
        # Add regional tech news domains
        self.tech_domains = (
            'techcrunch.com,wired.com,theverge.com,arstechnica.com,'
            'australianfintech.com.au,startupdaily.net,innovationaus.com,'  # Australian tech
            'sfgate.com/tech,sfstandard.com,missionlocal.org,'  # SF tech
            'venturebeat.com,protocol.com,siliconangle.com'  # Additional tech
        )
        
        # Add domains for interesting stories
        self.interesting_domains = (
            'hackernoon.com,thenextweb.com,inverse.com,'
            'interestingengineering.com,futurism.com'
        )

        self.tracker = ArticleTracker()
        self.tracking_base_url = "http://localhost:5000/track"  # We'll create this endpoint

    def fetch_top_news(self):
        """Fetch news articles based on specific topics and categories"""
        # Define topics and keywords
        tech_topics = (
            'artificial intelligence OR machine learning OR '
            'technology OR tech companies OR '
            'OpenAI OR Microsoft OR Google OR '
            'quantum computing OR robotics OR '
            'Silicon Valley OR startup OR venture capital'
        )
        
        australian_tech = (
            'Australian technology OR '
            'Australian startup OR '
            'Australian tech industry OR '
            'Australian innovation'
        )
        
        sf_tech = (
            'San Francisco technology OR '
            'Silicon Valley news OR '
            'Bay Area startup OR '
            'SF tech industry'
        )
        
        all_articles = []
        
        # Tech news params with regional variations
        params_list = [
            {
                'apiKey': self.news_api_key,
                'q': tech_topics,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 3,
                'domains': self.tech_domains
            },
            {
                'apiKey': self.news_api_key,
                'q': australian_tech,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 2,
            },
            {
                'apiKey': self.news_api_key,
                'q': sf_tech,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 2,
            }
        ]
        
        try:
            # Fetch all categories of tech news
            for params in params_list:
                response = requests.get(self.news_api_url, params=params)
                articles = response.json().get('articles', [])
                all_articles.extend(articles)
            
            # Fetch random interesting story
            interesting_params = {
                'apiKey': self.news_api_key,
                'domains': self.interesting_domains,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10  # Fetch 10 and randomly select one
            }
            
            interesting_response = requests.get(self.news_api_url, params=interesting_params)
            interesting_articles = interesting_response.json().get('articles', [])
            if interesting_articles:
                self.random_story = random.choice(interesting_articles)
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

        # Score and sort articles
        scored_articles = []
        for article in all_articles:
            score = self.tracker.get_article_score(article)
            scored_articles.append((score, article))
        
        # Sort by score and take top articles
        scored_articles.sort(reverse=True)
        return [article for score, article in scored_articles[:7]]  # Return top 7 articles

    def fetch_substack_articles(self, url: str) -> List[Dict[str, str]]:
        """Fetch articles from a Substack publication."""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            # Find all article posts on the homepage
            posts = soup.find_all('article', class_='post-preview')
            
            for post in posts:
                title_elem = post.find('h3', class_='post-preview-title')
                if not title_elem:
                    continue
                    
                link_elem = post.find('a', href=True)
                description_elem = post.find('div', class_='post-preview-description')
                
                articles.append({
                    'title': title_elem.text.strip(),
                    'url': link_elem['href'] if link_elem else None,
                    'description': description_elem.text.strip() if description_elem else ''
                })
            
            return articles
        except Exception as e:
            print(f"Error fetching Substack articles from {url}: {e}")
            return []

    def get_random_interesting_read(self) -> Dict[str, str]:
        """Get a random article from configured Substack publications."""
        all_articles = []
        for url in self.substack_urls:
            articles = self.fetch_substack_articles(url)
            all_articles.extend(articles)
        
        return random.choice(all_articles) if all_articles else None

    def generate_newsletter_html(self):
        # Modify the article URL to include tracking
        def add_tracking(article):
            encoded_url = urllib.parse.quote(article['url'])
            article['tracking_url'] = f"{self.tracking_base_url}?url={encoded_url}"
            return article
        
        news_articles = [add_tracking(article) for article in self.fetch_top_news()]
        interesting_read = self.get_random_interesting_read()
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .article {{ margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #ccc; }}
                    .date {{ color: #666; font-size: 0.9em; }}
                    .source {{ color: #0066cc; font-size: 0.9em; }}
                    .interesting-read {{ 
                        background-color: #f5f5f5; 
                        padding: 15px; 
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .tech-news {{ background-color: #e6f3ff; }}
                    .science-news {{ background-color: #e6ffe6; }}
                    .random-story {{ 
                        background-color: #fff0f5; 
                        border-radius: 5px;
                        padding: 15px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <h1>Your Tech & Science Newsletter - {datetime.now().strftime('%B %d, %Y')}</h1>
        """

        # Add interesting read section if available
        if interesting_read:
            html_content += f"""
                <div class="interesting-read">
                    <h2>Today's Interesting Read from Substack</h2>
                    <h3><a href="{interesting_read['url']}">{interesting_read['title']}</a></h3>
                    <p>{interesting_read['description']}</p>
                </div>
            """

        html_content += "<h2>Latest in Tech & Science</h2>"

        for article in news_articles:
            # Determine if it's tech or science based on source
            category_class = "tech-news" if any(domain in article.get('url', '') 
                for domain in ['techcrunch.com', 'wired.com', 'theverge.com', 'arstechnica.com']) else "science-news"
            
            html_content += f"""
                <div class="article {category_class}">
                    <h3><a href="{article['url']}">{article['title']}</a></h3>
                    <p class="source">Source: {article.get('source', {}).get('name', 'Unknown')}</p>
                    <p class="date">{article['publishedAt'][:10]}</p>
                    <p>{article['description']}</p>
                </div>
            """

        # Add random interesting story at the bottom
        if hasattr(self, 'random_story'):
            html_content += f"""
                <div class="random-story">
                    <h2>Today's Random Interesting Story</h2>
                    <h3><a href="{self.random_story['url']}">{self.random_story['title']}</a></h3>
                    <p class="source">Source: {self.random_story.get('source', {}).get('name', 'Unknown')}</p>
                    <p class="date">{self.random_story['publishedAt'][:10]}</p>
                    <p>{self.random_story['description']}</p>
                </div>
            """

        html_content += """
            </body>
        </html>
        """

        # Track all articles being sent
        for article in news_articles:
            self.tracker.track_article(article)

        return html_content

    def send_newsletter(self):
        html_content = self.generate_newsletter_html()
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Daily Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = self.email_sender
        msg['To'] = self.email_receiver

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            print("Newsletter sent successfully!")
        except Exception as e:
            print(f"Error sending newsletter: {e}") 
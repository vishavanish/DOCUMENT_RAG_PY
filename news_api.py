import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NewsAPIClient:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2'
    
    def fetch_latest_articles(self, country='us', page_size=20):
        url = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.api_key,
            'country': country,
            'pageSize': page_size
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                if article['url'] and article['title']:
                    articles.append({
                        'title': article['title'][:500],
                        'description': article.get('description', '')[:1000] if article.get('description') else '',
                        'url': article['url'],
                        'image_url': article.get('urlToImage', ''),
                        'published_at': self._parse_date(article.get('publishedAt')),
                        'source_name': article['source']['name'][:200] if article.get('source') else 'Unknown'
                    })
            
            return articles
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return []
    
    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None
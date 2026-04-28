from celery_config import celery_app
from news_api import NewsAPIClient
from database import DatabaseManager

@celery_app.task
def fetch_and_store_news():
    """Celery task to fetch news and store in database"""
    try:
        # Initialize clients
        news_client = NewsAPIClient()
        db_manager = DatabaseManager()
        
        # Fetch articles
        articles = news_client.fetch_latest_articles()
        
        # Store articles
        stored_count = 0
        for article in articles:
            if db_manager.insert_article(article):
                stored_count += 1
        
        print(f"Processed {len(articles)} articles, stored {stored_count} new articles")
        return f"Success: {stored_count}/{len(articles)} articles stored"
        
    except Exception as e:
        print(f"Task error: {e}")
        return f"Error: {str(e)}"
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery('news_collector')

celery_app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'fetch-news-every-minute': {
            'task': 'tasks.fetch_and_store_news',
            'schedule': 60.0,  # Every 60 seconds
        },
    },
)
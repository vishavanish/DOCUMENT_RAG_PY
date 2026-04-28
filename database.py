import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('MYSQL_HOST'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE')
        }
    
    def get_connection(self):
        return mysql.connector.connect(**self.config)
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                url VARCHAR(500) NOT NULL UNIQUE,
                image_url VARCHAR(500),
                published_at DATETIME,
                source_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_published_at (published_at),
                INDEX idx_source (source_name)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def insert_article(self, article_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT IGNORE INTO articles (title, description, url, image_url, published_at, source_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                article_data['title'],
                article_data['description'],
                article_data['url'],
                article_data['image_url'],
                article_data['published_at'],
                article_data['source_name']
            ))
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
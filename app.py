from flask import Flask, jsonify, request, render_template_string
from database import DatabaseManager
from tasks import fetch_and_store_news
from document_manager import DocumentManager
from authenticity_decision import AuthenticityDecision
import mysql.connector

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize document manager and authenticity system
doc_manager = DocumentManager()
auth_system = AuthenticityDecision()

@app.route('/')
def home():
    return jsonify({"message": "News Collection API is running"})

@app.route('/fetch-news')
def manual_fetch():
    """Manually trigger news fetching"""
    try:
        result = fetch_and_store_news.delay()
        return jsonify({"message": "News fetch task started", "task_id": str(result.id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/articles')
def get_articles():
    """Get latest articles from database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT title, description, url, published_at, source_name, created_at 
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"articles": articles, "count": len(articles)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/init-db')
def init_database():
    """Initialize database tables"""
    try:
        db = DatabaseManager()
        db.create_tables()
        doc_manager._create_documents_table()
        return jsonify({"message": "Database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# RAG System Endpoints
@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload and index a PDF document"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        doc_id = doc_manager.upload_document(file)
        return jsonify({"message": "Document uploaded and indexed", "document_id": doc_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documents')
def list_documents():
    """List all uploaded documents"""
    try:
        documents = doc_manager.list_documents()
        return jsonify({"documents": documents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query_document():
    """Query a document using RAG"""
    try:
        data = request.get_json()
        if not data or 'document_id' not in data or 'question' not in data:
            return jsonify({"error": "document_id and question are required"}), 400
        
        doc_id = data['document_id']
        question = data['question']
        k = data.get('k', 3)
        
        result = doc_manager.query_document(doc_id, question, k)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document"""
    try:
        doc_manager.delete_document(doc_id)
        return jsonify({"message": "Document deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/demo')
def demo_interface():
    """Serve the RAG demo interface"""
    with open('rag_demo.html', 'r') as f:
        return f.read()

# MODULE 3: Authenticity Decision Endpoints
@app.route('/check-authenticity', methods=['POST'])
def check_authenticity():
    """Check news authenticity using Module 3"""
    try:
        data = request.get_json()
        if not data or 'news_text' not in data:
            return jsonify({"error": "news_text is required"}), 400
        
        news_text = data['news_text']
        news_title = data.get('news_title', '')
        
        result = auth_system.analyze_authenticity(news_text, news_title)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trust-scores')
def get_trust_scores():
    """Get configured trust scores for sources"""
    return jsonify({
        "trust_scores": auth_system.trust_scores,
        "unknown_source_score": auth_system.unknown_source_score
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
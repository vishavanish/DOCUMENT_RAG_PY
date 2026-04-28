import os
import uuid
from werkzeug.utils import secure_filename
from simple_rag import SimpleRAG as RAGSystem
import mysql.connector
from database import DatabaseManager

class DocumentManager:
    def __init__(self, upload_folder="uploads"):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'pdf'}
        self.rag_systems = {}  # Store RAG instances per document
        
        # Create upload directory
        os.makedirs(upload_folder, exist_ok=True)
        
        # Initialize database
        self.db = DatabaseManager()
        self._create_documents_table()
    
    def _create_documents_table(self):
        """Create table for document metadata"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                chunks_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('processing', 'indexed', 'error') DEFAULT 'processing'
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def upload_document(self, file) -> str:
        """Upload and index a PDF document"""
        if not self.allowed_file(file.filename):
            raise ValueError("Only PDF files are allowed")
        
        # Generate unique ID and secure filename
        doc_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, f"{doc_id}_{filename}")
        
        # Save file
        file.save(file_path)
        
        # Store in database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (id, filename, original_name, file_path, status)
            VALUES (%s, %s, %s, %s, 'processing')
        """, (doc_id, f"{doc_id}_{filename}", filename[:200], file_path))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Index document
        try:
            rag_system = RAGSystem()
            chunks_count = rag_system.index_document(file_path)
            
            # Save index
            index_path = os.path.join(self.upload_folder, f"{doc_id}_index")
            rag_system.save_index(index_path)
            
            # Store RAG system
            self.rag_systems[doc_id] = rag_system
            
            # Update database
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET chunks_count = %s, status = 'indexed'
                WHERE id = %s
            """, (chunks_count, doc_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            return doc_id
            
        except Exception as e:
            # Update status to error
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET status = 'error'
                WHERE id = %s
            """, (doc_id,))
            conn.commit()
            cursor.close()
            conn.close()
            raise e
    
    def get_rag_system(self, doc_id: str) -> RAGSystem:
        """Get or load RAG system for document"""
        if doc_id not in self.rag_systems:
            # Load from saved index
            index_path = os.path.join(self.upload_folder, f"{doc_id}_index")
            if os.path.exists(index_path + ".pkl"):
                rag_system = RAGSystem()
                rag_system.load_index(index_path)
                self.rag_systems[doc_id] = rag_system
            else:
                raise ValueError(f"Document {doc_id} not found or not indexed")
        
        return self.rag_systems[doc_id]
    
    def query_document(self, doc_id: str, question: str, k: int = 3):
        """Query a specific document"""
        rag_system = self.get_rag_system(doc_id)
        return rag_system.query(question, k)
    
    def list_documents(self):
        """List all uploaded documents"""
        conn = self.db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, original_name, chunks_count, created_at, status
            FROM documents
            ORDER BY created_at DESC
        """)
        
        documents = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return documents
    
    def delete_document(self, doc_id: str):
        """Delete document and its index"""
        # Remove from memory
        if doc_id in self.rag_systems:
            del self.rag_systems[doc_id]
        
        # Get file path
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM documents WHERE id = %s", (doc_id,))
        result = cursor.fetchone()
        
        if result:
            file_path = result[0]
            
            # Delete files
            if os.path.exists(file_path):
                os.remove(file_path)
            
            index_path = os.path.join(self.upload_folder, f"{doc_id}_index")
            for ext in [".pkl", ".faiss"]:
                if os.path.exists(index_path + ext):
                    os.remove(index_path + ext)
            
            # Delete from database
            cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            conn.commit()
        
        cursor.close()
        conn.close()
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from typing import List, Dict, Any
import PyPDF2
from io import BytesIO
from llm_client import LLMClient

class RAGSystem:
    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.llm_client = LLMClient()
        self.vector_db = None
        self.chunks = []
        self.chunk_metadata = []
        
    def load_pdf(self, pdf_path: str) -> str:
        """Load and extract text from PDF"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text chunks"""
        return self.embedding_model.encode(texts)
    
    def build_vector_db(self, embeddings: np.ndarray):
        """Build FAISS vector database"""
        dimension = embeddings.shape[1]
        self.vector_db = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.vector_db.add(embeddings.astype('float32'))
    
    def index_document(self, pdf_path: str, doc_name: str = None):
        """Complete indexing pipeline"""
        # Load document
        text = self.load_pdf(pdf_path)
        
        # Split into chunks
        self.chunks = self.split_text(text)
        
        # Store metadata
        self.chunk_metadata = [{"doc_name": doc_name or pdf_path, "chunk_id": i} 
                              for i in range(len(self.chunks))]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(self.chunks)
        
        # Build vector database
        self.build_vector_db(embeddings)
        
        return len(self.chunks)
    
    def semantic_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve most similar chunks"""
        if not self.vector_db:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.vector_db.search(query_embedding.astype('float32'), k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                results.append({
                    "text": self.chunks[idx],
                    "score": float(score),
                    "metadata": self.chunk_metadata[idx]
                })
        
        return results
    
    def generate_answer(self, query: str, context_chunks: List[str]) -> str:
        """Generate answer using LLM with retrieved context"""
        context = "\n\n".join(context_chunks)
        return self.llm_client.generate_answer(query, context)
    
    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Complete RAG pipeline"""
        # Retrieve relevant chunks
        search_results = self.semantic_search(question, k)
        
        if not search_results:
            return {"answer": "No relevant information found.", "sources": []}
        
        # Extract context
        context_chunks = [result["text"] for result in search_results]
        
        # Generate answer
        answer = self.generate_answer(question, context_chunks)
        
        return {
            "answer": answer,
            "sources": search_results,
            "context_used": len(context_chunks)
        }
    
    def save_index(self, filepath: str):
        """Save the vector database and chunks"""
        data = {
            "chunks": self.chunks,
            "chunk_metadata": self.chunk_metadata
        }
        
        with open(filepath + ".pkl", "wb") as f:
            pickle.dump(data, f)
        
        if self.vector_db:
            faiss.write_index(self.vector_db, filepath + ".faiss")
    
    def load_index(self, filepath: str):
        """Load saved vector database and chunks"""
        with open(filepath + ".pkl", "rb") as f:
            data = pickle.load(f)
        
        self.chunks = data["chunks"]
        self.chunk_metadata = data["chunk_metadata"]
        self.vector_db = faiss.read_index(filepath + ".faiss")
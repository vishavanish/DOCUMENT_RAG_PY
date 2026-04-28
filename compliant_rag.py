import os
import numpy as np
import pickle
from typing import List, Dict, Any
import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class CompliantRAG:
    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
        # Dense embedding model as per specification
        self.embedding_model = SentenceTransformer(embedding_model)
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Specialized vector database (FAISS)
        self.vector_db = None
        self.chunks = []
        self.chunk_metadata = []
        
    def load_pdf(self, pdf_path: str) -> str:
        """Doc Loader: Extract raw text from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        clean_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
                        import re
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        text += clean_text + "\n"
                
                if not text.strip():
                    return "Document content could not be extracted."
                return text
        except Exception as e:
            print(f"PDF loading error: {e}")
            return "Error loading PDF document."
    
    def split_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Text Splitter: Chunking WITH OVERLAP as per specification"""
        import re
        text = re.sub(r'[^\w\s.,!?;:-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        words = text.split()
        chunks = []
        
        # Implement overlap as specified
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) > 20:  # Minimum chunk size
                chunk = " ".join(chunk_words)
                chunks.append(chunk)
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate DENSE vector embeddings as per specification"""
        return self.embedding_model.encode(texts)
    
    def build_vector_database(self, embeddings: np.ndarray):
        """Specialized Vector Database using FAISS as per specification"""
        dimension = embeddings.shape[1]
        
        # FAISS IndexFlatIP for cosine similarity (specialized vector DB)
        self.vector_db = faiss.IndexFlatIP(dimension)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.vector_db.add(embeddings.astype('float32'))
    
    def index_document(self, pdf_path: str) -> int:
        """Complete Phase 1: Indexing & Preparation"""
        # Step 1: Document Loading
        text = self.load_pdf(pdf_path)
        
        # Step 2: Text Splitting with overlap
        self.chunks = self.split_text(text)
        
        # Store metadata
        self.chunk_metadata = [{"chunk_id": i, "source": pdf_path} 
                              for i in range(len(self.chunks))]
        
        # Step 3: Generate dense embeddings
        embeddings = self.generate_embeddings(self.chunks)
        
        # Step 4: Store in specialized vector database
        self.build_vector_database(embeddings)
        
        return len(self.chunks)
    
    def semantic_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Step 6: Semantic Search using cosine similarity"""
        if not self.vector_db or not self.chunks:
            return []
        
        # Step 5: User Query Embedding (same model)
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Semantic search with cosine similarity
        scores, indices = self.vector_db.search(query_embedding.astype('float32'), k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks) and score > 0:
                results.append({
                    "text": self.chunks[idx],
                    "score": float(score),
                    "metadata": self.chunk_metadata[idx]
                })
        
        return results
    
    def generate_answer(self, query: str, context: str) -> str:
        """Step 8: Final Generation using LLM Brain"""
        try:
            # Step 7: System Query (Prompt Assembly)
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={self.google_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"You are a helpful assistant that analyzes content. Answer based only on the provided context.\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
                    }]
                }]
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"LLM Error: {e}")
            raise Exception(f"LLM is required but unavailable: {e}")
    
    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Complete Phase 2: Retrieval & Generation"""
        # Retrieve relevant chunks
        search_results = self.semantic_search(question, k)
        
        if not search_results:
            return {"answer": "No relevant information found.", "sources": []}
        
        # Combine context
        context = "\n\n".join([result["text"] for result in search_results])
        
        # Generate final answer
        answer = self.generate_answer(question, context)
        
        return {
            "answer": answer,
            "sources": search_results,
            "context_used": len(search_results)
        }
    
    def save_index(self, filepath: str):
        """Save specialized vector database and chunks"""
        data = {
            "chunks": self.chunks,
            "chunk_metadata": self.chunk_metadata
        }
        
        with open(filepath + ".pkl", "wb") as f:
            pickle.dump(data, f)
        
        if self.vector_db:
            faiss.write_index(self.vector_db, filepath + ".faiss")
    
    def load_index(self, filepath: str):
        """Load specialized vector database and chunks"""
        with open(filepath + ".pkl", "rb") as f:
            data = pickle.load(f)
        
        self.chunks = data["chunks"]
        self.chunk_metadata = data["chunk_metadata"]
        self.vector_db = faiss.read_index(filepath + ".faiss")
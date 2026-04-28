import os
import numpy as np
import pickle
from typing import List, Dict, Any
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class SimpleRAG:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.chunks = []
        self.chunk_vectors = None
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
    def load_pdf(self, pdf_path: str) -> str:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        # Clean and encode text properly
                        clean_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
                        # Remove excessive spaces and fix formatting
                        import re
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        clean_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_text)
                        text += clean_text + "\n"
                
                if not text.strip():
                    return "Document content could not be extracted."
                
                return text
        except Exception as e:
            print(f"PDF loading error: {e}")
            return "Error loading PDF document."
    
    def split_text(self, text: str, chunk_size: int = 300) -> List[str]:
        # Clean text first
        import re
        text = re.sub(r'[^\w\s.,!?;:-]', ' ', text)  # Remove special chars
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Split into sentences first for better chunks
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) < chunk_size * 5:  # Approx word count
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return [chunk for chunk in chunks if len(chunk) > 50]
    
    def index_document(self, pdf_path: str):
        text = self.load_pdf(pdf_path)
        self.chunks = self.split_text(text)
        self.chunk_vectors = self.vectorizer.fit_transform(self.chunks)
        return len(self.chunks)
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self.chunks:
            return []
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.chunk_vectors)[0]
        
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    "text": self.chunks[idx],
                    "score": float(similarities[idx])
                })
        
        return results
    
    def generate_answer(self, query: str, context: str) -> str:
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={self.google_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"You are a helpful assistant that analyzes news content. Answer based only on the provided context.\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
                    }]
                }]
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"Google Gemini API Error: {e}")
            raise Exception(f"LLM is required but unavailable: {e}")
    
    def query(self, question: str, k: int = 3) -> Dict:
        results = self.search(question, k)
        if not results:
            return {"answer": "No relevant information found.", "sources": []}
        
        context = "\n\n".join([r["text"] for r in results])
        answer = self.generate_answer(question, context)
        
        return {"answer": answer, "sources": results}
    
    def save_index(self, filepath: str):
        """Save the vectorizer and chunks"""
        data = {
            "chunks": self.chunks,
            "vectorizer": self.vectorizer,
            "chunk_vectors": self.chunk_vectors
        }
        with open(filepath + ".pkl", "wb") as f:
            pickle.dump(data, f)
    
    def load_index(self, filepath: str):
        """Load saved vectorizer and chunks"""
        with open(filepath + ".pkl", "rb") as f:
            data = pickle.load(f)
        
        self.chunks = data["chunks"]
        self.vectorizer = data["vectorizer"]
        self.chunk_vectors = data["chunk_vectors"]
import requests
import json

class LocalLLM:
    """Alternative LLM client for local models (Ollama, etc.)"""
    
    def __init__(self, base_url="http://localhost:11434", model="llama2"):
        self.base_url = base_url
        self.model = model
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using local LLM"""
        prompt = f"""Based on the following context, answer the user's question. If the answer cannot be found in the context, say "I cannot find this information in the provided document."

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 500}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "No response generated")
            else:
                return f"Error: Local LLM returned status {response.status_code}"
                
        except Exception as e:
            return f"Local LLM unavailable: {str(e)}"
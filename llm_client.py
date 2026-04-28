import openai
import os
from dotenv import load_dotenv
from local_llm import LocalLLM

load_dotenv()

class LLMClient:
    def __init__(self, use_local=False):
        self.use_local = use_local or os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'
        
        if self.use_local:
            self.local_llm = LocalLLM()
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if self.api_key:
                openai.api_key = self.api_key
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with retrieved context"""
        if self.use_local:
            return self.local_llm.generate_answer(query, context)
        
        if not self.api_key:
            return self._fallback_answer(query, context)
        
        prompt = f"""Based on the following context, answer the user's question. If the answer cannot be found in the context, say "I cannot find this information in the provided document."

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based only on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"LLM error: {e}")
            return self._fallback_answer(query, context)
    
    def _fallback_answer(self, query: str, context: str) -> str:
        """Fallback when LLM is not available"""
        return f"Based on the document content, here are the most relevant sections for '{query}':\n\n{context[:800]}..."
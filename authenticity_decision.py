from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import DatabaseManager
from simple_rag import SimpleRAG

class AuthenticityDecision:
    def __init__(self):
        # TASK 4: Source Trust Configuration
        self.trust_scores = {
            "BBC News": 0.9,
            "Reuters": 0.95,
            "CNN": 0.85,
            "The Times of India": 0.7,
            "The Hindu": 0.8,
            "Associated Press": 0.9,
            "NPR": 0.85,
            "Wall Street Journal": 0.8
        }
        self.unknown_source_score = 0.3
        
        self.db = DatabaseManager()
        self.rag_system = SimpleRAG()
    
    def get_source_trust_score(self, source_name: str, author: str = None, source_id: str = None) -> float:
        """TASK 4 & 5: Calculate trust score with penalties"""
        # Get base trust score
        base_score = self.trust_scores.get(source_name, self.unknown_source_score)
        
        # TASK 5: Apply penalties
        penalty = 0.0
        if not author or author.strip() == "":
            penalty += 0.1
        if not source_id or source_id.strip() == "":
            penalty += 0.2
        
        # Final score between 0 and 1
        final_score = max(0.0, min(1.0, base_score - penalty))
        return final_score
    
    def get_similar_articles(self, news_text: str, threshold: float = 0.8) -> List[Dict]:
        """Get similar articles from database using RAG-like similarity"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get all articles for comparison
            cursor.execute("""
                SELECT title, description, source_name, published_at, created_at, url
                FROM articles 
                ORDER BY created_at DESC 
                LIMIT 100
            """)
            
            articles = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Simple similarity calculation (can be enhanced with actual RAG)
            similar_articles = []
            for article in articles:
                # Basic text similarity (word overlap)
                similarity = self._calculate_similarity(news_text, article['title'] + " " + (article['description'] or ""))
                
                if similarity >= threshold:
                    similar_articles.append({
                        "title": article['title'],
                        "description": article['description'],
                        "source_name": article['source_name'],
                        "published_at": article['published_at'],
                        "similarity": similarity,
                        "url": article['url']
                    })
            
            return similar_articles
            
        except Exception as e:
            print(f"Error getting similar articles: {e}")
            return []
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple word-based similarity calculation"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def check_time_consistency(self, articles: List[Dict]) -> bool:
        """TASK 7: Check if articles were published within 48 hours"""
        if len(articles) < 2:
            return True
        
        publish_times = []
        for article in articles:
            if article.get('published_at'):
                if isinstance(article['published_at'], str):
                    try:
                        pub_time = datetime.strptime(article['published_at'], '%Y-%m-%d %H:%M:%S')
                        publish_times.append(pub_time)
                    except:
                        continue
                else:
                    publish_times.append(article['published_at'])
        
        if len(publish_times) < 2:
            return True
        
        # Check if all articles are within 48 hours of each other
        min_time = min(publish_times)
        max_time = max(publish_times)
        
        time_diff = max_time - min_time
        return time_diff <= timedelta(hours=48)
    
    def analyze_authenticity(self, news_text: str, news_title: str = "") -> Dict[str, Any]:
        """Complete authenticity analysis pipeline"""
        
        # Combine title and text for analysis
        full_text = f"{news_title} {news_text}".strip()
        
        # STEP 1 & TASK 6: Get similar articles and count strong matches
        similar_articles = self.get_similar_articles(full_text, threshold=0.8)
        similar_count = len(similar_articles)
        
        # STEP 2: Calculate average source credibility
        if similar_articles:
            trust_scores = []
            for article in similar_articles:
                score = self.get_source_trust_score(
                    article['source_name'],
                    author=None,  # Not available in current DB schema
                    source_id=None  # Not available in current DB schema
                )
                trust_scores.append(score)
            
            average_trust_score = sum(trust_scores) / len(trust_scores)
        else:
            average_trust_score = 0.0
        
        # STEP 3 & TASK 7: Check time consistency
        time_consistent = self.check_time_consistency(similar_articles)
        
        # STEP 4 & TASK 8: Apply decision rules
        label = self._determine_label(similar_count, average_trust_score, time_consistent)
        
        # Calculate confidence percentage
        confidence = self._calculate_confidence(similar_count, average_trust_score, time_consistent)
        
        # STEP 5: Prepare evidence
        evidence = {
            "similar_articles_count": similar_count,
            "average_trust_score": round(average_trust_score, 2),
            "time_consistent": time_consistent,
            "supporting_sources": [article['source_name'] for article in similar_articles[:5]],
            "similar_articles": similar_articles[:3]  # Top 3 for display
        }
        
        # Generate explanation
        reason = self._generate_explanation(similar_count, average_trust_score, time_consistent, similar_articles)
        
        return {
            "status": label,
            "confidence": confidence,
            "evidence": evidence,
            "reason": reason,
            "similar_count": similar_count,
            "average_trust_score": average_trust_score,
            "time_consistent": time_consistent
        }
    
    def _determine_label(self, similar_count: int, average_trust_score: float, time_consistent: bool) -> str:
        """TASK 8: Decision logic for authenticity labeling"""
        
        # VERIFIED REAL
        if similar_count >= 3 and average_trust_score >= 0.7 and time_consistent:
            return "VERIFIED REAL"
        
        # LIKELY REAL
        elif similar_count >= 2 and average_trust_score >= 0.6:
            return "LIKELY REAL"
        
        # LIKELY FAKE
        elif similar_count == 0 or average_trust_score <= 0.4:
            return "LIKELY FAKE"
        
        # UNVERIFIED
        else:
            return "UNVERIFIED"
    
    def _calculate_confidence(self, similar_count: int, average_trust_score: float, time_consistent: bool) -> int:
        """Calculate confidence percentage"""
        base_confidence = 50
        
        # Add confidence based on similar articles
        base_confidence += min(similar_count * 10, 30)
        
        # Add confidence based on trust score
        base_confidence += int(average_trust_score * 20)
        
        # Add confidence for time consistency
        if time_consistent:
            base_confidence += 10
        
        return min(base_confidence, 95)
    
    def _generate_explanation(self, similar_count: int, average_trust_score: float, 
                            time_consistent: bool, similar_articles: List[Dict]) -> str:
        """Generate human-readable explanation"""
        
        if similar_count == 0:
            return "No similar articles found in our database."
        
        sources = list(set([article['source_name'] for article in similar_articles[:3]]))
        source_text = ", ".join(sources)
        
        if similar_count >= 3 and average_trust_score >= 0.7:
            return f"Multiple trusted sources ({source_text}) reported similar news within a consistent timeframe."
        
        elif similar_count >= 2:
            return f"Found {similar_count} similar reports from sources including {source_text}."
        
        elif average_trust_score <= 0.4:
            return f"Similar articles found but from sources with low credibility scores."
        
        else:
            return f"Limited evidence found. {similar_count} similar article(s) with mixed source reliability."
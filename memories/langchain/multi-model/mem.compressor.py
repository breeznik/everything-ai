import json
from datetime import datetime , timedelta
from typing import Dict , List , Any
import numpy as np

class IntelligentMemoryCompressor:
    def __init__(self):
        self.compression_rules = {
            'importance_threshold': 0.6,
            'recency_weight': 0.3,
            'frequency_weight': 0.4,
            'user_engagement_weight': 0.3
        }
    
    def calculate_memory_importance(self , memory:Dict[str ,Any]) -> float:
        """Calculate how important a memory is for retention"""
        
        # Recency score (newer = more important)
        memory_date = datetime.fromisoformat(memory['timestamp'])
        days_old = (datetime.now() - memory_date).days
        recency_score = max(0, 1- (days_old / 30))
        
        # Frquency score (mentioned more = more) 
        frequency_score = min(1.0 , memory.get('mention_count' , 1) / 10)
        
        # user engagment score (longer responses = more important)
        engagement_score = min(1.0 , len(memory.get('content','')) / 500 )
        
        # Keywords that indicate importance
        important_keywords = ['problem', 'project', 'deadline', 'important', 'urgent', 'remember']
        
        keyword_score = sum(1 for keyword in important_keywords 
                            if keyword in memory.get('content', '').lower()) / len(important_keywords)
        
        # Weighted combination
        rules = self.compression_rules
        total_score = (
            recency_score * rules['recency_weight'] +
            frequency_score * rules['frequency_weight'] +
            engagement_score * rules['user_engagement_weight'] +
            keyword_score * 0.2
        )
        
        return min(1.0, total_score)
    
    def compress_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Intellignetly compress memory list"""
        
        # Score All Memories
        scored_memories = []
        
        for memory in memories:
            importance = self.calculate_memory_importance(memory)
            scored_memories.append((importance , memory))
        
        # Sort By Importance
        scored_memories.sort(key=lambda x: x[0] , reverse=True)
        
        # keep up top 70% of important memories
        keep_count = int(len(scored_memories)*0.7)
        important_memories = [memory for _, memory in scored_memories[:keep_count]]
        
        # Summarize the rest
        less_important = [memory for _, memory in scored_memories[keep_count:]]
        if less_important:
            summary = self.create_memory_summary(less_important)
            important_memories.append({
                 'type': 'summary',
                'content': summary,
                'timestamp': datetime.now().isoformat(),
                'original_count': len(less_important)
            })
        
        return important_memories
    
    def create_memory_summary(self , memories:List[Dict[str , Any]]) -> str:
        """Create a summary of multiple memories"""
        # Simple summarization - in production you'd use an llm
        topics = {}
        
        for memory in memories:
            content = memory.get('content' , '')
            # extract topics (simplified)
            words = content.lower().split()
            for word in words:
                if len(word) > 4:
                    topics[word] = topics.get(word , 0) + 1
                    
            # Get most common topics
            common_topics = sorted(topics.items() , key=lambda x: x[1] , reverse=True)
            topic_list = [topic for topic, count in common_topics]
            
            return f"Summary of {len(memories)} conversations covering: {', '.join(topic_list)}"
        

# Usage example
compressor = IntelligentMemoryCompressor()

# Simulate a large memory collection
large_memory_collection = [
    {
        'content': 'User asked about machine learning project deadline',
        'timestamp': (datetime.now() - timedelta(days=5)).isoformat(),
        'mention_count': 3
    },
    {
        'content': 'User mentioned they like coffee',
        'timestamp': (datetime.now() - timedelta(days=20)).isoformat(),
        'mention_count': 1
    },
    # ... many more memories
]

# Compress intelligently
optimized_memories = compressor.compress_memories(large_memory_collection)
print(f"Compressed {len(large_memory_collection)} memories to {len(optimized_memories)} {optimized_memories}")
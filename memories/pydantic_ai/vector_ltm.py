from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List , Optional
import asyncio
from datetime import datetime
import json

class MemoryEntry(BaseModel):
    user_id:str
    content:str
    timestamp:datetime
    conversation_id:str
    topics: List[str] = []
    importance_score: float = 0.5
    
class VectorMemorySystem:
        def __init__(self):
            self.agent = Agent('openai:gpt-4')
            self.memory_store: List[MemoryEntry] = []
            self.load_memory()
        
        def  load_memory(self):
            """load existing memories from storage"""
            try:
                with open('vector_memory.json', 'r') as f:
                    data = json.load(f)
                    self.memory_store = [MemoryEntry(**entry) for entry in data]
            except FileNotFoundError:
                self.memory_store = []
        
        def save_memory(self):
            """Save memories to persistent storage"""
            with open('vector_memory.json', 'w') as f:
                json.dump([entry.model_dump() for entry in self.memory_store], f, indent=2, default=str)
        
        async def store_memory(self , user_id : str , content:str , conversation_id: str):
            """Store a new memory with automatic topic extraction"""
            #extract topics using ai 
            
            topic_result = await self.agent.run(
                f"Extract 3-5 key topic or themes from this text. Return as comma-seprated: {content}"
            )
            topics = [topic.strip() for topic in topic_result.output.split(',')]
            
            #calculate importance (you could make this more sophisticated)
            importance = await self._calculate_importance(content)
            
            # create and store memory
            memory = MemoryEntry(
                user_id = user_id,
                content=content,
                timestamp=datetime.now(),
                conversation_id=conversation_id,
                importance_score=importance , 
                topics=topics
            )
            
            self.memory_store.append(memory)
            self.save_memory()
        
        async def _calculate_importance(self , content:str) -> float:
            """Calculate how important this memori is (0.0 to 1.0)"""
            # Simple importance scoring - you could make this much more sophisticated
            importance_keyword = ['problem' , 'issue' , 'urgent' , 'imprtance' , 'deadline']
            
            score = 0.5 #baseline
            content_lower = content.lower()
                        
            for keyword in importance_keyword:
                if keyword in content_lower:
                    score +=0.1
                    
            
            return min(score, 1.0)
        
        async def recall_memories(self , user_id: str , query:str , limit:int=5):
            """Find revelent for a user and query"""
            user_memories = [m for m in self.memory_store if m.user_id == user_id]
            
            if not user_memories:
                return []
            
            # simple keyword (in production , you'd use vector similarity)
            query_words = set(query.lower().split())
            scored_memories = []
            
            for memory in user_memories:
                # calculate revelence score 
                memeory_words = set(memory.content.lower().split())
                topic_words = set(' '.join(memory.topics).lower().split())
                
                keyword_overlap = len(query_words.intersection(memeory_words))
                topic_overlap = len(query_words.intersection(topic_words))
                
                relevance_score = (keyword_overlap * 0.7) + (topic_overlap * 0.3) + memory.importance_score
                
                if relevance_score > 0:
                    scored_memories.append((relevance_score , memory))
                    
            # sort by relevance and return top result
            scored_memories.sort(key=lambda x: x[0] , reverse=True)
            return [memory for _, memory in scored_memories[:limit]]
        
        async def chat_with_memory(self , user_id:str , message:str , conversation_id:str)-> str:
            """Chat with full memory context"""
            # Recall relevant memories
            relevant_memories = await self.recall_memories(user_id, message)
            
            # Build context from memories
            memory_context = ""
            if relevant_memories:
                memory_context = "Previous context:\n"
                for memory in relevant_memories:
                    memory_context += f"- {memory.timestamp.strftime('%Y-%m-%d')}: {memory.content[:100]}...\n"
            
            # Generate response with context
            full_prompt = f"{memory_context}\nCurrent message: {message}"
            response = await self.agent.run(full_prompt)
            
            # Store this interaction
            await self.store_memory(
                user_id=user_id,
                content=f"User: {message}\nAssistant: {response.output}",
                conversation_id=conversation_id
            )
            
            return response.data

# Usage example
memory_system = VectorMemorySystem()

async def main():
    # First conversation
    response1 = await memory_system.chat_with_memory(
        user_id="sarah_123",
        message="I'm working on a machine learning project for my company TechCorp",
        conversation_id="conv_001"
    )

    # Later conversation (different session)
    response2 = await memory_system.chat_with_memory(
        user_id="sarah_123", 
        message="How's my ML project coming along?",
        conversation_id="conv_002"
    )
    # The system will remember Sarah works at TechCorp on an ML project!

if __name__ == "__main__":
    asyncio.run(main())

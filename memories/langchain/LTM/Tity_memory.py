import json
from typing import Dict , Any
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationEntityMemory
from datetime import datetime

class PersistentEntityMemory:
    def __init__(self , storage_file: str = "entity_memory.json"):
        self.storage_file = storage_file
        self.entities = self.load_entities()
        
        #setup langchain entity memory
        self.langchain_memory = ConversationEntityMemory(llm=ChatOpenAI(temperature=0))
        
        #load existing entities into langchain memory
        self.langchain_memory.entity_store = self.entities
        
    def load_entities(self) -> Dict[str, any]:
        """load entities from storage"""
        try:
            with open(self.storage_file , 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_entities(self):
        """Save current entities to storage"""
        print('saving entiteis')
        with open(self.storage_file, 'w') as f:
            json.dump(self.langchain_memory.entity_store , f , indent=2)

    def get_current_timestamp(self) -> str:
        """Return the current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def remember_user(self , user_id: str, conversation_text:str):
        """process and remember information about a user"""
        #extract entities from conversation
        entities = self.langchain_memory.llm.invoke(f"Extract key information about people, companies and preferences from: {conversation_text}")
        
        #store user-specific information
        if user_id not in self.entities:
            self.entities[user_id] = {}
        
        # update entity information
        self.entities[user_id].update({
            "last_conversation": conversation_text[:200], #keep snippet
            "last_seen": self.get_current_timestamp(),
            "conversation_count": self.entities[user_id].get("conversation_count" , 0)+1
        })
        
        # save to persistent storage
        self.save_entities()
    
    def get_user_context(self, user_id: str) -> str:
        """Get relevant context about a user"""
        if user_id not in self.entities:
            return "This appears to be a new user."
        
        user_info = self.entities[user_id]
        return f"""
        Previous context about this user:
        - Last seen: {user_info.get('last_seen', 'Unknown')}
        - Conversations: {user_info.get('conversation_count', 0)}
        - Last topic: {user_info.get('last_conversation', 'No previous context')}
        """



# Usage example
memory_system = PersistentEntityMemory()

# When user starts conversation
user_context = memory_system.get_user_context("sarah_123")
print(user_context)

# After conversation ends
memory_system.remember_user("sarah_123", "Sarah discussed her new role as marketing director at TechCorp")


# so this is the custom base class for handling the entity graph with entity memory
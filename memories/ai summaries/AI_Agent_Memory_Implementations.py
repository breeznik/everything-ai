# Basic Chat Without Memory

def basic_chat_no_memory(user_message):
    """
    A basic chat function that does not retain any memory of previous messages.
    Each call is treated as a new conversation, leading to a lack of context retention.
    """
    response = ChatOpenAI.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content

# Example usage
# print(basic_chat_no_memory("My name is Sarah"))  # AI responds without remembering the name
# print(basic_chat_no_memory("What's my name?"))   # AI does not know the name since it has no memory


# Short-Term Memory with LangChain: Basic Conversation Memory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

def create_basic_conversation():
    """
    Sets up a LangChain conversation with buffer memory to retain full conversation history.
    """
    # Initialize the language model
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create a memory system that retains the entire conversation history
    memory = ConversationBufferMemory()

    # Set up the conversation chain with memory
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True  # Enable verbose mode to see the internal process
    )
    return conversation

# Example usage
# conversation = create_basic_conversation()
# response1 = conversation.predict(input="Hi, I'm Sarah and I love hiking")
# print(response1)  # Expected: AI acknowledges Sarah's interest in hiking
# response2 = conversation.predict(input="What outdoor activities would you recommend for me?")
# print(response2)  # Expected: AI suggests activities related to hiking


# Short-Term Memory with LangChain: Summary Memory
from langchain.memory import ConversationSummaryMemory

def create_summary_conversation():
    """
    Sets up a LangChain conversation with summary memory to condense older conversation parts.
    """
    # Initialize the language model for memory summarization
    summary_llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Create summary memory that condenses older conversation parts
    summary_memory = ConversationSummaryMemory(
        llm=summary_llm,
        max_token_limit=1000  # Trigger summarization when token limit is reached
    )

    # Initialize the language model for the conversation
    conversation_llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Set up the conversation chain with summary memory
    conversation_with_summary = ConversationChain(
        llm=conversation_llm,
        memory=summary_memory,
        verbose=True
    )
    return conversation_with_summary


# Short-Term Memory with LangChain: Window Memory
from langchain.memory import ConversationBufferWindowMemory

def create_window_conversation():
    """
    Sets up a LangChain conversation with window memory to retain the last 10 messages.
    """
    # Initialize the language model
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create window memory that retains the last 10 message exchanges
    window_memory = ConversationBufferWindowMemory(k=10)

    # Set up the conversation chain with window memory
    conversation_with_window = ConversationChain(
        llm=llm,
        memory=window_memory,
        verbose=True
    )
    return conversation_with_window


# Short-Term Memory with Pydantic AI: Structured Memory Management
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from typing import List

class ConversationManager:
    def __init__(self):
        """
        Initializes the ConversationManager with an AI agent and conversation history.
        """
        self.agent = Agent(
            'ChatOpenAI:gpt-4',
            system_prompt='You are a helpful assistant with perfect memory of our conversation.'
        )
        self.conversation_history: List[ModelMessage] = []

    async def chat(self, user_input: str) -> str:
        """
        Processes the user's input, adds it to the conversation history, gets the AI's response,
        and updates the history with the response.
        """
        
        # Get AI response using the full conversation history
        result = await self.agent.run(
            user_input,
            message_history=self.conversation_history
        )
        
        # Add AI's response to history
        self.conversation_history.extend(result.new_messages())
        
        return result.output

    def get_conversation_summary(self) -> dict:
        """
        Provides a summary of the conversation, including total messages, user messages,
        and recent topics.
        """
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len([msg for msg in self.conversation_history if isinstance(msg, UserMessage)]),
            "recent_topics": self._extract_recent_topics()
        }

    def _extract_recent_topics(self) -> List[str]:
        """
        Extracts recent topics from the conversation history.
        This is a placeholder and should be implemented with actual topic extraction logic.
        """
        # Placeholder implementation
        return ["hiking", "outdoor activities"]


# Short-Term Memory with Pydantic AI: Custom Memory Optimization
class OptimizedConversationManager(ConversationManager):
    def __init__(self, max_messages=20):
        """
        Initializes the OptimizedConversationManager with a maximum number of messages to retain.
        """
        super().__init__()
        self.max_messages = max_messages

    def _trim_history(self):
        """
        Trims the conversation history to retain only the first message and the last (max_messages - 1) messages.
        This helps in managing memory usage by limiting the history length.
        """
        if len(self.conversation_history) > self.max_messages:
            first_message = self.conversation_history[0]
            recent_messages = self.conversation_history[-(self.max_messages - 1):]
            self.conversation_history = [first_message] + recent_messages

    async def chat(self, user_input: str) -> str:
        """
        Processes the user's input, gets the AI's response, and trims the history if necessary.
        """
        result = await super().chat(user_input)
        self._trim_history()
        return result


# Long-Term Memory with LangChain: Entity Memory
from langchain.memory import ConversationEntityMemory
from langchain.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.chains import ConversationChain

def create_entity_conversation():
    """
    Sets up a LangChain conversation with entity memory to track key entities across sessions.
    """
    # Initialize the language model for entity extraction
    entity_llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Create entity memory to track key entities
    entity_memory = ConversationEntityMemory(
        llm=entity_llm,
        k=10,  # Track the 10 most recent entities
    )

    # Initialize the language model for the conversation
    conversation_llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Set up the conversation chain with entity memory and specific prompt template
    conversation = ConversationChain(
        llm=conversation_llm,
        memory=entity_memory,
        prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
        verbose=True
    )
    return conversation


# Long-Term Memory with LangChain: Persistent Entity Memory
import json
from datetime import datetime
from typing import Dict, Any

class PersistentEntityMemory:
    def __init__(self, storage_file: str = "entity_memory.json"):
        """
        Initializes a persistent entity memory system that saves data to a JSON file.
        """
        self.storage_file = storage_file
        self.entities = self.load_entities()
        
        # Initialize the language model for entity extraction
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        
        # Set up LangChain entity memory
        self.langchain_memory = ConversationEntityMemory(
            llm=llm,
            k=10
        )
        
        # Load existing entities into LangChain memory
        self.langchain_memory.entity_store = self.entities

    def load_entities(self) -> Dict[str, Any]:
        """Load entities from storage"""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_entities(self):
        """Save current entities to storage"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.langchain_memory.entity_store, f, indent=2)

    def remember_user(self, user_id: str, conversation_text: str):
        """Process and remember information about a user"""
        # Extract entities from conversation using the language model
        entities = self.langchain_memory.llm.predict(
            f"Extract key information about people, companies, and preferences from: {conversation_text}"
        )
        
        # Store user-specific information
        if user_id not in self.entities:
            self.entities[user_id] = {}
        
        # Update entity information
        self.entities[user_id].update({
            "last_conversation": conversation_text[:200],  # Keep a snippet of the last conversation
            "last_seen": datetime.now().isoformat(),
            "conversation_count": self.entities[user_id].get("conversation_count", 0) + 1
        })
        
        # Save to persistent storage
        self.save_entities()

    def get_user_context(self, user_id: str) -> str:
        """Get relevant context about a user"""
        if user_id not in self.entities:
            return "This appears to be a new user."
        
        user_info = self.entities[user_id]
        return f"""Previous context about this user:
- Last seen: {user_info.get('last_seen', 'Unknown')}
- Conversations: {user_info.get('conversation_count', 0)}
- Last topic: {user_info.get('last_conversation', 'No previous context')}"""


# Long-Term Memory with Pydantic AI: Vector Memory
from pydantic import BaseModel
import asyncio

class MemoryEntry(BaseModel):
    user_id: str
    content: str
    timestamp: datetime
    conversation_id: str
    topics: List[str] = []
    importance_score: float = 0.5

class VectorMemorySystem:
    def __init__(self):
        """
        Initializes the VectorMemorySystem with an AI agent and loads existing memories.
        """
        self.agent = Agent('ChatOpenAI:gpt-4')
        self.memory_store: List[MemoryEntry] = []
        self.load_memory()

    def load_memory(self):
        """
        Loads memories from 'vector_memory.json' if it exists.
        """
        try:
            with open('vector_memory.json', 'r') as f:
                data = json.load(f)
                self.memory_store = [MemoryEntry(**entry) for entry in data]
        except FileNotFoundError:
            self.memory_store = []

    def save_memory(self):
        """
        Saves the current memory store to 'vector_memory.json'.
        """
        with open('vector_memory.json', 'w') as f:
            json.dump([entry.dict() for entry in self.memory_store], f, indent=2, default=str)

    async def store_memory(self, user_id: str, content: str, conversation_id: str):
        """
        Stores a new memory entry after extracting topics and calculating importance.
        """
        # Extract topics using the AI agent
        topic_result = await self.agent.run(
            f"Extract 3-5 key topics or themes from this text. Return as comma-separated list: {content}"
        )
        topics = [topic.strip() for topic in topic_result.data.split(',')]
        
        # Calculate importance score
        importance = await self._calculate_importance(content)
        
        # Create memory entry
        memory = MemoryEntry(
            user_id=user_id,
            content=content,
            timestamp=datetime.now(),
            conversation_id=conversation_id,
            topics=topics,
            importance_score=importance
        )
        
        # Add to memory store and save
        self.memory_store.append(memory)
        self.save_memory()

    async def _calculate_importance(self, content: str) -> float:
        """
        Calculates an importance score for the memory based on keywords.
        This is a simple implementation and can be enhanced.
        """
        importance_keywords = ['problem', 'issue', 'urgent', 'important', 'deadline', 'project']
        score = 0.5  # baseline
        content_lower = content.lower()
        for keyword in importance_keywords:
            if keyword in content_lower:
                score += 0.1
        return min(score, 1.0)

    async def recall_memories(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Recalls relevant memories for a user based on the query using simple keyword matching.
        In production, consider using vector similarity for better results.
        """
        user_memories = [m for m in self.memory_store if m.user_id == user_id]
        if not user_memories:
            return []
        
        query_words = set(query.lower().split())
        scored_memories = []
        
        for memory in user_memories:
            memory_words = set(memory.content.lower().split())
            topic_words = set(' '.join(memory.topics).lower().split())
            
            keyword_overlap = len(query_words.intersection(memory_words))
            topic_overlap = len(query_words.intersection(topic_words))
            
            relevance_score = (keyword_overlap * 0.7) + (topic_overlap * 0.3) + memory.importance_score
            
            if relevance_score > 0:
                scored_memories.append((relevance_score, memory))
        
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]

    async def chat_with_memory(self, user_id: str, message: str, conversation_id: str) -> str:
        """
        Processes the user's message with context from relevant memories and stores the interaction.
        """
        # Recall relevant memories
        relevant_memories = await self.recall_memories(user_id, message)
        
        # Build memory context
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
            content=f"User: {message}\n{response.data}",
            conversation_id=conversation_id
        )
        
        return response.data


# Long-Term Memory with Agno: Production-Grade Memory
from agno import Agent
from agno.memory import VectorMemory

class ProductionMemoryAgent:
    def __init__(self, user_id: str):
        """
        Initializes the ProductionMemoryAgent with user-specific memory and agent.
        """
        self.user_id = user_id
        
        # Create user-specific vector memory
        self.memory = VectorMemory(
            collection_name=f"user_{user_id}",
            embeddings_model="text-embedding-3-large",
            distance_metric="cosine"
        )
        
        # Create agent with memory and instructions
        self.agent = Agent(
            model="gpt-4-turbo",
            memory=self.memory,
            instructions="""You are an AI assistant with perfect memory of your conversations with this user.
Always reference relevant past conversations when appropriate.
Be personal and build on previous interactions."""
        )

    async def chat(self, message: str) -> str:
        """
        Processes the user's message using the agent with memory integration.
        """
        response = await self.agent.run(message)
        return response

    async def get_memory_summary(self) -> dict:
        """
        Provides a summary of stored memories, including total memories, topics, and interaction timestamps.
        """
        memories = await self.memory.search(query="", limit=100)
        if not memories:
            return {"total_memories": 0, "conversation_topics": [], "first_interaction": None, "last_interaction": None}
        
        topics = await self._extract_topics(memories)
        first_interaction = memories[-1]["metadata"]["timestamp"]
        last_interaction = memories[0]["metadata"]["timestamp"]
        
        return {
            "total_memories": len(memories),
            "conversation_topics": topics,
            "first_interaction": first_interaction,
            "last_interaction": last_interaction
        }

    async def _extract_topics(self, memories: list) -> list:
        """
        Extracts the top 5 topics from recent memories using the agent.
        """
        if not memories:
            return []
        
        recent_content = " ".join([mem["content"] for mem in memories[:20]])
        topic_response = await self.agent.run(
            f"Extract the top 5 topics discussed in these conversations: {recent_content}"
        )
        return topic_response.split('\n')[:5]

# Example usage for all implementations
async def main():
    # Basic chat without memory
    print("Basic Chat Without Memory:")
    print(basic_chat_no_memory("My name is Sarah"))
    print(basic_chat_no_memory("What's my name?"))
    
    # LangChain basic conversation
    print("\nLangChain Basic Conversation:")
    conversation = create_basic_conversation()
    print(conversation.predict(input="Hi, I'm Sarah and I love hiking"))
    print(conversation.predict(input="What outdoor activities would you recommend for me?"))
    
    # Pydantic AI conversation
    print("\nPydantic AI Conversation:")
    chat_manager = ConversationManager()
    print(await chat_manager.chat("Hi, I'm planning a camping trip"))
    print(await chat_manager.chat("What should I pack?"))
    
    # Agno production memory
    print("\nAgno Production Memory:")
    sarah_agent = ProductionMemoryAgent("sarah_123")
    print(await sarah_agent.chat("I'm launching a new product at TechCorp next month"))
    print(await sarah_agent.chat("How should I prepare for the product launch?"))

if __name__ == "__main__":
    asyncio.run(main())
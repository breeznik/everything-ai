from langchain.memory import (
    CombinedMemory,
    ConversationSummaryMemory,
    ConversationEntityMemory,
    ConversationBufferMemory,
)
from langchain_community.memory.kg import ConversationKGMemory
from langchain_core.runnables import RunnableMap
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory

# --------- Advanced Memory Setup -------------
class AdvancedMemorySystem:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7)

        self.summary_memory = ConversationSummaryMemory(
            llm=self.llm,
            max_token_limit=1000,
            memory_key="summary_history"
        )

        self.entity_memory = ConversationEntityMemory(
            llm=self.llm,
            k=15,
            memory_key="entity_history"
        )

        self.kg_memory = ConversationKGMemory(
            llm=self.llm,
            k=10,
            memory_key="kg_history"
        )
        self.buffer_memory = ConversationBufferMemory(
            memory_key="chat_history",  # ✅ Unique key
            return_messages=True
        )

        self.combined_memory = CombinedMemory(
            memories=[
                self.summary_memory,
                self.entity_memory,
                self.kg_memory,
                self.buffer_memory
            ]
        )

        self.user_patterns = {}

    def track_interaction_pattern(self, user_id: str, interacation_data: dict):
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                'preferred_response_length': 'medium',
                'typical_session_duration': 0,
                'common_topics': [],
                'interaction_times': [],
                'complexity_preference': 'intermediate'
            }

        patterns = self.user_patterns[user_id]

        if 'response_length_preference' in interacation_data:
            patterns['preferred_response_length'] = interacation_data['response_length_preference']

        if 'session_duration' in interacation_data:
            current_avg = patterns['typical_session_duration']
            new_duration = interacation_data['session_duration']
            patterns['typical_session_duration'] = (current_avg * 0.8) + (new_duration * 0.2)

        if 'topics' in interacation_data:
            for topic in interacation_data['topics']:
                if topic not in patterns['common_topics']:
                    patterns['common_topics'].append(topic)

    def get_personalized_context(self, user_id: str) -> str:
        if user_id not in self.user_patterns:
            return ""

        patterns = self.user_patterns[user_id]

        context = f"""
        User Interaction Preferences:
        - Prefers {patterns['preferred_response_length']} length responses
        - Typically engages for {patterns['typical_session_duration']:.1f} minutes
        - Common topics: {', '.join(patterns['common_topics'][:5])}
        - Complexity level: {patterns['complexity_preference']}
        """
        return context.strip()

# --------- Prompt Template -------------
prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Use the following contextual memories:

Summary: {summary_history}
Entities: {entity_history}
Knowledge Graph: {kg_history}
Conversation History: {chat_history}

{input}
""")

# --------- Session Memory Store -------------
memory_store = {}

def get_message_history(session_id: str):
    if session_id not in memory_store:
        memory_store[session_id] = InMemoryChatMessageHistory()
    return memory_store[session_id]

if __name__ == "__main__":
    user_id = "Nikhil_123"
    advanced_memory = AdvancedMemorySystem()

    advanced_memory.track_interaction_pattern(user_id, {
        'response_length_preference': 'detailed',
        'session_duration': 15.5,
        'topics': ['machine learning', 'data science', 'python'],
        'complexity_preference': 'advanced'
    })

    personalized_context = advanced_memory.get_personalized_context(user_id)

    runnable = prompt | advanced_memory.llm

    chain = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )

    memory_vars = advanced_memory.combined_memory.load_memory_variables({"input": ""})

    full_inputs = {
        "chat_history": memory_vars.get("chat_history", ""),
        "summary_history": memory_vars.get("summary_history", ""),
        "entity_history": memory_vars.get("entity_history", ""),
        "kg_history": memory_vars.get("kg_history", ""),
        "input": "How do I optimize my neural network?"
    }


    response = chain.invoke(full_inputs, config={"configurable": {"session_id": user_id}})

    print("\nAssistant Response:\n", response.content)
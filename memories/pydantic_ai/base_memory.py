from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage , ModelRequest , ModelResponse
from typing import List

class ConversationManager:
    def __init__(self):
        self.agent = Agent('openai:gpt-4', system_prompt="You are a manica bot.")
        self.conversation_history: List[ModelMessage] = []

    async def chat(self, user_input: str) -> str:

         # Let the Agent create and append the user part based on the string
        result = await self.agent.run(user_input, message_history=self.conversation_history)
        
        # Save all messages returned (user + assistant)
        self.conversation_history = result.all_messages()        

        return result.output

    def get_conversation_summary(self) -> dict:
        return {
        "total_messages": len(self.conversation_history),
        "user_messages": len([m for m in self.conversation_history if isinstance(m, ModelRequest)]),
        "assistant_messages": len([m for m in self.conversation_history if isinstance(m, ModelResponse)]),
        "recent_topics": self._extract_recent_topics()
        }

    def _extract_recent_topics(self) -> List[str]:
        return ["hiking", "camping trip"]  # stub for now


from base_memory import ConversationManager

class OptimizedConversationManager(ConversationManager):
    def __init__(self , max_messages = 20):
        super().__init__()
        self.max_messsages = max_messages
    
    def trim_history(self):
        """keep conversation from getting too long"""
        
        if len(self.conversation_history)> self.max_messsages:
            #keep the first messsage (usally contains context)
            # adn the last max_messages-1 messages
            first_message = self.conversation_history[0]
            recent_messages = self.conversation_history[-(self.max_messsages-1):]
            self.conversation_history = [first_message] + recent_messages
    
    async def chat(self, user_input:str) -> str:
        result =  await super().chat(user_input)
        self.trim_history() #optimize after each exchange
        return result
    
    
# Optimization wrapper for the convrestationManager it cuts of the in between part that is not nessesory and keep only first message that in most cases contains the original context and the recent 20 messages.
# i don't like this one sliding window is better. but the way chat manager keeps an track of the topics can be used for indexing the chat.
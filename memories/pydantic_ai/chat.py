import asyncio
from base_memory import ConversationManager  # make sure the filename matches

chat_manager = ConversationManager()

async def main():
    response1 = await chat_manager.chat("Hi, I'm planning a camping trip")
    print(response1)

    response2 = await chat_manager.chat("What should I pack?")
    print(response2)

    print(chat_manager.get_conversation_summary())
    

if __name__ == "__main__":
    asyncio.run(main())

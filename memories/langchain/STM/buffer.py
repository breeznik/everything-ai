from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.base import ConversationChain 
# Load environment variables (e.g., for OpenAI API key)
load_dotenv()

# 1. Set up the Chat Model
llm = ChatOpenAI(temperature=0.7)

# Create a memory system that remembers everything
memory = ConversationBufferMemory()

conversation = ConversationChain(
    llm = llm,
    memory=memory,
    verbose=True  # So you can see what's happening
)

response1 = conversation.predict(input="Hi, I'm Sarah and I love hiking")
print(response1)

response2 = conversation.predict(input="What outdoor activities would you recommend for me?")
print(response2)
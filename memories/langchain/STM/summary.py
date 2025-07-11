from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
#create memory that summerizes old conversations
summary_memory = ConversationSummaryMemory(
    llm=ChatOpenAI(temperature=0),
    max_token_limit = 1000
)

conversation_with_memory = ConversationChain(
    llm=ChatOpenAI(temperature=0.7),
    memory=summary_memory,
    verbose=True
)

# Now your AI remembers context!
response1 = conversation_with_memory.predict(input="Hi, I'm Nikhil. I'm trying to get better at learning new things faster.")
print(response1)

response2 = conversation_with_memory.predict(input="Yeah, I'm currently learning Python and also trying to improve my memory.")
print(response2)

response3 = conversation_with_memory.predict(input="Yes, that would be helpful. I struggle with remembering syntax sometimes.")
print(response3)

response4 = conversation_with_memory.predict(input="That would be great. Something I can follow every day.")
print(response4)

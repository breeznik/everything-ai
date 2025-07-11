from langchain.memory import ConversationEntityMemory
from langchain.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.chains.conversation.base import ConversationChain
from langchain_openai import ChatOpenAI
import asyncio

# create entity memory that tracks important information
entity_memory = ConversationEntityMemory(
    llm=ChatOpenAI(temperature=0),
    k=10 ,# remember the last 10 entities
)


# set up the conversation with entity memory
conversation = ConversationChain(
    llm = ChatOpenAI(temperature=0.7),
    memory=entity_memory,
    prompt = ENTITY_MEMORY_CONVERSATION_TEMPLATE,
    verbose=True
)



async def main():
    userinput = ''
    while(userinput != "exit"):
        userinput = input('You: ')
        response = conversation.predict(input=userinput)
        print(response)
        
if __name__ == "__main__":
    asyncio.run(main())
    
    
#so langhchain maintains an knowledge graph of entities:
# example --
# Sarah:
# - Works at: TechCorp
# - Collaborating with: Mike
# - Project focus: Sustainable energy
# - Role: Project lead (inferred)

# Mike:
# - Colleague of: Sarah
# - Works at: TechCorp (inferred)
# - Focus area: Sustainable energy research

# TechCorp:
# - Type: Company
# - Employees mentioned: Sarah, Mike
# - Project areas: Sustainable energy

# memory duration - 
# session memory - hours
# user memmory - days-months
# domain memory - months-years
# relationship mmeory - years+
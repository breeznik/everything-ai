#agno production grade memeory architecture 

from agno.memory.v2.memory import Memory    
from agno.agent import Agent 
import asyncio

class ProductionMemoryAgent:
    def __init__(self , user_id:str):
        self.user_id = user_id
        
        # create user-specific vector memory
        self.memory = AgentMemory
        
        
# will do this one later
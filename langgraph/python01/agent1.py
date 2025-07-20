from typing import TypedDict , List
from langchain_core.messages import HumanMessage , AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph , START , END
 
load_dotenv()

class AgentState(TypedDict):
    messages: List[HumanMessage]
    
llm = ChatOpenAI(model="gpt-4o")

def process(state:AgentState) -> AgentState:
    
    response = llm.invoke(state["messages"])
    print(f"\nAI: {response.content}")
    state['messages'].append(AIMessage(content = response.content))
    print(state)
    return state

graph = StateGraph(AgentState)
graph.add_node("process" , process)
graph.add_edge(START , "process")
graph.add_edge("process" , END)
agent = graph.compile()


user_input = input("Enter: ")

while user_input != "exit":
    agent.invoke({"messages":  [HumanMessage(content=user_input)]})
    user_input = input("Enter: ")
    
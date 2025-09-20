from typing import Annotated , TypedDict , Sequence, Literal
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage , BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph , START , END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from state import State
from booking.schedule_agent import schedule_graph
load_dotenv()

def superivisor_agent(state:State) -> State:
    print('supervisor agent hit')
    """
    # decides which agent to call based on current state
    # if current step is schedule -> call schedule agent
    # if current step is contact -> call contact agent
    # if current step is None -> call schedule agent
    # if any agent fails -> exit
    """

instruction = """
you are an lounge booking agent supervisor, you help user navigate through booking process.
under you there are two agents
1. schedule agent - helps user to reserve lounge for their flight
2. contact agent - geathers contact information from

you will be the one to initate the booking process by asking user which product they would like to book - 
provide them with these options - 
Arrival Lounge
Departure Lounge
Arrival & Departure Lounge Bundle

once the product is selected - you will call schedule agent to help user with reservation
if user decided to change or update their schedule - you will call schedule agent again
user can exit the booking process at any point.

"""
supervisior_graph_builder = StateGraph(State)

supervisior_graph_builder.add_node("supervisor", superivisor_agent)
supervisior_graph_builder.add_node("schedule_agent", schedule_graph)

supervisior_graph_builder.add_edge(START, "supervisor")
supervisior_graph_builder.add_edge("supervisor", "schedule_agent")
supervisior_graph_builder.add_edge("schedule_agent", END)

superivisor_agent = supervisior_graph_builder.compile()

superivisor_agent.invoke({"messages":HumanMessage(content="Hello")})



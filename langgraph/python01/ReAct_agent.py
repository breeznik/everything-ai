from typing import Annotated , Sequence , TypedDict
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage , BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph , START , END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
load_dotenv()
#Reducer Function

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage] , add_messages]
    
@tool
def add(a: int , b:int):
    """This is an addition fucntion that adds 2 numbers together"""
    return a+b
def sub(a: int , b:int):
    """This is an subtraction fucntion that subtract 2 numbers together"""
    return a-b
def divide(a: int , b:int):
    """This is an division fucntion that divide 2 numbers together"""
    return a/b

tools = [add , sub , divide]

model = ChatOpenAI(model = "gpt-4o").bind_tools(tools)

def model_call(state:AgentState) -> AgentState:
    system_prompt = SystemMessage(content="you are my ai asistant , please answer my query to the best of your stupidity")
    response = model.invoke([system_prompt] + state["messages"])
    return {"messages":[response]}

def should_continue(state:AgentState) -> AgentState:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"
    
graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools" , tool_node)

graph.add_conditional_edges("our_agent" , should_continue , {
    "end":END,
    "continue":"tools"
})

graph.add_edge("tools","our_agent")
graph.add_edge(START, "our_agent")
app = graph.compile()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message , tuple):
            print(message)
        else:
            message.pretty_print()

inputs = {"messages": [("user", "[4,4] [3,1] [5,5] do all the opration on each of the set , add , divide , sub")]}
print_stream(app.stream(inputs , stream_mode="values"))
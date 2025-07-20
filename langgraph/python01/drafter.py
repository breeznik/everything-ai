from typing import Annotated , Sequence , TypedDict
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage , BaseMessage , ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph , START , END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
load_dotenv()
#Reducer Function

# injecting state
documentContent = ""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage] , add_messages]
    
@tool
def update(content: str) -> str:
    """update the document with the provided content"""
    global documentContent
    documentContent = content
    return f"doucment has been updated successfully! the current content is :\n{documentContent}"


def save(filename:str) -> str:
    """save the current document to a text file and finish the process
    Args:
        filename: Name for the text file
    """
    
    global documentContent
    
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
        
    try:
        with open(filename , "w") as file:
            file.write(documentContent)
        print(f"\n Documnet has been saved to: {filename}")
        return f"Document has been saved successfully to '{filename}'. "
    except Exception as e:
        return f"Error saving document: {str(e)}"


tools = [save , update]

model = ChatOpenAI(model = "gpt-4o").bind_tools(tools)

def model_call(state:AgentState) -> AgentState:
    system_prompt = SystemMessage(content=f"""You are a drafter , A helpful writing assistant. You are going to help the user update and draft modify documents
                                  
    -If the user wants to update or modify content, use the 'update' tool with the complete update content.
    -If the user wants to save the finish, you need to use the 'save' tool.
    -make sure to always show the current document state after modification.
    the current document cotent is: {documentContent}""")
    
    if not state["messages"]:
        user_input = "I'm ready to help you update a document. What would you like to create?"
        user_message = HumanMessage(content=user_input)
    else:
        user_input = input("\n What would you like to do with the document? ")
        print(f"\n user: {user_input}")
        user_message = HumanMessage(content=user_input)
    
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]
    response = model.invoke(all_messages)
    
    print(f"\n AI: {response.content}")
    if hasattr(response , "tool_calls") and response.tool_calls:
        print(f"USING TOOLS: {[tc['name'] for tc in response.tool_calls]}")
    
    return {"messages": state["messages"] + [user_message, response]}

def should_continue(state:AgentState) -> AgentState:
    """Determine if we should continue or end the conversation"""
    messages = state["messages"]
    
    if not messages:
        return "continue"
    
    for message in reversed(messages):
        if(isinstance(message, ToolMessage) and "saved" in message.content.lower() and "document" in message.content.lower() ):
            return "end"
    
    return "continue" 

def print_message(messages):
    """function to print the messages in a more readable formate"""
    if not messages:
        return
    
    for message in messages[-3:]:
        if isinstance(message , ToolMessage):
            print(f"\n TOOL RESULT: {message.content}")
    
    
graph = StateGraph(AgentState)
graph.add_node("agent", model_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools" , tool_node)

graph.add_conditional_edges("tools" , should_continue , {
    "end":END,
    "continue":"agent"
})

graph.add_edge("agent","tools")
 
graph.add_edge(START, "agent")
app = graph.compile()

def run_docment_agent():
    print("\n ===== Drafter ==== ")
    
    state = {"message":[]}
    
    for step in app.stream(state , stream_mode="values"):
        if "messages" in step:
            print_message(step["messages"])
        
        print("\n ==== Derafter finished")

if __name__ == "__main__":
    run_docment_agent()
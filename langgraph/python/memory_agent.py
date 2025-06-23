from typing import TypedDict , List , Union
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph , START , END
 
load_dotenv()

class AgentState(TypedDict):
    messages: List[Union[HumanMessage,AIMessage,SystemMessage] ]
    
llm = ChatOpenAI(model="gpt-4o")

def process(state:AgentState) -> AgentState:
    """This node will solve the user query"""
    response = llm.invoke(state["messages"])
    print(f"\nAI: {response.content}")
    state['messages'].append(AIMessage(content = response.content))
    return state

graph = StateGraph(AgentState)
graph.add_node("process" , process)
graph.add_edge(START , "process")
graph.add_edge("process" , END)
agent = graph.compile()

chat_history = []

user_input = input("Enter: ")

while user_input != "exit":
    humanMessage = HumanMessage(content=user_input)
    chat_history.append(humanMessage)
    state = agent.invoke({"messages":  chat_history})
    user_input = input("Enter: ")

with open("loging.txt", "w") as file:
    file.write("Your converstation Log:\n")
    for message in chat_history:
        if isinstance(message , HumanMessage):
            file.write(f"You: {message.content} \n")
        elif isinstance(message , AIMessage):
            file.write(f"AI: {message.content} \n\n")
    file.write("End of the conversation")

print("converstation saved to logging.txt")
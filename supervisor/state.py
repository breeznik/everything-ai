from typing import Annotated , TypedDict , Sequence, Literal
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage , BaseMessage
from langgraph.graph.message import add_messages


class agent_data(TypedDict):
    collected_info: dict
    api_data: dict

class data(TypedDict):
    schedule_agent: agent_data
    contact_agent: agent_data

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage] , add_messages]
    current_step: Literal["schedule", "contact"]
    data: dict
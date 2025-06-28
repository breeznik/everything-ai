import os
import json
import asyncio
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables
current_node = None
memory = []

class ProductType(str, Enum):
    ARRIVALONLY = "ARRIVALONLY"
    DEPARTURE = "DEPARTURE"
    ARRIVALBUNDLE = "ARRIVALBUNDLE"

class FlowType(str, Enum):
    BOOKING = "booking"
    GENERAL = "general"

class ContactInfo(TypedDict):
    title: str
    firstname: str
    lastname: str
    email: str
    phone: str

class CollectedData(TypedDict):
    A: Optional[Any]
    D: Optional[Any]

class ScheduleData(TypedDict):
    A: Optional[Any]
    D: Optional[Any]

class State(TypedDict):
    input: str
    flow: Optional[FlowType]
    done: bool
    current_node: Optional[str]
    collected: CollectedData
    schedule_data: ScheduleData
    product_id: Optional[ProductType]
    contact_info: Optional[ContactInfo]
    reservation_data: Optional[Any]
    messages: List[Dict[str, str]]

# LLM Setup
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

def message_obj(role: str, content: str) -> Dict[str, str]:
    """Create a message object"""
    return {"role": role, "content": content}

def json_parser(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM response"""
    try:
        # Try to extract JSON from the content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
        else:
            json_str = content
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If parsing fails, return a default structure
        return {
            "message": content,
            "done": False,
            "collected": {}
        }

# Instructions (you'll need to import these from your utils)
AGENT_INTRO = """You are a helpful booking assistant. Always respond in a friendly and professional manner."""

CLASSIFY_INSTRUCTION = """
Analyze the user's input and determine if they want to make a booking or have a general question.
Respond with either "booking" or "general".
"""

PRODUCT_TYPE_INSTRUCTION = """
Help the user choose their product type:
- ARRIVALONLY: Only arrival service
- DEPARTURE: Only departure service  
- ARRIVALBUNDLE: Both arrival and departure services

Return JSON with: {"message": "your response", "done": true/false, "collected": {"productid": "PRODUCT_TYPE"}}
"""

INDIVIDUAL_SCHEDULE_INSTRUCTION = """
Collect flight schedule information from the user.
You need: direction, airport_id, travel_date, flight_id, and ticket information (adult/child counts).

Return JSON with: {"message": "your response", "done": true/false, "collected": {"A": data, "D": data}}
"""

BUNDLE_INSTRUCTION = lambda direction: f"""
Collect {direction} flight schedule information.
You need: direction, airport_id, travel_date, flight_id, and ticket information.

Return JSON with: {"message": "your response", "done": true/false, "collected": {{"A": data, "D": data}}}
"""

CONTACT_INFO_INSTRUCTION = """
Collect contact information from the user:
- Title (Mr./Ms./Mrs.)
- First name
- Last name  
- Email address
- Phone number

Return JSON with: {"message": "your response", "done": true/false, "contact": {"title": "", "firstname": "", "lastname": "", "email": "", "phone": ""}}
"""

async def classify_node(state: State):
    """Classify user intent"""
    global memory
    
    prompt = message_obj("system", f"{AGENT_INTRO}\n{CLASSIFY_INSTRUCTION}")
    user_message = message_obj("user", state["input"])
    memory.append(user_message)
    
    messages = [
        SystemMessage(content=prompt["content"]),
        HumanMessage(content=user_message["content"])
    ]
    
    response = await llm.ainvoke(messages)
    print(f"Classification response: {response.content}")
    
    flow = response.content.lower().strip()
    if "booking" in flow:
        flow_type = FlowType.BOOKING
    else:
        flow_type = FlowType.GENERAL
    
    return {"flow": flow_type}

async def answer_general_node(state: State):
    """Handle general questions"""
    global memory
    
    messages = [HumanMessage(content=msg["content"]) for msg in memory]
    response = await llm.ainvoke(messages)
    
    assistant_message = message_obj("assistant", response.content)
    memory.append(assistant_message)
    
    print(f"General answer: {response.content}")
    return {}

async def product_type_node(state: State):
    """Collect product type information"""
    global memory, current_node
    
    current_node = "start_booking"
    
    prompt = f"{AGENT_INTRO}\n{PRODUCT_TYPE_INSTRUCTION}"
    user_message = message_obj("user", state["input"])
    memory.append(user_message)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_message["content"])
    ]
    
    response = await llm.ainvoke(messages)
    parsed = json_parser(response.content)
    
    if not parsed.get("done"):
        # In Python LangGraph, we handle interrupts differently
        # Return state with interrupt signal
        return {
            "current_node": "start_booking",
            "messages": [{"role": "assistant", "content": parsed["message"]}]
        }
    
    return {
        "done": parsed["done"],
        "product_id": ProductType(parsed["collected"]["productid"]),
        "current_node": "start_booking"
    }

async def info_collector_node(state: State):
    """Collect schedule information"""
    global memory, current_node
    
    current_node = "schedule_info"
    is_bundle = state.get("product_id") == ProductType.ARRIVALBUNDLE
    
    current_direction = None
    if is_bundle:
        if not state["collected"].get("A"):
            current_direction = "ARRIVAL"
        elif not state["collected"].get("D"):
            current_direction = "DEPARTURE"
    
    if is_bundle and current_direction:
        prompt = f"{AGENT_INTRO}\n{BUNDLE_INSTRUCTION(current_direction)}"
    else:
        prompt = f"{AGENT_INTRO}\n{INDIVIDUAL_SCHEDULE_INSTRUCTION}"
    
    user_message = message_obj("user", state["input"])
    memory.append(user_message)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_message["content"])
    ]
    
    response = await llm.ainvoke(messages)
    parsed = json_parser(response.content)
    
    memory.append(message_obj("assistant", parsed["message"]))
    
    if not parsed.get("done"):
        return {
            "current_node": "schedule_info",
            "messages": [{"role": "assistant", "content": parsed["message"]}]
        }
    
    # Update collected data
    updated_collected = {**state["collected"]}
    if parsed["collected"].get("A"):
        updated_collected["A"] = parsed["collected"]["A"]
    if parsed["collected"].get("D"):
        updated_collected["D"] = parsed["collected"]["D"]
    
    # Check if bundle is complete
    done = parsed["done"]
    if is_bundle:
        done = bool(updated_collected.get("A")) and bool(updated_collected.get("D"))
    
    return {
        "done": done,
        "collected": updated_collected,
        "current_node": "schedule_info"
    }

async def schedule_step_node(state: State):
    """Get schedule data from API"""
    response_handler = {"A": None, "D": None}
    
    if (state["product_id"] in [ProductType.ARRIVALONLY, ProductType.ARRIVALBUNDLE] 
        and state["collected"].get("A")):
        response_handler["A"] = await get_schedule(state["collected"]["A"])
    
    if (state["product_id"] in [ProductType.DEPARTURE, ProductType.ARRIVALBUNDLE] 
        and state["collected"].get("D")):
        response_handler["D"] = await get_schedule(state["collected"]["D"])
    
    return {
        "done": True,
        "schedule_data": response_handler,
        "current_node": "schedule_call"
    }

async def reserve_step_node(state: State):
    """Reserve tickets"""
    print(f"Reserve step state: {state}")
    
    direction = "A" if state["product_id"] == ProductType.ARRIVALONLY else "D"
    
    response = await reserve_cart({
        "childtickets": state["collected"][direction]["tickets"]["childtickets"],
        "adulttickets": state["collected"][direction]["tickets"]["adulttickets"],
        "schedule_data": state["schedule_data"],
        "product_id": state["product_id"]
    })
    
    print(f"Reserve response: {response}")
    return {
        "reservation_data": response,
        "current_node": "reservation"
    }

async def contact_handler_node(state: State):
    """Collect contact information"""
    global memory, current_node
    
    current_node = "contact_info"
    
    user_message = message_obj("user", state["input"])
    memory.append(user_message)
    
    prompt = f"{AGENT_INTRO}\n{CONTACT_INFO_INSTRUCTION}"
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_message["content"])
    ]
    
    response = await llm.ainvoke(messages)
    parsed = json_parser(response.content)
    
    memory.append(message_obj("assistant", parsed["message"]))
    
    if not parsed.get("done"):
        return {
            "current_node": "contact_info",
            "messages": [{"role": "assistant", "content": parsed["message"]}]
        }
    
    return {
        "done": parsed["done"],
        "contact_info": parsed["contact"],
        "current_node": "contact_info"
    }

async def set_contact_step_node(state: State):
    """Set contact information via API"""
    response = await set_contact({
        **state["contact_info"],
        "reservation_data": state["reservation_data"]
    })
    
    print(f"Set contact response: {response}")
    return {}

async def product_success_node(state: State):
    """Final success message"""
    print("Congratulations! Your product is booked successfully!")
    return {}

async def payment_handler_node(state: State):
    """Handle payment processing"""
    # Placeholder for payment processing
    return {}

# API Functions
async def get_schedule(schedule_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get flight schedule from API"""
    request_data = {
        "username": os.getenv("STATIC_USERNAME"),
        "sessionid": os.getenv("STATIC_SESSIONID"),
        "failstatus": 0,
        "request": {
            "direction": schedule_info["direction"],
            "airportid": schedule_info["airportid"],
            "traveldate": schedule_info["traveldate"]
        }
    }
    
    try:
        response = requests.post(
            f"{os.getenv('DEVSERVER')}/getschedule",
            json=request_data
        )
        
        if response.status_code == 200:
            data = response.json()
            flight_schedule = data.get("data", {}).get("flightschedule", [])
            result = [
                flight for flight in flight_schedule 
                if flight.get("flightId") == schedule_info["flightId"]
            ]
            return result
        
    except Exception as e:
        print(f"Error in get_schedule: {e}")
    
    return {"message": "Error getting schedule"}

async def reserve_cart(reservation_info: Dict[str, Any]) -> Dict[str, Any]:
    """Reserve cart items via API"""
    schedule_builder = {
        "arrivalscheduleid": 0,
        "departurescheduleid": 0
    }
    
    if reservation_info["product_id"] in [ProductType.ARRIVALONLY, ProductType.ARRIVALBUNDLE]:
        schedule_builder["arrivalscheduleid"] = reservation_info["schedule_data"]["A"][0]["scheduleId"]
    
    if reservation_info["product_id"] in [ProductType.DEPARTURE, ProductType.ARRIVALBUNDLE]:
        schedule_builder["departurescheduleid"] = reservation_info["schedule_data"]["D"][0]["scheduleId"]
    
    request_data = {
        "failstatus": 0,
        "sessionid": os.getenv("STATIC_SESSIONID"),
        "username": os.getenv("STATIC_USERNAME"),
        "request": {
            "adulttickets": reservation_info["adulttickets"],
            "arrivalscheduleid": schedule_builder["arrivalscheduleid"],
            "cartitemid": 0,
            "childtickets": reservation_info["childtickets"],
            "departurescheduleid": schedule_builder["departurescheduleid"],
            "distributorid": "",
            "paymenttype": "GUESTCARD",
            "productid": reservation_info["product_id"],
            "ticketsrequested": reservation_info["adulttickets"] + reservation_info["childtickets"]
        }
    }
    
    try:
        response = requests.post(
            f"{os.getenv('DEVSERVER')}/reservecartitem",
            json=request_data
        )
        
        if response.status_code == 200:
            return response.json().get("data")
    
    except Exception as e:
        print(f"Error in reserve_cart: {e}")
    
    return "Error reserving cart"

async def set_contact(contact_info: Dict[str, Any]) -> str:
    """Set contact information via API"""
    request_data = {
        "failstatus": 0,
        "request": {
            "contact": {
                "cartitemid": contact_info["reservation_data"]["cartitemid"],
                "email": contact_info["email"],
                "firstname": contact_info["firstname"],
                "lastname": contact_info["lastname"],
                "phone": contact_info["phone"],
                "title": contact_info.get("title", "MR.")
            }
        },
        "sessionid": os.getenv("STATIC_SESSIONID"),
        "username": os.getenv("STATIC_USERNAME")
    }
    
    try:
        response = requests.post(
            f"{os.getenv('DEVSERVER')}/setcontact",
            json=request_data
        )
        
        if response.status_code == 200:
            return "Your primary contacts are submitted"
    
    except Exception as e:
        print(f"Error in set_contact: {e}")
    
    return "Error setting contact information"

# Graph Construction
def create_graph():
    """Create and configure the state graph"""
    
    # Create the graph
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("classify", classify_node)
    graph.add_node("general", answer_general_node)
    graph.add_node("start_booking", product_type_node)
    graph.add_node("schedule_call", schedule_step_node)
    graph.add_node("reservation", reserve_step_node)
    graph.add_node("schedule_info", info_collector_node)
    graph.add_node("contact_info", contact_handler_node)
    graph.add_node("set_contact", set_contact_step_node)
    graph.add_node("product_end", product_success_node)
    graph.add_node("payment_handler", payment_handler_node)
    
    # Add conditional edges
    graph.add_conditional_edges(
        START,
        lambda state: state.get("current_node", "classify")
    )
    
    graph.add_conditional_edges(
        "classify",
        lambda state: "start_booking" if state.get("flow") == FlowType.BOOKING else "general"
    )
    
    graph.add_conditional_edges(
        "start_booking",
        lambda state: "schedule_info" if state.get("done") else "start_booking"
    )
    
    graph.add_conditional_edges(
        "schedule_info",
        lambda state: "schedule_call" if state.get("done") else "schedule_info"
    )
    
    graph.add_conditional_edges(
        "contact_info",
        lambda state: "set_contact" if state.get("done") else "contact_info"
    )
    
    graph.add_conditional_edges(
        "payment_handler",
        lambda state: "product_end" if state.get("done") else "payment_handler"
    )
    
    # Add regular edges
    graph.add_edge("general", END)
    graph.add_edge("schedule_call", "reservation")
    graph.add_edge("reservation", "contact_info")
    graph.add_edge("set_contact", "payment_handler")
    graph.add_edge("product_end", END)
    
    # Compile the graph
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# Main execution
async def run_conversation(user_input: str, compiled_graph, previous_state: Optional[State] = None):
    """Run a conversation turn"""
    config = {"configurable": {"thread_id": "booking-session"}}
    
    init_state = {
        "input": user_input,
        "flow": None,
        "done": False,
        "current_node": None,
        "collected": {"A": None, "D": None},
        "schedule_data": {"A": None, "D": None},
        "product_id": None,
        "contact_info": None,
        "reservation_data": None,
        "messages": []
    }
    
    if previous_state:
        init_state.update(previous_state)
        init_state["input"] = user_input
    
    try:
        result = await compiled_graph.ainvoke(init_state, config)
        
        # Handle interrupts (human-in-the-loop)
        if result.get("messages"):
            for msg in result["messages"]:
                if msg["role"] == "assistant":
                    print(f"🧠 {msg['content']}")
                    # In a real implementation, you'd wait for user input here
                    # For now, we'll just return the state for the next iteration
                    return result
        
        print(f"🎯 Final State: {result}")
        return result
        
    except Exception as e:
        print(f"Error in conversation: {e}")
        return init_state

async def main():
    """Main conversation loop"""
    compiled_graph = create_graph()
    current_state = None
    
    print("🤖 Booking Assistant started! Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'exit':
                print("👋 Exiting...")
                break
            
            if user_input:
                current_state = await run_conversation(user_input, compiled_graph, current_state)
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
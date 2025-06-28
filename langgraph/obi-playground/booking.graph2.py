# main.py
import asyncio
from booking_system.agent import BookingAgent
from booking_system.config import load_config

async def main():
    """Main entry point"""
    config = load_config()
    agent = BookingAgent(config)
    
    print("🛒 Multi-Product Booking System started!")
    print("Commands: 'cart' to view cart, 'checkout' to proceed to payment, 'exit' to quit")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'cart':
                await agent.show_cart()
                continue
            elif user_input.lower() == 'checkout':
                await agent.checkout()
                continue
            
            if user_input:
                await agent.process_message(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

# booking_system/__init__.py
"""Modular Booking System with Cart Functionality"""

# booking_system/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    """System configuration"""
    openai_api_key: str
    static_username: str
    static_session_id: str
    dev_server: str
    model_name: str = "gpt-4o"

def load_config() -> Config:
    """Load configuration from environment"""
    load_dotenv()
    
    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        static_username=os.getenv("STATIC_USERNAME"),
        static_session_id=os.getenv("STATIC_SESSIONID"),
        dev_server=os.getenv("DEVSERVER"),
    )

# booking_system/models.py
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

class ProductType(str, Enum):
    ARRIVALONLY = "ARRIVALONLY"
    DEPARTURE = "DEPARTURE"
    ARRIVALBUNDLE = "ARRIVALBUNDLE"

class FlowType(str, Enum):
    BOOKING = "booking"
    GENERAL = "general"
    CART_MANAGEMENT = "cart"

class BookingStatus(str, Enum):
    COLLECTING_PRODUCT = "collecting_product"
    COLLECTING_SCHEDULE = "collecting_schedule"
    READY_FOR_CART = "ready_for_cart"
    IN_CART = "in_cart"
    RESERVED = "reserved"
    COMPLETED = "completed"

@dataclass
class TicketInfo:
    adult_tickets: int = 0
    child_tickets: int = 0
    
    @property
    def total_tickets(self) -> int:
        return self.adult_tickets + self.child_tickets

@dataclass
class FlightInfo:
    direction: str
    airport_id: str
    travel_date: str
    flight_id: str
    tickets: TicketInfo = field(default_factory=TicketInfo)

@dataclass
class ContactInfo:
    title: str = ""
    firstname: str = ""
    lastname: str = ""
    email: str = ""
    phone: str = ""
    
    @property
    def is_complete(self) -> bool:
        return all([self.firstname, self.lastname, self.email, self.phone])

@dataclass
class CartItem:
    id: str
    product_type: ProductType
    arrival_info: Optional[FlightInfo] = None
    departure_info: Optional[FlightInfo] = None
    schedule_data: Optional[Dict] = None
    reservation_data: Optional[Dict] = None
    status: BookingStatus = BookingStatus.COLLECTING_PRODUCT
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_ready_for_reservation(self) -> bool:
        return self.status == BookingStatus.READY_FOR_CART and self.schedule_data
    
    @property
    def total_tickets(self) -> int:
        total = 0
        if self.arrival_info:
            total += self.arrival_info.tickets.total_tickets
        if self.departure_info:
            total += self.departure_info.tickets.total_tickets
        return total

class AgentState(TypedDict):
    """Simplified agent state"""
    input: str
    flow: Optional[FlowType]
    current_item_id: Optional[str]  # ID of item being worked on
    cart_items: List[CartItem]
    contact_info: Optional[ContactInfo]
    conversation_context: List[Dict[str, str]]
    needs_input: bool
    assistant_message: Optional[str]

# booking_system/services.py
import requests
from typing import Dict, Any, List, Optional
from .models import FlightInfo, CartItem, ProductType
from .config import Config

class APIService:
    """Handle all external API calls"""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def get_schedule(self, flight_info: FlightInfo) -> List[Dict[str, Any]]:
        """Get flight schedule from API"""
        request_data = {
            "username": self.config.static_username,
            "sessionid": self.config.static_session_id,
            "failstatus": 0,
            "request": {
                "direction": flight_info.direction,
                "airportid": flight_info.airport_id,
                "traveldate": flight_info.travel_date
            }
        }
        
        try:
            response = requests.post(
                f"{self.config.dev_server}/getschedule",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                flight_schedule = data.get("data", {}).get("flightschedule", [])
                return [
                    flight for flight in flight_schedule 
                    if flight.get("flightId") == flight_info.flight_id
                ]
        except Exception as e:
            print(f"❌ Schedule API error: {e}")
        
        return []
    
    async def reserve_cart_items(self, cart_items: List[CartItem]) -> List[Dict[str, Any]]:
        """Reserve multiple cart items"""
        results = []
        
        for item in cart_items:
            if item.is_ready_for_reservation:
                result = await self._reserve_single_item(item)
                results.append({"item_id": item.id, "result": result})
        
        return results
    
    async def _reserve_single_item(self, item: CartItem) -> Dict[str, Any]:
        """Reserve a single cart item"""
        schedule_builder = {"arrivalscheduleid": 0, "departurescheduleid": 0}
        total_adult = 0
        total_child = 0
        
        # Build schedule IDs and ticket counts
        if item.product_type in [ProductType.ARRIVALONLY, ProductType.ARRIVALBUNDLE]:
            if item.schedule_data and item.schedule_data.get("A"):
                schedule_builder["arrivalscheduleid"] = item.schedule_data["A"][0]["scheduleId"]
                if item.arrival_info:
                    total_adult += item.arrival_info.tickets.adult_tickets
                    total_child += item.arrival_info.tickets.child_tickets
        
        if item.product_type in [ProductType.DEPARTURE, ProductType.ARRIVALBUNDLE]:
            if item.schedule_data and item.schedule_data.get("D"):
                schedule_builder["departurescheduleid"] = item.schedule_data["D"][0]["scheduleId"]
                if item.departure_info:
                    total_adult += item.departure_info.tickets.adult_tickets
                    total_child += item.departure_info.tickets.child_tickets
        
        request_data = {
            "failstatus": 0,
            "sessionid": self.config.static_session_id,
            "username": self.config.static_username,
            "request": {
                "adulttickets": total_adult,
                "arrivalscheduleid": schedule_builder["arrivalscheduleid"],
                "cartitemid": 0,
                "childtickets": total_child,
                "departurescheduleid": schedule_builder["departurescheduleid"],
                "distributorid": "",
                "paymenttype": "GUESTCARD",
                "productid": item.product_type.value,
                "ticketsrequested": total_adult + total_child
            }
        }
        
        try:
            response = requests.post(
                f"{self.config.dev_server}/reservecartitem",
                json=request_data
            )
            
            if response.status_code == 200:
                return response.json().get("data", {})
                
        except Exception as e:
            print(f"❌ Reservation API error: {e}")
        
        return {"error": "Failed to reserve item"}
    
    async def set_contact(self, contact_info, reservation_data) -> str:
        """Set contact information"""
        request_data = {
            "failstatus": 0,
            "request": {
                "contact": {
                    "cartitemid": reservation_data.get("cartitemid", 0),
                    "email": contact_info.email,
                    "firstname": contact_info.firstname,
                    "lastname": contact_info.lastname,
                    "phone": contact_info.phone,
                    "title": contact_info.title or "MR."
                }
            },
            "sessionid": self.config.static_session_id,
            "username": self.config.static_username
        }
        
        try:
            response = requests.post(
                f"{self.config.dev_server}/setcontact",
                json=request_data
            )
            
            if response.status_code == 200:
                return "✅ Contact information submitted successfully"
                
        except Exception as e:
            print(f"❌ Contact API error: {e}")
        
        return "❌ Failed to set contact information"

class CartService:
    """Manage cart operations"""
    
    def __init__(self):
        self.items: List[CartItem] = []
    
    def add_item(self, item: CartItem) -> str:
        """Add item to cart"""
        self.items.append(item)
        return item.id
    
    def get_item(self, item_id: str) -> Optional[CartItem]:
        """Get item by ID"""
        return next((item for item in self.items if item.id == item_id), None)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from cart"""
        initial_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        return len(self.items) < initial_count
    
    def get_ready_items(self) -> List[CartItem]:
        """Get items ready for reservation"""
        return [item for item in self.items if item.is_ready_for_reservation]
    
    def get_total_tickets(self) -> int:
        """Get total tickets across all items"""
        return sum(item.total_tickets for item in self.items)
    
    def clear_cart(self) -> None:
        """Clear all items from cart"""
        self.items.clear()
    
    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

# booking_system/processors.py
import json
from typing import Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .models import ProductType, FlightInfo, TicketInfo, ContactInfo, CartItem, BookingStatus
from .config import Config
import uuid

class InputProcessor:
    """Unified input processor for all booking needs"""
    
    def __init__(self, config: Config):
        self.llm = ChatOpenAI(
            api_key=config.openai_api_key,
            model=config.model_name
        )
    
    async def process_booking_input(self, user_input: str, current_item: Optional[CartItem] = None) -> Tuple[CartItem, bool]:
        """Process booking input and return updated cart item and completion status"""
        
        if not current_item:
            current_item = CartItem(
                id=str(uuid.uuid4()),
                product_type=ProductType.ARRIVALONLY,  # Default, will be updated
                status=BookingStatus.COLLECTING_PRODUCT
            )
        
        # Determine what information we need to collect
        prompt = self._build_collection_prompt(current_item)
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user_input)
        ]
        
        response = await self.llm.ainvoke(messages)
        parsed_data = self._parse_json_response(response.content)
        
        # Update cart item based on response
        updated_item = self._update_cart_item(current_item, parsed_data)
        is_complete = self._is_collection_complete(updated_item)
        
        return updated_item, is_complete
    
    async def process_contact_input(self, user_input: str, current_contact: Optional[ContactInfo] = None) -> Tuple[ContactInfo, bool]:
        """Process contact information input"""
        
        if not current_contact:
            current_contact = ContactInfo()
        
        prompt = f"""
        You are collecting contact information. Current info: {current_contact.__dict__}
        
        Collect the missing information:
        - Title (Mr./Ms./Mrs.)
        - First name
        - Last name
        - Email address
        - Phone number
        
        Return JSON with:
        {{
            "message": "your response to user",
            "contact": {{"title": "", "firstname": "", "lastname": "", "email": "", "phone": ""}},
            "done": true/false
        }}
        """
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user_input)
        ]
        
        response = await self.llm.ainvoke(messages)
        parsed_data = self._parse_json_response(response.content)
        
        # Update contact info
        if parsed_data.get("contact"):
            for key, value in parsed_data["contact"].items():
                if value and hasattr(current_contact, key):
                    setattr(current_contact, key, value)
        
        return current_contact, parsed_data.get("done", False)
    
    def _build_collection_prompt(self, item: CartItem) -> str:
        """Build prompt based on what information is missing"""
        
        base_prompt = """You are a booking assistant collecting flight information step by step."""
        
        if item.status == BookingStatus.COLLECTING_PRODUCT:
            return f"""{base_prompt}
            
            First, determine the product type:
            - ARRIVALONLY: Only arrival service
            - DEPARTURE: Only departure service  
            - ARRIVALBUNDLE: Both arrival and departure services
            
            Return JSON: {{"message": "response", "product_type": "TYPE", "done": true/false}}
            """
        
        elif item.status == BookingStatus.COLLECTING_SCHEDULE:
            missing_info = []
            
            if item.product_type in [ProductType.ARRIVALONLY, ProductType.ARRIVALBUNDLE] and not item.arrival_info:
                missing_info.append("ARRIVAL")
            
            if item.product_type in [ProductType.DEPARTURE, ProductType.ARRIVALBUNDLE] and not item.departure_info:
                missing_info.append("DEPARTURE")
            
            current_collecting = missing_info[0] if missing_info else "NONE"
            
            return f"""{base_prompt}
            
            Collecting {current_collecting} flight information:
            - Direction: {current_collecting}
            - Airport ID
            - Travel date (YYYY-MM-DD)
            - Flight ID
            - Number of adult tickets
            - Number of child tickets
            
            Return JSON:
            {{
                "message": "response",
                "flight_info": {{
                    "direction": "{current_collecting}",
                    "airport_id": "",
                    "travel_date": "",
                    "flight_id": "",
                    "adult_tickets": 0,
                    "child_tickets": 0
                }},
                "done": true/false
            }}
            """
        
        return f"{base_prompt}\nReturn JSON: {{\"message\": \"response\", \"done\": true}}"
    
    def _update_cart_item(self, item: CartItem, parsed_data: Dict[str, Any]) -> CartItem:
        """Update cart item with parsed data"""
        
        # Update product type
        if parsed_data.get("product_type"):
            item.product_type = ProductType(parsed_data["product_type"])
            item.status = BookingStatus.COLLECTING_SCHEDULE
        
        # Update flight information
        if parsed_data.get("flight_info"):
            flight_data = parsed_data["flight_info"]
            direction = flight_data.get("direction", "").upper()
            
            flight_info = FlightInfo(
                direction=direction,
                airport_id=flight_data.get("airport_id", ""),
                travel_date=flight_data.get("travel_date", ""),
                flight_id=flight_data.get("flight_id", ""),
                tickets=TicketInfo(
                    adult_tickets=int(flight_data.get("adult_tickets", 0)),
                    child_tickets=int(flight_data.get("child_tickets", 0))
                )
            )
            
            if direction == "ARRIVAL":
                item.arrival_info = flight_info
            elif direction == "DEPARTURE":
                item.departure_info = flight_info
        
        return item
    
    def _is_collection_complete(self, item: CartItem) -> bool:
        """Check if all required information is collected"""
        
        if item.status == BookingStatus.COLLECTING_PRODUCT:
            return False
        
        # Check if all required flight info is collected
        needs_arrival = item.product_type in [ProductType.ARRIVALONLY, ProductType.ARRIVALBUNDLE]
        needs_departure = item.product_type in [ProductType.DEPARTURE, ProductType.ARRIVALBUNDLE]
        
        has_arrival = item.arrival_info is not None
        has_departure = item.departure_info is not None
        
        if needs_arrival and not has_arrival:
            return False
        
        if needs_departure and not has_departure:
            return False
        
        # All required info collected
        item.status = BookingStatus.READY_FOR_CART
        return True
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
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
            return {
                "message": content,
                "done": False
            }

# booking_system/agent.py
from typing import Optional
from .models import AgentState, CartItem, ContactInfo, FlowType, BookingStatus
from .services import APIService, CartService
from .processors import InputProcessor
from .config import Config
import uuid

class BookingAgent:
    """Main booking agent orchestrator"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_service = APIService(config)
        self.cart_service = CartService()
        self.input_processor = InputProcessor(config)
        
        self.state = AgentState(
            input="",
            flow=None,
            current_item_id=None,
            cart_items=[],
            contact_info=None,
            conversation_context=[],
            needs_input=False,
            assistant_message=None
        )
    
    async def process_message(self, user_input: str):
        """Process user message and route to appropriate handler"""
        self.state["input"] = user_input
        
        # Determine flow if not set
        if not self.state.get("flow"):
            self.state["flow"] = await self._classify_intent(user_input)
        
        if self.state["flow"] == FlowType.BOOKING:
            await self._handle_booking_flow()
        elif self.state["flow"] == FlowType.GENERAL:
            await self._handle_general_query()
    
    async def _handle_booking_flow(self):
        """Handle booking-related interactions"""
        # Get or create current item
        current_item = None
        if self.state["current_item_id"]:
            current_item = self.cart_service.get_item(self.state["current_item_id"])
        
        # Process booking input
        updated_item, is_complete = await self.input_processor.process_booking_input(
            self.state["input"], current_item
        )
        
        # Update cart
        if not current_item:
            item_id = self.cart_service.add_item(updated_item)
            self.state["current_item_id"] = item_id
            print(f"🛒 Started new booking: {updated_item.product_type.value}")
        
        if is_complete:
            # Get schedule data
            await self._fetch_schedule_data(updated_item)
            
            print(f"✅ Booking ready! Added to cart: {updated_item.product_type.value}")
            print("💡 Say 'add another' to add more items, or 'checkout' to proceed to payment")
            
            # Reset for next item
            self.state["current_item_id"] = None
            self.state["flow"] = None
        else:
            print("📝 Please provide the missing information...")
    
    async def _fetch_schedule_data(self, item: CartItem):
        """Fetch schedule data for cart item"""
        schedule_data = {}
        
        if item.arrival_info:
            arrival_schedule = await self.api_service.get_schedule(item.arrival_info)
            schedule_data["A"] = arrival_schedule
        
        if item.departure_info:
            departure_schedule = await self.api_service.get_schedule(item.departure_info)
            schedule_data["D"] = departure_schedule
        
        item.schedule_data = schedule_data
        item.status = BookingStatus.READY_FOR_CART
    
    async def show_cart(self):
        """Display current cart contents"""
        if self.cart_service.is_empty:
            print("🛒 Your cart is empty")
            return
        
        print(f"\n🛒 Cart Contents ({len(self.cart_service.items)} items):")
        print("-" * 50)
        
        for i, item in enumerate(self.cart_service.items, 1):
            print(f"{i}. {item.product_type.value} - Status: {item.status.value}")
            if item.arrival_info:
                print(f"   ✈️ Arrival: {item.arrival_info.flight_id} ({item.arrival_info.tickets.total_tickets} tickets)")
            if item.departure_info:
                print(f"   🛫 Departure: {item.departure_info.flight_id} ({item.departure_info.tickets.total_tickets} tickets)")
        
        print(f"\n📊 Total tickets: {self.cart_service.get_total_tickets()}")
        print("💡 Type 'checkout' to proceed or continue adding items")
    
    async def checkout(self):
        """Process checkout for all cart items"""
        if self.cart_service.is_empty:
            print("🛒 Your cart is empty! Add some items first.")
            return
        
        ready_items = self.cart_service.get_ready_items()
        if not ready_items:
            print("❌ No items ready for checkout. Please complete your bookings first.")
            return
        
        print(f"🔄 Processing checkout for {len(ready_items)} items...")
        
        # Collect contact info if not provided
        if not self.state["contact_info"] or not self.state["contact_info"].is_complete:
            await self._collect_contact_info()
        
        # Reserve all items
        print("📋 Reserving your bookings...")
        reservation_results = await self.api_service.reserve_cart_items(ready_items)
        
        # Update items with reservation data
        for result in reservation_results:
            item = self.cart_service.get_item(result["item_id"])
            if item:
                item.reservation_data = result["result"]
                item.status = BookingStatus.RESERVED
        
        # Set contact info for all reservations
        for item in ready_items:
            if item.reservation_data:
                await self.api_service.set_contact(self.state["contact_info"], item.reservation_data)
        
        print("✅ Checkout completed successfully!")
        print(f"🎉 {len(ready_items)} items booked and reserved!")
        
        # Clear cart
        self.cart_service.clear_cart()
        self.state["contact_info"] = None
    
    async def _collect_contact_info(self):
        """Collect contact information"""
        print("📞 We need your contact information to complete the booking...")
        
        contact_info = self.state.get("contact_info") or ContactInfo()
        
        while not contact_info.is_complete:
            contact_input = input("Contact info: ").strip()
            contact_info, is_complete = await self.input_processor.process_contact_input(
                contact_input, contact_info
            )
            
            if not is_complete:
                print("📝 Please provide the missing contact details...")
        
        self.state["contact_info"] = contact_info
        print("✅ Contact information collected!")
    
    async def _classify_intent(self, user_input: str) -> FlowType:
        """Classify user intent"""
        booking_keywords = ["book", "booking", "flight", "arrival", "departure", "ticket", "reserve"]
        
        if any(keyword in user_input.lower() for keyword in booking_keywords):
            return FlowType.BOOKING
        
        return FlowType.GENERAL
    
    async def _handle_general_query(self):
        """Handle general queries"""
        print("🤖 I'm here to help you book flights! Say 'book a flight' to get started.")
        self.state["flow"] = None
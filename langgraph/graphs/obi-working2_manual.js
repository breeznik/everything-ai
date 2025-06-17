// loungeBookingLangGraph.js
import { ChatOpenAI } from "@langchain/openai";
import dotenv from "dotenv";
import { StateGraph, START, END } from "@langchain/langgraph";
import { tool } from "@langchain/core/tools";
import z from "zod";
import readline from "readline";

dotenv.config();

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Utility function to ask questions
const askQuestion = (question) => {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
};

// --- Sample Tools (Mock Logic) ---
const sampleScheduleCall = async (input) => {
  console.log("🔧 Calling sampleScheduleCall with:", input);
  return {
    availableSlots: ["10:00 AM", "2:00 PM", "6:00 PM"],
    status: "ok",
  };
};

const sampleReserveCart = async (input) => {
  console.log("🔧 Calling sampleReserveCart with:", input);
  return {
    reservationId: "RES12345",
    status: "reserved",
  };
};

const sampleSetContact = async (input) => {
  console.log("🔧 Calling sampleSetContact with:", input);
  return { contactSaved: true };
};

const samplePayment = async (input) => {
  console.log("🔧 Calling samplePayment with:", input);
  return {
    paymentStatus: "success",
    transactionId: "TXN98765",
  };
};

// --- LLM Setup ---
const llm = new ChatOpenAI({
  openAIApiKey: process.env.OPENAI_API_KEY,
  modelName: "gpt-4o",
});

// --- Tool Wrappers ---
const scheduleTool = tool(sampleScheduleCall, {
  name: "scheduleCall",
  description: "Get available lounge slots",
  schema: z.object({
    airportid: z.enum(["NMIA", "SIA"]),
    direction: z.enum(["A", "D"]),
    travelDate: z.string(),
    flightId: z.string(),
  }),
});

const reserveTool = tool(sampleReserveCart, {
  name: "reserveLounge",
  description: "Reserve the lounge",
  schema: z.object({
    adulttickets: z.number(),
    childtickets: z.number(),
    productid: z.string(),
  }),
});

const contactTool = tool(sampleSetContact, {
  name: "setContactInfo",
  description: "Set contact details for reservation",
  schema: z.object({
    email: z.string().email(),
    firstname: z.string(),
    lastname: z.string(),
    phone: z.string(),
  }),
});

const paymentTool = tool(samplePayment, {
  name: "makePayment",
  description: "Process payment for lounge booking",
  schema: z.object({
    cardHolder: z.string(),
    cardNumber: z.string(),
    cardType: z.enum(["VISA", "MASTERCARD"]),
    cvv: z.string(),
    expiryDate: z.string(),
    email: z.string().email(),
  }),
});

// --- Interactive Node Functions ---
async function decideBooking(state) {
  console.log("\n🤖 === BOOKING DECISION ===");
  
  if (typeof state.shouldBook === "boolean") {
    console.log("✅ Decision already made:", state.shouldBook);
    return state;
  }
  
  if (!state.query) {
    const query = await askQuestion("What would you like to do today? ");
    state = { ...state, query };
  }
  
  console.log("🤔 Analyzing your request...");
  console.log(`📝 You said: "${state.query}"`);
  
  // Enhanced logic with explicit confirmation
  let shouldBook = state.query.toLowerCase().includes("book") || 
                   state.query.toLowerCase().includes("lounge") ||
                   state.query.toLowerCase().includes("reserve");
  
  // If not clearly a booking request, ask for clarification
  if (!shouldBook) {
    console.log("🤔 It seems you might want to book a lounge. Let me confirm...");
    const confirmation = await askQuestion("Would you like to book a lounge? (yes/no): ");
    shouldBook = confirmation.toLowerCase().startsWith('y');
  }
  
  if (shouldBook) {
    console.log("🎯 Decision: Proceed with booking");
  } else {
    console.log("👋 Decision: No booking needed. Have a great day!");
    return { ...state, shouldBook, finalOutput: "Thank you for visiting! No booking was made." };
  }
  
  return { ...state, shouldBook };
}

async function gatherSchedule(state) {
  console.log("\n🧑 === GATHER SCHEDULE INFORMATION ===");
  
  if (state.scheduleData) {
    console.log("✅ Schedule data already available");
    return state;
  }
  
  console.log("📋 I need some travel details to check lounge availability:");
  
  let airport, direction, travelDate, flightId;
  
  // Validate airport input
  do {
    airport = await askQuestion("Which airport? (NMIA/SIA): ");
    airport = airport.toUpperCase();
    if (!["NMIA", "SIA"].includes(airport)) {
      console.log("❌ Please enter either NMIA or SIA");
    }
  } while (!["NMIA", "SIA"].includes(airport));
  
  // Validate direction input
  do {
    direction = await askQuestion("Direction? (A for Arrival, D for Departure): ");
    direction = direction.toUpperCase();
    if (!["A", "D"].includes(direction)) {
      console.log("❌ Please enter either A (Arrival) or D (Departure)");
    }
  } while (!["A", "D"].includes(direction));
  
  // Get travel date with basic validation
  do {
    travelDate = await askQuestion("Travel date (YYYY-MM-DD): ");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(travelDate)) {
      console.log("❌ Please use YYYY-MM-DD format");
      travelDate = null;
    }
  } while (!travelDate);
  
  flightId = await askQuestion("Flight ID: ");
  
  const scheduleData = {
    airportid: airport,
    direction: direction,
    travelDate,
    flightId
  };
  
  console.log("✅ Schedule information collected:");
  console.log(`   - Airport: ${airport}`);
  console.log(`   - Direction: ${direction === 'A' ? 'Arrival' : 'Departure'}`);
  console.log(`   - Date: ${travelDate}`);
  console.log(`   - Flight: ${flightId}`);
  
  return { ...state, scheduleData };
}

async function scheduleCall(state) {
  console.log("\n📅 === CHECKING LOUNGE AVAILABILITY ===");
  
  try {
    console.log("🔍 Searching for available slots...");
    const result = await scheduleTool.invoke(state.scheduleData);
    
    console.log("✅ Available time slots:");
    result.availableSlots.forEach((slot, index) => {
      console.log(`   ${index + 1}. ${slot}`);
    });
    
    let choice;
    do {
      choice = await askQuestion("Which slot would you prefer? (1-3): ");
      const choiceNum = parseInt(choice);
      if (isNaN(choiceNum) || choiceNum < 1 || choiceNum > result.availableSlots.length) {
        console.log(`❌ Please enter a number between 1 and ${result.availableSlots.length}`);
        choice = null;
      }
    } while (!choice);
    
    const selectedSlot = result.availableSlots[parseInt(choice) - 1];
    
    console.log(`🎯 Selected slot: ${selectedSlot}`);
    
    return { ...state, availableSlots: result.availableSlots, selectedSlot };
  } catch (error) {
    console.error("❌ Error checking availability:", error);
    return { ...state, finalOutput: "Error checking availability. Please try again." };
  }
}

async function reserveLounge(state) {
  console.log("\n📦 === MAKING RESERVATION ===");
  
  try {
    let adults, children;
    
    do {
      adults = await askQuestion("Number of adult tickets (default 1): ") || "1";
      adults = parseInt(adults);
      if (isNaN(adults) || adults < 1) {
        console.log("❌ Please enter a valid number of adult tickets (minimum 1)");
        adults = null;
      }
    } while (!adults);
    
    do {
      children = await askQuestion("Number of child tickets (default 0): ") || "0";
      children = parseInt(children);
      if (isNaN(children) || children < 0) {
        console.log("❌ Please enter a valid number of child tickets (0 or more)");
        children = null;
      }
    } while (children === null);
    
    console.log("🔄 Processing reservation...");
    
    const result = await reserveTool.invoke({
      adulttickets: adults,
      childtickets: children,
      productid: "Lounge001",
    });
    
    console.log(`✅ Reservation confirmed! ID: ${result.reservationId}`);
    console.log(`   - Adult tickets: ${adults}`);
    console.log(`   - Child tickets: ${children}`);
    
    return { 
      ...state, 
      reservationId: result.reservationId,
      ticketDetails: { adults, children }
    };
  } catch (error) {
    console.error("❌ Error making reservation:", error);
    return { ...state, finalOutput: "Error making reservation. Please try again." };
  }
}

async function setContactInfo(state) {
  console.log("\n📞 === CONTACT INFORMATION ===");
  
  if (state.contactInfo) {
    console.log("✅ Contact information already available");
    return state;
  }
  
  console.log("📝 Please provide your contact details:");
  
  const firstname = await askQuestion("First name: ");
  const lastname = await askQuestion("Last name: ");
  
  let email;
  do {
    email = await askQuestion("Email: ");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      console.log("❌ Please enter a valid email address");
      email = null;
    }
  } while (!email);
  
  const phone = await askQuestion("Phone number: ");
  
  const contactInfo = { firstname, lastname, email, phone };
  
  try {
    await contactTool.invoke(contactInfo);
    console.log("✅ Contact information saved");
    console.log(`   - Name: ${firstname} ${lastname}`);
    console.log(`   - Email: ${email}`);
    console.log(`   - Phone: ${phone}`);
    return { ...state, contactInfo };
  } catch (error) {
    console.error("❌ Error saving contact info:", error);
    return { ...state, finalOutput: "Error saving contact information. Please try again." };
  }
}

async function makePayment(state) {
  console.log("\n💳 === PAYMENT PROCESSING ===");
  
  if (state.paymentResult) {
    console.log("✅ Payment already processed");
    return state;
  }
  
  console.log("💰 Payment required for lounge booking");
  console.log("📊 Booking Summary:");
  console.log(`   - Airport: ${state.scheduleData?.airportid}`);
  console.log(`   - Date: ${state.scheduleData?.travelDate}`);
  console.log(`   - Flight: ${state.scheduleData?.flightId}`);
  console.log(`   - Time Slot: ${state.selectedSlot}`);
  console.log(`   - Reservation ID: ${state.reservationId}`);
  console.log(`   - Adults: ${state.ticketDetails?.adults || 1}`);
  console.log(`   - Children: ${state.ticketDetails?.children || 0}`);
  
  const proceed = await askQuestion("Proceed with payment? (y/n): ");
  
  if (proceed.toLowerCase() !== 'y') {
    console.log("❌ Payment cancelled");
    return { ...state, finalOutput: "Booking cancelled by user" };
  }
  
  console.log("💳 Please provide payment details:");
  
  const cardHolder = await askQuestion("Card holder name: ");
  const cardNumber = await askQuestion("Card number: ");
  
  let cardType;
  do {
    cardType = await askQuestion("Card type (VISA/MASTERCARD): ");
    cardType = cardType.toUpperCase();
    if (!["VISA", "MASTERCARD"].includes(cardType)) {
      console.log("❌ Please enter either VISA or MASTERCARD");
      cardType = null;
    }
  } while (!cardType);
  
  const cvv = await askQuestion("CVV: ");
  const expiryDate = await askQuestion("Expiry date (MM/YY): ");
  
  const paymentData = {
    cardHolder,
    cardNumber,
    cardType,
    cvv,
    expiryDate,
    email: state.contactInfo?.email || ""
  };
  
  try {
    console.log("🔄 Processing payment...");
    const result = await paymentTool.invoke(paymentData);
    
    console.log("✅ Payment successful!");
    
    return {
      ...state,
      paymentResult: paymentData,
      finalOutput: `🎉 Booking complete! Transaction ID: ${result.transactionId}`
    };
  } catch (error) {
    console.error("❌ Payment failed:", error);
    return { ...state, finalOutput: "Payment processing failed" };
  }
}

// --- Graph Setup ---
const graph = new StateGraph({
  channels: {
    query: { 
      value: (x, y) => y ?? x,
      default: () => "",
    },
    shouldBook: {
      value: (x, y) => y ?? x,
      default: () => null, // Changed from false to null to ensure proper flow
    },
    scheduleData: {
      value: (x, y) => y ?? x,
      default: () => null,
    },
    availableSlots: {
      value: (x, y) => y ?? x,
      default: () => [],
    },
    selectedSlot: {
      value: (x, y) => y ?? x,
      default: () => "",
    },
    reservationId: {
      value: (x, y) => y ?? x,
      default: () => "",
    },
    ticketDetails: {
      value: (x, y) => y ?? x,
      default: () => null,
    },
    contactInfo: {
      value: (x, y) => y ?? x,
      default: () => null,
    },
    paymentResult: {
      value: (x, y) => y ?? x,
      default: () => null,
    },
    finalOutput: {
      value: (x, y) => y ?? x,
      default: () => "",
    },
  },
});

// Add nodes
graph.addNode("llmCall", decideBooking);
graph.addNode("gatherSchedule", gatherSchedule);
graph.addNode("scheduleCall", scheduleCall);
graph.addNode("reserveLounge", reserveLounge);
graph.addNode("setContactInfo", setContactInfo);
graph.addNode("makePayment", makePayment);

// Add edges
graph.addEdge(START, "llmCall");
graph.addConditionalEdges("llmCall", (state) => {
  console.log(`🔀 Routing decision: ${state.shouldBook ? "Continue booking" : "End session"}`);
  return state.shouldBook ? "gatherSchedule" : END;
});
graph.addEdge("gatherSchedule", "scheduleCall");
graph.addEdge("scheduleCall", "reserveLounge");
graph.addEdge("reserveLounge", "setContactInfo");
graph.addEdge("setContactInfo", "makePayment");
graph.addEdge("makePayment", END);

// Compile the graph
const bookingAgent = graph.compile();

// --- MAIN INTERACTIVE EXECUTION ---
async function runInteractiveBooking() {
  console.log("🏨 === WELCOME TO LOUNGE BOOKING SYSTEM ===");
  console.log("I'll help you book a lounge for your travel needs.\n");
  
  try {
    const result = await bookingAgent.invoke({});
    
    console.log("\n" + "=".repeat(50));
    console.log("🎯 SESSION COMPLETE");
    console.log("=".repeat(50));
    
    if (result.finalOutput) {
      console.log(result.finalOutput);
    }
    
    if (result.reservationId) {
      console.log(`📧 Confirmation email sent to: ${result.contactInfo?.email}`);
      console.log(`📱 SMS confirmation sent to: ${result.contactInfo?.phone}`);
    }
    
    console.log("\nThank you for using our lounge booking system! ✈️");
    
  } catch (error) {
    console.error("❌ Booking failed:", error);
  } finally {
    rl.close();
  }
}

// Start the interactive booking
runInteractiveBooking();

export { bookingAgent };
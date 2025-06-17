// loungeBookingLangGraph.js
import { ChatOpenAI } from "@langchain/openai";
import dotenv from "dotenv";
import { StateGraph, START, END } from "@langchain/langgraph";
import { tool } from "@langchain/core/tools";
import z from "zod";

dotenv.config();

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

// --- Node Functions ---
function decideBooking(state) {
  console.log("🤖 decideBooking received:", JSON.stringify(state, null, 2));
  
  // If shouldBook is already set, use it
  if (typeof state.shouldBook === "boolean") {
    console.log("✅ Skipping LLM decision, using provided value:", state.shouldBook);
    return state;
  }
  
  // If no query provided, default to not booking
  if (!state.query) {
    console.log("❗ No query provided, defaulting to not booking");
    return { ...state, shouldBook: false };
  }
  
  // For this demo, let's just return true if query contains "booking"
  const shouldBook = state.query.toLowerCase().includes("booking");
  console.log("🤖 decideBooking decision:", shouldBook);
  return { ...state, shouldBook };
}

function gatherSchedule(state) {
  console.log("🧑 gatherSchedule received:", JSON.stringify(state, null, 2));
  if (!state.scheduleData) {
    console.log("❗ Missing schedule data!");
    return state;
  }
  console.log("✅ Schedule data found");
  return state;
}

function scheduleCall(state) {
  console.log("📅 scheduleCall received:", JSON.stringify(state, null, 2));
  try {
    // Mock the tool call for now
    const result = {
      availableSlots: ["10:00 AM", "2:00 PM", "6:00 PM"],
      status: "ok",
    };
    console.log("📅 scheduleCall result:", result);
    return { ...state, availableSlots: result.availableSlots };
  } catch (error) {
    console.error("❌ Error in scheduleCall:", error);
    return state;
  }
}

function reserveLounge(state) {
  console.log("📦 reserveLounge received:", JSON.stringify(state, null, 2));
  try {
    // Mock the reservation
    const result = {
      reservationId: "RES12345",
      status: "reserved",
    };
    console.log("📦 reserveLounge result:", result);
    return { ...state, reservationId: result.reservationId };
  } catch (error) {
    console.error("❌ Error in reserveLounge:", error);
    return state;
  }
}

function setContactInfo(state) {
  console.log("📞 setContactInfo received:", JSON.stringify(state, null, 2));
  try {
    console.log("📞 Contact info set successfully");
    return state;
  } catch (error) {
    console.error("❌ Error in setContactInfo:", error);
    return state;
  }
}

function makePayment(state) {
  console.log("💳 makePayment received:", JSON.stringify(state, null, 2));
  try {
    const result = {
      paymentStatus: "success",
      transactionId: "TXN98765",
    };
    console.log("💳 makePayment result:", result);
    return {
      ...state,
      finalOutput: `Booking complete. Transaction ID: ${result.transactionId}`,
    };
  } catch (error) {
    console.error("❌ Error in makePayment:", error);
    return { ...state, finalOutput: "Payment failed" };
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
      default: () => false,
    },
    scheduleData: {
      value: (x, y) => y ?? x,
      default: () => null,
    },
    availableSlots: {
      value: (x, y) => y ?? x,
      default: () => [],
    },
    reservationId: {
      value: (x, y) => y ?? x,
      default: () => "",
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
  console.log("🔀 Conditional edge check - shouldBook:", state.shouldBook);
  return state.shouldBook ? "gatherSchedule" : END;
});
graph.addEdge("gatherSchedule", "scheduleCall");
graph.addEdge("scheduleCall", "reserveLounge");
graph.addEdge("reserveLounge", "setContactInfo");
graph.addEdge("setContactInfo", "makePayment");
graph.addEdge("makePayment", END);

// Compile the graph
const bookingAgent = graph.compile();

// --- MAIN EXECUTION ---
console.log("🚀 Starting booking agent...");

const initialState = {
  query: "I want a lounge booking",
  shouldBook: true,
  scheduleData: {
    airportid: "NMIA",
    direction: "D",
    travelDate: "2025-07-01",
    flightId: "AI202",
  },
  contactInfo: {
    email: "john@example.com",
    firstname: "John",
    lastname: "Doe",
    phone: "9876543210",
  },
  paymentResult: {
    cardHolder: "John Doe",
    cardNumber: "4111111111111111",
    cardType: "VISA",
    cvv: "123",
    expiryDate: "12/27",
    email: "john@example.com",
  },
};

console.log("📋 Initial state:", JSON.stringify(initialState, null, 2));

bookingAgent
  .invoke(initialState)
  .then((result) => {
    console.log("\n=== FINAL RESULTS ===");
    console.log("✅ Final Output:", result?.finalOutput);
    console.log("🔍 Full State:", JSON.stringify(result, null, 2));
    console.log("🎉 Booking agent completed successfully");
  })
  .catch((error) => {
    console.error("❌ Error running booking agent:", error);
    console.error("💥 Stack trace:", error.stack);
  });

export { bookingAgent };
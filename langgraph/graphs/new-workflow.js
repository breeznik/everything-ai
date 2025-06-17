import { ChatOpenAI } from "@langchain/openai";
import { StateGraph, END, START } from "@langchain/langgraph";
import { interrupt, Command } from "@langchain/langgraph";
import { z } from "zod";
import { MemorySaver } from "@langchain/langgraph";
import readline from "readline";
import dotenv from "dotenv";

dotenv.config();

// --- LLM Setup ---
const llm = new ChatOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  modelName: "gpt-4o",
});

// --- Define State Schema ---
const stateSchema = z.object({
  input: z.string(),
  flow: z.enum(["booking", "general"]).optional(),
  productType: z.string().optional(),
  direction: z.string().optional(),
  airportId: z.string().optional(),
  travelDate: z.string().optional(),
  flightId: z.string().optional(),
  ticketCount: z.string().optional(),
  scheduleFound: z.boolean().optional(),
  reservationConfirmed: z.boolean().optional(),
});

// --- Step: Classify booking or general ---
async function classify(state) {
  const res = await llm.invoke([
    { role: "system", content: "Classify this as 'booking' or 'general'." },
    { role: "user", content: state.input },
  ]);
  const flow = res.content.toLowerCase().includes("book")
    ? "booking"
    : "general";
  console.log("flow ouput : ", flow);
  return { flow };
}

// --- Step: Answer general query ---
async function answerGeneral(state) {
  const res = await llm.invoke([{ role: "user", content: state.input }]);
  console.log("💬 General Answer:", res.content);
  return {};
}

// --- Step: Ask missing booking info ---
// --- Step: LLM-driven smart info collection ---
async function collectInfo(state) {
  const res = await llm.invoke([
    {
      role: "system",
      content: `
You are an assistant helping to book a lounge. Extract the following fields from the user's message if available:

- productType (ARRIVAL, DEPARTURE, BUNDLE)
- direction (A or D)
- airportId (SIA, NMIA)
- travelDate (YYYYMMDD)
- flightId (e.g., AC920)
- ticketCount (e.g., "2 adult, 1 child")

you can fix the grammer or spelling mistake by user for the feild values.
confirm the values with user before channeling in the final json response.
when all the info is gethered Respond only with a JSON object including these keys.
      `.trim(),
    },
    {
      role: "user",
      content: state.input,
    },
  ]);

  let data = {};

  for (const key of [
    "productType",
    "direction",
    "airportId",
    "travelDate",
    "flightId",
    "ticketCount",
  ]) {
    if (!data[key]) {
      return {
        [key]: interrupt({ prompt: `Please enter ${key}` }),
      };
    }
  }

  return data;
}

// --- Step: Mock getSchedule API ---
async function getSchedule(state) {
  if (state.flightId?.startsWith("AC")) {
    return { scheduleFound: true };
  } else {
    return {
      scheduleFound: false,
      flightId: interrupt({
        prompt: "Schedule not found. Enter another flightId.",
      }),
    };
  }
}

// --- Step: Mock reserve API ---
async function reserve(state) {
  console.log("✅ Booking done for:", state.flightId);
  return { reservationConfirmed: true };
}

const G = new StateGraph({
  state: stateSchema, // ✅ Correct: Pass the full Zod schema
});

G.addNode("classify", classify);
G.addNode("general", answerGeneral);
G.addNode("startBooking", async () => ({}));
G.addNode("collectInfo", collectInfo);
G.addNode("getSchedule", getSchedule);
G.addNode("reserve", reserve);

G.addEdge(START, "classify");
G.addConditionalEdges("classify", (state) =>
  state.flow === "booking" ? "startBooking" : "general"
);
G.addEdge("general", END);
G.addEdge("startBooking", "collectInfo");
G.addEdge("collectInfo", "collectInfo"); // loops if info missing
G.addEdge("collectInfo", "getSchedule");
G.addConditionalEdges("getSchedule", (s) =>
  s.scheduleFound ? "reserve" : "getSchedule"
);
G.addEdge("reserve", END);

// --- Compile graph ---
const graph = G.compile({
  checkpointer: new MemorySaver(), // optional memory for resume
});

// --- Ask wrapper ---
async function ask(prompt) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) =>
    rl.question(`👉 ${prompt}: `, (answer) => {
      rl.close();
      resolve(answer);
    })
  );
}

// --- Run the chatbot ---
async function run(input) {
  const cfg = { configurable: { thread_id: "simple-thread" } };
  let state = await graph.invoke({ input }, cfg);

  while (state.__interrupt__) {
    const prompt = state.__interrupt__[0].value.prompt;
    const reply = await ask(prompt);
    state = await graph.invoke(new Command({ resume: reply }), cfg);
  }

  console.log("🎯 Final State:", state);
}

// --- Kickstart ---
run("i would like to book an lounge");

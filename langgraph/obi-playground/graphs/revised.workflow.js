import dotenv from "dotenv";
dotenv.config();
import { ChatOpenAI } from "@langchain/openai";
import {
  StateGraph,
  MessagesAnnotation,
  Command,
  START,
  END,
  interrupt,
} from "@langchain/langgraph";
import {
  agent_intro,
  classifyInstruction,
  productTypeInstruction,
  indiScheduleInstruction,
  bundleInstruction,
  contactInfoInstruction,
} from "./utils/instructions.js";
import { jsonParser } from "./utils/utils.js";

// ⛽ Setup
const model = new ChatOpenAI({ temperature: 0.3, modelName: "gpt-4o-mini" });

// 🧠 ROUTER NODE
const router = async (state) => {
  const prompt = `
${agent_intro}
Decide routing:
- booking → 'book_agent'
- general chat → 'general_agent'
Use output 'route: <agent_name>'.`;
  const res = await model.invoke([
    ...state.messages,
    { role: "system", content: prompt },
  ]);
  const match = res.content.match(/route:\s*(\w+)/i);
  const goto = match ? match[1] : "general_agent";
  return new Command({
    goto,
    update: { current_route: goto, messages: [...state.messages, res] },
  });
};

// 🧠 GENERAL CHAT NODE
const general_agent = async (state) => {
  const res = await model.invoke(state.messages);
  return new Command({
    goto: END,
    update: { messages: [...state.messages, res] },
  });
};

// 🧠 BOOKING ORCHESTRATOR NODE
const book_agent = async (state) => {
  if (!state.flow) {
    const res = await model.invoke([
      ...state.messages,
      { role: "system", content: productTypeInstruction },
    ]);
    const parsed = await jsonParser(res.content);
    if (!parsed.done) return interrupt({ prompt: parsed.message });
    return new Command({
      goto: "info_collector",
      update: {
        flow: "booking",
        productid: parsed.collected.productid,
        messages: [...state.messages, res],
        info_target: "A",
      },
    });
  }

  const isBundle = state.productid === "ARRIVALBUNDLE";
  const hasA = !!state.collected?.A;
  const hasD = !!state.collected?.D;

  if (isBundle && !hasA)
    return new Command({
      goto: "info_collector",
      update: { info_target: "A" },
    });
  if (isBundle && !hasD)
    return new Command({
      goto: "info_collector",
      update: { info_target: "D" },
    });
  if (!isBundle && !hasA)
    return new Command({
      goto: "info_collector",
      update: { info_target: "A" },
    });

  return new Command({ goto: "schedule_agent" });
};

// 🧠 MODULAR INFO COLLECTOR NODE
const info_collector = async (state) => {
  const direction = state.info_target;
  const isBundle = state.productid === "ARRIVALBUNDLE";
  const instruction = isBundle
    ? bundleInstruction(direction)
    : indiScheduleInstruction;

  const res = await model.invoke([
    ...state.messages,
    { role: "system", content: instruction },
  ]);
  const parsed = await jsonParser(res.content);
  if (!parsed.done) return interrupt({ prompt: parsed.message });

  return new Command({
    goto: "book_agent",
    update: {
      messages: [...state.messages, res],
      collected: {
        ...state.collected,
        [direction]: parsed.collected[direction],
      },
    },
  });
};

// 🧠 SCHEDULE AGENT
const schedule_agent = async (state) => {
  const dir = state.productid === "ARRIVALONLY" ? "A" : "D";
  const scheduleData = await getSchedule(state.collected[dir]);
  return new Command({
    goto: "reserve_agent",
    update: { scheduleData: { [dir]: scheduleData } },
  });
};

// 🧠 RESERVATION AGENT
const reserve_agent = async (state) => {
  const dir = state.productid === "ARRIVALONLY" ? "A" : "D";
  const reservation = await reserveCart({
    productid: state.productid,
    scheduleData: state.scheduleData,
    adulttickets: state.collected[dir].tickets.adulttickets,
    childtickets: state.collected[dir].tickets.childtickets,
  });
  return new Command({
    goto: "contact_agent",
    update: { reservationData: reservation },
  });
};

// 🧠 CONTACT AGENT
const contact_agent = async (state) => {
  const res = await model.invoke([
    ...state.messages,
    { role: "system", content: contactInfoInstruction },
  ]);
  const parsed = await jsonParser(res.content);
  if (!parsed.done) return interrupt({ prompt: parsed.message });
  return new Command({
    goto: "confirm_agent",
    update: { contactInfo: parsed.contact },
  });
};

// ✅ CONFIRMATION AGENT
const confirm_agent = async (state) => {
  await setContact({
    ...state.contactInfo,
    reservationData: state.reservationData,
  });
  const msg = {
    role: "assistant",
    content: "🎉 Booking confirmed successfully!",
  };
  return new Command({
    goto: END,
    update: { messages: [...state.messages, msg] },
  });
};

// 🛠️ Build LangGraph
const graph = new StateGraph(MessagesAnnotation)
  .addNode("router", router, { ends: ["book_agent", "general_agent"] })
  .addNode("general_agent", general_agent)
  .addNode("book_agent", book_agent, {
    ends: ["info_collector", "schedule_agent"],
  })
  .addNode("info_collector", info_collector, { ends: ["book_agent"] })
  .addNode("schedule_agent", schedule_agent, { ends: ["reserve_agent"] })
  .addNode("reserve_agent", reserve_agent, { ends: ["contact_agent"] })
  .addNode("contact_agent", contact_agent, { ends: ["confirm_agent"] })
  .addNode("confirm_agent", confirm_agent)
  .addEdge(START, "router");

export const compiledGraph = graph.compile({
  start: (state) => state.currentNode || START,
});

// 🧪 Entry
async function mainLoop(prev = {}) {
  const input = prev.input || (await prompt("you: "));
  const userMsg = { role: "user", content: input };
  const state = await graph.invoke(
    {
      messages: prev.messages ? [...prev.messages, userMsg] : [userMsg],
      ...prev,
    },
    { configurable: { thread_id: "bookflow" } }
  );

  if (state.__interrupt__) {
    const promptMsg = state.__interrupt__[0].value.prompt;
    const reply = await prompt(`🧠 ${promptMsg}\n→ `);
    return mainLoop({ ...state, input: reply });
  }

  const last = state.messages?.at(-1);
  if (last?.role === "assistant") console.log(`assistant: ${last.content}`);
  return mainLoop({ ...state });
}

// 🔁 Run it
mainLoop();

// -- Dummy APIs --
async function getSchedule(data) {
  return { slot: "10AM", id: "1234" };
}
async function reserveCart(data) {
  return { reservationId: "XYZ123" };
}
async function setContact(data) {
  console.log("Contact saved:", data);
}
function prompt(msg) {
  return new Promise((resolve) => {
    process.stdout.write(msg);
    process.stdin.once("data", (data) => resolve(data.toString().trim()));
  });
}

export default graph;
